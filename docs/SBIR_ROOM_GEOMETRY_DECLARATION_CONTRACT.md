# SBIR room-geometry declaration contract

```text
contract_id = acousticbrain.sbir_room_geometry_declaration.v1
version = 1
status = FROZEN
input_authority = ROOM_DESCRIPTION_JSON_V5
target_authority = EXACT_BASELINE_MANIFEST_ONLY
scientific_authority = USER_DECLARATION_WITH_EXPLICIT_QUALITY
implementation_status = INPUT_IMPLEMENTED
```

## Purpose

Define the only admissible path for adding the room geometry currently missing
from the real campaign before SBIR protocol-instance construction:

```text
canonical RoomDescription v5
        ↓
strict validation and exact baseline resolution
        ↓
read-only geometry preview
        ↓
explicit baseline declaration
        ↓
existing RoomGeometry and propagation engines
        ↓
SBIR geometry candidates
```

This contract reuses `RoomDescription`, `RoomDescriptionJsonCodec`,
`RoomDescriptionValidator` and `RoomGeometryBuilder`. It does not introduce a
second room model or accept free-form geometry.

## Canonical declaration input

Exactly these envelope fields are accepted:

```json
{
  "schema_version": 1,
  "declaration_input_id": "sbir-room-geometry-001",
  "target_experiment_id": "baseline",
  "declaration_source": "USER_MEASUREMENT",
  "room_description_document": {
    "schema_version": 5,
    "room_description": {}
  },
  "user_note": null
}
```

`room_description_document` is the complete canonical output of
`RoomDescriptionJsonCodec`, not a partial geometry object. Missing, unknown or
duplicate envelope fields are rejected. `user_note` is nullable but its field
is required. The closed values are `schema_version = 1`,
`target_experiment_id = baseline` and
`declaration_source = USER_MEASUREMENT`.

## Coordinate system

The existing `RoomDescription` coordinate system is unchanged:

- origin: front-left corner on the floor;
- `x`: front wall toward rear wall;
- `y`: left wall toward right wall;
- `z`: floor toward ceiling;
- unit: metres.

Coordinates are copied exactly. They are never converted from prose, guessed
from photographs or inferred from acoustic measurements.

## Minimum SBIR declaration

The canonical v5 document must contain:

1. positive finite room length, width and height;
2. exactly one `LEFT` speaker position;
3. exactly one `RIGHT` speaker position;
4. exactly one `LISTENING_POSITION` position;
5. one geometry-quality declaration for each of:
   - `LEFT`;
   - `RIGHT`;
   - `LISTENING_POSITION`;
   - `front_wall`;
   - `rear_wall`;
   - `left_wall`;
   - `right_wall`;
   - `floor`;
   - `ceiling`.

Every quality declaration preserves an explicit non-negative `precision_m`, a
bounded `confidence`, and at least one provenance code. Speaker orientations,
openings, materials, planar surfaces and other room features remain optional;
an absent optional fact stays absent.

Additional speakers or listening positions make the V1 SBIR target ambiguous
and are rejected. V1 never chooses one automatically.

## Exact target and provenance

The declaration targets exactly one discovered experiment whose identity and
type are:

```text
experiment_id = baseline
experiment_type = BASELINE
```

The future recorded declaration must preserve:

- the complete canonical RoomDescription payload;
- its SHA-256 fingerprint;
- the exact target experiment id;
- the declaration input id;
- the declaration source;
- an optional exact user note;
- every validation decision.

The payload is stored under a new versioned manifest field named
`room_description_contract`. Existing legacy inline geometry fields are not
rewritten or removed.

## Validation order

A future preview and declaration service must stop at the first failed stage:

1. `ROOM_DESCRIPTION_SCHEMA_VALID`;
2. `BASELINE_EXACTLY_RESOLVED`;
3. `SBIR_GEOMETRY_ENTITY_SET_EXACT`;
4. `ROOM_GEOMETRY_RELATIONALLY_VALID`;
5. `GEOMETRY_QUALITY_SET_EXACT`;
6. `LEGACY_GEOMETRY_NON_CONFLICTING`;
7. `SBIR_GEOMETRY_DECLARATION_READY`.

No later decision is produced after a failed or unavailable earlier stage.

## Legacy geometry boundary

If the baseline manifest contains legacy inline geometry, the canonical
dimensions, speaker coordinates and listening-position coordinates must match
exactly. Missing legacy geometry is acceptable. Divergent legacy geometry is
rejected with the incompatible field paths; it is never overwritten, merged or
silently preferred.

## Recording and idempotence

Preview is read-only and never creates a manifest. Explicit declaration may
write only `baseline/manifest.json` and must use atomic replacement.

- identical declaration input and payload: byte-idempotent;
- same declaration input id with divergent content: deterministic refusal;
- existing identical canonical manifest contract: no rewrite;
- existing divergent canonical manifest contract: deterministic refusal.

No geometry is copied into another experiment automatically. Existing explicit
reference and controlled-variable rules remain the only inheritance authority.

## Scientific boundary

A valid geometry declaration establishes only declared spatial facts and their
declared quality. It does not establish:

- that the coordinates were measured correctly;
- an SBIR cause;
- a preferred speaker position;
- a displacement direction or distance;
- that an experiment was performed;
- any permanent correction.

Candidate generation, correlation with measured dips, displacement proposal,
protocol-instance compatibility, experiment declaration, execution and result
evaluation remain separate downstream stages.

## Explicitly outside V1

- extracting dimensions or positions from free text, images or audio;
- selecting among multiple speakers or listening positions;
- estimating missing precision or confidence;
- modifying measurement files;
- changing non-baseline manifests;
- selecting an SBIR candidate or displacement;
- declaring or executing an experiment;
- causal or prescriptive conclusions.

## Future acceptance criteria

Implementation must prove with automated tests:

1. strict canonical v5 parsing without repository access;
2. exact minimum entity and quality sets;
3. exact baseline identity and type resolution;
4. relational room validation before preview readiness;
5. deterministic legacy-geometry conflict paths;
6. preview performs no write;
7. atomic explicit declaration to the baseline manifest only;
8. byte-idempotent identical replay;
9. divergent declaration and manifest contracts are rejected before writing;
10. historical manifests without either geometry format remain readable;
11. the existing geometry pipeline consumes the canonical contract;
12. no candidate selection, experiment declaration or causal promotion.
