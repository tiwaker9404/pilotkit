# Pilot readout

For Tom, Jordan and Lee.

Recommendation: roll out to all of engineering, and keep the red-team gate as a release blocker.

## Against the acceptance criteria

All five met: 0/284 leaks, 100% correct cited answers, 100% correct refusals, 96.8% citation precision, 8/8 weekly active.

## Usage (8 people, 10 working days)

- 158 questions, 13 on day 1, 22 on day 10
- 95% answered, 90% of those rated helpful
- answers in seconds vs 38 min median wait in #eng-help
- ~17 min saved per engineer per day, 22.5 hours total
- ~54 of those questions would otherwise have gone to #eng-help

## Value at rollout

Roughly 2,330 engineering hours a year, ~$256K. I kept the assumptions conservative:

- 8 min saved for the asker per helpful answer
- 5 min saved for whoever would have answered, but only for the 40% that would have hit #eng-help
- 60 engineers, 60% weekly active (pilot was 100%)
- $110/hr loaded cost, 230 working days

## Refusals

- Alex (contractor) asked about staging DB access 5 times. Correct, contractors don't have those docs.
- Dev asked about parental leave 3 times. No page exists, so this is a content gap. Sent to People Ops.

## Before rollout

1. Lee signs off on model provider data terms
2. DMs stay off
3. Each new team adds ~10 golden questions so the quality check covers what people actually ask
4. Ticket filing (phase 2) gets its own security review

Usage volume and thumbs-up rates in this readout are simulated with a fixed seed. Answers, refusals and latency come from running the pipeline (`make pilot`).
