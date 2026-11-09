# Reddit link post — DRAFT

**Type:** Link post. **Link target:** the PUBLISHED article URL (not the repo, not a draft).
**Subreddit:** pick ONE.
- First choice: **r/LLMDevs**, which suits an engineering write-up with measured baselines.
- Alternative: r/aiagents.

**Before posting, read the subreddit's sidebar rules while logged in.** Reddit blocks anonymous rule reads, so I could not verify them: self-promotion limits, flair requirements, account age/karma minimums, link-post allowance.

## Title (engineer-oriented, no hype)
Recording which facts each LLM answer cited, so a fact change finds the stale answers already sent

## Optional first comment (only if the subreddit allows author comments on link posts)
Author here. The comparison is what surprised me. On my small synthetic set:
- Hindsight's reflect `based_on` captured every true fact dependency (32/32), but over-cited (precision 0.78).
- A hand-written keyword index found the same candidate answers.
- The real difficulty was the verdict: is an answer that depends on a changed fact actually wrong? The LLM verifier over-flagged and wasn't deterministic. So it now has to quote the exact false sentence, or the item goes to human review.
- Re-run fully local (open-source Hindsight + Ollama qwen3.5:9b, 30 answers, 4 changes, 12 pre-labelled stale pairs): 0 of 12 silently cleared in two runs, "affected" precision 0.55. 4 of 5 "false positives" quoted a sent sentence that really was stale, because the model's answers restated neighbouring facts; 1 was a real verifier error. About 38 s per verification on a laptop.

Code and raw run logs: [GITHUB_REPO_URL]. I'd welcome critique of the evaluation design. Disclosure: I built this.

## Acceptance checklist
- [ ] The article is public and renders correctly, logged out.
- [ ] The subreddit rules have been read and allow this post.
- [ ] Posted as a **Link** post to the article URL.
- [ ] The permalink opens logged out and the post is not removed by AutoModerator (check after ~10 min).
- [ ] The permalink is recorded in `SUBMISSION_STATUS.md`.
