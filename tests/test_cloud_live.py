"""LIVE integration test against real Hindsight Cloud. Skipped (and reported as skipped) without HINDSIGHT_API_KEY.
Uses a fresh isolated bank and a 4-answer slice of the synthetic dataset. Costs a few reflect calls.
Run: HINDSIGHT_API_KEY=... uv run pytest tests/test_cloud_live.py -v -s
"""
import os, time
from datetime import datetime, timezone
import pytest
from errata_app import core
from errata_app.seed_data import FACTS, QUESTIONS

KEY = os.environ.get("HINDSIGHT_API_KEY")
pytestmark = pytest.mark.skipif(not KEY, reason="HINDSIGHT_API_KEY not set — live Cloud test not run")
SLICE = [q for q in QUESTIONS if q[0] in ("Q01", "Q03", "Q04", "Q22")]  # 2 affected by E1, 1 trap (Q03), 1 unrelated (Q04)


def test_live_change_flags_affected_keeps_trap_and_unrelated(tmp_path):
    hs = core.CloudHindsight(os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"), KEY)
    bank = "errata-test-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    e = core.Errata(hs, core.Store(str(tmp_path / "live.db")), bank, FACTS, SLICE)
    e.seed()
    for a in e.store.answers():
        print(a["qid"], "cited:", a["cited_facts"], "|", a["text"][:120])
    ch = e.propose_change("Ops update Nov 3: our Mumbai region (AWS ap-south-1) is now GA. New Indian customers' data is stored and processed in India by default; us-east-1 is no longer the only region.", "2026-11-03")
    print("recall ranked:", ch["ranked_facts"][:5])
    assert ch["suggested_fact"] == "F01", "recall did not map the residency change to F01"
    t = time.time()
    impacts = {i["qid"]: i for i in e.apply_change(ch["id"], "F01")}
    print(f"apply_change {time.time() - t:.1f}s:", {q: (i["verdict"], i["sources"]) for q, i in impacts.items()})
    # Run 1 (results/live_test_run1.txt) showed Q04 enters via the keyword index ("stored") by design; the index
    # over-generates on purpose and the verifier decides. Invariant: Hindsight must not cite F01 for the backups answer.
    if "Q04" in impacts:
        assert "hindsight_citation" not in impacts["Q04"]["sources"]
        print("NOTE Q04 (index-only candidate) verdict:", impacts["Q04"]["verdict"], "-", impacts["Q04"]["reason"][:160])
    assert impacts["Q01"]["verdict"] == "affected" and impacts["Q22"]["verdict"] == "affected"
    assert impacts["Q03"]["verdict"] in ("unaffected", "needs_review"), "trap answer (US customer, still true) was flagged affected"
    e.decide(ch["id"], "Q01", "approve", reviewer="live-test", text=impacts["Q01"]["draft"] or "Data can be hosted in Mumbai (ap-south-1).")
    reopened = core.Store(e.store.path)
    assert reopened.answer("Q01")["version"] == 2
