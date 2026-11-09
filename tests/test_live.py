"""LIVE integration tests against a REAL Hindsight server (default: local open-source server on :8888 + Ollama).
Start it first: scripts/hindsight-local.sh start.  Run: ERRATA_REQUIRE_LIVE=1 uv run pytest -m live -v -s
Without a reachable server these tests are SKIPPED (reported), or FAIL when ERRATA_REQUIRE_LIVE=1. Never faked.
Each run uses a fresh isolated bank (errata-test-*), never the demo bank.
"""
import os, time, urllib.request
from datetime import datetime, timezone
import pytest
from errata_app import core
from errata_app.seed_data import FACTS, QUESTIONS

URL = os.environ.get("HINDSIGHT_BASE_URL", "http://127.0.0.1:8888")
KEY = os.environ.get("HINDSIGHT_API_KEY") or None


def _up():
    try:
        return urllib.request.urlopen(URL + "/health", timeout=3).status == 200
    except Exception:
        return False


pytestmark = [pytest.mark.live]
if not _up():
    if os.environ.get("ERRATA_REQUIRE_LIVE"):
        raise RuntimeError(f"ERRATA_REQUIRE_LIVE=1 but Hindsight is not reachable at {URL}")
    pytestmark.append(pytest.mark.skip(reason=f"Hindsight not reachable at {URL} — live tests NOT run"))

SLICE = [q for q in QUESTIONS if q[0] in ("Q01", "Q03", "Q04", "Q22")]  # 2 affected by E1, 1 trap (Q03), 1 unrelated (Q04)
E1 = "Ops update Nov 3: our Mumbai region (AWS ap-south-1) is now GA. New Indian customers' data is stored and processed in India by default; us-east-1 is no longer the only region."


def test_live_change_flags_affected_keeps_trap_and_unrelated(tmp_path):
    hs = core.LiveHindsight(URL, KEY)
    bank = "errata-test-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    e = core.Errata(hs, core.Store(str(tmp_path / "live.db")), bank, FACTS, SLICE)
    t = time.time(); e.seed(); print(f"seed {time.time() - t:.1f}s (4 reflect drafts + 2 retain batches)")
    for a in e.store.answers():
        print(a["qid"], "cited:", a["cited_facts"], "|", a["text"][:120].replace("\n", " "))
        assert a["status"] == "sent" and a["text"], f"{a['qid']} draft failed: {a['status']}"
    ch = e.propose_change(E1, "2026-11-03")
    print("recall ranked:", ch["ranked_facts"][:5], f"{ch['recall_ms']} ms")
    assert ch["suggested_fact"] == "F01", "recall did not map the residency change to F01"
    t = time.time()
    impacts = {i["qid"]: i for i in e.apply_change(ch["id"], "F01")}
    print(f"apply_change {time.time() - t:.1f}s:"); [print(" ", q, i["verdict"], i["sources"], "|", i["reason"][:200]) for q, i in impacts.items()]
    # old fact version must be invalidated in memory, new version live
    gone = hs.list_memories(bank, document_id="fact:F01:v1", state="invalidated", limit=50)["items"]
    live = hs.list_memories(bank, document_id="fact:F01:v1", state="valid", limit=50)["items"]
    print("fact:F01:v1 invalidated:", len(gone), "still valid:", len(live), "| reason:", (gone[0].get("invalidation_reason") or "")[:80] if gone else None)
    assert gone and not live, "old fact version was not invalidated in Hindsight"
    assert hs.list_memories(bank, document_id="fact:F01:v2", state="valid", limit=50)["items"], "new fact version not live"
    if "Q04" in impacts:  # backups answer: may be a candidate (index, or an over-broad local citation), must not be judged affected
        print("Q04 sources:", impacts["Q04"]["sources"], "verdict:", impacts["Q04"]["verdict"])
        assert impacts["Q04"]["verdict"] != "affected", "backups answer (unrelated to residency) flagged affected"
    for q in ("Q01", "Q22"):  # affected must be grounded in a quote of the sent text, or honestly needs_review
        i = impacts[q]
        assert i["verdict"] in ("affected", "needs_review"), f"{q} silently cleared: {i['reason']}"
        if i["verdict"] == "affected":
            assert core.norm(i["quoted"]) in core.norm(e.store.answer(q)["text"])
    assert impacts["Q03"]["verdict"] in ("unaffected", "needs_review"), "trap answer (US customer, still true) was flagged affected"
    e.decide(ch["id"], "Q01", "approve", reviewer="live-test", text=impacts["Q01"]["draft"] or "Data can be hosted in Mumbai (ap-south-1).")
    reopened = core.Store(e.store.path)
    assert reopened.answer("Q01")["version"] == 2 and reopened.answer("Q01")["status"] == "correction approved (not sent)"
    mem = (hs.list_memories(bank, document_id="answer:Q01:v2", limit=10) or {}).get("items") or []
    assert mem, "approved correction was not retained into Hindsight"


def test_adapter_works_across_threads():
    """The server calls Hindsight from different threads (seed thread, request threads). hindsight-client's sync
    wrapper binds its aiohttp session to one event loop, so a shared client failed in the 2nd thread (found live)."""
    import threading
    hs, errs = core.LiveHindsight(URL, KEY), []
    hs.create_bank("errata-test-threads", name="thread check (no data)")
    hs.list_memories("errata-test-threads", limit=1)

    def other():
        try:
            hs.list_memories("errata-test-threads", limit=1)
        except Exception as e:
            errs.append(repr(e))
    t = threading.Thread(target=other); t.start(); t.join()
    assert not errs, errs
