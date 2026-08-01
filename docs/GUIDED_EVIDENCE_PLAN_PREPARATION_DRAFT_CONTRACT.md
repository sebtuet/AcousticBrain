# Guided evidence plan preparation draft contract

```text
contract_id = acousticbrain.guided_evidence_plan_preparation_draft.v1
version = 1
status = FROZEN
authority = PRESENTATION_AND_INPUT_SCAFFOLDING_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

This contract lets a non-specialist obtain a complete, valid preparation-input
draft without writing JSON, copying a plan fingerprint or discovering internal
prerequisite codes.

```text
explicit READY plan_id
→ exact current plan snapshot
→ deterministic preparation draft
→ user reviews every status
→ separate preview
→ separate explicit recording operation
```

A draft is not a declaration. Generating or displaying it writes nothing and
does not produce `PREPARATION_DECLARED` or
`ALL_PREREQUISITES_USER_CONFIRMED`.

## Exact source resolution

The user targets one explicit `plan_id`. The generator must resolve exactly
one current `EvidenceAcquisitionPlan` with status `READY`. Unknown, ambiguous,
`BLOCKED` and `PROPOSED` plans are rejected before a draft is rendered.

The generator copies, without interpretation:

- exact `plan_id`;
- canonical full-plan fingerprint;
- every exact `required_inputs` code, sorted only after validation;
- the plan's readable presentation label.

No plan is recommended, ranked or selected implicitly.

## Safe defaults

Every prerequisite starts as:

```text
UNKNOWN
```

The generator must never prefill `CONFIRMED` or `NOT_CONFIRMED` from files,
manifests, measurements, earlier declarations, notes, environment state or
heuristics. Empty prerequisites remain an explicit empty collection.

The initial `user_note` is absent. Free text cannot change a status.

## Candidate confirmation identity

The draft carries one candidate `confirmation_id` so the user never has to
invent an internal identifier. Given the exact plan and exact preparation
registry snapshot, allocation is deterministic:

```text
preparation-<lowercase first 12 fingerprint characters>-<ordinal>
```

`ordinal` is the smallest positive integer whose complete candidate identifier
is absent from the registry. Existing records are inspected only for identity
allocation; their statuses, notes and dates never influence the draft.

Generating twice against the same plan and registry snapshot returns the same
candidate. If the registry changes, the draft must be regenerated and
previewed before recording. Recording retains the registry's existing
idempotence and divergence rules.

## Draft projection

The generated draft contains exactly:

```json
{
  "schema_version": 1,
  "confirmation_id": "preparation-aaaaaaaaaaaa-1",
  "plan_id": "EVIDENCE_ACQUISITION_...",
  "plan_contract_fingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "prerequisites": [
    {
      "code": "documented_microphone_position",
      "status": "UNKNOWN"
    }
  ],
  "declaration_source": "GUIDED_USER_CONFIRMATION",
  "user_note": null
}
```

It must deserialize through the existing strict V1 preparation-input loader
without a privileged parsing path. Unknown fields and alternate status values
remain invalid.

## User interaction boundary

V1 generation displays:

1. the exact plan and readable label;
2. every prerequisite with `UNKNOWN`;
3. the candidate confirmation identifier;
4. one action: review and explicitly set each status, or leave it `UNKNOWN`;
5. the statement that nothing has been recorded or executed.

Generation cannot ask the user to assess acoustic truth, infer instrument
state or change an answer to unlock execution.

## Output and write safety

The generator may print the canonical JSON to standard output. Writing a draft
file requires an explicit output path that does not already exist. It must not
overwrite a file, update the preparation registry or create an experiment
directory.

The source plan, registries, measurements, protocols and manifests remain
byte-for-byte unchanged.

## CLI boundary

The future dedicated operation requires:

```text
--generate-evidence-plan-preparation PLAN_ID
--evidence-plan-preparation-registry PATH
```

An optional explicit output path may be provided. The operation cannot be
combined with recording, completion, reporting, user views, exploratory,
advisor or execution modes.

## Acceptance criteria

Automated tests must demonstrate:

1. exact unique `READY` plan resolution;
2. rejection of every non-`READY` source;
3. canonical current-plan fingerprint preservation;
4. exact complete prerequisite copying;
5. unconditional `UNKNOWN` defaults;
6. deterministic collision-free candidate identity allocation;
7. strict compatibility with the existing input loader;
8. stable canonical JSON ordering;
9. refusal to overwrite an output file;
10. no registry, plan, measurement, protocol, manifest or experiment write;
11. no declaration or all-confirmed decision;
12. unchanged historical workflows when generation is unused.

## Explicitly outside V1

V1 does not add an interactive terminal questionnaire, free-text
interpretation, prerequisite verification, declaration preview approval,
recording, experiment declaration, acquisition, comparison, prescription or
causal inference. Those remain separate later operations.
