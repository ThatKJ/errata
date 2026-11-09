# Video production, YouTube package and upload checklist

## Recording (human)
1. Close notifications (Focus mode). Use one browser window at 1920×1080 with nothing else on screen.
2. Recorder: QuickTime (File → New Screen Recording; region 1920×1080), or OBS if installed. Turn the mic on and do a 10 s test.
3. Start the local stack: `cd errata && scripts/hindsight-local.sh start && uv run python -m errata_app.server`, then open http://127.0.0.1:8765. The workspace must already be seeded (≈19 min, do it beforehand), and a fresh change must not yet be posted.
   - The demo bank `errata-demo-20261109193639` already has C1 (Mumbai) applied and Q02 approved. To record the change step live, either post a **different** change (for example the Snowflake subprocessor note from `errata_app/seed_data.py` CHANGES E2), or reseed into a fresh DB first: `ERRATA_DB=errata-video.db uv run python -m errata_app.server`, then click Load.
4. Follow `content/video-script.md`. Locally, **Supersede & check** takes ≈15–20 min for ~12 candidates (measured). Record the click and the first verdicts appearing, pause the recording, and resume when it finishes. Show "(≈18 min skipped, local LLM)" on screen. Never imply it is instant.
5. Before upload, verify the export with real numbers:
   `ffprobe -v error -show_entries stream=width,height -show_entries format=duration -of default=nw=1 errata-demo.mov`
   The result must be width ≥1920, height ≥1080, and duration between 120 and 300 s.
6. Optional thumbnail: a team photo plus the text "Find the answers you already sent wrong". Make it in Nano Banana per the guide, with real team photos only.

## Titles (pick one; no banned word)
1. Finding customer answers a fact change made wrong (Hindsight memory)
2. My agent remembers which facts every answer used
3. When a fact changes, which sent answers are now wrong?
4. Provenance with Hindsight reflect: correcting answers already sent
5. Errata demo: retain, recall, reflect, and a human approval

## Description (fill in the real URLs)
Errata finds security-questionnaire and RFP answers that a product-fact change made wrong. It shows the memory evidence and drafts a correction for human approval. All data shown is synthetic (a fictional company).

- How Hindsight is used: reflect drafts answers and records based_on citations; versioned fact IDs, with old memories invalidated rather than deleted; recall maps a free-text change to the fact; reflect with a response schema re-checks each answer and must quote the false sentence.
- Runs fully local: the open-source Hindsight server (embedded Postgres) + Ollama qwen3.5:9b. No API key.
- Measured on synthetic data (small n): see docs/LOCAL_VALIDATION_REPORT.md in the repo.

Code: [GITHUB_REPO_URL] · Article: [ARTICLE_URL] · Hindsight: https://github.com/vectorize-io/hindsight · Docs: https://hindsight.vectorize.io/

Chapters: 0:00 Intro · 0:20 The problem · 0:50 Post a change · 1:20 Impact check · 2:00 Negative control · 2:30 Review & approve · 3:00 Persistence · 3:15 Results · 3:35 Links
Tags: agent memory, Hindsight, LLM, RAG, provenance, Python

## YouTube upload checklist
- [ ] ffprobe shows ≥1920×1080 and 120–300 s (paste the output into SUBMISSION_STATUS.md)
- [ ] Visibility: **Public** (not Unlisted or Private)
- [ ] Title, description, chapters and real links filled in. No placeholder URLs.
- [ ] No key, email or account ID visible in any frame
- [ ] The URL opens in a private window while logged out
- [ ] The URL is recorded in SUBMISSION_STATUS.md
