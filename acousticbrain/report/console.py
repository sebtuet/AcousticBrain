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

        print()

        print()

        if report.recommendations:

            print("Recommandations structurées")
            print()

            for recommendation in report.recommendations:
                print(f" • {recommendation.code}")
                print(f"   Action : {recommendation.action}")
                print(f"   Cible : {recommendation.target}")
                print(f"   Priorité : {recommendation.priority.name}")
                print(f"   Confiance : {recommendation.confidence}%")
                print(
                    "   Provenance : "
                    + ", ".join(recommendation.source_analyses)
                )

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

            if self.detailed_traceability and traceability.links:
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

    @staticmethod
    def _diagnostics_to_render(report):
        if report.diagnostic_priority is None:
            return [(diagnostic, False) for diagnostic in report.diagnostics]

        return [
            (item.diagnostic, item.is_secondary)
            for item in report.diagnostic_priority.prioritized_diagnostics
        ]
