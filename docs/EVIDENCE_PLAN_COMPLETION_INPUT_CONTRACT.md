# Evidence plan completion input contract

```text
contract_id = acousticbrain.evidence_plan_completion_input.v1
version = 1
status = FROZEN
authority = CONTRACTUAL_TRANSFORMATION_ONLY
scientific_authority = NONE
implementation_status = NOT_IMPLEMENTED
```

## Purpose

This contract defines the only authorized V1 transition from an existing
evidence-acquisition plan blocked by `compatible_protocol_or_plan_id` to a new
derived plan that may become `READY`.

It does not mutate or promote the source plan. It records one explicit
structured completion input, resolves one existing reference, validates that
reference through existing structured compatibility evidence, and creates a
new traceable plan only when the derived contract is complete.

```text
source plan BLOCKED
→ explicit structured completion input
→ exact existing reference resolution
→ existing compatibility validation
→ new derived plan
→ existing plan-contract declaration workflow
```

This contract does not authorize execution, prescription, protocol invention,
free-text interpretation, causal promotion, or a generic parameter-completion
engine.

## V1 scope

V1 supports exactly one missing input code:

```text
compatible_protocol_or_plan_id
```

The source plan must:

- be resolved exactly by `source_plan_id`;
- have status `BLOCKED`;
- declare `compatible_protocol_or_plan_id` in `required_inputs`;
- retain a blocking factor whose structured source identifies that missing
  input;
- belong to the current deterministic report without collection-order
  dependence.

Any other missing input or blocking reason is outside V1. A completion input
cannot hide, delete or satisfy another blocking condition.

## Completion input

One command consumes exactly one immutable structured input:

```json
{
  "schema_version": 1,
  "completion_input_id": "completion-input-001",
  "source_plan_id": "EVIDENCE_ACQUISITION_..._DISCRIMINATE_HYPOTHESES",
  "reference_kind": "PROTOCOL",
  "reference_id": "protocol.example.v1",
  "declaration_source": "USER_JSON",
  "user_note": null
}
```

Required fields are:

- `schema_version` equal to `1`;
- globally stable, non-empty `completion_input_id`;
- exact non-empty `source_plan_id`;
- `reference_kind`, equal to `PROTOCOL` or `PLAN`;
- exact non-empty `reference_id`;
- explicit non-empty `declaration_source`.

`user_note` is optional text. It is archival only. It cannot supply an
identifier, parameter, compatibility claim, justification, criterion or
scientific rule.

Unknown fields are rejected. No field is inferred from filenames, labels,
notes, objectives, instructions, hypotheses, measurements or collection
position.

## Identity and cardinality

One operation targets exactly one source plan and one candidate reference.

The operation rejects:

- an unknown or non-unique `source_plan_id`;
- an unknown or non-unique `(reference_kind, reference_id)`;
- more than one completion input;
- more than one candidate reference;
- a reference whose exact identity is the source plan itself;
- aliases or equivalent identifiers that resolve to several objects;
- a source plan that is not `BLOCKED`;
- a source plan that does not declare the V1 missing input;
- a source plan with another unresolved blocking condition.

Reference-kind separation is strict. A protocol and a plan carrying the same
string identifier are different objects and do not resolve each other.

## Three separate decisions

The completion workflow exposes three decisions without collapsing them:

```text
REFERENCE_RESOLVED
REFERENCE_COMPATIBLE
DERIVED_PLAN_READY
```

Each decision is independently traceable.

### `REFERENCE_RESOLVED`

The exact `(reference_kind, reference_id)` identifies one existing structured
object. Resolution establishes identity only. It does not establish scientific
compatibility or plan readiness.

### `REFERENCE_COMPATIBLE`

Compatibility is true only when an existing deterministic source object under
an already-authorized contract explicitly associates the reference with the
source plan's action, reasoning, hypothesis or acquisition need.

V1 must not create a compatibility table, compare free text, compare names,
compare frequency ranges heuristically, or treat shared measurements as
compatibility. If no existing authority can establish compatibility, the
decision is unavailable or false and no derived `READY` plan is created.

### `DERIVED_PLAN_READY`

This decision is true only when:

- source plan identity is exact;
- reference identity is exact;
- compatibility is established by an existing authority;
- the reference supplies every acquisition parameter required by the source
  plan's existing contract;
- no source blocking condition remains unresolved;
- derived-plan provenance is complete.

`REFERENCE_RESOLVED` does not imply `REFERENCE_COMPATIBLE`.
`REFERENCE_COMPATIBLE` does not imply `DERIVED_PLAN_READY`.

## Derived plan

The operation creates a new `EvidenceAcquisitionPlan`. It never modifies the
source instance or reuses its `plan_id`.

The derived plan retains explicitly:

- a new stable `plan_id`;
- `source_plan_id`;
- `completion_input_id`;
- `reference_kind` and exact `reference_id`;
- the compatibility authority identifier and version;
- the source reasoning, action, evidence-weight and blocking-factor provenance;
- the V1 contract id and version.

