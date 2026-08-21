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

        self._print_repeated_capture_notice(report)
        self._print_repeatability(report)
        self._print_repeatability_evaluation(report)

        if positioning.status == "ACTION_AVAILABLE":
            self._print_available_action(report, positioning)
        else:
            self._print_blocked_action(report, positioning)

        print()
        print("Frontière scientifique")
        limitations = positioning.limitations
        if self._repeated_captures(report):
            limitations = tuple(
                item for item in limitations
                if item != "Une nouvelle mesure est nécessaire."
            )
        for limitation in limitations:
            print(f"- {limitation}")
        print(f"- Causality status: {positioning.causality_status}")
        print("- Cette vue ne déclare ni n’exécute aucune expérience.")
        print("=" * 60)

    @staticmethod
    def _print_repeated_capture_notice(report):
        repeated = SpeakerPlacementHomeConsoleReporter._repeated_captures(report)
        if not repeated:
            return
        print()
        print("Acquisition contrôlée enregistrée")
        for item in repeated:
            print(f"- {item.experiment_id} : acquisitions LEFT/RIGHT présentes.")
        print(
            "Les répétitions sont conservées sans être réduites à une seule "
            "réponse par canal. Aucun verdict acoustique de comparaison n’est "
            "produit."
        )

    @staticmethod
    def _repeated_captures(report):
        discovery = getattr(report, "experiments_discovered", None)
        experiments = getattr(discovery, "experiments", ())
        return tuple(
            item for item in experiments
            if (
                item.state == "READY"
                and {"LEFT", "RIGHT"}.issubset(item.available_channels)
                and item.source_evidence_acquisition_plan_id is not None
                and item.preserved_plan_objective is not None
            )
        )

    @staticmethod
    def _print_repeatability(report):
        values = getattr(report, "channel_isolation_repeatability", ())
        if not values:
            return
        print()
        value = values[-1]
        print("Dernier test contrôlé — répétabilité A/B")
        print(f"- {value.experiment_id}")
        SpeakerPlacementHomeConsoleReporter._print_difference(
            "Gauche", value.left_maximum_difference_db,
        )
        SpeakerPlacementHomeConsoleReporter._print_frequency(
            getattr(value, "left_maximum_difference_frequency_hz", None),
        )
        SpeakerPlacementHomeConsoleReporter._print_difference(
            "Droite", value.right_maximum_difference_db,
        )
        SpeakerPlacementHomeConsoleReporter._print_frequency(
            getattr(value, "right_maximum_difference_frequency_hz", None),
        )
        SpeakerPlacementHomeConsoleReporter._print_difference(
            "Écart gauche/droite", value.left_right_difference_maximum_change_db,
        )
        SpeakerPlacementHomeConsoleReporter._print_band_difference(
            "Gauche, 40–200 Hz",
            getattr(value, "left_40_200_maximum_difference_db", None),
            getattr(value, "left_40_200_maximum_difference_frequency_hz", None),
        )
        SpeakerPlacementHomeConsoleReporter._print_band_difference(
            "Droite, 40–200 Hz",
            getattr(value, "right_40_200_maximum_difference_db", None),
            getattr(value, "right_40_200_maximum_difference_frequency_hz", None),
        )
        print(
            "Ces écarts bruts décrivent les exports REW A/B ; aucun verdict "
            "acoustique ou causalité n’en est déduit. Une éventuelle évaluation "
            "numérique contractuelle est affichée séparément."
        )
        baseline_differences = getattr(value, "baseline_differences", ())
        if baseline_differences:
            reference = getattr(value, "reference_experiment_id", None)
            print(
                "Écart descriptif à la référence "
                f"{reference or 'indisponible'}"
            )
            for baseline in baseline_differences:
                print(f"  Répétition {baseline.label}")
                SpeakerPlacementHomeConsoleReporter._print_baseline_difference(
                    "Gauche", baseline.left_maximum_difference_db,
                )
                SpeakerPlacementHomeConsoleReporter._print_baseline_difference(
                    "Droite", baseline.right_maximum_difference_db,
                )
                SpeakerPlacementHomeConsoleReporter._print_baseline_difference(
                    "Écart gauche/droite",
                    baseline.left_right_difference_maximum_change_db,
                )
        if len(values) > 1:
            print(f"Historique conservé : {len(values) - 1} test(s) antérieur(s).")

    @staticmethod
    def _print_repeatability_evaluation(report):
        values = getattr(report, "channel_isolation_repeatability_evaluations", ())
        if not values:
            return
        value = values[-1]
        print()
        print("Évaluation numérique de répétabilité")
        print(f"- Contrat : {value.contract_id}")
        print(
            f"- Bande évaluée : {value.lower_hz:.0f}–{value.upper_hz:.0f} Hz ; "
            f"seuil : {value.threshold_db:.2f} dB."
        )
        SpeakerPlacementHomeConsoleReporter._print_band_difference(
            "Gauche",
            value.left_maximum_difference_db,
            value.left_maximum_difference_frequency_hz,
        )
        SpeakerPlacementHomeConsoleReporter._print_band_difference(
            "Droite",
            value.right_maximum_difference_db,
            value.right_maximum_difference_frequency_hz,
        )
        print(f"- Verdict : {value.status.value}")
        print(
            "Ce verdict décrit uniquement la cohérence numérique A/B dans cette "
            "bande ; il ne prouve pas la stabilité physique du microphone ou des "
            "enceintes."
        )
        print(
            "La position inchangée reste une déclaration utilisateur, non "
            "vérifiée indépendamment."
        )
        print(f"- Causality status: {value.causality_status}")

    @staticmethod
    def _print_baseline_difference(label, value):
        if value is None:
            print(f"    {label} : non comparable à la baseline.")
        else:
            print(f"    {label} : écart maximal à la baseline de {value:.2f} dB")

    @staticmethod
    def _print_difference(label, value):
        if value is None:
            print(f"  {label} : non comparable (grilles de fréquences différentes).")
        else:
            print(f"  {label} : écart maximal A/B de {value:.2f} dB")

    @staticmethod
    def _print_frequency(value):
        if value is not None:
            print(f"    Fréquence du maximum : {value:.2f} Hz")

    @staticmethod
    def _print_band_difference(label, value, frequency):
        if value is not None:
            print(f"  {label} : maximum A/B de {value:.2f} dB à {frequency:.2f} Hz")

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
        if self._repeated_captures(report):
            print(
                "Aucune nouvelle mesure n’est demandée. Les répétitions "
                "enregistrées restent disponibles pour une comparaison "
                "scientifique explicite ; cette vue ne choisit ni une répétition "
                "ni une conclusion acoustique à votre place."
            )
            return
        plan = self._recommended_plan(report)
        if plan is None:
            print(
                "Aucune action de positionnement ne peut être proposée tant "
                "qu’un contrat existant ne fournit pas une étape vérifiable."
            )
            return

        print("Démarrez la préparation du plan de vérification déjà sélectionné :")
        print(f"Plan : {plan.plan_id}")
        self._print_command(
            "python main.py",
            f"--measurements-root {self.measurements_root.resolve()}",
            "--start-placement",
        )
        print(
            "Cette étape vous demande de déclarer les prérequis connus ; elle "
            "ne déclare ni n’exécute une expérience."
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
