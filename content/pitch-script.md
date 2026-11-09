# 5-minute judge pitch + live demo script

## 0:00–0:40 — Problem and persona
"You're a solutions engineer. Last quarter you answered 40 security questionnaires. This morning ops launched an India region, and legal added a new subprocessor. **Which customers did you already tell the old version?** Answer libraries keep the *next* answer current. Nothing looks backwards."

## 0:40–1:10 — Evidence (no invented numbers)
- Questionnaire and RFP work is a real, recurring, paid workflow: Loopio's 2025 and 2026 benchmark reports surveyed more than 1,500 response professionals. Their 2020 report put a response at about 23.8 hours, which is dated, and we say so.
- Cost example, every assumption labelled HYPOTHETICAL: suppose one deal was promised "US-only hosting" and the contract references that answer. Discovering it after signature means legal review plus re-papering. We don't quote a dollar figure; the point is that today nobody even knows which deals to check.

## 1:10–1:25 — Solution in one sentence
"Errata remembers which facts every answer you sent relied on. When a fact changes, it lists the answers that are now wrong, with evidence, and drafts the fix for you to approve."

## 1:25–3:25 — Live demo (app on this laptop: local open-source Hindsight + Ollama; synthetic data)
1. **Sent answers table:** point at Q02, "cannot host data within India", and at the cited-fact chips. *"Drafted by Hindsight reflect. These chips are its `based_on` citations."*
2. **Post the change:** paste the Mumbai note → *Find the fact it changes* → recall ranks F01. *"I confirm. A human owns that mapping."*
3. **Supersede & check:** locally this takes several minutes (~38 s per candidate). Apply one change live and talk over the first verdicts, OR show a change applied before the pitch and say so plainly ("I ran this one at [time] on this laptop"): *"It's invalidating the old F01 memories (kept for audit, not deleted), retaining v2, and re-checking each linked answer. Each 'affected' must quote the false sentence."*
4. **Wow:** the affected list with Q02, Q01 and Q22.
5. **Negative control:** Q03, the US customer. Show its actual verdict. If it was flagged, say so honestly: *"this is exactly why a human approves; it's in our measured limitations."*
6. **Review Q02:** old answer vs. drafted correction, plus Memory evidence (v1 struck through, v2, `based_on` doc IDs) → Approve.
7. **Refresh:** v2, "approved (not sent)", and the audit trail.

**Fallback if the laptop stack fails:** say "here is a recorded run from [date]" and play the recorded demo video. Never pretend it's live. No network is needed for the live demo.

## 3:25–4:15 — Before vs. after (measured, synthetic, small n; docs/LOCAL_VALIDATION_REPORT.md, earlier Cloud spike in docs/MEMORY_PROOF.md)
- `based_on` captured **32/32** true fact dependencies (precision 0.78).
- New questions after 4 changes: **Hindsight 8/8**, plain RAG over the same docs 4/8, stateless 2/8.
- Local full-pipeline eval (30 answers, 4 changes, 12 pre-labelled stale pairs): **0 of 12 silently cleared** (two runs), recall mapping 4/4, "affected" precision 0.55; 4 of 5 false alarms quoted a really-stale sent sentence, 1 was a real error.
- Honest: a keyword index found the same candidates on this small fact sheet. The verdict is the hard part. Our verifier over-flagged, so verdicts must quote the false sentence and a human approves.

## 4:15–5:00 — Architecture, team, limitations, next
- Stdlib Python server, SQLite audit store, open-source Hindsight running locally (embedded Postgres) on Ollama qwen3.5:9b: retain / recall / reflect / invalidate. No paid API. Band Desktop was used for our agent review loop, not at runtime.
- Team contributions: [FILL IN — only real contributions].
- Next: Loopio/Responsive export import, per-customer region context, and evaluation on real (consented) questionnaire history.

## 12 hard questions
1. **Why not a database join?** If you hand-label every answer's dependencies, a join works. Our keyword index matched the candidates on 20 facts. Hindsight gives you the dependency record *without labelling* (32/32 recall), maps free-text change notes to facts (4/4), and keeps superseded facts out of new answers (8/8 vs. 4/8 for RAG).
2. **What does retain/recall/reflect each do here?** Retain stores facts, answers, notes and decisions. Recall ranks which fact a note supersedes. Reflect drafts answers with `based_on` and judges each candidate with a response schema.
3. **Is a citation the same as a dependency?** No. Precision was 0.78: it over-cites. That's why candidates are the union of citations and an index, and why the verdict is a separate step.
4. **How do you handle superseded facts?** Versioned document IDs and `PATCH state=invalidated` with a reason. We never upsert, because upserting deletes the memories that old citations point to.
5. **False positives?** Yes. On the residency change the verifier flagged 4 answers that weren't wrong. An "affected" verdict now needs a verbatim quote of a sentence that was actually sent, and a human approves everything.
6. **False negatives?** Candidate recall was 12/12 for both citation and index. An item whose verification fails becomes "needs review", never silently "unaffected". We saw that happen under a real HTTP 402.
7. **Is the data real?** No, it's synthetic, with the ground truth fixed before any run. The counts are small, and this is a mechanism test, not an accuracy claim.
8. **Can it send something wrong to a customer?** There is no send path in the code. Approved corrections are marked "not sent".
9. **Prompt injection via a change note?** Notes are quoted as data, the output is schema-constrained, and every change needs human confirmation of the fact and approval of the correction.
10. **What exactly is built?** Everything in the demo: seed, change, impact, review, approval, persistence, and tests (33 unit tests, a live integration test against the local Hindsight server, and a 30-answer ground-truth eval of the full pipeline). It runs fully offline on a laptop: open-source Hindsight + Ollama.
11. **Competitors?** Loopio and Responsive do forward hygiene. Conveyor and Inventive store answer sources but, as far as we could verify, don't sweep sent answers. Unsay did backward correction for medication safety; we credit it.
12. **What does Band do?** We used Band Desktop rooms for agent code review of the approval path. It isn't part of Errata's runtime, and it isn't connected to Hindsight.

13. **Why local, not Cloud?** We started on Hindsight Cloud and ran out of credits. The open-source server gave the same API (same client, same calls; the only change was making the API key optional). Customer commitments are sensitive, so local-by-default is also the better product answer. Trade-off: ~38 s per verification on a laptop.
