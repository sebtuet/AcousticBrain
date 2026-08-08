# Guided declared CHANNEL_ISOLATION contract

```text
contract_id = acousticbrain.guided_declared_channel_isolation.v1
version = 1
status = FROZEN
authority = EXISTING_EXPERIMENT_LIFECYCLE_PROJECTION_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Continue the guided journey after a qualified declaration without treating a
manifest or directory as evidence of execution.

```text
explicit experiment_id
+ exact selected preparation
→ existing experiment user view lifecycle
→ exact preparation provenance continuity
→ ACQUISITION_PENDING or ACQUISITION_INCOMPLETE
→ one acquisition action
```

## Exact resolution

`--guided-declared-experiment` is valid only with `--guided-status`, an
explicit preparation registry and one exact preparation identifier. It cannot
be combined with declaration-readiness identifiers or operational worksheet
inputs.

The existing experiment user-view presenter resolves the experiment exactly
and remains the sole lifecycle authority. The guided projection additionally
requires exact equality of source plan id, preparation confirmation id, plan
fingerprint and `ALL_PREREQUISITES_USER_CONFIRMED` qualification. Missing or
divergent provenance is rejected before rendering. The existing specialized
coverage status must be `PLAN_COVERAGE_PARTIAL` or `PLAN_COVERAGE_COMPLETE`;
an insufficient or absent `channel_isolation_declaration` never qualifies.

## Closed states

```text
READY_PLAN_EXPERIMENT_DECLARED_ACQUISITION_PENDING
READY_PLAN_EXPERIMENT_DECLARED_ACQUISITION_INCOMPLETE
```

Other experiment lifecycle states remain owned by `--experiment-view` and are
not reinterpreted here.

## Scientific boundary

The view is read-only. A manifest with no acquired files is
`ACQUISITION_PENDING`, never `EXECUTED`. A partial file set is
`ACQUISITION_INCOMPLETE`, never successful. The view writes no file, launches
no measurement, evaluates no result and establishes no causality.

## CLI

```text
python main.py --measurements-root PATH --guided-status \
  --guided-preparation-registry REGISTRY_PATH \
  --guided-preparation CONFIRMATION_ID \
  --guided-declared-experiment EXPERIMENT_ID
```
