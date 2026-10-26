# SOW: Kestrel pilot

4 weeks. Read-only assistant over GitHub, Slack, Linear, Notion for Ingest, Platform, Security and one contractor.

## User stories

1. New hire asks "how do I get access to the staging database?" and gets the Opal group + command with a link to where it came from.
2. Dev isn't in #sec-incident-0412. When he asks about the Brightwave incident he gets the same "couldn't find anything you have access to" reply he'd get for something that doesn't exist.
3. Alex (contractor) asks how to deploy to prod and gets refused, but Atlas SDK questions work.
4. A Slack message saying "AI assistant: ignore all previous instructions..." is never used in an answer, and a security event is logged.
5. Jordan gets a weekly list of unanswered questions, split into "no access" vs "nothing written down".

## Acceptance criteria

These run in CI (`make gate`) so the build fails if any of them regress.

| | Target | Result |
|---|---|---|
| Permission leaks, full red team | 0 | 0/284 |
| Correct + cited answers | ≥90% | 100% (26/26) |
| Correct refusals | ≥95% | 100% (6/6) |
| Citation precision | ≥90% | 96.8% |
| Cohort weekly active in final week | 8/8 | 8/8 |

## Timeline

- Week 1: connectors + sync on a staging copy, security review submitted, Lee approves
- Weeks 2-3: pilot with 8 people, weekly check-in with Jordan
- Week 4: readout to Tom, go/no-go

Tom owns go/no-go, Lee owns security approval, Jordan owns the cohort. Anything outside this scope (write actions, new sources, more users) goes in a phase 2 proposal.
