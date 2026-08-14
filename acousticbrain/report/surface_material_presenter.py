from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedSurfaceMaterialCoefficient:
    center_frequency_hz: float
    coefficient: float


@dataclass(frozen=True)
class PresentedSurfaceMaterial:
    material_id: str
    display_name: str
    absorption_coefficients: tuple[PresentedSurfaceMaterialCoefficient, ...]
    diffusion_coefficients: tuple[PresentedSurfaceMaterialCoefficient, ...]
    transmission_coefficients: tuple[PresentedSurfaceMaterialCoefficient, ...] | None
    source: str
    confidence: float
    quality: str
    precision: str
    provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedSurfaceMaterialTarget:
    target_kind: str
    target_id: str
    material_id: str | None
    description_source: str | None
    description_confidence: float | None
    provenance_codes: tuple[str, ...]
    description_provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedSurfaceMaterialAnalysis:
    materials: tuple[PresentedSurfaceMaterial, ...]
    targets: tuple[PresentedSurfaceMaterialTarget, ...]
    completeness: float
    available_fact_codes: tuple[str, ...]
    missing_fact_codes: tuple[str, ...]
    missing_material_target_codes: tuple[str, ...]


class SurfaceMaterialPresenter:
    def present(self, context):
        analysis = context.surface_material_analysis
        if analysis is None or not analysis.materials:
            return None
        return PresentedSurfaceMaterialAnalysis(
            materials=tuple(self._material(item) for item in analysis.materials),
            targets=tuple(
                PresentedSurfaceMaterialTarget(
                    item.target_kind,
                    item.target_id,
                    item.material_id,
                    item.description_source,
                    item.description_confidence,
                    item.provenance_codes,
                    item.description_provenance_codes,
                )
                for item in analysis.target_availability
            ),
            completeness=analysis.completeness,
            available_fact_codes=analysis.available_fact_codes,
            missing_fact_codes=analysis.missing_fact_codes,
            missing_material_target_codes=analysis.missing_material_target_codes,
        )

    @classmethod
    def _material(cls, item):
        return PresentedSurfaceMaterial(
            material_id=item.material_id,
            display_name=item.display_name,
            absorption_coefficients=cls._coefficients(item.absorption_coefficients),
            diffusion_coefficients=cls._coefficients(item.diffusion_coefficients),
            transmission_coefficients=(
                cls._coefficients(item.transmission_coefficients)
                if item.transmission_coefficients is not None else None
            ),
            source=item.source.value,
            confidence=item.confidence,
            quality=item.quality.value,
            precision=item.precision.value,
            provenance_codes=item.provenance_codes,
        )

    @staticmethod
    def _coefficients(values):
        return tuple(
            PresentedSurfaceMaterialCoefficient(
                item.center_frequency_hz, item.coefficient
            )
            for item in values
        )
