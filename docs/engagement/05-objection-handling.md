# 05 · Objection handling

Questions raised during the evaluation, with the answer given and the evidence behind it.

**"Will it show people Slack channels they're not in?"** · *Lee, Security*
No. Permissions are applied before the search runs, so the model never sees content the asker can't open. We tested every user against every document they can't read: 284 adversarial questions, zero leaks. The same suite against an unfiltered setup leaked 201 times, which is the proof the tests actually bite. Security can rerun it any time with `make redteam`.

**"Can it at least confirm that something exists? That's a leak too."** · *Lee*
It can't. A user without access gets the same reply whether the topic is restricted or doesn't exist at all ("Is Kestrel acquiring Tessellate?" and "Is Kestrel acquiring Zanzibar?" return identical text). The decision to refuse uses only documents the asker can read, so it can't become a side channel.

**"What about hallucinations?"** · *Tom, VP Eng*
Every answer cites its sources, and the assistant refuses rather than guesses when nothing relevant is readable. Golden-set results: 100% of answerable questions correct with the right citation, 100% correct refusals. Wrong answers are a bigger risk to adoption than missing ones, so the system is tuned to refuse when unsure.

**"Someone pasted an AWS key in Slack last month. Does that end up in answers?"** · *Lee*
No. Secrets and external emails are redacted when content is ingested and again on output. That exact message is in the pilot data, and the key never reaches the index.

**"What happens when someone leaves or changes teams?"** · *Priya, People Ops*
Access follows Okta and each source's own membership on every sync. If a source's permissions haven't synced within 24 hours, its documents drop out of search until they do.

**"Our docs are outdated. Won't it just repeat stale information?"** · *Jordan, EM*
It can, which is why every answer cites its source so people can check it. The weekly readout also lists unanswered questions split into "asker has no access" (working as intended) and "nothing exists" (write a doc). In the pilot, the parental leave policy came up as a genuine content gap for People Ops.

**"Can it file tickets or reply in threads?"** · *Tom*
Not in the pilot, by design. Write access needs new scopes and a separate security review. It's the first item in the phase 2 proposal, gated on the pilot's results.

**"How is this different from search we already have?"** · *Jordan*
Slack search, GitHub search and Notion search each cover one silo and return links, not answers. The most common questions in #eng-help need information from two or three of them (for example, staging access lives in a README, a Slack thread and an Opal group name).

**"What does it cost to run?"** · *Tom*
Retrieval runs on commodity compute. The main variable cost is model calls per question, which scale with usage and can be capped per user. The pilot readout's time-saved estimate is set against that cost in the rollout proposal.
