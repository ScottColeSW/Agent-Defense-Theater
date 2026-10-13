# Decision log

Status: Stub. This is the detection-and-response backbone: every defense decision is written here in a form that shows tampering.

## Requirements

- One entry per decision: who or what decided, what it saw, the verdict, and the reason.
- Each entry carries a hash of the previous entry, so deleting or editing history breaks the chain.
- A verifier walks the chain and reports the first broken link.
- Entries record the agent's trust tier and the delegation chain (used by ASI03 and ASI10).

## Known limits to write up when built

- A hash chain shows tampering after the fact. It does not prevent it, and a writer with full control can rebuild the chain.
- Stronger assurance needs an external anchor, such as a separate write-once store or a signed checkpoint held by another party.

## Planned files

| File | Purpose |
| --- | --- |
| `FORMAT.md` | Entry fields and hash rule |
| `VERIFY.md` | How verification works and what it proves |
