"""Background runner for the UI: one job at a time, because there is one GPU. A job is a list of tests run in order.

The rules the CLI enforces apply here too: a live result needs a committed prediction, scripted runs are labeled and never
results, a live run installs the GPU cooler, and a run that is cancelled or fails leaves no partial result behind.
"""
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path

from . import gpucooler, harness, modelmgr, models
from .harness import RunCancelled
from .loader import results_dir
from .registry import get_scenario, list_tests

MODES = ("scripted", "live", "exploratory")


class Busy(Exception):
    pass


class JobManager:
    def __init__(self):
        self.jobs, self.lock, self.active = {}, threading.Lock(), None

    # ---- public ----
    def submit(self, spec: dict) -> dict:
        mode = spec.get("mode", "scripted")
        if mode not in MODES:
            raise ValueError(f"mode must be one of {', '.join(MODES)}")
        known = {t["id"]: t for t in list_tests()}
        ids = spec.get("tests") or []
        if not ids or any(i not in known for i in ids):
            raise ValueError("choose at least one known test")
        spec = {"tests": ids, "mode": mode, "models": list(spec.get("models") or []), "reviewer": spec.get("reviewer") or None,
                "strong_reviewer": spec.get("strong_reviewer") or None, "max_temp": int(spec.get("max_temp", gpucooler.DEFAULT_MAX_C)),
                "defenses": list(spec.get("defenses") or []), "unload_before": bool(spec.get("unload_before", True)), "unload_after": bool(spec.get("unload_after", True))}
        if mode != "scripted":
            installed = {n for n, _ in models.ollama_models()} if self._ollama_up() else None
            if installed is None:
                raise ValueError("Ollama is not reachable. Start it, then try again.")
            names = spec["models"] + [r for r in (spec["reviewer"], spec["strong_reviewer"]) if r]
            if not spec["models"]:
                raise ValueError("choose at least one model for a live run")
            missing = [n for n in names if n not in installed]
            if missing:
                raise ValueError("not installed in Ollama: " + ", ".join(missing))
            ok, why = modelmgr.preflight(list(dict.fromkeys(names)))            # refuse a model that will not fit, before anything starts
            if not ok:
                raise ValueError(why)
            for i in ids:                                                       # and one the test does not accept (a thinking model, say)
                ok, why = modelmgr.check_eligible(i, known[i]["model_rules"], list(dict.fromkeys(names)))
                if not ok:
                    raise ValueError(why)
        if mode == "live":                       # a result needs a prediction committed first; say so before anything starts
            for i in ids:
                sc = get_scenario(i)
                ok, msg, _ = harness.check_prereg(sc.prereg_path, sc.code_dirs)
                if not ok:
                    raise ValueError(f"{i} is refused: {msg}")
        with self.lock:
            if self.active and self.jobs[self.active]["state"] in ("queued", "running"):
                raise Busy("a run is already in progress")
            job = {"id": uuid.uuid4().hex[:10], "spec": spec, "state": "queued", "created": time.time(), "started": None, "finished": None,
                   "tests": [{"id": i, "title": known[i]["title"], "state": "queued", "done": 0, "total": 0, "run_id": None, "message": "",
                              "model": "", "tally": {}} for i in ids], "log": [], "cancel": False, "error": None}
            self.jobs[job["id"]], self.active = job, job["id"]
        threading.Thread(target=self._work, args=(job,), daemon=True, name=f"job-{job['id']}").start()
        return job

    def get(self, job_id: str):
        return self.jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        j = self.jobs.get(job_id)
        if j and j["state"] in ("queued", "running"):
            j["cancel"] = True
            return True
        return False

    def view(self, job: dict) -> dict:
        c = gpucooler.active
        return {**{k: job[k] for k in ("id", "spec", "state", "created", "started", "finished", "tests", "error")}, "log": job["log"][-40:],
                "cooler": {"active": bool(c), "paused": bool(c and c.paused), **(c.stats() if c else {})}}

    # ---- internals ----
    @staticmethod
    def _ollama_up() -> bool:
        try:
            models.ollama_models()
            return True
        except OSError:
            return False

    def _say(self, job, msg):
        job["log"].append(f"{time.strftime('%H:%M:%S')}  {msg}")
        del job["log"][:-200]

    def _work(self, job):
        job["state"], job["started"] = "running", time.time()
        live = job["spec"]["mode"] != "scripted"
        try:
            if live and job["spec"]["unload_before"]:
                self._free(job, "before")
            for t in job["tests"]:
                if job["cancel"]:
                    t["state"], t["message"] = "cancelled", "not started"
                    continue
                self._run_test(job, t)
            states = {t["state"] for t in job["tests"]}
            job["state"] = "cancelled" if job["cancel"] else ("failed" if states & {"failed", "refused"} else "done")
        except Exception as e:                    # never let a bug in one job take the server down
            job["state"], job["error"] = "failed", f"{type(e).__name__}: {e}"
        finally:
            gpucooler.uninstall()
            if live and job["spec"]["unload_after"]:
                self._free(job, "after")
            job["finished"] = time.time()

    def _free(self, job, when):
        """Start (and leave) with an empty GPU, so one run's resident models never crowd the next."""
        try:
            r = modelmgr.unload_all()
            self._say(job, f"memory {when} the run: " + (("unloaded " + ", ".join(r["unloaded"])) if r["unloaded"] else "nothing was loaded") +
                      (f"; could not unload {', '.join(r['still_loaded'])}" if r["still_loaded"] else ""))
        except Exception as e:
            self._say(job, f"memory {when} the run: could not check ({type(e).__name__})")

    def _run_test(self, job, t):
        spec = job["spec"]
        sc = get_scenario(t["id"])
        item = t["id"].split("/")[0]
        mode = "scripted" if spec["mode"] == "scripted" else "live"
        exploratory = spec["mode"] == "exploratory"
        sub = "scripted" if mode == "scripted" else ("exploratory" if exploratory else "")
        if hasattr(sc, "configure"):
            sc.configure(reviewer=spec["reviewer"], strong_reviewer=spec["strong_reviewer"])
        defs = [d for d in sc.defenses if not spec["defenses"] or d.name in spec["defenses"]]
        runners = [models.ScriptedRunner()] if mode == "scripted" else [models.OllamaRunner(m) for m in spec["models"]]
        if mode == "live" and spec["max_temp"]:
            gpucooler.install(gpucooler.GpuCooler(max_c=spec["max_temp"], say=lambda m: self._say(job, m)))
        t["state"] = "running"
        self._say(job, f"{t['id']}: starting ({spec['mode']}, {len(sc.cases())} cases x {len(defs)} conditions x {len(runners)} model(s))")
        out_dir, run = results_dir(item, sub), {}

        def on_start(run_id, d):
            t["run_id"], run["id"], run["dir"] = run_id, run_id, Path(d)

        def on_progress(n, total, model, rec):
            t.update(done=n, total=total, model=model)
            s = t["tally"].setdefault(rec["defense"], {"attacks": 0, "succeeded": 0, "legit": 0, "done": 0, "errors": 0})
            if rec.get("model_error"):
                s["errors"] += 1
            elif rec["attack"] != "none":
                s["attacks"] += 1
                s["succeeded"] += rec["outcome"] == "attack_succeeded"
            else:
                s["legit"] += 1
                s["done"] += rec["outcome"] == "task_succeeded"

        try:
            meta = harness.run(sc, runners, out_dir, mode=mode, exploratory=exploratory, defenses=defs, progress=None,
                               on_start=on_start, on_progress=on_progress, should_stop=lambda: job["cancel"])
            t.update(state="done", message=f"{meta['records']} records in {meta['seconds']}s", done=meta["records"], total=meta["records"])
            self._say(job, f"{t['id']}: finished, {meta['records']} records, decision log {meta['decision_log_entries']} entries")
        except RunCancelled:
            t.update(state="cancelled", message="cancelled; the partial run was discarded")
            self._discard(run)
        except SystemExit as e:                   # the harness refused (for example, no committed prediction)
            t.update(state="refused", message=str(e))
            self._discard(run)
        except Exception as e:
            t.update(state="failed", message=f"{type(e).__name__}: {e}")
            self._say(job, f"{t['id']}: failed, {e}")
            self._discard(run)
        finally:
            gpucooler.uninstall()

    @staticmethod
    def _discard(run: dict):
        """Move a run that did not finish out of the way. A result folder must hold only complete runs."""
        if not run.get("id"):
            return
        dest = Path(tempfile.gettempdir()) / "adt" / "aborted"
        dest.mkdir(parents=True, exist_ok=True)
        for p in Path(run["dir"]).glob(run["id"] + ".*"):
            shutil.move(str(p), str(dest / p.name))


MANAGER = JobManager()
