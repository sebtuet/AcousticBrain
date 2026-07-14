# Material-aware reflection candidate ranking contract

PR-035 enrichit l’explicabilité des candidats de réflexion sans augmenter les
capacités de raisonnement acoustique d’AcousticBrain.

## Pure dependency contract

`MaterialAwareReflectionCandidateAnalysis` is exactly the deterministic
function:

```text
f(
    GeometryEarlyReflectionAnalysis,
    ETCReflectionCorrelationAnalysis,
    SurfaceMaterialAnalysis,
)
```

It accepts no fourth input and accesses no hidden service. In particular, it
does not access `RoomDescription`, `PropagationGeometry`, a material catalog,
measurements, impulse responses, ETC detectors, path generators, temporal
correlation engines, reasoning engines, planners, protocols or causal
decisions. It does not mutate any of its three inputs.

No upstream analysis depends on this analysis. The new stage is a leaf of the
analysis graph; only report presentation and traceability consume its output.

## Existing candidates only

Geometry remains the sole source of reflection paths. ETC correlation remains
the sole source of geometric-temporal compatibility. PR-035 creates neither a
path nor an ETC event and performs no temporal matching.

Every output references an existing `path_id`. An accepted output also
references an existing `correlation_id` and the observed channel/sample key.
An uncorrelated geometric path is published as `REJECTED`, receives no rank and
cannot be rehabilitated by material information.

For a path whose impact lies in a named region, the material assignment for the
exact region takes precedence. If the region has no material, an explicitly
declared assignment on its `base_surface_id` may be used. Both identifiers are
already part of `GeometryEarlyReflectionAnalysis`; no geometry is reopened.

## Timing snapshot policy

The core PR-035 model does not duplicate `theoretical_delay_ms`,
`measured_delay_ms` or `timing_error_ms`. These values already belong to the
immutable correlation referenced by `correlation_id` and `geometry_path_id`.
The report presenter resolves them through that structured link. This avoids a
second timing snapshot that could diverge from its source analysis.

## Secondary material assessment

Material assessment is deliberately qualitative and bounded:

- `UNKNOWN`: no usable absorption profile;
- `COMPATIBLE`: mean declared absorption no greater than `0.35`;
- `WEAKLY_INCOMPATIBLE`: mean declared absorption greater than `0.35` and no
  greater than `0.65`;
- `INCOMPATIBLE`: mean declared absorption greater than `0.65`.

The assessment describes whether the declared frequency profile is broadly
plausible for an already-observed reflection candidate. It is not a reflected
level prediction. Incidence angle, effective area, source directivity,
diffusion, propagation losses and the event frequency response are not jointly
modelled here and remain explicit limitations.

The fixed informative factors are `1.00`, `0.85` and `0.60` for `COMPATIBLE`,
`WEAKLY_INCOMPATIBLE` and `INCOMPATIBLE`. `UNKNOWN` is exactly neutral.

For every candidate:

```text
0 <= overall_compatibility_score <= geometric_temporal_score
```

And specifically:

```text
if material_assessment == UNKNOWN:
    overall_compatibility_score == geometric_temporal_score
else:
    0 <= overall_compatibility_score <= geometric_temporal_score
```

An overall score of at least `80` may receive the descriptive label
`STRONG_CANDIDATE`; lower accepted scores receive `CANDIDATE`. These labels and
the stable rank are informative only. Ties are resolved by overall score,
geometric-temporal score and then stable candidate identifier.

## No inference or decision

Every result has:

```text
causality_status = NOT_ESTABLISHED
eligibility_impact = NONE
```

PR-035 does not explain a reflection, validate a surface, confirm causality,
create or modify a hypothesis, unblock a protocol, change a recommendation or
alter experiment eligibility. `GeometryEarlyReflectionAnalysis`,
`ETCReflectionCorrelationAnalysis`, `SurfaceMaterialAnalysis`, acoustic
reasoning, experiment planning, recommendations and
`protocol.temporary_mask_surface.v1` retain their existing semantics and
thresholds.

## Traceability

Each assessment preserves the exact path, correlation, surface or region,
material, assignment and immutable catalog entry identifiers that exist in the
three sources. Evidence links distinguish:

- `GEOMETRIC_TEMPORAL_COMPATIBILITY`;
- `MATERIAL_FREQUENCY_COMPATIBILITY`.

The report shows the geometric status, material assessment, informative rank,
causality status and eligibility impact separately. Missing material data stays
visible as `UNKNOWN`; it is never inferred from names, catalogs or geometry.
