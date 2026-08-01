import json
from pathlib import Path

from acousticbrain.models import (
    ExploratoryFeasibilityDecision,
    ExploratoryFeasibilityRegistry,
    ExploratoryProposalInput,
    FeasibilityAnswer,
)


class ExploratoryProposalInputJsonLoader:
    SCHEMA_VERSION = 1

    def load(self, path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Unsupported exploratory-proposal schema version.")
        raw = payload.get("exploratory_proposal_input")
        if not isinstance(raw, dict):
            raise ValueError("Invalid exploratory-proposal document.")
        return ExploratoryProposalInput(
            candidate_id=raw["candidate_id"],
            reference_experiment_id=raw["reference_experiment_id"],
            reference_content_fingerprint=raw["reference_content_fingerprint"],
            reference_configuration=self._pairs(raw, "reference_configuration"),
            action_parameters=self._pairs(raw, "action_parameters"),
            return_action=raw["return_action"],
            feasibility_question=raw["feasibility_question"],
            limitations=self._strings(raw, "limitations"),
            field_provenance=self._pairs(raw, "field_provenance"),
        )

    @staticmethod
    def _pairs(raw, field):
        value = raw.get(field)
        if not isinstance(value, dict) or not value:
            raise ValueError(f"Exploratory {field} must be a non-empty object.")
        if any(not isinstance(key, str) or not isinstance(item, str)
               for key, item in value.items()):
            raise ValueError(f"Exploratory {field} values must be strings.")
        return tuple(sorted(value.items()))

    @staticmethod
    def _strings(raw, field):
        value = raw.get(field)
        if not isinstance(value, list) or not value or any(
            not isinstance(item, str) or not item for item in value
        ):
            raise ValueError(f"Exploratory {field} must be a non-empty string list.")
        return tuple(value)


class ExploratoryFeasibilityJsonRepository:
    SCHEMA_VERSION = 1

    def load(self, path):
        target = Path(path)
        if not target.exists():
            return ExploratoryFeasibilityRegistry()
        payload = json.loads(target.read_text(encoding="utf-8"))
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Unsupported exploratory-feasibility schema version.")
        raw = payload.get("decisions")
        if not isinstance(raw, list):
            raise ValueError("Invalid exploratory-feasibility document.")
        return ExploratoryFeasibilityRegistry(tuple(
            ExploratoryFeasibilityDecision(
                proposal_id=item["proposal_id"],
                reference_scope_id=item["reference_scope_id"],
                rule_version=item["rule_version"],
                answer=FeasibilityAnswer(item["answer"]),
                user_note=item.get("user_note"),
            )
            for item in raw
        ))

    def save(self, registry, path):
        if not isinstance(registry, ExploratoryFeasibilityRegistry):
            raise TypeError("ExploratoryFeasibilityRegistry is required.")
        target = Path(path)
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "decisions": [
                {
                    "proposal_id": item.proposal_id,
                    "reference_scope_id": item.reference_scope_id,
                    "rule_version": item.rule_version,
                    "answer": item.answer.value,
                    "user_note": item.user_note,
                }
                for item in registry.decisions
            ],
        }
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
