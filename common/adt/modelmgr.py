"""Model and memory management: what is installed, what fits, what is loaded, and what a run will cost in model swaps.

Standard library only. The ideas are proven in three sibling projects and reused here with their lessons kept:
  - Evo's ollama_client: /api/ps shows what is really resident, and unloading has to poll, because Ollama answers a
    keep_alive of 0 before the model has actually left VRAM. A 500 from Ollama is often VRAM exhaustion.
  - Aegis Vector's resource_guard (ported from the Dominion project): compare a model's estimated footprint with free
    memory before loading it, show only models that can generate text, and prefer a short keep_alive.
  - Evo's scheduler: group work by model so there is at most one swap per model.

The footprint is an estimate, not a simulation of Ollama's scheduler. It is the model's size on disk times a factor for the
context and runtime, and it is replaced by the size Ollama itself reports once a model has been seen loaded.
"""
import ctypes
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request

HOST = "http://localhost:11434"
GB = 1024 ** 3
FOOTPRINT_FACTOR = 1.3          # on-disk size understates the resident footprint (KV cache, compute buffers, runtime)
VRAM_USABLE = 0.95              # leave headroom on the card for the display and the driver
SECONDS_PER_GB_COLD = 7.0       # observed on this workstation: a cold load took about 7 s per GB of model
_seen = {}                      # model -> resident bytes, learned from /api/ps in this process
_desc = {}                      # digest (or name) -> description from /api/show, cached because it does not change

# Which models a test accepts. A test may override this with a `model_rules` attribute.
#   requires  capabilities a model must have          excludes  capabilities that rule a model out
#   separate  capability -> why such a model needs its own test, and is not offered here
DEFAULT_RULES = {
    "requires": ["completion"],
    "excludes": ["embedding"],
    "separate": {"thinking": "A thinking model reasons before it answers, which changes its cost and its behavior. It needs its own test."},
}


# ---------------- memory ----------------
def vram():
    """First NVIDIA GPU as {name, total, used, free} in bytes, or None."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--query-gpu=name,memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=8, check=True).stdout.splitlines()[0]
        name, total, used, free = [x.strip() for x in out.split(",")]
        return {"name": name, "total": int(total) * 1024 * 1024, "used": int(used) * 1024 * 1024, "free": int(free) * 1024 * 1024}
    except (subprocess.SubprocessError, ValueError, OSError, IndexError):
        return None


def ram():
    """System RAM as {total, free} in bytes, or None where it cannot be read."""
    try:
        if os.name == "nt":
            class MEM(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("avail", ctypes.c_ulonglong),
                            ("tpage", ctypes.c_ulonglong), ("apage", ctypes.c_ulonglong), ("tvirt", ctypes.c_ulonglong), ("avirt", ctypes.c_ulonglong),
                            ("ext", ctypes.c_ulonglong)]
            m = MEM()
            m.length = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return {"total": m.total, "free": m.avail}
        info = dict(line.split(":", 1) for line in open("/proc/meminfo"))
        kb = lambda k: int(info[k].split()[0]) * 1024
        return {"total": kb("MemTotal"), "free": kb("MemAvailable")}
    except (OSError, KeyError, ValueError, AttributeError):
        return None


def memory() -> dict:
    return {"vram": vram(), "ram": ram()}


# ---------------- Ollama ----------------
def _get(path, host=HOST, timeout=5):
    with urllib.request.urlopen(host + path, timeout=timeout) as r:
        return json.load(r)


def _post(path, body, host=HOST, timeout=30):
    req = urllib.request.Request(host + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def describe(name: str, digest: str = None, host=HOST) -> dict:
    """What Ollama says a model is: capabilities (completion, tools, thinking, vision, embedding), family, size, quantization and
    context length. Noted once per model version, so a run can say exactly what it tested."""
    key = digest or name
    if key not in _desc:
        try:
            s = _post("/api/show", {"model": name}, host, timeout=15)
        except (urllib.error.URLError, OSError, ValueError):
            return {"name": name, "digest": digest, "capabilities": [], "family": None, "params": None, "quant": None, "context": None}
        info, d = s.get("model_info", {}), s.get("details", {})
        _desc[key] = {"name": name, "digest": digest, "capabilities": s.get("capabilities") or [], "family": d.get("family"),
                      "params": d.get("parameter_size"), "quant": d.get("quantization_level"),
                      "context": next((v for k, v in info.items() if k.endswith(".context_length")), None)}
    return _desc[key]


def eligibility(capabilities, rules: dict = None) -> tuple:
    """(ok, reason) for a model with these capabilities under a test's rules."""
    rules, caps = rules or DEFAULT_RULES, set(capabilities or [])
    missing = [c for c in rules.get("requires", []) if c not in caps]
    if missing:
        return False, "missing capability: " + ", ".join(missing)
    for c in rules.get("excludes", []):
        if c in caps:
            return False, f"a {c} model, which cannot be tested this way"
    for c, why in rules.get("separate", {}).items():
        if c in caps:
            return False, why
    return True, "ok"


