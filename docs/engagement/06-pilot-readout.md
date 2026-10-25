# 06 · Pilot readout

**Audience:** Tom Becker (sponsor), Jordan Pike (champion), Lee Nakamura (security)
**Recommendation:** **Go.** Roll out to all of engineering in phase 2, keeping the CI permission gate as a release blocker.

## Results against the acceptance criteria

| Criterion | Target | Result | |
|---|---|---|---|
| Permission leaks (284 adversarial tests) | 0 | **0** | ✅ |
| Correct, cited answers | ≥ 90% | **100%** | ✅ |
| Correct refusals | ≥ 95% | **100%** | ✅ |
| Citation precision | ≥ 90% | **96.8%** | ✅ |
| Cohort weekly active, final week | 8/8 | **8/8** | ✅ |

## Usage (8 people, 10 working days)

- **158 questions**, ramping from 13 on day 1 to 22 on day 10
- **95% answered**, and **90% of answers rated helpful**
- **Seconds to an answer** vs a **38-minute** median first response in #eng-help
- **~17 minutes saved per engineer per day**, **22.5 hours** across the pilot
- **~54 questions** that would otherwise have landed in #eng-help

## Projected value at rollout

**~2,330 engineering hours a year, roughly $256K**, under deliberately conservative assumptions:

| Assumption | Value | Source |
|---|---|---|
| Minutes saved per helpful answer (asker) | 8 | Discovery interviews |
| Minutes saved per deflected question (responder) | 5 | Discovery interviews |
| Share of questions that would have hit #eng-help | 40% | #eng-help history vs pilot volume |
| Engineers at rollout | 60 | Kestrel headcount |
| Weekly active at rollout | 60% | Conservative vs 100% in pilot |
| Loaded cost per engineering hour | $110 | Kestrel finance |
| Working days per year | 230 | |

## What the refusals tell us

| Question | Asked by | Count | Meaning |
|---|---|---|---|
| How do I get access to the staging database? | Alex (contractor) | 5 | **Working as intended.** Contractors aren't in the staging docs. |
| What is the parental leave policy? | Dev | 3 | **Content gap.** No such page exists. Flagged to People Ops. |

## Risks and conditions for rollout

1. **Model data terms:** Lee signs off on the model provider's retention terms before real data flows.
2. **DMs stay off** unless Kestrel decides otherwise.
3. **Golden set grows with rollout:** each new team contributes 10 questions, so the quality gate keeps covering what people actually ask.
4. **Phase 2 actions** (filing Linear tickets) get their own security review.

*Usage volume and thumbs-up feedback are simulated (seeded) for this case study. Every answer, refusal and metric comes from running the real pipeline: `make pilot`.*
