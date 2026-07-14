# Geometry-driven early reflections contract

## Invariants

- Each layer consumes facts produced by the immediately lower layer. It does not
  reopen REW files or recompute lower-level facts.
- A geometrical match is a compatibility fact, not a causal conclusion.
- Causality requires a declared discriminating protocol and an explicit
  before/after experiment.
- No experiment is inferred from a recommendation or a user action.
- Every conclusion preserves its fact codes, limits, source analyses and
  declared geometrical provenance.
- The planner always records why a candidate is ineligible.

## Description and derived geometry

`RoomDescription` remains the user-owned source. Its rectangular surfaces,
placed surface regions, openings, furniture, loudspeakers and listening
positions are converted once into `RoomGeometry`. Optional
`GeometryDatumQualityDescription` entries attach a precision, confidence and
provenance to each named datum.

`GeometryEarlyReflectionEngine` is a derived factual layer. For first-order
specular reflections it computes:

- the image-source path and its exact named surface or placed region;
- the impact point, direct and reflected lengths and theoretical excess delay;
- propagated timing uncertainty and conservative geometrical confidence;
- exclusions caused by openings and geometrically placed obstacles.

It does not inspect ETC events and does not create hypotheses or actions.

## ETC compatibility

`ETCReflectionCorrelationEngine` compares already-observed ETC events with
already-derived paths. A correlation retains the observed event, named surface,
impact point, theoretical delay, timing error, uncertainty, confidence and
provenance. This match may support an acoustic hypothesis, but it does not prove
that the surface caused the event.

## Discriminating protocol

`protocol.temporary_mask_surface.v1` is eligible only when all of the following
are available:

- an exact named surface;
- an observed channel, event delay and reference level;
- a derived path and theoretical delay;
- a timing error no greater than **1.0 ms**;
- a propagated geometrical uncertainty no greater than **0.5 ms**;
- a geometrical confidence of at least **70/100**.

The protocol changes only the temporary masking of the named surface. The
microphone position, source position and orientation, signal chain, measurement
level and room configuration remain controlled. Its discriminating outcomes are:

- `REFLECTION_DECREASES_AFTER_MASKING`;
- `REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING`.

Failing thresholds remain explicit planner facts:

- `GEOMETRY_PARAMETER_MISSING`;
- `GEOMETRY_TIMING_INCOMPATIBLE`;
- `GEOMETRY_UNCERTAINTY_TOO_HIGH`;
- `GEOMETRY_CONFIDENCE_TOO_LOW`.
