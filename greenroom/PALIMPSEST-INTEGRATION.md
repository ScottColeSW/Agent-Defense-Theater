<!-- Imported from https://github.com/ScottColeSW/Adversarial-AI-Greenroom at commit 012cf90 (MIT, same author). The text below this line is unchanged. That repository holds a specification only; no code exists there. This copy is the working version for Agent-Defense-Theater. -->

# Palimpsest Integration: Auxiliary Design

Status: draft 0.1, an auxiliary design document for Adversarial-AI-Greenroom (Greenroom). It states what Greenroom needs from Palimpsest, what changes to Palimpsest would provide it, and the rules that keep those changes from damaging results already published in Project Aegis Vector (PAV).

Important caveat: this was written from Palimpsest's README, not its source code. Some proposed changes may already exist in whole or in part. Section 9 lists what must be verified against the code before any change is built.

## 1. Why this document exists

Greenroom's scenario S3 and the memory halves of S5, S6, and S11 depend on a memory gate. Palimpsest is that gate, and it was built for a different job: a single-agent curated memory, tested in PAV as an ingestion gate for documents. Greenroom uses it differently: as a gate on an agent's own memory writes, behind an arch that the agent cannot reach, with a decision point that holds the only authority to resolve disputes. A few small, additive changes make that use safe, measurable, and reproducible.

## 2. What Greenroom needs, in four requirements

1. Separation of authority. The agent can propose claims and read beliefs. It can never resolve, release, or contain. That separation should be a library guarantee, not wiring that Greenroom has to get right.
2. Machine-readable decisions. Every memory decision must come back as a structured record with stable reason codes, so Greenroom can copy it into its ledger and group results by gate behavior.
3. Shadow and containment. At T0 a memory write must be evaluated without persisting. When the kill switch fires, every claim an agent wrote must be held in one reversible operation.
4. Reproducibility and identity. The gate's configuration must have a fingerprint, and the whole path must be deterministic when Greenroom runs a policy experiment.

## 3. Interface contract

This is what Greenroom will do with Palimpsest once the changes land. It is a contract on Greenroom's side as much as Palimpsest's.

- Greenroom calls the Python API only. It never exposes Palimpsest's MCP server to an agent.
- One store per agent id, under the run directory, opened with the access mode the charter grants.
- The arch holds the admin view. The agent's adapter receives only the agent view.
- Every agent memory write goes through `learn` with the source forced to external. An external claim can never supersede anything, and is held for the user whenever the fixed rules or the judge flag it.
- Calls that clear a hold, `resolve` and `release`, originate only at the decision point and are ledgered with the true decider kind (policy approver, simulated approver, or human). Palimpsest cannot authenticate `by="user"`, so Greenroom's ledger is the record of who actually decided.
- The injection floor stays on in every condition except the explicit "gate off" comparison.
- The Palimpsest version is pinned and recorded in every result.

## 4. Proposed changes

Each change has an identifier, a reason, a proposed API sketch, and acceptance tests. The signatures are proposals, not existing APIs.

### P1. Capability separation

Reason: the README states that `by="user"` is an honor system at the tool level, and the MCP server exposes `resolve` to any connected client.

```python
mem = Memory(path, namespace="agent-7f3a", mode="read_write")
view = mem.agent_view()    # learn (source forced to external), consult, recall
admin = mem.admin_view()   # resolve, release, contain_author, pending_reviews, coverage
```

Also give the MCP server a setting that disables `resolve` and `release`, so any other MCP user can run an agent-safe server.

Acceptance:
- The agent view has no attribute, method, or alias that reaches `resolve`, `release`, or `contain_author`, including through the underlying objects it exposes.
- `view.learn(..., source="trusted")` is rejected or coerced to external, and the test asserts which.
- The MCP server with the disable setting lists five tools, not seven, and calling a disabled tool fails.

### P2. Structured decision record with stable codes

Reason: Greenroom's ledger and its reason-code analyses need machine-readable outcomes.

A `DecisionRecord` returned by `learn` and `consult` carries: claim id (none in a dry run), relation, held flag, the codes, the nearest claims with scores, the quantities compared, judge and refiner identities (or none), whether the floor applied, source, author, timestamp, and the gate fingerprint.

Proposed stable codes: VALUE_MISMATCH, UNCONFIRMED_DROPPED_VALUE, UNCONFIRMED_REVERSED_SENSE, EXTERNAL_HELD, EXCEPTION_REVIEW_NEEDED, OTHER_DOMAIN_HIT, ADJUDICATOR_CONTRADICTS, JUDGE_ERROR_DORMANT.

Acceptance:
- Every existing relation outcome maps to at least one code, and a test enumerates the mapping.
- Adding the record does not change any existing return value or any stored claim (section 6).

