# Crosswalk

[`coverage.csv`](coverage.csv) holds one row per OWASP agentic item: its name, the proposed OWASP LLM Top 10 2025 match, the proposed MITRE ATLAS match, status, existing work, and limits.

If you are placing your own agents against a framework, read this as a map of what has been measured, not a compliance claim: each item links to the scenario that tests that risk, so you can see which defense held and what it cost, not just which box is ticked.

## How the mapping was made

- Item names come from the OWASP Top 10 for Agentic Applications 2026.
- LLM Top 10 matches are the author's proposal. "Partial" means the overlap is real but incomplete, and "No direct match" means none was found.
- ATLAS IDs were checked against the ATLAS data, the ATLAS-2026.07 release (format-version 6.0.0). Every item now carries a proposed ATLAS mapping at technique level. ASI07 has no direct technique and is recorded as "No direct match", with AML.T0073 Impersonation noted as the nearest. The mappings are the author's proposal, not an OWASP or MITRE endorsement; the 2026 OWASP appendix itself maps at tactic level, so these are the finer-grained proposal.

## STRIDE mapping (threat categories)

For a threat-modeling reader, here is each item placed against STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege). This is the author's proposal, the same caveat as the OWASP and ATLAS columns: STRIDE was built for component data flows, not agent cognition, so prompt injection, for example, lands under Tampering because it alters the instruction stream the agent trusts. Each item links to the scenario that tests it.

| Item | STRIDE | Why |
| --- | --- | --- |
| [ASI01](../items/asi01-goal-hijack/) Agent Goal Hijack | Tampering | Injected instructions alter the agent's objective and plan. |
| [ASI02](../items/asi02-tool-misuse/) Tool Misuse and Exploitation | Elevation of Privilege; Tampering | The agent invokes privileged tools with unsafe or manipulated parameters. |
| [ASI03](../items/asi03-identity-privilege/) Identity and Privilege Abuse | Elevation of Privilege; Spoofing | The agent acts with authority beyond its tier, or under a shared or assumed identity. |
| [ASI04](../items/asi04-supply-chain/) Agentic Supply Chain | Tampering | A tampered tool or dependency is staged in front of the real one. |
| [ASI05](../items/asi05-code-execution/) Unexpected Code Execution | Elevation of Privilege; Information Disclosure (Denial of Service for the compute tier) | Generated code escapes the sandbox, exfiltrates a secret, or exhausts compute. |
| [ASI06](../items/asi06-memory-context-poisoning/) Memory and Context Poisoning | Tampering | A forged document alters the memory the agent later trusts. |
| [ASI07](../items/asi07-inter-agent-communication/) Insecure Inter-Agent Communication | Spoofing; Tampering; Repudiation | A forged or replayed message impersonates a sender; an unsigned receipt leaves the action deniable. |
| [ASI08](../items/asi08-cascading-failures/) Cascading Failures | Tampering | A false figure injected into one agent propagates as trusted data through the crew. |
| [ASI09](../items/asi09-human-agent-trust/) Human-Agent Trust Exploitation | Spoofing | The agent's self-written account misrepresents what it did, so a human approves. |
| [ASI10](../items/asi10-rogue-agents/) Rogue Agents | Elevation of Privilege; Repudiation | The agent takes restricted actions outside its scope and reports them as routine. |

## Maintenance

The README matrix, `site/index.html`, and this CSV show the same data. Update the CSV first and copy the change to the other two until a generator exists.

## OWASP Top 10 for LLM Applications 2026 reference (current)

