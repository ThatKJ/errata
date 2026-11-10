# Release claims registry

Every number used in the README, article, social posts or video, reconciled against the raw file on 2026-11-10. All data is synthetic (fictional company "Kestrel Ledger").

| Claim | Value | Numerator / denominator | Method and model | Source |
|---|---|---|---|---|
| Stale answers silently cleared | 0 / 12 (both runs) | 12 gold (answer, change) pairs: run 2 → 6 `affected`, 6 `needs_review`, 0 `unaffected` / not candidate | full app pipeline, local Hindsight 1.2.0 + Ollama `qwen3.5:9b`, labels fixed before any run | `results/local/eval_local.json` (run 2, finished 2026-11-09T21:41:45Z), `results/local/eval_local_run1.json` |
| Precision of `needs correction` (`affected`) | 0.545 | TP 6 / (TP 6 + FP 5) | same run 2 | same; FP analysis in `docs/LOCAL_VALIDATION_REPORT.md` §4 |
| Recall of `affected` (verifier recall) | 0.50 | TP 6 / 12 gold | same run 2. Not the candidate recall: all 12 gold pairs were candidates | same |
| Gold pairs routed to a human | 12 / 12 | (affected + needs_review) / 12 | same run 2 | same |
| "4 of 5 false alarms quote a really stale sentence" | 4 / 5 | manual reading of the 5 FP quotes; strict labels kept as the reported result | human review | `docs/LOCAL_VALIDATION_REPORT.md` §4 |
| Change note → fact (recall top-1) | 4 / 4 | E1→F01, E2→F03, E3→F06, E4→F08 | Hindsight `recall`, local | `eval_local.json` `mapping` |
| Verification latency | median 38.5 s | per candidate, run 2 (`verify_ms_median` 38459) | laptop, Apple silicon | `eval_local.json` |
| `based_on` citation recall / precision | 1.00 / 0.78 | TP 32, FP 9, FN 0 | earlier **Hindsight Cloud** spike, different model; not comparable to local runs | `docs/MEMORY_PROOF.md`, `results/spike/` |
| Post-change questions answered correctly | Hindsight 8/8, BM25 RAG 4/8, stateless 2/8 | 8 questions | Cloud spike, same answer model per arm. A keyword lookup over the current fact table also scored 8/8 | `results/spike/eval.json` `taskB_summary` |

## Not claimed
- Production readiness, compliance certification, a customer deployment, zero false positives, deterministic verdicts, or any automatic sending. Approved corrections are "approved (not sent)".
- Learning from reviewer feedback: the isolated experiment (`results/local/learn_experiment.json`) recalled one customer's decision for another customer in 1 of 2 runs, so it is not integrated and not claimed.
- Band AI Desktop is a team workflow tool here, not a runtime integration.
