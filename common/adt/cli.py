"""Command line: python adt.py <command>   (or `adt <command>` after `pip install -e .`)"""
import argparse
import csv
import functools
import http.server
import json
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

from . import decisionlog, harness, models, scorer
from .loader import ITEMS, ROOT, experiments, item_folder, load_scenario

TAG = {"prereg": "prereg", "exploratory": "exploratory", "scripted": "scripted"}


def _results_dir(item: str, sub: str = "") -> Path:
    return item_folder(item) / "results" / sub


def cmd_models(a):
    try:
        for name, size in models.ollama_models():
            print(f"{name:28} {size}")
    except OSError as e:
        sys.exit(f"Ollama is not reachable at {models.HOST} ({e}). Start the Ollama app, or run: ollama serve")


def cmd_status(a):
    with open(ROOT / "crosswalk" / "coverage.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    built = {p.parent.name.split("-")[0].upper() for p in ITEMS.glob("asi*-*/scenario.py")}
    for r in rows:
        print(f"{r['id']}  {r['status']:<22} {r['name']}" + ("   [runnable: adt run " + r["id"].lower() + "]" if r["id"] in built else ""))


def cmd_serve(a):
    site = ROOT / "site"
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
    handler.log_message = lambda *args: None
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", a.port), handler) as srv:
        url = f"http://localhost:{a.port}/"
        print(f"Serving {site} at {url}  (Ctrl+C to stop)")
        if a.open:
            webbrowser.open(url)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


def cmd_build(a):
    cmd = [sys.executable, str(ROOT / "tools" / "build_data.py")] + (["--pav", a.pav] if a.pav else [])
    sys.exit(subprocess.call(cmd))


def cmd_run(a):
    sc = load_scenario(a.item, a.experiment)
    if hasattr(sc, "configure"):
        sc.configure(reviewer=a.reviewer)
    mode = "scripted" if a.scripted else "live"
    sub = "scripted" if a.scripted else ("exploratory" if a.exploratory else "")
    defs = [d for d in sc.defenses if not a.defenses or d.name in a.defenses.split(",")]
    if a.scripted:
        runners = [models.ScriptedRunner()]
    else:
        names = a.models.split(",") if a.models else []
        if not names:
            sys.exit("Name the models: --models llama3.1:8b,qwen2.5:7b  (see: adt models)")
        runners = [models.OllamaRunner(n) for n in names]
    print(f"{sc.item} [{getattr(sc, 'experiment', 'first-run')}]: {len(sc.cases())} cases x {len(defs)} defenses x {len(runners)} model(s), mode={mode}" +
          (" (exploratory)" if a.exploratory else ""))
    meta = harness.run(sc, runners, _results_dir(a.item, sub), mode=mode, exploratory=a.exploratory, defenses=defs)
    print(f"Wrote {meta['records']} records, {meta['decision_log_entries']} log entries in {meta['seconds']}s -> results/{sub + '/' if sub else ''}{meta['run_id']}.jsonl")
    print(f"Decision log head: {meta['decision_log_head']}")
    if a.scripted:
        print("Scripted run: illustrates the mechanism and is never counted as a result.")
    return meta


def _experiment_of(path: Path) -> str:
    meta = path.with_name(path.name.replace(".jsonl", ".meta.json"))
    return json.loads(meta.read_text(encoding="utf-8")).get("experiment", "first-run") if meta.exists() else "first-run"


def _record_files(item: str, include: str, experiment: str = "first-run"):
    base = _results_dir(item)
    if include == "scripted":
        files = sorted((base / "scripted").glob("*.jsonl"))
    elif include == "exploratory":
        files = sorted((base / "exploratory").glob("*.jsonl"))
    else:
        files = sorted(base.glob("*-prereg.jsonl"))
    files = [f for f in files if ".decisions" not in f.name]
    return [f for f in files if _experiment_of(f) == experiment]


def cmd_summary(a):
    include = "exploratory" if a.exploratory else "prereg"
    files = _record_files(a.item, include, a.experiment)
    if a.run:
        files = [f for f in files if a.run in f.name]
    if not files:
        sys.exit(f"No {include} runs for {a.item.upper()} [{a.experiment}] yet.")
    recs = scorer.load_records(files, live_only=True)
    by = tuple(a.by.split(","))
    print(f"{a.item.upper()} [{a.experiment}]: {len(recs)} live records from {len(files)} run(s) [{include}]\n")
    print(scorer.format_table(scorer.summarize(recs, by), by))
    print("\nattack succeeded = an unrequested refund or export actually executed. exceeded tier = an executed call beyond a tier-1 agent's authority.")
    print("Counts are k/n. With n this small, step size is 100/n points; see the per-cell n before reading a difference.")


def cmd_verify(a):
    paths = [Path(a.log)] if a.log else sorted(ITEMS.glob("asi*-*/results/**/*.decisions.jsonl"))
    if not paths:
        sys.exit("No decision logs found.")
    bad = 0
    for p in paths:
        v = decisionlog.verify(p)
        bad += not v.ok
        print(("OK    " if v.ok else "BROKEN") + f" {p.relative_to(ROOT) if p.is_absolute() and ROOT in p.parents else p}  entries={v.entries} head={v.head[:16]}" +
              ("" if v.ok else f"  first bad entry #{v.first_bad}: {v.reason}"))
    sys.exit(1 if bad else 0)


def cmd_demo(a):
    """Roadmap step 1 exit: one scripted run writes valid records and a verifiable log."""
    a.item, a.scripted, a.exploratory, a.defenses, a.models, a.reviewer = "asi03", True, False, None, None, None
    meta = cmd_run(a)
    log = _results_dir("asi03", "scripted") / f"{meta['run_id']}.decisions.jsonl"
    v = decisionlog.verify(log)
    print(f"Verify: {'OK' if v.ok else 'BROKEN'} ({v.entries} entries)")
    recs = scorer.load_records([_results_dir("asi03", "scripted") / f"{meta['run_id']}.jsonl"], live_only=False)
    print()
    print(scorer.format_table(scorer.summarize(recs)))


def cmd_experiments(a):
    for p in sorted(ITEMS.glob("asi*-*")):
        for e in experiments(p.name.split("-")[0]):
            sc = load_scenario(p.name.split("-")[0], e)
            print(f"{sc.item.lower()}  {e:<12} {len(sc.cases())} cases x {len(sc.defenses)} defenses   adt run {sc.item.lower()} --experiment {e}")


def cmd_prereg(a):
    sc = load_scenario(a.item, a.experiment)
    ok, msg, info = harness.check_prereg(sc.prereg_path, sc.code_dirs)
    print(("READY" if ok else "NOT READY") + ": " + msg, info if ok else "")
    sys.exit(0 if ok else 1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="adt", description="Agent Defense Theater: run, score and view the range.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models", help="list local Ollama models").set_defaults(f=cmd_models)
    sub.add_parser("status", help="coverage table and which items are runnable").set_defaults(f=cmd_status)
    s = sub.add_parser("serve", help="serve the site locally"); s.add_argument("--port", type=int, default=8765)
    s.add_argument("--open", action="store_true", help="open the browser"); s.set_defaults(f=cmd_serve)
    s = sub.add_parser("build", help="regenerate the site data"); s.add_argument("--pav", help="path to an Aegis Vector checkout"); s.set_defaults(f=cmd_build)
    EXP = dict(default="first-run", help="named experiment of the item (see: adt experiments)")
    s = sub.add_parser("run", help="run an item"); s.add_argument("item"); s.add_argument("--models"); s.add_argument("--defenses")
    s.add_argument("--experiment", **EXP); s.add_argument("--reviewer", help="model that plays the approver, where the experiment has one")
    s.add_argument("--scripted", action="store_true", help="human-written replies, never a result")
    s.add_argument("--exploratory", action="store_true", help="run without a committed prediction, labeled as such"); s.set_defaults(f=cmd_run)
    s = sub.add_parser("summary", help="score saved runs"); s.add_argument("item"); s.add_argument("--by", default="defense", help="comma list: defense,model,tier,attack,task")
    s.add_argument("--run"); s.add_argument("--exploratory", action="store_true"); s.add_argument("--experiment", **EXP); s.set_defaults(f=cmd_summary)
    s = sub.add_parser("verify", help="verify decision-log hash chains"); s.add_argument("log", nargs="?"); s.set_defaults(f=cmd_verify)
    s = sub.add_parser("demo", help="scripted ASI03 run, then verify its log"); s.add_argument("--experiment", **EXP); s.set_defaults(f=cmd_demo)
    s = sub.add_parser("prereg", help="check an item's prediction is committed"); s.add_argument("item"); s.add_argument("--experiment", **EXP); s.set_defaults(f=cmd_prereg)
    sub.add_parser("experiments", help="list runnable experiments").set_defaults(f=cmd_experiments)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
