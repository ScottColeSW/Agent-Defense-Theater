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

### Starter issues

These are open now. Each issue has the problem, a proposal, notes on the code to read first and acceptance criteria. Comment on the issue before you start, so two people do not take the same one.

| Issue | What | Kind |
| --- | --- | --- |
| [#3](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/3) | Show the pass bar in the console after a run and in `adt summary` | Tooling, good first issue |
| [#4](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/4) | Predicted vs observed values in `adt summary` | Tooling |
| [#5](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/5) | `adt summary --why` for non-completed valid work | Tooling |
| [#6](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/6) | Speed up the test suite | Tooling |
| [#7](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/7) | Per-model table by default after a run | Tooling |
| [#8](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/8) | Extend the KTP capacity gate to `export_customers` | Experiment |
| [#9](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/9) | Simple rules against the KTP gate | Experiment |
| [#10](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/10) | Split-grant probe | Experiment |
| [#11](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/11) | Record the Ollama server version in run metadata | Tooling, good first issue |
| [#12](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/12) | Repetitive tool-loop signal from saved decision logs | Analysis, good first issue |
| [#13](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/13) | Audit how saved outcomes were reached (unintended routes) | Analysis |
| [#14](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/14) | CI workflow that runs the tests on every pull request | Tooling, good first issue |
| [#15](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/15) | Dry-run issue filing for missed pass-bar criteria | Tooling |
| [#16](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/16) | Graduated kill switch for ASI10 | Experiment |
| [#17](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/17) | Rule of Two, remove one leg at a time | Experiment |
| [#18](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/18) | Policy shadow mode | Experiment |
| [#19](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/19) | Corpus diffing for the ASI06 corpora | Tooling |
| [#20](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/20) | Diff the behavior-defining elements between two saved runs | Tooling |
| [#24](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/24) | Audit reply readers for duplicate JSON keys (a second decision key wins) | Scoring fix |
| [#25](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/25) | ASI07: the deal id is outside the signature (experiment `bound-signature` is preregistered) | Defense fix, in progress |
| [#26](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/26) | ASI05: agent code can disable the audit hook and the wall-clock cap | Defense fix |
| [#27](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/27) | ASI03: `NaN` and `-Infinity` refund amounts defeat the budget and the scorer | Scoring fix |
| [#28](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/28) | ASI03: request binding treats "do not refund $200" as asking for it | Defense fix |
| [#29](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/29) | ASI03: reviewer card misreads destinations and prints model-written fields raw | Defense fix |
| [#30](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/30) | ASI02: export recipient check and request binding match text, not intent | Defense fix |
| [#31](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/31) | ASI04: code pin ignores file boundaries | Defense fix |
| [#32](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/32) | Reword claims that say a defense stops a class when it stopped the attacks written | Docs |
| [#33](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/33) | Tracking: root causes from the defense review, and adaptive rounds by a non-author | Tracking |
| [#34](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/34) | ASI03: "bad approvals" counts approved holds on the requested refund inside attack cases | Scoring fix |

Standards for all of them:

- **Tooling and analysis issues (#3 to #7, #11 to #15, #19 and #20) change how results are shown, recorded or compared, never how they are scored, and never modify a saved result.** Reuse `scorer.summarize` and `report.build_report` rather than adding a second scoring path. Standard library only. Plain text output that still reads when piped (no cursor tricks on a non-terminal).
- **A defense fix (#25, #26, #28 to #31) never edits a committed experiment.** The fixed defense is a new condition in a new preregistered experiment, run beside the old one with the bypass as an adaptive attack, and the old result gets an addendum saying what it did and did not show. If you found the bypass, say so in the preregistration: the attacker is then not independent of the defense.
- **Credit the people whose work you build on.** Name the contributor and link their pull request in the addendum and in the README row for the result, and say thank you on the pull request with what their work showed.
- **Recording a run is more than the result files.** Add the addendum to the preregistration (results, every miss, what the run does not show), then update the root README, the item README and `docs/LIMITS-AND-ANSWERS.md` in the same piece of work.
- **A scoring fix (#24, #27, #34) is the one kind that changes what a record says.** Keep it narrow, resolve anything unclear restrictively (a denial, flagged), leave every saved result and committed prediction untouched, and state in the pull request which recorded fields differ for new runs.
- **Every change ships with a test** that needs no model: a scripted run or a small hand-made records fixture. Say in the pull request what you ran and what you did not.
- **Experiment issues (#8 to #10, #16 to #18) follow the rules above in full.** Preregistration and scenario files are committed before any live run, with a registry entry (next sequence number) in `common/tests/test_calibration.py`. Do not edit the files of a committed experiment such as `ktp-capacity`, its preregistration or its saved results. A new experiment gets new files.
- **Write the predictions to be wrong in public.** If a simple rule might tie the gate, say so beforehand. A tie, or a miss by one case, is a result and goes in an addendum.
- **State the reading you chose** wherever the specification is silent (as #2 does for undefined leases), and label it as the experiment's reading.
- **Do not run tests while a live model run is going** (timing and GPU), and keep test temp and scratch output out of the repo.
- **One issue per pull request**, and name the issue (`Closes #N`) in the description. #3 and #4 touch the same summary code, so do them in order.

## Opening a pull request

- One experiment or doc fix per pull request.
- Include the preregistration commit before any results commit.
- Run `python -m pytest -q` and say in the description what you did and did not run.
