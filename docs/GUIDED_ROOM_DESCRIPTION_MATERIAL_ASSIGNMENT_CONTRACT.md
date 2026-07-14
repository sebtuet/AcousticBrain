# Guided room description and material assignment contract

## Scientific objective

Provide a controlled acquisition workflow for room geometry, surfaces, material
assignments and placements without requiring users to edit the versioned JSON
schema. Conversation assists acquisition; it is never a source of scientific
truth.

## Responsibility boundaries

AcousticBrain detects missing facts, chooses the next useful question, exposes
allowed values and constraints, constructs a non-persisted proposal, validates
it, requests explicit confirmation, persists it and runs a complete new
analysis.

Ollama may reformulate a structured question and map free text to candidates
already authorized by AcousticBrain. It may report ambiguity, contradiction or
insufficient information. It cannot create acoustic coefficients, choose an
unconfirmed target, modify `RoomDescription`, decide protocol eligibility or
derive causal conclusions.

## Workflow

`QuestionPlan -> user answer -> candidate interpretation -> ChangeProposal ->
deterministic validation -> before/after summary -> explicit confirmation ->
persistence -> complete AcousticBrain analysis`

The proposal states are `DRAFT`, `NEEDS_CLARIFICATION`, `INVALID`,
`READY_FOR_CONFIRMATION`, `CONFIRMED`, `APPLIED` and `REJECTED`. `CONFIRMED`
and `APPLIED` are strictly distinct. Only `CONFIRMED` proposals can be applied.

## Provenance

Profile origins include `MEASURED`, `MANUFACTURER_DATA`, `CATALOG_ESTIMATE`
and `USER_PROVIDED`. Description origins include
`USER_DESCRIPTION_INTERPRETED`, `USER_STRUCTURED_INPUT` and
`IMPORTED_PROJECT_DATA`. Description confidence never replaces profile
confidence.

## Informative projections

`potentially_unblocked_capabilities` and predicted completeness changes are
informative projections. They never assert eligibility. Applying a proposal
never edits conclusions; it always triggers a complete new analysis.

## Target ambiguity

A semantic role may match several surfaces. AcousticBrain may select a target
without confirmation only when exactly one candidate exists. Otherwise the
proposal remains `NEEDS_CLARIFICATION` until an explicit target is supplied.

## Versioned catalog

Catalog identifiers are immutable and explicitly versioned, for example
`material.gypsum_board_painted.v1`. There is no implicit latest-version
resolution. Historical projects are never reinterpreted when a later catalog
entry is introduced.

## Persistence and compatibility

Schema v5 adds description provenance, description confidence and immutable
catalog references. Reading v1 through v4 remains supported and migration is
additive. Legacy projects gain no inferred material, profile or provenance.

## Exclusions

- no modification of modal, SBIR or reflection calculations;
- no modification of experiment protocols or causal conclusions;
- no automatic application without confirmation;
- no second-order reflections, diffraction or probabilistic hypothesis ranking;
- no dependency on Ollama for deterministic tests or structured input.

## Isolated end-to-end review demo

The guided workflow is deliberately separate from the automatic behavior of
`main.py`. Reviewers can exercise the complete vertical slice with no access to
local measurement folders and no project-file writes:

```bash
.venv/bin/python -m acousticbrain.commands.demo_guided_room_description --scenario confirmed
```

This scenario constructs a synthetic project in memory, plans the next material
question, interprets `plaque de plâtre` through the controlled vocabulary,
shows that serialized room data is unchanged before confirmation, confirms and
applies the proposal, then invokes the real `AcousticBrain.analyze()` pipeline
exactly once on the updated project.

The conservative ambiguity path is available separately:

```bash
.venv/bin/python -m acousticbrain.commands.demo_guided_room_description --scenario ambiguous
```

It must return `NEEDS_CLARIFICATION`, select no catalog entry, persist nothing,
and trigger no new analysis. Both commands print structured JSON evidence,
including immutable catalog identity, distinct descriptive/profile provenance,
confirmation and application states, and the disclaimer that projected
capabilities are not eligibility results.
