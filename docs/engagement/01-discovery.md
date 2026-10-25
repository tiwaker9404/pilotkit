# 01 · Discovery

**Customer:** Kestrel Labs · **Calls:** 3 (sponsor, champion, security) · **Status:** qualified for a pilot

## Stakeholders

| Person | Role in the deal | What they care about |
|---|---|---|
| Tom Becker, VP Engineering | Executive sponsor, signs off | New-hire ramp time, senior engineers' focus time |
| Jordan Pike, EM Ingest | Champion, runs the pilot team | His two new hires are blocked on questions daily |
| Lee Nakamura, Head of Security | Gatekeeper, can veto | "An AI that reads Slack" must never show anyone something they couldn't already see |
| Priya Shah, People Ops | Informed | Exec and HR content must stay out of reach |

## What they said vs what they need

- **They said:** "We want ChatGPT for our docs."
- **What's actually going on:** Kestrel's knowledge isn't in docs. It's spread across Slack threads, Linear issues, READMEs and a few Notion pages, and the people who know where things are are three staff engineers who get interrupted all day.
- **The real need:** get answers to new and mid-level engineers *without* routing through those staff engineers, and without creating a security incident.
- **The real risk:** permissions, not answer quality. Lee will block anything that can't prove it respects private channels, private repos and restricted pages.

## Current state (measured from 90 days of #eng-help, shared by Jordan)

```
Engineer has a question
  └─ searches Notion / GitHub / Slack            ~10 to 20 min, often fails
      └─ posts in #eng-help or DMs a staff engineer
          └─ waits                                median first response: 38 min
              └─ staff engineer context-switches  ~5 min each, ~25 times a week
                  └─ answer lives in a thread nobody will find next time
```

- ~410 questions in #eng-help in 90 days, 31% answered by the same three staff engineers
- New hires' median time to first merged PR: 9 working days
- Most repeated questions: staging access, deploy freeze rules, on-call, local setup, runbooks

## Future state

```
Engineer asks the assistant (Slack or web)
  └─ assistant searches only what that engineer can already read
      └─ cited answer in seconds, or "I couldn't find anything you have access to"
          └─ unanswered questions are reported weekly as documentation gaps
```

## Success criteria (agreed with Tom and Jordan, written into the SOW)

1. **Zero permission leaks** across an adversarial test suite Security reviews. Non-negotiable; this is Lee's gate.
2. **90%+ of answerable questions answered correctly with a citation** to the right source.
3. **95%+ correct refusals** when the asker has no access or nothing exists.
4. **Weekly active use by the full pilot cohort** by week 2.
5. **A credible time-saved estimate** Tom can take to the CFO, with every assumption written down.

## Constraints and open questions

- Read-only for v1. Tom wants actions (filing tickets) later; Lee doesn't, yet.
- Contractors exist (Northwind Studio on the Atlas SDK) and must see only their project.
- Identity is Okta. GitHub uses SAML, so logins map to corporate email.
- Model provider data terms must be reviewed by Lee before any real data flows. The pilot runs on synthetic data plus a staging copy.
- **Open:** does Slack Enterprise Grid data export require a separate admin approval? (Jordan to confirm.)
