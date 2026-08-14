# Evidence plan preparation user view contract

```text
contract_id = acousticbrain.evidence_plan_preparation_user_view.v1
version = 1
status = FROZEN
authority = PRESENTATION_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

This view explains one exact persisted preparation confirmation to a
non-specialist. It is a read-only projection of the dedicated preparation
registry and the exact current evidence plan. It does not verify the user's
declaration, change a prerequisite status, declare an experiment or authorize
execution.

```text
confirmation_id
→ exact registry record
→ exact current plan snapshot
→ preparation user view
```

## Exact resolution

V1 requires an explicit `confirmation_id` and one explicit registry path.
Exactly one registry record must match. An unknown or ambiguous identifier is
rejected before rendering.

The current analysis must resolve exactly one plan with the recorded
`plan_id`. Its canonical fingerprint must equal the recorded
`plan_contract_fingerprint`. A missing, ambiguous or changed plan produces an
explicit contract-continuity error; historical intent is never reconstructed.

No confirmation is selected by plan identifier, recency, status or file order.

## Required blocks

The view always renders these four blocks in this order.

### 1. Declared preparation

Display the exact confirmation identifier, plan identifier, readable plan
label, declaration source and optional user note. The note is archival text
only and cannot alter any decision.

### 2. Prerequisite statuses

Display every recorded prerequisite exactly once with its closed status:

```text
CONFIRMED
NOT_CONFIRMED
UNKNOWN
```

No status may be translated into a stronger status or inferred from files,
measurements, manifests, earlier confirmations or free text.

### 3. Recorded decisions

Display separately:

```text
PLAN_EXACTLY_RESOLVED
PREPARATION_DECLARED
ALL_PREREQUISITES_USER_CONFIRMED
```

The first two must reflect their recorded values.
`ALL_PREREQUISITES_USER_CONFIRMED` is displayed as available only when the
record carries that exact decision; otherwise it is explicitly unavailable.
It remains a user declaration, not independent verification.

### 4. User action and scientific boundary

Display exactly one action:

- when any status is `UNKNOWN`, determine that prerequisite or leave it
  explicitly unknown;
- otherwise, when any status is `NOT_CONFIRMED`, satisfy it operationally or
  preserve the declaration unchanged;
- otherwise, no preparation-status action is required.

The action cannot recommend changing an answer merely to unlock a workflow.
Every view states that no prerequisite was independently verified and no
experiment was declared or executed. It displays:

```text
Causality status: NOT_ESTABLISHED
```

## Historical and divergence rules

Several confirmations for one plan remain distinct historical declarations.
The view never merges, supersedes, ranks or selects between them. A current
plan fingerprint mismatch is shown as a continuity failure, not silently
accepted as a historical equivalent.

Registry contents, source plans, measurements, protocols and manifests remain
byte-for-byte unchanged by rendering.

## CLI boundary

The dedicated operation requires all three explicit values:

```text
--evidence-plan-preparation-view CONFIRMATION_ID
--evidence-plan-preparation-registry PATH
--measurements-root PATH
```

It cannot be combined with preparation recording, plan completion, reporting,
experiment views, exploratory operations, advisor mode or execution commands.

## Acceptance criteria

Automated tests must demonstrate:

1. exact unique confirmation and plan resolution;
2. current plan fingerprint continuity;
3. all four blocks always rendered;
4. exact preservation of every prerequisite status;
5. separate recorded decisions;
6. exactly one non-coercive user action;
7. unknown, ambiguous and stale identities rejected before partial rendering;
8. no implicit selection among confirmations;
9. no registry, plan, measurement, protocol or manifest write;
10. unchanged historical CLI behavior when the view is unused.
