from .report import Report


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
                print(
                    "   Observations : "
                    + (", ".join(step.observation_codes) or "aucune")
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
            for trajectory in causal.compatible_trajectories:
                print(
                    f" • {trajectory.trajectory_code} — support "
                    f"{trajectory.support_score:.1f} / 100"
                )
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

        if comparison_analysis is None and causal is None:
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
                if recommendation.status.name == "DEFERRED":
                    print("   Statut : DEFERRED")
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
                    print(
                        "   Références d'action : "
                        + ", ".join(domain.recommendation_codes)
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

        planning = report.experiment_planning
        if planning is not None:
            print("PROCHAINE EXPÉRIENCE RECOMMANDÉE")
            print()
            print(f"Statut : {planning.status}")
            candidate = planning.recommended_candidate
            if candidate is None:
                print("Code : aucune")
            else:
                print(f"Code : {candidate.candidate_id}")
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
        print(f"Expérience {comparison.after_experiment_id}")
        print(f"Avant : {comparison.before_experiment_id}")
        print(f"Après : {comparison.after_experiment_id}")
        print(f"Comparabilité : {comparison.eligibility}")
        if comparison.ineligibility_reasons:
            print("Raisons : " + ", ".join(comparison.ineligibility_reasons))
        print(f"Protocole : {comparison.source_protocol_id or 'non déclaré'}")
        print(f"Hypothèse : {comparison.source_hypothesis_code or 'non déclarée'}")
        print(f"Évolution : {comparison.outcome}")
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
    def _diagnostics_to_render(report):
        if report.diagnostic_priority is None:
            return [(diagnostic, False) for diagnostic in report.diagnostics]

        return [
            (item.diagnostic, item.is_secondary)
            for item in report.diagnostic_priority.prioritized_diagnostics
        ]
