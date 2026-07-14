from acousticbrain.models import (
    SurfaceMaterialAnalysis,
    SurfaceMaterialTargetAvailability,
)


class SurfaceMaterialAnalyzer:
    """Projette uniquement les faits descriptifs déjà déclarés."""

    def analyze(self, room_description, propagation_geometry):
        materials = tuple(sorted(
            room_description.materials if room_description is not None else (),
            key=lambda item: item.material_id,
        ))
        assignments = tuple(sorted(
            room_description.material_assignments if room_description is not None else (),
            key=lambda item: item.assignment_id,
        ))
        material_by_id = {item.material_id: item for item in materials}
        assignment_by_target = {
            (item.target_kind, item.target_id): item for item in assignments
        }
        targets = []
        if propagation_geometry is not None:
            targets.extend(("SURFACE", item.surface_id) for item in propagation_geometry.surfaces)
            targets.extend(("REGION", item.region_id) for item in propagation_geometry.regions)
        targets = tuple(sorted(targets))
        availability = []
        missing_targets = []
        facts = []
        missing_facts = []
        for kind, target_id in targets:
            assignment = assignment_by_target.get((kind, target_id))
            material = material_by_id.get(assignment.material_id) if assignment else None
            provenance = material.provenance_codes if material is not None else ()
            availability.append(SurfaceMaterialTargetAvailability(
                target_kind=kind,
                target_id=target_id,
                material_id=material.material_id if material is not None else None,
                provenance_codes=provenance,
                description_provenance_codes=(
                    assignment.provenance_codes if assignment is not None else ()
                ),
                description_source=(
                    assignment.description_source.value if assignment is not None else None
                ),
                description_confidence=(
                    assignment.description_confidence if assignment is not None else None
                ),
            ))
            if material is None:
                missing_targets.append(f"MATERIAL_MISSING.{kind}.{target_id}")
            else:
                facts.extend((
                    f"surface_material_assignment.{kind}.{target_id}.description_source",
                    f"surface_material_assignment.{kind}.{target_id}.description_confidence",
                    f"surface_material_assignment.{kind}.{target_id}.provenance",
                ))
        for material in materials:
            prefix = f"surface_material.{material.material_id}"
            facts.extend((
                f"{prefix}.source", f"{prefix}.confidence",
                f"{prefix}.quality", f"{prefix}.precision",
                f"{prefix}.provenance",
            ))
            for property_name, coefficients in (
                ("absorption", material.absorption_coefficients),
                ("diffusion", material.diffusion_coefficients),
                ("transmission", material.transmission_coefficients),
            ):
                if coefficients:
                    facts.extend(
                        f"{prefix}.{property_name}.{item.center_frequency_hz:g}_hz"
                        for item in coefficients
                    )
                else:
                    missing_facts.append(f"{prefix}.{property_name}")
        if propagation_geometry is None:
            missing_facts.append("propagation_geometry")
        assigned_count = sum(item.material_id is not None for item in availability)
        completeness = 100.0 * assigned_count / len(targets) if targets else 0.0
        return SurfaceMaterialAnalysis(
            materials=materials,
            assignments=assignments,
            target_availability=tuple(availability),
            available_material_ids=tuple(item.material_id for item in materials),
            missing_material_target_codes=tuple(missing_targets),
            completeness=completeness,
            available_fact_codes=tuple(facts),
            missing_fact_codes=tuple(missing_facts),
            source_analysis_codes=("RoomDescription", "PropagationGeometryAnalysis"),
            applied_rule_codes=(
                "SURFACE_MATERIALS_DESCRIPTIVE_ONLY",
                "SURFACE_MATERIALS_NO_INFERENCE",
                "SURFACE_MATERIALS_NO_PHYSICAL_RECALCULATION",
            ),
        )
