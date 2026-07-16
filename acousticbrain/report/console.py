from .report import Report
from .action_oriented_positioning_presenter import (
    ActionOrientedPositioningPresenter,
)
from .decision_first_presenter import DecisionFirstReportPresenter
from .one_minute_executive_summary_presenter import (
    OneMinuteExecutiveSummaryPresenter,
)


class ConsoleReporter:

    def __init__(self, *, detailed_traceability=False):
        self.detailed_traceability = detailed_traceability

    def print(self, report: Report):

        print()
        print("=" * 60)
        print("ACOUSTICBRAIN REPORT")
        print("=" * 60)
        print()

        print(f"Projet : {report.project_name}")
        decision = DecisionFirstReportPresenter().present(report)
        self._print_one_minute(
            OneMinuteExecutiveSummaryPresenter().present(decision)
        )
        self._print_decision_first(decision)
        self._print_action_oriented_positioning(
            ActionOrientedPositioningPresenter().present(report)
        )
        if report.room_properties is not None:

            rp = report.room_properties

            print()

            print("Salle")

            print(
                f"Volume : {rp.volume:.2f} m³"
            )

            print(
                f"Surface : {rp.floor_area:.2f} m²"
            )

            print(
                f"Schroeder : "
                f"{rp.schroeder_frequency:.1f} Hz"
            )

        geometry = report.room_geometry
        if geometry is not None:
            print()
            print("Géométrie")
            print(f"Source : {geometry.source}")
            print(f"Modèle : {geometry.model}")
            print(f"Version : {geometry.model_version}")
            print(
                "Dimensions : "
                f"{geometry.length_m:.2f} × {geometry.width_m:.2f} × "
                f"{geometry.height_m:.2f} m"
            )
            print(f"Complétude : {geometry.completeness:.0f} %")
            feature_completeness = (
                f"{geometry.feature_completeness:.0f} %"
                if geometry.feature_completeness is not None
                else "indisponible"
            )
            print(f"Complétude des features : {feature_completeness}")
            print(
                "Informations disponibles : "
                f"{geometry.oriented_speaker_count}/{geometry.speaker_count} orientations, "
                f"{geometry.surface_material_count} matériaux, "
                f"{geometry.placed_covering_zone_count}/{geometry.covering_zone_count} revêtements placés, "
                f"{geometry.placed_furniture_count}/{geometry.furniture_count} meubles placés, "
                f"{geometry.placed_treatment_count}/{geometry.treatment_count} traitements placés"
            )
            print(f"Compatibilité des sources : {geometry.comparison_status}")
            if geometry.differing_fields:
                print(
                    "Avertissement : RoomDescription et Room legacy divergent "
                    "sur " + ", ".join(geometry.differing_fields)
                )
            if geometry.propagation_scene_id is not None:
                print()
                print("Géométrie de propagation")
                print(f"Source de scène : {geometry.propagation_scene_source}")
                print(f"Version de scène : {geometry.propagation_scene_version}")
                print(f"Identifiant de scène : {geometry.propagation_scene_id}")
                print(
                    "Éléments : "
                    f"{geometry.propagation_surface_count} surfaces, "
                    f"{geometry.propagation_region_count} régions"
                )
                print(
                    "Complétude de propagation : "
                    f"{geometry.propagation_completeness:.0f} %"
                )

        materials = report.surface_materials
        if materials is not None:
            print()
            print("Surface materials")
            print(f"Completeness: {materials.completeness:.0f} %")
            for material in materials.materials:
                print()
                print(f"Material: {material.material_id} — {material.display_name}")
                print(f"Source: {material.source}")
                print(f"Confidence: {material.confidence:.1f} %")
                print(f"Quality: {material.quality}")
                print(f"Precision: {material.precision}")
                print(
                    "Provenance: "
                    + (", ".join(material.provenance_codes) or "none")
                )
                self._print_material_coefficients(
                    "Absorption", material.absorption_coefficients
                )
                self._print_material_coefficients(
                    "Diffusion", material.diffusion_coefficients
                )
                self._print_material_coefficients(
                    "Transmission", material.transmission_coefficients
                )
            print("Assignments:")
            for target in materials.targets:
                print(
                    f" • {target.target_kind} {target.target_id}: "
                    f"{target.material_id or 'missing'}"
                )
                if target.material_id is not None:
                    print(
                        f"   Description source: {target.description_source}; "
                        f"confidence: {target.description_confidence:.1f} %"
                    )
                    print(
                        "   Description provenance: "
                        + (
                            ", ".join(target.description_provenance_codes)
                            or "none"
                        )
                    )
            print(
                "Available facts: "
                + (", ".join(materials.available_fact_codes) or "none")
            )
            print(
                "Missing facts: "
                + (", ".join(
                    (*materials.missing_fact_codes,
                     *materials.missing_material_target_codes)
                ) or "none")
            )

        material_candidates = report.material_aware_reflection_candidates
        if material_candidates is not None:
            print()
            print("Material-aware reflection candidates")
            for candidate in material_candidates.candidates:
                print()
                print(f"Candidate: {candidate.candidate_id}")
                print(f"Path: {candidate.path_id}")
                print(f"Correlation: {candidate.correlation_id or 'none'}")
                print(
                    "Target: "
                    + (
                        f"region {candidate.region_id} on {candidate.surface_id}"
                        if candidate.region_id is not None
                        else f"surface {candidate.surface_id}"
                    )
                )
                if candidate.theoretical_delay_ms is not None:
                    print(
                        "Timing: "
                        f"theoretical {candidate.theoretical_delay_ms:.3f} ms; "
                        f"observed {candidate.measured_delay_ms:.3f} ms; "
                        f"difference {candidate.timing_error_ms:.3f} ms"
                    )
                print(
                    "Geometry: "
                    f"{candidate.geometric_status}; "
                    f"score {candidate.geometric_temporal_score:.1f} / 100"
                )
                print(
                    "Material: "
                    f"{candidate.material_assessment}; "
                    f"id {candidate.material_id or 'unknown'}"
                )
                print(
                    "Informative ranking: "
                    f"{candidate.informative_rank or 'none'}; "
                    f"score {candidate.overall_compatibility_score:.1f} / 100; "
                    f"status {candidate.status}"
                )
                print(f"Causality: {candidate.causality_status}")
                print(f"Eligibility impact: {candidate.eligibility_impact}")
                print("Limitations: " + ", ".join(candidate.limitations))

        reflection_planning = report.controlled_reflection_verification_planning
        if reflection_planning is not None:
            print()
            print("Controlled reflection verification proposals")
            for proposal in reflection_planning.proposals:
                print()
                print(
                    f"Proposal {proposal.proposal_order}: {proposal.proposal_id}"
                )
                print(f"Source candidate: {proposal.source_candidate_id}")
                print(
                    f"Target: {proposal.target_kind.lower()} {proposal.target_id}"
                )
                print(f"Method: {proposal.method}")
                print(
                    "Conditions: "
                    f"{proposal.reference_condition_code} -> "
                    f"{proposal.intervention_condition_code}"
                )
                print(
                    "Controlled variables: "
                    + ", ".join(proposal.controlled_variable_codes)
                )
                print(
                    "Changed variables: "
                    + ", ".join(proposal.changed_variable_codes)
                )
                print(
                    "Observables: " + ", ".join(proposal.observable_fact_codes)
                )
                print(f"Execution: {proposal.execution_status}")
                print(f"Causality: {proposal.causality_status}")
                print(f"Eligibility impact: {proposal.eligibility_impact}")
                print(f"Recommendation impact: {proposal.recommendation_impact}")
                print(
                    "Source evidence: "
                    + ", ".join(proposal.source_evidence_codes)
                )
                print(
                    "Source provenance: "
                    + (
                        ", ".join(proposal.source_provenance_codes)
                        or "none"
                    )
                )
                print(
                    "Planning rules: "
                    + ", ".join(proposal.planning_rule_codes)
                )
                print("Limitations: " + ", ".join(proposal.limitations))
            for exclusion in reflection_planning.exclusions:
                print()
                print(
                    "Excluded candidate: "
                    f"{exclusion.source_candidate_id} — {exclusion.reason}"
                )
                print(
                    "Source evidence: "
                    + ", ".join(exclusion.source_evidence_codes)
                )
                print(
                    "Source provenance: "
                    + (
                        ", ".join(exclusion.source_provenance_codes)
                        or "none"
                    )
                )

        reflection_declarations = (
            report.controlled_reflection_experiment_declarations
        )
        if reflection_declarations:
            print()
            print("Controlled reflection experiment declarations")
            for declaration in reflection_declarations:
                print()
                print(f"Declaration: {declaration.declaration_id}")
                print(f"Proposal: {declaration.proposal_id}")
                print(f"Status: {declaration.status}")
                if declaration.status_reason_code is not None:
                    print(f"Status reason: {declaration.status_reason_code}")
                for label, condition in (
                    ("Baseline", declaration.reference_condition),
                    ("Intervention", declaration.intervention_condition),
                ):
                    print(f"{label} condition: {condition.condition_code}")
                    if condition.measurement_references:
                        for reference in condition.measurement_references:
                            content_hash = reference.content_hash or "none"
                            print(
                                " • Measurement "
                                f"{reference.reference_id}: "
                                f"{reference.experiment_id}/"
                                f"{reference.measurement_name}; "
                                f"hash {content_hash}"
                            )
                    else:
                        print(" • Measurements: none")
                print("Result interpretation: NONE")
                print("Causality: NOT_ESTABLISHED")
                print("Ranking impact: NONE")
                print("Recommendation impact: NONE")

        reflection_comparisons = (
            report.controlled_reflection_experiment_comparisons
        )
        if reflection_comparisons:
            print()
            print("Deterministic reflection experiment comparisons")
            for comparison in reflection_comparisons:
                print()
                print(f"Comparison: {comparison.comparison_id}")
                print(f"Declaration: {comparison.experiment_declaration_id}")
                print(f"Proposal: {comparison.proposal_id}")
                print(f"Temporal window: {comparison.temporal_window_code}")
                print(f"Status: {comparison.status}")
                if comparison.reason_codes:
                    print("Reasons: " + ", ".join(comparison.reason_codes))
                for difference in comparison.observed_differences:
                    print(
                        f" • {difference.observable_code}: "
                        f"{difference.baseline_value:g} -> "
                        f"{difference.intervention_value:g} "
                        f"{difference.unit}; delta "
                        f"{difference.signed_difference:+g}"
                    )
                    print(
                        "   Baseline provenance: "
                        + ", ".join(difference.baseline_provenance_codes)
                    )
                    print(
                        "   Intervention provenance: "
                        + ", ".join(difference.intervention_provenance_codes)
                    )
                print(f"Causality: {comparison.causality_status}")
                print(f"Ranking impact: {comparison.ranking_impact}")
                print(f"Recommendation impact: {comparison.recommendation_impact}")
                print(f"Eligibility impact: {comparison.eligibility_impact}")

        hypothesis_updates = (
            report.controlled_reflection_hypothesis_status_updates
        )
        if hypothesis_updates:
            print()
            print("Controlled reflection hypothesis observation status")
            for update in hypothesis_updates:
                print()
                print(f"Update: {update.update_id}")
                print(f"Target: {update.target_kind} {update.target_id}")
                print(f"Proposal: {update.proposal_id}")
                print(f"Declaration: {update.experiment_declaration_id}")
                print(f"Comparison: {update.comparison_id or 'none'}")
                print(f"Observation status: {update.status}")
                print(
                    "Measured facts: "
                    + (", ".join(update.measured_fact_codes) or "none")
                )
                print(
                    "Comparison results: "
                    + (", ".join(update.comparison_result_codes) or "none")
                )
                print("Transition rules: " + ", ".join(update.transition_rule_codes))
                print("Status provenance: " + ", ".join(update.status_provenance_codes))
                print("Justification: " + ", ".join(update.justification_codes))
                print(f"Causality: {update.causality_status}")
                print(f"Recommendation impact: {update.recommendation_impact}")
                print(f"Ranking impact: {update.ranking_impact}")
                print(f"Eligibility impact: {update.eligibility_impact}")

        discovery = report.experiments_discovered
        if discovery is not None:
            print()
            print("EXPERIMENTS DISCOVERED")
            print()
            for experiment in discovery.experiments:
                print(experiment.experiment_id)
                print(f"État : {experiment.state}")
                print(f"Fichiers : {experiment.file_count}")
                print(f"Date : {experiment.timestamp}")
                print(
                    "Canaux : "
                    + (", ".join(experiment.available_channels) or "aucun")
                )
                print()

        comparison_analysis = report.experiment_comparison
        if comparison_analysis is not None:
            print()
            print("ÉVOLUTION DES EXPÉRIENCES")
            print()
            print("Chronologie : " + " → ".join(comparison_analysis.chronology))
            print()
            print("Comparaisons locales")
            for index, comparison in enumerate(comparison_analysis.local_comparisons):
                if index:
                    print()
                self._print_experiment_evolution(
                    comparison, comparison_analysis.detailed_traceability
                )
            print()
            print("Synthèse cumulative depuis la baseline")
            for index, comparison in enumerate(comparison_analysis.cumulative_comparisons):
                if index:
                    print()
                self._print_experiment_evolution(
                    comparison, comparison_analysis.detailed_traceability
                )

        if report.experiment_campaigns:
            print()
            print("CAMPAGNES EXPÉRIMENTALES")
            for campaign in report.experiment_campaigns:
                print()
                print(f"Campagne : {campaign.campaign_code}")
                print(f"Protocole : {campaign.protocol_id}")
                print(f"Hypothèse : {campaign.hypothesis_code}")
                print(f"Objectif : {campaign.objective_label}")
                print(f"Statut : {campaign.status}")
                print("Mesures :")
                for measurement in campaign.measurements:
                    sign = "+" if measurement.offset_m > 0.0 else ""
                    print(
                        f" ✓ {measurement.experiment_id} — {measurement.role} "
                        f"({sign}{measurement.offset_m:.2f} m) — {measurement.state}"
                    )
                print("Résultats par position :")
                for branch in campaign.branch_results:
                    sign = "+" if branch.offset_m > 0.0 else ""
                    print(
                        f" • {branch.role} ({sign}{branch.offset_m:.2f} m, "
                        f"{branch.experiment_id}) — évolution acoustique "
                        f"{branch.acoustic_outcome}"
                    )
                    if (
                        branch.reference_value is not None
                        and branch.observed_value is not None
                    ):
                        print(
                            "   Décroissance maximale : "
                            f"{branch.reference_value:.3f} → "
                            f"{branch.observed_value:.3f} s"
                        )
                    for label in branch.result_labels:
                        print(f"   - {label}")
                print("Conclusion actuelle :")
                for conclusion in campaign.conclusions:
                    marker = "✓" if conclusion.established else "✗"
                    print(f" {marker} {conclusion.label}")
                for metric in campaign.metrics:
                    if metric.code == "MAXIMUM_BASS_DECAY_REDUCTION":
                        print(
                            "Diminution maximale observée : "
                            f"{metric.reference_value:.3f} → {metric.best_value:.3f} s "
                            f"({metric.improvement_percent:.1f} %, "
                            f"{metric.best_experiment_id})"
                        )
                print(
                    "Discriminations restantes : "
                    + (
                        ", ".join(campaign.unresolved_discrimination_labels)
                        or "aucune"
                    )
                )
                print(
                    "Prochaine discrimination nécessaire : "
                    + (campaign.next_discrimination_label or "aucune")
                )
                if self.detailed_traceability or campaign.detailed_traceability:
                    print(f"Trace : {campaign.trace_id}")
                    print(
                        "Comparaisons sources : "
                        + (
                            ", ".join(campaign.trace_comparison_result_ids)
                            or "aucune"
                        )
                    )
                    print(
                        "Observations sources : "
                        + (
                            ", ".join(campaign.trace_observation_codes)
                            or "aucune"
                        )
                    )
                    print(
                        "Règles appliquées : "
                        + (
                            ", ".join(campaign.trace_applied_rule_codes)
                            or "aucune"
                        )
                    )

        causal = report.causal_discrimination
        if causal is not None:
            print()
            print("DISCRIMINATION CAUSALE")
            print()
            print(f"Protocole : {causal.protocol_code}")
            print(f"Statut : {causal.status}")
            print(f"Résultat discriminant : {causal.outcome}")
            print("Étapes terminées :")
            for step in causal.completed_steps:
                print(
                    f" • {step.step_index} — {step.step_code} "
                    f"({step.experiment_id})"
                )
                print(
                    "   Variables contrôlées : "
                    + (", ".join(step.controlled_variable_codes) or "aucune")
                )
                print(
                    "   Variables modifiées : "
                    + (", ".join(step.changed_variable_codes) or "aucune")
                )
                print(
                    "   Variables inconnues : "
                    + (", ".join(step.unknown_variable_codes) or "aucune")
                )
                if (
                    step.step_code
                    in {"STEP_2_SPEAKER_SWAP", "STEP_3_SIGNAL_CHAIN_SWAP"}
                    and not step.observation_codes
                ):
                    print("   Observation causale : non encore qualifiée")
                else:
                    print(
                        "   Observations : "
                        + (", ".join(step.observation_codes) or "aucune")
                    )
            unqualified_steps = tuple(
                step.step_code
                for step in causal.completed_steps
                if step.step_code
                in {"STEP_2_SPEAKER_SWAP", "STEP_3_SIGNAL_CHAIN_SWAP"}
                and not step.observation_codes
            )
            if unqualified_steps:
                print("Conclusion causale : non établie")
                print(
                    "Prochaine information nécessaire : qualifier "
                    "l’observation de "
                    + ", ".join(unqualified_steps)
                )
            print(
                "Étapes restantes : "
                + (", ".join(causal.remaining_step_codes) or "aucune")
            )
            print(
                "Étapes différées : "
                + (", ".join(causal.deferred_step_codes) or "aucune")
            )
            print("Trajectoires compatibles :")
            if causal.compatible_trajectories:
                for trajectory in causal.compatible_trajectories:
                    print(
                        f" • {trajectory.trajectory_code} — support "
                        f"{trajectory.support_score:.1f} / 100"
                    )
            else:
                print(" • aucune")
            print("Trajectoires contradictoires :")
            if causal.contradicted_trajectories:
                for trajectory in causal.contradicted_trajectories:
                    print(
                        f" • {trajectory.trajectory_code} — contre-preuves : "
                        + ", ".join(trajectory.counter_evidence_codes)
                    )
            else:
                print(" • aucune")
            print(
                "Discriminations résolues : "
                + (", ".join(causal.resolved_discrimination_codes) or "aucune")
            )
            print(
                "Discriminations restantes : "
                + (", ".join(causal.remaining_discrimination_codes) or "aucune")
            )
            print(
                "Nouvelles ambiguïtés : "
                + (", ".join(causal.new_ambiguity_codes) or "aucune")
            )
            print(
                "Ambiguïtés perdues : "
                + (", ".join(causal.lost_ambiguity_codes) or "aucune")
            )
            print("Décisions utilisateur :")
            if causal.discrimination_decisions:
                for decision in causal.discrimination_decisions:
                    print(
                        f" • {decision.discrimination_code} — {decision.status} "
                        f"({decision.reason}, {decision.experiment_id})"
                    )
            else:
                print(" • aucune")
            print(
                "Prochain protocole recommandé : "
                + (causal.recommended_next_protocol or "aucun")
            )
            if self.detailed_traceability or causal.detailed_traceability:
                print(f"Trace : {causal.trace_id}")
                print(
                    "Observations tracées : "
                    + (", ".join(causal.trace_observation_codes) or "aucune")
                )
                print(
                    "Règles appliquées : "
                    + (", ".join(causal.trace_applied_rule_codes) or "aucune")
                )
                print(
                    "Décisions tracées : "
                    + (", ".join(causal.trace_decision_codes) or "aucune")
                )

        learning = report.longitudinal_experimental_learning
        if learning is not None and learning.states:
            print()
            print("APPRENTISSAGE EXPÉRIMENTAL")
            for state in learning.states:
                print()
                print(f"Hypothèse : {state.hypothesis_code}")
                print(f"État de campagne : {state.learning_status}")
                print(
                    "Preuves longitudinales admissibles : "
                    + (
                        ", ".join(
                            state.evidence_contributing_experiment_codes
                        )
                        or "aucune"
                    )
                )
                self._print_historical_experiments(
                    "Historique expérimental conservé — discrimination",
                    state.discrimination_source_experiments,
                )
                self._print_historical_experiments(
                    "Historique expérimental conservé — campagnes",
                    state.campaign_source_experiments,
                )
                print("Historique non admissible comme nouvelle preuve :")
                if state.excluded_experiments:
                    for code, reason in state.excluded_experiments:
                        print(f" • {code} — {reason}")
                else:
                    print(" • aucune")
                print(
                    "Observations favorables : "
                    + (", ".join(state.supporting_observation_ids) or "aucune")
                )
                print(
                    "Observations contradictoires : "
                    + (", ".join(state.contradicting_observation_ids) or "aucune")
                )
                print(
                    "Observations inchangées : "
                    + (", ".join(state.unchanged_observation_ids) or "aucune")
                )
                print(
                    "Observations inconclusives : "
                    + (", ".join(state.inconclusive_observation_ids) or "aucune")
                )
                print("Ambiguïtés résolues :")
                if state.resolved_ambiguity_provenance:
                    for source in state.resolved_ambiguity_provenance:
                        print(f" • {source.ambiguity_code}")
                        print(
                            "   Provenance : "
                            f"{source.protocol_code} — {source.source_id}"
                        )
                        if source.source_experiments:
                            print(
                                "   Historique expérimental de la trace : "
                                + ", ".join(
                                    item.experiment_code
                                    for item in source.source_experiments
                                )
                            )
                        else:
                            print(
                                "   Historique expérimental de la trace : "
                                "indisponible"
                            )
                elif state.resolved_ambiguities:
                    for code in state.resolved_ambiguities:
                        print(f" • {code} — provenance expérimentale indisponible")
                else:
                    print(" • aucune")
                print(
                    "Ambiguïtés restantes : "
                    + (", ".join(state.remaining_ambiguities) or "aucune")
                )
                print(
                    "Prochaine information nécessaire : "
                    + state.next_information_need
                )
                source_statuses = {
                    item.declaration_status
                    for item in state.discrimination_source_experiments
                }
                if state.resolved_ambiguities and (
                    not state.discrimination_source_experiments
                    or source_statuses
                    & {"UNKNOWN_DECLARATION", "DECLARATION_UNAVAILABLE"}
                ):
                    print("Limite :")
                    print(
                        "Les résultats historiques de la discrimination sont "
                        "conservés, mais ses expériences ne sont pas "
                        "requalifiées comme interventions contrôlées."
                    )
                print(f"Causalité : {state.causality_status}")

        if (
            comparison_analysis is None
            and causal is None
            and not report.experiment_campaigns
        ):
            print()
            print()
        elif causal is not None and report.recommendations:
            print()

        if report.recommendations:

            print("Recommandations structurées")
            print()

            for recommendation in report.recommendations:
                print(f" • {recommendation.code}")
                print(f"   Action : {recommendation.action}")
                print(f"   Cible : {recommendation.target}")
                if recommendation.status.name != "ACTIVE":
                    print(f"   Statut : {recommendation.status.name}")
                    print(f"   Raison : {recommendation.status_reason}")
                else:
                    print(f"   Priorité : {recommendation.priority.name}")
                print(f"   Confiance : {recommendation.confidence}%")
                print(
                    "   Provenance : "
                    + ", ".join(recommendation.source_analyses)
                )
                if recommendation.hypothesis_codes:
                    print(
                        "   Hypothèses : "
                        + ", ".join(recommendation.hypothesis_codes)
                    )
                if recommendation.verification_action:
                    print("   Nature : vérification")

                if recommendation.parameters:
                    print("   Paramètres :")
                    for name, value in recommendation.parameters.items():
                        print(f"    - {name} : {value}")

                print()

        global_analysis = report.global_analysis
        if global_analysis is not None:

            print("Synthèse acoustique globale")
            print()

            score = (
                f"{global_analysis.score:.1f} / 100"
                if global_analysis.score is not None
                else "indisponible"
            )
            confidence = (
                f"{global_analysis.confidence:.1f}%"
                if global_analysis.confidence is not None
                else "indisponible"
            )
            print(f"Score : {score}")
            print(f"Confiance : {confidence}")
            print(
                "Domaines prioritaires : "
                + (", ".join(global_analysis.priority_domains) or "aucun")
            )
            print(
                "Analyses sources : "
                + (", ".join(global_analysis.source_analyses) or "aucune")
            )
            blocked_families = [
                family for family, status in global_analysis.readiness_statuses
                if status == "BLOCKED"
            ]
            if blocked_families:
                print(
                    "Avertissement : résultats calculés à titre provisoire "
                    "pour les familles BLOCKED : "
                    + ", ".join(blocked_families)
                )
                print("Validité technique : non garantie pour ces familles")
            print()

            for domain in global_analysis.domains:
                domain_confidence = (
                    f"{domain.confidence:.1f}%"
                    if domain.confidence is not None
                    else "indisponible"
                )
                print(f" • Domaine {domain.code}")
                score_label = (
                    "Score acoustique"
                    if domain.contributes_to_acoustic_score
                    else "Score technique de disponibilité"
                )
                print(f"   {score_label} : {domain.score:.1f} / 100")
                print(f"   Confiance : {domain_confidence}")
                print(f"   Provenance : {domain.source_analysis}")
                print(f"   Nature : {domain.kind}")
                print(
                    "   Contribution au score acoustique : "
                    + ("oui" if domain.contributes_to_acoustic_score else "non")
                )
                if domain.recommendation_codes:
                    status_by_code = dict(domain.recommendation_statuses)
                    print(
                        "   Références d'action : "
                        + ", ".join(
                            code
                            if status_by_code.get(code, "ACTIVE") == "ACTIVE"
                            else f"{code} — {status_by_code[code]}"
                            for code in domain.recommendation_codes
                        )
                    )

            if global_analysis.domains:
                print()

            for correlation in global_analysis.correlations:
                print(f" • Corrélation {correlation.code}")
                print(f"   Domaines : {', '.join(correlation.domain_codes)}")
                print(f"   Score : {correlation.score:.1f} / 100")
                print(
                    "   Provenances : "
                    + ", ".join(correlation.source_analyses)
                )

            if global_analysis.correlations:
                print()

        traceability = report.traceability_analysis
        if traceability is not None:

            print("Traçabilité")
            print()
            print(
                "Analyses sources : "
                + (", ".join(traceability.source_analyses) or "aucune")
            )
            print(f"Preuves disponibles : {len(traceability.evidence_references)}")
            print(f"Liens explicatifs : {len(traceability.links)}")
            print()

            for evidence in (
                traceability.evidence_references
                if self.detailed_traceability
                else ()
            ):
                print(f" • Preuve {evidence.code}")
                print(f"   Fait : {evidence.fact_code}")
                print(f"   Analyse : {evidence.source_analysis}")
                print(f"   Niveau : {evidence.evidence_level}")
                if evidence.value is not None:
                    print(f"   Valeur : {evidence.value}")

            if self.detailed_traceability and traceability.evidence_references:
                print()

            for link in traceability.links if self.detailed_traceability else ():
                print(f" • Lien {link.code}")
                print(f"   Faits : {', '.join(link.fact_codes)}")
                print(f"   Preuves : {', '.join(link.evidence_codes)}")
                if link.correlation_codes:
                    print(
                        "   Corrélations : "
                        + ", ".join(link.correlation_codes)
                    )
                if link.recommendation_codes:
                    print(
                        "   Recommandations : "
                        + ", ".join(link.recommendation_codes)
                    )
                if link.hypothesis_codes:
                    print("   Hypothèses : " + ", ".join(link.hypothesis_codes))
                if link.protocol_codes:
                    print("   Protocoles : " + ", ".join(link.protocol_codes))
                if link.candidate_codes:
                    print("   Candidats : " + ", ".join(link.candidate_codes))
                if link.ranking_codes:
                    print("   Classement : " + ", ".join(link.ranking_codes))
                if link.recommended_candidate_codes:
                    print(
                        "   Expérience recommandée : "
                        + ", ".join(link.recommended_candidate_codes)
                    )
                if link.iteration_codes:
                    print("   Itérations : " + ", ".join(link.iteration_codes))

            if self.detailed_traceability and traceability.links:
                print()

        generated = getattr(report, "acoustic_hypothesis_experiment_generation", None)
        if generated is not None:
            print("HYPOTHÈSES EXPLORATOIRES ET CANDIDATS EXPÉRIMENTAUX")
            print()
            for hypothesis in generated.hypotheses[:3]:
                print(f"Hypothèse exploratoire : {hypothesis.hypothesis_code}")
                print(f"Statut exploratoire : {hypothesis.status}")
                facts = (
                    hypothesis.supporting_fact_codes
                    or hypothesis.contradicting_fact_codes
                    or hypothesis.rationale_codes
                    or hypothesis.missing_fact_codes
                )
                print("Pourquoi : " + (", ".join(facts[:3]) or "faits structurés insuffisants"))
                if hypothesis.uncertainty_reasons:
                    print("Limites : " + ", ".join(hypothesis.uncertainty_reasons))
                print(f"Causalité : {hypothesis.causality_status}")
                print()
            main_experiment = next(
                (
                    item
                    for item in generated.experiments
                    if item.candidate_id == generated.recommended_candidate_id
                ),
                None,
            )
            if main_experiment is None:
                print("Aucune expérience principale directement exécutable")
                missing = tuple(dict.fromkeys(
                    reason
                    for item in generated.experiments
                    for reason in item.blocking_reasons
                ))
                if missing:
                    print("Donnée nécessaire : " + ", ".join(missing))
                print()
            else:
                print("Expérience principale")
                print(f"Type : {main_experiment.experiment_type}")
                print(f"Cible : {main_experiment.target}")
                print()
            for experiment in generated.experiments[:3]:
                state = "EXÉCUTABLE" if not experiment.blocking_reasons else "BLOQUÉ"
                print(f"Candidat expérimental : {experiment.experiment_type} — {state}")
                print(f"Cible : {experiment.target}")
                if experiment.movement_direction is not None:
                    print(f"Direction : {experiment.movement_direction}")
                if experiment.step_distance_m is not None:
                    print(f"Distance : {experiment.step_distance_m:.2f} m")
                print(
                    "Effets mesurables attendus : "
                    + ", ".join(
                        item.observation_code for item in experiment.expected_observations
                    )
                )
                if experiment.acquisition_positions:
                    print()
                    print("Campagne proposée")
                    print(
                        f"Protocole : {experiment.sampling_protocol_id} "
                        f"v{experiment.sampling_protocol_version}"
                    )
                    print(f"Position centrale : {experiment.reference_position_id}")
                    print(
                        "Règle de comparabilité : "
                        + experiment.comparability_rule_code
                    )
                    for index, position in enumerate(experiment.acquisition_positions):
                        if index:
                            print("↓")
                        offsets = []
                        if position.longitudinal_offset_m is not None:
                            offsets.append(
                                f"longitudinal {position.longitudinal_offset_m:+.2f} m"
                            )
                        if position.lateral_offset_m is not None:
                            offsets.append(
                                f"latéral {position.lateral_offset_m:+.2f} m"
                            )
                        if position.vertical_offset_m is not None:
                            offsets.append(
                                f"vertical {position.vertical_offset_m:+.2f} m"
                            )
                        print(
                            position.position_id
                            + (f" ({', '.join(offsets)})" if offsets else "")
                        )
                        print(
                            f"  Rôle : {position.role} ; "
                            f"parent : {position.parent_position_id or 'aucun'} ; "
                            f"référence : {position.reference_position_id or 'aucune'} ; "
                            f"ordre : {position.acquisition_order}"
                        )
                    print()
                print("Mesures : " + ", ".join(experiment.required_measurements))
                print("Variables contrôlées : " + ", ".join(experiment.controlled_variables))
                if experiment.blocking_reasons:
                    print("Donnée nécessaire : " + ", ".join(experiment.blocking_reasons))
                print("Limite : test exploratoire sans garantie d’amélioration globale.")
                print(f"Causalité : {experiment.causality_status}")
                print()

        planning = report.experiment_planning
        if planning is not None:
            print(
                "PLANIFICATION EXPÉRIMENTALE — TRAÇABILITÉ"
                if generated is not None
                else "EXPÉRIENCE PRINCIPALE"
            )
            print()
            print(f"Statut : {planning.status}")
            candidate = planning.recommended_candidate
            if candidate is None:
                print("Code : aucune")
                print("Pourquoi aucun candidat n’est éligible :")
                reason_labels = {
                    "ALREADY_COMPLETED": "campagne déjà terminée",
                    "USER_DEFERRED": "investigation différée par décision utilisateur",
                    "GEOMETRY_PARAMETER_MISSING": "géométrie précise manquante",
                    "GEOMETRY_TIMING_INCOMPATIBLE": "délai théorique incompatible avec l’événement observé",
                    "GEOMETRY_UNCERTAINTY_TOO_HIGH": "incertitude géométrique trop élevée",
                    "GEOMETRY_CONFIDENCE_TOO_LOW": "confiance géométrique insuffisante",
                    "SBIR_FREQUENCY_MISMATCH_TOO_HIGH": "écart fréquentiel SBIR trop élevé",
                    "SBIR_PREDICTION_UNCERTAINTY_TOO_HIGH": "incertitude de prédiction SBIR trop élevée",
                    "PREREQUISITE_MISSING": "prérequis du protocole manquant",
                    "HYPOTHESIS_REFUTED": "hypothèse contredite",
                    "SOURCE_HYPOTHESIS_MISSING": "hypothèse source absente",
                    "INCOMPLETE_PROVENANCE": "provenance structurée insuffisante",
                    "CAUSAL_DISCRIMINATION_COMPLETED": "discrimination causale déjà terminée",
                    "ACQUISITION_PROTOCOL_INCOMPLETE": "protocole d’acquisition incomplet",
                }
                for item in planning.all_candidates:
                    if item.eligible:
                        continue
                    name = item.source_action_code or item.candidate_id
                    labels = tuple(
                        reason_labels.get(reason, reason)
                        for reason in item.ineligibility_reasons
                    )
                    print(f" • {name} — {', '.join(labels)}")
                if planning.uncovered_active_action_codes:
                    print(
                        " • Actions actives sans protocole planifiable : "
                        + ", ".join(planning.uncovered_active_action_codes)
                    )
            else:
                print(f"Code : {candidate.candidate_id}")
                print(f"Protocole : {candidate.source_protocol_id}")
                print(f"Hypothèse : {candidate.hypothesis_code}")
                print(
                    "Valeur informative : "
                    f"{candidate.informative_value:.2f} / 100"
                )
                print(f"Difficulté : {candidate.difficulty}")
                print(f"Réversibilité : {candidate.reversibility}")
                duration = (
                    f"{candidate.estimated_duration_minutes} min"
                    if candidate.estimated_duration_minutes is not None
                    else "indisponible"
                )
                print(f"Durée estimée : {duration}")
                print(f"Coût : {candidate.cost_category}")
                print(f"Objectif : {candidate.objective_code}")
                print(
                    "Faits à mesurer : "
                    + ", ".join(candidate.observable_fact_codes)
                )
                print(
                    "Raison principale du choix : "
                    + (candidate.primary_selection_reason or "aucune")
                )
                print(
                    "Prérequis : "
                    + (", ".join(candidate.prerequisite_codes) or "aucun")
                )
                if candidate.parameters:
                    print("Paramètres discriminants :")
                    for name, value in candidate.parameters.items():
                        print(f" • {name} : {value}")
                if candidate.changed_variable_codes:
                    print(
                        "Variables modifiées : "
                        + ", ".join(candidate.changed_variable_codes)
                    )
                if candidate.controlled_variable_codes:
                    print(
                        "Variables contrôlées : "
                        + ", ".join(candidate.controlled_variable_codes)
                    )
                print("Alternatives classées :")
                for alternative in planning.alternatives:
                    print(
                        f" • {alternative.candidate_id} — "
                        f"{alternative.informative_value:.2f} / 100"
                    )
            print()

            if self.detailed_traceability:
                print("Candidats expérimentaux exhaustifs")
                for item in planning.all_candidates:
                    eligibility = "éligible" if item.eligible else "inéligible"
                    print(f" • {item.candidate_id} — {eligibility}")
                    if item.ineligibility_reasons:
                        print(
                            "   Raisons : "
                            + ", ".join(item.ineligibility_reasons)
                        )
                print()

        session = report.optimization_session
        if session is not None:
            print("SESSION D’OPTIMISATION")
            print()
            print(f"Identifiant : {session.session_id}")
            print(f"Itération courante : {session.current_iteration}")
            print(f"Expériences terminées : {session.completed_experiments}")
            print(
                "Hypothèses ouvertes : "
                + (", ".join(session.open_hypotheses) or "aucune")
            )
            print(
                "Hypothèses renforcées : "
                + (", ".join(session.reinforced_hypotheses) or "aucune")
            )
            print(
                "Hypothèses réfutées : "
                + (", ".join(session.refuted_hypotheses) or "aucune")
            )
            gain = (
                f"{session.global_gain:+.1f} points"
                if session.global_gain is not None else "indisponible"
            )
            print(f"Gain global depuis l’état initial : {gain}")
            print(
                "Améliorations principales : "
                + (", ".join(session.main_improvements) or "aucune")
            )
            print(
                "Dégradations principales : "
                + (", ".join(session.main_degradations) or "aucune")
            )
            print(
                "Expérience en attente : "
                + (session.pending_experiment or "aucune")
            )
            print()

            for iteration in session.iterations:
                print(f"Itération {iteration.number}")
                print(f"Hypothèse testée : {iteration.hypothesis_code}")
                print(f"Expérience réalisée : {iteration.experiment_label}")
                print(f"État avant : {iteration.before_state_id}")
                print(f"État après : {iteration.after_state_id or 'en attente'}")
                print(
                    "Faits améliorés : "
                    + (", ".join(iteration.improved_fact_codes) or "aucun")
                )
                print(
                    "Faits dégradés : "
                    + (", ".join(iteration.degraded_fact_codes) or "aucun")
                )
                print(
                    "Résultat sur l’hypothèse : "
                    + (iteration.hypothesis_result or "en attente")
                )
                print()

            if self.detailed_traceability or session.detailed_traceability:
                for chain in session.trace_chains:
                    print(f"Chaîne de session {chain.progression_id}")
                    print(
                        f"Mesure ou état analysé : {chain.measurement_name} / "
                        f"{chain.source_state_id}"
                    )

                    print("Faits : " + (", ".join(chain.fact_codes) or "aucun"))
                    print(
                        "Corrélations : "
                        + (", ".join(chain.correlation_codes) or "aucune")
                    )
                    print(f"Hypothèse : {chain.hypothesis_code}")
                    print(f"Protocole ou expérience : {chain.protocol_id}")
                    print(f"Nouvel état : {chain.new_state_id}")
                    print(f"Comparaison : {chain.comparison_id}")
                    print(f"Évolution de l’hypothèse : {chain.evolution_result}")
                    print(f"Progression de la session : {chain.progression_id}")
                    print()

        for diagnostic, is_secondary in self._diagnostics_to_render(report):

            print("-" * 60)

            title = diagnostic.title
            if is_secondary:
                title += " (secondaire)"
            print(title)
            print()

            if diagnostic.observations:

                print("Observations")

                for observation in diagnostic.observations:
                    print(f" • {observation}")

                print()

            if diagnostic.conclusion:

                print("Conclusion")
                print()
                print(diagnostic.conclusion)
                print()

            else:

                print(diagnostic.message)
                print()

            print(f"Gravité : {diagnostic.severity}")
            if diagnostic.analysis_family is not None:
                print(f"Famille : {diagnostic.analysis_family}")
                print(f"Readiness : {diagnostic.readiness_status}")
                if diagnostic.provisional:
                    print("Statut du résultat : calculé à titre provisoire")
                print(f"Validité : {diagnostic.validity}")
            if diagnostic.score is not None:
                print(f"{diagnostic.score_label} : {diagnostic.score:.0f} / 100")
            print(f"Confiance : {diagnostic.confidence}%")
            print(f"Niveau de preuve : {diagnostic.evidence_level.value}")
            print()

            if diagnostic.causes:

                print("Causes")

                for cause in diagnostic.causes:
                    print(f" • {cause}")

                print()

            if diagnostic.recommendations:

                print("Recommandations")

                for recommendation in diagnostic.recommendations:
                    print(f" • {recommendation}")

                print()

    def _print_experiment_evolution(self, comparison, detailed_traceability=False):
        print()
        if comparison.comparison_type == "CUMULATIVE":
            print(
                "Comparaison cumulative depuis baseline — "
                f"{comparison.after_experiment_id}"
            )
        else:
            print(f"Expérience {comparison.after_experiment_id}")
        print(f"Avant : {comparison.before_experiment_id}")
        print(f"Après : {comparison.after_experiment_id}")
        print(f"Comparabilité : {comparison.eligibility}")
        if comparison.ineligibility_reasons:
            print("Raisons : " + ", ".join(comparison.ineligibility_reasons))
        print(f"Protocole : {comparison.source_protocol_id or 'non déclaré'}")
        print(f"Hypothèse : {comparison.source_hypothesis_code or 'non déclarée'}")
        if comparison.experiment_kind != "UNKNOWN":
            print(f"Déclaration expérimentale : {comparison.experiment_kind}")
            print(
                "Référence déclarée : "
                + (comparison.reference_experiment_code or "non établie")
            )
            print(
                "Variables modifiées déclarées : "
                + (", ".join(comparison.modified_variables) or "aucune")
            )
            print(
                "Variables contrôlées déclarées : "
                + (", ".join(comparison.controlled_variables) or "aucune")
            )
        for name, value in comparison.experiment_parameters:
            print(f"{name} : {value}")
        print(f"Évolution acoustique : {comparison.acoustic_outcome}")
        print(f"Évolution de l’hypothèse : {comparison.outcome}")
        if comparison.experimental_result_labels:
            print(
                "Résultat expérimental : "
                + ", ".join(comparison.experimental_result_labels)
            )
        print("Faits améliorés : " + (", ".join(comparison.improved_fact_codes) or "aucun"))
        print("Faits dégradés : " + (", ".join(comparison.degraded_fact_codes) or "aucun"))
        print("Faits modifiés sans direction : " + (", ".join(comparison.changed_fact_codes) or "aucun"))
        print("Faits inchangés pertinents : " + (", ".join(comparison.unchanged_fact_codes) or "aucun"))
        print("Faits indisponibles : " + (", ".join(comparison.unavailable_fact_codes) or "aucun"))
        if comparison.observation_labels:
            print("Observations :")
            for label in comparison.observation_labels:
                print(f" • {label}.")
        if comparison.counter_fact_codes:
            print("Contre-faits : " + ", ".join(comparison.counter_fact_codes))
        if comparison.unresolved_discrimination_labels:
            print("Limites :")
            for label in comparison.unresolved_discrimination_labels:
                print(f" • {label}.")
        confidence = (
            f"{comparison.technical_confidence:.1f}%"
            if comparison.technical_confidence is not None else "indisponible"
        )
        print(f"Confiance : {confidence}")
        if self.detailed_traceability or detailed_traceability:
            print(f"Trace : {comparison.trace_id}")
            print(f"Hash avant : {comparison.trace_before_file_hash}")
            print(f"Hash après : {comparison.trace_after_file_hash}")
            print("Faits avant : " + (", ".join(comparison.trace_before_fact_codes) or "aucun"))
            print("Faits après : " + (", ".join(comparison.trace_after_fact_codes) or "aucun"))
            print("Deltas : " + (", ".join(comparison.trace_delta_fact_codes) or "aucun"))
            print("Faits expérimentaux : " + (", ".join(comparison.trace_observed_fact_codes) or "aucun"))
            print("Discriminations ouvertes : " + (", ".join(comparison.trace_unresolved_discrimination_codes) or "aucune"))

    @staticmethod
    def _print_one_minute(summary):
        print()
        print("EN UNE MINUTE")
        for heading, lines in (
            ("Situation", summary.situation),
            ("Verdict", summary.verdict),
            ("Puis-je conclure ?", summary.conclusion),
            ("Ce que je fais maintenant", summary.actions),
            ("Pourquoi", summary.reasons),
            ("Confiance", summary.confidence),
        ):
            print()
            print(heading)
            for line in lines:
                prefix = "• " if heading == "Ce que je fais maintenant" else ""
                print(prefix + line)

    @staticmethod
    def _print_decision_first(decision):
        print()
        print("DÉCISION ACOUSTIQUE")
        print()
        print("Objectif actuel")
        print(decision.objective)

        print()
        print("Verdict")
        print(decision.verdict)
        for item in decision.comparison_context:
            print(f" • {item}")

        if decision.tested_variable_declared:
            print()
            print("Déclaration expérimentale")
            print(decision.experiment_kind)
            print("Référence")
            print(decision.reference_experiment_code or "non établie")
            print("Variables modifiées")
            for item in decision.modified_variables:
                print(f" • {item}")
            print("Protocole scientifique")
            print(decision.source_protocol_id or "non établi")
            print("Hypothèse scientifique")
            print(decision.source_hypothesis_code or "non établie")

        print()
        print("Prochaine action")
        print(decision.action)
        if decision.target is not None:
            print(f"Objet à modifier : {decision.target}.")
        if decision.direction is not None:
            print(f"Direction : {decision.direction}.")
        if decision.amplitude is not None:
            print(f"Amplitude : {decision.amplitude}.")
        if decision.tested_variable is not None:
            print(f"Variable testée : {decision.tested_variable}.")

        if decision.unchanged_items:
            print()
            print("À maintenir inchangé")
            for item in decision.unchanged_items:
                print(f" • {item}")

        if decision.required_measurements:
            print()
            print("Mesure suivante")
            print(
                " • Réalisez une nouvelle expérience REW : "
                + ", ".join(decision.required_measurements)
                + "."
            )
            print(" • Conservez la position du microphone et le volume.")
            print(" • Ne modifiez aucune autre variable.")
            if decision.positioning_proposal_id is not None:
                print(
                    " • Mesurez et consignez la position physique avant et après "
                    "le déplacement."
                )
            print(" • Enregistrez précisément l’unique modification réalisée.")
            if decision.positioning_proposal_id is not None:
                print(
                    " • Déclarez l’expérience contrôlée avant ou après l’acquisition."
                )

        if decision.action_reasons:
            print()
            print("Pourquoi")
            for item in decision.action_reasons:
                print(f" • {item}")

        if decision.unblock_steps:
            print()
            print("À faire avant de poursuivre")
            for item in decision.unblock_steps:
                print(f" • {item}")

        if decision.established_facts:
            print()
            print("Ce que l’on sait")
            for item in decision.established_facts:
                print(f" • {item}")

        print()
        print("Ce que l’on ne sait pas encore")
        for item in decision.active_limits:
            print(f" • {item}")
        print(" • L’origine causale exacte n’est pas établie.")

        print()
        print("Statut de confiance")
        print(f" • Verdict : {decision.verdict_confidence}.")
        print(f" • Action : {decision.action_confidence}.")
        print(
            " • Causalité : Non établi "
            f"({decision.causality_status})."
        )

    @staticmethod
    def _print_action_oriented_positioning(positioning):
        print()
        print("PROCHAINE ÉTAPE DE POSITIONNEMENT")
        print()
        print("Situation actuelle")
        print(positioning.situation)
        print()
        print("Niveau de certitude")
        print(positioning.certainty)

        if positioning.measured_facts:
            print()
            print("Faits mesurés qui soutiennent cette priorité")
            for fact in positioning.measured_facts:
                print(f" • {fact}")

        if positioning.possible_explanations:
            print()
            print("Explications possibles — à vérifier")
            for explanation in positioning.possible_explanations:
                print(f" • {explanation}")

        if positioning.previous_result is not None:
            print()
            print("Résultat du test précédent")
            print(positioning.previous_result)

        print()
        print("Action proposée")
        print(positioning.action)

        if positioning.target is not None:
            print(f"Objet concerné : {positioning.target}")
            print(
                "Direction : "
                + (
                    positioning.direction
                    if positioning.direction is not None
                    else "non déterminée par les données disponibles"
                )
            )
            print(
                "Amplitude : "
                + (
                    positioning.amplitude
                    if positioning.amplitude is not None
                    else "non déterminée par les données disponibles"
                )
            )

        if positioning.unchanged_items:
            print()
            print("Ne modifiez pas")
            for item in positioning.unchanged_items:
                print(f" • {item}")

        if positioning.required_measurements:
            print()
            print("Nouvelle mesure REW attendue")
            print(" • Créez une nouvelle expérience REW distincte.")
            print(
                " • Reprenez les mesures : "
                + ", ".join(positioning.required_measurements)
                + "."
            )
            print(" • Conservez le microphone et le volume strictement inchangés.")
            print(
                " • Mesurez et consignez la position physique avant et après "
                "le déplacement."
            )
            print(" • Notez précisément l’unique élément modifié.")
            print(
                " • Déclarez l’expérience contrôlée avant ou après l’acquisition."
            )
            print(" • Consultez le guide REW pour les détails d’acquisition et d’export.")

            print()
            print("Ce qu’AcousticBrain comparera")
            if positioning.comparison_criteria:
                for criterion in positioning.comparison_criteria:
                    print(
                        " • AcousticBrain vérifiera si ce test est associé à un "
                        f"changement mesurable concernant {criterion}."
                    )
            else:
                print(
                    " • AcousticBrain comparera uniquement les observables déjà "
                    "définis pour cette expérience."
                )

        if positioning.missing_information:
            print()
            print("Données encore nécessaires")
            for item in positioning.missing_information:
                print(f" • {item}")

        print()
        print("Limites")
        for limitation in positioning.limitations:
            print(f" • {limitation}")
        print(
            " • Statut scientifique conservé : "
            f"{positioning.causality_status}."
        )

    @staticmethod
    def _diagnostics_to_render(report):
        if report.diagnostic_priority is None:
            return [(diagnostic, False) for diagnostic in report.diagnostics]

        return [
            (item.diagnostic, item.is_secondary)
            for item in report.diagnostic_priority.prioritized_diagnostics
        ]

    @staticmethod
    def _print_historical_experiments(title, experiments):
        labels = {
            "UNKNOWN_DECLARATION": (
                "déclaration expérimentale historique non disponible"
            ),
            "DECLARATION_UNAVAILABLE": "statut de déclaration indisponible",
            "CONTROLLED_INTERVENTION": "déclarée CONTROLLED_INTERVENTION",
            "MEASUREMENT_REPEAT": "déclarée MEASUREMENT_REPEAT",
        }
        print(f"{title} :")
        if not experiments:
            print(" • aucune")
            return
        for item in experiments:
            label = labels.get(item.declaration_status, item.declaration_status)
            print(f" • {item.experiment_code} — {label}")

    @staticmethod
    def _print_material_coefficients(label, coefficients):
        if coefficients is None:
            print(f"{label}: unavailable")
            return
        if not coefficients:
            print(f"{label}: none")
            return
        print(
            f"{label}: "
            + ", ".join(
                f"{item.center_frequency_hz:g} Hz={item.coefficient:.3f}"
                for item in coefficients
            )
        )
