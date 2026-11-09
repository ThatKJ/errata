# Nightly execution log (overnight sprint, 2026-11-10 IST)

**Branch:** `improve/errata-overnight` (from `main` @ `1caf2bb`, tagged `baseline-1caf2bb`). Nothing pushed, nothing published.

## Stage 00/01: audit (DONE, read-only)
- Run 2 is complete on disk: `results/local/eval_local.json` finished 2026-11-09T21:41:45Z, summary: 0/12 false clears, precision 0.545, recall 0.50, mapping 4/4, median verify 38.5 s. Both eval DBs and all 4 Hindsight banks preserved (`errata-demo-20261109193639`, two `errata-eval-*`, `errata-test-threads`).
- Demo DB `errata-local.db` backed up to `results/backups/errata-local-pre-overnight-20261110033851.db` (git-ignored). Q02 approval intact.
- Resources at start: swap 3.2 GB used of 4 GB, free memory 74%, Ollama idle (no model loaded), Hindsight PID 98713 (venv `../hindsight-local/.venv`, `REASONING_EFFORT=none`, `MAX_CONCURRENT=1`), 4 stale playwright-mcp processes from earlier sessions left untouched. No LLM inference was run by this sprint so far.

## Stage 02/03: research (DONE, bounded)
- Competitor pages re-checked 2026-11-10: Conveyor docs (3 pages, fetched), Inventive homepage (fetched), Loopio blog (fetched), Loopio support (403), Responsive (search only). None documents re-checking answers already sent after a fact changes. Full prior table: `results/spike/competitor-check.md`. Write-up: `docs/UX_REFERENCE_AND_COMPETITORS.md`.
- Design references found via search (Pinterest itself not browsed): Dribbble activity-log collection, Netguru audit-trail shot, SaaSUI activity-feed patterns, GitLab/Harness split diff viewers. Adopted: left change rail, per-change tally strip, verbatim quotes in serif, vertical evidence timeline, side-by-side before/after. Not copied: any layout pixel-for-pixel, cards-everywhere SaaS kit, all-caps labels.

## Stage 04A/04B + 05: product (DONE, commits `9b7c574`, `de60bb2`, `615541b`)
- `core.py`: `candidates()`, `supersede()` (fast, no LLM), `verify_pending()` (one verdict per candidate, each persisted, resumable), `progress()`, `evidence()` (timeline from SQLite + live Hindsight `list_memories`, labelled live/stored). `apply_change` behaviour unchanged. New `impacts.verified_at` column (additive).
- `server.py`: apply returns 202 and verifies in a background thread; `POST /api/changes/C/resume`; `GET /api/changes/C/impacts/Q/evidence`; state carries `progress`, `running`, `verified_at`.
- New UI (`static/`): blast-radius view, filters, evidence time machine dialog, tabs. CSP-clean (no inline styles). Verified in the real browser against the real demo bank at 1440×900 and 390×844; Q02 evidence shows the real invalidated memory `c42f8c1f…` with reason and `invalidated_at`.
- Tests: 47 unit/HTTP tests pass (`uv run pytest`). Live tests not re-run (verdict logic untouched).
- Running server: restarted on the new code (log `errata-server.log`); same DB and bank.

## Stage 08: demo and video assets (DONE as draft)
- `docs/demo/errata-recorded-screens-draft.mp4` (1920×1080, 152 s): four real screenshots + three title cards, each frame labelled "recorded screenshot, 10 Nov 2026", no narration, no implied live timing. ffprobe verified. The 90-second live route is in `content/pitch-script.md` and `content/video-script.md` (updated to the new UI).
- Preflight for a live demo: `scripts/hindsight-local.sh status` (healthy), `curl 127.0.0.1:8765/api/state` (`configured: true`), open http://127.0.0.1:8765, select change C1 (recorded run) and open Q02's evidence. One small live action that needs no LLM: open any evidence dialog (live `list_memories`). A live change needs one reflect per candidate (~40 s to 3 min each).

## Stage 09: content (DONE, blocked only on the repo URL)
- `python3 content/check_content.py`: every check passes except the `[GITHUB_REPO_URL]` placeholder (human: public repo not approved). Article 1,497 words. LinkedIn 707 chars.
- Article, LinkedIn, Reddit, video script, pitch and publishing checklist agree with run 2, the current code and the new UI. The article does not claim the learning loop.

