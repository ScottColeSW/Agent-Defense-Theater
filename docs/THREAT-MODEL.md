# Threat model

Status: stub. This page fixes the vocabulary; each item folder holds its own specifics.

## What is being protected

An organization's agents act on its behalf with real tools, memory, and credentials. The assets are the decisions the agents make, the data they can reach, the actions they can take, and the trust people place in their output.

## Actors

| Actor | Capability assumed |
| --- | --- |
| External content author | Can place text in documents, web pages, or messages that an agent reads |
| Malicious or compromised tool provider | Can change a tool, manifest, or server an agent loads |
| Compromised agent | Controls one agent in a crew and can message the others |
| Careless insider | Approves requests without reading them |
| Adaptive attacker | Knows the defenses and writes attacks against them |

The attackers in this repository are written by the author unless an item says otherwise. That limit applies to every result.

## Trust boundaries

1. Between agent and the content it reads (data is not instructions).
2. Between agent and tools (a policy gate decides what a call may do).
3. Between agent and agent (peer output is untrusted input).
4. Between agent and person (an approval must show what will change).
5. Between agent and memory (a new claim is judged before it is believed).

## Out of scope

Model training attacks, model theft, and infrastructure attacks unrelated to agents.

## References

[OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/), [MITRE ATLAS](https://atlas.mitre.org/).
