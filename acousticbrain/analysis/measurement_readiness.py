from dataclasses import dataclass
from statistics import fmean

from acousticbrain.models import (
    AnalysisReadiness,
    ImpulseChannel,
    MeasurementAnalysisFamily,
    MeasurementQualityAnalysis,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementReadinessAnalysis,
    MeasurementReadinessStatus,
)


@dataclass(frozen=True)
class _ReadinessPolicy:
    family: MeasurementAnalysisFamily
    required_channels: tuple[ImpulseChannel, ...]
    channel_blockers: frozenset[MeasurementQualityIssueCode]
    reservations: frozenset[MeasurementQualityIssueCode]
    global_blockers: frozenset[MeasurementQualityIssueCode] = frozenset()


class MeasurementReadinessEngine:
    """Décide l'exploitabilité sans exécuter ni arrêter une analyse."""

    COMMON_RESERVATIONS = frozenset(
        {
            MeasurementQualityIssueCode.CLIPPING_DETECTED,
            MeasurementQualityIssueCode.LOW_SIGNAL_LEVEL,
            MeasurementQualityIssueCode.HIGH_NOISE_FLOOR,
            MeasurementQualityIssueCode.INSUFFICIENT_DYNAMIC_RANGE,
            MeasurementQualityIssueCode.CHANNEL_SAMPLE_RATE_MISMATCH,
            MeasurementQualityIssueCode.CHANNEL_LENGTH_MISMATCH,
            MeasurementQualityIssueCode.CHANNEL_TIMING_MISMATCH,
            MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
        }
    )

    POLICIES = (
        _ReadinessPolicy(
            MeasurementAnalysisFamily.FREQUENCY,
            (),
            frozenset(
                {MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA}
            ),
            COMMON_RESERVATIONS,
        ),
        _ReadinessPolicy(
            MeasurementAnalysisFamily.RT60,
            (),
            frozenset(
                {
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    MeasurementQualityIssueCode.INSUFFICIENT_IR_DURATION,
                    MeasurementQualityIssueCode.INSUFFICIENT_DYNAMIC_RANGE,
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                }
            ),
            COMMON_RESERVATIONS,
        ),
        _ReadinessPolicy(
            MeasurementAnalysisFamily.ETC,
            (),
            frozenset(
                {
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                }
            ),
            COMMON_RESERVATIONS
            | {MeasurementQualityIssueCode.INSUFFICIENT_IR_DURATION},
        ),
        _ReadinessPolicy(
            MeasurementAnalysisFamily.CLARITY,
            (),
            frozenset(
                {
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    MeasurementQualityIssueCode.INSUFFICIENT_IR_DURATION,
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                }
            ),
            COMMON_RESERVATIONS,
        ),
        _ReadinessPolicy(
            MeasurementAnalysisFamily.SPATIAL,
            (ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
            frozenset(
                {
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                }
            ),
            COMMON_RESERVATIONS,
            frozenset(
                {
                    MeasurementQualityIssueCode.CHANNEL_SAMPLE_RATE_MISMATCH,
                    MeasurementQualityIssueCode.CHANNEL_TIMING_MISMATCH,
                }
            ),
        ),
        _ReadinessPolicy(
            MeasurementAnalysisFamily.DIRECT_REVERBERANT,
            (),
            frozenset(
                {
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    MeasurementQualityIssueCode.INSUFFICIENT_IR_DURATION,
                    MeasurementQualityIssueCode.INSUFFICIENT_DYNAMIC_RANGE,
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                }
            ),
            COMMON_RESERVATIONS,
        ),
        _ReadinessPolicy(
            MeasurementAnalysisFamily.BASS_DECAY,
            (),
            frozenset(
                {
                    MeasurementQualityIssueCode.INVALID_DIRECT_PEAK,
                    MeasurementQualityIssueCode.HIGH_NOISE_FLOOR,
                    MeasurementQualityIssueCode.INSUFFICIENT_DYNAMIC_RANGE,
                    MeasurementQualityIssueCode.INSUFFICIENT_IR_DURATION,
                    MeasurementQualityIssueCode.INCONSISTENT_MEASUREMENT_METADATA,
                }
            ),
            COMMON_RESERVATIONS,
        ),
    )

    def analyze(
        self,
        quality: MeasurementQualityAnalysis,
    ) -> MeasurementReadinessAnalysis:
        if not isinstance(quality, MeasurementQualityAnalysis):
            raise TypeError(
                "MeasurementReadinessEngine requires MeasurementQualityAnalysis."
            )
        decisions = tuple(
            self._decision(quality, policy) for policy in self.POLICIES
        )
        return MeasurementReadinessAnalysis(
            analyses=decisions,
            confidence=(
                fmean(item.confidence for item in decisions)
                if decisions
                else 0.0
            ),
        )

    @classmethod
    def _decision(cls, quality, policy):
        qualities = {item.channel: item for item in quality.channel_qualities}
        all_issues = [
            issue
            for item in quality.channel_qualities
            for issue in item.issues
        ]
        if quality.measurement_set_quality is not None:
            all_issues.extend(quality.measurement_set_quality.issues)

        relevant_codes = (
            policy.channel_blockers
            | policy.reservations
            | policy.global_blockers
            | {MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL}
        )
        relevant = [issue for issue in all_issues if issue.code in relevant_codes]
        missing_facts = []
        blocking = []
        non_blocking = []

        if policy.required_channels:
            for channel in policy.required_channels:
                channel_quality = qualities.get(channel)
                if channel_quality is None:
                    missing_facts.append(f"CHANNEL_{channel.value}")
                    continue
                channel_blockers = [
                    issue
                    for issue in channel_quality.issues
                    if issue.code in policy.channel_blockers
                ]
                if not cls._base_facts_available(channel_quality):
                    missing_facts.append(f"ELIGIBLE_CHANNEL_{channel.value}")
                blocking.extend(channel_blockers)
                non_blocking.extend(
                    issue
                    for issue in channel_quality.issues
                    if issue in relevant and issue not in channel_blockers
                )
            for issue in relevant:
                if issue.scope is not MeasurementQualityScope.MEASUREMENT_SET:
                    continue
                if issue.code is MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL:
                    missing = issue.observed_metrics.get("missing_channel")
                    if missing in {
                        channel.value for channel in policy.required_channels
                    }:
                        blocking.append(issue)
                elif issue.code in policy.global_blockers:
                    blocking.append(issue)
                else:
                    non_blocking.append(issue)
        else:
            eligible = [
                item
                for item in quality.channel_qualities
                if cls._base_facts_available(item)
                and not any(
                    issue.code in policy.channel_blockers
                    for issue in item.issues
                )
            ]
            channel_relevant = [
                issue
                for issue in relevant
                if issue.scope is MeasurementQualityScope.CHANNEL
            ]
            if not eligible:
                missing_facts.append("ANY_ELIGIBLE_CHANNEL")
                blocking.extend(
                    issue
                    for issue in channel_relevant
                    if issue.code in policy.channel_blockers
                )
                non_blocking.extend(
                    issue
                    for issue in channel_relevant
                    if issue.code not in policy.channel_blockers
                )
            else:
                non_blocking.extend(channel_relevant)
            non_blocking.extend(
                issue
                for issue in relevant
                if issue.scope is MeasurementQualityScope.MEASUREMENT_SET
                and issue.code
                is not MeasurementQualityIssueCode.MISSING_REQUIRED_CHANNEL
            )

        blocking = cls._unique(blocking)
        non_blocking = cls._unique(
            issue for issue in non_blocking if issue not in blocking
        )
        missing_facts = tuple(dict.fromkeys(missing_facts))
        status = (
            MeasurementReadinessStatus.BLOCKED
            if blocking or missing_facts
            else MeasurementReadinessStatus.AVAILABLE_WITH_RESERVATIONS
            if non_blocking
            else MeasurementReadinessStatus.AVAILABLE
        )
        confidence_values = [quality.confidence]
        confidence_values.extend(
            issue.confidence for issue in (*blocking, *non_blocking)
        )
        return AnalysisReadiness(
            family=policy.family,
            status=status,
            blocking_issues=tuple(blocking),
            non_blocking_issues=tuple(non_blocking),
            required_channels=policy.required_channels,
            missing_facts=missing_facts,
            confidence=fmean(confidence_values),
            applied_rule_codes=cls._rule_codes(policy),
        )

    @staticmethod
    def _base_facts_available(quality):
        return (
            quality.sample_rate_hz is not None
            and quality.sample_count is not None
            and quality.sample_count > 0
        )

    @staticmethod
    def _unique(issues):
        unique = []
        for issue in issues:
            if issue not in unique:
                unique.append(issue)
        return unique

    @staticmethod
    def _rule_codes(policy):
        requirement = (
            "REQUIRE_" + "_".join(
                channel.value for channel in policy.required_channels
            )
            if policy.required_channels
            else "REQUIRE_ANY_ELIGIBLE_CHANNEL"
        )
        return (
            requirement,
            "REQUIRE_VALID_SAMPLE_FACTS",
            *tuple(
                f"BLOCK_{code.value}"
                for code in sorted(
                    policy.channel_blockers,
                    key=lambda item: item.value,
                )
            ),
            *tuple(
                f"BLOCK_GLOBAL_{code.value}"
                for code in sorted(
                    policy.global_blockers,
                    key=lambda item: item.value,
                )
            ),
        )
