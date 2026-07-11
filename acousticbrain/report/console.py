from .report import Report


class ConsoleReporter:

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
            print()

            for domain in global_analysis.domains:
                domain_confidence = (
                    f"{domain.confidence:.1f}%"
                    if domain.confidence is not None
                    else "indisponible"
                )
                print(f" • Domaine {domain.code}")
                print(f"   Score : {domain.score:.1f} / 100")
                print(f"   Confiance : {domain_confidence}")
                print(f"   Provenance : {domain.source_analysis}")
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
            if diagnostic.score is not None:
                print(f"Score : {diagnostic.score:.0f} / 100")
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
