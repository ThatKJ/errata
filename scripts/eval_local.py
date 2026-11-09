"""Ground-truth evaluation of the REAL app pipeline (core.Errata) against a real Hindsight server.
SYNTHETIC data (errata_app/seed_data.py): 30 sent answers, 4 changes, 12 gold-affected (answer, change) pairs, 3 traps.
Fresh isolated bank (errata-eval-*). For each change: propose (recall suggestion recorded) -> apply to the GOLD fact -> verdicts.
Run: uv run python scripts/eval_local.py      Writes results/local/eval_local.json
"""
import json, os, sys, time
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from errata_app import core
from errata_app.seed_data import FACTS, QUESTIONS, CHANGES

URL = os.environ.get("HINDSIGHT_BASE_URL", "http://127.0.0.1:8888")
TRAPS = {"Q03", "Q07", "Q10"}
# Resume: `eval_local.py <stamp>` reuses an already-seeded bank + db (all answers drafted) and runs only the changes.
stamp = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
os.makedirs("results/local", exist_ok=True)
e = core.Errata(core.LiveHindsight(URL), core.Store(f"results/local/eval-{stamp}.db"), f"errata-eval-{stamp}", FACTS, QUESTIONS)
out = {"bank": e.bank, "hindsight": URL, "model": os.environ.get("ERRATA_LLM", "qwen3.5:9b"), "started": core.now(), "rows": [], "mapping": []}

if len(sys.argv) > 1:
    assert all(a["status"] == "sent" for a in e.store.answers()) and len(e.store.answers()) == len(QUESTIONS), "bank not fully seeded"
    out["resumed_from_existing_seed"] = True
else:
    t = time.time(); e.seed(progress=lambda d, n: print(f"seed {d}/{n}", flush=True)); out["seed_s"] = round(time.time() - t, 1)
out["drafted"] = sum(a["status"] == "sent" for a in e.store.answers())
gold = {q[0]: q[4] for q in QUESTIONS}
for eid, fid, note, _v2, date in CHANGES:
    ch = e.propose_change(note, date)
    out["mapping"].append({"change": eid, "gold_fact": fid, "suggested": ch["suggested_fact"], "ranked": ch["ranked_facts"][:5], "recall_ms": ch["recall_ms"]})
    imp = {i["qid"]: i for i in e.apply_change(ch["id"], fid)}
    for qid in gold:
        i = imp.get(qid)
        out["rows"].append({"change": eid, "fact": fid, "qid": qid, "gold_affected": gold[qid] == eid, "trap": qid in TRAPS and gold[qid] is None and fid in [q[3] for q in QUESTIONS if q[0] == qid][0],
                            "state": i["verdict"] if i else "not_candidate", "sources": i["sources"] if i else [], "quoted": i["quoted"] if i else "",
                            "reason": (i["reason"] if i else "")[:300], "verify_ms": e.store.x("select verify_ms from impacts where change_id=? and qid=?", (ch["id"], qid)).fetchone()[0] if i else None})
    print(eid, {q: i["verdict"] for q, i in imp.items()}, flush=True)

R = out["rows"]
P = [r for r in R if r["gold_affected"]]
tp = sum(r["state"] == "affected" for r in P)
fp = sum(r["state"] == "affected" and not r["gold_affected"] for r in R)
s = {"gold_affected_pairs": len(P), "candidates": sum(r["state"] != "not_candidate" for r in R),
     "TP": tp, "FP": fp, "FN": len(P) - tp,
     "TN_candidates": sum(r["state"] == "unaffected" and not r["gold_affected"] for r in R),
     "needs_review": sum(r["state"] == "needs_review" for r in R),
     "gold_routed_to_needs_review": sum(r["state"] == "needs_review" for r in P),
     "false_clear": [f"{r['change']}/{r['qid']}:{r['state']}" for r in P if r["state"] in ("unaffected", "not_candidate")],
     "trap_flagged_affected": [f"{r['change']}/{r['qid']}" for r in R if r["trap"] and r["state"] == "affected"],
     "recall_mapping_correct": sum(m["suggested"] == m["gold_fact"] for m in out["mapping"]),
     "verify_ms_median": sorted(v for v in (r["verify_ms"] for r in R) if v)[len([r for r in R if r["verify_ms"]]) // 2] if any(r["verify_ms"] for r in R) else None}
s["precision"] = round(tp / (tp + fp), 3) if tp + fp else None
s["recall"] = round(tp / len(P), 3)
s["flagged_for_human_recall"] = round(sum(r["state"] in ("affected", "needs_review") for r in P) / len(P), 3)  # 1 - false-clear rate
out["summary"], out["finished"] = s, core.now()
json.dump(out, open("results/local/eval_local.json", "w"), indent=1)
print(json.dumps(s, indent=1))
