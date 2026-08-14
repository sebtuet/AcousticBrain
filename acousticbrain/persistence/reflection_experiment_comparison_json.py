import json
from pathlib import Path

from acousticbrain.models import (
    ControlledReflectionExperimentComparison,
    ControlledReflectionExperimentComparisonRegistry,
    ObservedReflectionDifference,
    ReflectionComparisonCausalityStatus,
    ReflectionComparisonImpact,
    ReflectionExperimentComparisonStatus,
)


class ControlledReflectionExperimentComparisonJsonCodec:
    SCHEMA_VERSION = 1

    def dumps(self, registry, *, indent=2):
        if not isinstance(registry, ControlledReflectionExperimentComparisonRegistry):
            raise TypeError("Reflection comparison registry is required.")
        return json.dumps(
            {
                "schema_version": self.SCHEMA_VERSION,
                "comparisons": [
                    self._encode(item)
                    for item in sorted(
                        registry.comparisons,
                        key=lambda item: item.comparison_id,
                    )
                ],
            },
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )

    def loads(self, payload):
        try:
            value = json.loads(payload)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError("Invalid reflection comparison JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("Reflection comparison payload must be an object.")
        if value.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Unsupported reflection comparison schema version.")
        values = value.get("comparisons")
        if not isinstance(values, list):
            raise ValueError("Reflection comparisons must be a list.")
        return ControlledReflectionExperimentComparisonRegistry(
            comparisons=tuple(sorted(
                (self._decode(item) for item in values),
                key=lambda item: item.comparison_id,
            )),
            schema_version=self.SCHEMA_VERSION,
        )

    @classmethod
    def _encode(cls, item):
        return {
            "comparison_id": item.comparison_id,
            "experiment_declaration_id": item.experiment_declaration_id,
            "proposal_id": item.proposal_id,
            "status": item.status.value,
            "temporal_window_code": item.temporal_window_code,
            "baseline_measurement_reference_ids": list(
                item.baseline_measurement_reference_ids
            ),
            "intervention_measurement_reference_ids": list(
                item.intervention_measurement_reference_ids
            ),
            "observed_differences": [
                {
                    "observable_code": difference.observable_code,
                    "unit": difference.unit,
                    "baseline_value": difference.baseline_value,
                    "intervention_value": difference.intervention_value,
                    "signed_difference": difference.signed_difference,
                    "absolute_difference": difference.absolute_difference,
                    "baseline_provenance_codes": list(
                        difference.baseline_provenance_codes
                    ),
                    "intervention_provenance_codes": list(
                        difference.intervention_provenance_codes
                    ),
                }
                for difference in item.observed_differences
            ],
            "reason_codes": list(item.reason_codes),
            "causality_status": item.causality_status.value,
            "ranking_impact": item.ranking_impact.value,
            "recommendation_impact": item.recommendation_impact.value,
            "eligibility_impact": item.eligibility_impact.value,
            "source_analysis_codes": list(item.source_analysis_codes),
            "applied_rule_codes": list(item.applied_rule_codes),
        }

    @classmethod
    def _decode(cls, value):
        if not isinstance(value, dict):
            raise ValueError("Reflection comparison must be an object.")
        try:
            status = ReflectionExperimentComparisonStatus(value.get("status"))
            causality = ReflectionComparisonCausalityStatus(
                value.get("causality_status")
            )
            ranking = ReflectionComparisonImpact(value.get("ranking_impact"))
            recommendation = ReflectionComparisonImpact(
                value.get("recommendation_impact")
            )
            eligibility = ReflectionComparisonImpact(
                value.get("eligibility_impact")
            )
        except (TypeError, ValueError) as error:
            raise ValueError("Unsupported reflection comparison enum value.") from error
        differences = value.get("observed_differences")
        if not isinstance(differences, list):
            raise ValueError("Observed reflection differences must be a list.")
        return ControlledReflectionExperimentComparison(
            comparison_id=cls._string(value, "comparison_id"),
            experiment_declaration_id=cls._string(
                value, "experiment_declaration_id"
            ),
            proposal_id=cls._string(value, "proposal_id"),
            status=status,
            temporal_window_code=cls._string(value, "temporal_window_code"),
            baseline_measurement_reference_ids=cls._strings(
                value, "baseline_measurement_reference_ids"
            ),
            intervention_measurement_reference_ids=cls._strings(
                value, "intervention_measurement_reference_ids"
            ),
            observed_differences=tuple(sorted(
                (cls._difference(item) for item in differences),
                key=lambda item: item.observable_code,
            )),
            reason_codes=cls._strings(value, "reason_codes"),
            causality_status=causality,
            ranking_impact=ranking,
            recommendation_impact=recommendation,
            eligibility_impact=eligibility,
            source_analysis_codes=cls._strings(value, "source_analysis_codes"),
            applied_rule_codes=cls._strings(value, "applied_rule_codes"),
        )

    @classmethod
    def _difference(cls, value):
        if not isinstance(value, dict):
            raise ValueError("Observed reflection difference must be an object.")
        return ObservedReflectionDifference(
            observable_code=cls._string(value, "observable_code"),
            unit=cls._string(value, "unit"),
            baseline_value=cls._number(value, "baseline_value"),
            intervention_value=cls._number(value, "intervention_value"),
            signed_difference=cls._number(value, "signed_difference"),
            absolute_difference=cls._number(value, "absolute_difference"),
            baseline_provenance_codes=cls._strings(
                value, "baseline_provenance_codes"
            ),
            intervention_provenance_codes=cls._strings(
                value, "intervention_provenance_codes"
            ),
        )

    @staticmethod
    def _string(value, key):
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Reflection comparison field {key} is required.")
        return item

    @staticmethod
    def _strings(value, key):
        items = value.get(key)
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise ValueError(f"Reflection comparison field {key} must be a list.")
        return tuple(items)

    @staticmethod
    def _number(value, key):
        item = value.get(key)
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            raise ValueError(f"Reflection comparison field {key} must be numeric.")
        return item


class ControlledReflectionExperimentComparisonJsonRepository:
    def __init__(self, codec=None):
        self.codec = codec or ControlledReflectionExperimentComparisonJsonCodec()

    def save(self, path, registry):
        target = Path(path)
        serialized = self.codec.dumps(registry) + "\n"
        if target.is_file() and target.read_text(encoding="utf-8") == serialized:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(target)
        return True

    def load(self, path):
        target = Path(path)
        if not target.is_file():
            return ControlledReflectionExperimentComparisonRegistry(())
        return self.codec.loads(target.read_text(encoding="utf-8"))
