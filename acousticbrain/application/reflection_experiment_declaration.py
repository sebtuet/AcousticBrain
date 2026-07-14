from acousticbrain.models import (
    ControlledReflectionExperimentDeclaration,
    ControlledReflectionExperimentDeclarationRegistry,
    ControlledReflectionVerificationPlanningAnalysis,
    ReflectionDeclarationFieldProvenance,
    ReflectionDeclarationProvenanceSource,
    ReflectionExperimentConditionDeclaration,
    ReflectionExperimentDeclarationStatus,
    ReflectionExperimentMeasurementReference,
)
from acousticbrain.persistence import ControlledReflectionExperimentJsonRepository


class ControlledReflectionExperimentDeclarationService:
    """Records execution metadata without comparing or interpreting measurements."""

    def __init__(self, repository=None):
        self.repository = repository or ControlledReflectionExperimentJsonRepository()

    def declare(
        self,
        planning_analysis,
        *,
        proposal_id,
        status,
        declarer_id,
        reference_measurements=(),
        intervention_measurements=(),
        status_reason_code=None,
    ):
        if not isinstance(
            planning_analysis,
            ControlledReflectionVerificationPlanningAnalysis,
        ):
            raise ValueError("Reflection declaration requires PR-036 planning analysis.")
        proposal = next(
            (
                item for item in planning_analysis.proposals
                if item.proposal_id == proposal_id
            ),
            None,
        )
        if proposal is None:
            raise ValueError("Reflection declaration requires an existing proposal.")
        if not isinstance(status, ReflectionExperimentDeclarationStatus):
            raise ValueError("Reflection declaration status is invalid.")
        if not isinstance(declarer_id, str) or not declarer_id.strip():
            raise ValueError("Reflection declaration requires a declarer id.")
        declaration_id = f"reflection_experiment_declaration.{proposal_id}"
        reference = self._condition(
            proposal.reference_condition_code,
            tuple(reference_measurements),
            proposal_id,
            declarer_id,
        )
        intervention = self._condition(
            proposal.intervention_condition_code,
            tuple(intervention_measurements),
            proposal_id,
            declarer_id,
        )
        provenance = [
            self._provenance(
                "declaration_id",
                ReflectionDeclarationProvenanceSource.SYSTEM_DERIVED,
                proposal_id,
                "DECLARATION_ID_DERIVED_FROM_PROPOSAL",
            ),
            self._provenance(
                "proposal_id",
                ReflectionDeclarationProvenanceSource.UPSTREAM_ANALYSIS,
                proposal_id,
                "CONTROLLED_REFLECTION_VERIFICATION_PROPOSAL",
            ),
            self._provenance(
                "status",
                ReflectionDeclarationProvenanceSource.USER_DECLARATION,
                declarer_id,
                "EXPLICIT_DECLARATION_STATUS",
            ),
            self._provenance(
                "reference_condition",
                ReflectionDeclarationProvenanceSource.UPSTREAM_ANALYSIS,
                proposal_id,
                "PR036_REFERENCE_CONDITION",
            ),
            self._provenance(
                "intervention_condition",
                ReflectionDeclarationProvenanceSource.UPSTREAM_ANALYSIS,
                proposal_id,
                "PR036_INTERVENTION_CONDITION",
            ),
        ]
        if status_reason_code is not None:
            provenance.append(self._provenance(
                "status_reason_code",
                ReflectionDeclarationProvenanceSource.USER_DECLARATION,
                declarer_id,
                "EXPLICIT_DECLARATION_STATUS_REASON",
            ))
        return ControlledReflectionExperimentDeclaration(
            declaration_id=declaration_id,
            proposal_id=proposal_id,
            status=status,
            reference_condition=reference,
            intervention_condition=intervention,
            status_reason_code=status_reason_code,
            field_provenance=tuple(
                sorted(provenance, key=lambda item: item.field_code)
            ),
        )

    @classmethod
    def measurement_reference(
        cls,
        *,
        reference_id,
        experiment_id,
        measurement_name,
        manifest_id,
        content_hash=None,
    ):
        values = (reference_id, experiment_id, measurement_name, manifest_id)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Measurement manifest references require identifiers.")
        fields = ["reference_id", "experiment_id", "measurement_name"]
        if content_hash is not None:
            fields.append("content_hash")
        return ReflectionExperimentMeasurementReference(
            reference_id=reference_id,
            experiment_id=experiment_id,
            measurement_name=measurement_name,
            content_hash=content_hash,
            field_provenance=tuple(sorted(
                (
                    cls._provenance(
                        field,
                        ReflectionDeclarationProvenanceSource.MEASUREMENT_MANIFEST,
                        manifest_id,
                        f"MEASUREMENT_MANIFEST_{field.upper()}",
                    )
                    for field in fields
                ),
                key=lambda item: item.field_code,
            )),
        )

    def save(self, path, declarations):
        registry = ControlledReflectionExperimentDeclarationRegistry(
            declarations=tuple(declarations)
        )
        self.repository.save(path, registry)
        return registry

    def load(self, path):
        return self.repository.load(path)

    def load_into_project(self, project, path):
        registry = self.load(path)
        project.controlled_reflection_experiment_declarations = (
            registry.declarations
        )
        return registry

    @classmethod
    def _condition(cls, code, measurements, proposal_id, declarer_id):
        return ReflectionExperimentConditionDeclaration(
            condition_code=code,
            measurement_references=tuple(sorted(
                measurements,
                key=lambda item: item.reference_id,
            )),
            field_provenance=tuple(sorted((
                cls._provenance(
                    "condition_code",
                    ReflectionDeclarationProvenanceSource.UPSTREAM_ANALYSIS,
                    proposal_id,
                    "PR036_CONDITION_CODE",
                ),
                cls._provenance(
                    "measurement_references",
                    ReflectionDeclarationProvenanceSource.USER_DECLARATION,
                    declarer_id,
                    "EXPLICIT_MEASUREMENT_REFERENCE_SET",
                ),
            ), key=lambda item: item.field_code)),
        )

    @staticmethod
    def _provenance(field, source, source_id, code):
        return ReflectionDeclarationFieldProvenance(
            field_code=field,
            source=source,
            source_id=source_id,
            provenance_codes=(code,),
        )