### P3. Dry run

Reason: at T0 the green room, an agent's memory writes must be judged as shadow evidence and persist nothing.

```python
result = view.learn(text, dry_run=True)   # runs framing, judging, and the floor
result.record                             # a DecisionRecord, claim id is None
```

Acceptance:
- After a dry run, the store is byte for byte unchanged, including history and edges.
- The record from a dry run equals the record from the real call on the same input and state, except for the claim id and timestamp.

### P4. Contain an author

Reason: the kill switch and the containment drill need every claim an agent wrote to be held in one operation. Today a person resolves claims one at a time, which is too slow.

```python
ids = admin.contain_author(author="agent-7f3a", since="2026-10-05T11:00:00Z",
                           reason="kill switch", by="decision_point")
admin.uncontain(containment_id, reason="false alarm", by="decision_point")
```

Semantics: each affected claim becomes held for the user with the reason, is no longer counted among beliefs, and stays in history. Nothing is deleted. The operation is idempotent and reversible.

Acceptance:
- After containment, `recall` returns none of the author's claims as beliefs, and `held_for_user` lists them.
- Containing twice changes nothing the second time.
- Un-containing restores exactly the prior state.
- Claims by other authors are untouched.

### P5. Read-only open mode

Reason: a T1 agent should hold a handle that cannot write at all, which is a real guarantee instead of a policy.

`Memory(path, mode="read_only")` opens the SQLite file in read-only mode. `learn`, `save`, and every admin write raise a `ReadOnlyError`.

Acceptance:
- Every write path raises, and the file's modification time and contents are unchanged afterward.
- `recall` and `consult` still work.

### P6. Provenance on every recall item

Reason: Greenroom's taint rule can only be precise if each recalled item says where it came from. A trusted belief should not taint the context. An admitted external claim should.

Each `recall` item carries: source label, author, timestamp, origin, held flag, and weight. If the library already returns this, the change is documentation and a test.

Acceptance:
- No recall item lacks a source label and an author.
- A claim learned as external is labeled external in recall for as long as it is a belief.

### P7. Registry and coverage report

Reason: the gate protects only registered facts. In PAV, 6 of 13 verified figure documents were covered. Greenroom wants that number as a memory integrity line in the blast radius table.

The fact registry currently lives in PAV (the scenarios and gate modules and the coverage report). Palimpsest has its own domain registry, which is separate. This change proposes moving the registry concept into the library as a first-class object, with:

```python
report = admin.coverage(referents=["procurement_policy"])
# share of readable facts that are registered, with the unregistered ones listed
```

Acceptance:
- On PAV's corpus the report reproduces PAV's recorded coverage count.
- Unregistered facts are listed by name, not just counted.

### P8. Gate fingerprint

Reason: a change to the gate is a change to the system under test. Greenroom's recertification rule treats it as a fingerprint change for every agent that uses the gate. PAV currently records the Palimpsest version by hand.

`mem.fingerprint()` returns: Palimpsest version, rules version, thresholds, the NLI and embedder identities, the refiner identity or none, the framer identity, the floor setting, and one digest over all of them.

Acceptance:
- Changing any component changes the digest. Changing nothing leaves it identical across processes.

### P9. Review queue protection

Reason: memory flooding, many held claims to bury a forgery or to exhaust a reviewer, is the memory analogue of approval flooding.

A cap on pending items per author, and an option to group near-duplicate held claims so a reviewer sees one cluster once, with a count: `admin.pending_reviews(group_duplicates=True)`. Distinct claims are never merged.

Acceptance:
- A flood of duplicates collapses to one group with a count, and one distinct malicious claim in the flood remains visible as its own item.
- Hitting the cap holds new claims from that author instead of dropping them, and records why.

### Deferred

A hash-chained history for the memory store would make Palimpsest's own record tamper-evident. Greenroom's ledger already covers its need, so this is deferred. A cheap middle step if wanted later is a `history_digest()` that Greenroom's ledger can record at checkpoints, making change detectable between checkpoints.

## 5. Version plan

Proposed numbering, to be adjusted to the library's own.

- v0.6.0, the gate contract, needed before Greenroom's M1: P1, P2, P3, P5.
- v0.7.0, containment, needed before M3: P4.
- v0.8.0, measurement, needed before M5 and M6: P6, P7, P8.
- Later: P9, and the deferred history work.

The order follows what Greenroom cannot build without. S3 and the memory halves of the ladder need the first group. The containment drill needs the second. Blast radius and the experiments need the third.

## 6. Regression gate

Every release must pass all of the following before Greenroom adopts it.

