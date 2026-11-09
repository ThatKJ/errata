# Local validation report: Errata on open-source Hindsight + Ollama
_Measured 2026-11-10 (IST) on one MacBook Pro (Apple silicon arm64, 17 GB unified memory). All data is SYNTHETIC. Nothing here used Hindsight Cloud._

## Stack (pinned)
| Component | Version / setting |
|---|---|
| Hindsight server | `hindsight-all==1.2.0` (api-slim 1.2.0, embed 1.2.0) in an isolated Python 3.12 venv |
| Storage | embedded PostgreSQL + pgvector via `pg0-embedded 0.16.1` (`~/.pg0`, 123 MB after all runs) |
| Embeddings / reranker | Hindsight defaults, local (`sentence-transformers`; 724 MB HF cache) |
| LLM | Ollama 0.40.8, `qwen3.5:9b` (9.7B, nvfp4, MLX runner, 100% GPU), `HINDSIGHT_API_LLM_REASONING_EFFORT=none`, `LLM_MAX_CONCURRENT=1`, observations disabled |
| Client | `hindsight-client==1.2.0` (unchanged), app adapter `core.LiveHindsight` (no API key, no auth header) |
| Start / stop | `scripts/hindsight-local.sh start` / `stop` (binds 127.0.0.1:8888 only) |

**qwen3.5:9b compatibility:** tool calling verified directly via Ollama's OpenAI-compatible API. Hindsight's agentic `reflect` completes with tool calls (typically 3 iterations, 2 tool calls) and `response_schema` structured output parses. Thinking is on by default for this model. `reasoning_effort=none` turns it off (a probe produced 5 completion tokens instead of 542). Hindsight 1.2.0 forwards that setting to Ollama, as confirmed in the startup log.

## 1. Smoke test (fresh bank `smoke-local-1`)
| Call | Result | Time |
|---|---|---|
| `create_bank` | ok | 43 ms |
| `retain_batch` (2 facts) | ok; LLM fact extraction | 12.3 s |
| `recall` | top hit = F01 fact, tags intact | 305 ms |
| `reflect` (include_facts) | correct answer; `based_on` → `F01` | 20.9 s |
| `reflect` + `response_schema` | valid `{status, false_sentence, reason, corrected_answer}` | 28.3 s |

**Restart persistence:** `hindsight-local.sh stop` stopped the server, the health check was confirmed down, then `start` brought it back (warm start ≈16 s). The same bank still listed both memories (`fact:F01:v1`, `fact:F09:v1`).

## 2. Unit tests: `uv run pytest`
**33 passed, 1 deselected** (the live test is opt-in). They use a FAKE client for logic. Connection-loss tests use the **real adapter** against a closed port.
New in this migration (each written failing first, except the Markdown case, which already passed and is kept as a regression guard):
- no `Authorization` header without a key
- Hindsight unreachable → `needs_review`; propose fails loudly
- an answer whose draft failed is always a candidate (→ `needs_review`)
- old fact version not found to invalidate → never `unaffected`
- a rejected (ungrounded) quote is shown to the reviewer

## 3. Live integration test: `ERRATA_REQUIRE_LIVE=1 uv run pytest -m live -v -s`
**1 passed in 508 s** (`results/local/live_test_run_local.txt`). Fresh bank `errata-test-*`, 4-answer slice:
- seed 297 s; all 4 answers drafted with `based_on` citations
- `recall` mapped the Mumbai change note to **F01** (503 ms)
- `fact:F01:v1` **invalidated** in Hindsight with its reason; `fact:F01:v2` valid (verified with `list_memories(state=…)` on that bank)
- Q22 `affected` with a quote that is verbatim from the sent answer; Q01, Q03 (trap) and Q04 → `needs_review`; none cleared wrongly
- approval → SQLite answer v2 `correction approved (not sent)`, and `answer:Q01:v2` retained into Hindsight

The first live run failed one assertion carried over from the Cloud era: "Hindsight must not cite F01 for the backups answer Q04". The local model's verbose backup answer also mentions primary hosting, so it cites F01. That's a provenance-precision difference, not a safety one. The assertion now checks the outcome instead: Q04 must not be judged *affected* by the residency change.

