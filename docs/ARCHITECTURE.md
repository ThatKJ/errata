# Errata architecture (as built)

```
Browser (static HTML/JS, no secrets)
   │  JSON over HTTP (127.0.0.1)
   ▼
errata_app/server.py   stdlib ThreadingHTTPServer · input validation · one mutating workflow at a time
                       apply = supersede (sync, no LLM) + background verify job (one reflect per candidate, each verdict persisted)
                       GET …/evidence = stored rows + live list_memories (ids, state, invalidation reason), no LLM
   │
   ▼
errata_app/core.py ── Errata engine ──────────────┬──► local Hindsight server 1.2.0 (127.0.0.1:8888, open source)
   │                                              │      retain · recall · reflect(based_on, response_schema)
   ▼                                              │      list_memories · PATCH state=invalidated
SQLite audit store (errata-local.db)              │        ├─ embedded PostgreSQL + pgvector (pg0) — memory persists on disk
                                                  │        ├─ local embeddings + reranker (sentence-transformers)
                                                  │        └─► Ollama 127.0.0.1:11434 · qwen3.5:9b (thinking off)
 facts (versions + history) · answers (versions,  │
 cited facts, index deps, evidence) · changes ·   │
 impacts (verdict, sources, evidence, decision) · │
 events                                           │
```

No Docker, no Cloud, no API key, no paid service. `scripts/hindsight-local.sh start|stop|status` runs the server; the same adapter (`core.LiveHindsight`) also works against Hindsight Cloud if `HINDSIGHT_BASE_URL` and `HINDSIGHT_API_KEY` point there. Observations/mental models are disabled (`HINDSIGHT_API_ENABLE_OBSERVATIONS=false`); Errata does not use them.

## Who does what
| Concern | Where | Why there |
|---|---|---|
| Fact text, answer text, change notes, human decisions as memory | Hindsight `retain` (`core.py` `seed`, `propose_change`, `apply_change`, `decide`) | Extraction, entity/temporal indexing, consolidation |
| "Which fact does this free-text note change?" | Hindsight `recall` over `kind:fact` memories, ranked (`propose_change`) | Semantic match from untrusted prose. A human confirms the suggestion |
| Drafting answers **and** capturing which facts they used | Hindsight `reflect` with `include_facts`; `based_on.memories` tags → fact ids (`seed`, `facts_from_based_on`) | Provenance comes from the memory system itself, not hand labels |
| Retiring the old fact | `PATCH /memories/{id} {state: invalidated, reason}` on every memory of `fact:Fxx:vN`; new text retained as `fact:Fxx:vN+1` (`supersede`) | Versioned document IDs. We never upsert the same ID, because upserting deletes the memories that earlier `based_on` citations point to |
| Is a sent answer now wrong? | Hindsight `reflect` scoped to `fact:Fxx`, with `response_schema` {status, false_sentence, reason, corrected_answer} (`verify_pending` → `_verify`, background thread, resumable) | Judged against the *current* fact, with the invalidated version excluded from recall |
| Candidate selection | `hindsight_citation` ∪ `dependency_index` (keyword rules on the question) | `based_on` is not a complete dependency graph, so a deterministic index backs it up |
| Answer versions, approvals, audit | SQLite (`Store`) | Exact, queryable state. Memory is not a system of record |
| Evidence for one (change, answer) pair | `evidence()`: SQLite rows + live `list_memories` for the old/new fact documents and the answer documents | The reviewer sees memory ids, `invalidated` state, reason and time from Hindsight itself, labelled *live*; stored rows labelled *stored*. If Hindsight is down the stored evidence still renders, with that said on screen |
| Human approval | `decide` → answer v+1, status "correction approved (not sent)", decision retained as an experience | No autonomous outbound action exists in the code |

## Failure behaviour (tested in `tests/test_core.py`; connection loss uses the real adapter against a closed port)
- A verification call fails, or returns an unparseable verdict → `needs_review`. The verdict is never silently "unaffected".
- A missing original answer text → `needs_review`.
- Deciding twice → 409 `Conflict`.
- An empty or oversized change note → 400.
- Hindsight unreachable (or Ollama down, which surfaces as a Hindsight error) → verification `needs_review`; change apply → `failed`; HTTP 502 with the upstream error. No data is faked.
- Server restarted mid-verification → the change stays `applying` with the verdicts already persisted; the UI shows *Interrupted, k of n checked* and **Resume checking** verifies only the rest (`POST /api/changes/C/resume`).

## Band
Band Desktop is used for the team's agent review workflow, not in Errata's runtime. See `BAND_USAGE.md`.