def installed(host=HOST) -> list:
    """Installed models that can generate text (embedding-only models are left out), smallest first, each with its description."""
    out = []
    for m in _get("/api/tags", host).get("models", []):
        name = m.get("name")
        if not name or not isinstance(m.get("size"), (int, float)):
            continue
        d = describe(name, m.get("digest"), host)
        caps = m.get("capabilities") or d["capabilities"]
        can = "completion" in caps if caps else "embed" not in name                 # older builds report no capabilities
        det = m.get("details", {})
        if can:
            out.append({"name": name, "disk": int(m["size"]), "params": det.get("parameter_size") or d["params"], "quant": det.get("quantization_level") or d["quant"],
                        "family": det.get("family") or d["family"], "capabilities": list(caps), "context": d["context"], "digest": m.get("digest")})
    return sorted(out, key=lambda x: x["disk"])


def loaded(host=HOST) -> list:
    """What Ollama has resident right now: {name, size, vram}. Learns each model's real footprint as it goes."""
    out = []
    for m in _get("/api/ps", host).get("models", []):
        size, in_vram = int(m.get("size", 0)), int(m.get("size_vram", 0))
        if m.get("name") and size:
            _seen[m["name"]] = size
        out.append({"name": m.get("name"), "size": size, "vram": in_vram, "expires": m.get("expires_at")})
    return out


def unload(model, host=HOST, wait_s=20.0, poll_s=0.5) -> bool:
    """Evict a model and wait until it has really left memory. True if it is gone."""
    try:
        _post("/api/generate", {"model": model, "keep_alive": 0}, host)
    except (urllib.error.URLError, OSError, ValueError):
        pass
    end = time.time() + wait_s
    while time.time() < end:
        try:
            if model not in {m["name"] for m in loaded(host)}:
                return True
        except (urllib.error.URLError, OSError):
            return False
        time.sleep(poll_s)
    return False


def unload_all(host=HOST) -> dict:
    gone, stuck = [], []
    for m in loaded(host):
        (gone if unload(m["name"], host) else stuck).append(m["name"])
    return {"unloaded": gone, "still_loaded": stuck}


# ---------------- fit and plan ----------------
def footprint(entry: dict) -> tuple:
    """(bytes needed, 'observed' or 'estimated')."""
    seen = _seen.get(entry["name"])
    return (seen, "observed") if seen else (int(entry["disk"] * FOOTPRINT_FACTOR), "estimated")


def classify(entry: dict, mem: dict, resident_bytes: int = 0) -> dict:
    """Does it run on the GPU, spill into system RAM, or not fit? Judged against the whole card, as if nothing else were
    loaded, and separately against what is free now."""
    need, basis = footprint(entry)
    v, r = mem.get("vram"), mem.get("ram")
    budget_gpu = v["total"] * VRAM_USABLE if v else 0
    free_now = (v["free"] + resident_bytes) if v else 0                    # a model already resident is not competing with itself
    spill = (r["free"] if r else 0) + (v["free"] if v else 0) + resident_bytes
    if v and need <= budget_gpu:
        cls, why = "gpu", ("runs fully on the GPU" + ("" if need <= free_now else ", once other models are unloaded"))
    elif need <= spill and (v or r):
        cls, why = "partial", "does not fit the GPU alone, so part runs from system RAM and is much slower"
    else:
        cls, why = "no", "will not fit in memory"
    return {"need": need, "basis": basis, "class": cls, "why": why, "fits_free_now": bool(v) and need <= free_now}


def catalog(host=HOST) -> dict:
    mem, res = memory(), {m["name"]: m for m in loaded(host)}
    rows = []
    for e in installed(host):
        c = classify(e, mem, res.get(e["name"], {}).get("size", 0))
        rows.append({**e, **c, "resident": e["name"] in res, "resident_vram": res.get(e["name"], {}).get("vram", 0)})
    return {"memory": mem, "models": rows, "loaded": list(res.values())}


