# Verifying the decision log

```bash
python adt.py verify                         # every decision log under asi*/results/
python adt.py verify path/to/run.decisions.jsonl
```

The verifier walks the file from the start and stops at the first problem, reporting the entry number and which rule failed.

| Failure | Meaning |
| --- | --- |
| sequence jumps | An entry was removed or reordered |
| prev hash does not match | The entry before it was changed, or this one was moved |
| contents do not match its hash | This entry was edited |
| not valid JSON | The file was damaged |

## What a pass proves

That the file is internally consistent: no entry was edited, removed or reordered without breaking the chain after it.

## What it does not prove

- It does not prevent tampering. Anyone who can write the file can rebuild every later hash.
- Deleting the last entries leaves a shorter valid chain. Truncation is caught only by comparing against the head hash.

Each run records its final hash (`decision_log_head`) in `<run_id>.meta.json`, and the run's result commit is the external anchor. For stronger assurance, copy the head hash somewhere the writer cannot reach (a signed note, a separate write-once store). That step is not built.
