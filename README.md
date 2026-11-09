# Errata

**For the sales/solutions engineer who answers security questionnaires and RFPs: when a product fact changes, Errata finds every answer you already sent that is now wrong, shows the memory evidence, and drafts a correction for your approval.**

> All data in this repo is **synthetic** (a fictional company, "Kestrel Ledger", and fictional customers). Errata never contacts customers. Approved corrections are marked *"approved (not sent)"*.

## Results (measured locally, synthetic data, small n)
Full pipeline on the open-source Hindsight server + Ollama `qwen3.5:9b`: 30 sent answers, 4 fact changes, and 12 stale (answer, change) pairs labelled before any run. Details and raw rows: [`docs/LOCAL_VALIDATION_REPORT.md`](docs/LOCAL_VALIDATION_REPORT.md), `results/local/eval_local.json`.

| | |
|---|---|
| Stale answers **silently cleared** | **0 / 12** in two independent runs: all 12 reached a human (run 2: 6 *needs correction*, 6 *needs review*) |
| Change note → right fact (Hindsight `recall` top-1) | 4 / 4 |
| Precision of *needs correction* | 0.55 (run 2). 4 of the 5 "false alarms" quote a sent sentence that really is stale but sits outside the pre-registered labels; 1 is a genuine verifier error |
| Old fact version after a change | invalidated in Hindsight with a reason; new version live; verified via `list_memories(state=…)` |
| Persistence | memory and audit trail survive a full restart of Hindsight and the app |
| Latency (laptop, Apple silicon) | `reflect` median ≈32 s; verification median ≈38 s per candidate (up to ~3 min for long drafts); seeding 30 answers ≈19–20 min |

An earlier spike on Hindsight Cloud (different model) measured `based_on` citation recall of 32/32. On 8 post-change questions it scored Hindsight 8/8, BM25 RAG 4/8 and stateless 2/8: [`docs/MEMORY_PROOF.md`](docs/MEMORY_PROOF.md).


## Why memory, not a search box
Answer libraries such as Loopio and Responsive keep *future* answers fresh. Nobody tracks which customer was told the *old* version. To do that you need:
1. **Provenance at send time.** Which facts did each answer rely on? Errata drafts answers with Hindsight `reflect` and records the facts in `based_on`.
2. **Facts that change over time.** Superseded versions are *invalidated* in memory, not overwritten. The new version gets a new document id.
3. **A judgement per answer.** Not every answer that depends on a changed fact is wrong. "Is our US data stored in the US?" is still true after a new India region launches. Errata re-checks each candidate against the current fact and says why.

The same idea, retroactively repairing past decisions when a fact is retracted, was shown before in a different domain by [Unsay](https://github.com/JonathanSolvesProblems/unsay) (medication safety). Errata applies it to B2B commitments, using Hindsight as the memory layer.

## The three-step journey
1. **Post a change.** Paste the announcement as it arrived. Hindsight `recall` suggests which fact it supersedes, and you confirm.
2. **See the affected sent answers.** Each candidate is grouped as *needs correction*, *needs human review* or *still accurate*, with how it was found (`hindsight_citation` / `dependency_index`).
3. **Review and approve.** Compare the old answer, the drafted correction and the memory evidence (old fact struck through, new fact, `based_on` memories). Approve or reject. The decision is retained back into Hindsight.

## Where Hindsight is used (real calls, `errata_app/core.py`)
| Operation | Function | Purpose |
|---|---|---|
| `retain` / `retain_batch` | `seed`, `propose_change`, `apply_change`, `decide` | facts (`fact:Fxx:vN`), sent answers (`answer:Qxx:vN`), change notes, human decisions |
| `reflect` + `based_on` | `seed` | draft answers and capture which facts they used |
| `recall` | `propose_change` | rank which fact a free-text change note supersedes |
| `list_memories` + `PATCH state=invalidated` | `apply_change` | retire every memory of the old fact version, with a reason |
| `reflect` + `response_schema` | `_verify` | per-answer verdict {affected/unaffected, reason, corrected answer} against current facts |

Architecture and failure behaviour: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Band Desktop usage (team workflow, not runtime): [`docs/BAND_USAGE.md`](docs/BAND_USAGE.md).

## Run it locally (no Cloud, no API key, no Docker)
Errata runs against the **open-source Hindsight server** on your machine, with embedded PostgreSQL and a local LLM via Ollama.

Prerequisites: macOS/Linux, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) running, about 10 GB of disk space, and 16 GB of RAM recommended.
```bash
git clone <this repo> && cd errata
ollama pull qwen3.5:9b                 # ~7.6 GB, once
cp .env.example .env                   # local defaults; no key needed
scripts/hindsight-local.sh start       # installs hindsight-all==1.2.0 into .hindsight-venv on first run, serves 127.0.0.1:8888
uv sync
uv run python -m errata_app.server     # http://127.0.0.1:8765
```
Stop: `Ctrl-C` the app, then run `scripts/hindsight-local.sh stop`. Memory lives in Hindsight's embedded Postgres, and the audit trail lives in `errata-local.db`. Both survive restarts, and the app never re-seeds an existing workspace.

Click **Load synthetic workspace**. It makes 30 real local `reflect` calls, so seeding takes tens of minutes on a laptop (see measured timings above). Then paste a change, for example:
> Ops update Nov 3: our Mumbai region (AWS ap-south-1) is now GA. New Indian customers' data is stored and processed in India by default; us-east-1 is no longer the only region.

The same adapter also works against Hindsight Cloud: set `HINDSIGHT_BASE_URL` and `HINDSIGHT_API_KEY` in `.env`.

## Tests
```bash
uv run pytest                                            # unit tests (FAKE client for logic, real adapter for connection loss)
ERRATA_REQUIRE_LIVE=1 uv run pytest -m live -v -s        # REAL local Hindsight + Ollama, fresh isolated bank
uv run python scripts/eval_local.py                      # ground-truth eval of the full app pipeline (30 answers, 4 changes)
```

## Limitations (honest)
- The demo data is synthetic. Results on 30 answers and 4 changes are not a production accuracy claim.
- The dependency index is a hand-written keyword list for this fact sheet.
- Verdicts come from an LLM (Hindsight `reflect`). Every verdict is reviewable, and nothing is sent automatically.
- Latency is local-LLM-bound (tens of seconds per `reflect` on a laptop). The one-time seed of 30 drafts takes tens of minutes.
- Single user, single workspace, local SQLite. No authentication.

## License
MIT
