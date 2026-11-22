# OWASP Cheat Sheet references

A map from each item and experiment here to the OWASP Cheat Sheets that give the corresponding
defender guidance. This is the author's proposal, not an OWASP endorsement, and it is a reference
map, not a compliance claim: each item links to the scenario that actually measures the risk.

Only section titles are cited. No cheat-sheet text is reproduced; the corroborations below are
paraphrased in this project's own words. Source: OWASP Cheat Sheet Series,
<https://cheatsheetseries.owasp.org/>.

## Scope note

The OWASP "Top Ten 2021" index that this started from maps cheat sheets to the **web-application**
Top 10 (A01 Broken Access Control, A03 Injection, A10 SSRF, and so on), a different taxonomy from the
Agentic (ASI) Top 10 this repository is organized around. That index references no AI or agent
guidance. The relevant material is instead the series' **AI-specific** sheets plus a few classic
sheets whose mechanism our items exercise. Those are what is cited here.

AI-specific sheets used: AI Agent Security; LLM Prompt Injection Prevention; MCP Security; RAG
Security; Secure AI/ML Model Ops; Secure Coding with AI; Verifying Third-Party Agent Execution
Evidence. Classic sheets used where the mechanism matches: Authorization; Access Control; Insecure
Direct Object Reference Prevention; Transaction Authorization; OS Command Injection Defense; Threat
Modeling; Abuse Case; Attack Surface Analysis; Logging; Secrets Management; Key Management;
Deserialization.

## Item mapping

| Item | OWASP Cheat Sheet (section) |
| --- | --- |
| [ASI01](../items/asi01-goal-hijack/) Agent Goal Hijack | LLM Prompt Injection Prevention (Common Attack Types; Primary Defenses); AI Agent Security (Key Risks: Goal Hijacking) |
| [ASI02](../items/asi02-tool-misuse/) Tool Misuse | AI Agent Security (Tool Security & Least Privilege); MCP Security (Least Privilege; Prompt Injection via Tool Return Values); Authorization |
| [ASI03](../items/asi03-identity-privilege/) Identity and Privilege Abuse | AI Agent Security (High-Impact Action Integrity Controls); MCP Security (Authentication, Authorization & Transport Security); Authorization; Insecure Direct Object Reference Prevention; Transaction Authorization |
| [ASI04](../items/asi04-supply-chain/) Agentic Supply Chain | Secure AI/ML Model Ops; MCP Security (Supply Chain Security); Secure Coding with AI (Prompt-to-Code Supply Chain Risk); Verifying Third-Party Agent Execution Evidence; Deserialization |
| [ASI05](../items/asi05-code-execution/) Unexpected Code Execution | MCP Security (Sandbox and Isolate MCP Servers); Secure Coding with AI (Agent Runtime Sandboxing); OS Command Injection Defense |
| [ASI06](../items/asi06-memory-context-poisoning/) Memory and Context Poisoning | RAG Security (Document Poisoning; Index Integrity); AI Agent Security (Memory & Context Security) |
| [ASI07](../items/asi07-inter-agent-communication/) Insecure Inter-Agent Communication | AI Agent Security (Multi-Agent Security); MCP Security (Tool Description & Schema Integrity; Optional Message-Level Integrity); LLM Prompt Injection Prevention (Agent-Specific Attacks/Defenses); Verifying Third-Party Agent Execution Evidence; Key Management |
| [ASI08](../items/asi08-cascading-failures/) Cascading Failures | AI Agent Security (Multi-Agent Security: circuit breakers); Secure Coding with AI (Multi-Agent and Sub-Agent Propagation); RAG Security (Tool Invocation and Agent Safety) |
| [ASI09](../items/asi09-human-agent-trust/) Human-Agent Trust Exploitation | AI Agent Security (Human-in-the-Loop Controls); LLM Prompt Injection Prevention (Human-in-the-Loop Controls); MCP Security (Human-in-the-Loop for Sensitive Actions) |
| [ASI10](../items/asi10-rogue-agents/) Rogue Agents | AI Agent Security (Monitoring & Observability; Multi-Agent Security); Verifying Third-Party Agent Execution Evidence |

