# Test results record (2026-11-09, IST)

> **Superseded for current numbers by [`LOCAL_VALIDATION_REPORT.md`](LOCAL_VALIDATION_REPORT.md) (2026-11-10, local open-source Hindsight + Ollama).** This file records the earlier Cloud/fake-backend phase.

Tests are separated by what they prove. **"Fake" means a recording stub, not Hindsight Cloud.**

## A. Automated unit tests (FAKE Hindsight client — logic only)
`uv run pytest -q` → **27 passed, 1 skipped** (the live Cloud test skips without a key in the environment).
Covered:
- `based_on` → fact-id parsing
- versioned document IDs
- recall-rank suggestion
- invalidate old + retain new
- candidate union, and unrelated answers untouched
- failed verification → `needs_review`
- a decision recorded once, then 409
- persistence across store reopen
- note validation
- grounded "affected" (must quote a sentence actually sent; 4 cases)
- review fixes: v2 retained before v1 invalidated; failed apply locks the change (`failed`, not re-appliable, no half-applied fact); 0-memory invalidation logged as a warning; JSON-escaped note in the verifier prompt; memory retained before a decision is recorded; cannot approve an `unaffected` item or blank text; grounding needs ≥2 words and tolerates curly punctuation; an all-failed seed is not marked seeded

## B. Live Hindsight Cloud (real calls)
| Test | Result | Evidence |
|---|---|---|
| Auth: list banks with valid / invalid key | 200 / 401 | session log |
| Live integration test, run 1 (4-answer slice) | recall → F01 ✔; Q01, Q22 affected ✔; trap Q03 unaffected ✔; Q04 index-only candidate judged affected (dataset ambiguity; the test's assertion was wrong about the design and was corrected) | `results/live_test_run1.txt` |
| Spike: 97 calls | 0 errors | `results/spike/hindsight_run.json` |
| Provenance, recall mapping, superseded-fact answering, baselines | see `docs/MEMORY_PROOF.md` | `results/spike/eval.json` |
| App verifier (pre-grounding), 20 candidates | 10 valid verdicts; 10 failed HTTP 402 → all `needs_review` | `results/spike/verify_reflect.json` |
| App seeded against Cloud via UI/API | 30/30 answers drafted, 0 errors | `docs/screenshots/01-workspace-seeded-real.png` |
| **Grounded verifier, live** | **BLOCKED: HTTP 402, balance $0.01** (20 attempts, all `needs_review`; one confirmation call since; no retries) | `results/spike/verify_reflect_grounded.json` |

## C. Browser E2E (FAKE backend; Playwright, Chromium) — UI and persistence only
`tests/ui_fake_backend.py` (port 8790, temp DB):
- seed → post change → recall-ranked proposal → apply → impacts grouped → Review dialog (old vs draft + memory evidence) → approve → dialog closes, no error banner ✔
- **Reload:** Q02 shows `v2 · correction approved (not sent)`, impact `approved · UI test`, audit log top = `decide` ✔
- **API failure paths:** double approve → **409**; blank note → **400**; bad date → **400**; unknown fact → **400** ✔
- Browser console: the only error was a favicon 404, fixed (returns 204).
- Screenshots from this mode are NOT published.

## C2. Server hardening (FAKE backend, curl)
text/plain POST → **403**; foreign Host header → **403** (CSRF and DNS-rebinding guard); non-object JSON → **400**; second seed → **409**; re-apply of the same change → **409**; approve an unaffected item → **400**; approve without text → uses the draft explicitly (**200**).

## Independent code review (ECC code-reviewer agent)
- HIGH (non-crash-safe `apply_change`) and 6 MEDIUM findings were **fixed** with the tests above.
- Remaining LOW items, accepted for the demo scope:
  - shared SQLite cursor iteration outside the lock;
  - change note retained before confirmation (an orphan memory if never applied);
  - urllib would forward auth on a redirect: an `http://` base URL is never used (the base URL is https).
- No XSS (every model string is escaped), no secret leakage, no external send path.

## D. Security checks
- `.env` and `errata.db` are git-ignored (verified with `git check-ignore`). No tracked env or db files.
- Scan of tracked files **and full git history** for `hsk_…`, `sk-…`, `ghp_…`, `AKIA…` and private keys: **none**.
- Key rotation: **pending (human, Hindsight console)**. The key appeared in chat.

## E. Not yet done
- Real-Cloud E2E in the browser (needs credits).
- A recorded demo (needs credits).

