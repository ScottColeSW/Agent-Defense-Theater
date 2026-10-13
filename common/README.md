# Common: shared harness

Status: Built. Runs and is tested. The one item that uses it is ASI03.

Code is in [`adt/`](adt/) (standard library only, no install needed) and tests in [`tests/`](tests/). Run everything through the command line from the repository root:

```bash
python adt.py status        # coverage table, and which items are runnable
python adt.py demo          # scripted ASI03 run, then verify its log
python adt.py models        # local Ollama models
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

- **No prediction, no result.** A live run is refused unless the item's `PREREGISTRATION.md` is committed and unedited, and the harness and item code match a commit. The commits are recorded in the run's `meta.json`. `--exploratory` runs anyway and writes to `results/exploratory/`.
- **Scripted is never a result.** Scripted runs go to `results/scripted/` (ignored by git) and the scorer drops them.
- **Cost and utility travel with attack success.** Every table shows all three, and the count behind each percentage.

## Where results go

| Folder under `asiNN-*/results/` | Contents |
| --- | --- |
| `*.jsonl`, `*.decisions.jsonl`, `*.meta.json` | A preregistered live run: records, decision log, run metadata |
| `exploratory/` | Live runs without a committed prediction |
| `scripted/` | Mechanism demos, not committed |

## Constraints

- Local models first, no external API required to reproduce a result.
- Fixed seeds and temperature zero.
- The hardware limit on model size is recorded in every result.

## Not built yet

A second item on the harness, agents on separate hosts, a model runner for hosted APIs, and an external anchor for the decision log.
