# Crosswalk

[`coverage.csv`](coverage.csv) holds one row per OWASP agentic item: its name, the proposed OWASP LLM Top 10 2025 match, the proposed MITRE ATLAS match, status, existing work, and limits.

## How the mapping was made

- Item names come from the OWASP Top 10 for Agentic Applications 2026.
- LLM Top 10 matches are the author's proposal. "Partial" means the overlap is real but incomplete, and "No direct match" means none was found.
- ATLAS IDs listed were checked against the ATLAS data. Rows marked "To be mapped" have not been checked yet and must be verified against the current ATLAS release before they are filled in.

## Maintenance

The README matrix, `site/index.html`, and this CSV show the same data. Update the CSV first and copy the change to the other two until a generator exists.

## Other files

- [`governance.csv`](governance.csv) and [`governance-links.json`](governance-links.json): the governance crosswalk and which pass-bar criteria of each test bear on which row. See [`../docs/GOVERNANCE-CROSSWALK.md`](../docs/GOVERNANCE-CROSSWALK.md).
- [`threat-surfaces.json`](threat-surfaces.json): the author's grouping of planted attacks into prompt injection, identity and authority claims, and excessive agency, used by the report's Threat surfaces view.
