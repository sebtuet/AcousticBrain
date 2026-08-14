# Structured listening-position sampling protocol contract

## Purpose

`ListeningPositionSamplingProtocol` is a deterministic scientific description of a multi-position acquisition campaign. It does not create experiment directories, measurements or manifests. It does not alter acoustic analyses, scores, hypotheses, recommendations, causal discrimination or longitudinal learning.

The protocol is optional and must be supplied explicitly through `AcousticBrain.analyze(listening_position_sampling_protocol=...)`. When it is absent or structurally incomplete, the existing `LISTENING_POSITION_MULTI_POINT` candidate remains blocked by `MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE`.

Its projection into future acquisition steps is specified separately by
`LISTENING_POSITION_CAMPAIGN_PLAN_CONTRACT.md`. The protocol remains the sole
source of sampling geometry; the campaign plan does not duplicate or reconstruct
it.

## Protocol structure

A protocol carries only declared data:

- `protocol_id` and positive integer `version`;
- ordered `positions`;
- exactly one modified variable, `LISTENING_POSITION`;
- explicitly controlled variables;
- an explicit comparability rule code;
- the complete set of deterministic completion-condition codes.

No position count, offset, parent, reference or acquisition order is supplied by a default. Geometry belongs to the protocol and is never reconstructed from names, manifests, experiment descriptors or acoustic results.

## Position structure

Each `ListeningPositionSamplingPosition` declares:

- `position_code`;
- `position_role`: `REFERENCE`, `FORWARD` or `BACKWARD`;
- `longitudinal_offset_m`;
- optional `lateral_offset_m` and `vertical_offset_m`, which remain `None` when absent;
- `parent_position_code`;
- `reference_position_code`;
- `acquisition_order`;
- `required_measurements`.

Offsets are protocol data. Additional positions such as `FORWARD_200MM` and `BACKWARD_200MM` require only additional position records; the protocol engine and generator do not change.

## Structural invariants

- Position codes are unique.
- Acquisition orders are explicit, contiguous and start at one.
- A parent must exist and precede its child.
- A reference relation must identify an existing position.
- A complete definition contains exactly one `REFERENCE`, at least one `FORWARD` and at least one `BACKWARD` position.
- The reference has an explicit longitudinal offset of `0.0`.
- Forward longitudinal offsets are explicit and positive.
- Backward longitudinal offsets are explicit and negative.
- Every position explicitly requires `LEFT`, `RIGHT` and `STEREO`.
- The reference has no parent and refers to itself.
- Every non-reference position carries both an explicit parent and the reference position code.

The engine validates these declarations. It never derives a branch from offsets or position-code text.

## Comparability

The protocol carries its comparability rule as data. For the ordered reference branch, every acquired position must reproduce the parent and reference relations declared by the corresponding protocol position. The engine compares the declarations directly; it does not infer an alternative topology.

The modified variable is:

```text
LISTENING_POSITION
```

The controlled variables for a concrete protocol are declared explicitly, for example:

```text
LOUDSPEAKER_POSITION
LOUDSPEAKER_ASSIGNMENT
SIGNAL_CHAIN_ASSIGNMENT
ROOM_CONFIGURATION
MICROPHONE_ORIENTATION
MEASUREMENT_LEVEL
REW_PARAMETERS
```

They are consumed from the protocol and are not restated as modal-generation rules.

## Completeness

`definition_completeness` evaluates whether the protocol itself is executable. `assess(acquisitions)` evaluates an acquired campaign against the same declaration. Both return the deterministic states:

- reference present;
- all forward positions present;
- all backward positions present;
- structured geometry available;
- required `LEFT`/`RIGHT`/`STEREO` measurements available at every position;
- declared comparability relations respected.

The corresponding condition codes are:

```text
REFERENCE_POSITION_PRESENT
FORWARD_POSITION_PRESENT
BACKWARD_POSITION_PRESENT
STRUCTURED_GEOMETRY_AVAILABLE
REQUIRED_MEASUREMENTS_AVAILABLE
COMPARABILITY_RULE_SATISFIED
```

Completeness is true only when no condition code is missing.

## Generator and report

The deterministic experiment generator does not inspect past experiment descriptors to construct a proposed campaign. It consumes a complete `ListeningPositionSamplingProtocol` and projects its positions, offsets, order, relations, measurements, variables, version, comparability rule and completion conditions without changing them.

The console may describe this projection as “Campagne proposée”. This is descriptive output only. No `exp-008`, `exp-009`, `exp-010` or other experiment is created.

## Scientific limits

The protocol does not assert that a position will improve the response. It does not establish causality. It does not modify measured facts, hypotheses, acoustic scores, historical recommendations, causal discrimination or longitudinal learning. Missing protocol data remains missing and is never replaced by an implicit distance or geometry.
