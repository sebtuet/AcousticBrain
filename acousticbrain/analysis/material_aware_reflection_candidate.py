from statistics import fmean

from acousticbrain.models import (
    MaterialAssessment,
    MaterialAwareReflectionCandidateAnalysis,
    ReflectionCandidateAssessment,
    ReflectionCandidateCausalityStatus,
    ReflectionCandidateEligibilityImpact,
    ReflectionCandidateEvidenceLink,
    ReflectionCandidateGeometricStatus,
    ReflectionCandidateStatus,
)


class ReflectionCandidateCompatibilityEngine:
    """Ranks existing geometry/ETC candidates using descriptive material facts."""

    STRONG_CANDIDATE_SCORE = 80.0
    COMPATIBLE_MAXIMUM_MEAN_ABSORPTION = 0.35
    WEAKLY_INCOMPATIBLE_MAXIMUM_MEAN_ABSORPTION = 0.65
    MATERIAL_FACTORS = {
        MaterialAssessment.COMPATIBLE: 1.0,
        MaterialAssessment.WEAKLY_INCOMPATIBLE: 0.85,
        MaterialAssessment.INCOMPATIBLE: 0.60,
    }
    SOURCE_ANALYSES = (
        "GeometryEarlyReflectionAnalysis",
        "ETCReflectionCorrelationAnalysis",
        "SurfaceMaterialAnalysis",
    )
    RULES = (
        "MATERIAL_RANKING_EXISTING_CANDIDATES_ONLY",
        "GEOMETRY_TEMPORAL_SCORE_DOMINATES",
        "UNKNOWN_MATERIAL_IS_SCORE_NEUTRAL",
        "MATERIAL_RANKING_NO_CAUSALITY",
        "MATERIAL_RANKING_NO_ELIGIBILITY_IMPACT",
    )

    def analyze(
        self,
        geometry_analysis,
        correlation_analysis,
        material_analysis,
    ) -> MaterialAwareReflectionCandidateAnalysis:
        """Pure function of the three upstream analysis objects."""
        correlations_by_path = {}
        for correlation in correlation_analysis.correlations:
            if correlation.geometry_path_id is not None:
                correlations_by_path.setdefault(
                    correlation.geometry_path_id, []
                ).append(correlation)

        availability = {
            (item.target_kind, item.target_id): item
            for item in material_analysis.target_availability
        }
        assignments = {
            (item.target_kind, item.target_id): item
            for item in material_analysis.assignments
        }
        materials = {item.material_id: item for item in material_analysis.materials}
        drafts = []
        for path in sorted(geometry_analysis.paths, key=lambda item: item.path_id):
            correlations = sorted(
                correlations_by_path.get(path.path_id, ()),
                key=lambda item: item.code,
            )
            if not correlations:
                drafts.append(self._assessment(
                    path, None, availability, assignments, materials
                ))
                continue
            drafts.extend(
                self._assessment(
                    path, correlation, availability, assignments, materials
                )
                for correlation in correlations
            )

        accepted = sorted(
            (
                item for item in drafts
                if item["geometric_status"]
                is ReflectionCandidateGeometricStatus.ACCEPTED
            ),
            key=lambda item: (
                -item["overall_compatibility_score"],
                -item["geometric_temporal_score"],
                item["candidate_id"],
            ),
        )
        ranks = {
            item["candidate_id"]: index for index, item in enumerate(accepted, 1)
        }
        candidates = tuple(
            self._with_rank(item, ranks.get(item["candidate_id"]))
            for item in sorted(drafts, key=lambda item: item["candidate_id"])
        )
        return MaterialAwareReflectionCandidateAnalysis(
            candidates=candidates,
            source_analysis_codes=self.SOURCE_ANALYSES,
            applied_rule_codes=self.RULES,
        )

    @classmethod
    def _assessment(cls, path, correlation, availability, assignments, materials):
        target_keys = [
            (
                "REGION" if path.surface_id != path.base_surface_id else "SURFACE",
                path.surface_id,
            )
        ]
        if path.surface_id != path.base_surface_id:
            target_keys.append(("SURFACE", path.base_surface_id))
        target_key = next(
            (
                key for key in target_keys
                if availability.get(key) is not None
                and availability[key].material_id is not None
            ),
            target_keys[0],
        )
        target = availability.get(target_key)
        assignment = assignments.get(target_key)
        material = (
            materials.get(target.material_id)
            if target is not None and target.material_id is not None
            else None
        )
        assessment = cls._material_assessment(material)
        geometric_score = correlation.match_score if correlation is not None else 0.0
        overall = (
            geometric_score
            if assessment is MaterialAssessment.UNKNOWN
            else geometric_score * cls.MATERIAL_FACTORS[assessment]
        )
        accepted = correlation is not None
        candidate_id = (
            f"material_reflection_candidate.{correlation.code}"
            if correlation is not None
            else f"material_reflection_candidate.rejected.{path.path_id}"
        )
        evidence = [ReflectionCandidateEvidenceLink(
            code=f"evidence.{candidate_id}.geometry",
            source_analysis="GeometryEarlyReflectionAnalysis",
            source_id=path.path_id,
            fact_code="GEOMETRIC_TEMPORAL_COMPATIBILITY",
        )]
        if correlation is not None:
            evidence.append(ReflectionCandidateEvidenceLink(
                code=f"evidence.{candidate_id}.correlation",
                source_analysis="ETCReflectionCorrelationAnalysis",
                source_id=correlation.code,
                fact_code="GEOMETRIC_TEMPORAL_COMPATIBILITY",
            ))
        if material is not None:
            evidence.append(ReflectionCandidateEvidenceLink(
                code=f"evidence.{candidate_id}.material",
                source_analysis="SurfaceMaterialAnalysis",
                source_id=material.material_id,
                fact_code="MATERIAL_FREQUENCY_COMPATIBILITY",
            ))
        limitations = [
            "CAUSALITY_NOT_ESTABLISHED",
            "ELIGIBILITY_UNCHANGED",
            "NO_REFLECTED_LEVEL_PREDICTION",
        ]
        if material is None or assessment is MaterialAssessment.UNKNOWN:
            limitations.append("MATERIAL_PROFILE_UNAVAILABLE")
        else:
            limitations.extend((
                "MATERIAL_ASSESSMENT_IS_QUALITATIVE",
                "EVENT_FREQUENCY_RESPONSE_UNAVAILABLE",
                "INCIDENCE_AREA_DIRECTIVITY_AND_DIFFUSION_UNMODELED",
            ))
        provenance = cls._unique((
            *path.provenance_codes,
            *(correlation.provenance_codes if correlation is not None else ()),
            *(target.provenance_codes if target is not None else ()),
            *(target.description_provenance_codes if target is not None else ()),
            *(assignment.provenance_codes if assignment is not None else ()),
            *(material.provenance_codes if material is not None else ()),
        ))
        material_confidence = cls._material_confidence(material, target)
        return dict(
            candidate_id=candidate_id,
            correlation_id=correlation.code if correlation is not None else None,
            path_id=path.path_id,
            surface_id=path.base_surface_id,
            region_id=(
                path.surface_id if path.surface_id != path.base_surface_id else None
            ),
            observed_event_id=(
                f"etc_event.{correlation.channel.value.lower()}."
                f"{correlation.event.sample_index}"
                if correlation is not None else None
            ),
            geometric_temporal_score=geometric_score,
            geometric_confidence=path.confidence,
            geometric_status=(
                ReflectionCandidateGeometricStatus.ACCEPTED
                if accepted else ReflectionCandidateGeometricStatus.REJECTED
            ),
            material_assessment=assessment,
            material_confidence=material_confidence,
            material_id=material.material_id if material is not None else None,
            assignment_id=assignment.assignment_id if assignment is not None else None,
            catalog_entry_id=(
                material.catalog_entry_id if material is not None else None
            ),
            overall_compatibility_score=round(overall, 10),
            causality_status=ReflectionCandidateCausalityStatus.NOT_ESTABLISHED,
            eligibility_impact=ReflectionCandidateEligibilityImpact.NONE,
            evidence_links=tuple(evidence),
            limitations=tuple(limitations),
            provenance_codes=provenance,
            rules_applied=cls.RULES,
        )

    @classmethod
    def _with_rank(cls, item, rank):
        values = dict(item)
        values["informative_rank"] = rank
        values["status"] = (
            ReflectionCandidateStatus.REJECTED
            if rank is None
            else (
                ReflectionCandidateStatus.STRONG_CANDIDATE
                if item["overall_compatibility_score"]
                >= cls.STRONG_CANDIDATE_SCORE
                else ReflectionCandidateStatus.CANDIDATE
            )
        )
        return ReflectionCandidateAssessment(**values)

    @classmethod
    def _material_assessment(cls, material):
        if material is None or not material.absorption_coefficients:
            return MaterialAssessment.UNKNOWN
        mean_absorption = fmean(
            item.coefficient for item in material.absorption_coefficients
        )
        if mean_absorption <= cls.COMPATIBLE_MAXIMUM_MEAN_ABSORPTION:
            return MaterialAssessment.COMPATIBLE
        if mean_absorption <= cls.WEAKLY_INCOMPATIBLE_MAXIMUM_MEAN_ABSORPTION:
            return MaterialAssessment.WEAKLY_INCOMPATIBLE
        return MaterialAssessment.INCOMPATIBLE

    @staticmethod
    def _material_confidence(material, target):
        if material is None:
            return None
        values = [material.confidence]
        if target is not None and target.description_confidence is not None:
            values.append(target.description_confidence)
        return min(values)

    @staticmethod
    def _unique(values):
        return tuple(dict.fromkeys(values))
