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
→ ACQUISITION_PENDING, ACQUISITION_INCOMPLETE,
  COMPARISON_UNAVAILABLE, RESULT_INCONCLUSIVE
  or RESULT_AVAILABLE
→ one existing lifecycle action
```

## Exact resolution

`--guided-declared-experiment` is valid only with `--guided-status`, an
explicit preparation registry and one exact preparation identifier. It cannot
be combined with declaration-readiness identifiers or operational worksheet
inputs.

When no experiment identifier is supplied, the view may enumerate discovered
experiments carrying the exact selected preparation identifier. It never
selects one implicitly, including when exactly one candidate exists. Candidate
identifiers are sorted, duplicate identities are rejected, and plan,
fingerprint, qualification and specialized declaration coverage must remain
exactly compatible with the selected preparation.

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
READY_PLAN_EXPERIMENT_ACQUISITION_COMPLETE_COMPARISON_UNAVAILABLE
READY_PLAN_EXPERIMENT_RESULT_INCONCLUSIVE
READY_PLAN_EXPERIMENT_RESULT_AVAILABLE
READY_PLAN_DECLARED_EXPERIMENT_SELECTION_REQUIRED
READY_PLAN_DECLARED_EXPERIMENT_SELECTION_AMBIGUOUS
```

`COMPARISON_UNAVAILABLE` is accepted only with
`PLAN_COVERAGE_COMPLETE`. It records that the specialized declared acquisition
is complete while no unique comparable local comparison exists. Other
experiment lifecycle states remain owned by `--experiment-view` and are not
reinterpreted here.

Result states additionally require `PLAN_COVERAGE_COMPLETE`, one exact local
`comparison_id`, one exact reference experiment, and the existing
`REVIEW_OBSERVED_RESULT` action. Their accepted outcome sets are closed:

```text
RESULT_INCONCLUSIVE → MIXED or INCONCLUSIVE
RESULT_AVAILABLE    → IMPROVED, DEGRADED or UNCHANGED
```

The observed outcome is copied verbatim. The guided presenter never derives,
groups, softens or promotes it. `MIXED` remains textually visible.

## Scientific boundary

The view is read-only. A manifest with no acquired files is
`ACQUISITION_PENDING`, never `EXECUTED`. A partial file set is
`ACQUISITION_INCOMPLETE`, never successful. Complete declared acquisition with
no unique comparable local comparison is `COMPARISON_UNAVAILABLE`, never an
observed result. The view writes no file, launches no measurement, creates no
comparison, evaluates no result and establishes no causality.

When an existing unique comparable local comparison is present, the view may
display its existing result and identifier. This is a read-only projection,
not a new evaluation. `causality_status` must remain `NOT_ESTABLISHED`.

## CLI

```text
python main.py --measurements-root PATH --guided-status \
  --guided-preparation-registry REGISTRY_PATH \
  --guided-preparation CONFIRMATION_ID \
  --guided-declared-experiment EXPERIMENT_ID
```
