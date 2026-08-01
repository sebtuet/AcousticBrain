# Evidence plan preparation declaration preview contract

```text
contract_id = acousticbrain.evidence_plan_preparation_declaration_preview.v1
version = 1
status = FROZEN
authority = PRESENTATION_ONLY
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose

Preview the exact decisions that one structured preparation input would
produce, without recording it.

```text
explicit input JSON
→ strict V1 loading
→ exact READY-plan resolution
→ declaration decision projection
→ preview only
```

The preview reuses the existing resolver and declaration service. It must not
introduce a second interpretation path.

## Decisions

The view always displays `PLAN_EXACTLY_RESOLVED` and
`PREPARATION_DECLARED` after successful resolution.
`ALL_PREREQUISITES_USER_CONFIRMED` is displayed only when every exact status
is `CONFIRMED`; otherwise it is explicitly unavailable.

`CONFIRMED` remains an unverified user assertion. `UNKNOWN` and
`NOT_CONFIRMED` are preserved exactly and never rewritten to help the workflow
advance.

## Required preview blocks

1. exact confirmation and plan identity;
2. every prerequisite and submitted status;
3. the three separate projected decisions;
4. exactly one action and the scientific boundary.

The action asks the user either to review unresolved statuses or, when all are
confirmed, to choose separately whether to record the declaration. Previewing
never counts as approval.

## Safety and divergence

The explicit preparation registry is loaded to detect identity reuse before
rendering the final preview:

- an identical existing record is shown as `ALREADY_RECORDED`;
- a divergent reuse of `confirmation_id` is rejected with the existing sorted
  incompatible field paths;
- an unused identity is shown as `NOT_RECORDED`.

No record is selected by plan, recency or status. The registry, plan,
measurements, protocols and manifests remain byte-for-byte unchanged.

Every preview states that no prerequisite was independently verified, no
preparation was recorded by the operation, and no experiment was declared or
executed. Causality remains `NOT_ESTABLISHED`.

## CLI boundary

```text
--preview-evidence-plan-preparation INPUT_JSON
--evidence-plan-preparation-registry PATH
--measurements-root PATH
```

The operation cannot be combined with generation, recording, completion,
reporting, user views, exploratory, advisor or execution modes.

## Acceptance criteria

Tests must demonstrate strict loading, exact plan and fingerprint resolution,
status preservation, separate decisions, deterministic existing/divergent
identity handling, exactly one action, no partial rendering on failure, and no
filesystem write.
