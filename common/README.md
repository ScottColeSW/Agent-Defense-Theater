# Common: shared harness

Status: Built. Runs and is tested. The one item that uses it is ASI03.

Code is in [`adt/`](adt/) (standard library only, no install needed) and tests in [`tests/`](tests/). Run everything through the command line from the repository root:

```bash
python adt.py status        # coverage table, and which items are runnable
python adt.py demo          # scripted ASI03 run, then verify its log
python adt.py models        # local Ollama models
python adt.py gpu           # GPU temperature against the cooler limit
python adt.py prereg asi03  # is the prediction committed and the code clean?
python adt.py run asi03 --models llama3.1:8b,qwen2.5:7b
python adt.py summary asi03 --by defense,model
python adt.py verify        # check every decision-log hash chain
python adt.py serve --open  # the site
python adt.py build         # regenerate site data
python -m pytest -q
```

## Interfaces

| Interface | Where | Responsibility |
| --- | --- | --- |
| Scenario | an item's `scenario.py` | Supplies cases, defenses, and `run_case`. One per item |
| Model runner | [`adt/models.py`](adt/models.py) | Ollama at temperature 0 with a fixed seed; a cache that makes defenses comparable on identical model output; a scripted runner that is never a result |
| Attack, Defense | the item folders | Attacks state their tier and item; defenses state their layer |
| Scorer | [`adt/scorer.py`](adt/scorer.py) | Attack success, retained utility, cost, with counts and Wilson 95% intervals |
| Recorder | [`adt/harness.py`](adt/harness.py) | Writes one record per answer in [`RESULTS-SCHEMA.md`](RESULTS-SCHEMA.md) and validates it |
| Decision log | [`adt/decisionlog.py`](adt/decisionlog.py) | Hash-chained, one entry per decision, see [`decision-log/`](decision-log/) |

## Rules the harness enforces

- **No prediction, no result.** A live run is refused unless the item's `PREREGISTRATION.md` is committed and unedited, and the harness and item code match a commit. The commits are recorded in the run's `meta.json`. `--exploratory` runs anyway, labeled as such, and writes to the temp folder, not the repository.
- **Scripted is never a result.** Scripted runs go to the temp folder, not the repository, and the scorer drops them.
- **Cost and utility travel with attack success.** Every table shows all three, and the count behind each percentage.

- **A hot GPU waits.** Live runs install the GPU cooler ([`adt/gpucooler.py`](adt/gpucooler.py)): before each model call it reads the GPU temperature and, above 72 C (`--max-temp`, 0 turns it off), pauses until the card is at 60 C or lower, easing off with a short rest before each call between 66 and 72 C, and settling the card to 60 C before a run and between models. It gives up after 30 minutes rather than stall. Every result record carries `gpu_temp_c` and `thermal_wait_ms`, and the run's `meta.json` records the peak, the number of pauses and the seconds paused, so latency can be read with the waits taken out. It checks between calls, so one long generation can still overshoot, which is why a background sampler tracks the true peak. It reads temperature only and does not touch fans, clocks or power.

## The runner and its API

`python adt.py serve --open` serves the site and a JSON API from [`adt/server.py`](adt/server.py), bound to localhost only. The pages that use it are described in [`../site/README.md`](../site/README.md).

| Endpoint | Purpose |
| --- | --- |
| `GET /api/tests` | Every runnable test, whether its prediction is committed, its last result |
| `GET /api/status`, `GET /api/gpu` | Runner, Ollama and GPU readiness; temperature, history, limits and cooler state |
| `GET /api/models`, `POST /api/models/unload`, `POST /api/plan` | Installed models and what fits, unload one or all, and the plan for a model choice (see below) |
| `POST /api/jobs`, `GET /api/jobs/<id>`, `POST /api/jobs/<id>/cancel` | Start, follow and cancel a run of one or more tests, one job at a time because there is one GPU |
| `GET /api/reports`, `GET /api/reports/<run_id>` | Saved runs and the detailed report for one ([`adt/report.py`](adt/report.py)) |

Each experiment registers itself as a test ([`adt/registry.py`](adt/registry.py)) by providing a title, a summary, its conditions, its committed predictions and its pass bar. A new experiment appears in the runner without changes to it. Protections: only local host names are served, a POST must be JSON and any browser `Origin` must be the server's own (so a page on another site cannot start runs here), and model names must be ones Ollama actually has.

## Model and memory management

[`adt/modelmgr.py`](adt/modelmgr.py) helps you choose models that fit before a run starts, instead of finding out from a crash. It reuses what three sibling projects learned the hard way (Evo's `ollama_client` and scheduler, the Dominion inference layer, and Aegis Vector's `resource_guard`), in the standard library only.

| What | How |
| --- | --- |
| **Installed models** | `/api/tags`, keeping only models that can generate text. Embedding-only models are left out |
| **What fits** | A footprint (size on disk times 1.3 for the context and runtime, replaced by the size Ollama reports once the model has been seen loaded), judged against the whole card: **fits the GPU**, **spills to RAM (slow)**, or **will not fit** |
| **What is loaded** | `/api/ps`, with how much of each model is on the GPU |
| **Unloading** | `keep_alive: 0`, then polling until the model has really left. Ollama answers before it has |
| **Run plan** | Walks the order a run uses models in (each agent model, then each reviewer) with least-recently-used eviction, and reports how many loads to expect and roughly how many seconds they cost (about 7 s per GB cold on this workstation) |
| **Preflight** | A live run is refused if a chosen model will not fit |
| **Clean start** | A live run unloads everything before it starts and after it ends, so one run's resident models never crowd the next. Both can be turned off |

In the runner UI this is the models table under the live run modes: fit, size, what is in memory now with an Unload button, a Free GPU memory button, and a plan box that updates as you tick models. Endpoints: `GET /api/models`, `POST /api/models/unload`, `POST /api/plan`.

The footprint is a conservative estimate and not a simulation of Ollama's scheduler. A failed model call now keeps Ollama's own error text, since a 500 is often memory exhaustion.

## Where results go

| Folder under `items/asiNN-*/results/` | Contents |
| --- | --- |
| `*.jsonl`, `*.decisions.jsonl`, `*.meta.json` | A preregistered live run: records, decision log, run metadata |
| `exploratory/`, `scripted/` | Not in the repository. Throwaway test output goes under the system temp folder (`<temp>/adt/<item>/exploratory|scripted/`), which follows `TMP`/`TEMP`/`TMPDIR`. Set those to your testing area before running |

## Constraints

- Local models first, no external API required to reproduce a result.
- Fixed seeds and temperature zero.
- The hardware limit on model size is recorded in every result.

## Not built yet

A second item on the harness, agents on separate hosts, a model runner for hosted APIs, and an external anchor for the decision log.
