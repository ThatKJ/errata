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

## Resume commands
```bash
cd ~/Hackathons/HWB/errata && git status && git log --oneline -6
scripts/hindsight-local.sh status; curl -s 127.0.0.1:8765/api/state | head -c 300
uv run pytest -q
```
Rollback of the UI only: `git checkout baseline-1caf2bb -- errata_app/static`. Full rollback: `git checkout main`.
