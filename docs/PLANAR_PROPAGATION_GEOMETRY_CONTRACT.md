# Planar propagation geometry contract

## Scientific boundary

`RoomGeometry` remains the rectangular analytical model used for volume,
Schroeder frequency and rectangular room modes. `PropagationGeometry` is a
separate scene model used only for propagation paths. Neither model silently
replaces, merges with or validates the conclusions of the other.

The first implementation accepts finite convex planar polygons, coplanar
regions and first-order specular reflections. Concave polygons, curved
surfaces, diffraction, transmission, meshes and higher-order reflections are
outside this contract.

## Knowledge invariants

- A layer consumes lower-layer facts and produces new knowledge only.
- Geometry compatibility is never causal evidence.
- Missing surfaces and regions remain missing and are never inferred.
- Every derived scene, path and compatibility fact preserves uncertainty,
  confidence and provenance.
- Existing PR-030 and PR-031 thresholds, protocols and causal limitations are
  unchanged.

## Declared geometry

Room-description schema version 3 adds optional `planar_surfaces` and
`planar_regions`. A surface has a stable identifier, a semantic room role and
an ordered convex polygon in global room coordinates. A region has a stable
identifier, a parent surface, a role and a coplanar convex polygon.

Schema versions 1 and 2 remain readable. Their absent planar collections are
reconstructed as empty tuples without inventing detailed geometry.

## Propagation engines

`PropagationGeometryEngine` defines the construction boundary. Two explicit
implementations are available:

- `RectangularPropagationEngine`, which adapts the six PR-030 rectangular
  surfaces without changing their geometry;
- `PlanarPropagationEngine`, which derives planes, deterministic local bases,
  normals, areas and placed regions from schema-v3 declarations.

`PropagationGeometryStage` selects an engine from declared facts. It never
merges the two results and never falls back after a declared planar scene has
failed validation.

## Stable scene identity

Each scene exposes `scene_id`, `scene_version` and `scene_source`. `scene_id`
is the SHA-256 digest of a canonical serialization of all propagation-relevant
facts. Collection order and JSON formatting do not affect the identifier;
coordinates, roles, placements and source-point facts do.

The identifier supports traceability, comparison and caching. Equal identifiers
mean equal canonical inputs, not equal acoustic observations or causal effects.

## Downstream compatibility

The planar reflection engine produces `GeometryEarlyReflectionAnalysis`, the
same output layer as PR-030. Additive path geometry may expose the surface
normal, speaker-to-surface direction and orthogonal boundary distance required
by generalized SBIR prediction. Existing rectangular fields and values remain
unchanged.

PR-031 continues to consume first-order paths. It does not derive planes or
impact points again. `protocol.temporary_mask_surface.v1` and
`protocol.temporary_move_speaker.v1` remain the only discriminating protocols
for the affected hypotheses.
