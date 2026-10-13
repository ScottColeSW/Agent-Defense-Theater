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


SHOW = {"nomic-embed-text:latest": ["embedding"]}                          # what /api/show says where /api/tags says nothing
TAGS = [tag("qwen3:4b", 2.6, "4B", caps=["completion", "tools", "thinking"]), tag("phi4-mini:3.8b", 2.5, "3.8B"), tag("llama3.1:8b", 4.9, "8B"), tag("qwen2.5:7b", 4.7), tag("big:14b", 9.0, "14B"), tag("huge:70b", 40, "70B"),
        tag("nomic-embed-text:latest", 0.27, "137M"), tag("tagged-embedder", 0.5, caps=["embedding"]), tag("tagged-chat", 1.0, caps=["completion", "tools"])]


@pytest.fixture
def fake(monkeypatch):
    state = {"ps": [], "vram": {"name": "Test GPU", "total": 8192 * MB, "used": 500 * MB, "free": 7692 * MB}, "ram": {"total": 32 * GB, "free": 20 * GB}, "posts": []}

    def get(path, host=mm.HOST, timeout=5):
        return {"models": TAGS} if path == "/api/tags" else {"models": state["ps"]}

    monkeypatch.setattr(mm, "_get", get)
    def post(path, body, host=mm.HOST, timeout=30):
        state["posts"].append((path, body))
        if path == "/api/show":
            return {"capabilities": SHOW.get(body["model"], ["completion"]), "details": {"family": "x", "parameter_size": "7B", "quantization_level": "Q4_K_M"},
                    "model_info": {"llama.context_length": 32768}}
        return {}

    monkeypatch.setattr(mm, "_post", post)
    monkeypatch.setattr(mm, "_desc", {})
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


# ---------------- what Ollama says a model is ----------------
def test_the_description_is_noted_once_per_model_version(fake):
    d = mm.describe("llama3.1:8b", "sha-1")
    assert d["context"] == 32768 and "completion" in d["capabilities"] and d["params"] == "7B" and d["digest"] == "sha-1"
    n = len(fake["posts"])
    mm.describe("llama3.1:8b", "sha-1")
    assert len(fake["posts"]) == n                                            # cached
    mm.describe("llama3.1:8b", "sha-2")
    assert len(fake["posts"]) == n + 1                                        # a new digest is a new version of the model


def test_installed_models_carry_their_capabilities_and_context(fake):
    rows = {m["name"]: m for m in mm.installed()}
    assert "thinking" in rows["qwen3:4b"]["capabilities"] and rows["qwen3:4b"]["context"] == 32768
    assert "nomic-embed-text:latest" not in rows                              # /api/show says embedding, though /api/tags was silent


def test_eligibility_rules():
    assert mm.eligibility(["completion", "tools"]) == (True, "ok")
    assert mm.eligibility(["completion", "vision"]) == (True, "ok")           # a vision model still answers text
    ok, why = mm.eligibility(["completion", "tools", "thinking"])
    assert not ok and "own test" in why                                       # thinking models are kept for their own tests
    assert not mm.eligibility(["embedding"])[0] and "missing capability" in mm.eligibility(["tools"])[1]
    thinking_only = {"requires": ["completion", "thinking"], "excludes": ["embedding"]}
    assert mm.eligibility(["completion", "thinking"], thinking_only)[0] and not mm.eligibility(["completion"], thinking_only)[0]


def test_check_eligible_names_the_model_and_the_test(fake):
    ok, msg = mm.check_eligible("asi03/first-run", mm.DEFAULT_RULES, ["llama3.1:8b", "qwen3:4b"])
    assert not ok and "qwen3:4b cannot run asi03/first-run" in msg
    assert mm.check_eligible("asi03/first-run", mm.DEFAULT_RULES, ["llama3.1:8b"]) == (True, "ok")