The new identity is deterministic from the canonical completion contract. The
same source plan and byte-equivalent normalized completion input resolve to the
same derived identity. A difference in any normalized completion field,
including `completion_input_id`, reference, reference kind, declaration source
or `user_note`, produces a different identity.

The source plan remains readable and `BLOCKED`. Historical reports must be
able to display both plans and their derivation link.

## Fields that cannot change

Completion cannot change the source plan's:

- objective;
- scientific justification or upstream reasoning;
- priority;
- estimated effort;
- test type;
- instructions;
- controlled or independent variables;
- measurements to capture;
- expected observations;
- success or failure criteria;
- evidence targets;
- scientific limitations.

V1 may replace only the explicitly missing
`compatible_protocol_or_plan_id` requirement with the exact resolved reference
and with acquisition parameters already carried by that reference under its
existing contract.

If completion would require changing any protected field, adding an undeclared
parameter, selecting among scientific alternatives or interpreting a note, it
is rejected.

## Status preservation

The source status never changes.

The derived plan is `READY` only when `DERIVED_PLAN_READY` is established. If
resolution, compatibility or completeness fails, the operation returns an
explicit deterministic failure and creates no derived plan. V1 does not create
a partially derived plan and does not use `PROPOSED` as a silent fallback.

`READY` means structurally ready for the existing explicit plan-contract
declaration operation. It does not mean executed, successful, prescriptive,
optimal or causally validated.

## Idempotence and divergence

An identical completion is idempotent:

- the same canonical input produces the same derived plan identity;
- an already persisted byte-equivalent completion is not rewritten;
- no duplicate derived plan or provenance event is created.

A divergent second completion for the same `completion_input_id` is rejected.
The error lists incompatible field paths in deterministic sorted order.

A second completion using another `completion_input_id` does not overwrite the
first. If it targets the same source plan, it is a distinct candidate
derivation and must not be selected implicitly. Any consumer requiring one
derived plan must reject that ambiguity or require an exact derived `plan_id`.

## Failure states

Failures are explicit and deterministic. V1 distinguishes at least:

```text
SOURCE_PLAN_UNKNOWN
SOURCE_PLAN_AMBIGUOUS
SOURCE_PLAN_NOT_BLOCKED
SOURCE_PLAN_NOT_V1_COMPLETABLE
SOURCE_PLAN_HAS_OTHER_BLOCKERS
REFERENCE_UNKNOWN
REFERENCE_AMBIGUOUS
REFERENCE_SELF_REFERENCE
REFERENCE_INCOMPATIBLE
REFERENCE_COMPATIBILITY_NOT_ESTABLISHED
REFERENCE_CONTRACT_INCOMPLETE
COMPLETION_INPUT_DIVERGENT
DERIVED_IDENTITY_AMBIGUOUS
```

Failure messages identify the relevant source and reference ids. They never
recommend or substitute another reference.

## Persistence and atomicity

The implementation must validate the complete operation before writing. A
failure writes nothing.

Persistence must retain the normalized completion input, the three decisions,
their source identifiers, the derived plan and the derivation link. It must use
the repository's existing atomic-write behavior and must never modify
measurement files, the source plan snapshot, an existing experiment manifest,
or a protocol declaration.

Creation of a derived plan and declaration of an experiment are separate
explicit operations. After a derived plan is `READY`, the existing
`EvidenceAcquisitionPlanContractService` remains the only V1 path from that
plan to an experiment manifest.

## Acceptance criteria

An implementation conforms only when automated tests demonstrate:

1. exactly one source plan and one reference are resolved;
2. source and reference collection order does not affect the result;
3. unknown, ambiguous and self references are rejected;
4. a protocol and plan with the same textual id remain distinct;
5. compatibility uses an existing structured authority only;
6. absent compatibility is never inferred;
7. the source plan remains byte-for-byte and semantically unchanged;
8. the source plan remains `BLOCKED`;
9. the derived plan has a new deterministic identity;
10. provenance retains `source_plan_id`, `completion_input_id`, reference and
    compatibility authority;
11. protected scientific and prioritization fields remain unchanged;
12. other blockers prevent derivation;
13. `REFERENCE_RESOLVED`, `REFERENCE_COMPATIBLE` and `DERIVED_PLAN_READY`
    remain distinct;
14. identical completion is idempotent;
15. divergent reuse of `completion_input_id` reports sorted incompatible
    fields;
16. multiple derivations are never selected implicitly;
17. no measurement, source plan, manifest or protocol is modified;
18. no experiment is executed or declared by completion alone;
19. `PRESCRIPTIVE` behavior and causal status remain unavailable;
20. the existing READY-plan declaration workflow remains unchanged.

## Explicitly outside V1

V1 does not add:

- generic completion of arbitrary missing parameters;
- protocol authoring or protocol discovery;
- compatibility inference;
- free-text parsing;
- scientific ranking or selection between references;
- plan mutation or status promotion;
- experiment directory creation;
- experiment declaration or execution;
- measurement validation;
- comparison or result evaluation;
- prescriptive decisions;
- causal conclusions.