## A2A experiment mapping (issues)

| Experiment | OWASP Cheat Sheet (section) |
| --- | --- |
| Agent-card poisoning (merged) | AI Agent Security (Input Validation & Prompt Injection Defense); RAG Security (Document Poisoning); Verifying Third-Party Agent Execution Evidence |
| Confused deputy (merged) | AI Agent Security (High-Impact Action Integrity Controls); MCP Security (Prompt Injection via Tool Return Values) |
| Peer pressure (#96) | LLM Prompt Injection Prevention (Multi-Turn and Persistent Attacks); AI Agent Security (Multi-Agent Security) |
| Direction asymmetry (#97) | RAG Security (Source Attribution and Provenance); Verifying Third-Party Agent Execution Evidence |
| Two-way contagion (#98) | Secure Coding with AI (Multi-Agent and Sub-Agent Propagation); AI Agent Security (Multi-Agent Security: circuit breakers) |
| Scope retention (#99) | AI Agent Security (High-Impact Action Integrity Controls: short-lived authorization, bind approval to the exact action, step-up auth); MCP Security (Authentication, Authorization & Transport Security) |
| Read-side laundering (#100) | RAG Security (Access Control Inheritance); Authorization |
| Covert channel (#101) | AI Agent Security (Key Risks: Data Exfiltration; Output Validation & Guardrails; Monitoring & Observability); LLM Prompt Injection Prevention (Data Exfiltration); Secrets Management |

## Method mapping

The repository's measurement discipline lines up with specific cheat-sheet guidance:

| Our practice | OWASP Cheat Sheet (section) |
| --- | --- |
| Preregistered prediction, pass bar, and honest addendum | LLM Prompt Injection Prevention (Smoke-Testing Your Defenses: grade the intended outcome; report results with their limits) |
| Hash-chained decision log; harm read from system state, not the agent's say-so | Verifying Third-Party Agent Execution Evidence (Six Questions to Ask About an Execution Record) |
| Fail-closed when a gate, broker, or check fails | RAG Security (Fail-Closed Design); AI Agent Security (High-Impact Action Integrity Controls) |
| STRIDE and threat-surfaces crosswalk; preregistered attack surfaces | Threat Modeling; Abuse Case; Attack Surface Analysis |

## Where OWASP guidance independently states findings measured here

These are paraphrases of the cited sheets' recommendations, in this project's own words.

- **Agent-card poisoning ("authenticity is not authority").** The RAG and Verifying-Evidence sheets
  draw the same line the merged experiment measured: a valid signature or a matching digest shows a
  payload is consistent with an approved baseline, not that its content is safe or that an action
  actually happened. The experiment found a signed-card defense withheld every tampered card yet the
  coordinator still produced a bad offer in a third of cases, because withholding the card is not the
  same as making the right call.

- **Confused deputy ("bind to the grant, recompute independently").** The AI Agent Security and MCP
  sheets both recommend separating decision-making from execution and validating scope, privilege, and
  approval independently of the model's interpretation. That is exactly the declared-grant defense the
  merged experiment showed stops laundering while keeping the operator's authorized action.

- **Read-side laundering (#100, before it is built).** The RAG Access Control Inheritance section
  recommends enforcing access checks at retrieval time rather than at ingestion, and not relying on the
  language model to enforce access control. That is the read-side defense #100 is designed to test.

- **The measurement posture itself.** The Verifying-Evidence sheet's framework (use an observer that is
  independent of the component's own reports, record the trust assumptions and limits with each result,
  and do not read a missing entry as proof that nothing happened) matches this repository's decision-log,
  harm-from-state, and honest-addendum discipline.

- **Runtime loop detection (#12 / #89).** The AI Agent Security monitoring guidance calls for watching
  repeated approval-bypass attempts and abnormal tool-invocation frequency, which is what the contributed
  runtime duplicate-tool-loop detector observes.
