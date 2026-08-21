from pathlib import Path

from .action_oriented_positioning_presenter import ActionOrientedPositioningPresenter


class SpeakerPlacementHomeConsoleReporter:
    """Renders the public placement homepage from existing report objects only."""

    def __init__(self, *, measurements_root, positioning_presenter=None):
        self.measurements_root = Path(measurements_root)
        self.positioning_presenter = (
            positioning_presenter or ActionOrientedPositioningPresenter()
        )

    def print(self, report):
        positioning = self.positioning_presenter.present(report)

        print("=" * 60)
        print("ACOUSTICBRAIN — PLACEMENT DES ENCEINTES")
        print("=" * 60)
        print()
        print("Puis-je déplacer une enceinte maintenant ?")
        if positioning.status == "ACTION_AVAILABLE":
            print(
                "Oui, un test réversible est disponible. Il ne constitue ni une "
                "correction établie ni une amélioration prédite."
            )
        else:
            print(
                "Pas encore. Aucun déplacement unique n’est actuellement justifié "
                "par les données disponibles."
            )

        print()
        print("Pourquoi")
        print(positioning.action)

        if positioning.measured_facts:
            print()
            print("Ce qui est mesuré")
            for fact in positioning.measured_facts:
                print(f"- {fact}")

        if positioning.status == "ACTION_AVAILABLE":
            self._print_available_action(report, positioning)
        else:
            self._print_blocked_action(report, positioning)

        print()
        print("Frontière scientifique")
        for limitation in positioning.limitations:
            print(f"- {limitation}")
        print(f"- Causality status: {positioning.causality_status}")
        print("- Cette vue ne déclare ni n’exécute aucune expérience.")
        print("=" * 60)

    def _print_available_action(self, report, positioning):
        print()
        print("Test réversible disponible")
        print(f"Enceinte concernée : {positioning.target}")
        print(f"Direction : {positioning.direction}")
        print(f"Amplitude : {positioning.amplitude}")

        proposal = getattr(
            getattr(report, "loudspeaker_positioning_experiment", None),
            "proposal",
            None,
        )
        proposal_id = getattr(proposal, "proposal_id", None)
        if proposal_id is None:
            return

        print()
        print("Prochaine étape")
        print(
            "Déclarez volontairement ce test avant toute acquisition ; cette "
            "commande ne l’exécute pas."
        )
        self._print_command(
            "python main.py",
            f"--measurements-root {self.measurements_root.resolve()}",
            f"--accept-positioning-proposal {proposal_id}",
            "--positioning-experiment-id <NOUVEL_EXPERIMENT_ID>",
            "--positioning-reference <EXPERIENCE_REFERENCE>",
        )

    def _print_blocked_action(self, report, positioning):
        print()
        print("Prochaine étape")
        plan = self._recommended_plan(report)
        if plan is None:
            print(
                "Aucune action de positionnement ne peut être proposée tant "
                "qu’un contrat existant ne fournit pas une étape vérifiable."
            )
            return

        print("Ouvrez le parcours guidé du plan de vérification déjà sélectionné :")
        print(f"Plan : {plan.plan_id}")
        self._print_command(
            "python main.py",
            f"--measurements-root {self.measurements_root.resolve()}",
            "--guided-status",
        )
        print(
            "Cette étape examine le plan existant ; elle ne déclare ni "
            "n’exécute une expérience."
        )

        if positioning.missing_information:
            print()
            print("Information encore nécessaire")
            for item in positioning.missing_information:
                print(f"- {item}")

    @staticmethod
    def _print_command(*arguments):
        print((" " + chr(92) + "\n  ").join(arguments))

    @staticmethod
    def _recommended_plan(report):
        plans = getattr(report, "evidence_acquisition_plans", None)
        return getattr(plans, "recommended_plan", None)
