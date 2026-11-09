# Errata

**For the sales/solutions engineer who answers security questionnaires and RFPs: when a product fact changes, Errata finds every answer you already sent that is now wrong, shows the memory evidence, and drafts a correction for your approval.**

> All data in this repo is **synthetic** (a fictional company, "Kestrel Ledger", and fictional customers). Errata never contacts customers. Approved corrections are marked *"approved (not sent)"*.

<!-- RESULTS -->

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

## Run it (≈2 minutes + seeding)
```bash
git clone <this repo> && cd errata
cp .env.example .env            # add your Hindsight Cloud key (https://ui.hindsight.vectorize.io)
uv sync
uv run python -m errata_app.server   # http://127.0.0.1:8765
```
Click **Load synthetic workspace**. This makes 30 real `reflect` calls, so expect several minutes. Then paste a change, for example:
> Ops update Nov 3: our Mumbai region (AWS ap-south-1) is now GA. New Indian customers' data is stored and processed in India by default; us-east-1 is no longer the only region.

## Tests
```bash
uv run pytest                          # unit tests use a FAKE Hindsight client (logic only)
HINDSIGHT_API_KEY=... uv run pytest tests/test_cloud_live.py -s   # real Cloud, isolated bank
```

## Limitations (honest)
- The demo data is synthetic. Results on 30 answers and 4 changes are not a production accuracy claim.
- The dependency index is a hand-written keyword list for this fact sheet.
- Verdicts come from an LLM (Hindsight `reflect`). Every verdict is reviewable, and nothing is sent automatically.
- Latency is LLM-bound (seconds per call, and it varies). The one-time seed of 30 drafts takes minutes.
- Single user, single workspace, local SQLite. No authentication.

## License
MIT
