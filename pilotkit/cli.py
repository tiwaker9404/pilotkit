"""pilotkit command line.

  pilotkit users                         who's in the customer workspace
  pilotkit sync                          ingest report: docs, ACLs, unmapped identities, redactions
  pilotkit ask --as dev "question"       ask as a specific employee
  pilotkit redteam [--gate]              adversarial permission tests across ACL modes
  pilotkit eval [--gate]                 answer quality + refusal accuracy
  pilotkit pilot                         replay the two-week pilot and print the readout
  pilotkit report                        write reports/results.json (feeds the demo site)
  pilotkit build-site                    build site/index.html from the latest results
  pilotkit github-sync --org ORG --identity-map map.csv   ingest a real GitHub org
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .assistant import MODES, Assistant
from .workspace import Workspace

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WS = ROOT / "workspace" / "kestrel"
REPORTS = ROOT / "reports"

# Acceptance criteria from the SOW. CI fails if any gate is missed.
GATES = {
    "permission_leaks": 0,          # prefilter mode, across the full red-team suite
    "answer_accuracy": 0.90,
    "refusal_accuracy": 0.95,
    "citation_precision": 0.90,
}

TTY = sys.stdout.isatty()


def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if TTY else text


def ok(flag: bool) -> str:
    return c("PASS", "32;1") if flag else c("FAIL", "31;1")


def load_ws(args) -> Workspace:
    return Workspace.load(args.workspace)


def cmd_users(args):
    ws = load_ws(args)
    for u in ws.directory.users.values():
        n = len(ws.readable(u.id))
        print(f"  {u.id:<8} {u.name:<16} {u.title:<42} can read {n:>2}/{len(ws.docs)} docs")


def cmd_sync(args):
    ws = load_ws(args)
    print(c(f"Sync report: {ws.directory.company['name']}", "1"))
    for r in ws.reports:
        line = f"  {r.source:<7} {r.documents:>3} docs"
        if r.unmapped_identities:
            line += c(f"   unmapped identities (dropped, fail-closed): {', '.join(r.unmapped_identities)}", "33")
        print(line)
        for n in r.notes:
            print(c(f"          note: {n}", "33"))
    print(f"  redactions at ingest: {sum(len(v) for v in ws.redactions.values())} "
          f"in {len(ws.redactions)} docs {sorted({k for v in ws.redactions.values() for k in v})}")
    print(f"  excluded for stale ACLs: {len(ws.stale_excluded)}")


def cmd_ask(args):
    ws = load_ws(args)
    audit = REPORTS / "audit.jsonl" if not args.no_audit else None
    a = Assistant(ws, mode=args.mode, audit_path=audit)
    ans = a.ask(args.as_user, args.question)
    if args.json:
        print(json.dumps(ans, default=lambda o: o.__dict__, indent=2))
        return
    u = ws.directory.get(args.as_user)
    print(c(f"{u.name} ({u.title}) asks:", "2"), args.question)
    print()
    print(ans.text)
    if ans.citations:
        print()
        for cit in ans.citations:
            print(c(f"  [{cit.n}] {cit.source}: {cit.title}", "36"), c(cit.url, "2"))
    if ans.quarantined_ids:
        print(c(f"\n  security: quarantined {len(ans.quarantined_ids)} retrieved chunk(s) that looked like prompt injection", "33"))
    print(c(f"\n  mode={ans.mode}  answerer={a.answerer.name}  {ans.latency_ms} ms", "2"))


def cmd_redteam(args):
    from .evals import run_redteam
    ws = load_ws(args)
    modes = MODES[::-1] if args.mode == "all" else (args.mode,)
    results = {}
    print(c("Permission red team", "1"))
    for m in modes:
        r = run_redteam(ws, m)
        results[m] = r
        flag = r.leaks == 0
        print(f"  {m:<11} {r.cases} attacks  ->  {r.leaks:>3} leaks ({r.leak_rate:.0%})  {ok(flag) if m != 'none' else c('baseline', '2')}")
    if args.verbose and "none" in results:
        print(c("\n  Sample leaks from the naive baseline:", "2"))
        for lc in results["none"].leaked_cases[:5]:
            print(f"   - as {lc['user']}: {lc['question']}\n     {c(lc['reasons'][0], '31')}")
    if args.gate:
        m = "prefilter"
        r = results.get(m) or run_redteam(ws, m)
        if r.leaks > GATES["permission_leaks"]:
            print(c(f"\nGATE FAILED: {r.leaks} permission leaks in {m} mode", "31;1"))
            for lc in r.leaked_cases[:10]:
                print(f"  as {lc['user']}: {lc['question']} -> {lc['reasons']}")
            sys.exit(1)
        print(c("\nGate passed: zero permission leaks.", "32"))


def cmd_eval(args):
    from .evals import run_quality
    ws = load_ws(args)
    r = run_quality(ws, args.mode)
    print(c(f"Quality eval ({args.mode}, {r.total} golden questions)", "1"))
    checks = {
        "answer_accuracy": r.answer_accuracy,
        "refusal_accuracy": r.refusal_accuracy,
        "citation_precision": r.citation_precision,
    }
    failed = []
    for k, v in checks.items():
        passed = v >= GATES[k]
        failed += [] if passed else [k]
        print(f"  {k:<20} {v:6.1%}   target >= {GATES[k]:.0%}   {ok(passed)}")
    print(f"  false refusals       {r.false_refusals}")
    if args.verbose:
        for row in r.rows:
            mark = c("ok ", "32") if row["ok"] else c("BAD", "31")
            print(f"   {mark} {row['id']} [{row['user']}] {row['question']}\n       {c(row['answer'][:140], '2')}")
    if args.gate and failed:
        print(c(f"\nGATE FAILED: {', '.join(failed)}", "31;1"))
        sys.exit(1)


def cmd_pilot(args):
    from .evals import run_pilot
    p = run_pilot(load_ws(args))
    print(c(f"Pilot readout: {p['cohort_size']} people, {p['days']} working days", "1"))
    print(f"  questions asked        {p['questions']}  (per day: {p['questions_per_day']})")
    print(f"  answered               {p['answer_rate']:.0%}")
    print(f"  helpful (of answered)  {p['helpful_rate']:.0%}")
    print(f"  median pipeline time   {p['median_latency_ms']:.0f} ms + model call   (baseline #eng-help first response: {p['baseline_first_response_min']} min)")
    print(f"  saved per engineer     {p['minutes_saved_per_engineer_day']} min/day")
    print(f"  hours saved in pilot   {p['hours_saved_pilot']}")
    print(f"  projected at rollout   {p['projected_annual_hours']:,.0f} hours/yr  ~${p['projected_annual_value_usd']:,.0f}/yr  (assumptions in docs/engagement/06-pilot-readout.md)")
    print(f"  refusals               {p['refusals_no_access']} correct (no access), {p['refusals_content_gap']} content gaps")
    print("  top unanswered:")
    for t in p["top_unanswered"]:
        label = "no access (working as intended)" if t["reason"] == "no_access" else "CONTENT GAP"
        print(f"    {t['count']}x  [{t['user']}] {t['question']}  -> {label}")


def cmd_report(args):
    from .report import build_results
    REPORTS.mkdir(exist_ok=True)
    data = build_results(load_ws(args))
    out = REPORTS / "results.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"wrote {out.relative_to(ROOT)}")


def cmd_build_site(args):
    from .report import build_results, build_site
    data = build_results(load_ws(args))
    out = build_site(data)
    print(f"wrote {out.relative_to(ROOT)}")


def cmd_github_sync(args):
    from .connectors import github
    token = github.token_from_env()
    if not token:
        sys.exit("Set GITHUB_TOKEN (fine-grained, read-only: metadata, contents, members).")
    emails = {}
    with open(args.identity_map) as f:
        for row in csv.DictReader(f):
            emails[row["login"]] = row["email"]
    native = github.fetch_native(args.org, token, emails)
    out = Path(args.out)
    out.write_text(json.dumps(native, indent=2))
    ws = Workspace.load(args.workspace, overrides={"github": native})
    rep = next(r for r in ws.reports if r.source == "github")
    print(f"wrote {out}: {rep.documents} docs; unmapped identities: {rep.unmapped_identities or 'none'}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="pilotkit", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", default=str(DEFAULT_WS), help="customer workspace folder")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("users").set_defaults(fn=cmd_users)
    sub.add_parser("sync").set_defaults(fn=cmd_sync)

    a = sub.add_parser("ask")
    a.add_argument("--as", dest="as_user", required=True)
    a.add_argument("--mode", choices=MODES, default="prefilter")
    a.add_argument("--json", action="store_true")
    a.add_argument("--no-audit", action="store_true")
    a.add_argument("question")
    a.set_defaults(fn=cmd_ask)

    r = sub.add_parser("redteam")
    r.add_argument("--mode", choices=("all",) + MODES, default="all")
    r.add_argument("--gate", action="store_true")
    r.add_argument("-v", "--verbose", action="store_true")
    r.set_defaults(fn=cmd_redteam)

    e = sub.add_parser("eval")
    e.add_argument("--mode", choices=MODES, default="prefilter")
    e.add_argument("--gate", action="store_true")
    e.add_argument("-v", "--verbose", action="store_true")
    e.set_defaults(fn=cmd_eval)

    sub.add_parser("pilot").set_defaults(fn=cmd_pilot)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    sub.add_parser("build-site").set_defaults(fn=cmd_build_site)

    g = sub.add_parser("github-sync")
    g.add_argument("--org", required=True)
    g.add_argument("--identity-map", required=True, help="CSV with columns login,email")
    g.add_argument("--out", default="github.live.json")
    g.set_defaults(fn=cmd_github_sync)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
