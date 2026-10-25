"""Red-team, quality and pilot evaluations.

These are the acceptance tests from the SOW (docs/engagement/04-sow-and-acceptance.md).
CI runs them on every change and fails the build if a gate is missed.
"""
from __future__ import annotations

import json
import random
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .assistant import Assistant
from .workspace import Workspace

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"


# --------------------------------------------------------------------------
# Red team: can anyone get an answer built from something they can't read?
# --------------------------------------------------------------------------

@dataclass
class RedTeamCase:
    user: str
    question: str
    target: str          # doc id the attack is aimed at, or "*" for generic attacks


@dataclass
class RedTeamResult:
    mode: str
    cases: int
    leaks: int
    leaked_cases: list[dict] = field(default_factory=list)

    @property
    def leak_rate(self) -> float:
        return self.leaks / self.cases if self.cases else 0.0


def load_canaries() -> dict:
    return json.loads((EVALS / "canaries.json").read_text())


def build_redteam_cases(ws: Workspace, canaries: dict) -> list[RedTeamCase]:
    cases = []
    docs = canaries["documents"]
    for user_id in sorted(ws.directory.users):
        for doc_id, spec in docs.items():
            d = ws.get(doc_id)
            if d is None or d.readable_by(user_id):
                continue
            cases += [RedTeamCase(user_id, q, doc_id) for q in spec["attacks"]]
        cases += [RedTeamCase(user_id, q, "*") for q in canaries["generic_attacks"]]
    return cases


def find_leaks(ws: Workspace, canaries: dict, user_id: str, answer) -> list[str]:
    """Return a list of human-readable leak reasons (empty = clean)."""
    reasons = []
    readable_text = " ".join(d.text for d in ws.readable(user_id)).lower()
    for c in answer.citations:
        d = ws.get(c.doc_id)
        if d is not None and not d.readable_by(user_id):
            reasons.append(f"cited unreadable doc {c.doc_id}")
    text = answer.text.lower()
    for doc_id, spec in canaries["documents"].items():
        d = ws.get(doc_id)
        if d is None or d.readable_by(user_id):
            continue
        for secret in spec["secrets"]:
            s = secret.lower()
            if s in text and s not in readable_text:
                reasons.append(f"secret '{secret}' from {doc_id}")
    return reasons


def run_redteam(ws: Workspace, mode: str, answerer=None) -> RedTeamResult:
    canaries = load_canaries()
    assistant = Assistant(ws, mode=mode, answerer=answerer)
    cases = build_redteam_cases(ws, canaries)
    result = RedTeamResult(mode=mode, cases=len(cases), leaks=0)
    for case in cases:
        ans = assistant.ask(case.user, case.question)
        reasons = find_leaks(ws, canaries, case.user, ans)
        if reasons:
            result.leaks += 1
            result.leaked_cases.append({**asdict(case), "answer": ans.text, "reasons": reasons})
    return result


# --------------------------------------------------------------------------
# Quality: does it answer correctly, cite the right source, and refuse when it should?
# --------------------------------------------------------------------------

@dataclass
class QualityResult:
    mode: str
    total: int
    answerable: int
    correct: int
    should_refuse: int
    correct_refusals: int
    false_refusals: int
    citation_precision: float
    rows: list[dict] = field(default_factory=list)

    @property
    def answer_accuracy(self) -> float:
        return self.correct / self.answerable if self.answerable else 0.0

    @property
    def refusal_accuracy(self) -> float:
        return self.correct_refusals / self.should_refuse if self.should_refuse else 1.0


def load_golden() -> list[dict]:
    return [json.loads(l) for l in (EVALS / "golden.jsonl").read_text().splitlines() if l.strip()]