1. Behavior preserving. The new API surface adds capability and does not change existing behavior. On the existing benchmark cases, `consult` and `learn` outputs must be identical to a golden file recorded before the change.
2. PAV battery. Re-run the PAV defenses battery in hold mode, under both hand labels and the model labeler. All ten payloads must still be held and there must be no new false holds on the legitimate corpus. Compare against the recorded run, not against memory.
3. Existing tests. The full test suite passes, and the new tests for the release are added.
4. Judge benchmark. The held-out leaderboard rows do not change, because no judging code should have moved.

If any check fails, the release is not adopted, and the difference is investigated before anything else.

## 7. Determinism rules

Greenroom's reproducibility claim is that the same seed produces the same ledger hash for scripted agents. Memory must not break that.

- Policy experiments use the judge configuration the README recommends for small deployments: the hybrid judge with the NLI model and the embedder and no language model refiner. That path is deterministic on CPU given fixed model weights.
- The framer must be deterministic as well. In the README's design the framer is a model-driven step by default. For policy experiments Greenroom supplies hand labels or a rule-based framer, as PAV did. The model labeler is a separate, clearly labeled condition and is not part of reproducibility claims.
- A test runs the same inputs twice and requires identical decision records, apart from timestamps, and an identical fingerprint digest.

## 8. Rules for the two projects

- All changes are additive and versioned. Nothing already measured is altered.
- Greenroom's held-out variant sets are test data and are never used to tune Palimpsest. If a Greenroom result exposes a Palimpsest weakness, the fix is developed on Palimpsest's own development cases and scored on a fresh batch, as the README's process already requires.
- The judge is never placed in Greenroom's ladder or ledger. Ladder decisions are deterministic rules over structured evidence, and the ledger needs tamper evidence, which Palimpsest does not claim to provide.
- Palimpsest stays single-agent. Greenroom opens one store per agent id and adds no multi-agent sharing to the library.
- Attribution in results: S3 is reported with the gate off and on, and with each gate configuration, so the finding is about the gate and not smeared across the arch and the gate together.

## 9. Verify against the code first

Before building anything, read the Palimpsest source and mark each item as exists, partial, or missing. In particular check:

- Whether `learn` and `consult` already return a structured result with reason information (P2).
- Whether `recall` already returns source, author, and timestamp per item (P6).
- Whether any read-only or dry-run behavior exists (P3, P5).
- How `resolve` and `release` are reached through the MCP server, and whether the tool list is configurable (P1).
- Where the fact registry lives and how the domain registry differs (P7).
- Whether the framer can be supplied as a deterministic callable (section 7).

## 10. Mapping to the Greenroom spec

- Section 6.7 becomes the interface contract (section 3 here).
- Section 6.1: the charter's memory block names namespaces and access modes (P5).
- Section 7: the pipeline gains a memory path using dry run at T0 and real writes at T2 and above (P3).
- Section 7.1: reason codes become two-level, with gate subcodes under MEMORY_GATE_QUARANTINE (P2).
- Section 7.3: taint reads per-item provenance (P6).
- Section 7.5: a halt calls contain-author, and undo for memory means held, not deleted (P4).
- Section 8: ledger entries carry the decision record and gate fingerprint (P2, P8).
- Section 10.3: the gate fingerprint joins the agent fingerprint (P8).
- Section 11: static blast radius adds memory exposure from the coverage report (P7).
- Section 12: new metrics for coverage, memory containment time, memory undo completeness, and review queue depth (P4, P7, P9).
- Sections 13 and 14: memory-targeted attack operators and the S3 split come from Palimpsest's own open weaknesses.
- Section 15: the regression gate (section 6 here) becomes an entry condition for any Palimpsest upgrade.
- Section 18: a parallel track for the Palimpsest versions in section 5.

## 11. Risks

- Coupling. Two repositories changing together can mask which one caused a result. Mitigation: additive versioned changes, a pinned version, the regression gate, and reporting results with the gate off and on.
- False confidence. The judge's accuracy on fresh cases has been 72% to 78% in the README's own held-out batches, with wide intervals, and a forgery that neither the rules nor the judge flags is admitted. Greenroom's reports state these limits wherever S3 results appear.
- Scope. Nine changes is a lot. Mitigation: only the first group blocks Greenroom's early milestones.
- Misread authority. Palimpsest cannot authenticate `by="user"`. Greenroom's ledger is the authoritative record of who decided, and the documentation says so.

## 12. Open questions

1. Which items already exist, after the code check in section 9.
2. Names for the agent view and the admin view, and whether they should be separate classes or one class with enforced modes.
3. Whether the fact registry belongs in the library (P7) or stays an application concern.
4. Version numbering and release cadence.
5. Whether this document is mirrored in the Palimpsest repository as its requirements source.
6. Whether a deterministic rule-based framer should ship with the library or live in Greenroom.