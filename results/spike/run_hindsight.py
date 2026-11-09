"""Errata spike — Hindsight arm. Calls the REAL Hindsight Cloud API (hindsight-client 1.2.0 + raw HTTP for PATCH/consolidate/ops).
Writes every response, latency and error to results/hindsight_run.json. Failed calls are recorded, never dropped silently.
Usage: .venv/bin/python run_hindsight.py
"""
import json, os, re, time, urllib.request, urllib.error
from datetime import datetime, timezone
from hindsight_client import Hindsight
from data import FACTS, CHANGES, QUESTIONS, NEW_QUESTIONS

BASE = os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
KEY = dict(l.strip().split("=", 1) for l in open(".env") if "=" in l)["HINDSIGHT_API_KEY"]
BANK = "errata-spike-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
OUT = "results/hindsight_run.json"
os.makedirs("results", exist_ok=True)
R = {"bank": BANK, "base_url": BASE, "started": datetime.now(timezone.utc).isoformat(), "calls": [], "errors": []}
hs = Hindsight(base_url=BASE, api_key=KEY, timeout=180.0)


def save():
    json.dump(R, open(OUT, "w"), indent=2, default=str)


def timed(_op, fn, *a, **k):
    t = time.time()
    try:
        res = fn(*a, **k)
        R["calls"].append({"op": _op, "ms": round((time.time() - t) * 1000), "ok": True})
        return res
    except Exception as e:  # record, never swallow silently
        R["calls"].append({"op": _op, "ms": round((time.time() - t) * 1000), "ok": False})
        R["errors"].append({"op": _op, "error": repr(e)[:500]})
        save()
        return None


def http(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read() or b"{}")


def dump(obj):
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj


def wait_idle(limit=240):
    t = time.time()
    while time.time() - t < limit:
        ops = timed("list_operations", http, "GET", f"/v1/default/banks/{BANK}/operations") or {}
        items = ops.get("operations", ops.get("items", []))
        if not [o for o in items if str(o.get("status", "")).lower() in ("pending", "running", "processing", "queued")]:
            return round(time.time() - t, 1)
        time.sleep(3)
    R["errors"].append({"op": "wait_idle", "error": f"operations not idle after {limit}s"})
    return None


def cited(based_on):
    """Return list of {id,type,document_id,tags} for every memory reflect says it used."""
    mems = (based_on or {}).get("memories") or []
    return [{"id": m.get("id"), "type": m.get("type"), "document_id": m.get("document_id"), "tags": m.get("tags"), "text": (m.get("text") or "")[:200]} for m in mems]


# ---- 0. version + bank -------------------------------------------------------
R["server_version"] = dump(timed("get_version", hs.get_version))
timed("create_bank", hs.create_bank, BANK, name="Errata spike (SYNTHETIC)",
      mission="You are Kestrel Ledger's RFP and security-questionnaire assistant. Answer strictly from Kestrel Ledger product facts.",
      reflect_mission="Answer customer RFP/security questions in 1-3 sentences using only Kestrel Ledger product facts. Never invent facts.",
      disposition_literalism=5, disposition_skepticism=4)
save()

# ---- 1. retain 20 versioned facts --------------------------------------------
items = [{"content": text, "document_id": f"fact:{fid}:v1", "tags": ["kind:fact", f"fact:{fid}"], "timestamp": "2026-08-01T00:00:00Z",
          "context": "Kestrel Ledger authoritative product fact sheet (SYNTHETIC)", "metadata": {"fact_id": fid, "version": "v1"}}
         for fid, (_, text) in FACTS.items()]
R["retain_facts"] = dump(timed("retain_batch_facts", hs.retain_batch, BANK, items))
R["idle_after_facts_s"] = wait_idle()
save()

# ---- 2. draft & 'send' 30 answers via reflect (provenance captured from based_on) ----
R["answers"] = {}
for qid, deal, q, deps, aff in QUESTIONS:
    res = timed(f"reflect_draft_{qid}", hs.reflect, BANK, f"Customer {deal} asks: {q}", budget="low", include_facts=True,
                tags=["kind:fact"], tags_match="any_strict")
    d = dump(res) if res else None
    R["answers"][qid] = {"text": d and d.get("text"), "cited": cited(d and d.get("based_on")), "usage": d and d.get("usage"), "failed": res is None}
    save()

