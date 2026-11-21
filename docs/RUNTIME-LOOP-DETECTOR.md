# Live Runtime Duplicate Tool-Loop Detector: Design Plan & Reasoning

Follow-up to [issue #12](https://github.com/ScottColeSW/Agent-Defense-Theater/issues/12) and the empirical audit in [`LOG-AUDIT-FINDINGS.md`](LOG-AUDIT-FINDINGS.md).

## 1. Empirical Reasoning (Why This Rule)

Across all 39 preregistered decision logs (50,383 entries, 1,247 contiguous action streaks) analyzed in [`LOG-AUDIT-FINDINGS.md`](LOG-AUDIT-FINDINGS.md):

1. **Action-name-only tracking produces false positives**: Naive streak counting flags 33 `harness` model-timeout retries (`actor="harness"`, `action="model call"`, `saw.args` absent) as well as legitimate multi-item batch workflows where arguments advance per call.
2. **Failure recovery must remain unblocked**: In the ASI03 `probe_failed_first` control, an initial failed attempt followed by a valid retry produces `deny/error -> allow` streaks, which represent legitimate recovery rather than duplicate payout replay.
3. **Three-condition isolation**: Filtering strictly on:
   - `actor != "harness"` (agent tool calls only),
   - identical canonicalized `saw["args"]` (`json.dumps(..., sort_keys=True)`), and
   - prior `verdict == "allow"`
   isolates 100% of the unblocked duplicate-refund replays (`186` streaks under `defense="none"`) with **0 false positives** across all 32 standard/benign runs and all `probe_failed_first` controls.

## 2. Architecture & Hook Point

- **Module (`common/adt/loopguard.py`)**: Provides `RuntimeLoopDetector`, an $O(1)$ per-step, purely in-memory state tracker keyed by `actor`. It canonicalizes `saw["args"]` and emits a structured `LoopAlert` when a contiguous duplicate `allow` occurs.
- **Observer integration (`common/adt/decisionlog.py`)**: `DecisionLog` accepts optional read-only `observers` callbacks invoked *after* an entry is serialized, hashed, and written to disk.
  - **Zero latency overhead**: In-memory dictionary lookup and canonical JSON comparison take microseconds per decision.
  - **Zero log mutation**: `DecisionLog` record format, SHA-256 hash chain (`_digest`), and saved `.decisions.jsonl` artifacts remain completely untouched.

## 3. Rollout Plan

1. **Phase 1 (This PR — Telemetry & Observer Primitive)**: Land `RuntimeLoopDetector`, the `DecisionLog` read-only observer hook, and model-free unit tests (`common/tests/test_loopguard.py`) without altering any existing scenario scores or preregistered baselines.
2. **Phase 2 (Optional Defense Layer Integration)**: Wire `RuntimeLoopDetector` into `detect` or `contain` layers (or surface duplicate-allow flags on `verdict="hold"` escalations per NIST AI RMF `GOVERN 3.2`) in an opt-in experiment.
