import json
import re
from difflib import SequenceMatcher

from acousticbrain.models import (
    AdvisorDimensionStatus,
    AdvisorResponse,
    AdvisorResponseLanguage,
    AdvisorResponseSource,
    AdvisorValidationStatus,
)


class AdvisorResponseValidator:
    RESPONSE_SCHEMA_VERSION = "advisor-response.v2"

    def validate(self, request, provider, output):
        context = request.deterministic_context
        by_id = {value.object_id: value for value in context.objects}
        scientific = []
        references = []
        coverage = []
        language = []
        degeneracy = []

        unknown = tuple(value for value in output.referenced_object_ids if value not in by_id)
        if unknown:
            references.append(f"UNKNOWN_REFERENCES:{','.join(unknown)}")
        for claim in output.claims:
            missing = tuple(value for value in claim.supporting_object_ids if value not in by_id)
            if missing:
                references.append(f"UNGROUNDED_CLAIM:{claim.text}")
            omitted = tuple(
                value for value in claim.supporting_object_ids
                if value not in output.referenced_object_ids
            )
            if omitted:
                references.append(f"CLAIM_REFERENCE_NOT_DECLARED:{claim.text}")
            self._validate_assertions(claim, by_id, scientific)
            self._validate_claim_facts(claim, context, by_id, scientific)

        self._preserved("BLOCKING_FACTORS", context.blocking_factors, output.blocking_factors, scientific)
        self._preserved("CONTRADICTIONS", context.contradictions, output.contradictions, scientific)
        self._preserved("LIMITATIONS", context.limitations, output.limitations, scientific)
        existing_actions = {
            value.object_id for value in context.objects if value.object_type == "ACTION"
        }
        invented = tuple(value for value in output.proposed_action_ids if value not in existing_actions)
        if invented:
            scientific.append(f"INVENTED_ACTIONS:{','.join(invented)}")
        if output.introduced_scores or re.search(r"\b\d+(?:\.\d+)?\s*%", output.answer):
            scientific.append("INTRODUCED_GLOBAL_SCORE_OR_PERCENTAGE")
        normalized_answer = output.answer.casefold()
        semantic_override = any(value in normalized_answer for value in (
            "blocked action is applicable", "blocked action can be executed",
            "contradiction is resolved", "contradiction can be ignored",
            "limitation is resolved",
        ))
        explicit_negations = (
            "no blocked action is applicable",
            "no blocked action can be executed",
            "aucune action bloquée n’est présentée comme applicable",
            "aucune action bloquée n'est présentée comme applicable",
        )
        if semantic_override and not any(
            value in normalized_answer for value in explicit_negations
        ):
            scientific.append("UNGROUNDED_SEMANTIC_OVERRIDE")
        serialized_context = " ".join(value.canonical_json for value in context.objects)
        invented_geometry = tuple(value for value in re.findall(
            r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|degrees?|°)\b",
            output.answer, flags=re.IGNORECASE,
        ) if value not in serialized_context)
        if invented_geometry:
            scientific.append(f"INVENTED_GEOMETRY:{'|'.join(invented_geometry)}")

        requirements = (
            ("REASONING", context.required_reasoning_ids, output.covered_reasoning_ids),
            ("BLOCKING_FACTOR", context.required_blocking_factor_ids, output.covered_blocking_factor_ids),
            ("READY_PLAN", context.required_ready_plan_ids, output.covered_ready_plan_ids),
            ("BLOCKED_PLAN", context.required_blocked_plan_ids, output.covered_blocked_plan_ids),
        )
        for label, expected, received in requirements:
            self._coverage(label, expected, received, coverage)
        crossed = set(output.covered_ready_plan_ids) & set(output.covered_blocked_plan_ids)
        if crossed:
            coverage.append(f"PLAN_STATUS_CROSS_CLASSIFICATION:{'|'.join(sorted(crossed))}")
        if output.response_language is not context.expected_response_language:
            language.append(
                "RESPONSE_LANGUAGE_DECLARATION_MISMATCH:"
                f"{context.expected_response_language.value}->{output.response_language.value}"
            )
        self._validate_answer_language(output.answer, context.expected_response_language, language)
        self._validate_degeneracy(output, context, degeneracy)

        groups = [scientific, coverage, language, references, degeneracy]
        groups = [list(dict.fromkeys(values)) for values in groups]
        violations = tuple(dict.fromkeys(value for values in groups for value in values))
        statuses = tuple(
            AdvisorDimensionStatus.INVALID if values else AdvisorDimensionStatus.VALID
            for values in groups
        )
        valid = not violations
        response_source = (
            AdvisorResponseSource.PROVIDER if valid
            else AdvisorResponseSource.LOCAL_SAFETY_RESPONSE
        )
        answer = output.answer if valid else self._safety_answer(context)
        refs = (
            tuple(value for value in output.referenced_object_ids if value in by_id)
            if valid else tuple(by_id)
        )
        typed = self._typed_references(refs, by_id)
        warnings = () if provider.provider_id == "mock" else (
            "Provider-generated text is not guaranteed byte-for-byte deterministic.",
        )
        return AdvisorResponse(
            schema_version=self.RESPONSE_SCHEMA_VERSION,
            advisor_request_id=request.request_id,
            provider_id=provider.provider_id,
            model_id=provider.model_id,
            original_question=request.question,
            answer_text=answer,
            referenced_object_ids=refs,
            referenced_observation_ids=typed["OBSERVATION"],
            referenced_reasoning_ids=typed["REASONING"],
            referenced_action_ids=typed["ACTION"],
            referenced_evidence_weight_ids=typed["EVIDENCE_WEIGHT"],
            preserved_blocking_factors=context.blocking_factors,
            preserved_contradictions=context.contradictions,
            preserved_limitations=context.limitations,
            unsupported_claims=violations,
            validation_status=(AdvisorValidationStatus.VALID if valid else AdvisorValidationStatus.INVALID),
            warnings=warnings,
            response_source=response_source,
            scientific_fidelity_status=statuses[0],
            semantic_coverage_status=statuses[1],
            response_language_status=statuses[2],
            reference_integrity_status=statuses[3],
            degeneracy_status=statuses[4],
            response_language=context.expected_response_language,
            covered_reasoning_ids=(output.covered_reasoning_ids if valid else context.required_reasoning_ids),
            covered_blocking_factor_ids=(output.covered_blocking_factor_ids if valid else context.required_blocking_factor_ids),
            covered_ready_plan_ids=(output.covered_ready_plan_ids if valid else context.required_ready_plan_ids),
            covered_blocked_plan_ids=(output.covered_blocked_plan_ids if valid else context.required_blocked_plan_ids),
        )

    @staticmethod
    def _coverage(label, expected, received, violations):
        duplicates = tuple(dict.fromkeys(value for value in received if received.count(value) > 1))
        missing = tuple(value for value in expected if value not in received)
        unknown = tuple(value for value in received if value not in expected)
        if duplicates:
            violations.append(f"DUPLICATE_{label}_COVERAGE:{'|'.join(duplicates)}")
        if missing:
            violations.append(f"MISSING_{label}_COVERAGE:{'|'.join(missing)}")
        if unknown:
            violations.append(f"UNKNOWN_{label}_COVERAGE:{'|'.join(unknown)}")
        if not duplicates and not missing and not unknown and received != expected:
            violations.append(f"REORDERED_{label}_COVERAGE")

    @staticmethod
    def _validate_answer_language(answer, expected, violations):
        tokens = re.findall(r"[a-zà-ÿ]+", answer.casefold())
        french = {"le", "la", "les", "des", "une", "est", "sont", "pour", "aucune", "avec", "prêts", "bloqués", "résumé", "problèmes"}
        english = {"the", "and", "is", "are", "for", "with", "none", "ready", "blocked", "summary", "problems"}
        expected_hits = sum(value in (french if expected is AdvisorResponseLanguage.FR else english) for value in tokens)
        other_hits = sum(value in (english if expected is AdvisorResponseLanguage.FR else french) for value in tokens)
        if other_hits >= 3 and other_hits > expected_hits * 2:
            violations.append(f"ANSWER_LANGUAGE_MISMATCH:{expected.value}")

    @classmethod
    def _validate_degeneracy(cls, output, context, violations):
        normalized = cls._normalized(output.answer)
        tokens = normalized.split()
        if len(tokens) < 12 or len(normalized) < 70:
            violations.append("DEGENERATE_ANSWER_TOO_SHORT")
        generic = cls._normalized("The answer restates only the supplied deterministic objects.")
        if normalized == generic:
            violations.append("DEGENERATE_GENERIC_METADATA_ANSWER")
        internal = [claim.text for claim in output.claims] + list(context.limitations)
        for value in internal:
            candidate = cls._normalized(value)
            if candidate and (normalized == candidate or SequenceMatcher(None, normalized, candidate).ratio() >= 0.92):
                violations.append("DEGENERATE_INTERNAL_TEXT_REPETITION")
                break
        lowered = output.answer.casefold()
        categories = (
            (context.required_reasoning_ids, ("problem", "problèm", "reasoning", "raisonnement", "hypoth"), "REASONING"),
            (context.required_blocking_factor_ids, ("blocking", "blocked", "blocage", "bloqu", "contradiction", "missing", "manquant"), "BLOCKING_FACTOR"),
            (context.required_ready_plan_ids, ("ready", "prêt"), "READY_PLAN"),
            (context.required_blocked_plan_ids, ("blocked", "bloqué", "bloqués"), "BLOCKED_PLAN"),
        )
        for required, markers, label in categories:
            if required and not any(marker in lowered for marker in markers):
                violations.append(f"DEGENERATE_MISSING_{label}_SYNTHESIS")
        plans = context.required_ready_plan_ids + context.required_blocked_plan_ids
        if plans and not any(value in output.answer for value in plans):
            violations.append("DEGENERATE_NO_PLAN_REFERENCE_IN_ANSWER")

    @staticmethod
    def _normalized(value):
        return " ".join(re.findall(r"[\wà-ÿ]+", value.casefold()))

    @staticmethod
    def _safety_answer(context):
        labels = dict(context.object_labels)
        def listed(values, empty):
            return "; ".join(f"{labels.get(value, value)} [{value}]" for value in values) or empty
        if context.expected_response_language is AdvisorResponseLanguage.FR:
            return (
                "Réponse locale de sûreté. Résumé des problèmes déterministes : "
                + listed(context.required_reasoning_ids, "aucun")
                + ". Facteurs de blocage préservés : "
                + listed(context.required_blocking_factor_ids, "aucun")
                + ". Plans READY — tests prêts : "
                + listed(context.required_ready_plan_ids, "aucun")
                + ". Plans BLOCKED — tests bloqués : "
                + listed(context.required_blocked_plan_ids, "aucun")
                + ". La réponse du fournisseur a été rejetée; aucune conclusion scientifique ni action n’est modifiée."
            )
        return (
            "Local safety response. Deterministic problem summary: "
            + listed(context.required_reasoning_ids, "none")
            + ". Preserved blocking factors: "
            + listed(context.required_blocking_factor_ids, "none")
            + ". READY plans — tests ready to run: "
            + listed(context.required_ready_plan_ids, "none")
            + ". BLOCKED plans — blocked tests: "
            + listed(context.required_blocked_plan_ids, "none")
            + ". The provider response was rejected; no scientific conclusion or action is modified."
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
                violations.append(f"ACTION_APPLICABILITY_MODIFIED:{action_id}:{actual}->{asserted}")
        for weight_id, dimension, asserted in claim.asserted_weight_dimensions:
            value = by_id.get(weight_id)
            if value is None or value.object_type != "EVIDENCE_WEIGHT":
                violations.append(f"UNKNOWN_WEIGHT_ASSERTION:{weight_id}")
                continue
            data = json.loads(value.canonical_json)
            field = dimension.casefold()
            if field not in data or data[field] != asserted:
                violations.append(f"WEIGHT_DIMENSION_MODIFIED:{weight_id}:{dimension}")

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
            kind: tuple(value for value in references if value in by_id and by_id[value].object_type == kind)
            for kind in types
        }
