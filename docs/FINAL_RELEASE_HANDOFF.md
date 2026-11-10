# Final release handoff (2026-11-10)

The canonical submission tracker is `../SUBMISSION_STATUS.md`, outside this repo, because it holds form details. This file covers only the public release.

| Deliverable | Status | Evidence |
|---|---|---|
| Public repo | **VERIFIED PUBLIC**: logged-out HTTP 200 for the repo, README, LICENSE and screenshots | https://github.com/ThatKJ/errata, default branch `main` |
| Tests | **PASS**: 48 passed, 2 deselected (live tests are opt-in) | `uv run pytest -q` |
| Secret scan | **PASS**: no keys or tokens in tracked files or full history; `.env*` and databases are ignored | `docs/RELEASE_READINESS.md` row 13 |
| Claims | reconciled against raw rows | `docs/RELEASE_CLAIMS.md` |
| Article | **PUBLISHED** on DEV, verified logged out | https://dev.to/kirtan120007/the-answers-you-already-sent-are-the-ones-hindsight-remembers-3b8e |
| Demo video | **FILE READY**, 3:05, 1080p, synthesized narration disclosed; not yet uploaded | `docs/demo/errata-demo.mp4`, `content/youtube-upload.md` |
| LinkedIn, Reddit, YouTube, Band, forms | need the owner's signed-in browser | `../SUBMISSION_STATUS.md` |

## Release refs
- Baseline: tag `baseline-1caf2bb`. Overnight work: tag `overnight-final-4481e38`, branch `improve/errata-overnight`.
- Release: `main`. Rollback of the UI only: `git checkout baseline-1caf2bb -- errata_app/static`.

## Fixed in the release run
- Buttons stayed stuck on their busy label ("Asking Hindsight…") after a successful proposal or a failed action. The shared `busy()` helper now always restores the label. Regression test: `tests/test_static.py`.

## Data notes
- The demo recording used a copy of the demo DB (`errata-local-video.db`, git-ignored). The original `errata-local.db` and its Q02 approval are unchanged.
- Posting the video's change note retained change-note memories into the demo bank: `change:C2`, plus `change:C3` and `change:C4` from two aborted takes. These are tagged `kind:change`. Every recall and reflect call filters on fact tags, so they cannot affect drafts, recall rankings or verdicts. They were left in place rather than deleted.

## Start the demo
```bash
cd errata && scripts/hindsight-local.sh status   # or: start
uv run python -m errata_app.server              # http://127.0.0.1:8765
```