## 4. Ground-truth evaluation of the full app pipeline: `scripts/eval_local.py`
Dataset `errata_app/seed_data.py`: 30 sent answers, 20 facts, 4 changes. The **12 gold-affected (answer, change) pairs** and the 3 traps were fixed before any model ran. Each change: `propose_change` (recall suggestion recorded) → `apply_change` on the gold fact → verdicts. Raw rows: `results/local/eval_local.json`.

| Metric | Formula | Value |
|---|---|---|
| Change → fact mapping (recall top-1) | correct / 4 | **4 / 4** |
| Candidates verified | union of `based_on` citations and the keyword index | 39 |
| TP (affected ∧ gold) | | 6 |
| FP (affected ∧ ¬gold) | | 6 |
| FN (gold ∧ ¬affected) | | 6, **all 6 are `needs_review`** |
| Precision of `affected` | TP / (TP+FP) | **0.50** |
| Recall of `affected` | TP / 12 | **0.50** |
| **False clears** (gold ∧ `unaffected`/not a candidate) | | **0 / 12** |
| Gold pairs routed to a human (`affected` or `needs_review`) | | **12 / 12 = 1.00** |
| `needs_review` total | | 19 |
| Trap flagged `affected` | | 1 (E2/Q07) |
| Median verifier latency | per candidate | 38.3 s |

**Error analysis.** All 6 FPs come with a quote checked in code against the text that was actually sent, and each quote contradicts the new fact:
- E1/Q29: *"Customer data is stored and processed exclusively in the AWS us-east-1 region"*. False after the Mumbai launch.
- E2/Q07 (trap): *"No other third parties process customer data, including any analytics vendors."* False after the Snowflake analytics subprocessor.
- E4/Q28: *"…permanently deletes all customer data within **90 days**."* False after the 180-day hold.

The pre-registered labels assumed each answer stays on its question's topic. qwen3.5:9b drafts are verbose and restate neighbouring facts, so they contain additional statements that really are stale. We report the strict numbers as the result and don't re-label. The 6 FNs are all cases where the verifier said *affected* but its quote didn't match the sent text verbatim. The grounding rule then routes the item to `needs_review` instead of *needs correction*. That costs precision of the label, never safety.

**Run note.** The first eval run's final seed step (`retain_batch` of 30 sent answers) exceeded the 300 s client timeout. The server finished it (46 answer memory units present), and the run was resumed on the same bank and DB (`eval_local.py 20261109190940`). Fixes: answers are now retained with `retain_async=True` (an audit record nothing waits on), and the client timeout (600 s) exceeds the server LLM timeout (300 s). Seeding 30 drafts took ≈33 min wall-clock.

## 5. Failure behaviour
| Scenario | How tested | Result |
|---|---|---|
| Hindsight down | unit test, real adapter → closed port; UI `/api/state` health ping | `needs_review`; propose → error; UI shows "Hindsight unreachable" banner |
| Ollama down | see §6 | see §6 |
| Verifier unparseable / exception | unit tests | `needs_review` |
| Ungrounded "affected" | unit tests + eval (6 cases) | `needs_review`, rejected quote shown |
| Double decision / approve unaffected / blank text | unit tests | 409 / 400 / 400 |
| Foreign Host header on GET | curl | 403 |

## 6. Ollama down
_PENDING: run after the demo seed finishes (it would interrupt it)._

## 7. Resources
- Ollama reports 16 GB for qwen3.5:9b with a 4096-token context (MLX, unified memory).
- Hindsight peak RSS is 752 MB.
- System free memory was 19% during inference.
- Disk: Hindsight venv 2.1 GB, HF models 724 MB, pg0 123 MB, qwen3.5:9b 7.6 GB.
- Practical consequence: one generation at a time. Do not run the eval and a demo seed at once.

## Limits
- One synthetic dataset and one model, so this is a mechanism test. LLM verdicts vary between runs.
- Latency is tens of seconds per `reflect` on a laptop, so a full seed takes about half an hour. The demo uses a pre-seeded bank, which persists across restarts.
- No stateless/RAG baseline was re-run locally. The Cloud-era baseline numbers in `MEMORY_PROOF.md` used a different model and are **not** comparable to these.
