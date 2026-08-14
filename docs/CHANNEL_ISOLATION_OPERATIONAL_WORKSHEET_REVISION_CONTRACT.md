# Channel isolation operational worksheet revision contract

```text
contract_id = acousticbrain.channel_isolation_operational_worksheet_revision.v1
version = 1
status = FROZEN
authority = EXPLICIT_USER_DOCUMENTATION_DRAFT
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Let a user fill the two existing `CHANNEL_ISOLATION` worksheets without
editing JSON manually and without being forced to invent unknown information.

```text
two exact source worksheets
→ one or more explicit field=value assignments
→ two new derived worksheets
→ separate operational-record preview
→ separate preparation decision
```

Revision is a drafting operation. It does not verify documentation, create a
preparation declaration, declare an experiment or execute a measurement.

## Exact source continuity

The command accepts exactly one microphone-position worksheet and one
acquisition-settings worksheet for one exact `READY` `CHANNEL_ISOLATION` plan.
Both source objects must retain the plan identity and canonical fingerprint
already required by the operational-record contract.

Root fields, schema version, identifiers, documentation source and any
previously filled values are validated before revision. The source files
remain byte-for-byte unchanged. Record identifiers are preserved because the
operation fills the same prospective records rather than creating new records.

## Closed assignment paths

V1 accepts only:

```text
microphone_position.reference_geometry
microphone_position.position_description
microphone_position.orientation_description
acquisition_settings.gain
acquisition_settings.time_window
acquisition_settings.signal_chain
acquisition_settings.reuse_declaration
```

Every assignment is explicit exact text in `PATH=VALUE` form. Paths may appear
at most once per operation. Missing, unknown, duplicate, empty or
whitespace-normalized values are rejected rather than corrected.

`reuse_declaration` remains closed to `INTENDED_UNCHANGED` and
`NOT_INTENDED_UNCHANGED`. Assigning a generated `REPLACE_WITH_...` marker is
forbidden. Identity, fingerprint, provenance and note fields cannot be changed
by this operation.

## Partial revision

One or more fields may be revised at a time. Unassigned generated markers are
preserved exactly and reported as missing. This permits the user to stop when
information is unknown instead of supplying a guess.

The result is `DOCUMENTATION_INCOMPLETE` while any marker remains and
`DOCUMENTATION_COMPLETE` only when both strict record loaders accept every
field. Completeness means only that explicit documentation text exists.

## Field guidance

The CLI associates every allowed path with one stable question and one
scientific limitation. Guidance explains what the field documents but never
supplies a measurement value, device setting, position, tolerance or preferred
answer. The two closed reuse choices are displayed verbatim.

## Output safety

Both output paths are explicit, new and distinct. They must also differ from
both source paths. Existing files are never overwritten. All semantic and
target validation occurs before either output is written.

Only the two requested output worksheets may be created. Measurement roots,
source worksheets, preparation registries, plans, manifests and protocols
remain unchanged.

## CLI

```text
--revise-channel-isolation-records PLAN_ID
--microphone-position-record SOURCE_PATH
--acquisition-settings-record SOURCE_PATH
--operational-field PATH=VALUE        # repeated
--microphone-position-output NEW_PATH
--acquisition-settings-output NEW_PATH
--measurements-root PATH
```

The operation cannot be combined with generation, preview, documentation
review, preparation, declaration, reporting, exploratory or advisor modes.

## Acceptance criteria

Tests must demonstrate exact plan and fingerprint continuity, strict source
validation, the closed assignment paths, duplicate and unknown rejection,
partial marker preservation, closed reuse values, completed strict decoding,
source immutability, output prevalidation, overwrite refusal, no preparation
status, no declaration or execution, stable field guidance and causality
`NOT_ESTABLISHED`.
