# Objections from the eval

Questions that came up during the pilot and what I answered.

**Lee: "Will it show people Slack channels they're not in?"**
No. Permissions are applied before search, so the model never sees anything the user can't open. 284 targeted attacks, 0 leaks. The same suite with filtering off leaks 201 times, so the tests do catch real leaks. Lee can rerun it with `make redteam`.

**Lee: "Can it at least confirm something exists? That's a leak too."**
No. "Is Kestrel acquiring Tessellate?" and "Is Kestrel acquiring Zanzibar?" get the same reply from someone without access. The refusal check only uses docs the asker can read.

**Tom: "What about hallucinations?"**
Every answer cites sources, and it refuses instead of guessing when nothing readable matches. 100% correct on the golden set, but that's 32 questions, so we grow it during rollout.

**Lee: "Someone pasted an AWS key in Slack last month."**
That exact message is in the pilot data. The key is redacted at ingest and never reaches the index.

**Priya: "What happens when someone leaves or changes teams?"**
Access follows Okta and source membership on every sync. If a source hasn't synced in 24h, its docs drop out until it does.

**Jordan: "Our docs are out of date."**
It can repeat stale info, which is why every answer links its source. The weekly unanswered list also shows where docs are missing. The parental leave policy came up as an actual gap.

**Tom: "Can it file tickets?"**
Not in the pilot. Needs write scopes and another security review. First thing in phase 2.

**Jordan: "How is this different from Slack/Notion search?"**
Those each search one tool and return links. Most #eng-help questions need two or three tools. Staging access, for example, is in a README, a Slack thread and an Opal group name.

**Tom: "What does it cost?"**
Retrieval is cheap. The main cost is model calls per question, which can be capped per user. I put the number next to the time-saved estimate in the rollout proposal.
