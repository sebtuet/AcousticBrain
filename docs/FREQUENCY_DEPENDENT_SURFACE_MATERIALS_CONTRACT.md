# Frequency-dependent surface materials contract

## Scientific objective

PR-033 introduces an immutable, deterministic description of frequency-dependent physical surface properties. It records declared absorption, diffusion and optional transmission coefficients by frequency band, together with source, confidence, quality, precision and provenance.

These values are descriptive inputs. Their presence is not evidence of an acoustic cause.

## Scope

- `SurfaceMaterialDescription` stores a stable material identity and ordered coefficient series.
- `SurfaceMaterialAssignment` associates one material with exactly one propagation surface or planar region.
- `PropagationGeometry` carries assignment references only.
- `SurfaceMaterialAnalysis` reports declared materials, target availability, provenance, completeness, available facts and missing facts.
- `SurfaceMaterialStage` runs immediately after `PropagationGeometryStage`.
- JSON schema v4 persists material catalogs and assignments additively.
- The report exposes a factual `Surface materials` section only when frequency-dependent materials are declared.

## Exclusions

PR-033 does not:

- modify room modes, Schroeder frequency or rectangular room physics;
- modify early-reflection path calculations;
- attenuate, filter or otherwise alter propagation paths;
- modify SBIR predictions or correlations;
- create recommendations, hypotheses or causal evidence;
- change experiment protocols or eligibility thresholds;
- infer missing coefficients;
- model multiple reflections, diffraction or non-planar propagation.

## Deterministic rules

- Coefficients are finite values in `[0, 1]` and bands are unique and sorted.
- Material confidence is finite and bounded to `[0, 100]`.
- Assignments reference a declared material and one known surface or region.
- At most one assignment is accepted for a given target.
- Collection ordering is canonicalized by stable identifiers during persistence and analysis.
- Missing properties remain explicitly missing; migration never manufactures values.

## Relationship with PR-030

Geometry-driven early reflections continue to consume geometric paths only. Material coefficients do not change delays, impact points, compatibility or causal status.

## Relationship with PR-031

Geometry-driven SBIR remains unchanged. Material coefficients do not modify path distances, predicted cancellation frequencies, correlations, confidence thresholds or `protocol.temporary_move_speaker.v1`.

## Relationship with PR-032

`RoomGeometry` remains the rectangular analytical model. `PropagationGeometry` remains the propagation scene and gains only immutable material references. `PlanarSurfaceDescription` and `PlanarRegionDescription` are unchanged. The scene engines perform no acoustic material calculation.

## Legacy compatibility

- JSON schemas v1, v2 and v3 remain readable.
- Their absence of frequency-dependent material data migrates to empty `materials` and `material_assignments` collections.
- The historical whole-surface material declaration remains supported as an explicit legacy mode and continues to feed `RoomGeometry` only.
- `LEGACY_ROOM` produces no invented material profile and no `Surface materials` report section.
- The legacy golden report remains byte-for-byte unchanged.

## Provenance and auditability

Each material retains its declared source, confidence, quality, precision and provenance codes. Analysis facts are derived only by projection from `RoomDescription` and `PropagationGeometryAnalysis`; applied rules explicitly state that no inference or lower-layer recalculation occurred.