# retain sent answers as experiences, with the app-recorded provenance in tags + metadata
ans_items = []
for qid, deal, q, deps, aff in QUESTIONS:
    a = R["answers"][qid]
    facts = sorted({t.split(":", 1)[1] for c in a["cited"] for t in (c["tags"] or []) if t.startswith("fact:")})
    a["recorded_facts"] = facts
    if a["text"]:
        ans_items.append({"content": f"Answer {qid} sent to {deal} on 2026-10-20. Question: {q} Our answer: {a['text']}",
                          "document_id": f"answer:{qid}", "timestamp": "2026-10-20T00:00:00Z", "tags": ["kind:answer"] + [f"cites:{f}" for f in facts],
                          "context": f"RFP answer already sent to customer {deal}", "metadata": {"qid": qid, "cites": ",".join(facts)}})
R["retain_answers"] = dump(timed("retain_batch_answers", hs.retain_batch, BANK, ans_items))
R["idle_after_answers_s"] = wait_idle()
save()

# ---- 3. change events ----------------------------------------------------------
R["changes"] = {}
for eid, fid, note, v2, date in CHANGES:
    ch = {}
    ch["retain_note"] = dump(timed(f"retain_note_{eid}", hs.retain, BANK, note, document_id=f"change:{eid}", tags=["kind:change"],
                                   timestamp=f"{date}T09:00:00Z", context="Internal change announcement (SYNTHETIC)"))
    # (a) map free-text note -> superseded fact with recall over CURRENT facts
    rec = timed(f"recall_map_{eid}", hs.recall, BANK, note, types=["world"], budget="low", tags=["kind:fact"], tags_match="any_strict", max_tokens=1024)
    hits = [dump(x) for x in (rec.results if rec else [])]
    ch["recall_hits"] = [{"document_id": h.get("document_id"), "tags": h.get("tags"), "text": (h.get("text") or "")[:160]} for h in hits[:5]]
    first = next((t.split(":", 1)[1] for h in hits for t in (h.get("tags") or []) if t.startswith("fact:")), None)
    ch["mapped_fact"] = first
    # (b) Errata sweep #2: reflect over the sent-answer memories
    sweep = timed(f"reflect_sweep_{eid}", hs.reflect, BANK,
                  f"This change was just announced: \"{note}\" Which answers we ALREADY SENT to customers (IDs like Q05) are now false or materially incomplete because of this change? Only list answers whose claim is contradicted.",
                  budget="mid", include_facts=True, tags=["kind:answer"], tags_match="any_strict",
                  response_schema={"type": "object", "properties": {"affected_answer_ids": {"type": "array", "items": {"type": "string"}}}, "required": ["affected_answer_ids"]})
    sd = dump(sweep) if sweep else {}
    ch["sweep"] = {"structured": sd.get("structured_output"), "text": sd.get("text"), "cited": cited(sd.get("based_on")), "usage": sd.get("usage"), "failed": sweep is None}
    # (c) invalidate v1 fact memories, retain v2 (versioned id; never upsert the same document_id)
    lst = timed(f"list_v1_{eid}", hs.list_memories, BANK, document_id=f"fact:{fid}:v1", limit=50)
    mem_ids = [m.get("id") for m in (dump(lst).get("items", []) if lst else [])]
    ch["invalidated"] = []
    for mid in mem_ids:
        r = timed(f"invalidate_{eid}", http, "PATCH", f"/v1/default/banks/{BANK}/memories/{mid}", {"state": "invalidated", "reason": f"superseded by {eid}: {note[:120]}"})
        ch["invalidated"].append({"id": mid, "ok": r is not None})
    ch["retain_v2"] = dump(timed(f"retain_v2_{eid}", hs.retain, BANK, v2, document_id=f"fact:{fid}:v2", tags=["kind:fact", f"fact:{fid}"],
                                 timestamp=f"{date}T10:00:00Z", context="Kestrel Ledger authoritative product fact sheet (SYNTHETIC)",
                                 metadata={"fact_id": fid, "version": "v2"}))
    R["changes"][eid] = ch
    save()

R["consolidate"] = timed("consolidate", http, "POST", f"/v1/default/banks/{BANK}/consolidate", {})
R["idle_after_changes_s"] = wait_idle()
save()

# ---- 4. superseded-fact test on new questions ---------------------------------
R["new_answers"] = {}
for nid, q, new, stale in NEW_QUESTIONS:
    out = {}
    for arm, kw in [("H_facts", {"tags": ["kind:fact"], "tags_match": "any_strict"}), ("H_all", {})]:
        res = timed(f"reflect_new_{arm}_{nid}", hs.reflect, BANK, f"A customer asks: {q}", budget="low", include_facts=True, **kw)
        d = dump(res) if res else {}
        out[arm] = {"text": d.get("text"), "cited": cited(d.get("based_on")), "usage": d.get("usage"), "failed": res is None}
    R["new_answers"][nid] = out
    save()

R["finished"] = datetime.now(timezone.utc).isoformat()
save()
print(json.dumps({"bank": BANK, "errors": len(R["errors"]), "calls": len(R["calls"])}, indent=1))
