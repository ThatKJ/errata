# YouTube demo video — script and storyboard (target 3:30, hard limit 2–5 min, 1920×1080)

**Must be true on screen:** a live app against Hindsight Cloud, with the synthetic data labelled. If a step is replayed from a recording, the narration must say "recorded run".
**Prerequisites:** Cloud credits topped up; app seeded (`errata.db` present); one change NOT yet posted; terminal font ≥18 pt; browser zoom 125%.

| Time | On screen | Narration (conversational, don't read verbatim) |
|---|---|---|
| 0:00–0:20 | Face cam or title card, then the Errata header | "I'm [NAME]. I built Errata. When a product fact changes, it finds every customer answer you already sent that's now wrong, and drafts the fix for a human to approve." |
| 0:20–0:50 | The Sent answers table. Highlight Q02 (Bharat Microfinance): *"cannot host data within India…"*. Point at the SYNTHETIC tag. | "This is synthetic data for a fictional company. These 30 answers were drafted by Hindsight reflect, and each one stores the facts it cited. Q02 told an Indian customer we can't host in India. Then ops launches a Mumbai region. Answer libraries keep the next answer right. Nothing tells you about the 30 already sent." |
| 0:50–1:20 | Paste the Mumbai note → click **Find the fact it changes**. The proposal shows recall's ranking F01 › … | "I paste the Slack message as-is. Hindsight recall ranks which fact it supersedes. It's F01, data residency. I confirm it, because a human owns that call." |
| 1:20–2:00 | Click **Supersede fact & check sent answers** (wait about 30–45 s; cut the wait in the edit and say so). The impacts panel shows its groups. | "Errata invalidates the old F01 memories in Hindsight. They're not deleted, so they stay auditable. It retains v2, then re-checks every answer linked to F01 by citation or by our index. Each verdict has to quote the exact sentence that's now false." |
| 2:00–2:30 | Point at the *Checked — still accurate* group (Q03, Midwest Credit Union), **if it is there in this run**. If it isn't, show it under *needs review* and say so. | "Here's the negative control. A US credit union was told its data stays in the US. That's still true, so it shouldn't be flagged." (Say whatever actually happened in this run.) |
| 2:30–3:00 | Open **Review** on Q02. Show the old answer, the drafted correction and the Memory evidence: v1 struck through, v2, `based_on` doc IDs. Type a reviewer name → **Approve**. | "Old answer, drafted correction, and the evidence: the invalidated fact version, the new one, and the memories reflect cited. I approve it. It's recorded and retained back into Hindsight. Nothing goes to the customer." |
| 3:00–3:15 | Refresh the page. Q02 shows v2, *correction approved (not sent)*. The audit trail. | "Refresh. The state persists: answer version 2 and an audit trail." |
| 3:15–3:35 | `docs/MEMORY_PROOF.md` tables | "What I measured, on synthetic data and small n: citations caught 32 of 32 real dependencies. After four changes, Hindsight answered 8 of 8 new questions correctly, against 4 of 8 for plain RAG. A keyword index found the same candidates. The hard part is the verdict, so a human always approves." |
| 3:35–3:45 | Repo URL on screen | "Code, data and raw logs are in the repo. Hindsight is linked below." |

**Do not:** fake terminal footage, claim accuracy beyond MEMORY_PROOF.md, show the API key or account email, or say the word that is banned in the article/social copy.
