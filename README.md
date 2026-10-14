# Agent-Defense-Theater

A live range for defending AI agents against the [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). Real local models are attacked through real tools, each defense is measured against the valid work it must still allow, and every prediction is written down before the run.

The stakes are fiction: a fake support desk, a fake deal pipeline, mail that lands in a table. The models, the tool protocols, the attacks and the numbers are real, and the numbers include the misses.

## What it demonstrates

- **Defenses are measured against valid use, not alone.** Every run reports the attacks that got through next to the legitimate work that still got done. A defense that blocks everything scores zero on the second.
- **Predictions come first.** The harness refuses a live run unless the prediction file is committed and the code matches a commit. Results that missed the prediction are reported as misses.
- **Results can be checked.** Every decision is written to a hash-chained log (`python adt.py verify`). Scripted demo runs are labeled and never count.
- **It runs live in the browser.** `python adt.py serve --open` starts a runner with a model picker, a GPU temperature guard that pauses runs above 72 C, a progress view, and a detailed report for each run.

## Where it stands

| Item | What is measured | Headline |
| --- | --- | --- |
| [ASI03](items/asi03-identity-privilege/) Identity and Privilege Abuse | A support desk with a shared token, scoped credentials, an approval step, request binding, and model and rule reviewers, over three rounds | With no defense 62 of 120 planted instructions were carried out. Request binding plus holds let 0 of 120 through and kept 61 of 63 valid tasks. A model reviewer alone approved 12 refunds the operator never asked for, and whether one reviewer followed the same card depended on the model |
| [ASI02](items/asi02-tool-misuse/) Tool Misuse and Exploitation | Two real MCP servers (the author's real-estate calculators and a SQLite deal desk that can be overwritten), with schema gates, a dry run and request binding | Built, prediction committed, first live run in progress |
| [ASI06](items/asi06-memory-context-poisoning/) Memory and Context Poisoning | Measured in two sibling repositories | Linked, not yet re-run here |

The rest of the Top 10 is stubbed with a written plan. The [coverage matrix](#coverage-matrix) says exactly which. Each item ends with what it would take to close the gap, collected in [`docs/LIMITS-AND-ANSWERS.md`](docs/LIMITS-AND-ANSWERS.md). The [governance crosswalk](docs/GOVERNANCE-CROSSWALK.md) sets what is measured beside NIST AI RMF, EU AI Act and ISO/IEC 42001 requirements, with the gaps stated.

## What the results do not show

- The attacks, the gates and the harm definitions are written by the author. No result has been tested against an attacker who knows the defense, except where an item says so.
- The models are local ones up to 8B parameters, on one workstation. Nothing here says how larger models behave.
- The taxonomy mapping is the author's classification, not an endorsement by OWASP or MITRE.

## How it fits together

Two ideas from the author's earlier work are joined:

- **Theater** is the governance layer. Agents start on probation, earn trust, and are classed as performing, miscast, or bad from their outcomes. Human oversight runs at three speeds, slower for higher-impact actions.
- **Greenroom** is the adversarial arena. A Black Hat side attacks a crew of agents and a White Hat side defends it, in the episode format used in [Aegis Vector](https://github.com/ScottColeSW/Project-Aegis-Vector).

A shared harness (`common/`) scores every run the same way: attack success against retained utility, with cost and latency split into model time, reviewer time and our own code. Each item is cross-referenced to the [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) and [MITRE ATLAS](https://atlas.mitre.org/).

## Coverage matrix

| ID | Risk | OWASP LLM 2025 | MITRE ATLAS | Status | Existing work |
| --- | --- | --- | --- | --- | --- |
| [ASI01](items/asi01-goal-hijack/) | Agent Goal Hijack | LLM01 Prompt Injection | AML.T0051 (.000 direct, .001 indirect) | Partial evidence elsewhere | Aegis Vector (injection and spotlighting results) |
| [ASI02](items/asi02-tool-misuse/) | Tool Misuse and Exploitation | LLM06 Excessive Agency | AML.T0053 AI Agent Tool Invocation | Built | [RealEstateTools](items/asi02-tool-misuse/targets/) (copied in) and a new Deal Desk server |
| [ASI03](items/asi03-identity-privilege/) | Identity and Privilege Abuse | LLM06 Excessive Agency | To be mapped | Measured | [Preregistered run](items/asi03-identity-privilege/PREREGISTRATION.md): scoped credentials, 0 of 90 beyond tier |
| [ASI04](items/asi04-supply-chain/) | Agentic Supply Chain Vulnerabilities | LLM03 Supply Chain | To be mapped | Stub | New work |
| [ASI05](items/asi05-code-execution/) | Unexpected Code Execution | LLM05 Improper Output Handling | To be mapped | Stub | New work |
| [ASI06](items/asi06-memory-context-poisoning/) | Memory and Context Poisoning | LLM04 Data and Model Poisoning; LLM08 Vector and Embedding Weaknesses | AML.T0070 RAG Poisoning | Measured elsewhere | Palimpsest and Aegis Vector |
| [ASI07](items/asi07-inter-agent-communication/) | Insecure Inter-Agent Communication | No direct match | To be mapped | Stub | New work |
| [ASI08](items/asi08-cascading-failures/) | Cascading Failures | LLM10 Unbounded Consumption (partial) | To be mapped | Stub | New work |
| [ASI09](items/asi09-human-agent-trust/) | Human-Agent Trust Exploitation | LLM09 Misinformation (partial) | To be mapped | Designed elsewhere | Agent Theater Framework |
| [ASI10](items/asi10-rogue-agents/) | Rogue Agents | LLM06 Excessive Agency | To be mapped | Designed elsewhere | Agent Theater Framework and Void-Marauders |

Status labels: **Stub** (plan written, nothing built), **Designed** (the design exists, nothing measured), **Built** (runs, not yet measured), **Measured** (saved results with a prior prediction), **Adversarially tested** (measured against an attacker who knows the defense). "Elsewhere" means the work lives in another repository and is linked, not copied. The same data is in [`crosswalk/coverage.csv`](crosswalk/coverage.csv). Every item also has a "limits and what it would take" entry, collected in [`docs/LIMITS-AND-ANSWERS.md`](docs/LIMITS-AND-ANSWERS.md).

## Quick start

Python 3.10 or newer, standard library only. [Ollama](https://ollama.com) is needed only to run live, and Node 18 or newer only for the ASI02 calculators.

```bash
python adt.py status            # coverage and which items are runnable
python adt.py demo              # scripted ASI03 run, then verify its decision log
python adt.py serve --open      # the site and the test runner at http://localhost:8765/start.html
python adt.py models            # local models Ollama can see
python adt.py gpu               # GPU temperature; live runs pause above 72 C
python adt.py run asi03 --models llama3.1:8b,qwen2.5:7b,phi4-mini:3.8b
python adt.py run asi02 --models llama3.1:8b,qwen2.5:7b,phi4-mini:3.8b   # needs Node 18+, and npm install in items/asi02-tool-misuse/targets/real-estate-tools
python adt.py summary asi03 --by defense,model
python adt.py verify            # check every decision-log hash chain
python -m pytest -q
```

A live run is refused unless the item's prediction is committed first. See [`common/README.md`](common/README.md).

## Architecture

```
          Theater (governance)               Greenroom (arena)
   tiers, earned trust, oversight   <--->   Black Hat attacks, White Hat defends
                    \                           /
                     \                         /
                      common/  harness, scoring, decision log
                                   |
              asi01 ... asi10  attacks, defenses, eval, results
```

## Repository map

| Path | Purpose |
| --- | --- |
| `theater/` | Trust tiers, earned trust, and the three oversight speeds |
| `greenroom/` | The adversarial arena and the episode format |
| `common/` | The shared harness (`adt` command line), results schema, and the tamper-evident decision log |
| `asi01-...` to `asi10-...` | One folder per OWASP agentic risk, same template each |
| `crosswalk/` | Coverage data and the OWASP and ATLAS mapping |
| `docs/` | Threat model, methodology, preregistration template, limits register, roadmap, demo script |
| `integrations/` | Links to Palimpsest, Aegis Vector, and Void-Marauders |
| `demo/` | The walkthrough and what is scripted versus live |
| `site/` | The static site: status, coverage matrix, ASI06 plots, About and Books. Run with `python -m http.server -d site` |
| `adt.py` | Command line launcher, no install needed |
| `tools/` | `build_data.py` generates the site data and converts saved runs to the results schema |

## Build order

1. `common/` harness and results schema, so every later item shares one scoring format.
2. ASI03 Identity and Privilege Abuse, ASI02 Tool Misuse, and ASI05 Code Execution, the largest gaps in agent containment.
3. ASI01 Goal Hijack on a tool-using crew, then ASI04 Supply Chain.
4. ASI07, ASI08, ASI09, and ASI10 on the multi-agent crew.

Details and exit criteria per step are in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Related projects

- [Palimpsest](https://github.com/ScottColeSW/Palimpsest): the memory gate behind ASI06.
- [Aegis Vector](https://github.com/ScottColeSW/Project-Aegis-Vector): the forgery testbed and the Black Hat vs White Hat episode player.
- [Void-Marauders](https://github.com/ScottColeSW/Void-Marauders): outcome-sensitive trust between agents.
- [Evo](https://github.com/ScottColeSW/Evo): a multi-agent simulation with a headless benchmark harness.

## About the author

Built by Scott A. Cole. See [About](site/about.html) and [Books](site/books.html) (served from `site/`, see [`site/README.md`](site/README.md)), or [github.com/ScottColeSW](https://github.com/ScottColeSW).

## License

MIT. See [LICENSE](LICENSE).
