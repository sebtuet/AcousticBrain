# Evidence plan preparation confirmation contract

```text
contract_id = acousticbrain.evidence_plan_preparation_confirmation.v1
version = 1
status = FROZEN
authority = EXPLICIT_OPERATIONAL_USER_DECLARATION
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose

This contract defines how a user may record the operational availability of
the prerequisites already declared by one exact `READY`
`EvidenceAcquisitionPlan`.

It does not verify that a declaration is true, validate acoustic competence,
modify the plan, promote a status, declare an experiment or authorize
execution.

```text
READY plan snapshot
→ exact prerequisite list
→ explicit status for every prerequisite
→ immutable preparation confirmation
→ separate future experiment declaration
```

The plan remains the scientific and procedural authority. The confirmation is
only an auditable user assertion about operational preparation.

## Source-plan resolution

One confirmation targets exactly one existing plan. The plan must:

- resolve uniquely by exact `plan_id`;
- have status `READY`;
- match the submitted canonical `plan_contract_fingerprint`;
- expose exactly the `required_inputs` present in the confirmation;
- remain byte-for-byte and semantically unchanged.

An unknown, ambiguous, `BLOCKED` or `PROPOSED` plan is rejected. A stale
fingerprint is rejected even when the textual `plan_id` is unchanged.

## Structured input

A V1 input is an immutable JSON object:

```json
{
  "schema_version": 1,
  "confirmation_id": "preparation-confirmation-001",
  "plan_id": "EVIDENCE_ACQUISITION_...",
  "plan_contract_fingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "prerequisites": [
    {
      "code": "documented_microphone_position",
      "status": "CONFIRMED"
    },
    {
      "code": "existing_acquisition_settings",
      "status": "UNKNOWN"
    }
  ],
  "declaration_source": "USER_JSON",
  "user_note": null
}
```

Required root fields are:

- `schema_version`, exactly `1`;
- stable non-empty `confirmation_id`;
- exact non-empty `plan_id`;
- canonical SHA-256 `plan_contract_fingerprint`;
- `prerequisites`, containing every declared required input exactly once;
- explicit non-empty `declaration_source`.

`user_note` is optional archival text. It cannot supply a missing prerequisite,
change a status, validate a protocol or assert scientific compatibility.

Unknown fields are rejected. Identifiers, statuses and codes are never
trimmed, corrected, translated or inferred.

## Prerequisite statuses

V1 permits exactly three statuses:

```text
CONFIRMED
NOT_CONFIRMED
UNKNOWN
```

- `CONFIRMED` means only that the user explicitly declares the prerequisite
  operationally available.
- `NOT_CONFIRMED` means the user explicitly declares it unavailable or not yet
  satisfied.
- `UNKNOWN` means the user cannot currently determine its availability.

None of these statuses is an acoustic measurement, scientific validation,
causal conclusion or proof of execution conformity.

Every `required_inputs` code from the exact plan must appear once and only
once. Extra, missing, duplicate or reordered-by-inference codes are rejected.
Serialization may sort entries by exact code only after validation.

## Separate decisions

The workflow preserves these distinct decisions:

```text
PLAN_EXACTLY_RESOLVED
PREPARATION_DECLARED
ALL_PREREQUISITES_USER_CONFIRMED
```

`PLAN_EXACTLY_RESOLVED` establishes identity and snapshot continuity only.

`PREPARATION_DECLARED` means a complete structured status set was recorded. It
is available even when one or more statuses are `NOT_CONFIRMED` or `UNKNOWN`.

`ALL_PREREQUISITES_USER_CONFIRMED` is available only when every declared
prerequisite status is `CONFIRMED`. It remains a user declaration, not an
independent verification and not permission to execute.

No decision changes `EvidenceAcquisitionStatus.READY` and no decision implies
an `ExperimentDeclaration`.

## Persistence, idempotence and divergence

Confirmations are stored in a dedicated versioned registry outside measurement
files and experiment manifests.

Persistence must:

- validate the complete operation before writing;
- use atomic replacement;
- preserve normalized input, exact plan identity and fingerprint, all three
  decisions and declaration provenance;
- never modify the source plan, measurements, protocol declarations or
  manifests;
- preserve multiple confirmations without selecting one implicitly.

Re-recording a byte-equivalent normalized confirmation is idempotent and must
not rewrite the registry. Reusing `confirmation_id` with divergent content is
rejected with deterministically sorted incompatible field paths.

A second confirmation for the same plan requires a new `confirmation_id`. It
creates another historical declaration; it does not supersede, merge or erase
an earlier confirmation automatically.

## User-facing rules

A user interface must:

- show the exact plan and its readable label;
- show every prerequisite, including `UNKNOWN` values;
- distinguish user declaration from independent verification;
- display exactly one next action;
- say that declaration is unavailable when any status is not `CONFIRMED`;
- never recommend changing an answer to unlock execution;
- never infer an answer from files, manifests, previous measurements or notes.

## Acceptance criteria

An implementation conforms only when automated tests demonstrate:

1. exact unique READY-plan resolution;
2. canonical full-plan fingerprint validation;
3. exact prerequisite-set equality independent of submitted order;
4. rejection of missing, extra and duplicate prerequisite codes;
5. closed status vocabulary;
6. preservation of `UNKNOWN` and `NOT_CONFIRMED`;
7. source-plan immutability;
8. separate resolution, declaration and all-confirmed decisions;
9. no experiment declaration or execution;
10. no measurement, manifest or protocol mutation;
11. atomic persistence;
12. strict idempotence;
13. sorted deterministic divergence errors;
14. no implicit supersession or selection between confirmations;
15. unchanged historical workflows when no confirmation is supplied.

## Explicitly outside V1

V1 does not add:

- free-text prerequisite interpretation;
- automatic inspection of microphone placement or acquisition settings;
- truth verification of user declarations;
- scientific compatibility or protocol validation;
- plan selection or ranking;
- plan mutation or status promotion;
- experiment-directory creation;
- experiment declaration or execution;
- acquisition validation;
- comparison, prescription or causal conclusions.
