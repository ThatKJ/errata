"""Unit tests for Errata's logic. These use FakeHindsight — a recording stub, NOT Hindsight Cloud.
They prove orchestration/bookkeeping logic only. Real-API behaviour is tested in test_cloud_live.py."""
import pytest
from errata_app import core


class FakeHindsight:
    """Records calls; returns canned shapes mirroring hindsight-client 1.2.0 (verified field names)."""
    def __init__(self, verdicts=None, fail_reflect_for=()):
        self.calls, self.verdicts, self.fail_for = [], verdicts or {}, set(fail_reflect_for)

    def create_bank(self, bank_id, **k): self.calls.append(("create_bank", bank_id))
    def retain_batch(self, bank_id, items, **k): self.calls.append(("retain_batch", [i["document_id"] for i in items]))
    def retain(self, bank_id, content, **k): self.calls.append(("retain", k.get("document_id"), k.get("tags")))

    def reflect(self, bank_id, query, **k):
        self.calls.append(("reflect", query[:40], k.get("tags")))
        for marker in self.fail_for:
            if marker in query:
                raise RuntimeError("simulated 500")
        if k.get("response_schema"):
            for marker, v in self.verdicts.items():
                if marker in query:
                    return {"text": "", "structured_output": v, "based_on": {"memories": [{"id": "m9", "document_id": "fact:F01:v2", "tags": ["kind:fact", "fact:F01"], "type": "world", "text": "new"}]}}
            return {"text": "", "structured_output": {"status": "unaffected", "reason": "still true", "corrected_answer": ""}, "based_on": {"memories": []}}
        fid = "F02" if "backup" in query.lower() else "F01"
        return {"text": "Seeded answer.", "based_on": {"memories": [{"id": "m1", "document_id": f"fact:{fid}:v1", "tags": ["kind:fact", f"fact:{fid}"], "type": "world", "text": "old"}]}}

    def recall(self, bank_id, query, **k):
        self.calls.append(("recall", query[:40]))
        return {"results": [{"document_id": "fact:F01:v1", "tags": ["kind:fact", "fact:F01"], "text": "x"},
                            {"document_id": "fact:F02:v1", "tags": ["kind:fact", "fact:F02"], "text": "y"}]}

    def list_memories(self, bank_id, document_id=None, **k):
        return {"items": [{"id": "m1"}, {"id": "m2"}]}

    def invalidate(self, bank_id, memory_id, reason):
        self.calls.append(("invalidate", memory_id))


@pytest.fixture
def app(tmp_path):
    hs = FakeHindsight(verdicts={"Acme": {"status": "affected", "reason": "Mumbai now available", "corrected_answer": "Data can stay in Mumbai."}})
    e = core.Errata(hs, core.Store(str(tmp_path / "t.db")), bank="test-bank",
                    facts={"F01": ("residency", "US only"), "F02": ("backups", "Oregon")},
                    questions=[("Q01", "Acme Fintech (IN)", "Where is our data hosted?", ["F01"], "E1"),
                               ("Q03", "Midwest CU (US)", "Is data stored in the United States?", ["F01"], None),
                               ("Q04", "Bharat MF (IN)", "Where are backups kept?", ["F02"], None)])
    e.seed()
    return e, hs


def test_facts_from_based_on_parses_tags_and_doc_ids():
    mems = [{"tags": ["kind:fact", "fact:F03"]}, {"document_id": "fact:F07:v2", "tags": None}, {"type": "observation", "tags": []}]
    assert core.facts_from_based_on({"memories": mems}) == ["F03", "F07"]


def test_next_doc_id():
    assert core.next_doc_id("fact:F01:v1") == "fact:F01:v2"


def test_seed_records_hindsight_citations_as_provenance(app):
    e, hs = app
    a = e.store.answer("Q01")
    assert a["cited_facts"] == ["F01"] and a["status"] == "sent"
    assert ("retain_batch", ["fact:F01:v1", "fact:F02:v1"]) in hs.calls


def test_change_suggests_fact_from_recall_rank(app):
    e, _ = app
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    assert ch["suggested_fact"] == "F01" and ch["ranked_facts"][:2] == ["F01", "F02"]


def test_apply_invalidates_old_version_and_retains_new(app):
    e, hs = app
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    e.apply_change(ch["id"], "F01")
    assert ("invalidate", "m1") in hs.calls and ("invalidate", "m2") in hs.calls
    assert any(c[0] == "retain" and c[1] == "fact:F01:v2" for c in hs.calls)
    assert e.store.fact("F01")["version"] == 2


def test_candidates_are_union_of_citation_and_index_and_unrelated_untouched(app):
    e, _ = app
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    impacts = {i["qid"]: i for i in e.apply_change(ch["id"], "F01")}
    assert set(impacts) == {"Q01", "Q03"}            # Q04 depends on F02 only -> never a candidate
    assert impacts["Q01"]["verdict"] == "affected"
    assert impacts["Q03"]["verdict"] == "unaffected"  # negative control: depends on F01 but still true
    assert "hindsight_citation" in impacts["Q01"]["sources"]


def test_failed_verification_is_needs_review_never_silently_unaffected(tmp_path):
    hs = FakeHindsight(fail_reflect_for=("Midwest",))
    e = core.Errata(hs, core.Store(str(tmp_path / "t.db")), bank="b", facts={"F01": ("residency", "US only")},
                    questions=[("Q03", "Midwest CU (US)", "Is data stored in the United States?", ["F01"], None)])
    e.seed()  # seed reflect for Q03 fails too -> answer marked draft_failed but still indexed
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    imp = e.apply_change(ch["id"], "F01")[0]
    assert imp["verdict"] == "needs_review" and "failed" in imp["reason"]


def test_decision_is_recorded_once_and_retained_as_experience(app):
    e, hs = app
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    e.apply_change(ch["id"], "F01")
    e.decide(ch["id"], "Q01", "approve", reviewer="SE reviewer", text="Data can stay in Mumbai.")
    assert e.store.answer("Q01")["version"] == 2 and e.store.answer("Q01")["status"] == "correction approved (not sent)"
    assert any(c[0] == "retain" and c[1] == "answer:Q01:v2" for c in hs.calls)
    with pytest.raises(core.Conflict):
        e.decide(ch["id"], "Q01", "approve", reviewer="SE reviewer", text="again")


def test_state_persists_across_store_reopen(app):
    e, _ = app
    ch = e.propose_change("Mumbai region is GA", "2026-11-03")
    e.apply_change(ch["id"], "F01")
    again = core.Store(e.store.path)
    assert again.answer("Q01")["cited_facts"] == ["F01"] and len(again.impacts(ch["id"])) == 2


@pytest.mark.parametrize("note", ["", "   ", "x" * 5001])
def test_change_note_validated(app, note):
    e, _ = app
    with pytest.raises(ValueError):
        e.propose_change(note, "2026-11-03")
