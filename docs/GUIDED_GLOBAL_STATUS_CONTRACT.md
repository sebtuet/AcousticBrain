# Guided global status contract

```text
contract_id = acousticbrain.guided_global_status.v1
version = 1
status = FROZEN
authority = EXISTING_WORKFLOW_STATE_PROJECTION_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Give a non-specialist one read-only answer to: “Where am I, what is blocking
me, and what is the single safe next action?”

```text
current deterministic report
→ existing evidence-plan recommendation
→ optional explicit preparation registry
→ workflow-state projection
→ exactly one user action
```

The view is a presenter over existing decisions. It does not introduce a new
analysis, rank plans again, infer preparation, or create a second experimental
workflow.

## Inputs and resolution

The measurement root is explicit. The current analysis supplies discovered
experiments and the existing deterministic evidence-plan report. When that
report already exposes a `recommended_plan`, the view reuses it verbatim.

A preparation registry is optional and must be passed by an explicit path.
The view never discovers a registry by filename or location. Its absence is
rendered as unavailable, not reconstructed.

An optional explicit preparation `confirmation_id` may be supplied only with
that registry. It resolves exactly one record and must target the recommended
plan. Unknown, ambiguous or cross-plan identifiers are rejected. The view
never fills this identifier itself.

When a registry is supplied, records are matched only by the recommended
plan's exact `plan_id`. Zero, one and multiple matches remain distinct:

- zero: no preparation has been declared for that plan;
- one: identity, fingerprint and prerequisite continuity are validated;
- multiple: the view refuses to select by recency, status or identifier.

A stale or incompatible single record is displayed as stale and is never
silently ignored or repaired.

## Closed workflow states

V1 exposes only:

```text
NO_EVIDENCE_PLAN
NO_READY_EVIDENCE_PLAN
READY_PLAN_PREPARATION_UNAVAILABLE
READY_PLAN_PREPARATION_NOT_DECLARED
READY_PLAN_PREPARATION_AMBIGUOUS
READY_PLAN_PREPARATION_STALE
READY_PLAN_PREPARATION_INCOMPLETE
READY_PLAN_PREPARATION_CONFIRMED
```

These are product-navigation states, not scientific conclusions. A confirmed
preparation remains an unverified user declaration.

## Required blocks

Every successful rendering contains:

1. `État actuel`;
2. `Dernière étape validée`;
3. `Blocage actuel`;
4. `Action utilisateur` with exactly one action;
5. `Frontière scientifique` and `Causality status: NOT_ESTABLISHED`.

Missing content is shown explicitly. No partial rendering occurs after an
ambiguous report identity or invalid typed input.

## Action boundary

Actions route the user only to an existing workflow:

- inspect the evidence-plan overview when no plan is ready;
- inspect the exact recommended plan when preparation state is unavailable;
- generate a preparation draft when no declaration exists;
- select an explicit preparation identifier when several exist;
- regenerate a draft after an incompatible historical record;
- inspect and revise the exact preparation when it is incomplete;
- run the existing declaration-readiness preflight when it is confirmed.

The view never invokes those operations and never recommends changing a user
answer merely to unlock a later step.

## Mutation and scientific boundary

The command is strictly read-only. It does not modify measurements, plans,
registries, manifests, experiments or comparisons. It does not declare or
execute an experiment and does not establish compatibility, validity,
improvement, prescription or causality.

## CLI

```text
python main.py --measurements-root PATH --guided-status

python main.py --measurements-root PATH --guided-status \
  --guided-preparation-registry REGISTRY_PATH

python main.py --measurements-root PATH --guided-status \
  --guided-preparation-registry REGISTRY_PATH \
  --guided-preparation CONFIRMATION_ID
```

`--guided-preparation-registry` and `--guided-preparation` are valid only with
`--guided-status`; the identifier additionally requires the registry. The mode
cannot be combined with another report, view, mutation, exploratory or advisor
mode.

## Acceptance criteria

Tests must demonstrate reuse of the existing recommended plan, explicit
registry absence, exact zero/one/multiple record handling, stale fingerprint
handling, preservation of `UNKNOWN` and `NOT_CONFIRMED`, all-confirmed routing,
exactly five rendered blocks, exactly one action, no writes, no declaration or
execution, deterministic ordering, unchanged historical CLI behavior and
causality `NOT_ESTABLISHED`.