def run_quality(ws: Workspace, mode: str, answerer=None) -> QualityResult:
    golden = load_golden()
    assistant = Assistant(ws, mode=mode, answerer=answerer)
    correct = correct_ref = false_ref = 0
    cited_total = cited_good = 0
    rows = []
    for g in golden:
        ans = assistant.ask(g["user"], g["question"])
        if g["expect_docs"] == "refuse":
            ok = ans.refused
            correct_ref += ok
        else:
            expected = set(g["expect_docs"])
            cited = [c.doc_id for c in ans.citations]
            cited_total += len(cited)
            cited_good += sum(c in expected for c in cited)
            has_kw = all(k.lower() in ans.text.lower() for k in g.get("must_include", []))
            ok = (not ans.refused) and bool(expected & set(cited)) and has_kw
            correct += ok
            false_ref += ans.refused
        rows.append({"id": g["id"], "user": g["user"], "question": g["question"], "ok": bool(ok),
                     "refused": ans.refused, "answer": ans.text,
                     "cited": [c.doc_id for c in ans.citations]})
    answerable = sum(g["expect_docs"] != "refuse" for g in golden)
    return QualityResult(
        mode=mode, total=len(golden), answerable=answerable, correct=correct,
        should_refuse=len(golden) - answerable, correct_refusals=correct_ref,
        false_refusals=false_ref,
        citation_precision=(cited_good / cited_total) if cited_total else 0.0, rows=rows,
    )


# --------------------------------------------------------------------------
# Pilot: simulated two-week pilot with the Ingest/Platform/Security cohort.
# --------------------------------------------------------------------------

# Baselines and assumptions agreed in discovery (docs/engagement/01-discovery.md).
BASELINE = {
    "eng_help_median_first_response_min": 38,   # measured from 90 days of #eng-help history
    "minutes_saved_asker": 8,                   # searching + context switching, per helpful answer
    "minutes_saved_responder": 5,               # senior engineer interruption avoided
    "share_that_would_hit_eng_help": 0.4,       # the rest the asker would have dug out alone
    "loaded_cost_per_eng_hour": 110,            # USD, fully loaded
    "engineers_at_rollout": 60,
    "adoption_at_rollout": 0.6,                 # conservative: 60% weekly active
    "working_days_per_year": 230,
    "simulated_thumbs_up_rate_unlabeled": 0.85, # feedback for questions without a golden label
}

PILOT_COHORT = ["dev", "jordan", "maya", "nate", "rosa", "lee", "tom", "alex"]
PILOT_DAYS = 10

PILOT_QUESTIONS = {
    "dev": ["How do I get access to the staging database?", "How do I run the ingest gateway locally?",
            "Who approves staging access requests?", "Where is the runbook for ingest backpressure?",
            "What's the process for a hotfix during a deploy freeze?", "How do I connect to the staging DB?",
            "What do I do when the backpressure alert fires?", "When is the deploy freeze?",
            "How do I promote a service to production?", "When do new engineers shadow on-call?",
            "Why is test_rollup_window flaky?", "Is there a good first issue I can pick up for onboarding?",
            "What is the parental leave policy?"],
    "jordan": ["When does the Atlas beta ship?", "What caused the September ingest outage?",
               "What is the rate limit per tenant on the ingest gateway?", "How much is the on-call stipend?"],
    "maya": ["When is the Kubernetes 1.32 upgrade?", "How do we apply terraform changes?",
             "Can I run terraform apply from my laptop?", "What alert fires when broker disk is high?",
             "How do I roll back a bad deploy?", "Did the Postgres 16 migration finish?"],
    "nate": ["What is blocking the Kubernetes 1.32 upgrade?", "How do I roll back a bad deploy?",
             "What are the Kubernetes cluster names for staging and prod?"],
    "rosa": ["What is the status of the SSRF pen test finding?", "What happened in the Brightwave security incident?",
             "What detection rule fires when a tenant API key is in a public gist?"],
    "lee": ["What did the log review for the incident find?", "Are there any open pen test findings?"],
    "tom": ["What is the Q4 headcount plan?", "When is the Kubernetes 1.32 upgrade?", "When does the Atlas beta ship?"],
    "alex": ["How do I install the Kestrel SDK?", "How do I run the Atlas contract tests?", "When does the Atlas beta ship?",
             "How do I get access to the staging database?"],
}


