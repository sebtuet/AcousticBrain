from dataclasses import dataclass

from acousticbrain.application.sbir_protocol_instance_view import (
    SBIRProtocolInstanceView,
)


@dataclass(frozen=True)
class PresentedSBIRProtocolInstanceView:
    protocol_instance_id: str
    provenance_lines: tuple[str, ...]
    decision_lines: tuple[str, ...]
    declaration_status: str
    execution_status: str
    scientific_boundary_lines: tuple[str, ...]
    causality_status: str


class SBIRProtocolInstanceViewPresenter:
    """Presents only the immutable fields already stored in the registry."""

    def present(self, view):
        if not isinstance(view, SBIRProtocolInstanceView):
            raise TypeError("SBIRProtocolInstanceView is required.")
        record = view.record
        input_value = record.protocol_instance_input
        return PresentedSBIRProtocolInstanceView(
            protocol_instance_id=input_value.protocol_instance_id,
            provenance_lines=(
                "Plan : " + record.source_plan_id,
                "Empreinte du plan : " + record.source_plan_contract_fingerprint,
                "Protocole : " + record.protocol_id,
                "Expérience de référence : " + record.reference_experiment_id,
                "Expérience déplacée : " + record.moved_experiment_id,
                "Candidat géométrique : " + record.geometry_candidate_id,
                "Proposition de déplacement : " + record.displacement_proposal_id,
            ),
            decision_lines=tuple(
                decision.value
                for decision in (
                    *record.resolution_decisions,
                    *record.compatibility_decisions,
                )
            ),
            declaration_status=view.declaration_status,
            execution_status=view.execution_status,
            scientific_boundary_lines=(
                "Cette vue relit uniquement le snapshot enregistré ; elle ne "
                "recalcule aucune compatibilité ni aucun candidat.",
                "Instance enregistrée ≠ expérience déclarée ; expérience "
                "déclarée ≠ expérience exécutée.",
                "Aucune causalité, correction permanente ou recommandation "
                "acoustique n’est établie.",
            ),
            causality_status=view.causality_status,
        )


class SBIRProtocolInstanceViewConsoleReporter:
    def print(self, view):
        print("SBIR PROTOCOL INSTANCE VIEW — " + view.protocol_instance_id)
        print()
        print("Provenance enregistrée")
        print("\n".join(view.provenance_lines))
        print()
        print("Décisions enregistrées")
        print("\n".join(view.decision_lines))
        print()
        print("Statut")
        print("Déclaration : " + view.declaration_status)
        print("Exécution : " + view.execution_status)
        print()
        print("Frontière scientifique")
        print("\n".join(view.scientific_boundary_lines))
        print("Causality status: " + view.causality_status)
