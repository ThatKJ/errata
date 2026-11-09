# Memory proof — measured results (real Hindsight Cloud, 2026-11-09)

**Everything here is from real API calls on a SYNTHETIC dataset:** 20 facts, 30 previously sent answers, 4 fact changes, 12 answers truly affected, and 3 "trap" answers that depend on a changed fact but stay true. The ground truth was fixed before any run (`results/spike/data.py`). This is small-n and **not** a production accuracy claim.

Environment:
- Hindsight Cloud `api_version 1.1.0`, `hindsight-client 1.2.0`. Bank `errata-spike-20261109170945`.
- Baseline LLM: local Ollama `qwen3.5:9b`, temperature 0.
- Raw outputs: `results/spike/hindsight_run.json`, `eval.json`, `verify_reflect.json`.

## 1. Hindsight operations worked as documented
| Operation | Result |
|---|---|
| retain (batch) of facts and answers, sync | 0 errors; 7.3 s for 20 facts, 11.5 s for 30 answers |
| `recall` mapping a free-text change note → superseded fact | **4/4 correct** (top-1) |
| `reflect` drafting with `based_on` | 30/30 answers drafted; p50 5.1 s, max 7.1 s |
| `PATCH state=invalidated` on old fact memories | 6/6 succeeded |
| 97 API calls in the spike run | 0 errors |

## 2. Provenance: Hindsight citations vs actual dependencies
| | Precision | Recall | Counts |
|---|---|---|---|
| **A.** facts cited in reflect `based_on` (automatic) | 0.78 | **1.00** | TP 32 · FP 9 · FN 0 |
| **C.** hand-written keyword dependency index | 0.94 | 0.94 | TP 30 · FP 2 · FN 2 |

- `based_on` never missed a true dependency here. It over-cites, mostly through consolidated observations that mention neighbouring facts.
- A keyword index written by someone who knows the fact sheet is more precise but missed 2. The app uses the **union** of the two.

## 3. Finding affected sent answers (same tasks; candidates → same verifier)
**Candidate stage** (TP / FP / FN out of 12):
| Arm | TP | FP | FN |
|---|---|---|---|
| Hindsight `based_on` provenance | 12 | 7 | 0 |
| Hindsight single reflect sweep over sent answers | 11 | 5 | 1 |
| Keyword dependency index | 12 | 4 | 0 |
| Hand-maintained dependency table (ceiling) | 12 | 4 | 0 |
| BM25 retrieval over sent answers (top-10) | 12 | 28 | 0 |
| Stateless LLM | N/A: has no record of what was sent | | |

**After the same local verifier** (qwen3.5:9b): every arm except the sweep reached **TP 10 / FN 2**. The two misses are the SOC 2 mobile-app change (Q09, Q25), and the trap Q03 was flagged by every arm. **The verifier, not candidate generation, is the bottleneck.**

**App verifier (Hindsight reflect + response_schema), partial run:**
- 10 of 20 calls failed with **HTTP 402 (credits exhausted)**. All 10 were correctly recorded as `needs_review`, never as "unaffected".
- **E1 (data residency):**
  - all 3 true positives found;
  - **4 false positives**, including trap Q03 (US customer, still true) and Q04 (backups).
  - The same Q03 was judged *unaffected* in the earlier live test run (`results/live_test_run1.txt`), so **the verdict is not deterministic**.
- **E2 (subprocessor):** Q05 and Q06 correctly affected; trap Q07 correctly unaffected.

## 4. Answering new questions after the changes (superseded-fact usage, 8 questions)
| Arm | Correct | Superseded / mixed | Missing |
|---|---|---|---|
| Hindsight reflect (facts only) | **8** | 0 | 0 |
| Hindsight reflect (all memories, incl. old sent answers) | **8** | 0 | 0 |
| Current fact table (deterministic) | 8 | 0 | 0 |
| BM25 RAG over the same raw documents | 4 | 1 mixed | 3 |
| Stateless LLM | 2 | 1 superseded | 5 |

Even with the old (now wrong) sent answers in the same bank, Hindsight reflect never repeated a superseded value.

## Honest conclusion
- **Where Hindsight carries weight:**
  - Provenance is captured automatically at answer time (recall 1.00, with no hand labelling).
  - Free-text change notes map to the right fact (4/4).
  - Superseded facts stop influencing answers (8/8, vs 4/8 for plain RAG over the same documents).
- **Where it does not, yet:**
  - On this tiny, hand-built fact sheet, a keyword index finds the same candidates.
  - Judging whether an answer is *really* wrong is the hard part. The reflect verifier over-flags, and its verdicts vary between runs.
  - Errata therefore presents verdicts as **triage for a human reviewer**, not as decisions.
