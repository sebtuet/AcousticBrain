from acousticbrain.models import (
    EvidenceAcquisitionTestType,
    ImpulseChannel,
    PlanCoverageResult,
    PlanCoverageStatus,
)


class ChannelIsolationPlanCoverageValidator:
    """Validates declared CHANNEL_ISOLATION structure without interpreting results."""

    _SUPPORTED_LIMITATION = (
        "Coverage validates declarations only; it does not validate execution, "
        "measurement content, results, success criteria, or causality."
    )
    _UNSUPPORTED_LIMITATION = (
        "Plan coverage validation supports CHANNEL_ISOLATION only."
    )

    def validate(self, experiment, resolved_plan):
        if resolved_plan is None:
            return self._result(
                PlanCoverageStatus.NOT_APPLICABLE,
                limitations=(
                    "Plan coverage requires an exactly resolved plan reference.",
                ),
            )
        if (
            getattr(resolved_plan, "test_type", None)
            is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION
        ):
            return self._result(
                PlanCoverageStatus.NOT_APPLICABLE,
                limitations=(self._UNSUPPORTED_LIMITATION,),
            )

        declaration = experiment.channel_isolation_declaration
        if declaration is None:
            return self._result(
                PlanCoverageStatus.INSUFFICIENT_DECLARATION,
                unverifiable=(
                    self._verifiable_requirements(resolved_plan)
                    | self._intrinsically_unverifiable(resolved_plan)
                ),
                limitations=(self._SUPPORTED_LIMITATION,),
            )

        declared = self._declared_requirements(experiment)
        required = self._verifiable_requirements(resolved_plan)
        covered = required & declared
        missing = required - declared
        if not missing:
            status = PlanCoverageStatus.COMPLETE
        elif covered:
            status = PlanCoverageStatus.PARTIAL
        else:
            status = PlanCoverageStatus.INSUFFICIENT_DECLARATION
        return self._result(
            status,
            covered=covered,
            missing=missing,
            unverifiable=self._intrinsically_unverifiable(resolved_plan),
            limitations=(self._SUPPORTED_LIMITATION,),
        )

    @staticmethod
    def _declared_requirements(experiment):
        values = {
            f"acquired_channel:{channel.value}"
            for channel in experiment.available_channels
            if channel in (ImpulseChannel.LEFT, ImpulseChannel.RIGHT)
        }
        declaration = experiment.channel_isolation_declaration
        if declaration is not None:
            values.update(
                f"repeated_channel:{channel.value}"
                for channel in declaration.repeated_channels
            )
            values.update(
                f"required_input:{value}"
                for value in declaration.available_inputs
            )
            values.update(
                f"measurement:{value}"
                for value in declaration.measurements
            )
            values.update(
                f"controlled_variable:{value}"
                for value in declaration.controlled_variables
            )
            values.update(
                f"independent_variable:{value}"
                for value in declaration.independent_variables
            )
        return frozenset(values)

    @staticmethod
    def _verifiable_requirements(plan):
        values = {
            "acquired_channel:LEFT",
            "acquired_channel:RIGHT",
            "repeated_channel:LEFT",
            "repeated_channel:RIGHT",
        }
        values.update(
            f"required_input:{value}" for value in plan.required_inputs
        )
        values.update(
            f"controlled_variable:{value}"
            for value in plan.controlled_variables
        )
        values.update(
            f"independent_variable:{value}"
            for value in plan.independent_variables
        )
        values.update(
            f"measurement:{value}"
            for value in plan.measurements_to_capture
        )
        return frozenset(values)

    @staticmethod
    def _intrinsically_unverifiable(plan):
        values = set()
        if plan.instructions:
            values.add("procedure_execution")
        if plan.expected_observations:
            values.add("expected_observation_results")
        return values

    @staticmethod
    def _result(
        status,
        *,
        covered=(),
        missing=(),
        unverifiable=(),
        limitations=(),
    ):
        return PlanCoverageResult(
            status=status,
            covered_requirements=tuple(sorted(covered)),
            missing_requirements=tuple(sorted(missing)),
            unverifiable_requirements=tuple(sorted(unverifiable)),
            limitations=tuple(sorted(limitations)),
        )
