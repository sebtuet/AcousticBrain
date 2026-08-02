# Guided evidence plan preparation recording contract

```text
contract_id = acousticbrain.guided_evidence_plan_preparation_recording.v1
version = 1
status = FROZEN
authority = EXPLICIT_OPERATIONAL_USER_DECLARATION
scientific_authority = NONE
implementation_status = PARTIALLY_IMPLEMENTED
```

## Purpose

This contract connects the guided draft and preview journey to the existing
transactional preparation workflow. It deliberately introduces no second
recording engine and no alternate registry format.

```text
generated draft
→ user edits explicit statuses
→ read-only preview
→ separate explicit approval
→ existing --confirm-evidence-plan-preparation operation
→ atomic preparation registry
```

Generation and preview never constitute approval. Recording is a distinct
command invocation initiated by the user after reviewing the exact input and
projected decisions.

## Single recording authority

The only V1 recording boundary remains:

```text
--confirm-evidence-plan-preparation INPUT_JSON
--evidence-plan-preparation-registry PATH
```

It must reuse `EvidencePlanPreparationWorkflowService`. A guided UI may offer
this operation as its next action, but must not add an alias with different
validation, persistence, idempotence or divergence semantics.

## Approval boundary

The preview displays exactly one next action:

- `NOT_RECORDED`: explicitly run the recording operation, or keep the draft;
- `ALREADY_RECORDED`: no recording action is required;
- divergent identity: fail before displaying a recording action.

The action includes the exact input and registry paths supplied to the preview
when available. It never runs the command automatically and never interprets
free text as consent.

Recording is permitted with `UNKNOWN` or `NOT_CONFIRMED`; those values are
historical declarations and must not be coerced to `CONFIRMED`.
`ALL_PREREQUISITES_USER_CONFIRMED` remains unavailable unless every status is
explicitly `CONFIRMED`, and even then it is not execution authorization.

## Transactional guarantees

Before writing, the existing workflow must validate strict JSON, exact unique
`READY` plan resolution, current plan fingerprint, exact prerequisite set and
registry identity compatibility.

An identical record is idempotent and does not rewrite the registry. Divergent
reuse is rejected with sorted incompatible paths. A new declaration uses its
own generated `confirmation_id` and never supersedes an earlier declaration.

No source plan, measurement, protocol, experiment manifest or acquisition
file is modified. No experiment is declared or executed. Causality remains
`NOT_ESTABLISHED`.

## Acceptance criteria

Tests must demonstrate one explicit action after preview, reuse of the existing
workflow, recording of `UNKNOWN` without promotion, all-confirmed separation,
atomic persistence, idempotence, deterministic divergence, no automatic
preview-to-record transition and unchanged legacy confirmation behavior.
