import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adt import gpucooler, harness, models, scorer
from adt.gpucooler import GpuCooler
from adt.loader import load_scenario


def test_latency_is_the_sum_of_its_parts(tmp_path):
    sc = load_scenario("asi03", "escalation")
    meta = harness.run(sc, [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None)
    recs = scorer.load_records([tmp_path / f"{meta['run_id']}.jsonl"], live_only=False)
    assert recs and all(r["latency_ms"] == r["model_ms"] + r["review_ms"] + r["gate_ms"] for r in recs)
    assert all(r["model_ms"] == 0 for r in recs)                 # a scripted run has no model, so all of it is our code
    rows = scorer.summarize(recs)
    assert all(r["split"] for r in rows) and "defense ms" in scorer.format_table(rows)


def test_old_records_without_the_split_still_summarize():
    rec = dict(run_id="r", item="X", tier="loud", attack="a", defense="d", layer="none", model="m", crew="c", outcome="blocked",
               tokens_in=1, tokens_out=1, latency_ms=10, mode="live", prereg="", hardware_note="", timestamp="t")
    rows = scorer.summarize([rec])
    assert rows[0]["split"] is False and rows[0]["model_ms"] is None
    assert "ms" in scorer.format_table(rows).splitlines()[0]


def test_cooler_timeline_records_samples_and_pauses():
    seq, t = [75, 71, 66], {"now": 100.0}
    c = GpuCooler(read=lambda: seq.pop(0) if len(seq) > 1 else seq[0], sleep=lambda s: t.__setitem__("now", t["now"] + s),
                  clock=lambda: t["now"], say=lambda m: None)
    c.wait()
    tl = c.timeline()
    assert tl["max_c"] == 72 and tl["resume_c"] == 68 and tl["pause_events"] == [dict(start_s=0.0, seconds=6.0, from_c=75, to_c=66)] and tl["pauses"] == 1
    assert [s[1] for s in tl["samples"]] == [75, 71, 66] and tl["samples"][0][0] == 0.0 and tl["peak_c"] == 75


def test_harness_writes_the_gpu_timeline_when_a_cooler_is_active(tmp_path):
    sc = load_scenario("asi03")
    c = GpuCooler(read=lambda: 60, say=lambda m: None)
    gpucooler.install(c, sampler=False)
    try:
        meta = harness.run(sc, [models.ScriptedRunner()], tmp_path, mode="scripted", progress=None, defenses=sc.defenses[:1])
    finally:
        gpucooler.uninstall()
    assert (tmp_path / f"{meta['run_id']}.gpu.json").exists() and meta["gpu"]["max_c"] == 72


def test_cooler_busy_time_counts_checks_and_pauses_so_callers_can_subtract_it():
    seq, t = [75, 66], {"now": 0.0}
    c = GpuCooler(read=lambda: seq.pop(0) if len(seq) > 1 else seq[0], sleep=lambda s: t.__setitem__("now", t["now"] + s),
                  clock=lambda: t["now"], say=lambda m: None)
    gpucooler.install(c, sampler=False)
    try:
        assert gpucooler.busy_ms() == 0
        c.wait()
        assert gpucooler.busy_ms() == 3000                      # one poll of three seconds
    finally:
        gpucooler.uninstall()
    assert gpucooler.busy_ms() == 0
