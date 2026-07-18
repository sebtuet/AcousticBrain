import json
import re

from acousticbrain.models import AdvisorResponse, AdvisorValidationStatus


class AdvisorResponseValidator:
    RESPONSE_SCHEMA_VERSION = "advisor-response.v1"
    SAFETY_ANSWER = (
        "The advisor could not produce a response compliant with the deterministic "
        "objects. The scientific conclusions of the engine remain unchanged."
    )

    def validate(self, request, provider, output):
        context = request.deterministic_context
        by_id = {value.object_id: value for value in context.objects}
        violations = []
        unknown = tuple(value for value in output.referenced_object_ids if value not in by_id)
        if unknown:
            violations.append(f"UNKNOWN_REFERENCES:{','.join(unknown)}")
        for claim in output.claims:
            missing = tuple(value for value in claim.supporting_object_ids if value not in by_id)
            if missing:
                violations.append(f"UNGROUNDED_CLAIM:{claim.text}")
            omitted = tuple(
                value
                for value in claim.supporting_object_ids
                if value not in output.referenced_object_ids
            )
            if omitted:
                violations.append(f"CLAIM_REFERENCE_NOT_DECLARED:{claim.text}")
            self._validate_assertions(claim, by_id, violations)
            self._validate_claim_facts(claim, context, by_id, violations)
        self._preserved(
            "BLOCKING_FACTORS",
            context.blocking_factors,
            output.blocking_factors,
            violations,
        )
        self._preserved(
            "CONTRADICTIONS",
            context.contradictions,
            output.contradictions,
            violations,
        )
        self._preserved(
            "LIMITATIONS",
            context.limitations,
            output.limitations,
            violations,
        )
        existing_actions = {
            value.object_id for value in context.objects if value.object_type == "ACTION"
        }
        invented = tuple(
            value for value in output.proposed_action_ids if value not in existing_actions
        )
        if invented:
            violations.append(f"INVENTED_ACTIONS:{','.join(invented)}")
        if output.introduced_scores or re.search(r"\b\d+(?:\.\d+)?\s*%", output.answer):
            violations.append("INTRODUCED_GLOBAL_SCORE_OR_PERCENTAGE")
        normalized_answer = output.answer.casefold()
        if any(
            value in normalized_answer
            for value in (
                "blocked action is applicable",
                "blocked action can be executed",
                "contradiction is resolved",
                "contradiction can be ignored",
                "limitation is resolved",
            )
        ):
            violations.append("UNGROUNDED_SEMANTIC_OVERRIDE")
        serialized_context = " ".join(value.canonical_json for value in context.objects)
        invented_geometry = tuple(
            value
            for value in re.findall(
                r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|degrees?|°)\b",
                output.answer,
                flags=re.IGNORECASE,
            )
            if value not in serialized_context
        )
        if invented_geometry:
            violations.append(f"INVENTED_GEOMETRY:{'|'.join(invented_geometry)}")

        status = (
            AdvisorValidationStatus.INVALID
            if violations
            else AdvisorValidationStatus.VALID
        )
        answer = self.SAFETY_ANSWER if violations else output.answer
        references = (
            tuple(by_id)
            if violations
            else tuple(value for value in output.referenced_object_ids if value in by_id)
        )
        typed = self._typed_references(references, by_id)
        warnings = ()
        if provider.provider_id != "mock":
            warnings = ("Provider-generated text is not guaranteed byte-for-byte deterministic.",)
        return AdvisorResponse(
            schema_version=self.RESPONSE_SCHEMA_VERSION,
            advisor_request_id=request.request_id,
            provider_id=provider.provider_id,
            model_id=provider.model_id,
            original_question=request.question,
            answer_text=answer,
            referenced_object_ids=references,
            referenced_observation_ids=typed["OBSERVATION"],
            referenced_reasoning_ids=typed["REASONING"],
            referenced_action_ids=typed["ACTION"],
            referenced_evidence_weight_ids=typed["EVIDENCE_WEIGHT"],
            preserved_blocking_factors=context.blocking_factors,
            preserved_contradictions=context.contradictions,
            preserved_limitations=context.limitations,
            unsupported_claims=tuple(violations),
            validation_status=status,
            warnings=warnings,
        )

    @staticmethod
    def _validate_assertions(claim, by_id, violations):
        for action_id, asserted in claim.asserted_action_applicability:
            value = by_id.get(action_id)
            if value is None or value.object_type != "ACTION":
                violations.append(f"UNKNOWN_ACTION_ASSERTION:{action_id}")
                continue
            actual = json.loads(value.canonical_json)["applicability"]
            normalized = "BLOCKED" if actual.startswith("BLOCKED") else actual
            if asserted != normalized:
                violations.append(
                    f"ACTION_APPLICABILITY_MODIFIED:{action_id}:{actual}->{asserted}"
                )
        for weight_id, dimension, asserted in claim.asserted_weight_dimensions:
            value = by_id.get(weight_id)
            if value is None or value.object_type != "EVIDENCE_WEIGHT":
                violations.append(f"UNKNOWN_WEIGHT_ASSERTION:{weight_id}")
                continue
            data = json.loads(value.canonical_json)
            field = dimension.casefold()
            if field not in data or data[field] != asserted:
                violations.append(
                    f"WEIGHT_DIMENSION_MODIFIED:{weight_id}:{dimension}"
                )

    @staticmethod
    def _validate_claim_facts(claim, context, by_id, violations):
        evidence = set()
        for object_id in claim.supporting_object_ids:
            value = by_id.get(object_id)
            if value is None:
                continue
            data = json.loads(value.canonical_json)
            evidence.update(data.get("supporting_evidence", ()))
            evidence.update(data.get("contradicting_evidence", ()))
        checks = (
            ("EVIDENCE", claim.asserted_evidence, evidence),
            ("BLOCKING_FACTOR", claim.asserted_blocking_factors, set(context.blocking_factors)),
            ("CONTRADICTION", claim.asserted_contradictions, set(context.contradictions)),
            ("LIMITATION", claim.asserted_limitations, set(context.limitations)),
        )
        for label, asserted, available in checks:
            unknown = tuple(value for value in asserted if value not in available)
            if unknown:
                violations.append(f"INVENTED_{label}:{'|'.join(unknown)}")

    @staticmethod
    def _preserved(label, expected, received, violations):
        missing = tuple(value for value in expected if value not in received)
        unknown = tuple(value for value in received if value not in expected)
        if missing:
            violations.append(f"OMITTED_{label}:{'|'.join(missing)}")
        if unknown:
            violations.append(f"INVENTED_{label}:{'|'.join(unknown)}")

    @staticmethod
    def _typed_references(references, by_id):
        types = ("OBSERVATION", "REASONING", "ACTION", "EVIDENCE_WEIGHT")
        return {
            kind: tuple(
                value for value in references
                if value in by_id and by_id[value].object_type == kind
            )
            for kind in types
        }
