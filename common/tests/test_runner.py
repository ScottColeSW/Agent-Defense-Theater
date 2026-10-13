import http.client
import json
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import harness, models, registry, report
from adt import jobs as jobs_mod
from adt.jobs import Busy, JobManager
from adt.server import make_server


@pytest.fixture
def iso(tmp_path, monkeypatch):
    """Send every throwaway run to a folder owned by the test."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    return tmp_path


def wait(pred, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.05)
    return False


def finished(m, job):
    return wait(lambda: m.get(job["id"])["state"] in ("done", "failed", "cancelled"))


def test_registry_lists_every_built_experiment():
    ts = {t["id"]: t for t in registry.list_tests(refresh=True)}
    assert {"asi03/first-run", "asi03/escalation"} <= set(ts)
    e = ts["asi03/escalation"]
    assert e["cases"] == 61 and len(e["defenses"]) == 6 and e["has_reviewer"] and e["title"] and e["summary"]


def test_scripted_job_runs_to_a_verified_report(iso):
    m = JobManager()
    job = m.submit({"tests": ["asi03/first-run"], "mode": "scripted"})
    assert finished(m, job) and m.get(job["id"])["state"] == "done"
    t = m.get(job["id"])["tests"][0]
    assert t["state"] == "done" and t["done"] == t["total"] == 180 and t["run_id"]
    assert set(t["tally"]) == {"none", "prompt_guard", "scoped_credentials", "prompt_guard+scoped"}
    rep = report.build_report(t["run_id"])
    assert rep["kind"] == "scripted" and rep["integrity"]["ok"] and rep["integrity"]["matches_recorded"]
    assert rep["pass_bar"] is None and "never a result" in rep["label"]       # a scripted run is never scored as a result
    assert len(rep["summary"]) == 4 and len(rep["records"]["rows"]) == 180


def test_live_result_is_refused_without_a_committed_prediction(monkeypatch):
    monkeypatch.setattr(jobs_mod.JobManager, "_ollama_up", staticmethod(lambda: True))
    monkeypatch.setattr(jobs_mod.models, "ollama_models", lambda: [("m", "1B")])
    monkeypatch.setattr(jobs_mod.harness, "check_prereg", lambda *a: (False, "PREREGISTRATION.md is not committed.", {}))
    monkeypatch.setattr(jobs_mod.modelmgr, "preflight", lambda names, host=None: (True, "ok"))
    with pytest.raises(ValueError, match="is refused: .*not committed"):
        JobManager().submit({"tests": ["asi03/first-run"], "mode": "live", "models": ["m"]})
    # an exploratory run does not need one, and says so by name
    monkeypatch.setattr(jobs_mod.JobManager, "_work", lambda self, job: None)
    assert JobManager().submit({"tests": ["asi03/first-run"], "mode": "exploratory", "models": ["m"]})["state"] == "queued"


def test_bad_requests_are_rejected_before_anything_starts(monkeypatch):
    m = JobManager()
    with pytest.raises(ValueError, match="known test"):
        m.submit({"tests": ["asi99/nope"], "mode": "scripted"})
    with pytest.raises(ValueError, match="mode"):
        m.submit({"tests": ["asi03/first-run"], "mode": "reckless"})
    monkeypatch.setattr(jobs_mod.JobManager, "_ollama_up", staticmethod(lambda: True))
    monkeypatch.setattr(jobs_mod.models, "ollama_models", lambda: [("a", "1B")])
    with pytest.raises(ValueError, match="not installed in Ollama: b"):
        m.submit({"tests": ["asi03/first-run"], "mode": "exploratory", "models": ["b"]})
    with pytest.raises(ValueError, match="at least one model"):
        m.submit({"tests": ["asi03/first-run"], "mode": "exploratory", "models": []})
    monkeypatch.setattr(jobs_mod.JobManager, "_ollama_up", staticmethod(lambda: False))
    with pytest.raises(ValueError, match="not reachable"):
        m.submit({"tests": ["asi03/first-run"], "mode": "exploratory", "models": ["a"]})


def _slow(monkeypatch):
    real = models.ScriptedRunner.generate
    monkeypatch.setattr(models.ScriptedRunner, "generate", lambda self, s, u, hint=None: (time.sleep(0.02), real(self, s, u, hint))[1])


def test_cancel_stops_the_run_and_leaves_no_partial_result(iso, monkeypatch):
    _slow(monkeypatch)
    m = JobManager()
    job = m.submit({"tests": ["asi03/escalation"], "mode": "scripted"})
    assert wait(lambda: m.get(job["id"])["tests"][0]["done"] > 5)
    assert m.cancel(job["id"])
    assert finished(m, job) and m.get(job["id"])["state"] == "cancelled"
    assert m.get(job["id"])["tests"][0]["state"] == "cancelled"
    run_id = m.get(job["id"])["tests"][0]["run_id"]
    scripted = list((iso / "adt").glob("asi03-*/scripted/*"))
    assert not [p for p in scripted if run_id in p.name]                    # nothing half-finished is left as a report
    assert [p for p in (iso / "adt" / "aborted").glob("*") if run_id in p.name]
    assert report.find_run(run_id) is None


def test_second_job_is_turned_away_while_one_runs(iso, monkeypatch):
    _slow(monkeypatch)
    m = JobManager()
    job = m.submit({"tests": ["asi03/escalation"], "mode": "scripted"})
    with pytest.raises(Busy):
        m.submit({"tests": ["asi03/first-run"], "mode": "scripted"})
    m.cancel(job["id"])
    assert finished(m, job)


# ---------------- the HTTP API ----------------
@pytest.fixture
def api(iso):
    srv = make_server(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    def call(method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        h = {"Content-Type": "application/json", **(headers or {})}
        c.request(method, path, json.dumps(body) if body is not None else None, h)
        r = c.getresponse()
        data = r.read()
        return r.status, (json.loads(data) if data else None)

    yield call
    srv.shutdown()
    srv.monitor.stop()


def test_api_reads(api):
    s, d = api("GET", "/api/tests")
    assert s == 200 and {t["id"] for t in d["tests"]} >= {"asi03/first-run", "asi03/escalation"}
    s, d = api("GET", "/api/status")
    assert s == 200 and d["runner"] is True and "models" in d and d["max_temp_default"] == 72
    s, d = api("GET", "/api/gpu")
    assert s == 200 and {"temp_c", "history", "max_c", "resume_c", "paused", "cooler_active"} <= set(d)
    assert api("GET", "/api/reports/no-such-run")[0] == 404 and api("GET", "/api/nope")[0] == 404


def test_api_runs_a_scripted_job_and_serves_its_report(api):
    s, job = api("POST", "/api/jobs", {"tests": ["asi03/first-run"], "mode": "scripted"})
    assert s == 201 and job["state"] in ("queued", "running")
    assert wait(lambda: api("GET", f"/api/jobs/{job['id']}")[1]["state"] == "done")
    _, v = api("GET", f"/api/jobs/{job['id']}")
    s, rep = api("GET", f"/api/reports/{v['tests'][0]['run_id']}")
    assert s == 200 and rep["integrity"]["ok"] and rep["kind"] == "scripted"
    assert v["tests"][0]["run_id"] in {r["run_id"] for r in api("GET", "/api/reports")[1]["reports"]}


def test_api_refuses_cross_site_and_malformed_requests(api):
    ok = {"tests": ["asi03/first-run"], "mode": "scripted"}
    assert api("POST", "/api/jobs", ok, {"Origin": "http://evil.example"})[0] == 403          # another site cannot start runs here
    assert api("POST", "/api/jobs", ok, {"Content-Type": "text/plain"})[0] == 415
    assert api("GET", "/api/tests", headers={"Host": "evil.example"})[0] == 403               # DNS rebinding
    s, d = api("POST", "/api/jobs", {"tests": ["asi99/nope"], "mode": "scripted"})
    assert s == 400 and "known test" in d["error"]


# ---------------- memory management ----------------
def _live_ready(monkeypatch, installed=("a",)):
    monkeypatch.setattr(jobs_mod.JobManager, "_ollama_up", staticmethod(lambda: True))
    monkeypatch.setattr(jobs_mod.models, "ollama_models", lambda: [(n, "1B") for n in installed])
    monkeypatch.setattr(jobs_mod.modelmgr, "preflight", lambda names, host=None: (True, "ok"))


def test_a_model_that_will_not_fit_is_refused_before_anything_starts(monkeypatch):
    _live_ready(monkeypatch, ("huge",))
    monkeypatch.setattr(jobs_mod.modelmgr, "preflight", lambda names, host=None: (False, "huge needs about 52.0 GB and would not fit in memory"))
    with pytest.raises(ValueError, match="would not fit"):
        JobManager().submit({"tests": ["asi03/first-run"], "mode": "exploratory", "models": ["huge"]})


def test_a_live_job_starts_and_ends_with_an_empty_gpu_unless_told_not_to(iso, monkeypatch):
    _live_ready(monkeypatch)
    calls = []
    monkeypatch.setattr(jobs_mod.modelmgr, "unload_all", lambda host=None: calls.append(1) or {"unloaded": ["a"], "still_loaded": []})
    monkeypatch.setattr(jobs_mod.JobManager, "_run_test", lambda self, job, t: t.update(state="done"))
    m = JobManager()
    job = m.submit({"tests": ["asi03/first-run"], "mode": "exploratory", "models": ["a"]})
    assert finished(m, job) and len(calls) == 2
    log = " ".join(m.get(job["id"])["log"])
    assert "memory before the run: unloaded a" in log and "memory after the run" in log
    job2 = m.submit({"tests": ["asi03/first-run"], "mode": "exploratory", "models": ["a"], "unload_before": False, "unload_after": False})
    assert finished(m, job2) and len(calls) == 2                                      # opted out, so it did not touch memory
    job3 = m.submit({"tests": ["asi03/first-run"], "mode": "scripted"})
    assert finished(m, job3) and len(calls) == 2                                      # a scripted run uses no model, so never does


def test_api_models_unload_and_plan(api, monkeypatch):
    from adt import server
    fake_cat = {"memory": {"vram": {"name": "GPU", "total": 8 * 2**30, "used": 0, "free": 8 * 2**30}, "ram": None}, "models": [{"name": "m", "class": "gpu"}], "loaded": []}
    monkeypatch.setattr(server.modelmgr, "catalog", lambda: fake_cat)
    monkeypatch.setattr(server.modelmgr, "unload", lambda name: name == "m")
    monkeypatch.setattr(server.modelmgr, "unload_all", lambda: {"unloaded": ["m"], "still_loaded": []})
    monkeypatch.setattr(server.modelmgr, "plan", lambda agents, reviewers: {"ok": True, "agents": agents, "reviewers": reviewers})
    assert api("GET", "/api/models") == (200, fake_cat)
    assert api("POST", "/api/models/unload", {"model": "m"}) == (200, {"unloaded": ["m"], "still_loaded": []})
    assert api("POST", "/api/models/unload", {"model": "stuck"}) == (200, {"unloaded": [], "still_loaded": ["stuck"]})
    assert api("POST", "/api/models/unload", {}) == (200, {"unloaded": ["m"], "still_loaded": []})
    assert api("POST", "/api/models/unload", {"model": 5})[0] == 400
    s, d = api("POST", "/api/plan", {"agents": ["a", 7, "b"], "reviewers": ["r"]})
    assert s == 200 and d["agents"] == ["a", "b"] and d["reviewers"] == ["r"]                    # non-names are dropped
    assert api("POST", "/api/plan", {"agents": ["a"]}, {"Origin": "http://evil.example"})[0] == 403


def test_api_models_says_so_when_ollama_is_down(api, monkeypatch):
    import urllib.error
    from adt import server

    def down():
        raise urllib.error.URLError(ConnectionRefusedError())

    monkeypatch.setattr(server.modelmgr, "catalog", down)
    s, d = api("GET", "/api/models")
    assert s == 503 and "not reachable" in d["error"]