Checked against the 2026 PDF supplied for this project. Its cover carries the date August 4th, 2026 beside a "publication date to be set" placeholder, so confirm the numbering against the published edition. Only entry numbers and titles are cited, and no OWASP text is reproduced. The source is licensed CC BY-SA 4.0 ([genai.owasp.org](https://genai.owasp.org/llm-top-10/)).

The 2026 list renumbers the 2025 list, so `coverage.csv` carries both: `owasp_llm_2025` is kept as written and `owasp_llm_2026` is the same proposal under the new numbers.

| 2026 entry | 2025 entry it follows | Items that map to it here |
| --- | --- | --- |
| LLM01 Prompt Injection | LLM01 Prompt Injection | ASI01 |
| LLM02 Sensitive Information Disclosure | LLM02 Sensitive Information Disclosure | None yet |
| LLM03 Excessive Agency | LLM06 Excessive Agency | ASI02, ASI03, ASI10 |
| LLM04 Supply Chain | LLM03 Supply Chain | ASI04 |
| LLM05 Data and Model Poisoning | LLM04 Data and Model Poisoning | ASI06 |
| LLM06 Unbounded Consumption | LLM10 Unbounded Consumption | ASI08 (partial) |
| LLM07 Misinformation | LLM09 Misinformation | ASI09 (partial) |
| LLM08 Hidden Context Exposure | LLM07 System Prompt Leakage (renamed and widened) | None yet |
| LLM09 Vector and Embedding Weaknesses | LLM08 Vector and Embedding Weaknesses | ASI06 |
| LLM10 Improper Output Handling | LLM05 Improper Output Handling | ASI05 |

What the 2026 document says that bears on this crosswalk:

- **The boundary with the Agentic list.** The 2026 list covers the model as a component inside an application. When the model becomes an actor with tools, memory and downstream consequences, the risk moves to the Agentic Top 10. That is the reason this repository is organized around the ASI items.
- **Its own LLM-to-ASI mapping agrees with the proposals here where it was readable.** It lists Excessive Agency as showing up as ASI02, ASI03 and ASI08, treats Improper Output Handling as foundational for ASI05 and only a loose match for ASI09, and points ASI06 and ASI07 as the agentic amplifications of Hidden Context Exposure, "not an equivalent risk". ASI07 therefore stays "No direct match". The PDF's per-entry framework tables are laid out in columns that did not extract cleanly, so only the clear statements are used. Read the PDF's Appendix A for the rest.
- **MITRE ATLAS is now mapped at tactic level.** The 2026 appendix maps entries to ATLAS tactics (content v2026.06) and removes the per-entry technique references that the 2025 edition had. The technique IDs below are from the 2025 edition and are kept for reference only.

## OWASP Top 10 for LLM Applications 2025 reference (superseded)

Checked against the published PDF (version 2025, November 18, 2024). Only entry numbers, titles and the MITRE ATLAS references the PDF lists are cited here, and no OWASP text is reproduced. The source is licensed CC BY-SA 4.0 and is published at [genai.owasp.org](https://genai.owasp.org/llm-top-10/).

| LLM Top 10 entry | ATLAS references the OWASP document lists | Items that map to it here |
| --- | --- | --- |
| LLM01 Prompt Injection | AML.T0051.000, AML.T0051.001, AML.T0054 | ASI01 |
| LLM02 Sensitive Information Disclosure | AML.T0024.000, AML.T0024.001, AML.T0024.002 | None yet |
| LLM03 Supply Chain | "ML Supply Chain Compromise" (no ID given) | ASI04 |
| LLM04 Data and Model Poisoning | AML.T0018 | ASI06 |
| LLM05 Improper Output Handling | None listed | ASI05 |
| LLM06 Excessive Agency | None listed | ASI02, ASI03, ASI10 |
| LLM07 System Prompt Leakage | AML.T0051.000 | None yet |
| LLM08 Vector and Embedding Weaknesses | None listed | ASI06 |
| LLM09 Misinformation | AML.T0048.002 | ASI09 (partial) |
| LLM10 Unbounded Consumption | AML.T0029, AML.T0034, AML.T0025 | ASI08 (partial) |

What this changes and what it does not:

- Every LLM Top 10 title used in `coverage.csv` matches the PDF.
- The ATLAS column in `coverage.csv` is now filled for every item, mapped to the ATLAS-2026.07 release. The 2026 edition added agent-specific techniques (AI Agent Tool Invocation, AI Agent Tool Poisoning, Generate Malicious Commands, Agentic Resource Consumption, LLM Trusted Output Components Manipulation) that fit these items directly, so the 2025 LLM-entry candidate IDs above are superseded by the item-level mappings.
- LLM02 and LLM07 have no matching item. ASI05's secret-exfiltration attacks overlap LLM02. That is listed as a stub in [`../docs/OPEN-WORK.md`](../docs/OPEN-WORK.md).

## Other files

- [`governance.csv`](governance.csv) and [`governance-links.json`](governance-links.json): the governance crosswalk and which pass-bar criteria of each test bear on which row. See [`../docs/GOVERNANCE-CROSSWALK.md`](../docs/GOVERNANCE-CROSSWALK.md).
- [`threat-surfaces.json`](threat-surfaces.json): the author's grouping of planted attacks into prompt injection, identity and authority claims, and excessive agency, used by the report's Threat surfaces view.
