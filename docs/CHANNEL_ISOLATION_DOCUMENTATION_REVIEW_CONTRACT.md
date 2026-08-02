# Channel isolation documentation review contract

```text
contract_id = acousticbrain.channel_isolation_documentation_review.v1
version = 1
status = FROZEN
authority = USER_DECISION_SUPPORT_ONLY
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose

Connect two complete `CHANNEL_ISOLATION` operational records to the existing
guided preparation-revision journey without converting documentation into a
preparation declaration.

```text
strict complete operational records
→ exact READY CHANNEL_ISOLATION plan
→ prerequisite-by-prerequisite documentation review
→ explicit user decision remains required
→ existing preparation revision command
```

This is a read-only continuity view. It does not create a second preparation
workflow and does not add fields to preparation manifests.

## Exact inputs

The review accepts exactly:

- one exact `READY` plan whose test type is `CHANNEL_ISOLATION`;
- one strict complete microphone-position record;
- one strict complete acquisition-settings record;
- one strict source preparation draft for the same plan and fingerprint.

The plan, both records and the source draft must share the same canonical
`plan_id` and plan-contract fingerprint. Unknown, ambiguous, stale, incomplete
or cross-plan inputs are rejected before any rendering. Source files are never
modified.

## Closed prerequisite mapping

V1 exposes only the two mappings already defined by the plan contract:

```text
documented_microphone_position
← microphone-position operational record

existing_acquisition_settings
← acquisition-settings operational record
```

Each row reports `DOCUMENTATION_AVAILABLE` and
`USER_PREPARATION_DECISION_REQUIRED`. The view never reports
`CONFIRMED`, `NOT_CONFIRMED` or `UNKNOWN` on behalf of the user and never
interprets record text as proof of physical truth.

No identifier, field, setting, tolerance or prerequisite mapping may be
inferred. A future plan with a different prerequisite set requires a new
versioned contract.

## User action

The view presents exactly one action: make an explicit decision for every
prerequisite and invoke the existing guided preparation-revision command with
one exact `code=STATUS` assignment per prerequisite.

The allowed statuses remain the existing closed vocabulary:
`CONFIRMED`, `NOT_CONFIRMED` and `UNKNOWN`. The view may display a command
template, but every status position remains an explicit placeholder; it must
never prefill `CONFIRMED` from record presence.

Revision, preview and recording remain separate commands. The review itself
does not allocate a confirmation identifier or write an output file.

## Scientific and execution boundary

Operational documentation establishes only that explicit text was supplied.
It does not independently verify microphone placement, acquisition settings,
their reuse during acquisition, measurement validity or repeatability.

The review never changes a prerequisite status, declares an experiment,
executes a measurement, compares results or establishes causality. Its
causality status is always `NOT_ESTABLISHED`.

## Acceptance criteria

Tests must demonstrate exact plan/fingerprint continuity, strict completed
records, strict source-draft continuity, the closed two-row mapping, explicit
status placeholders, exactly one user action, source immutability, no writes,
no automatic preparation status, no declaration or execution, and deterministic
errors before partial rendering.
