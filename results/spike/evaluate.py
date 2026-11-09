"""Errata spike — baselines (stateless LLM, plain BM25 RAG, deterministic dependency index) + scoring.
Reads results/hindsight_run.json (real Hindsight outputs). Baseline LLM = local Ollama qwen3.5:9b, temperature 0, think off.
All arms' Task-A candidates pass through the SAME local verifier, so arms differ only in candidate generation.
Usage: .venv/bin/python evaluate.py [--selftest]
"""
import json, math, re, sys, time, urllib.request
from collections import Counter
from data import FACTS, CHANGES, QUESTIONS, NEW_QUESTIONS, AFFECTED, GOLD_DEPS, TRAPS

MODEL = "qwen3.5:9b"
CHG = {e[0]: e for e in CHANGES}
QS = {q[0]: q for q in QUESTIONS}

# Deterministic keyword index (D). Written BEFORE any run; not tuned afterwards.
KW = {"F01": ["hosted", "hosting", "region", "stored", "data remain", "india", "united states", "asia-pacific"], "F02": ["backup"],
      "F03": ["third part", "subprocessor", "analytics", "vendor", "billing", "companies"], "F04": ["at rest"], "F05": ["in transit"],
      "F06": ["soc 2", "audit scope", "mobile"], "F07": ["iso"], "F08": ["delet", "terminat", "contract ends", "erase", "offboard"],
      "F09": ["sso", "single sign"], "F10": ["multi-factor", "mfa"], "F11": ["uptime", "sla"], "F12": ["rto", "rpo"], "F13": ["penetration"],
      "F14": ["breach"], "F15": ["support hours"], "F16": ["rate limit"], "F17": ["export"], "F18": ["audit log"], "F19": ["pric"], "F20": ["gdpr", "dpa"]}


def kw_deps(text):
    t = text.lower()
    return sorted(f for f, ws in KW.items() if any(w in t for w in ws))


def prf(pred, gold):
    pred, gold = set(pred), set(gold)
    tp = len(pred & gold)
    return {"tp": tp, "fp": len(pred - gold), "fn": len(gold - pred),
            "precision": round(tp / len(pred), 3) if pred else None, "recall": round(tp / len(gold), 3) if gold else None}


def judge(text, new, stale):
    t = (text or "").lower()
    n, s = any(w in t for w in new), any(w in t for w in stale)
    return "correct" if n and not s else "superseded" if s and not n else "mixed" if n and s else "missing/other"


def bm25(query, docs, k=10):
    tok = lambda s: re.findall(r"[a-z0-9\-]+", s.lower())
    D = [tok(d) for d in docs]; avg = sum(map(len, D)) / len(D); N = len(D)
    df = Counter(w for d in D for w in set(d))
    def score(d):
        tf = Counter(d)
        return sum(math.log(1 + (N - df[w] + .5) / (df[w] + .5)) * tf[w] * 2.2 / (tf[w] + 1.2 * (.25 + .75 * len(d) / avg)) for w in tok(query) if w in tf)
    return sorted(range(N), key=lambda i: -score(D[i]))[:k]


def llm(prompt, fmt=None):
    body = {"model": MODEL, "think": False, "stream": False, "options": {"temperature": 0}, "messages": [{"role": "user", "content": prompt}]}
    if fmt: body["format"] = fmt
    t = time.time()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=300).read())["message"]["content"]
    return out, round((time.time() - t) * 1000)


def verify(answer_text, note):
    out, ms = llm(f"A company previously sent this answer to a customer:\n\"{answer_text}\"\n\nThis change was then announced:\n\"{note}\"\n\n"
                  "Is the previously sent answer now FALSE or MATERIALLY INCOMPLETE because of the change? Answer JSON {\"affected\": true|false}.", "json")
    try: return bool(json.loads(out).get("affected")), ms
    except Exception: return None, ms  # recorded as an explicit failure, not as 'not affected'


