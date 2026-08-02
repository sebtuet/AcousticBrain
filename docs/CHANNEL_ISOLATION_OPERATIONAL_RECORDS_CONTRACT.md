# Channel isolation operational records contract

```text
contract_id = acousticbrain.channel_isolation_operational_records.v1
version = 1
status = FROZEN
authority = USER_DOCUMENTATION_ONLY
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose

Provide strict, immutable worksheets for documenting the two operational
prerequisites of the current `CHANNEL_ISOLATION` plan. Records preserve what a
user explicitly entered; they do not verify physical truth or change a
preparation status.

```text
empty guided worksheet
→ explicit user documentation
→ strict operational record
→ separate preparation revision decision
```

## Microphone-position record

```json
{
  "schema_version": 1,
  "record_id": "channel-isolation-microphone-position-001",
  "plan_id": "EVIDENCE_ACQUISITION_...",
  "plan_contract_fingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "reference_geometry": "explicit user text",
  "position_description": "explicit user text",
  "orientation_description": "explicit user text",
  "documentation_source": "USER_JSON",
  "user_note": null
}
```

The three descriptions are required exact non-empty text. V1 does not parse
coordinates, invent a tolerance, decide reproducibility or inspect placement.

## Acquisition-settings record

```json
{
  "schema_version": 1,
  "record_id": "channel-isolation-acquisition-settings-001",
  "plan_id": "EVIDENCE_ACQUISITION_...",
  "plan_contract_fingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "gain": "explicit user text",
  "time_window": "explicit user text",
  "signal_chain": "explicit user text",
  "reuse_declaration": "INTENDED_UNCHANGED",
  "documentation_source": "USER_JSON",
  "user_note": null
}
```

`reuse_declaration` is closed to `INTENDED_UNCHANGED` or
`NOT_INTENDED_UNCHANGED`. It describes intent only. Values remain exact text;
no unit, device, software or preferred setting is inferred.

## Identity and continuity

Both records target one explicit exact `READY` `CHANNEL_ISOLATION` plan and
carry its canonical fingerprint. Unknown, ambiguous, stale, non-ready or
different-type plans are rejected.

Unknown fields, missing fields, surrounding whitespace, invalid schema
versions and identifier reuse with divergent content are rejected. Records are
stored outside measurements and manifests in dedicated versioned registries.

## Relationship to preparation

Record presence never yields `CONFIRMED`. A later guided view may show that
documentation exists and let the user decide whether it supports their
declaration. AcousticBrain must not create or revise a preparation input from
these records automatically.

The microphone record cannot verify physical position. The settings record
cannot verify actual reuse. Neither authorizes experiment declaration or
execution.

## Generation and persistence boundary

V1 first generates empty example worksheets to explicit new paths. Completed
records are loaded and previewed separately before any future persistence.
Files are never overwritten. Source plans, preparation registries,
measurements, protocols and manifests remain unchanged.

## Acceptance criteria

Tests must demonstrate strict schemas, exact plan identity and fingerprint,
closed reuse vocabulary, text preservation without interpretation, new-file
output only, no automatic preparation status, no experiment or execution, and
neutral scientific boundaries with causality `NOT_ESTABLISHED`.
