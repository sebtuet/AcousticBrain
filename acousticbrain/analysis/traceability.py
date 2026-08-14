from __future__ import annotations

from typing import TYPE_CHECKING

from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayCorrelationAnalysis,
    BinauralSpatialInterpretation,
    ClarityAnalysis,
    ClarityCorrelationAnalysis,
    DirectReverberantAnalysis,
    DirectReverberantCorrelationAnalysis,
    ETCAnalysis,
    ETCReflectionCorrelationAnalysis,
    EvidenceLevel,
    EvidenceReference,
    ExplanationLink,
    RT60Analysis,
    SpatialAnalysis,
    SpatialCorrelationAnalysis,
    SpeakerPairSpatialInterpretation,
    TraceabilityAnalysis,
    MeasurementQualityAnalysis,
    MeasurementReadinessAnalysis,
    RoomGeometry,
    RoomGeometryComparison,
    PropagationGeometry,
    AcousticReasoningAnalysis,
    ExperimentPlanningAnalysis,
)
from acousticbrain.knowledge_codes import FactCode, SourceAnalysisCode

if TYPE_CHECKING:
    from acousticbrain.models import (
        ConfidenceAnalysis,
        GlobalAnalysis,
        RecommendationAnalysis,
    )


class TraceabilityEngine:
    """Construit un graphe explicable à partir de connaissances structurées."""

    CLARITY_THRESHOLDS = (
        ("left_right_c50_differences_db", 2.0),
        ("left_right_c80_differences_db", 2.0),
        ("left_right_d50_differences_percent", 15.0),
        ("left_right_ts_differences_s", 0.02),
    )

    def analyze(
        self,
        *,
        global_analysis: GlobalAnalysis,
        recommendation_analysis: RecommendationAnalysis,
        rt60: RT60Analysis | None = None,
        etc: ETCAnalysis | None = None,
        clarity: ClarityAnalysis | None = None,
        spatial: SpatialAnalysis | None = None,
        spatial_interpretation: (
            SpeakerPairSpatialInterpretation
            | BinauralSpatialInterpretation
            | None
        ) = None,
        clarity_correlations: ClarityCorrelationAnalysis | None = None,
        spatial_correlations: SpatialCorrelationAnalysis | None = None,
        etc_reflection_correlations: (
            ETCReflectionCorrelationAnalysis | None
        ) = None,
        direct_reverberant: DirectReverberantAnalysis | None = None,
        direct_reverberant_correlations: (
            DirectReverberantCorrelationAnalysis | None
        ) = None,
        bass_decay: BassDecayAnalysis | None = None,
        bass_decay_correlations: BassDecayCorrelationAnalysis | None = None,
        confidence: ConfidenceAnalysis | None = None,
        measurement_quality: MeasurementQualityAnalysis | None = None,
        measurement_readiness: MeasurementReadinessAnalysis | None = None,
        room_geometry: RoomGeometry | None = None,
        room_geometry_comparison: RoomGeometryComparison | None = None,
        propagation_geometry: PropagationGeometry | None = None,
        acoustic_reasoning: AcousticReasoningAnalysis | None = None,
        experiment_planning: ExperimentPlanningAnalysis | None = None,
        material_aware_reflection_candidates=None,
        controlled_reflection_verification_planning=None,
        controlled_reflection_experiment_declarations=(),
        controlled_reflection_experiment_comparisons=(),
        controlled_reflection_hypothesis_status_updates=(),
    ) -> TraceabilityAnalysis:
        domain_evidence = {
            domain.source_analysis: EvidenceReference(
                code=self._evidence_code(domain.code),
                source_analysis=SourceAnalysisCode.GLOBAL,
                fact_code=self._fact_code(domain.code),
                evidence_level=EvidenceLevel.CALCULATED,
                value=domain.score,
            )
            for domain in global_analysis.domains
        }
        evidence_references = list(domain_evidence.values())
        physical_evidence = self._physical_evidence(
            rt60=rt60,
            etc=etc,
            clarity=clarity,
            spatial=spatial,
            spatial_interpretation=spatial_interpretation,
            clarity_correlations=clarity_correlations,
            spatial_correlations=spatial_correlations,
            etc_reflection_correlations=etc_reflection_correlations,
            direct_reverberant=direct_reverberant,
            direct_reverberant_correlations=(
                direct_reverberant_correlations
            ),
            bass_decay=bass_decay,
            bass_decay_correlations=bass_decay_correlations,
            measurement_quality=measurement_quality,
            measurement_readiness=measurement_readiness,
            room_geometry=room_geometry,
            room_geometry_comparison=room_geometry_comparison,
            propagation_geometry=propagation_geometry,
        )
        evidence_references.extend(physical_evidence)
        for item in physical_evidence:
            # La première preuve déclarée est le fait physique principal du
            # domaine ; les liens spécialisés peuvent sélectionner un fait
            # plus précis dans _recommendation_links.
            current = domain_evidence.get(item.source_analysis)
            if (
                current is None
                or current.source_analysis == SourceAnalysisCode.GLOBAL
            ):
                domain_evidence[item.source_analysis] = item
        links = self._correlation_links(global_analysis, domain_evidence)
        links.extend(
            self._recommendation_links(
                global_analysis,
                recommendation_analysis,
                domain_evidence,
                evidence_references,
            )
        )
        if acoustic_reasoning is not None:
            reasoning_evidence, reasoning_links = self._reasoning_graph(
                acoustic_reasoning,
                recommendation_analysis,
            )
            evidence_references.extend(reasoning_evidence)
            links.extend(reasoning_links)
        if experiment_planning is not None:
            links.extend(self._planning_graph(experiment_planning))
        if material_aware_reflection_candidates is not None:
            material_evidence, material_links = self._material_candidate_graph(
                material_aware_reflection_candidates
            )
            evidence_references.extend(material_evidence)
            links.extend(material_links)
        if controlled_reflection_verification_planning is not None:
            links.extend(self._reflection_verification_planning_graph(
                controlled_reflection_verification_planning
            ))
        if controlled_reflection_experiment_declarations:
            links.extend(self._reflection_experiment_declaration_graph(
                controlled_reflection_experiment_declarations
            ))
        if controlled_reflection_experiment_comparisons:
            links.extend(self._reflection_experiment_comparison_graph(
                controlled_reflection_experiment_comparisons
            ))
        if controlled_reflection_hypothesis_status_updates:
            links.extend(self._reflection_hypothesis_status_update_graph(
                controlled_reflection_hypothesis_status_updates
            ))

        if confidence is not None:
            confidence_evidence = EvidenceReference(
                code="evidence.global.confidence",
                source_analysis="ConfidenceAnalysis",
                fact_code="global.confidence",
                evidence_level=EvidenceLevel.CALCULATED,
                value=confidence.score,
            )
            evidence_references.append(confidence_evidence)
            links.append(
                ExplanationLink(
                    code="explanation.global.confidence",
                    fact_codes=(confidence_evidence.fact_code,),
                    evidence_codes=(confidence_evidence.code,),
                )
            )

        recommendation_sources = (
            source
            for recommendation in recommendation_analysis.recommendations
            for source in recommendation.source_analyses
        )
        sources = tuple(
            dict.fromkeys(
                (
                    "GlobalAnalysis",
                    "RecommendationAnalysis",
                    *global_analysis.source_analyses,
                    *recommendation_sources,
                    *(item.source_analysis for item in physical_evidence),
                    *(("AcousticReasoningAnalysis",) if acoustic_reasoning is not None else ()),
                    *(
                        acoustic_reasoning.source_analyses
                        if acoustic_reasoning is not None
                        else ()
                    ),
                    *(
                        ("ExperimentPlanningAnalysis",)
                        if experiment_planning is not None
                        else ()
                    ),
                    *(
                        experiment_planning.plan.source_analysis_codes
                        if experiment_planning is not None
                        else ()
                    ),
                    *(("ConfidenceAnalysis",) if confidence is not None else ()),
                    *(
                        (
                            "MaterialAwareReflectionCandidateAnalysis",
                            *material_aware_reflection_candidates.source_analysis_codes,
                        )
                        if material_aware_reflection_candidates is not None
                        else ()
                    ),
                    *(
                        (
                            "ControlledReflectionVerificationPlanningAnalysis",
                            *controlled_reflection_verification_planning.source_analysis_codes,
                        )
                        if controlled_reflection_verification_planning is not None
                        else ()
                    ),
                    *(
                        ("ControlledReflectionExperimentDeclaration",)
                        if controlled_reflection_experiment_declarations
                        else ()
                    ),
                    *(
                        ("ControlledReflectionExperimentComparison",)
                        if controlled_reflection_experiment_comparisons
                        else ()
                    ),
                    *(
                        ("ControlledReflectionHypothesisStatusUpdate",)
                        if controlled_reflection_hypothesis_status_updates
                        else ()
                    ),
                )
            )
        )

        return TraceabilityAnalysis(
            evidence_references=evidence_references,
            links=links,
            source_analyses=sources,
        )

    @staticmethod
    def _material_candidate_graph(analysis):
        evidence = []
        links = []
        for candidate in analysis.candidates:
            evidence_code = f"evidence.{candidate.candidate_id}.overall_compatibility"
            fact_code = (
                f"material_aware_reflection_candidate.{candidate.candidate_id}."
                "overall_compatibility_score"
            )
            evidence.append(EvidenceReference(
                code=evidence_code,
                source_analysis="MaterialAwareReflectionCandidateAnalysis",
                fact_code=fact_code,
                evidence_level=EvidenceLevel.CALCULATED,
                value=candidate.overall_compatibility_score,
            ))
            evidence.extend(
                EvidenceReference(
                    code=item.code,
                    source_analysis=item.source_analysis,
                    fact_code=item.fact_code,
                    evidence_level=EvidenceLevel.CALCULATED,
                )
                for item in candidate.evidence_links
            )
            links.append(ExplanationLink(
                code=f"explanation.{candidate.candidate_id}",
                fact_codes=(fact_code,),
                evidence_codes=(
                    evidence_code,
                    *(item.code for item in candidate.evidence_links),
                ),
                correlation_codes=(
                    (candidate.correlation_id,)
                    if candidate.correlation_id is not None else ()
                ),
                candidate_codes=(candidate.candidate_id,),
                ranking_codes=(
                    (f"informative_rank.{candidate.informative_rank}",)
                    if candidate.informative_rank is not None else ()
                ),
            ))
        return evidence, links

    @staticmethod
    def _reflection_verification_planning_graph(analysis):
        links = []
        for proposal in analysis.proposals:
            links.append(ExplanationLink(
                code=f"explanation.{proposal.proposal_id}",
                fact_codes=(
                    "material_aware_reflection_candidate."
                    f"{proposal.source_candidate_id}.overall_compatibility_score",
                ),
                evidence_codes=proposal.source_evidence_codes,
                correlation_codes=(proposal.correlation_id,),
                candidate_codes=(proposal.source_candidate_id,),
                verification_proposal_codes=(proposal.proposal_id,),
                ranking_codes=(
                    f"informative_rank.{proposal.proposal_order}",
                ),
            ))
        for exclusion in analysis.exclusions:
            links.append(ExplanationLink(
                code=(
                    "explanation.reflection_verification_exclusion."
                    f"{exclusion.source_candidate_id}"
                ),
                fact_codes=(
                    "material_aware_reflection_candidate."
                    f"{exclusion.source_candidate_id}.geometric_status",
                ),
                evidence_codes=exclusion.source_evidence_codes,
                candidate_codes=(exclusion.source_candidate_id,),
            ))
        return links

    @staticmethod
    def _reflection_experiment_declaration_graph(declarations):
        return [
            ExplanationLink(
                code=f"explanation.{declaration.declaration_id}",
                fact_codes=(),
                evidence_codes=(),
                verification_proposal_codes=(declaration.proposal_id,),
                experiment_declaration_codes=(declaration.declaration_id,),
            )
            for declaration in sorted(
                declarations,
                key=lambda item: item.declaration_id,
            )
        ]

    @staticmethod
    def _reflection_experiment_comparison_graph(comparisons):
        return [
            ExplanationLink(
                code=f"explanation.{comparison.comparison_id}",
                fact_codes=tuple(
                    f"{comparison.comparison_id}.{item.observable_code}.difference"
                    for item in comparison.observed_differences
                ),
                evidence_codes=(),
                verification_proposal_codes=(comparison.proposal_id,),
                experiment_declaration_codes=(
                    comparison.experiment_declaration_id,
                ),
                experiment_comparison_codes=(comparison.comparison_id,),
            )
            for comparison in sorted(
                comparisons,
                key=lambda item: item.comparison_id,
            )
        ]

    @staticmethod
    def _reflection_hypothesis_status_update_graph(updates):
        return [
            ExplanationLink(
                code=f"explanation.{update.update_id}",
                fact_codes=update.measured_fact_codes,
                evidence_codes=(),
                candidate_codes=(update.target_id,),
                verification_proposal_codes=(update.proposal_id,),
                experiment_declaration_codes=(
                    update.experiment_declaration_id,
                ),
                experiment_comparison_codes=(
                    (update.comparison_id,)
                    if update.comparison_id is not None else ()
                ),
                hypothesis_status_update_codes=(update.update_id,),
            )
            for update in sorted(updates, key=lambda item: item.update_id)
        ]

    @staticmethod
    def _planning_graph(analysis):
        return [
            ExplanationLink(
                code=f"explanation.{item.trace_id}",
                fact_codes=item.fact_codes,
                evidence_codes=item.evidence_codes,
                hypothesis_codes=(item.hypothesis_code,),
                protocol_codes=(item.source_protocol_id,),
                candidate_codes=(item.candidate_id,),
                ranking_codes=(
                    (f"experiment_rank.{item.rank}",)
                    if item.rank is not None
                    else ()
                ),
                recommended_candidate_codes=(
                    (item.candidate_id,) if item.recommended else ()
                ),
                iteration_codes=(
                    (f"optimization_iteration.{item.session_iteration_number}",)
                    if item.session_iteration_number is not None
                    else ()
                ),
            )
            for item in analysis.trace_links
        ]

    @staticmethod
    def _reasoning_graph(analysis, recommendation_analysis):
        evidence_references = []
        links = []
        recommendation_codes = {
            item.code for item in recommendation_analysis.recommendations
        }
        for hypothesis in analysis.hypotheses:
            evidence = tuple(
                item
                for collection in (
                    hypothesis.supporting_evidence,
                    hypothesis.counter_evidence,
                    hypothesis.context_evidence,
                )
                for item in collection
            )
            references = tuple(
                EvidenceReference(
                    code=f"evidence.reasoning.{item.code.lower()}",
                    source_analysis=item.source_analysis,
                    fact_code=item.fact_code,
                    evidence_level=EvidenceLevel.CALCULATED,
                    value=item.value,
                )
                for item in evidence
            )
            evidence_references.extend(references)
            links.append(
                ExplanationLink(
                    code=f"explanation.hypothesis.{hypothesis.code.value.lower()}",
                    fact_codes=tuple(item.fact_code for item in evidence),
                    evidence_codes=tuple(item.code for item in references),
                    correlation_codes=tuple(
                        dict.fromkeys(
                            code
                            for item in evidence
                            for code in item.correlation_codes
                        )
                    ),
                    hypothesis_codes=(hypothesis.code.value,),
                )
            )
            by_fact = {
                item.fact_code: reference
                for item, reference in zip(evidence, references)
            }
            for action in hypothesis.verification_actions:
                action_evidence = tuple(
                    by_fact[fact]
                    for fact in action.evidence_fact_codes
                    if fact in by_fact
                )
                if len(action_evidence) != len(action.evidence_fact_codes):
                    continue
                links.append(
                    ExplanationLink(
                        code=f"explanation.action.{action.code.lower()}",
                        fact_codes=action.evidence_fact_codes,
                        evidence_codes=tuple(
                            item.code for item in action_evidence
                        ),
                        recommendation_codes=(action.code,)
                        if action.code in recommendation_codes
                        else (),
                        hypothesis_codes=(hypothesis.code.value,),
                        action_codes=(action.code,),
                    )
                )
        return evidence_references, links

    @classmethod
    def _physical_evidence(
        cls,
        *,
        rt60,
        etc,
        clarity,
        spatial,
        spatial_interpretation,
        clarity_correlations,
        spatial_correlations,
        etc_reflection_correlations,
        direct_reverberant,
        direct_reverberant_correlations,
        bass_decay,
        bass_decay_correlations,
        measurement_quality,
        measurement_readiness,
        room_geometry,
        room_geometry_comparison,
        propagation_geometry,
    ):
        evidence = []
        if rt60 is not None:
            reliable_count = sum(
                item.confidence >= 70.0
                and abs(item.difference_seconds) >= 0.2
                for item in rt60.left_right_band_differences
            )
            evidence.extend(
                [
                    cls._evidence(
                        "evidence.rt60.broadband_mean",
                        SourceAnalysisCode.RT60,
                        FactCode.RT60_BROADBAND_MEAN,
                        getattr(rt60, "broadband_rt60_seconds", None),
                    ),
                    cls._evidence(
                        "evidence.rt60.reliable_difference_count",
                        SourceAnalysisCode.RT60,
                        FactCode.RT60_RELIABLE_DIFFERENCE_COUNT,
                        reliable_count,
                    ),
                    cls._evidence(
                        "evidence.rt60.interchannel_homogeneity",
                        SourceAnalysisCode.RT60,
                        FactCode.RT60_INTERCHANNEL_HOMOGENEITY,
                        getattr(rt60, "interchannel_homogeneity", None),
                    ),
                ]
            )
        if etc is not None:
            specific_count = (
                etc.left_only_event_count + etc.right_only_event_count
            )
            evidence.append(
                cls._evidence(
                    "evidence.etc.channel_specific_event_count",
                    SourceAnalysisCode.ETC,
                    FactCode.ETC_CHANNEL_SPECIFIC_EVENT_COUNT,
                    specific_count,
                )
            )
        if clarity is not None:
            centers = {
                center
                for attribute, threshold in cls.CLARITY_THRESHOLDS
                for center, difference in getattr(clarity, attribute).items()
                if abs(difference) >= threshold
            }
            evidence.append(
                cls._evidence(
                    "evidence.clarity.channel_asymmetry_count",
                    SourceAnalysisCode.CLARITY,
                    FactCode.CLARITY_CHANNEL_ASYMMETRY_COUNT,
                    len(centers),
                )
            )
        if spatial is not None and spatial_interpretation is not None:
            stability = getattr(
                spatial_interpretation,
                "technical_center_stability",
                None,
            )
            evidence.append(
                cls._evidence(
                    "evidence.spatial.technical_center_stability",
                    SourceAnalysisCode.SPATIAL,
                    FactCode.SPATIAL_TECHNICAL_CENTER_STABILITY,
                    getattr(stability, "value", "BINAURAL"),
                )
            )
        if clarity_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.clarity.correlation_count",
                    SourceAnalysisCode.CLARITY_CORRELATION,
                    FactCode.CLARITY_CORRELATION_COUNT,
                    len(clarity_correlations.correlations),
                )
            )
        if spatial_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.spatial.correlation_count",
                    SourceAnalysisCode.SPATIAL_CORRELATION,
                    FactCode.SPATIAL_CORRELATION_COUNT,
                    len(spatial_correlations.correlations),
                )
            )
        if etc_reflection_correlations is not None:
            unmatched_count = sum(
                event.delay_ms <= 20.0 and event.relative_level_db >= -20.0
                for events in etc_reflection_correlations.unmatched_events.values()
                for event in events
            )
            evidence.append(
                cls._evidence(
                    "evidence.etc_reflection.dominant_unmatched_event_count",
                    SourceAnalysisCode.ETC_REFLECTION_CORRELATION,
                    FactCode.ETC_REFLECTION_DOMINANT_UNMATCHED_EVENT_COUNT,
                    unmatched_count,
                )
            )
        if direct_reverberant is not None:
            evidence.extend(
                [
                    cls._evidence(
                        "evidence.direct_reverberant.broadband_drr_db",
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                        FactCode.DRR_BROADBAND_DB,
                        direct_reverberant.broadband_direct_to_reverberant_db,
                    ),
                    cls._evidence(
                        "evidence.direct_reverberant.asymmetric_band_count",
                        SourceAnalysisCode.DIRECT_REVERBERANT,
                        FactCode.DRR_ASYMMETRIC_BAND_COUNT,
                        sum(
                            abs(value) >= 3.0
                            for value in direct_reverberant.left_right_direct_to_reverberant_differences_db.values()
                        ),
                    ),
                ]
            )
        if direct_reverberant_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.direct_reverberant.correlation_count",
                    SourceAnalysisCode.DIRECT_REVERBERANT_CORRELATION,
                    FactCode.DRR_CORRELATION_COUNT,
                    len(direct_reverberant_correlations.correlations),
                )
            )
        if bass_decay is not None:
            times = [
                band.estimated_decay_time_seconds
                for band in bass_decay.aggregate_bands
                if band.estimated_decay_time_seconds is not None
            ]
            significant_count = sum(
                abs(item.difference_seconds) >= 0.25
                for item in bass_decay.left_right_band_differences
            )
            evidence.extend(
                [
                    cls._evidence(
                        "evidence.bass_decay.maximum_decay_time",
                        SourceAnalysisCode.BASS_DECAY,
                        FactCode.BASS_DECAY_MAXIMUM_DECAY_TIME,
                        max(times) if times else None,
                    ),
                    cls._evidence(
                        "evidence.bass_decay.usable_band_count",
                        SourceAnalysisCode.BASS_DECAY,
                        FactCode.BASS_DECAY_USABLE_BAND_COUNT,
                        len(times),
                    ),
                    cls._evidence(
                        "evidence.bass_decay.significant_difference_count",
                        SourceAnalysisCode.BASS_DECAY,
                        FactCode.BASS_DECAY_SIGNIFICANT_DIFFERENCE_COUNT,
                        significant_count,
                    ),
                ]
            )
        if bass_decay_correlations is not None:
            evidence.append(
                cls._evidence(
                    "evidence.bass_decay.correlation_count",
                    SourceAnalysisCode.BASS_DECAY_CORRELATION,
                    FactCode.BASS_DECAY_CORRELATION_COUNT,
                    len(bass_decay_correlations.correlations),
                )
            )
            modal_matches = [
                match
                for correlation in bass_decay_correlations.correlations
                if getattr(correlation, "code", None)
                == "SLOW_DECAY_MODAL_INTERACTION"
                for match in getattr(correlation, "modal_matches", ())
            ]
            if modal_matches:
                evidence.append(
                    cls._evidence(
                        "evidence.bass_decay.modal_match.count",
                        SourceAnalysisCode.BASS_DECAY_CORRELATION,
                        FactCode.BASS_DECAY_MODAL_MATCH_COUNT,
                        len(modal_matches),
                    )
                )
                evidence.extend(cls._modal_match_evidence(modal_matches))
        if measurement_quality is not None:
            evidence.extend(cls._measurement_quality_evidence(measurement_quality))
        if measurement_readiness is not None:
            evidence.extend(cls._measurement_readiness_evidence(measurement_readiness))
        if room_geometry is not None:
            dimensions = room_geometry.dimensions
            values = (
                ("source", room_geometry.source.value),
                ("model", room_geometry.model.value),
                ("model_version", room_geometry.model_version),
                ("length_m", dimensions.length_m),
                ("width_m", dimensions.width_m),
                ("height_m", dimensions.height_m),
                ("completeness", room_geometry.completeness),
            )
            evidence.extend(
                cls._evidence(
                    f"evidence.room_geometry.{name}",
                    SourceAnalysisCode.ROOM_GEOMETRY,
                    f"room_geometry.{name}",
                    value,
                )
                for name, value in values
            )
            evidence.extend(cls._room_feature_evidence(room_geometry))
        if room_geometry_comparison is not None:
            evidence.append(
                cls._evidence(
                    "evidence.room_geometry.comparison_status",
                    SourceAnalysisCode.ROOM_GEOMETRY,
                    "room_geometry.comparison_status",
                    room_geometry_comparison.status.value,
                )
            )
            evidence.extend(
                cls._evidence(
                    f"evidence.room_geometry.difference.{field}",
                    SourceAnalysisCode.ROOM_GEOMETRY,
                    f"room_geometry.difference.{field}",
                    difference,
                )
                for field, difference in (
                    room_geometry_comparison.absolute_differences_m.items()
                )
            )
        if propagation_geometry is not None:
            source = SourceAnalysisCode.PROPAGATION_GEOMETRY
            values = (
                ("scene_id", propagation_geometry.scene_id),
                ("scene_version", propagation_geometry.scene_version),
                ("scene_source", propagation_geometry.scene_source.value),
                ("surface_count", len(propagation_geometry.surfaces)),
                ("region_count", len(propagation_geometry.regions)),
                ("completeness", propagation_geometry.completeness),
            )
            evidence.extend(
                cls._evidence(
                    f"evidence.propagation_geometry.{name}",
                    source,
                    f"propagation_geometry.{name}",
                    value,
                )
                for name, value in values
            )
            for surface in propagation_geometry.surfaces:
                prefix = f"propagation_geometry.surface.{surface.surface_id}"
                evidence.extend((
                    cls._evidence(
                        f"evidence.{prefix}.role", source, f"{prefix}.role",
                        surface.role.value,
                    ),
                    cls._evidence(
                        f"evidence.{prefix}.area_m2", source, f"{prefix}.area_m2",
                        surface.area_m2,
                    ),
                ))
            for region in propagation_geometry.regions:
                prefix = f"propagation_geometry.region.{region.region_id}"
                evidence.extend((
                    cls._evidence(
                        f"evidence.{prefix}.surface_id", source,
                        f"{prefix}.surface_id", region.surface_id,
                    ),
                    cls._evidence(
                        f"evidence.{prefix}.role", source, f"{prefix}.role",
                        region.role.value,
                    ),
                ))
        return evidence

    @classmethod
    def _room_feature_evidence(cls, geometry):
        source = SourceAnalysisCode.ROOM_GEOMETRY
        evidence = []
        completeness = geometry.feature_completeness
        if completeness is not None:
            for name, value in (
                ("orientation_coverage", completeness.orientation_coverage),
                ("material_coverage", completeness.material_coverage),
                ("covering_placement_coverage", completeness.covering_placement_coverage),
                ("furniture_placement_coverage", completeness.furniture_placement_coverage),
                ("treatment_placement_coverage", completeness.treatment_placement_coverage),
                ("score", completeness.score),
            ):
                evidence.append(
                    cls._evidence(
                        f"evidence.room_geometry.feature_completeness.{name}",
                        source,
                        f"room_geometry.feature_completeness.{name}",
                        value,
                    )
                )
        for item in geometry.speaker_orientations:
            evidence.append(
                cls._evidence(
                    f"evidence.room_geometry.speaker.{item.speaker_id}.yaw_degrees",
                    source,
                    f"room_geometry.speaker.{item.speaker_id}.yaw_degrees",
                    item.yaw_degrees,
                )
            )
        for item in geometry.surface_materials:
            prefix = f"room_geometry.surface.{item.surface_id}.material"
            evidence.append(
                cls._evidence(
                    f"evidence.{prefix}.type",
                    source,
                    f"{prefix}.type",
                    item.material_type.value,
                )
            )
        for category, items, id_attribute, placement_attribute in (
            ("covering_zone", geometry.covering_zones, "zone_id", "placement"),
            ("furniture", geometry.furniture, "furniture_id", "bounding_box"),
            ("treatment", geometry.acoustic_treatments, "treatment_id", "placement"),
        ):
            for item in items:
                identifier = getattr(item, id_attribute)
                placed = getattr(item, placement_attribute) is not None
                prefix = f"room_geometry.{category}.{identifier}"
                evidence.append(
                    cls._evidence(
                        f"evidence.{prefix}.placed",
                        source,
                        f"{prefix}.placed",
                        placed,
                    )
                )
                surface_id = getattr(item, "surface_id", None)
                if surface_id is not None:
                    evidence.append(
                        cls._evidence(
                            f"evidence.{prefix}.surface_id",
                            source,
                            f"{prefix}.surface_id",
                            surface_id,
                        )
                    )
        return evidence

    @classmethod
    def _measurement_quality_evidence(cls, analysis):
        issues = [
            issue
            for channel in analysis.channel_qualities
            for issue in channel.issues
        ]
        if analysis.measurement_set_quality is not None:
            issues.extend(analysis.measurement_set_quality.issues)
        evidence = [
            cls._evidence(
                "evidence.measurement_quality.issue_count",
                SourceAnalysisCode.MEASUREMENT_QUALITY,
                "measurement_quality.issue_count",
                len(issues),
            )
        ]
        for index, issue in enumerate(issues):
            prefix = f"measurement_quality.issue.{index}"
            values = [
                ("code", issue.code.value),
                ("scope", issue.scope.value),
                ("confidence", issue.confidence),
            ]
            if issue.channel is not None:
                values.append(("channel", issue.channel.value))
            if issue.severity is not None:
                values.append(("severity", issue.severity.value))
            values.extend(
                (f"metric.{name}", value)
                for name, value in sorted(issue.observed_metrics.items())
            )
            values.extend(
                (f"threshold.{name}", value)
                for name, value in sorted(issue.applied_thresholds.items())
            )
            evidence.extend(
                cls._evidence(
                    f"evidence.{prefix}.{name}",
                    SourceAnalysisCode.MEASUREMENT_QUALITY,
                    f"{prefix}.{name}",
                    value,
                )
                for name, value in values
            )
        return evidence

    @classmethod
    def _measurement_readiness_evidence(cls, analysis):
        evidence = []
        for item in analysis.analyses:
            prefix = f"measurement_readiness.{item.family.value.lower()}"
            values = (
                ("status", item.status.value),
                ("blocking_issue_count", len(item.blocking_issues)),
                ("non_blocking_issue_count", len(item.non_blocking_issues)),
                ("required_channels", ",".join(channel.value for channel in item.required_channels) or "NONE"),
                ("missing_facts", ",".join(item.missing_facts) or "NONE"),
                ("confidence", item.confidence),
                ("applied_rules", ",".join(item.applied_rule_codes) or "NONE"),
            )
            evidence.extend(
                cls._evidence(
                    f"evidence.{prefix}.{name}",
                    SourceAnalysisCode.MEASUREMENT_READINESS,
                    f"{prefix}.{name}",
                    value,
                )
                for name, value in values
            )
        return evidence

    @classmethod
    def _modal_match_evidence(cls, matches):
        evidence = []
        per_band_indices = {}
        for match in matches:
            band_code = cls._frequency_code(
                match.band_center_frequency_hz
            )
            index = per_band_indices.get(band_code, 0)
            per_band_indices[band_code] = index + 1
            prefix = f"bass_decay.modal_match.{band_code}.{index}"
            values = (
                ("band_center_frequency", match.band_center_frequency_hz),
                ("mode_frequency", match.mode_frequency_hz),
                ("mode_type", match.mode_type.value),
                ("order_x", match.order_x),
                ("order_y", match.order_y),
                ("order_z", match.order_z),
                ("frequency_error", match.frequency_error_hz),
            )
            evidence.extend(
                cls._evidence(
                    f"evidence.{prefix}.{name}",
                    SourceAnalysisCode.BASS_DECAY_CORRELATION,
                    f"{prefix}.{name}",
                    value,
                )
                for name, value in values
            )
        return evidence

    @staticmethod
    def _frequency_code(frequency):
        return f"{frequency:g}".replace(".", "_") + "hz"

    @staticmethod
    def _evidence(code, source, fact, value):
        return EvidenceReference(
            code=code,
            source_analysis=source,
            fact_code=fact,
            evidence_level=EvidenceLevel.CALCULATED,
            value=value,
        )

    @classmethod
    def _correlation_links(cls, global_analysis, domain_evidence):
        links = []
        for correlation in global_analysis.correlations:
            evidence = [
                domain_evidence[source]
                for source in correlation.source_analyses
                if source in domain_evidence
            ]
            if len(evidence) != len(correlation.source_analyses):
                continue

            links.append(
                ExplanationLink(
                    code=f"explanation.correlation.{correlation.code.lower()}",
                    fact_codes=tuple(item.fact_code for item in evidence),
                    evidence_codes=tuple(item.code for item in evidence),
                    correlation_codes=(correlation.code,),
                )
            )
        return links

    @classmethod
    def _recommendation_links(
        cls,
        global_analysis,
        recommendation_analysis,
        domain_evidence,
        evidence_references,
    ):
        links = []
        evidence_by_code = {
            item.code: item for item in evidence_references
        }
        for recommendation in recommendation_analysis.recommendations:
            recommendation_evidence = dict(domain_evidence)
            if recommendation.code == "INVESTIGATE_DRR_CHANNEL_DIFFERENCES":
                asymmetric = evidence_by_code.get(
                    "evidence.direct_reverberant.asymmetric_band_count"
                )
                if asymmetric is not None:
                    recommendation_evidence[
                        SourceAnalysisCode.DIRECT_REVERBERANT
                    ] = asymmetric
            if recommendation.code == "IMPROVE_DIRECT_SOUND_DOMINANCE":
                broadband = evidence_by_code.get(
                    "evidence.direct_reverberant.broadband_drr_db"
                )
                if broadband is not None:
                    recommendation_evidence[
                        SourceAnalysisCode.DIRECT_REVERBERANT
                    ] = broadband
            if recommendation.code == "INVESTIGATE_RT60_CHANNEL_DIFFERENCES":
                reliable = evidence_by_code.get(
                    "evidence.rt60.reliable_difference_count"
                )
                if reliable is not None:
                    recommendation_evidence[SourceAnalysisCode.RT60] = reliable
            if recommendation.code == "COMPARE_BASS_DECAY_CHANNELS":
                differences = evidence_by_code.get(
                    "evidence.bass_decay.significant_difference_count"
                )
                if differences is not None:
                    recommendation_evidence[
                        SourceAnalysisCode.BASS_DECAY
                    ] = differences
            if recommendation.code == "CHECK_MODAL_EXCITATION":
                modal_count = evidence_by_code.get(
                    "evidence.bass_decay.modal_match.count"
                )
                if modal_count is not None:
                    recommendation_evidence[
                        SourceAnalysisCode.BASS_DECAY_CORRELATION
                    ] = modal_count
            evidence = [
                recommendation_evidence[source]
                for source in recommendation.source_analyses
                if source in recommendation_evidence
            ]
            if (
                not evidence
                or len(evidence) != len(recommendation.source_analyses)
            ):
                continue

            if recommendation.code == "CHECK_MODAL_EXCITATION":
                evidence.extend(
                    item
                    for item in evidence_references
                    if item.code.startswith(
                        "evidence.bass_decay.modal_match."
                    )
                    and item.code
                    != "evidence.bass_decay.modal_match.count"
                )
            if recommendation.code in {
                "RETAKE_CLIPPED_MEASUREMENT",
                "IMPROVE_SIGNAL_TO_NOISE",
                "FIX_CHANNEL_TIMING",
                "COMPLETE_REQUIRED_CHANNELS",
                "CHECK_MEASUREMENT_METADATA",
            }:
                evidence = [
                    item for item in evidence_references
                    if item.source_analysis in recommendation.source_analyses
                ]

            recommendation_sources = set(recommendation.source_analyses)
            correlation_codes = tuple(
                correlation.code
                for correlation in global_analysis.correlations
                if set(correlation.source_analyses).issubset(recommendation_sources)
            )
            links.append(
                ExplanationLink(
                    code=(
                        "explanation.recommendation."
                        f"{recommendation.code.lower()}"
                    ),
                    fact_codes=tuple(item.fact_code for item in evidence),
                    evidence_codes=tuple(item.code for item in evidence),
                    correlation_codes=correlation_codes,
                    recommendation_codes=(recommendation.code,),
                )
            )
        return links

    @staticmethod
    def _evidence_code(domain_code: str) -> str:
        return f"evidence.global.domain.{domain_code.lower()}.score"

    @staticmethod
    def _fact_code(domain_code: str) -> str:
        return f"global.domain.{domain_code.lower()}.score"
