import http.client
import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import server, study


def test_each_participant_gets_all_cards_and_nothing_reveals_the_style_or_the_answer(tmp_path):
    s = study.Study(tmp_path)
    first = s.start()
    assert len(first["cards"]) == 22 and {"participant", "instructions", "cards"} == set(first)
    assert all(set(c) == {"n", "card"} for c in first["cards"]) and [c["n"] for c in first["cards"]] == list(range(1, 23))
    assert "style" not in json.dumps(first).lower() or "agent_card" not in json.dumps(first)
    two, three = s.start(), s.start()
    # rotating the style across the first three participants shows every request in every style once
    seen = {}
    for p in (first, two, three):
        for item in s.sessions[p["participant"]]["items"]:
            seen.setdefault((item["family"], item["ticket"]), []).append(item["style"])
    assert all(sorted(v) == sorted(study.STYLES) for v in seen.values())
    assert [x["card"] for x in s.sessions[first["participant"]]["items"]] != [x["card"] for x in s.sessions[two["participant"]]["items"]]     # each in their own order


def test_answers_are_recorded_once_checked_and_scored_against_the_right_answer(tmp_path):
    s = study.Study(tmp_path)
    p = s.start()["participant"]
    items = s.sessions[p]["items"]
    for bad in (("nobody", 1, "approve", 100), (p, 0, "approve", 100), (p, 23, "approve", 100), (p, 1, "maybe", 100), (p, 1, "approve", -5), (p, 1, "approve", "x"), (p, True, "approve", 1)):
        with pytest.raises(ValueError):
            s.answer(*bad)
    right = lambda it: it["truth"]
    wrong = lambda it: "deny" if it["truth"] == "approve" else "approve"
    assert s.answer(p, 1, right(items[0]), 4000)["recorded"] is True
    assert s.answer(p, 1, wrong(items[0]), 10)["recorded"] is False                       # the first answer to a card stands
    for n in range(2, 6):
        s.answer(p, n, wrong(items[n - 1]), 2000)
    rows = s.rows(p)
    assert len(rows) == 5 and rows[0]["correct"] is True and all(r["correct"] is False for r in rows[1:])
    fin = s.finish(p)
    assert fin["answered"] == 5 and fin["overall"]["n"] == 5 and fin["overall"]["correct"] == 1
    assert sum(v["n"] for v in fin["by_style"].values()) == 5


def test_summary_says_when_there_are_too_few_people_and_sets_models_beside_them(tmp_path):
    s = study.Study(tmp_path)
    p = s.start()["participant"]
    for it in s.sessions[p]["items"]:
        s.answer(p, it["n"], it["truth"], 3000)
    sm = s.summary()
    assert sm["participants"] == 1 and sm["finished"] == 1 and sm["enough"] is False and sm["answers"] == 22
    assert sum(v["n"] for v in sm["by_style"].values()) == 22 and all(v["false_approvals"] == 0 and v["false_denials"] == 0 for v in sm["by_style"].values() if v["n"])
    assert set(sm["models"]) == set(study.STYLES) and sm["models"]["agent_card"]["non_matching"] == 112      # 8 configurations x 14 non-matching cards
    assert sm["models"]["agent_card"]["false_approvals"] == 45


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "STUDY", study.Study(tmp_path))
    srv = server.make_server(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    def call(method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        c.request(method, path, json.dumps(body) if body is not None else None, {"Content-Type": "application/json", **(headers or {})})
        r = c.getresponse()
        data = r.read()
        return r.status, (json.loads(data) if data else None)

    yield call
    srv.shutdown()
    srv.monitor.stop()


def test_the_study_api_runs_a_participant_through_and_keeps_the_runner_protections(api):
    s, d = api("POST", "/api/study/start", {})
    assert s == 201 and len(d["cards"]) == 22
    pid = d["participant"]
    assert api("POST", "/api/study/answer", {"participant": pid, "n": 1, "decision": "deny", "ms": 5000})[1]["recorded"] is True
    assert api("POST", "/api/study/answer", {"participant": "nobody", "n": 1, "decision": "deny", "ms": 5})[0] == 400
    assert api("POST", "/api/study/answer", {"participant": pid, "n": 2, "decision": "approve", "ms": 5}, {"Origin": "http://evil.example"})[0] == 403
    assert api("POST", "/api/study/start", {}, {"Host": "evil.example"})[0] in (403, 404)
    s, fin = api("POST", "/api/study/finish", {"participant": pid})
    assert s == 200 and fin["answered"] == 1
    s, sm = api("GET", "/api/study/summary")
    assert s == 200 and sm["participants"] == 1 and sm["answers"] == 1
