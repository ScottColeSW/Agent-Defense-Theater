import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import modelmgr as mm

GB = mm.GB
MB = 1024 * 1024


def tag(name, gb, params="7B", caps=None):
    d = {"name": name, "size": int(gb * GB), "details": {"parameter_size": params, "quantization_level": "Q4_K_M", "family": "x"}}
    if caps is not None:
        d["capabilities"] = caps
    return d


TAGS = [tag("phi4-mini:3.8b", 2.5, "3.8B"), tag("llama3.1:8b", 4.9, "8B"), tag("qwen2.5:7b", 4.7), tag("big:14b", 9.0, "14B"), tag("huge:70b", 40, "70B"),
        tag("nomic-embed-text:latest", 0.27, "137M"), tag("tagged-embedder", 0.5, caps=["embedding"]), tag("tagged-chat", 1.0, caps=["completion", "tools"])]


@pytest.fixture
def fake(monkeypatch):
    state = {"ps": [], "vram": {"name": "Test GPU", "total": 8192 * MB, "used": 500 * MB, "free": 7692 * MB}, "ram": {"total": 32 * GB, "free": 20 * GB}, "posts": []}

    def get(path, host=mm.HOST, timeout=5):
        return {"models": TAGS} if path == "/api/tags" else {"models": state["ps"]}

    monkeypatch.setattr(mm, "_get", get)
    monkeypatch.setattr(mm, "_post", lambda path, body, host=mm.HOST, timeout=30: state["posts"].append((path, body)) or {})
    monkeypatch.setattr(mm, "vram", lambda: state["vram"])
    monkeypatch.setattr(mm, "ram", lambda: state["ram"])
    monkeypatch.setattr(mm, "_seen", {})
    monkeypatch.setattr(mm.time, "sleep", lambda s: None)
    return state


def test_only_models_that_can_generate_text_are_listed_smallest_first(fake):
    names = [m["name"] for m in mm.installed()]
    assert "nomic-embed-text:latest" not in names and "tagged-embedder" not in names     # embedding-only, by name or by capability
    assert "tagged-chat" in names and names == sorted(names, key=lambda n: next(t["size"] for t in TAGS if t["name"] == n))


def test_fit_gpu_partial_or_no(fake):
    c = {m["name"]: m for m in mm.catalog()["models"]}
    assert c["llama3.1:8b"]["class"] == "gpu" and c["phi4-mini:3.8b"]["class"] == "gpu"
    assert c["big:14b"]["class"] == "partial" and "system RAM" in c["big:14b"]["why"]        # 9 GB x 1.3 is more than the card, less than card + RAM
    assert c["huge:70b"]["class"] == "no"
    assert c["llama3.1:8b"]["basis"] == "estimated" and c["llama3.1:8b"]["need"] == int(4.9 * GB * 1.3)


def test_a_footprint_seen_loaded_replaces_the_estimate(fake):
    fake["ps"] = [{"name": "qwen2.5:7b", "size": int(5.6 * GB), "size_vram": int(5.6 * GB), "expires_at": "x"}]
    c = {m["name"]: m for m in mm.catalog()["models"]}
    assert c["qwen2.5:7b"]["basis"] == "observed" and c["qwen2.5:7b"]["need"] == int(5.6 * GB) and c["qwen2.5:7b"]["resident"]
    fake["ps"] = []
    assert {m["name"]: m for m in mm.catalog()["models"]}["qwen2.5:7b"]["basis"] == "observed"   # remembered after it unloads


def test_simulate_counts_the_swaps_of_a_real_run_order(fake):
    sizes = {"llama": 6.4 * GB, "qwen": 6.1 * GB, "phi": 3.25 * GB}
    # Three agents, each followed by two reviewers, on a card that holds one of the big models at a time.
    seq = ["llama", "qwen", "llama", "qwen", "qwen", "llama", "phi", "qwen", "llama"]
    r = mm.simulate(seq, sizes, 7.6 * GB)
    assert r["load_count"] == 8 and r["loads"][0] == "llama"
    assert r["est_seconds"] == round(sum(sizes[n] for n in r["loads"]) / GB * mm.SECONDS_PER_GB_COLD)
    # On a card that holds them all, each is loaded once.
    assert mm.simulate(seq, sizes, 24 * GB)["load_count"] == 3


def test_plan_warns_about_swaps_and_misfits(fake):
    p = mm.plan(["llama3.1:8b", "qwen2.5:7b", "phi4-mini:3.8b"], ["qwen2.5:7b", "llama3.1:8b"])
    assert p["ok"] and p["load_count"] > 3 and any("swapped" in a for a in p["advice"])
    bad = mm.plan(["huge:70b"], ["qwen2.5:7b"])
    assert not bad["ok"] and any("will not fit" in w for w in bad["warnings"])
    slow = mm.plan(["big:14b"], [])
    assert slow["ok"] and any("system RAM" in w for w in slow["warnings"])
    assert not mm.plan(["nomic-embed-text:latest"], [])["ok"]                             # cannot generate text, so it is not choosable


def test_plan_says_when_everything_fits_together(fake):
    fake["vram"] = {"name": "Big GPU", "total": 48 * 1024 * MB, "used": 0, "free": 48 * 1024 * MB}
    p = mm.plan(["llama3.1:8b", "qwen2.5:7b"], ["qwen2.5:7b"])
    assert any("fit on the GPU together" in a for a in p["advice"]) and p["load_count"] == 2


def test_preflight_refuses_what_will_not_fit(fake):
    assert mm.preflight(["llama3.1:8b", "qwen2.5:7b"]) == (True, "ok")
    ok, msg = mm.preflight(["huge:70b"])
    assert not ok and "would not fit" in msg
    assert not mm.preflight(["not-installed"])[0]


def test_unload_waits_until_the_model_has_really_left(fake, monkeypatch):
    seen = iter([[{"name": "m", "size": 1, "size_vram": 1}], [{"name": "m", "size": 1, "size_vram": 1}], []])
    monkeypatch.setattr(mm, "loaded", lambda host=mm.HOST: next(seen))
    assert mm.unload("m", wait_s=5) is True
    assert fake["posts"][0] == ("/api/generate", {"model": "m", "keep_alive": 0})
    monkeypatch.setattr(mm, "loaded", lambda host=mm.HOST: [{"name": "m", "size": 1, "size_vram": 1}])
    ticks = iter(range(0, 1000))
    monkeypatch.setattr(mm.time, "time", lambda: next(ticks))
    assert mm.unload("m", wait_s=3) is False                                              # Ollama said done, but it never left


def test_unload_all_reports_what_went_and_what_did_not(fake, monkeypatch):
    state = {"a": [{"name": "a", "size": 1, "size_vram": 1}, {"name": "b", "size": 1, "size_vram": 1}]}
    monkeypatch.setattr(mm, "loaded", lambda host=mm.HOST: state["a"])
    monkeypatch.setattr(mm, "unload", lambda name, host=mm.HOST, **k: name == "a")
    assert mm.unload_all() == {"unloaded": ["a"], "still_loaded": ["b"]}
