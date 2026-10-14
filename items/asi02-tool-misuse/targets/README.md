# ASI02 targets

The two MCP servers an agent reaches in the ASI02 test. They are in this repository so the test runs from a clone.

| Folder | What it is | Language | Can it be hurt? |
| --- | --- | --- | --- |
| [`real-estate-tools/`](real-estate-tools/) | RealEstateTools: 31 real-estate investment calculators (four are offered to the agent) | Node | No. It computes and keeps no state. Its one weakness is that it checks no inputs, so a huge `simulations` value ties it up and a rate given as 6.5 and not 0.065 gives nonsense without an error |
| [`deal-desk/`](deal-desk/) | A pipeline of deals in SQLite with tools that overwrite a price, delete a deal, and "send" offers and exports | Python (standard library) | Yes. It is rebuilt from a seed for every test case, and "sent" mail only lands in an `outbox` table |

## Provenance

**real-estate-tools** is the author's own MCP server, copied here from `H:\SAC_Local_AI_Agents\n8n-ai-stack\real-estate-mcp-server` (never in version control, files dated 23 to 28 August 2025, version 1.0.0, MIT, Scott A. Cole). Copied: `server.js`, `RealEstateCalculator.js`, `package.json`, `realestate-tools.json`, `test_mcp_protocol.js`. Left behind: the packaged `.dxt`, the icon and screenshots, `install.sh`, and `comprehensive_validation.js`.

| File | SHA-256 of the original (first 16 hex) |
| --- | --- |
| `server.js` | `35acd746cd163de6` |
| `RealEstateCalculator.js` | `482097be34e00f21` (before the change below) |
| `package.json` | `b6ac886bd0244ef2` |

Changes made here, and only these:

1. `RealEstateCalculator.js`, `runMonteCarlo`: `Math.random()` replaced by a seeded generator (mulberry32, seed from an optional `seed` argument, default 1). The same call now gives the same answer, so replies can be reused and runs repeat. The function is otherwise unchanged, including that `simulations` is not bounded. That is the weakness the test uses.
2. `package-lock.json` added by `npm install`. The SDK is `@modelcontextprotocol/sdk` 0.4.0 as declared.

The calculators are the author's simplified implementations ("Many advanced tools are simulations. These are simplified implementations", says the source). Nothing in this repository claims the finance is right, and the test does not depend on it. Rates are fractions (0.065), although the tool descriptions say "percentage".

Install: `npm install` inside `real-estate-tools/` (Node 18 or newer). `node_modules/` is ignored by git.

**deal-desk** was written for this repository.
