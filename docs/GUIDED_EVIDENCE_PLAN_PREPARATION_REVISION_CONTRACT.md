# Guided evidence plan preparation revision contract

```text
contract_id = acousticbrain.guided_evidence_plan_preparation_revision.v1
version = 1
status = FROZEN
authority = EXPLICIT_OPERATIONAL_USER_DECLARATION_DRAFT
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Create a new preparation draft from one strict existing draft and an explicit
status for every exact prerequisite, without editing or superseding the source.

```text
strict source draft
→ exact current READY plan
→ explicit code=status assignments
→ new deterministic confirmation_id
→ new output file
→ separate preview and recording
```

## Explicit status input

Every prerequisite code from the exact plan must appear once and only once.
The closed values remain `CONFIRMED`, `NOT_CONFIRMED` and `UNKNOWN`. Missing,
extra, duplicate or invalid assignments are rejected. Codes and values are not
trimmed, translated, inferred or read from free text.

The system never proposes `CONFIRMED`. The user may explicitly preserve
`UNKNOWN` for any prerequisite.

## Continuity and identity

The source draft must pass the existing strict loader and exact plan/fingerprint
resolution. Its content remains byte-for-byte unchanged.

The revised draft copies plan identity, fingerprint and declaration source,
applies only the explicit statuses, and receives the smallest free deterministic
ordinal defined by the guided draft contract. It never reuses the source
`confirmation_id`, even when statuses are unchanged.

The explicit preparation registry is consulted only for identity allocation
and is never modified. Existing declarations are neither selected nor merged.

## Output safety

Revision writes only to an explicit new file path. Existing files are never
overwritten. Validation completes before atomic writing. Standard output shows
the exact before/after statuses and states that nothing was recorded or
executed.

## CLI boundary

```text
--revise-evidence-plan-preparation SOURCE_JSON
--preparation-status exact_code=STATUS   # repeated
--evidence-plan-preparation-registry PATH
--evidence-plan-preparation-output NEW_PATH
--measurements-root PATH
```

Revision cannot be combined with generation, preview, recording, completion,
user views, reporting, exploratory, advisor or execution modes.

## Acceptance criteria

Tests must demonstrate strict source loading, exact plan continuity, complete
closed status assignments, preservation of `UNKNOWN`, deterministic new
identity, source and registry immutability, atomic new-file output, overwrite
refusal, no declaration or experiment, and unchanged historical workflows.
