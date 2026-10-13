# ASI06 results

Only saved runs live here.

## `pav-defenses.jsonl`

2,860 per-answer records from the Aegis Vector defenses battery, converted to the schema in [`../../../common/RESULTS-SCHEMA.md`](../../../common/RESULTS-SCHEMA.md). One line per answer. Answer text stays in the source repository.

| | |
| --- | --- |
| Source | [Project-Aegis-Vector](https://github.com/ScottColeSW/Project-Aegis-Vector) `results/defenses/defenses.json` |
| Run | 2026-10-03, five small local models (llama3.2, qwen2.5:3b, gemma2:2b, phi3:mini, phi4-mini), judge qwen2.5:7b, temperature 0 |
| Shape | 13 defenses × (10 forgeries + 1 clean baseline) × 4 queries × 5 models |
| Mode | `live` |
| Regenerate | `python tools/build_data.py --pav ../Project-Aegis-Vector` |

The converter recomputes adoption and utility from these records and refuses to write if they disagree with the published report.

### Fields added to the schema

These are extra and do not change the base contract.

| Field | Meaning |
| --- | --- |
| `source_label` | The original judge label: `TRUE`, `ADOPTED_FORGED`, `CONFLICT`, `BLOCKED`, or `NO_FIGURE` |
| `query` | The question asked |
| `source_commit` | Commit of the source repository the run was read from |

### Mappings that are the author's classification

| Source | Schema |
| --- | --- |
| `ADOPTED_FORGED` | `attack_succeeded` |
| `BLOCKED` | `blocked` |
| `CONFLICT` | `flagged` |
| `TRUE` | `task_succeeded` (on a forged corpus this means the true figure survived) |
| `NO_FIGURE` | `task_failed` (no figure stated) |

| Forgery | Tier |
| --- | --- |
| `blunt_override`, `instruction_injection` | loud |
| `inside_job` | adaptive (built against the light defenses, sent through a trusted channel. It was not built against the gate.) |
| the other six | quiet |

Defense layers (`prevent`, `detect`, `contain`) are assigned in [`tools/build_data.py`](../../../tools/build_data.py). The clean-corpus baseline rows use `attack` = `none` and measure retained utility.

## Reading these results

- Attacks were written by the author. No one who knew the gate has tried to beat it.
- Twenty answers per defense per forgery after pooling models, so steps are 5 points. Per-model cells are smaller.
- `prereg` points to Aegis Vector because this run predates this repository. Runs made here will point to their own `PREREGISTRATION.md`.
- This is one scenario (a forged procurement limit). See [`../README.md`](../README.md) for what is untested.