## Stage 4C: learning experiment (EXPERIMENTAL, isolated bank `errata-learn-*`)
- Script `scripts/learn_experiment.py`; results `results/local/learn_experiment.json` (bank `errata-learn-20261109234523`, finished 2026-11-09T23:56:34+00:00). Ground truth declared in the script before any call. 2 samples per held-out case, one run, qwen3.5:9b, ~32–74 s per verdict.
- **Result (verbatim from the summary):**
  - L2, held-out similar case for the *same* customer (truth unaffected): before 0/2 matched truth (`needs_review`, `affected`); **after 2/2 `unaffected`, and the retained decision `decision:C1:L1` was in `based_on` both times.** The reasons cite it ("The reviewer decision explicitly confirms that backup and disaster-recovery copies are governed by the backup fact…").
  - L3, control (truth affected): `affected` 2/2 before and 2/2 after. **Never cleared**, even with the experience recalled.
  - L4, cross-customer (Acme, truth unaffected): before `affected` 2/2 (verifier error); after `affected` 1, `needs_review` 1; **Bharat's decision was recalled in 1 of 2 Acme verifications.** No false clear, but the experience is not scoped to the customer at retrieval time.
- **Verdict: EXPERIMENTAL, not integrated.** The mechanism works end to end (retain → recall in `based_on` → verdict changes toward ground truth on the held-out case, control intact), but n=2 per case in one run, and the cross-customer recall means a customer-scoped tag filter is required before this could ship without inventing a global rule from one customer's context. Not in the main pitch; may be described as an experiment with these exact numbers.
- Memory during this run: Ollama loaded qwen3.5:9b (7.8 GB, 100% GPU); swap grew from 2.8 GB used of 4 GB to 15.7 GB used of 16 GB with 19% free memory. One inference at a time was respected; nothing else heavy was started. The model unloads itself after ~5 min idle.

## Resume commands
```bash
cd ~/Hackathons/HWB/errata && git status && git log --oneline -6
scripts/hindsight-local.sh status; curl -s 127.0.0.1:8765/api/state | head -c 300
uv run pytest -q
```
Rollback of the UI only: `git checkout baseline-1caf2bb -- errata_app/static`. Full rollback: `git checkout main`.

## Stage 07: adversarial council (written by the coordinator, skeptical by design)
- **Innovation (30%).** Beyond document freshness: the unit of work is a *sent commitment*, and the evidence chain is memory-derived (`based_on`), not hand-labelled. Weakness: the mechanism is Unsay's and the candidate set is matched by a keyword index on this small sheet; the honest claim is "first application to sent B2B answers among products checked", nothing stronger. Not fixed: no cross-customer disclosure logic yet.
- **Hindsight (25%).** Necessary and visible: `retain` (facts, answers, changes, decisions), `recall` (change → fact, 4/4), `reflect` + `based_on` (drafting provenance), `reflect` + `response_schema` (verdicts), `PATCH state=invalidated` (shown live in the time machine with reason and time), `list_memories` (evidence). Weakness: "learns over time" is not demonstrated; the retained decisions are not yet shown changing a later verdict. Stage 4C left EXPERIMENTAL/not run; the pitch must not claim learning.
- **Technical (20%).** Model lies → grounding forces a verbatim quote or routes to review; crash mid-run → verdicts persisted, resume verifies only the rest (tested in the browser with a simulated interruption); bank unavailable → `needs_review`, evidence still renders from stored rows with the outage stated. Weakness: single-process SQLite, no auth, one job at a time by design.
- **UX (15%).** The change header, struck-through old fact, blast-radius bar and severity-ordered rows answer "what changed / who may be wrong / evidence / next" on one screen; the time machine reads top to bottom. Weakness: the verdict *reasons* are long model prose (clamped to two lines); `needs_review` rows still need a reviewer to read the reason to know why.
- **Impact (10%).** A solutions engineer would use the sweep when a region, subprocessor or retention fact changes. What the demo does not prove: performance on real questionnaire history, precision beyond 0.55 on a small synthetic set, latency acceptable beyond a laptop batch.
- **Fixed this sprint from this review:** long waits no longer block the request (background job, live progress, resume); evidence provenance is labelled live vs stored; recorded results are labelled "Recorded run, verified <time>". **Deferred:** disclosure drafts per customer, owner/deadline per fact, per-customer region context, learning experiment.
