import json
from pathlib import Path

from acousticbrain.models import (
    ControlledReflectionHypothesisStatusUpdate,
    ControlledReflectionHypothesisStatusUpdateRegistry,
    ReflectionHypothesisCausalityStatus,
    ReflectionHypothesisImpact,
    ReflectionHypothesisObservationStatus,
)


class ControlledReflectionHypothesisStatusJsonCodec:
    SCHEMA_VERSION = 1

    def dumps(self, registry, *, indent=2):
        if not isinstance(registry, ControlledReflectionHypothesisStatusUpdateRegistry):
            raise TypeError("Reflection hypothesis status registry is required.")
        return json.dumps(
            {
                "schema_version": self.SCHEMA_VERSION,
                "updates": [
                    self._encode(item)
                    for item in sorted(registry.updates, key=lambda item: item.update_id)
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
            raise ValueError("Invalid reflection hypothesis status JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("Hypothesis status payload must be an object.")
        if value.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Unsupported hypothesis status schema version.")
        updates = value.get("updates")
        if not isinstance(updates, list):
            raise ValueError("Hypothesis status updates must be a list.")
        return ControlledReflectionHypothesisStatusUpdateRegistry(
            updates=tuple(sorted(
                (self._decode(item) for item in updates),
                key=lambda item: item.update_id,
            )),
            schema_version=self.SCHEMA_VERSION,
        )

    @staticmethod
    def _encode(item):
        return {
            "update_id": item.update_id,
            "target_kind": item.target_kind,
            "target_id": item.target_id,
            "proposal_id": item.proposal_id,
            "experiment_declaration_id": item.experiment_declaration_id,
            "comparison_id": item.comparison_id,
            "status": item.status.value,
            "measured_fact_codes": list(item.measured_fact_codes),
            "comparison_result_codes": list(item.comparison_result_codes),
            "transition_rule_codes": list(item.transition_rule_codes),
            "status_provenance_codes": list(item.status_provenance_codes),
            "justification_codes": list(item.justification_codes),
            "causality_status": item.causality_status.value,
            "recommendation_impact": item.recommendation_impact.value,
            "ranking_impact": item.ranking_impact.value,
            "eligibility_impact": item.eligibility_impact.value,
            "source_analysis_codes": list(item.source_analysis_codes),
        }

    @classmethod
    def _decode(cls, value):
        if not isinstance(value, dict):
            raise ValueError("Hypothesis status update must be an object.")
        try:
            status = ReflectionHypothesisObservationStatus(value.get("status"))
            causality = ReflectionHypothesisCausalityStatus(
                value.get("causality_status")
            )
            recommendation = ReflectionHypothesisImpact(
                value.get("recommendation_impact")
            )
            ranking = ReflectionHypothesisImpact(value.get("ranking_impact"))
            eligibility = ReflectionHypothesisImpact(
                value.get("eligibility_impact")
            )
        except (TypeError, ValueError) as error:
            raise ValueError("Unsupported hypothesis status enum value.") from error
        comparison_id = value.get("comparison_id")
        if comparison_id is not None and (
            not isinstance(comparison_id, str) or not comparison_id.strip()
        ):
            raise ValueError("Optional comparison id cannot be empty.")
        return ControlledReflectionHypothesisStatusUpdate(
            update_id=cls._string(value, "update_id"),
            target_kind=cls._string(value, "target_kind"),
            target_id=cls._string(value, "target_id"),
            proposal_id=cls._string(value, "proposal_id"),
            experiment_declaration_id=cls._string(
                value, "experiment_declaration_id"
            ),
            comparison_id=comparison_id,
            status=status,
            measured_fact_codes=cls._strings(value, "measured_fact_codes"),
            comparison_result_codes=cls._strings(
                value, "comparison_result_codes"
            ),
            transition_rule_codes=cls._strings(value, "transition_rule_codes"),
            status_provenance_codes=cls._strings(
                value, "status_provenance_codes"
            ),
            justification_codes=cls._strings(value, "justification_codes"),
            causality_status=causality,
            recommendation_impact=recommendation,
            ranking_impact=ranking,
            eligibility_impact=eligibility,
            source_analysis_codes=cls._strings(value, "source_analysis_codes"),
        )

    @staticmethod
    def _string(value, key):
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Hypothesis status field {key} is required.")
        return item

    @staticmethod
    def _strings(value, key):
        items = value.get(key)
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise ValueError(f"Hypothesis status field {key} must be a list.")
        return tuple(items)


class ControlledReflectionHypothesisStatusJsonRepository:
    def __init__(self, codec=None):
        self.codec = codec or ControlledReflectionHypothesisStatusJsonCodec()

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
            return ControlledReflectionHypothesisStatusUpdateRegistry(())
        return self.codec.loads(target.read_text(encoding="utf-8"))
