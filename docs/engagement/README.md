# The engagement

A four-week engagement with **Kestrel Labs** (fictional), an observability company with about 180 employees and 60 engineers. Kestrel is evaluating an AI assistant that answers engineering questions from their GitHub, Slack, Linear and Notion.

I play the deployment engineer on the vendor side: run discovery, design the solution, get it through security review, run a pilot, and hand it off.

| Week | Phase | Artifact |
|---|---|---|
| 0 | Discovery calls with the sponsor, champion and security | [01-discovery.md](01-discovery.md) |
| 0 | Solution design and trade-offs | [02-solution-design.md](02-solution-design.md) |
| 1 | Security questionnaire and threat model | [03-security-review.md](03-security-review.md) |
| 1 | Scope, user stories, acceptance criteria | [04-sow-and-acceptance.md](04-sow-and-acceptance.md) |
| 1 to 3 | Objections raised during the evaluation | [05-objection-handling.md](05-objection-handling.md) |
| 3 | Two-week pilot results and recommendation | [06-pilot-readout.md](06-pilot-readout.md) |
| 4 | Runbook for the customer's team | [07-handoff-runbook.md](07-handoff-runbook.md) |

Every number in these documents is produced by the code in this repo. Run `make all` to regenerate them.

**What's simulated:** the customer, their data, and pilot usage volume. **What's real:** the permission model, connectors, retrieval, red team, evals and every answer.
