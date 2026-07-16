# Causal source comparison association contract

## Purpose

A causal protocol step and a local experimental comparison are distinct source
declarations. `causal_protocol_step` states which controlled step was executed
and which causal observation the user qualified. It does not state that the
measurement comparison belongs to a scientific protocol or hypothesis.

`CausalSourceComparisonAssociationService` provides that missing explicit
boundary. It associates one existing local comparison with one supported
protocol/hypothesis pair. Nothing is inferred from the experiment directory,
the modified variable, or the presence or name of a causal step.

The four declarations remain separate:

- `experiment_declaration`: reference, modified and controlled variables;
- `causal_protocol_step`: executed step and explicit causal observation;
- `comparison`: parent and scientific source association;
- causal discrimination: deterministic interpretation of already-declared
  observations against discriminations opened by the source comparison.

## Supported scope

This contract supports only:

- protocol `protocol.verify_speaker_room_asymmetry.v1`;
- hypothesis `ASYMMETRIC_SPEAKER_ROOM_INTERACTION`;
- `STEP_2_SPEAKER_SWAP`;
- `STEP_3_SIGNAL_CHAIN_SWAP`.

The causal step itself continues to use the operational code
`VERIFY_SPEAKER_ROOM_ASYMMETRY`. Other known protocol/hypothesis combinations
are rejected as incompatible; unknown identifiers are rejected separately.

## Coherence requirements

The target directory and a valid `READY` manifest must exist. The manifest must
already contain:

- a `comparison` with exactly one existing parent directory;
- a `CONTROLLED_INTERVENTION` declaration whose reference equals that parent;
- a supported `causal_protocol_step`;
- the expected modified variable in both the causal step and the experiment
  declaration.

For STEP_2 the expected variable is `LOUDSPEAKER_ASSIGNMENT`; for STEP_3 it is
`SIGNAL_CHAIN_ASSIGNMENT`. The two declared variable sets must agree. An
optional CLI reference is only a consistency assertion and is rejected when it
differs from the manifest parent.

Existing conflicting source metadata or the other causal swap code is rejected
instead of overwritten. Existing comparison parameters and extension fields
are preserved.

## Persisted comparison metadata

STEP_2 adds `CONTROLLED_LOUDSPEAKER_SWAP`; STEP_3 adds
`CONTROLLED_SIGNAL_CHAIN_SWAP`. The service writes the canonical parent,
protocol and hypothesis, merges the applicable change code, and requires these
already-projected scalar facts:

- `spatial.left_right.level_difference_abs_db`;
- `direct_reverberant.left_right.maximum_difference_abs_db`;
- `bass_decay.left_right.maximum_difference_abs_s`;
- `etc.channel_specific_event_count`.

The planner's `stereo.symmetry_score`, `spatial.pair_analysis`,
`etc.channel_specific_event_difference` and `verification.*` identifiers are
not scalar facts projected by `ExperimentFactProjector`; this association does
not invent them. Required facts determine comparison eligibility. Declared
change codes determine the comparison's remaining discriminations.

The automatic comparison projects the descriptor metadata to both the local
and cumulative views. Causal initialization uses only the first chronologically
ordered local comparison explicitly associated with this protocol and
hypothesis. Later associated comparisons do not create or merge a second
initial source.

## Command

```bash
python -m acousticbrain.commands.associate_causal_source_comparison \
  measurements exp-005 \
  --protocol protocol.verify_speaker_room_asymmetry.v1 \
  --hypothesis ASYMMETRIC_SPEAKER_ROOM_INTERACTION \
  --reference exp-004
```

For exp-006, the reference is exp-005. Omitting `--reference` uses the unique
parent already declared in `comparison`; it never derives a parent from the
directory name or chronology.

## Persistence and errors

The existing `MeasurementRepository.save_manifest` operation provides sorted,
atomic, idempotent JSON writes. Repeating an identical association does not
rewrite the file. `files`, `content_hash`, `channel_assignments`,
`causal_protocol_step`, measurements and all unrelated manifest keys remain
unchanged. WAV, TXT and MDAT files are never opened for writing.

Errors distinguish missing directories/manifests, non-READY experiments,
missing or ambiguous parents, unknown identifiers, incompatible pairs, absent
causal steps, variable inconsistencies, parent inconsistencies and conflicting
existing comparison metadata.

## Causal and longitudinal impact

Association is not evidence and is not a causal conclusion. It only makes the
source comparison eligible to initialize the pre-existing causal
discriminations. Explicit STEP_2 and STEP_3 observations may then produce
`DISCRIMINATED` when the existing rules resolve every initially open
discrimination.

`SOURCE_COMPARISON_UNAVAILABLE` disappears only because a valid explicit source
now exists. Longitudinal learning may leave `INSUFFICIENT_CAUSAL_CONTEXT` and
use its existing valid-discrimination projection. In every case:

- `causality_status` remains `NOT_ESTABLISHED`;
- trajectories remain only `COMPATIBLE` or `CONTRADICTED`;
- no `CONFIRMED`, `ESTABLISHED` or new causal completion status is introduced;
- `CAUSAL_NEVER_CONFIRM_TRAJECTORY` remains unchanged.

## exp-005 / exp-006 example

exp-005 associates `exp-004 → exp-005`, STEP_2 and
`CONTROLLED_LOUDSPEAKER_SWAP`. exp-006 associates `exp-005 → exp-006`, STEP_3
and `CONTROLLED_SIGNAL_CHAIN_SWAP`. Both carry the same scientific protocol and
hypothesis. The first associated local comparison initializes the remaining
alternatives; both explicit causal observations are then evaluated by the
existing discriminator.
