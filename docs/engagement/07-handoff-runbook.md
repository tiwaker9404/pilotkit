# Runbook

For Kestrel's Platform team. Owner: Maya Okafor. Security contact: Lee Nakamura. Content gaps: Jordan Pike.

## Daily

Sync runs hourly. In the `pilotkit sync` output, look for:
- unmapped identities: usually a bot or someone who left. Fix the mapping or leave it excluded. Don't add manual overrides without Security.
- stale ACL exclusions: a source didn't sync in 24h, so its docs are out of search. Usually an expired token.

Injection events (`prompt_injection_quarantined` in `reports/audit.jsonl`) go to #security-alerts. Check the source message and remove it if it's malicious.

## Before every release

```
make gate
```

If the red team fails, don't ship. Some user can see something they shouldn't. The output lists the leaked cases. Fix the connector's permission mapping.

## Common stuff

- Add a golden question: append to `evals/golden.jsonl`, run `make eval`
- Add a restricted doc to the red team: add its id, planted strings and attack questions to `evals/canaries.json`
- Rotate a token: update it in the vault, next sync picks it up
- New GitHub org: `pilotkit github-sync --org <org> --identity-map logins.csv`
- "Why did X see Y?": find the request in the audit log (doc ids), then check that doc's readers on the access map
- Urgent offboarding: remove from Okta and run a manual sync instead of waiting for the hourly one

## Escalation

- Possible permission leak: Lee immediately, then the vendor. Turn the assistant off until it's fixed.
- Broken connector: Platform on-call, then vendor support.
- Wrong answer: whoever owns the cited doc. Add a golden question once it's fixed.
