# Contributing

Welcome. This page gets you from a fresh clone to a passing test run, and explains the few rules that keep the results honest. For what the project is and what it has found, start with the [README](README.md).

## Get running in ten minutes

Python 3.10 or newer is the only hard requirement, and the harness uses the standard library only. Optional tools unlock more:

| Tool | Needed for |
| --- | --- |
| [Ollama](https://ollama.com) with a local model | Live runs against local models |
| Node 18 or newer | The ASI02 tool servers (`npm install` once in `items/asi02-tool-misuse/targets/real-estate-tools`) |
| Docker | The ASI05 sandbox |
| API keys | Hosted models, blind attack generation. Optional, see below |

```bash
git clone https://github.com/ScottColeSW/Agent-Defense-Theater.git
cd Agent-Defense-Theater
python adt.py status      # the coverage table and which items are runnable
python adt.py demo        # a scripted run, then verify its decision log
python adt.py serve --open
python -m pytest -q       # the full suite can take several minutes
```

`python adt.py -h` lists every command. The scripted demo is an illustration of the mechanism and is never counted as a result.

At least one test (`test_thinking_scripted_run_and_sidecar` in `common/tests/test_calibration.py`) calls a local Ollama and fails with "Ollama is not reachable" if it is not running. Start Ollama first, or expect that failure and run the rest.

## The rules that matter

1. **Preregister before you run.** Copy [`docs/PREREGISTRATION-TEMPLATE.md`](docs/PREREGISTRATION-TEMPLATE.md) into the item folder, write the prediction and the pass bar, and commit it before the first live run. A live run refuses to start without it (`python adt.py prereg` checks).
2. **Never edit a prediction afterward.** Add an addendum with what happened, including every miss. Misses are part of the result.
3. **State the limit beside the number.** Every figure needs its caveat: sample size, who wrote the attacks, which models, what was simulated.
4. **Claims are tested.** Several docs quote numbers that a test recomputes from the saved results. If you change a quoted figure or its wording, run the tests and update the assertion on purpose.
5. **Keep the docs in step.** When an item's status changes, update `crosswalk/coverage.csv` first, then `site/data/coverage.json`, the README coverage table and `docs/LIMITS-AND-ANSWERS.md`. See [`crosswalk/README.md`](crosswalk/README.md).
6. **Plain writing.** Use periods, commas or parentheses, not em dashes. Some documents are checked by a test.

## Keys and secrets

Copy `keys.example.ini` to `keys.ini` only if you use hosted models. Git ignores `keys.ini`, and a test fails if a configured key, or a string shaped like one, is found in a tracked or uncommitted file. Set `max_calls` under `[limits]` to cap spend. A key pasted into a chat, screenshot or log is exposed: revoke it at the provider.

## Where things live

| Path | What |
| --- | --- |
| `items/asi01-...` to `items/asi10-...` | One folder per OWASP Agentic risk: `attacks/`, `defenses/`, `eval/`, `results/`, preregistrations |
| `common/` | The `adt` harness, results schema, decision log, tests |
| `docs/` | Methodology, threat model, limits register, roadmap, open work |
| `crosswalk/` | Coverage and governance mapping data, and the OWASP LLM Top 10 reference |
| `site/` | The static site and report viewer |
| `blackice/`, `theater/`, `greenroom/` | Related designs and the arena spec |

## Picking something to work on

[`docs/OPEN-WORK.md`](docs/OPEN-WORK.md) lists every known gap as a stub: what is missing, what it would take, and where to start. Open an issue or leave a note on a stub before starting, so two people do not run the same experiment.

## Opening a pull request

- One experiment or doc fix per pull request.
- Include the preregistration commit before any results commit.
- Run `python -m pytest -q` and say in the description what you did and did not run.
