# Geometry-driven SBIR contract

## Invariants

- Each layer produces new knowledge from facts already produced by the lower
  layer. It does not reopen measurements or recompute their conclusions.
- Geometry-to-frequency compatibility is evidence of compatibility only. It is
  never causal proof.
- A causal SBIR conclusion requires a declared discriminating protocol and an
  explicit before/after comparison.
- No experiment is inferred from a recommendation, a directory name or a
  measurement sequence.
- Every prediction, correlation, hypothesis, recommendation and experiment
  candidate preserves uncertainty, confidence, source analyses and geometry
  provenance.
- The planner records every failed eligibility condition.
- The geometry-driven early-reflection contract remains unchanged. SBIR
  prediction consumes its derived paths rather than deriving those paths again.

## Scope and derived prediction

`GeometrySBIRPredictionEngine` consumes `RoomGeometry` and the first-order paths
already produced by `GeometryEarlyReflectionEngine`. It accepts only the six
rectangular room boundaries and rectangular placed surface regions. Arbitrary
polygons are outside this contract.

For each loudspeaker, listening position and valid boundary path it records:

- the named surface and physical relationship to the loudspeaker;
- the impact point, direct path, reflected path and excess distance;
- the loudspeaker-to-boundary distance;
- the first expected cancellation frequency, `c / (2 * excess distance)`;
- propagated distance and frequency uncertainty;
- conservative geometrical confidence;
- the complete provenance inherited from the room datum and derived path.

This layer does not inspect frequency measurements and produces no hypothesis,
recommendation or experiment.

## Frequency-domain compatibility

`SBIRGeometryCorrelationEngine` compares derived predictions with already
observed frequency-response dips. A correlation retains both source facts, the
absolute and relative frequency errors, a deterministic match score,
confidence and provenance.

The correlation code describes compatibility only. It must not contain or
imply `CAUSE`, `CAUSED_BY`, `CONFIRMED` or an equivalent causal assertion.
Reasoning may create a structured `SBIR_PLACEMENT_INTERACTION` hypothesis from
that compatibility while retaining the explicit non-causal limitation.

## Discriminating protocol

`protocol.temporary_move_speaker.v1` is eligible only when all of the following
are available:

- an exact named surface, loudspeaker and listening position;
- a geometry candidate and its source reflection path;
- a predicted and an observed cancellation frequency;
- a frequency error no greater than **15%**;
- propagated prediction uncertainty no greater than **10%**;
- geometrical confidence of at least **70/100**;
- a finite, reversible, non-zero proposed loudspeaker displacement.

The protocol modifies only `LOUDSPEAKER_POSITION`. It controls:

- `MICROPHONE_POSITION`;
- `LOUDSPEAKER_ORIENTATION`;
- `OTHER_LOUDSPEAKER_POSITIONS`;
- `SIGNAL_CHAIN_ASSIGNMENT`;
- `MEASUREMENT_LEVEL`;
- `ROOM_CONFIGURATION`.

Its discriminating observations are:

- `SBIR_MOVES_WITH_SPEAKER`;
- `SBIR_REMAINS_FIXED`.

The declaration service records the named speaker, surface, geometry candidate,
displacement, controlled variables, modified variable and expected observations
without creating or altering measurement facts.

## Planning and auditability

An ineligible candidate remains visible with explicit reasons, including
missing geometry, excessive frequency mismatch, excessive prediction
uncertainty and insufficient confidence. Completion is recognized only from an
explicit manifest declaration of `TEMPORARY_SPEAKER_MOVE` under the protocol.

Legacy SBIR analysis and reports remain available when exact geometry-driven
facts do not exist. Exact geometry-driven correlations suppress duplicate
generic distance recommendations but never erase their source evidence.