def selftest():
    assert prf(["Q1", "Q2"], ["Q2", "Q3"]) == {"tp": 1, "fp": 1, "fn": 1, "precision": 0.5, "recall": 0.5}
    assert judge("Data is deleted within 180 days", ["180"], ["90 days"]) == "correct"
    assert judge("within 90 days", ["180"], ["90 days"]) == "superseded"
    assert kw_deps("Where are backups stored?") == ["F01", "F02"]
    assert bm25("snowflake analytics", ["no match here", "snowflake analytics vendor"], k=1) == [1]
    assert sum(1 for v in AFFECTED.values() if v) == 12 and len(QUESTIONS) == 30 and len(FACTS) == 20 and len(CHANGES) == 4
    print("selftest ok")


def main():
    H = json.load(open("results/hindsight_run.json"))
    ans = H["answers"]
    sent = {q: f"Question: {QS[q][2]} Answer: {ans[q]['text'] or ''}" for q in QS}
    E = {"phase2": {}, "taskA": {}, "taskB": {}, "latency_ms": {}, "llm_failures": []}

    # ---------------- Phase 2: provenance (A cited vs B gold vs C recorded) ----------------
    rows = []
    for q in QS:
        A = ans[q].get("recorded_facts") or []
        C_kw = kw_deps(QS[q][2])
        rows.append({"qid": q, "gold_B": GOLD_DEPS[q], "cited_A": A, "keyword_C": C_kw, "failed": ans[q].get("failed"),
                     "cited_doc_ids": [c["document_id"] for c in ans[q]["cited"]], "cited_types": [c["type"] for c in ans[q]["cited"]]})
    def micro(key):
        tp = sum(len(set(r[key]) & set(r["gold_B"])) for r in rows); fp = sum(len(set(r[key]) - set(r["gold_B"])) for r in rows)
        fn = sum(len(set(r["gold_B"]) - set(r[key])) for r in rows)
        return {"precision": round(tp / (tp + fp), 3) if tp + fp else None, "recall": round(tp / (tp + fn), 3) if tp + fn else None, "tp": tp, "fp": fp, "fn": fn}
    E["phase2"] = {"rows": rows, "hindsight_cited_A": micro("cited_A"), "keyword_index_C": micro("keyword_C"),
                   "answers_with_zero_fact_citations": [r["qid"] for r in rows if not r["cited_A"]]}

    # ---------------- Task A: impacted-answer detection ----------------
    gold_by_e = {e: sorted(q for q, a in AFFECTED.items() if a == e) for e in CHG}
    cands = {}
    for e, (_, fid, note, v2, _) in CHG.items():
        ch = H["changes"][e]
        mapped = ch.get("mapped_fact")
        cands[e] = {
            "H1_provenance(mapped by recall)": sorted(q for q in QS if mapped and mapped in (ans[q].get("recorded_facts") or [])),
            "H1_provenance(oracle mapping)": sorted(q for q in QS if fid in (ans[q].get("recorded_facts") or [])),
            "H2_reflect_sweep": sorted({x.strip().upper() for x in ((ch["sweep"].get("structured") or {}).get("affected_answer_ids") or []) if x.strip().upper() in QS}),
            "D_keyword_index": sorted(q for q in QS if fid in kw_deps(QS[q][2])),
            "D_oracle_manual_table": sorted(q for q in QS if fid in GOLD_DEPS[q]),
            "B_rag_bm25_top10": sorted(list(sent)[i] for i in bm25(note, list(sent.values()), k=10)),
        }
        E["taskA"].setdefault("mapping", {})[e] = {"true_fact": fid, "recall_mapped_fact": mapped, "correct": mapped == fid}
    vcache = {}
    for e in CHG:
        for arm, cs in cands[e].items():
            final = []
            for q in cs:
                if (q, e) not in vcache:
                    vcache[(q, e)] = verify(ans[q]["text"] or "", CHG[e][2])
                    E["latency_ms"].setdefault("qwen_verify", []).append(vcache[(q, e)][1])
                    if vcache[(q, e)][0] is None: E["llm_failures"].append(f"verify {q} {e}")
                if vcache[(q, e)][0]: final.append(q)
            E["taskA"].setdefault(arm, {})[e] = {"candidates": cs, "after_verify": final}
    arms = list(cands["E1"].keys())
    summary = {}
    for arm in arms:
        cand = [(e, q) for e in CHG for q in E["taskA"][arm][e]["candidates"]]
        fin = [(e, q) for e in CHG for q in E["taskA"][arm][e]["after_verify"]]
        gold = [(e, q) for e in CHG for q in gold_by_e[e]]
        summary[arm] = {"candidate_stage": prf(cand, gold), "after_verify": prf(fin, gold),
                        "false_negatives_after_verify": sorted(f"{q}/{e}" for e, q in set(gold) - set(fin)),
                        "trap_false_positives_after_verify": sorted(f"{q}/{e}" for e, q in set(fin) - set(gold) if q in TRAPS)}
    summary["A_stateless"] = "N/A: a stateless LLM has no record of what was sent, so recall is 0 by construction"
    E["taskA"]["summary"] = summary
    E["taskA"]["gold"] = gold_by_e

    # ---------------- Task B: superseded-fact usage on new questions ----------------
    corpus = [f"FACT {f} v1: {t}" for f, (_, t) in FACTS.items()] + [f"FACT {c[1]} v2: {c[3]}" for c in CHANGES] + \
             [f"CHANGE {c[0]}: {c[2]}" for c in CHANGES] + list(sent.values())
    current = {f: t for f, (_, t) in FACTS.items()}; current.update({c[1]: c[3] for c in CHANGES})
    for nid, q, new, stale in NEW_QUESTIONS:
        r = {}
        txt, ms = llm(f"You are Kestrel Ledger's sales engineer. Customer asks: {q} Answer in 1-3 sentences."); r["A_stateless"] = txt
        E["latency_ms"].setdefault("qwen_answer", []).append(ms)
        ctx = "\n".join(corpus[i] for i in bm25(q, corpus, k=5))
        txt, ms = llm(f"Using ONLY these retrieved Kestrel Ledger documents:\n{ctx}\n\nCustomer asks: {q} Answer in 1-3 sentences."); r["B_rag_bm25"] = txt
        dep = kw_deps(q)
        txt, ms = llm(f"Using ONLY these current Kestrel Ledger facts:\n" + "\n".join(current[f] for f in dep) + f"\n\nCustomer asks: {q} Answer in 1-3 sentences."); r["D_keyword_current_table"] = txt
        for arm in ("H_facts", "H_all"):
            r[f"C_{arm}"] = (H["new_answers"].get(nid, {}).get(arm) or {}).get("text")
        E["taskB"][nid] = {"question": q, "answers": r, "labels": {k: judge(v, new, stale) for k, v in r.items()}}
    E["taskB_summary"] = {arm: dict(Counter(E["taskB"][n]["labels"][arm] for n in E["taskB"])) for arm in E["taskB"]["N1"]["labels"]}

    # ---------------- Hindsight latency/cost ----------------
    by = {}
    for c in H["calls"]:
        k = re.sub(r"_(Q|E|N)\d+$|_(H_facts|H_all)_N\d+$", "", c["op"]); by.setdefault(k, []).append(c["ms"])
    E["hindsight_latency_ms"] = {k: {"n": len(v), "p50": sorted(v)[len(v) // 2], "max": max(v)} for k, v in by.items()}
    E["hindsight_errors"] = H["errors"]
    n_reflect = sum(1 for c in H["calls"] if c["op"].startswith("reflect"))
    E["cost_estimate_usd"] = {"reflect_calls": n_reflect, "reflect_cost_at_$0.05": round(n_reflect * 0.05, 2),
                              "note": "Retain/recall token charges not itemised by the API responses we captured; see raw usage fields. ESTIMATE from published Cloud pricing."}
    json.dump(E, open("results/eval.json", "w"), indent=2, default=str)
    print(json.dumps({"phase2": {k: E["phase2"][k] for k in ("hindsight_cited_A", "keyword_index_C", "answers_with_zero_fact_citations")},
                      "taskA": {a: (s if isinstance(s, str) else {"cand": s["candidate_stage"], "final": s["after_verify"]}) for a, s in summary.items()},
                      "mapping": E["taskA"]["mapping"], "taskB": E["taskB_summary"], "errors": len(H["errors"]), "llm_failures": E["llm_failures"]}, indent=1))


if __name__ == "__main__":
    selftest()
    if "--selftest" not in sys.argv:
        main()
