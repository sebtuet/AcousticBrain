# SBIR protocol-instance input contract

```text
contract_id = acousticbrain.sbir_protocol_instance_input.v1
version = 1
status = FROZEN
authority = STRUCTURED_INPUT_AND_EXISTING_SOURCE_RESOLUTION_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED_WITHOUT_CLI
```

## Purpose

Define the only admissible structured input for connecting the current SBIR
additional-observation V2 plan to the existing protocol:

```text
EVIDENCE_ACQUISITION_SBIR_PLACEMENT_INTERACTION_REASONING_
ACQUIRE_SUPPORTING_OBSERVATION_V2
        ↓
exact structured protocol-instance input
        ↓
protocol.temporary_move_speaker.v1
```

This contract does not declare or execute an experiment. It defines data that
a future resolver may validate against existing structured sources.

## Canonical JSON

Exactly these keys are accepted:

```json
{
  "schema_version": 1,
  "protocol_instance_id": "sbir-protocol-instance-001",
  "protocol_id": "protocol.temporary_move_speaker.v1",
  "source_plan_id": "EVIDENCE_ACQUISITION_SBIR_PLACEMENT_INTERACTION_REASONING_ACQUIRE_SUPPORTING_OBSERVATION_V2",
  "source_plan_contract_fingerprint": "<sha256>",
  "reference_experiment_id": "baseline",
  "moved_experiment_id": "exp-sbir-001",
  "speaker_id": "left",
  "surface_id": "front_wall",
  "geometry_candidate_id": "<existing-candidate-id>",
  "speaker_displacement_m": 0.12,
  "declaration_source": "STRUCTURED_SCIENTIFIC_SOURCE",
  "user_note": null
}
```

Unknown and missing fields are rejected. Identifiers are non-empty exact text;
they are never trimmed, case-normalized, corrected or inferred. The required
`user_note` field is either `null` or non-empty exact text and carries no
scientific authority.

`speaker_displacement_m` is a finite, non-zero JSON number. Booleans, numeric
strings, zero, infinities and NaN are invalid.

## Closed values

```text
schema_version = 1
protocol_id = protocol.temporary_move_speaker.v1
source_plan_id = EVIDENCE_ACQUISITION_SBIR_PLACEMENT_INTERACTION_REASONING_ACQUIRE_SUPPORTING_OBSERVATION_V2
declaration_source = STRUCTURED_SCIENTIFIC_SOURCE
```

The reference and moved experiment identifiers must differ.

## Resolution order

A future resolver must apply this order and stop at the first failed stage:

1. `INPUT_SCHEMA_VALID` — strict JSON shape and primitive types;
2. `PLAN_EXACTLY_RESOLVED` — exactly one current V2 plan;
3. `PLAN_FINGERPRINT_MATCHES` — no historical or divergent contract;
4. `PROTOCOL_EXACTLY_RESOLVED` — the fixed existing protocol only;
5. `EXPERIMENTS_EXACTLY_RESOLVED` — distinct reference and moved experiments;
6. `GEOMETRY_CANDIDATE_EXACTLY_RESOLVED` — exactly one existing candidate;
7. `SPEAKER_SURFACE_MATCH` — candidate provenance matches both identifiers;
8. `DISPLACEMENT_SOURCE_MATCH` — displacement equals an existing structured
   proposal associated with that candidate;
9. `PROTOCOL_INSTANCE_COMPATIBLE` — every prior decision is available.

No later decision is produced after an unavailable or failed earlier stage.
Directory existence, free text, acoustic similarity and identifier shape never
establish compatibility.

## Provenance and immutability

Any future recorded instance must preserve all input fields plus the resolved
plan fingerprint and source-object identifiers. The source plan, geometry
candidate, displacement proposal, experiments and measurement files remain
immutable.

Recording a strictly identical `protocol_instance_id` is idempotent. Reusing
that identifier with divergent content is rejected deterministically with the
incompatible field names. Two identifiers never become equivalent through
normalization.

## Scientific boundary

The input is a declaration, not evidence. Even a compatible instance does not
mean that:

- the physical speaker was moved;
- the declared distance was applied;
- acquisition settings remained controlled;
- measurements were captured;
- an SBIR relation, cause or correction was established.

Compatibility may unlock a separate declaration preflight only. Manifest
writing, acquisition, comparison, result evaluation and prescription remain
outside this contract.

Compatible instances are recorded in a dedicated immutable registry. Recording
the same contract again is byte-idempotent; divergent content under the same
`protocol_instance_id` is rejected before any write. This registry is not an
experiment manifest and does not declare an experiment.

## Explicitly outside V1

- free-form protocol authoring;
- selecting a geometry candidate or displacement automatically;
- creating experiment directories;
- modifying manifests;
- launching measurements;
- evaluating observed results;
- promoting causality;
- choosing permanent speaker placement.

## Future acceptance criteria

Implementation must prove with automated tests:

1. strict round-trip serialization;
2. rejection of every missing or unknown field;
3. closed-value and primitive-type validation;
4. exact identifier handling without normalization;
5. reference/moved inequality;
6. finite non-zero displacement validation;
7. exact plan and fingerprint continuity;
8. exact geometry, speaker, surface and displacement-source continuity;
9. deterministic idempotence and divergent-content refusal;
10. no repository access in the JSON loader;
11. no writes during parsing or compatibility preview;
12. no experiment declaration, execution, result or causal promotion.
