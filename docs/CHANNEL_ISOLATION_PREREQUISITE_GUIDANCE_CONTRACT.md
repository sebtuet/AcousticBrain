# Channel isolation prerequisite guidance contract

```text
contract_id = acousticbrain.channel_isolation_prerequisite_guidance.v1
version = 1
status = FROZEN
authority = OPERATIONAL_EXPLANATION_ONLY
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose

Explain the exact prerequisites of a `CHANNEL_ISOLATION` plan so a user can
make an honest structured declaration without interpreting internal codes.
Guidance does not inspect the room, microphone, software or measurement files
and never chooses a status for the user.

## Closed V1 vocabulary

### `documented_microphone_position`

The user may declare `CONFIRMED` only when a written record made before
acquisition identifies a reproducible microphone location and orientation.
The record must state the reference geometry used by the operator; V1 does not
mandate a coordinate system or numeric tolerance that the plan does not define.

Use `NOT_CONFIRMED` when no such record exists or the microphone will knowingly
move without an updated record. Use `UNKNOWN` when the user cannot determine
whether the existing record is sufficient.

The system does not verify placement accuracy or repeatability.

### `existing_acquisition_settings`

The user may declare `CONFIRMED` only when the acquisition settings intended
for LEFT, RIGHT and repetitions are explicitly recorded and will be reused.
The record must cover the plan's controlled settings (`gain`, `time_window`,
`signal_chain`) without requiring values not defined by the plan.

Use `NOT_CONFIRMED` when settings are absent or will knowingly differ. Use
`UNKNOWN` when the user cannot establish whether they are complete or stable.

The system does not inspect software or hardware configuration.

## User-facing projection

For every exact prerequisite, display:

1. readable meaning;
2. what supports `CONFIRMED`;
3. when to use `NOT_CONFIRMED`;
4. when to preserve `UNKNOWN`;
5. verification limitation.

Display exactly one next action: review the listed evidence and create a new
guided preparation draft only if the user wishes to make a new declaration.
Historical declarations remain immutable.

Unknown prerequisite codes receive neutral guidance: no local rule exists and
the status must remain `UNKNOWN` unless an external authoritative procedure
defines it. Codes are never guessed or normalized.

## Safety boundary

The view is read-only. It does not edit a draft, record a declaration, promote
preparation, declare an experiment, start acquisition, validate coverage or
infer scientific results. `CONFIRMED` remains a user assertion and causality
remains `NOT_ESTABLISHED`.

## Acceptance criteria

Tests must demonstrate the closed exact-code mapping, neutral unknown-code
fallback, all guidance blocks, exactly one action, no automatic status, no
plan or registry selection, and no filesystem write.
