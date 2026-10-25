# 07 · Handoff runbook

For Kestrel's Platform team, who own the assistant after the pilot.

## Daily

- **Sync runs hourly.** Check `pilotkit sync` output for:
  - *Unmapped identities:* a source user with no Okta match. Usually a bot or an ex-employee. Fix the mapping or leave it excluded. Never add a manual override without Security.
  - *Stale ACL exclusions:* a source failed to sync within 24h and its documents dropped out of search. Fix the connector first (usually an expired token).
- **Security events** (`prompt_injection_quarantined` in `reports/audit.jsonl`) go to #security-alerts. Review the source message and remove it if malicious.

## Before every release

```bash
make gate     # tests + red team + quality eval; any failure blocks the release
```

If the red-team gate fails, **do not ship.** A failure means some user could see something they shouldn't. Look at `leaked_cases` in the output and fix the connector's permission mapping.

## Common tasks

| Task | How |
|---|---|
| Add a question to the golden set | Append a line to `evals/golden.jsonl`, run `make eval` |
| Add a restricted doc to the red team | Add its id, secrets and attack questions to `evals/canaries.json` |
| Rotate a source token | Update the secret in your vault; the next sync picks it up |
| Onboard a new GitHub org | `pilotkit github-sync --org <org> --identity-map logins.csv` |
| Investigate "why did X see Y?" | Find the request in `reports/audit.jsonl` (doc ids), then check that doc's readers in the access matrix |
| Offboard someone urgently | Remove from Okta; run a manual sync to drop them immediately rather than waiting for the hourly sync |

## Escalation

| Issue | First contact | Then |
|---|---|---|
| Suspected permission leak | Lee Nakamura (Security), immediately | Vendor DE; disable the assistant until resolved |
| Connector broken | Platform on-call | Vendor support |
| Wrong or outdated answers | Owner of the cited doc | Add to golden set once fixed |

## Owners

- **Service owner:** Platform team (Maya Okafor)
- **Security owner:** Lee Nakamura
- **Content gaps:** Jordan Pike triages the weekly unanswered report
