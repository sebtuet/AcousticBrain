# Listening Position Campaign Plan Contract

## Purpose

`ListeningPositionCampaignPlan` is the deterministic projection between a
structured multi-position protocol and future experiments. The architecture is:

`hypothesis -> experimental candidate -> sampling protocol -> campaign plan -> future experiments -> measurements`.

The plan is distinct from the protocol, the candidate, an experiment manifest,
an observed experiment and longitudinal learning. It is a read-only business
projection: building it creates no directory, manifest, measurement or experiment.

## Sources and provenance

The builder consumes only:

- the `LISTENING_POSITION_MULTI_POINT` candidate produced by the deterministic
  hypothesis/experiment generator;
- the complete `ListeningPositionSamplingProtocol` supplied through the public
  analysis API;
- discovered experiment descriptors;
- the structured experiment-comparison chronology and local eligibility;
- structured experiment declarations.

Every plan records its candidate, hypothesis, protocol identifier/version and,
when admissible, its existing reference experiment. It never reserves or
constructs a future `exp-XXX` identifier.

## Reference selection

References are inspected in reverse structured chronology order. The first
admissible descriptor is retained; the last directory or lexical identifier is
never assumed to be valid merely because it is last.

An admissible reference must satisfy all of these implemented rules:

1. its descriptor is `READY`;
2. `LEFT`, `RIGHT` and `STEREO` are available;
3. it is the `after_experiment_id` of a local comparison classified
   `COMPARABLE`;
4. its experiment declaration is not `UNKNOWN`;
5. its declared modified and controlled variables jointly cover every variable
   that the sampling protocol requires to remain controlled.

If no descriptor satisfies these rules, the plan is `BLOCKED` with
`CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE`. No reference is inferred.

## Step projection

Each protocol position is projected exactly once and in its declared acquisition
order. Geometry is copied without conversion or defaults: longitudinal, lateral
and vertical offsets retain their exact values, including `None`. Position codes
are mapped to stable internal identifiers using
`campaign-step.<position_code>`; these are plan identifiers, not experiment
identities.

Parent and reference position codes are mapped to their corresponding internal
step identifiers. The existing reference experiment is recorded separately.
Modified variables, controlled variables, required measurements and the
comparability rule are copied from the protocol. Every step requires exactly
`LEFT`, `RIGHT`, `STEREO`.

## Structural invariants

A plan validates:

- unique step identifiers and position codes;
- a total, contiguous and deterministic order;
- exactly one `REFERENCE` step;
- known parent and reference relations;
- parents that precede children, preventing parent cycles;
- zero longitudinal offset for the reference position;
- positive longitudinal offsets for `FORWARD` positions;
- negative longitudinal offsets for `BACKWARD` positions;
- exact plan/step controlled variables, measurements, comparability rule and
  existing reference;
- `NOT_ESTABLISHED` causality.

The reference step may reference its own identifier as a scientific reference;
this is not an execution dependency. Parent relations alone define execution
dependencies and must be acyclic.

## Statuses

- `READY`: candidate eligible, protocol complete, existing reference admissible,
  geometry/relations complete, measurements and comparability rule available.
- `BLOCKED`: the plan remains visible but is not executable and carries at least
  one structured blocking reason.
- `COMPLETE`: reserved for a future observed execution lifecycle.
- `NOT_APPLICABLE`: reserved for a future explicit non-applicability projection.

Implemented blocking reasons are:

- `MULTI_POSITION_SAMPLING_GEOMETRY_UNAVAILABLE`;
- `CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE`;
- `CAMPAIGN_STEP_RELATION_INVALID`;
- `REQUIRED_MEASUREMENTS_UNAVAILABLE`;
- `COMPARABILITY_RULE_UNAVAILABLE`;
- `SOURCE_CANDIDATE_NOT_ELIGIBLE`.

A blocked plan propagates its reasons to the derived experimental candidate.
Consequently it cannot be the main executable action and the legacy experiment
planner remains `NO_ELIGIBLE_CANDIDATE` unless another executable candidate is
available.

## Scientific limits

The plan does not establish causality, predict improvement, add acoustic
thresholds, alter scores or recommendations, or reinterpret historical results.
It does not create files, change the current working directory, mutate source
analyses, assign future experiment identities or modify a personal campaign.

Future campaign types may introduce their own protocol and plan builders. They
must preserve the separation between protocol definition, deterministic plan,
future experiment creation and observed longitudinal state.
