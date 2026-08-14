from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedCampaignReferenceQualification:
    status: str
    qualification_id: str | None
    experiment_id: str | None
    intended_protocol_id: str | None
    intended_protocol_version: int | None
    intended_campaign_instance_id: str | None
    reference_role: str | None
    supporting_fact_codes: tuple[str, ...]
    contradicting_fact_codes: tuple[str, ...]
    missing_fact_codes: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    required_measurements_status: str
    controlled_variables_status: str
    protocol_compatibility_status: str
    campaign_instance_compatibility_status: str
    qualified_controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    causality_status: str
    source_path: str | None

    def to_dict(self):
        value = asdict(self)
        value.pop("source_path", None)
        return value


class CampaignReferenceQualificationPresenter:
    def present(self, context):
        value = getattr(context, "campaign_reference_qualification", None)
        if value is None:
            return None
        return PresentedCampaignReferenceQualification(
            status=value.status.value,
            qualification_id=value.qualification_id,
            experiment_id=value.experiment_id,
            intended_protocol_id=value.intended_protocol_id,
            intended_protocol_version=value.intended_protocol_version,
            intended_campaign_instance_id=value.intended_campaign_instance_id,
            reference_role=value.reference_role,
            supporting_fact_codes=value.supporting_fact_codes,
            contradicting_fact_codes=value.contradicting_fact_codes,
            missing_fact_codes=value.missing_fact_codes,
            blocking_reasons=value.blocking_reasons,
            required_measurements_status=(
                value.required_measurements_status.value
            ),
            controlled_variables_status=value.controlled_variables_status.value,
            protocol_compatibility_status=(
                value.protocol_compatibility_status.value
            ),
            campaign_instance_compatibility_status=(
                value.campaign_instance_compatibility_status.value
            ),
            qualified_controlled_variables=(
                value.qualified_controlled_variables
            ),
            required_measurements=value.required_measurements,
            causality_status=value.causality_status,
            source_path=value.source_path,
        )
