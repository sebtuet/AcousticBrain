# Guided global status operational-documentation extension

```text
contract_id = acousticbrain.guided_global_status.operational_documentation.v1
version = 1
status = FROZEN
authority = EXPLICIT_OPERATIONAL_DOCUMENTATION_PROJECTION_ONLY
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Extend the frozen guided global status with the state of two explicitly supplied
`CHANNEL_ISOLATION` operational worksheets. This extension does not alter the
original workflow states when no worksheets are supplied.

## Exact inputs

Both worksheet paths are required together. They are accepted only with an
explicit preparation registry and an exact `confirmation_id`. No file,
preparation or plan is discovered, selected by recency, or inferred.

The existing operational-record preview validates worksheet structure, plan
identity and plan fingerprint. Invalid or stale inputs fail before rendering.

## Additional navigation states

When the exact preparation remains incomplete:

```text
READY_PLAN_OPERATIONAL_DOCUMENTATION_INCOMPLETE
READY_PLAN_OPERATIONAL_DOCUMENTATION_COMPLETE_PREPARATION_INCOMPLETE
```

The first state lists every placeholder field and routes to the existing
worksheet-revision command. The second records only that the documents are
structurally complete and routes to the exact preparation view.

Document completeness never changes `UNKNOWN` or `NOT_CONFIRMED` to
`CONFIRMED`. It never verifies a physical condition. If preparation is already
fully confirmed, the existing declaration-readiness route remains authoritative.

## CLI

```text
python main.py --measurements-root PATH --guided-status \
  --guided-preparation-registry REGISTRY_PATH \
  --guided-preparation CONFIRMATION_ID \
  --microphone-position-record MICROPHONE_JSON \
  --acquisition-settings-record SETTINGS_JSON
```

The command is read-only. It does not modify worksheets, registries, plans,
manifests, measurements or experiments, and causality remains
`NOT_ESTABLISHED`.
