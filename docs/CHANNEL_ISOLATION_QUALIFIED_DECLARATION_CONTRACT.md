# Qualified CHANNEL_ISOLATION declaration contract

```text
contract_id = acousticbrain.channel_isolation_qualified_declaration.v1
version = 1
status = FROZEN
authority = EXISTING_DECLARATION_ENGINE_WITH_QUALIFIED_EXTENSION
scientific_authority = NONE
implementation_status = IMPLEMENTED
```

## Purpose

Preserve the exact preparation provenance and declared structural acquisition
contract when the existing evidence-plan declaration command is invoked from a
successful `CHANNEL_ISOLATION` preflight.

```text
exact READY CHANNEL_ISOLATION plan
+ exact ALL_PREREQUISITES_USER_CONFIRMED preparation
+ existing reference id
+ absent target id
→ existing declaration-readiness service
→ existing evidence-plan contract declaration service
→ plan contract + channel declaration + preparation provenance
```

This is an optional qualified extension of the existing declaration engine,
not a second engine. Historical generic declarations remain compatible.

## Exact inputs

`--preparation-registry` and `--preparation` are required together. When they
are supplied, the resolved plan must be `CHANNEL_ISOLATION`. The existing
preflight validates plan identity, preparation identity and fingerprint,
user-confirmed prerequisite statuses, reference existence and target absence
before the target directory is created.

## Manifest projection

The existing complete plan contract and experiment declaration remain
authoritative. The qualified path additionally writes:

- `channel_isolation_declaration`, copied deterministically from the plan's
  required inputs, controlled variables, independent variables and measurements,
  with the declared LEFT and RIGHT repetitions required by the existing
  specialized coverage contract;
- `channel_isolation_preparation`, preserving schema version, confirmation id,
  plan id, exact plan fingerprint and
  `ALL_PREREQUISITES_USER_CONFIRMED` qualification.

An existing divergent block is rejected with deterministic incompatible field
paths. Existing unrelated manifest keys and measurement files are preserved.

## Scientific boundary

The declaration records intent and provenance. It does not claim that LEFT or
RIGHT files exist, that repetitions were executed, that controlled variables
remained constant, or that measurements are valid. Coverage, result evaluation
and causality remain separate decisions. No acquisition is executed.

## CLI

```text
python main.py --measurements-root PATH \
  --declare-evidence-plan-experiment NEW_EXPERIMENT_ID \
  --evidence-plan-id PLAN_ID \
  --evidence-plan-reference REFERENCE_EXPERIMENT_ID \
  --evidence-plan-declaration-preparation-registry PREPARATION_REGISTRY_PATH \
  --evidence-plan-declaration-preparation CONFIRMATION_ID
```
