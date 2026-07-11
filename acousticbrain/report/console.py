from .report import Report


class ConsoleReporter:

    def print(self, report: Report):

        print()
        print("=" * 60)
        print("ACOUSTICBRAIN REPORT")
        print("=" * 60)
        print()

        print(f"Projet : {report.project_name}")
        if hasattr(report, "room_properties"):

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

        traceability = report.traceability_analysis
        if traceability is not None:

            print("Traçabilité")
            print()
            print(
                "Analyses sources : "
                + (", ".join(traceability.source_analyses) or "aucune")
            )
            print()

            for evidence in traceability.evidence_references:
                print(f" • Preuve {evidence.code}")
                print(f"   Fait : {evidence.fact_code}")
                print(f"   Analyse : {evidence.source_analysis}")
                print(f"   Niveau : {evidence.evidence_level}")
                if evidence.value is not None:
                    print(f"   Valeur : {evidence.value}")

            if traceability.evidence_references:
                print()

            for link in traceability.links:
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

            if traceability.links:
                print()

        for diagnostic in report.diagnostics:

            print("-" * 60)

            print(diagnostic.title)
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
