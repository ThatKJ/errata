# Release readiness (overnight sprint, branch `improve/errata-overnight`)

_Status values: **PASS** (ran, evidence path given), **FAIL**, **BLOCKED** (needs a human or an external account), **NOT RUN**. Updated 2026-11-10 05:10 IST._

## Reproducible commands

| # | Check | Command | Status | Evidence |
|---|---|---|---|---|
| 1 | Unit + HTTP tests (FAKE Hindsight; real adapter for connection loss) | `uv run pytest -q` | **PASS** 47 passed, 2 deselected | this session, after commit `3df6a7a` |
| 2 | Live tests against local Hindsight + Ollama (fresh bank, ~9 min, one LLM call at a time) | `ERRATA_REQUIRE_LIVE=1 uv run pytest -m live -v -s` | **NOT RUN this sprint** (verdict logic untouched; last PASS 2026-11-10 01:37 in `results/local/live_test_run_local.txt`) | `results/local/live_test_run_local.txt` |
| 3 | Ground-truth eval, run 2 | `uv run python scripts/eval_local.py` | **PASS (recorded)**, not re-run: 0/12 false clears, precision 0.545, recall 0.50, mapping 4/4 | `results/local/eval_local.json` (finished 2026-11-09T21:41:45Z) |
| 4 | App serves the real demo bank | `uv run python -m errata_app.server` then `curl -s 127.0.0.1:8765/api/state` | **PASS** `configured: true`, bank `errata-demo-20261109193639`, C1 applied, 12/12 verified | `errata-server.log` |
| 5 | Evidence endpoint reads live memory state (no LLM) | `curl -s 127.0.0.1:8765/api/changes/C1/impacts/Q02/evidence` | **PASS** `live: true`, `quote_found: true`, old `fact:F01:v1` memory `c42f8c1f…` state `invalidated` with reason and `invalidated_at` | screenshot `docs/screenshots/overnight-03-invalidated-memory.png` |
| 6 | Browser, real stack, desktop 1440×900 | Playwright MCP against :8765 | **PASS**, 0 console errors | `docs/screenshots/overnight-01-blast-radius.png`, `overnight-02-evidence-time-machine.png` |
| 7 | Browser, real stack, mobile 390×844 | same | **PASS**, no horizontal page scroll (`scrollWidth == 390`); the answers table scrolls inside its own wrapper | `docs/screenshots/overnight-04-mobile.png` |
| 8 | Browser E2E of the whole flow on the FAKE backend (seed → post change → confirm fact → 202 background job → verdicts → review → approve → reload) | `ERRATA_DB=/tmp/x.db PORT=8790 uv run python tests/ui_fake_backend.py` | **PASS**, 0 console errors; Q02 became v2 `correction approved (not sent)`; audit event `decide` recorded | screenshots kept out of docs (fake data) in `.playwright-mcp/shot-06…09` |
| 9 | Interrupted job: change left `applying` with 1 of 5 verdicts, server shows "Interrupted", **Resume checking** verifies only the 4 remaining | simulated in the fake-backend temp DB | **PASS** (`C2 applied`, 5 impacts, the crash verdict kept) | `.playwright-mcp/shot-10-interrupted.png`; unit test `test_supersede_then_verify_pending_is_resumable` |
| 10 | CSP (`default-src 'self'`, no inline styles/scripts) | browser console on load | **PASS** after removing inline `style=` attributes (first load had 5 CSP violations, fixed) | console log, this session |
| 11 | Localhost-only, Host-header and content-type guards | `tests/test_server.py::test_guards_still_hold` | **PASS** 403 / 403 | pytest |
| 12 | Content checks | `python3 content/check_content.py` | see `SUBMISSION_STATUS.md` | |
| 13 | Secrets in tracked files / history | `git grep -nE 'hsk_|sk-[A-Za-z0-9]{10}|ghp_|AKIA'` | **PASS** none (re-run this sprint) | |

## Fail-closed invariants (where each is enforced and tested)

| Invariant | Code | Test |
|---|---|---|
| `unaffected` cannot coexist with a quoted false sent sentence | `core.grounded` | `test_unaffected_that_quotes_a_false_sent_sentence_goes_to_review` |
| Ungrounded `affected` quote → `needs_review`, quote shown | `core.grounded` | `test_affected_requires_quoting_a_sentence_that_was_actually_sent`, `test_ungrounded_quote_is_shown_to_reviewer` |
| Error / timeout / bad schema → `needs_review`, never cleared | `core._verify` | `test_failed_verification_is_needs_review_never_silently_unaffected`, `test_hindsight_down_never_clears` |
| Draft failed or no provenance → always a candidate | `core.candidates` | `test_failed_draft_is_always_a_candidate` |
| New fact version retained before old is invalidated; 0 invalidated → never `unaffected` | `core.supersede`, `core.verify_pending` | `test_new_version_is_retained_before_old_is_invalidated`, `test_nothing_invalidated_never_clears` |
| One Hindsight client per thread | `core.LiveHindsight.c` | live `test_adapter_works_across_threads` |
| Approval never sends anything; cannot approve `unaffected` or blank text; second decision → 409 | `core.decide`, server | `test_cannot_approve_an_unaffected_impact_or_empty_text`, `test_decision_is_recorded_once…` |
| Decisions and verdicts survive restart; interrupted job resumes without re-verifying | SQLite rows per verdict, `verify_pending` | `test_state_persists_across_store_reopen`, `test_supersede_then_verify_pending_is_resumable` |
| Audit entries carry ids, times, source types, statuses | `Store.log`, `evidence()` | `test_evidence_timeline_is_built_from_stored_and_live_memory` |

## Rollback
- UI only: `git checkout baseline-1caf2bb -- errata_app/static`
- Whole sprint: `git checkout main` (baseline `1caf2bb`). The SQLite schema change is additive (`impacts.verified_at`, `quoted`), so the old code still opens the same `errata-local.db`. Demo DB backup: `results/backups/errata-local-pre-overnight-20261110033851.db` (git-ignored).

## Blocked (human-only)
Public repo creation and push, article/LinkedIn/Reddit/YouTube publication, organizer form, team names, Band Desktop sign-in, API-key rotation. See `../SUBMISSION_STATUS.md`.
