from .report import Report


class ConsoleReporter:

    def print(self, report: Report):

        print()
        print("=" * 60)
        print("ACOUSTICBRAIN REPORT")
        print("=" * 60)
        print()

        print(f"Projet : {report.project_name}")
        print()

        for diagnostic in report.diagnostics:

            print("-" * 60)

            print(diagnostic.title)
            print()

            print(diagnostic.message)
            print()

            print(f"Gravité : {diagnostic.severity}")
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