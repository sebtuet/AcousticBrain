# Listening Position Campaign Instance Contract

## Role

The declarative campaign instance is the explicit user input between the generic
sampling protocol and the deterministic campaign plan:

`protocol -> user instance -> campaign plan -> future experiments`.

The protocol defines allowed roles, measurements, controlled variables,
comparability and completion conditions. The instance supplies concrete
positions, geometry, order and the requested existing reference. The plan
validates this input against observed campaign facts. None of these objects is an
experiment manifest or longitudinal observation.

## JSON declaration

The CLI accepts an explicitly selected UTF-8 JSON file with `schema_version: 1`.
There is no automatic discovery and no active default file. Every structural
field is required, including nullable offsets and relations; only `notes` may be
omitted. Array order is preserved and never silently sorted.

The editable file at
`docs/examples/listening-position-campaign.example.json` is documentation only.
Its distances and `exp-007` reference are illustrative values, not defaults, and
the engine never loads it automatically.

## Known protocol contract

Schema version 1 recognizes
`protocol.verify_modal_bass_persistence.v1`, protocol version `1`. Its existing
declarative contract requires:

- roles `REFERENCE`, `FORWARD`, `BACKWARD`;
- measurements `LEFT`, `RIGHT`, `STEREO`;
- comparability rule `LISTENING_POSITION_ORDERED_REFERENCE_BRANCH`;
- the controlled-variable tuple declared in the example;
- the PR-050 completion conditions.

The contract contains no position, distance or experiment reference.

## Syntax and semantic validation

The standard-library JSON loader validates file existence, file type, JSON
syntax, schema version, required fields and explicit value types. The immutable
model then validates:

- known protocol and compatible version;
- non-empty instance identity and explicit scientific reference;
- unique position codes and one-based, contiguous, already-sorted order;
- exactly one reference plus forward and backward branches;
- finite numeric offsets or `null`;
- zero reference, positive forward and negative backward longitudinal offsets;
- known and acyclic ordered parent relations;
- explicit reference relations;
- exact per-instance and per-position measurements and controlled variables;
- `LISTENING_POSITION` as the sole modified variable on moved branches;
- no position code shaped as a future `exp-XXX` identity.

The sign checks express role consistency only. AcousticBrain does not decide
whether a user-selected distance is scientifically optimal and applies no
acoustic threshold.

## Validation results

Valid declarations produce status `VALID`. Invalid declarations preserve a
structured code and readable message, using:

- `CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH`;
- `CAMPAIGN_INSTANCE_SCHEMA_INVALID`;
- `CAMPAIGN_INSTANCE_POSITION_INVALID`;
- `CAMPAIGN_INSTANCE_RELATION_INVALID`;
- `CAMPAIGN_INSTANCE_MEASUREMENTS_INCOMPLETE`;
- `CAMPAIGN_INSTANCE_CONTROLLED_VARIABLES_INCOMPATIBLE`;
- `CAMPAIGN_INSTANCE_REFERENCE_INVALID`.

CLI input errors terminate with a non-zero status and no traceback. Invalid
analysis projections remain renderable as `INVALID` for structured consumers.

## Reference validation and plan projection

A requested reference is never substituted. PR-051 accepts that exact experiment
only when it is `READY`, contains `LEFT`, `RIGHT`, `STEREO`, is the target of a
local `COMPARABLE` comparison, has a non-`UNKNOWN` declaration and covers all
controlled configuration variables. Otherwise the instance stays valid but the
plan is `BLOCKED` with `CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE`.

A valid plan copies every position, offset (including `None`), order, relation,
measurement, variable, comparability rule and reference without rounding or
transformation. No fallback branch or future experiment identity is created.

## Read-only guarantee

Loading and planning read the selected JSON and campaign only. They never modify
the instance source, current working directory, measurement root, manifests,
REW exports, impulse files or experiment directories. The technical source path
may be printed in console traceability but is excluded from the scientific
`to_dict()` projection.
