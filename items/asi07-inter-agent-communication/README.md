# ASI07: Insecure Inter-Agent Communication

| | |
| --- | --- |
| Status | Stub |
| OWASP LLM Top 10 2025 | No direct match |
| MITRE ATLAS | To be mapped |
| Existing work | New work |

The mapping to the LLM Top 10 and ATLAS is the author's proposal. See [`../../crosswalk/README.md`](../../crosswalk/README.md).

## Threat

Messages between agents are spoofed, tampered with, replayed, or trusted without verification.

**Example scenario.** One agent sends another a message claiming to come from the supervisor.

## Attack tiers

Every item is tested at three tiers, written down before the run (see `PREREGISTRATION.md`).

| Tier | Planned attack |
| --- | --- |
| Loud | Unsigned messages claiming authority. |
| Quiet | Replayed genuine messages in a new context. |
| Adaptive | Messages that exploit how the receiver parses structure. |

## Defense layers

| Layer | Planned defense |
| --- | --- |
| Prevent | Signed messages with sender identity, nonce, and scope. |
| Detect | Reject and log unsigned, stale, or out-of-scope messages. |
| Contain | Receivers treat peer output as untrusted input by default. |

## Measurement

Spoof and replay rejection rate; legitimate message loss; added latency.

Results use the shared schema in [`../../common/RESULTS-SCHEMA.md`](../../common/RESULTS-SCHEMA.md) and only saved runs appear in `results/`.

## What exists today

Evo and Void-Marauders are multi-agent simulations that can host the test crew. They have no message signing.

## Limits and what it would take

Needs agents on separate hosts or runtimes and a real key management service. A single-process crew cannot show network-level attacks.

## Folder map

- `attacks/`: attack payloads and generators, one file per tier.
- `defenses/`: defense implementations, one file per layer.
- `eval/`: test cases and pass criteria.
- `results/`: saved runs only.
- `PREREGISTRATION.md`: the prediction, committed before the first run.
