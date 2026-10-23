# Audit checkpoints and offline verification

An administrator can capture the current audit head, protect that checkpoint separately, and export exactly the history ending at that head. New events arriving during export are excluded. Files are private (mode 0600), published only after successful verification, and never overwrite existing paths. The destination filesystem must support hard links. Audit exports may contain sensitive mission and action information; store them accordingly.

```sh
python -m agentvisa.operator --config credentials.json checkpoint --output checkpoint.json
python -m agentvisa.operator --config credentials.json export-audit --checkpoint checkpoint.json --output audit.ndjson
python -m agentvisa.audit_verify --checkpoint checkpoint.json --audit audit.ndjson
```

The last command is offline, needs no credentials or running gateway, and returns exit code 0 on success or 1 on failure. Save the checkpoint to separately controlled storage before relying on it as evidence. These commands do not automatically establish a trusted timestamp or external anchor.

`GET /audit/checkpoint` requires administrator authentication and returns `version: 1`, a nonnegative `sequence`, and a lowercase SHA-256 `event_hash`. An empty history uses sequence zero and 64 zeroes. The checkpoint reads the stored head; it does not independently certify that history.

Each NDJSON record contains exactly `sequence`, `event`, `previous_hash`, and `event_hash`. Hashes follow the gateway format: SHA-256 of the previous hexadecimal hash concatenated with the event encoded as sorted, compact JSON with ASCII escaping, UTF-8 bytes, and no nonfinite numbers. The verifier requires contiguous sequences starting at one, correct chain links and hashes, and exact agreement with the checkpoint's sequence and final hash. Duplicate JSON keys, oversized records (over 1 MiB), malformed checkpoints, and extra records beyond the checkpoint are rejected. Export uses bounded pages and verification streams one record at a time.

A separately protected, trustworthy checkpoint detects edits, rehashed history, missing records, and truncation *within its prefix*. It says nothing about later events: deleting events created after an older checkpoint is undetectable against that checkpoint. Capture fresh checkpoints according to your retention requirements. Neither the database nor this format has a cryptographic identity binding; choose the intended gateway and checkpoint through trusted operational procedures.

These are unsigned checkpoints, not notarization or proof that an event happened in the real world. Someone able to replace both checkpoint and export can create a matching history. A compromised gateway can lie before a checkpoint is captured. This feature adds no external signing service, protected storage, trusted clock, or guarantee of real external effects.
