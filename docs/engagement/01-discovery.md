# Discovery notes: Kestrel Labs

Three calls, week 0.

## Call 1: Tom Becker (VP Eng, sponsor)

- Asked for "ChatGPT for our docs"
- Actual problem: new hires take ~9 working days to first merged PR, and three staff engineers answer most questions in #eng-help
- Wants: faster ramp, fewer interruptions for seniors
- Would like it to file tickets eventually. Told him read-only for the pilot.

## Call 2: Jordan Pike (EM, Ingest, champion)

- Two new hires on his team, blocked on questions daily
- Knowledge mostly isn't in docs. It's in Slack threads, Linear issues, READMEs, a few Notion pages
- Shared 90 days of #eng-help stats:
  - ~410 questions, 31% answered by the same 3 people
  - median first response 38 min
  - repeats: staging access, deploy freeze, on-call, local setup, runbooks
- Happy to run the pilot with Ingest + a few people from Platform and Security

## Call 3: Lee Nakamura (Head of Security)

- Will block anything that can show someone content from a channel, repo or page they're not in. This is the real risk, more than answer quality.
- Also wants: no confirming that restricted things exist, no secrets in answers, contractors limited to their project, audit trail
- Okta is the IdP, GitHub uses SAML so logins map to corporate email
- Needs to review model provider data terms before real data goes in. Pilot uses a staging copy.
- One contractor team (Northwind Studio, Atlas SDK) has guest access to one Slack channel, one repo, one Notion page

## How a question gets answered today

1. search Notion/GitHub/Slack separately (10-20 min, often fails)
2. post in #eng-help or DM a staff engineer
3. wait (38 min median)
4. staff engineer context switches (~25x a week)
5. answer ends up in a thread nobody finds next time

## Agreed success criteria (going into the SOW)

1. zero permission leaks on an adversarial suite Lee can review and rerun
2. 90%+ of answerable questions answered correctly with the right citation
3. 95%+ correct refusals
4. whole pilot cohort weekly active by week 2
5. a time-saved estimate Tom can take to finance, with assumptions written out

## Open

- Does Slack Enterprise Grid export need separate admin approval? (Jordan checking)
- DMs: off unless Kestrel asks
