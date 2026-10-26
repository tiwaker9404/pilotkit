# Security review

Answers for Lee's vendor questionnaire.

## Scopes (all read-only)

- GitHub: fine-grained token. Metadata, contents, members: read. No Actions, secrets, admin or write.
- Slack: bot token. `channels:read`, `channels:history`, `groups:read`, `groups:history`, `users:read`, `users:read.email`. No `chat:write`. No `im:history`, so DMs are off by default. The fixtures include one DM only to test that participant-only access works.
- Linear: OAuth `read`.
- Notion: read content + read user info with email. No insert/update.

## Permission rules

| Source | Who can read | Test |
|---|---|---|
| GitHub | public: everyone. internal: org members, not outside collaborators. private: granted teams + direct collaborators | test_permissions.py |
| Slack | public channel: full members, not guests. private channel / DM: members only | test_permissions.py |
| Linear | public team: all members. private team: team members | test_permissions.py |
| Notion | workspace page: members, not guests. restricted: whoever it's shared with | test_permissions.py |

All sources fail closed: unknown visibility type, unmapped identity, or ACLs older than 24h all mean the doc is excluded.

## Threats

- **Seeing restricted content.** Prefilter before search. Red team: 0 leaks out of 284 (201 with no filtering).
- **Confirming something exists** ("are we acquiring X?"). Same refusal text whether it's restricted or doesn't exist, and the refusal check only looks at the user's own readable docs. `test_refusal_does_not_reveal_existence`
- **Prompt injection in Slack/docs.** Quarantined and logged. Prefilter caps the damage anyway.
- **Secrets in content.** Redacted at ingest and on output. `test_ingested_secret_never_reaches_index`
- **Offboarded users.** Access follows Okta and source membership each sync; stale ACLs fail closed.
- **Audit log leaking data.** Only stores user, redacted question and doc ids. `test_audit_log_has_ids_not_content`

## Red team

Every restricted doc has planted strings (tracker ids like `CNRY-SEC-7731` and specific facts). An answer is a leak if it contains one of those for a doc the user can't read, or cites such a doc. Each user is tested against each doc they can't read with 1-3 targeted questions, plus generic jailbreaks. CI fails on a single leak.

## Data

Docs and ACLs stay in Kestrel's environment. In Claude mode, retrieved snippets go to the model API per request, so Lee needs to sign off on retention/training terms first. Offline mode sends nothing out. Audit logs kept 90 days by default.
