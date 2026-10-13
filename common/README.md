# Common: shared harness

Status: Stub. Interfaces are described here so the item folders can be written against them before code exists.

## Planned interfaces

| Interface | Responsibility |
| --- | --- |
| Target agent | Runs a task for a crew member and returns the answer and the actions taken |
| Model runner | Calls a local model (Ollama first) with fixed settings so runs repeat |
| Attack | Produces a payload and states which tier and which ASI item it belongs to |
| Defense | Wraps the target at one layer (prevent, detect, contain) and reports what it blocked |
| Scorer | Labels each outcome and computes attack success, retained utility, and cost |
| Recorder | Writes a result record using [`RESULTS-SCHEMA.md`](RESULTS-SCHEMA.md) |
| Decision log | Appends a tamper-evident entry for every decision (see [`decision-log/`](decision-log/)) |

## Constraints

- Local models first, no external API required to reproduce a result.
- Fixed seeds and temperature zero where the model allows it.
- The hardware limit on model size is recorded in every result.
