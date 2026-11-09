"""HTTP-level regression tests for the stdlib server with a FAKE Hindsight (no LLM, no network).
Covers: background verification job (202 + progress), resume rules, evidence endpoint, guards."""
import json, os, threading, time, urllib.request, urllib.error
import pytest


@pytest.fixture(scope="module")
def srv(tmp_path_factory):
    os.environ["ERRATA_DB"] = str(tmp_path_factory.mktemp("db") / "s.db")
    os.environ["HINDSIGHT_BASE_URL"] = "http://127.0.0.1:9"   # closed port: health=False, but the fake never touches it
    os.environ["ERRATA_BANK"] = "test-server-bank"
    from errata_app import core, server
    from tests.test_core import FakeHindsight
    fake = FakeHindsight(verdicts={"Bharat": {"status": "affected", "false_sentence": "Seeded answer.", "reason": "India region", "corrected_answer": "Mumbai available."}})
    server.APP = core.Errata(fake, server.store, server.BANK, server.FACTS, server.QUESTIONS)
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", server
    httpd.shutdown()


def call(base, path, body=None, method=None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"} if body is not None else {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def wait(base, pred, timeout=10):
    t = time.time()
    while time.time() - t < timeout:
        st = call(base, "/api/state")[1]
        if pred(st):
            return st
        time.sleep(0.05)
    raise AssertionError("timed out")


def test_apply_runs_in_background_and_reports_progress(srv):
    base, server = srv
    assert call(base, "/api/seed", {})[0] == 202
    st = wait(base, lambda s: s["seeded_at"] and not s["seed"]["running"])
    assert len(st["answers"]) == 30
    code, ch = call(base, "/api/changes", {"note": "Mumbai region GA", "effective": "2026-11-03"})
    assert code == 200 and ch["status"] == "proposed"
    code, r = call(base, f"/api/changes/{ch['id']}/apply", {"fact_id": "F01"})
    assert code == 202 and r["progress"]["candidates"] > 0
    st = wait(base, lambda s: s["changes"][0]["status"] == "applied")
    c = st["changes"][0]
    assert c["progress"]["verified"] == c["progress"]["candidates"] and c["progress"]["pending"] == []
    assert c["verified_at"] and not c["running"]
    assert {i["verdict"] for i in c["impacts"]} <= {"affected", "unaffected", "needs_review"}
    # the lock was released by the job: another mutation is accepted
    assert call(base, "/api/changes", {"note": "x", "effective": "2026-11-04"})[0] == 200


def test_resume_only_for_interrupted_changes(srv):
    base, server = srv
    cid = call(base, "/api/state")[1]["changes"][-1]["id"]            # C1, applied
    assert call(base, f"/api/changes/{cid}/resume", {})[0] == 409
    assert call(base, "/api/changes/C77/resume", {})[0] == 409


def test_evidence_endpoint(srv):
    base, server = srv
    st = call(base, "/api/state")[1]
    c = st["changes"][-1]
    qid = c["impacts"][0]["qid"]
    code, ev = call(base, f"/api/changes/{c['id']}/impacts/{qid}/evidence")
    assert code == 200 and [s["kind"] for s in ev["timeline"]][:3] == ["fact_retained", "answer_sent", "change_effective"]
    assert ev["live"] is True and ev["provenance"]
    assert call(base, f"/api/changes/{c['id']}/impacts/Q99/evidence")[0] == 404


def test_guards_still_hold(srv):
    base, _ = srv
    req = urllib.request.Request(base + "/api/changes", data=b"note=x", headers={"Content-Type": "text/plain"}, method="POST")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 403
    req = urllib.request.Request(base + "/api/state", headers={"Host": "evil.example"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 403
