from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedListeningPositionCampaignInstance:
    status: str
    instance_id: str | None
    protocol_id: str | None
    protocol_version: int | None
    reference_experiment_id: str | None
    position_codes: tuple[str, ...]
    comparability_rule: str | None
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    declaration_source: str | None
    declaration_version: int | None
    notes: str | None
    blocking_reasons: tuple[str, ...]
    validation_messages: tuple[str, ...]
    source_path: str | None

    def to_dict(self):
        value = asdict(self)
        value.pop("source_path", None)
        return value


class ListeningPositionCampaignInstancePresenter:
    def present(self, context):
        analysis = getattr(
            context, "listening_position_campaign_instance_analysis", None
        )
        if analysis is None:
            return None
        instance = analysis.instance
        return PresentedListeningPositionCampaignInstance(
            status=analysis.status.value,
            instance_id=instance.instance_id if instance is not None else None,
            protocol_id=instance.protocol_id if instance is not None else None,
            protocol_version=(
                instance.protocol_version if instance is not None else None
            ),
            reference_experiment_id=(
                instance.reference_experiment_id if instance is not None else None
            ),
            position_codes=(
                tuple(item.position_code for item in instance.positions)
                if instance is not None
                else ()
            ),
            comparability_rule=(
                instance.comparability_rule if instance is not None else None
            ),
            controlled_variables=(
                instance.controlled_variables if instance is not None else ()
            ),
            required_measurements=(
                instance.required_measurements if instance is not None else ()
            ),
            declaration_source=(
                instance.declaration_source if instance is not None else None
            ),
            declaration_version=(
                instance.declaration_version if instance is not None else None
            ),
            notes=instance.notes if instance is not None else None,
            blocking_reasons=analysis.blocking_reasons,
            validation_messages=analysis.validation_messages,
            source_path=analysis.source_path,
        )
