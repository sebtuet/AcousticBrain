from acousticbrain.models import (
    CampaignReferenceAssertionStatus,
    CampaignReferenceCriterionStatus,
    CampaignReferenceDeclarationStatus,
    CampaignReferenceQualification,
    CampaignReferenceQualificationStatus,
    ComparisonEligibilityStatus,
    ExperimentKind,
    ExperimentState,
    ListeningPositionCampaignInstanceStatus,
    REQUIRED_POSITION_MEASUREMENTS,
)


class CampaignReferenceQualificationBuilder:
    """Validates an explicit reference declaration against observed facts."""

    def build(self, context):
        declaration_analysis = getattr(
            context, "campaign_reference_qualification_declaration_analysis", None
        )
        instance_analysis = getattr(
            context, "listening_position_campaign_instance_analysis", None
        )
        if declaration_analysis is None and instance_analysis is None:
            return None
        if declaration_analysis is None:
            return self._result(
                status=CampaignReferenceQualificationStatus.BLOCKED,
                reasons=("CAMPAIGN_REFERENCE_DECLARATION_UNAVAILABLE",),
                missing=("campaign_reference.qualification_declaration",),
            )
        if (
            declaration_analysis.status
            is CampaignReferenceDeclarationStatus.INVALID
        ):
            return self._result(
                status=CampaignReferenceQualificationStatus.INVALID,
                reasons=declaration_analysis.blocking_reasons,
                missing=("campaign_reference.valid_declaration",),
                source_path=declaration_analysis.source_path,
            )

        declaration = declaration_analysis.declaration
        protocol = getattr(context, "listening_position_sampling_protocol", None)
        instance = (
            instance_analysis.instance
            if instance_analysis is not None
            and instance_analysis.status
            is ListeningPositionCampaignInstanceStatus.VALID
            else None
        )
        descriptors = {
            item.experiment_id: item
            for item in getattr(context, "experiment_descriptors", ())
        }
        descriptor = descriptors.get(declaration.experiment_id)
        comparison = getattr(context, "experiment_comparison_analysis", None)
        sequence = getattr(comparison, "sequence", None)
        comparable = {
            item.after_experiment_id
            for item in getattr(sequence, "local_comparisons", ())
            if item.eligibility is ComparisonEligibilityStatus.COMPARABLE
        }

        reasons = []
        supporting = ["campaign_reference.user_declaration.valid"]
        contradicting = []
        missing = []

        protocol_status = CampaignReferenceCriterionStatus.SATISFIED
        if (
            protocol is None
            or declaration.intended_protocol_id != protocol.protocol_id
            or declaration.intended_protocol_version != protocol.version
        ):
            reasons.append("CAMPAIGN_REFERENCE_PROTOCOL_MISMATCH")
            contradicting.append("campaign_reference.protocol_mismatch")
            protocol_status = CampaignReferenceCriterionStatus.BLOCKED
        else:
            supporting.append("campaign_reference.protocol_compatible")

        instance_status = CampaignReferenceCriterionStatus.SATISFIED
        if instance is None:
            reasons.append("CAMPAIGN_REFERENCE_INSTANCE_MISMATCH")
            missing.append("campaign_reference.valid_campaign_instance")
            instance_status = CampaignReferenceCriterionStatus.BLOCKED
        elif (
            declaration.experiment_id != instance.reference_experiment_id
            or (
                declaration.intended_campaign_instance_id is not None
                and declaration.intended_campaign_instance_id
                != instance.instance_id
            )
        ):
            reasons.append("CAMPAIGN_REFERENCE_INSTANCE_MISMATCH")
            contradicting.append("campaign_reference.instance_mismatch")
            instance_status = CampaignReferenceCriterionStatus.BLOCKED
        else:
            supporting.append("campaign_reference.instance_compatible")

        if declaration.reference_role != "REFERENCE":
            reasons.append("CAMPAIGN_REFERENCE_DECLARATION_INVALID")
            contradicting.append("campaign_reference.role_not_reference")

        measurements_status = CampaignReferenceCriterionStatus.SATISFIED
        if descriptor is None:
            reasons.append("CAMPAIGN_REFERENCE_EXPERIMENT_NOT_FOUND")
            missing.append("campaign_reference.experiment_descriptor")
            measurements_status = CampaignReferenceCriterionStatus.BLOCKED
        else:
            supporting.append("campaign_reference.experiment_exists")
            if descriptor.state is not ExperimentState.READY:
                reasons.append("CAMPAIGN_REFERENCE_EXPERIMENT_NOT_READY")
                contradicting.append("campaign_reference.experiment_not_ready")
            else:
                supporting.append("campaign_reference.experiment_ready")
            channels = {
                getattr(item, "value", str(item))
                for item in descriptor.available_channels
            }
            declared_measurements = declaration.required_measurement_assertions
            if (
                declared_measurements != REQUIRED_POSITION_MEASUREMENTS
                or not set(REQUIRED_POSITION_MEASUREMENTS).issubset(channels)
            ):
                reasons.append("CAMPAIGN_REFERENCE_MEASUREMENTS_INCOMPLETE")
                missing.extend(
                    f"campaign_reference.measurement.{code}"
                    for code in REQUIRED_POSITION_MEASUREMENTS
                    if code not in channels or code not in declared_measurements
                )
                if any(code not in channels for code in declared_measurements):
                    contradicting.append(
                        "campaign_reference.measurement_assertion_contradicted"
                    )
                measurements_status = CampaignReferenceCriterionStatus.BLOCKED
            else:
                supporting.append("campaign_reference.measurements_available")

            historical = descriptor.experiment_declaration
            if historical.experiment_kind is ExperimentKind.UNKNOWN:
                reasons.append("CAMPAIGN_REFERENCE_DECLARATION_UNKNOWN")
                missing.append("campaign_reference.historical_declaration")
            else:
                supporting.append(
                    "campaign_reference.historical_declaration_structured"
                )
            if descriptor.experiment_id not in comparable:
                reasons.append("CAMPAIGN_REFERENCE_COMPARABILITY_UNAVAILABLE")
                missing.append("campaign_reference.local_comparison_comparable")
            else:
                supporting.append("campaign_reference.local_comparison_comparable")

        controls_status = CampaignReferenceCriterionStatus.SATISFIED
        assertions = dict(declaration.controlled_variable_assertions)
        required_controls = tuple(
            getattr(protocol, "controlled_variables", ())
        )
        if not set(required_controls).issubset(assertions):
            reasons.append("CAMPAIGN_REFERENCE_CONFIGURATION_INCOMPLETE")
            missing.extend(
                f"campaign_reference.configuration.{code}"
                for code in required_controls
                if code not in assertions
            )
            controls_status = CampaignReferenceCriterionStatus.BLOCKED

        historical_facts = set()
        if descriptor is not None:
            historical = descriptor.experiment_declaration
            historical_facts.update(historical.modified_variables)
            historical_facts.update(historical.controlled_variables)
        qualified_controls = []
        for code in required_controls:
            status = assertions.get(code)
            if status is CampaignReferenceAssertionStatus.KNOWN:
                qualified_controls.append(code)
                supporting.append(
                    f"campaign_reference.user_assertion.{code}.known"
                )
                if code in historical_facts:
                    supporting.append(
                        f"campaign_reference.historical_fact.{code}"
                    )
            elif status is None or status is CampaignReferenceAssertionStatus.UNKNOWN:
                reasons.append("CAMPAIGN_REFERENCE_CONFIGURATION_INCOMPLETE")
                missing.append(f"campaign_reference.configuration.{code}.known")
                controls_status = CampaignReferenceCriterionStatus.BLOCKED
                if code in historical_facts:
                    reasons.append("CAMPAIGN_REFERENCE_HISTORICAL_CONTRADICTION")
                    contradicting.append(
                        f"campaign_reference.assertion_conflicts_history.{code}"
                    )
            else:
                reasons.append("CAMPAIGN_REFERENCE_CONFIGURATION_INCOMPLETE")
                contradicting.append(
                    f"campaign_reference.required_variable_not_applicable.{code}"
                )
                controls_status = CampaignReferenceCriterionStatus.BLOCKED
                if code in historical_facts:
                    reasons.append("CAMPAIGN_REFERENCE_HISTORICAL_CONTRADICTION")

        for code, status in assertions.items():
            if code in required_controls:
                continue
            if status is CampaignReferenceAssertionStatus.KNOWN:
                supporting.append(
                    f"campaign_reference.user_assertion.{code}.known"
                )
                if code in historical_facts:
                    supporting.append(
                        f"campaign_reference.historical_fact.{code}"
                    )
            elif code in historical_facts:
                reasons.append("CAMPAIGN_REFERENCE_HISTORICAL_CONTRADICTION")
                contradicting.append(
                    f"campaign_reference.assertion_conflicts_history.{code}"
                )

        reasons = tuple(dict.fromkeys(reasons))
        supporting = tuple(dict.fromkeys(supporting))
        contradicting = tuple(dict.fromkeys(contradicting))
        missing = tuple(dict.fromkeys(missing))
        status = (
            CampaignReferenceQualificationStatus.QUALIFIED
            if not reasons
            else CampaignReferenceQualificationStatus.BLOCKED
        )
        return self._result(
            declaration=declaration,
            status=status,
            reasons=reasons,
            supporting=supporting,
            contradicting=contradicting,
            missing=missing,
            measurements_status=measurements_status,
            controls_status=controls_status,
            protocol_status=protocol_status,
            instance_status=instance_status,
            qualified_controls=tuple(qualified_controls),
            source_path=declaration_analysis.source_path,
        )

    @staticmethod
    def _result(
        *,
        status,
        reasons,
        declaration=None,
        supporting=(),
        contradicting=(),
        missing=(),
        measurements_status=CampaignReferenceCriterionStatus.NOT_APPLICABLE,
        controls_status=CampaignReferenceCriterionStatus.NOT_APPLICABLE,
        protocol_status=CampaignReferenceCriterionStatus.NOT_APPLICABLE,
        instance_status=CampaignReferenceCriterionStatus.NOT_APPLICABLE,
        qualified_controls=(),
        source_path=None,
    ):
        return CampaignReferenceQualification(
            qualification_id=(
                declaration.qualification_id if declaration is not None else None
            ),
            experiment_id=(
                declaration.experiment_id if declaration is not None else None
            ),
            intended_protocol_id=(
                declaration.intended_protocol_id if declaration is not None else None
            ),
            intended_protocol_version=(
                declaration.intended_protocol_version
                if declaration is not None
                else None
            ),
            intended_campaign_instance_id=(
                declaration.intended_campaign_instance_id
                if declaration is not None
                else None
            ),
            reference_role=(
                declaration.reference_role if declaration is not None else None
            ),
            status=status,
            supporting_fact_codes=tuple(supporting),
            contradicting_fact_codes=tuple(contradicting),
            missing_fact_codes=tuple(missing),
            blocking_reasons=tuple(reasons),
            required_measurements_status=measurements_status,
            controlled_variables_status=controls_status,
            protocol_compatibility_status=protocol_status,
            campaign_instance_compatibility_status=instance_status,
            qualified_controlled_variables=tuple(qualified_controls),
            required_measurements=(
                declaration.required_measurement_assertions
                if declaration is not None
                else ()
            ),
            causality_status="NOT_ESTABLISHED",
            source_path=source_path,
        )
