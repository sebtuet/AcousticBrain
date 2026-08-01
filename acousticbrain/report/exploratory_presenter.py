from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedExploratoryAnalysis:
    status: str
    proposal_id: str | None
    reference_scope_id: str | None
    rule_version: int | None
    candidate_id: str | None
    target: str | None
    reference_experiment_id: str | None
    action_parameters: tuple[tuple[str, str], ...]
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    return_action: str | None
    feasibility_question: str | None
    limitations: tuple[str, ...]
    observable_fact_codes: tuple[str, ...]
    mode: str
    causality_status: str
    universal_optimum: str


@dataclass(frozen=True)
class PresentedExploratoryResult:
    proposal_id: str
    acoustic_outcome: str
    reference_stability: str
    robust_winner: bool
    next_step: str
    observed_fact_codes: tuple[str, ...]
    causality_status: str


class ExploratoryAnalysisPresenter:
    def present(self, context):
        analysis = getattr(context, "exploratory_analysis", None)
        proposal = getattr(analysis, "proposal", None)
        if proposal is None:
            return PresentedExploratoryAnalysis(
                status=analysis.status.value if analysis else "NO_ACTION_AVAILABLE",
                proposal_id=None, reference_scope_id=None, rule_version=None,
                candidate_id=None, target=None, action_parameters=(),
                reference_experiment_id=None, modified_variables=(),
                controlled_variables=(), required_measurements=(), return_action=None,
                feasibility_question=None, limitations=(), observable_fact_codes=(),
                mode="EXPLORATORY", causality_status="NOT_ESTABLISHED",
                universal_optimum="NOT_CLAIMED",
            )
        return PresentedExploratoryAnalysis(
            status=analysis.status.value,
            proposal_id=proposal.proposal_id,
            reference_scope_id=proposal.reference_scope_id,
            rule_version=proposal.rule_version,
            candidate_id=proposal.experiment.candidate_id,
            target=proposal.experiment.target,
            reference_experiment_id=(
                proposal.proposal_input.reference_experiment_id
            ),
            action_parameters=proposal.proposal_input.action_parameters,
            modified_variables=proposal.experiment.modified_variables,
            controlled_variables=proposal.experiment.controlled_variables,
            required_measurements=proposal.experiment.required_measurements,
            return_action=proposal.proposal_input.return_action,
            feasibility_question=proposal.proposal_input.feasibility_question,
            limitations=proposal.proposal_input.limitations,
            observable_fact_codes=proposal.observable_fact_codes,
            mode=proposal.mode,
            causality_status=proposal.causality_status,
            universal_optimum=proposal.universal_optimum,
        )


class ExploratoryResultPresenter:
    def present(self, result):
        if result is None:
            return None
        return PresentedExploratoryResult(
            proposal_id=result.proposal_id,
            acoustic_outcome=result.acoustic_outcome,
            reference_stability=result.reference_stability.value,
            robust_winner=result.robust_winner,
            next_step=result.next_step,
            observed_fact_codes=result.observed_fact_codes,
            causality_status=result.causality_status,
        )


class ExploratoryConsoleReporter:
    def print(self, report):
        value = report.exploratory_analysis
        result = report.exploratory_result
        print("MODE EXPLORATOIRE V1")
        print()
        print(f"Statut : {value.status}")
        print(f"Mode : {value.mode}")
        print(f"Causalité : {value.causality_status}")
        print(f"Optimum universel : {value.universal_optimum}")
        if result is not None:
            print()
            print("RÉSULTAT EXPLORATOIRE OBSERVÉ")
            print(f"Proposition : {result.proposal_id}")
            print(f"Résultat acoustique : {result.acoustic_outcome}")
            print(f"Stabilité de référence : {result.reference_stability}")
            print(f"Gagnant robuste : {'OUI' if result.robust_winner else 'NON'}")
            print(f"Étape suivante : {result.next_step}")
            print("Faits observés : " + ", ".join(result.observed_fact_codes))
            print(f"Causalité : {result.causality_status}")
        if value.proposal_id is None:
            print("Aucune action exploratoire exacte et réversible n’est disponible.")
            return
        print(f"Proposition : {value.proposal_id}")
        print(f"Périmètre de référence : {value.reference_scope_id}")
        print(f"Candidat : {value.candidate_id}")
        print(f"Cible : {value.target}")
        print("Paramètres : " + ", ".join(
            f"{key}={item}" for key, item in value.action_parameters
        ))
        print("Variables contrôlées : " + ", ".join(value.controlled_variables))
        print("Mesures requises : " + ", ".join(value.required_measurements))
        print(f"Retour à la référence : {value.return_action}")
        print("Faits comparés : " + ", ".join(value.observable_fact_codes))
        print("Limites : " + ", ".join(value.limitations))
        if value.status == "FEASIBILITY_REQUIRED":
            print()
            print(f"Question de faisabilité : {value.feasibility_question}")