def simulate(sequence: list, sizes: dict, budget: float) -> dict:
    """Walk the order models are used in, keeping the most recently used resident while they fit in `budget`.
    A model that is not resident costs a cold load. Returns the loads and an estimated time lost to them."""
    resident, loads, order = {}, [], 0
    for name in sequence:
        order += 1
        if name in resident:
            resident[name] = order
            continue
        need = sizes[name]
        while resident and sum(sizes[n] for n in resident) + need > budget:
            del resident[min(resident, key=resident.get)]                  # evict the least recently used
        resident[name] = order
        loads.append(name)
    secs = sum(sizes[n] / GB * SECONDS_PER_GB_COLD for n in loads)
    return {"loads": loads, "load_count": len(loads), "est_seconds": round(secs)}


def plan(agents: list, reviewers: list, host=HOST) -> dict:
    """What choosing these models will mean. Each agent model is used first, then each reviewer in turn, which is how the
    experiments order their work, so the sequence below is the real order of loads."""
    cat = catalog(host)
    by = {m["name"]: m for m in cat["models"]}
    chosen = list(dict.fromkeys(agents + reviewers))
    unknown = [n for n in chosen if n not in by]
    advice, warn = [], []
    if unknown:
        return {"ok": False, "error": "not installed (or cannot generate text): " + ", ".join(unknown), "models": [], "loads": 0, "est_seconds": 0, "advice": [], "warnings": []}
    models_info = [{"name": n, "need": by[n]["need"], "class": by[n]["class"], "why": by[n]["why"], "basis": by[n]["basis"]} for n in chosen]
    for m in models_info:
        if m["class"] == "no":
            warn.append(f"{m['name']} needs about {m['need'] / GB:.1f} GB and will not fit. It would be refused.")
        elif m["class"] == "partial":
            warn.append(f"{m['name']} needs about {m['need'] / GB:.1f} GB, more than the GPU holds, so it would run partly from system RAM and be slow.")
    v = cat["memory"]["vram"]
    budget = (v["total"] * VRAM_USABLE) if v else 0
    sizes = {n: by[n]["need"] for n in chosen}
    seq = [x for a in agents for x in [a] + reviewers]
    sim = simulate(seq, sizes, budget) if budget else {"loads": [], "load_count": 0, "est_seconds": 0}
    ideal = len(chosen)
    if v and len(chosen) > 1:
        together = sum(sizes.values())
        if together <= budget:
            advice.append(f"All {len(chosen)} models fit on the GPU together ({together / GB:.1f} of {budget / GB:.1f} GB), so none has to be swapped out.")
        else:
            advice.append(f"Together these models need {together / GB:.1f} GB and the GPU holds {budget / GB:.1f} GB, so models will be swapped. "
                          f"Expect about {sim['load_count']} loads, roughly {sim['est_seconds']} s lost to loading.")
            overlap = [a for a in agents if a in reviewers]
            if not overlap and sim["load_count"] > ideal:
                advice.append("Using one of the agent models as the reviewer as well would save a swap.")
    if any(m["class"] != "no" for m in models_info) and sim["load_count"] > ideal:
        advice.append(f"{sim['load_count'] - ideal} of the loads are reloads of a model evicted earlier.")
    return {"ok": not any(m["class"] == "no" for m in models_info), "models": models_info, "sequence": seq, **sim, "advice": advice, "warnings": warn,
            "vram_budget": budget, "vram_total": v["total"] if v else None}


def preflight(names: list, host=HOST) -> tuple:
    """(ok, message). Refuse a model that will not fit, as Aegis Vector's resource guard does."""
    by = {m["name"]: m for m in catalog(host)["models"]}
    for n in names:
        if n not in by:
            return False, f"{n} is not installed or cannot generate text"
        if by[n]["class"] == "no":
            return False, f"{n} needs about {by[n]['need'] / GB:.1f} GB and would not fit in memory"
    return True, "ok"


def check_eligible(test_id: str, rules: dict, names: list, host=HOST) -> tuple:
    """(ok, message): every chosen model has to be one this test accepts."""
    by = {m["name"]: m for m in installed(host)}
    for n in names:
        ok, why = eligibility(by[n]["capabilities"] if n in by else [], rules)
        if not ok:
            return False, f"{n} cannot run {test_id}: {why}"
    return True, "ok"
