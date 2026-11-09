"""Regression tests for the incremental verification flow (background apply, resume after interruption)
and the evidence time machine. FAKE client (recording stub); see test_live.py for the real server."""
import pytest
from errata_app import core
from tests.test_core import FakeHindsight

Q = [("Q01", "Acme Fintech (IN)", "Where is our data hosted?", ["F01"], "E1"),
     ("Q03", "Midwest CU (US)", "Is data stored in the United States?", ["F01"], None),
     ("Q04", "Bharat MF (IN)", "Where are backups kept?", ["F02"], None)]
F = {"F01": ("residency", "US only"), "F02": ("backups", "Oregon")}
V = {"Acme": {"status": "affected", "false_sentence": "Seeded answer.", "reason": "Mumbai now available", "corrected_answer": "Data can stay in Mumbai."}}


def make(tmp_path, hs=None):
    e = core.Errata(hs or FakeHindsight(verdicts=V), core.Store(str(tmp_path / "t.db")), "b", F, Q)
    e.seed()
    return e


def test_candidates_are_known_before_any_verification(tmp_path):
    e = make(tmp_path)
    c = e.candidates("F01")
    assert [x["qid"] for x in c] == ["Q01", "Q03"] and "hindsight_citation" in c[0]["sources"]
    assert e.candidates("F02") and e.candidates("F02")[0]["qid"] == "Q04"


def test_supersede_then_verify_pending_is_resumable(tmp_path):
    """A crash after some verdicts must not lose them or re-verify them; resume finishes the rest."""
    e = make(tmp_path)
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    e.supersede(ch["id"], "F01")
    assert e.store.change(ch["id"])["status"] == "applying" and e.store.fact("F01")["version"] == 2
    # simulate: first candidate verified, then the process died
    cands = e.candidates("F01")
    e._verify(ch["id"], e.store.change(ch["id"]), "F01", e.store.answer(cands[0]["qid"]), cands[0]["sources"])
    n_reflect = sum(c[0] == "reflect" for c in e.hs.calls)
    out = e.verify_pending(ch["id"])
    assert [i["qid"] for i in out] == ["Q03"]                                   # only the remaining one
    assert sum(c[0] == "reflect" for c in e.hs.calls) == n_reflect + 1
    assert e.store.change(ch["id"])["status"] == "applied"
    assert {i["qid"]: i["verdict"] for i in e.store.impacts(ch["id"])} == {"Q01": "affected", "Q03": "unaffected"}
    assert all(i["verified_at"] for i in e.store.impacts(ch["id"]))


def test_verify_pending_refuses_non_applying_change(tmp_path):
    e = make(tmp_path)
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    with pytest.raises(core.Conflict):
        e.verify_pending(ch["id"])                                               # still 'proposed'
    e.apply_change(ch["id"], "F01")
    with pytest.raises(core.Conflict):
        e.verify_pending(ch["id"])                                               # already 'applied'


def test_apply_change_still_does_both_steps(tmp_path):
    e = make(tmp_path)
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    out = e.apply_change(ch["id"], "F01")
    assert {i["qid"] for i in out} == {"Q01", "Q03"} and e.store.change(ch["id"])["status"] == "applied"


def test_progress_reports_pending_candidates(tmp_path):
    e = make(tmp_path)
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    e.supersede(ch["id"], "F01")
    p = e.progress(ch["id"])
    assert p == {"candidates": 2, "verified": 0, "pending": ["Q01", "Q03"]}
    e.verify_pending(ch["id"])
    assert e.progress(ch["id"]) == {"candidates": 2, "verified": 2, "pending": []}


def test_evidence_timeline_is_built_from_stored_and_live_memory(tmp_path):
    class WithMem(FakeHindsight):
        def list_memories(self, bank_id, document_id=None, state=None, **k):
            if document_id == "fact:F01:v1":
                return {"items": [{"id": "m1", "state": "invalidated", "invalidation_reason": "superseded by change C1", "invalidated_at": "2026-11-09T20:25:15+00:00", "text": "US only"}]} if state != "valid" else {"items": []}
            if document_id == "fact:F01:v2":
                return {"items": [{"id": "m9", "state": "valid", "text": "Mumbai GA"}]}
            if document_id and document_id.startswith("answer:Q01"):
                return {"items": [{"id": "a1", "state": "valid", "text": "Answer Q01 sent"}]}
            return {"items": []}
    e = make(tmp_path, WithMem(verdicts=V))
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    e.apply_change(ch["id"], "F01")
    ev = e.evidence(ch["id"], "Q01")
    kinds = [s["kind"] for s in ev["timeline"]]
    assert kinds == ["fact_retained", "answer_sent", "change_effective", "verified"]
    assert ev["timeline"][2]["invalidated"][0]["invalidation_reason"] == "superseded by change C1"
    assert ev["timeline"][2]["new_version"][0]["id"] == "m9"
    assert ev["quoted"] == "Seeded answer." and ev["quote_found"] is True
    assert ev["provenance"] == ["hindsight_citation", "dependency_index"] and ev["live"] is True
    e.decide(ch["id"], "Q01", "approve", reviewer="r", text="Data can stay in Mumbai.")
    ev = e.evidence(ch["id"], "Q01")
    assert ev["timeline"][-1]["kind"] == "decided" and ev["timeline"][-1]["retained_as"] == "answer:Q01:v2"


def test_evidence_survives_hindsight_outage(tmp_path):
    """Live memory listing is optional: when Hindsight is down the stored evidence is still shown, honestly labelled."""
    e = make(tmp_path)
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    e.apply_change(ch["id"], "F01")
    def boom(*a, **k): raise RuntimeError("connection refused")
    e.hs.list_memories = boom
    ev = e.evidence(ch["id"], "Q01")
    assert ev["live"] is False and "connection refused" in ev["live_error"]
    assert ev["timeline"][2]["invalidated"] is None and len(ev["timeline"]) == 4


def test_evidence_unknown_impact(tmp_path):
    e = make(tmp_path)
    with pytest.raises(ValueError):
        e.evidence("C9", "Q01")