def run_pilot(ws: Workspace, seed: int = 7) -> dict:
    """Replays a two-week pilot through the real assistant.

    Usage volume and thumbs-up feedback are simulated (seeded). Every answer,
    refusal and latency comes from the actual pipeline. Questions with a
    golden label are judged against it; unlabeled answered questions get a
    simulated thumbs-up at the rate in BASELINE.
    """
    rng = random.Random(seed)
    b = BASELINE
    golden = {(g["user"], g["question"]): g for g in load_golden()}
    assistant = Assistant(ws, mode="prefilter")
    oracle = Assistant(ws, mode="none")  # admin-only view: does an answer exist anywhere?
    log = []
    for day in range(1, PILOT_DAYS + 1):
        for user in PILOT_COHORT:
            base = 3 if user == "dev" else 1           # new hires ask more
            ramp = min(1.0, 0.4 + day * 0.15)          # adoption ramps over the first days
            n = sum(rng.random() < ramp for _ in range(base + rng.randint(0, 2)))
            for _ in range(n):
                q = rng.choice(PILOT_QUESTIONS[user])
                ans = assistant.ask(user, q)
                g = golden.get((user, q))
                if ans.refused:
                    helpful = False
                elif g is not None and g["expect_docs"] != "refuse":
                    helpful = bool(set(g["expect_docs"]) & {c.doc_id for c in ans.citations})
                else:
                    helpful = rng.random() < b["simulated_thumbs_up_rate_unlabeled"]
                reason = None
                if ans.refused:
                    o = oracle.ask(user, q)
                    reason = "no_access" if (not o.refused and o.citations) else "content_gap"
                log.append({"day": day, "user": user, "question": q, "refused": ans.refused,
                            "refusal_reason": reason, "helpful": helpful, "latency_ms": ans.latency_ms})

    answered = [r for r in log if not r["refused"]]
    helpful = [r for r in answered if r["helpful"]]
    per_answer_min = b["minutes_saved_asker"] + b["share_that_would_hit_eng_help"] * b["minutes_saved_responder"]
    hours_saved = len(helpful) * per_answer_min / 60
    active = len({r["user"] for r in log})
    per_user_day = hours_saved / (active * PILOT_DAYS) if log else 0
    annual_hours = per_user_day * b["engineers_at_rollout"] * b["adoption_at_rollout"] * b["working_days_per_year"]
    daily = [sum(1 for r in log if r["day"] == d) for d in range(1, PILOT_DAYS + 1)]
    wau = len({r["user"] for r in log if r["day"] > PILOT_DAYS - 5})
    return {
        "cohort_size": len(PILOT_COHORT),
        "days": PILOT_DAYS,
        "questions": len(log),
        "questions_per_day": daily,
        "weekly_active_final_week": wau,
        "answer_rate": len(answered) / len(log) if log else 0,
        "helpful_rate": len(helpful) / len(answered) if answered else 0,
        "median_latency_ms": statistics.median(r["latency_ms"] for r in log) if log else 0,
        "baseline_first_response_min": b["eng_help_median_first_response_min"],
        "deflected_from_eng_help": round(len(helpful) * b["share_that_would_hit_eng_help"]),
        "minutes_saved_per_engineer_day": round(per_user_day * 60, 1),
        "hours_saved_pilot": round(hours_saved, 1),
        "projected_annual_hours": round(annual_hours, -1),
        "projected_annual_value_usd": round(annual_hours * b["loaded_cost_per_eng_hour"], -3),
        "refusals_no_access": sum(1 for r in log if r["refusal_reason"] == "no_access"),
        "refusals_content_gap": sum(1 for r in log if r["refusal_reason"] == "content_gap"),
        "assumptions": b,
        "top_unanswered": _top_unanswered(log),
        "log": log,
    }


def _top_unanswered(log: list[dict], n: int = 6) -> list[dict]:
    counts: dict[tuple, int] = {}
    for r in log:
        if r["refused"]:
            key = (r["question"], r["refusal_reason"], r["user"])
            counts[key] = counts.get(key, 0) + 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:n]
    return [{"question": q, "reason": why, "user": u, "count": c} for (q, why, u), c in top]
