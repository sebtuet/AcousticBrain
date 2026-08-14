import json
from typing import Protocol

from acousticbrain.models import (
    GuidedAnswerInterpretation,
    GuidedInterpretationStatus,
    RoomDescriptionQuestionPlan,
)


class ConversationalRoomDescriptionInterpreter(Protocol):
    def formulate(self, question: RoomDescriptionQuestionPlan) -> str:
        ...

    def interpret(
        self, question: RoomDescriptionQuestionPlan, user_answer: str
    ) -> GuidedAnswerInterpretation:
        ...


class OllamaGuidedRoomDescriptionAdapter:
    """Interprète du texte, sans construire ni persister de données métier."""

    def __init__(self, client):
        if not hasattr(client, "ask") or not callable(client.ask):
            raise TypeError("Ollama adapter requires an ask-capable client.")
        self.client = client

    def formulate(self, question):
        payload = self._question_payload(question)
        prompt = (
            "Reformule en une question utilisateur concise, sans ajouter de choix "
            "ni de faits. Réponds uniquement par la question.\n"
            + json.dumps(payload, sort_keys=True)
        )
        return str(self.client.ask(prompt)).strip()

    def interpret(self, question, user_answer):
        if not isinstance(user_answer, str) or not user_answer.strip():
            return self._insufficient("EMPTY_USER_ANSWER")
        prompt = (
            "Tu es un interprète contrôlé. Choisis uniquement parmi allowed_value_ids "
            "et target_candidates. N'invente aucune propriété acoustique. Réponds en "
            "JSON avec status, candidate_value_ids, target_id, confidence et "
            "ambiguity_codes.\n"
            + json.dumps({
                "question": self._question_payload(question),
                "user_answer": user_answer,
            }, sort_keys=True)
        )
        try:
            raw = json.loads(self.client.ask(prompt))
            status = GuidedInterpretationStatus(raw["status"])
            candidates = tuple(raw.get("candidate_value_ids", ()))
            target_id = raw.get("target_id")
            confidence = raw.get("confidence", 0.0)
            ambiguities = tuple(raw.get("ambiguity_codes", ()))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return self._insufficient("INVALID_INTERPRETER_RESPONSE")

        allowed = {item.value_id for item in question.allowed_values}
        if any(item not in allowed for item in candidates):
            return self._insufficient("INTERPRETER_VALUE_OUTSIDE_ALLOWED_SET")
        if target_id is not None and target_id not in question.target_candidates:
            return self._insufficient("INTERPRETER_TARGET_OUTSIDE_ALLOWED_SET")
        try:
            return GuidedAnswerInterpretation(
                status=status,
                candidate_value_ids=candidates,
                target_id=target_id,
                confidence=confidence,
                ambiguity_codes=ambiguities,
                provenance_codes=("USER_DESCRIPTION_INTERPRETED",),
            )
        except ValueError:
            return self._insufficient("INVALID_INTERPRETER_RESPONSE")

    @staticmethod
    def _question_payload(question):
        return {
            "question_id": question.question_id,
            "fact_code": question.fact_code,
            "target_kind": question.target_kind,
            "target_role": question.target_role,
            "target_candidates": list(question.target_candidates),
            "allowed_value_ids": [
                item.value_id for item in question.allowed_values
            ],
            "constraints": list(question.validation_constraints),
        }

    @staticmethod
    def _insufficient(code):
        return GuidedAnswerInterpretation(
            status=GuidedInterpretationStatus.INSUFFICIENT,
            ambiguity_codes=(code,),
            provenance_codes=("USER_DESCRIPTION_INTERPRETED",),
        )
