from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedReflectionDeclarationFieldProvenance:
    field_code: str
    source: str
    source_id: str
    provenance_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedReflectionExperimentMeasurementReference:
    reference_id: str
    experiment_id: str
    measurement_name: str
    content_hash: str | None
    field_provenance: tuple[PresentedReflectionDeclarationFieldProvenance, ...]


@dataclass(frozen=True)
class PresentedReflectionExperimentConditionDeclaration:
    condition_code: str
    measurement_references: tuple[
        PresentedReflectionExperimentMeasurementReference, ...
    ]
    field_provenance: tuple[PresentedReflectionDeclarationFieldProvenance, ...]


@dataclass(frozen=True)
class PresentedControlledReflectionExperimentDeclaration:
    declaration_id: str
    proposal_id: str
    status: str
    reference_condition: PresentedReflectionExperimentConditionDeclaration
    intervention_condition: PresentedReflectionExperimentConditionDeclaration
    status_reason_code: str | None
    field_provenance: tuple[PresentedReflectionDeclarationFieldProvenance, ...]


class ControlledReflectionExperimentDeclarationPresenter:
    """Presents persisted declarations without comparing their measurements."""

    def present(self, context):
        declarations = context.controlled_reflection_experiment_declarations
        if not declarations:
            return ()
        return tuple(self._declaration(item) for item in declarations)

    @classmethod
    def _declaration(cls, item):
        return PresentedControlledReflectionExperimentDeclaration(
            declaration_id=item.declaration_id,
            proposal_id=item.proposal_id,
            status=item.status.value,
            reference_condition=cls._condition(item.reference_condition),
            intervention_condition=cls._condition(item.intervention_condition),
            status_reason_code=item.status_reason_code,
            field_provenance=cls._provenance(item.field_provenance),
        )

    @classmethod
    def _condition(cls, item):
        return PresentedReflectionExperimentConditionDeclaration(
            condition_code=item.condition_code,
            measurement_references=tuple(
                PresentedReflectionExperimentMeasurementReference(
                    reference_id=reference.reference_id,
                    experiment_id=reference.experiment_id,
                    measurement_name=reference.measurement_name,
                    content_hash=reference.content_hash,
                    field_provenance=cls._provenance(
                        reference.field_provenance
                    ),
                )
                for reference in item.measurement_references
            ),
            field_provenance=cls._provenance(item.field_provenance),
        )

    @staticmethod
    def _provenance(values):
        return tuple(
            PresentedReflectionDeclarationFieldProvenance(
                field_code=item.field_code,
                source=item.source.value,
                source_id=item.source_id,
                provenance_codes=item.provenance_codes,
            )
            for item in values
        )
