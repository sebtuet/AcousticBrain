# Channel isolation declaration readiness contract

```text
contract_id = acousticbrain.channel_isolation_declaration_readiness.v1
version = 1
status = FROZEN
authority = DECLARATION_PREFLIGHT_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Provide the final read-only preflight between an explicitly complete
`CHANNEL_ISOLATION` preparation and the existing evidence-plan experiment
declaration command.

```text
exact READY CHANNEL_ISOLATION plan
→ exact recorded preparation
→ ALL_PREREQUISITES_USER_CONFIRMED
→ explicit reference and new experiment identifiers
→ DECLARATION_READY
→ existing declaration command remains separate
```

The preflight reuses the existing plan, preparation and declaration contracts.
It is not another declaration engine.

## Exact inputs

V1 accepts one explicit value for each of:

- `plan_id`;
- recorded preparation `confirmation_id` and its explicit registry;
- existing reference experiment identifier;
- proposed new experiment identifier;
- measurement root.

The plan must resolve exactly once, be `READY`, have test type
`CHANNEL_ISOLATION`, and match the preparation fingerprint. The preparation
must resolve exactly once and carry
`ALL_PREREQUISITES_USER_CONFIRMED`. No preparation is selected by recency,
plan identity or convenience.

The reference must resolve to exactly one existing experiment directory under
the measurement root. The proposed experiment identifier must be exact
non-empty text, must not contain path traversal or directory separators, must
not equal the reference identifier, and its target path must not exist.

## Closed result

Successful preflight returns only:

```text
PLAN_EXACTLY_RESOLVED
PREPARATION_EXACTLY_RESOLVED
ALL_PREREQUISITES_USER_CONFIRMED
REFERENCE_EXACTLY_RESOLVED
EXPERIMENT_TARGET_AVAILABLE
DECLARATION_READY
```

These statuses qualify declaration inputs. They do not establish that the
physical prerequisites are true, that acquisition has occurred, or that the
future experiment will conform to the plan.

An incomplete, unknown, ambiguous, stale or mismatched input fails
deterministically before any partial ready result is rendered.

## Single user action

On success, the view displays exactly one action: invoke the existing
`acousticbrain.commands.declare_evidence_plan_experiment` command with the
same exact plan, experiment and reference identifiers.

The preflight never invokes that command. Declaration remains a separate
explicit operation because it creates a directory and writes a manifest.

## Mutation and scientific boundary

The preflight is strictly read-only. It never creates the experiment target,
writes a manifest, changes a preparation registry, edits a plan, starts an
acquisition, compares measurements or establishes causality.

`ALL_PREREQUISITES_USER_CONFIRMED` remains a preserved user declaration, not
independent verification. `DECLARATION_READY` is not execution permission and
never means `EXECUTED`. Causality remains `NOT_ESTABLISHED`.

## Acceptance criteria

Tests must demonstrate exact plan and preparation resolution, rejection when
any prerequisite is not confirmed, exact fingerprint continuity, strict safe
identifiers, existing reference resolution, absent target enforcement, one
separate declaration command, source and registry immutability, no filesystem
writes, no declaration or execution, deterministic failures before partial
rendering, and `Causality status: NOT_ESTABLISHED`.
