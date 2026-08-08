# Guided global status declaration-readiness extension

```text
contract_id = acousticbrain.guided_global_status.declaration_readiness.v1
version = 1
status = FROZEN
authority = EXISTING_DECLARATION_PREFLIGHT_PROJECTION_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Project the existing `CHANNEL_ISOLATION` declaration preflight inside the
read-only guided global status after an exact preparation has been explicitly
selected and all its prerequisites carry the user-declared status
`CONFIRMED`.

```text
exact confirmed preparation
+ explicit existing reference experiment_id
+ explicit absent target experiment_id
→ existing declaration-readiness service
→ READY_PLAN_DECLARATION_READY
→ separate declaration command
```

## Inputs and resolution

The reference and target identifiers are required together. They are valid
only with `--guided-status`, an explicit preparation registry and an exact
preparation identifier. Neither identifier is discovered, generated,
normalized or selected by the view.

The existing preflight remains the sole authority for exact plan and
preparation resolution, fingerprint continuity, user-confirmed prerequisites,
reference-directory existence and target-path availability. Any failure occurs
before rendering a partial ready state.

## Closed additional state

Successful qualification adds only:

```text
READY_PLAN_DECLARATION_READY
```

The view preserves every closed preflight status and renders exactly one user
action: the existing separate experiment-declaration command with the same
measurement root, plan, reference, target and qualified preparation identifiers.
The command uses the qualified declaration extension documented in
`CHANNEL_ISOLATION_QUALIFIED_DECLARATION_CONTRACT.md`.

## CLI

```text
python main.py --measurements-root PATH --guided-status \
  --guided-preparation-registry REGISTRY_PATH \
  --guided-preparation CONFIRMATION_ID \
  --channel-isolation-reference REFERENCE_EXPERIMENT_ID \
  --channel-isolation-experiment NEW_EXPERIMENT_ID
```

The command is read-only. It never creates the target directory, writes a
manifest, changes the registry, executes a measurement or establishes
causality. `DECLARATION_READY` never means `EXECUTED`.
