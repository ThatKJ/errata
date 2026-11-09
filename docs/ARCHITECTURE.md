# Errata architecture (as built)

```
Browser (static HTML/JS, no secrets)
   │  JSON over HTTP (127.0.0.1)
   ▼
errata_app/server.py   stdlib ThreadingHTTPServer · input validation · one mutating workflow at a time
   │
   ▼
errata_app/core.py ── Errata engine ──────────────┬──► Hindsight Cloud (hindsight-client 1.2.0 + 1 raw PATCH)
   │                                              │      retain · recall · reflect(based_on, response_schema)
   ▼                                              │      list_memories · PATCH state=invalidated
SQLite audit store (errata.db)                    │
 facts (versions + history) · answers (versions,  │
 cited facts, index deps, evidence) · changes ·   │
 impacts (verdict, sources, evidence, decision) · │
 events                                           │
```

## Who does what
| Concern | Where | Why there |
|---|---|---|
| Fact text, answer text, change notes, human decisions as memory | Hindsight `retain` (`core.py` `seed`, `propose_change`, `apply_change`, `decide`) | Extraction, entity/temporal indexing, consolidation |
| "Which fact does this free-text note change?" | Hindsight `recall` over `kind:fact` memories, ranked (`propose_change`) | Semantic match from untrusted prose. A human confirms the suggestion |
| Drafting answers **and** capturing which facts they used | Hindsight `reflect` with `include_facts`; `based_on.memories` tags → fact ids (`seed`, `facts_from_based_on`) | Provenance comes from the memory system itself, not hand labels |
| Retiring the old fact | `PATCH /memories/{id} {state: invalidated, reason}` on every memory of `fact:Fxx:vN`; new text retained as `fact:Fxx:vN+1` (`apply_change`) | Versioned document IDs. We never upsert the same ID, because upserting deletes the memories that earlier `based_on` citations point to |
| Is a sent answer now wrong? | Hindsight `reflect` scoped to `fact:Fxx`, with `response_schema` {status, reason, corrected_answer} (`_verify`) | Judged against the *current* fact, with the invalidated version excluded from recall |
| Candidate selection | `hindsight_citation` ∪ `dependency_index` (keyword rules on the question) | `based_on` is not a complete dependency graph, so a deterministic index backs it up |
| Answer versions, approvals, audit | SQLite (`Store`) | Exact, queryable state. Memory is not a system of record |
| Human approval | `decide` → answer v+1, status "correction approved (not sent)", decision retained as an experience | No autonomous outbound action exists in the code |

## Failure behaviour (tested in `tests/test_core.py` with a fake client)
- A verification call fails, or returns an unparseable verdict → `needs_review`. The verdict is never silently "unaffected".
- A missing original answer text → `needs_review`.
- Deciding twice → 409 `Conflict`.
- An empty or oversized change note → 400.
- No API key → 503 with an explicit message. The UI shows a banner, and no data is faked.

## Band
Band Desktop is used for the team's agent review workflow, not in Errata's runtime. See `BAND_USAGE.md`.
