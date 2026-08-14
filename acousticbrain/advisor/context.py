from dataclasses import asdict
import hashlib
import json

from acousticbrain.models import (
    AdvisorContextObject,
    AdvisorAssessmentContext,
    AdvisorRequest,
    AdvisorResponseLanguage,
)


class AdvisorContextBuilder:
    """Builds the bounded Advisor context from CampaignUserAssessment only."""

    SCHEMA_VERSION = "advisor-assessment-context.v1"
    REQUEST_SCHEMA_VERSION = "advisor-request.v3"

    def build(self, report, *, selected_object_ids=(), expected_response_language=AdvisorResponseLanguage.EN):
        assessment = getattr(report, "campaign_user_assessment", None)
        if assessment is None:
            raise ValueError("Advisor requires CampaignUserAssessment.")
        objects = self._assessment_objects(assessment)
        by_id = {value.object_id: value for value in objects}
        requested = tuple(selected_object_ids)
        unknown = tuple(value for value in requested if value not in by_id)
        if unknown:
            raise ValueError(f"Unknown advisor assessment ids: {', '.join(unknown)}")
        if requested:
            objects = tuple(value for value in objects if value.object_id in requested)
            by_id = {value.object_id: value for value in objects}
        allowed_sources = tuple(dict.fromkeys(
            source for value in objects
            for source in self._data(value).get("source_ids", (value.object_id,))
        ))
        findings = tuple(value.object_id for value in objects if value.object_type == "REASONING")
        uncertainties = tuple(
            value.object_id for value in objects
            if value.object_type == "REASONING" and self._data(value).get("uncertain")
        )
        next_steps = tuple(
            value.object_id for value in objects
            if value.object_type == "EVIDENCE_ACQUISITION_PLAN"
        )
        return AdvisorAssessmentContext(
            schema_version=self.SCHEMA_VERSION,
            project_id=str(report.project_name),
            objects=objects,
            blocking_factors=uncertainties,
            contradictions=tuple(
                value.object_id for value in objects
                if value.object_type == "REASONING"
                and self._data(value).get("conclusion") == "CONTRADICTORY_EVIDENCE"
            ),
            limitations=tuple(assessment.scientific_boundaries),
            expected_response_language=expected_response_language,
            required_reasoning_ids=findings,
            required_blocking_factor_ids=uncertainties,
            required_ready_plan_ids=tuple(
                value for value in next_steps
                if self._data(by_id[value]).get("planning_status") == "READY"
            ),
            required_blocked_plan_ids=tuple(
                value for value in next_steps
                if self._data(by_id[value]).get("planning_status") == "BLOCKED"
            ),
            allowed_object_ids=tuple(value.object_id for value in objects),
            allowed_source_ids=allowed_sources,
            object_labels=tuple((value.object_id, self._label(value)) for value in objects),
        )

    def request(self, report, *, question, audience, detail_level,
                provider_configuration_reference, selected_object_ids=(),
                expected_response_language=AdvisorResponseLanguage.EN):
        context = self.build(
            report,
            selected_object_ids=selected_object_ids,
            expected_response_language=expected_response_language,
        )
        identity = json.dumps(
            {
                "question": question,
                "audience": audience.value,
                "detail": detail_level.value,
                "project": context.project_id,
                "objects": list(context.allowed_object_ids),
                "provider": provider_configuration_reference,
                "language": expected_response_language.value,
            },
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
        request_id = f"advisor-request.{hashlib.sha256(identity.encode()).hexdigest()[:16]}"
        return AdvisorRequest(
            schema_version=self.REQUEST_SCHEMA_VERSION,
            request_id=request_id,
            question=question,
            requested_audience=audience,
            requested_detail_level=detail_level,
            selected_project_id=context.project_id,
            selected_object_ids=tuple(selected_object_ids),
            deterministic_context=context,
            provider_configuration_reference=provider_configuration_reference,
        )

    def serialize(self, context):
        groups = {
            "campaign_status": "CAMPAIGN_STATUS",
            "findings": "REASONING",
            "applicable_actions": "ACTION",
            "unavailable_actions": "ACTION",
            "scientific_boundaries": "SCIENTIFIC_BOUNDARY",
        }
        payload = {"schema_version": context.schema_version}
        for name, object_type in groups.items():
            payload[name] = [
                self._serialized(value) for value in context.objects
                if value.object_type == object_type and (
                    name not in ("applicable_actions", "unavailable_actions")
                    or (self._data(value).get("applicability") == "APPLICABLE")
                    == (name == "applicable_actions")
                )
            ]
        payload["uncertainties"] = list(context.required_blocking_factor_ids)
        payload["recommended_next_step"] = next((
            self._serialized(value) for value in context.objects
            if value.object_type == "EVIDENCE_ACQUISITION_PLAN"
        ), None)
        payload["prerequisites"] = (
            payload["recommended_next_step"]["data"].get("prerequisites", [])
            if payload["recommended_next_step"] else []
        )
        payload["allowed_source_ids"] = list(context.allowed_source_ids)
        payload["expected_language"] = context.expected_response_language.value
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _assessment_objects(cls, assessment):
        values = []
        status = assessment.measurement_status
        values.append(cls._object("CAMPAIGN_STATUS", "CAMPAIGN_MEASUREMENT_STATUS", {
            "experiment_states": status.experiment_states,
            "analysis_readiness": tuple(asdict(value) for value in status.analysis_readiness),
            "source_ids": tuple(
                [value[0] for value in status.experiment_states]
                + [f"ANALYSIS_READINESS:{value.family}" for value in status.analysis_readiness]
            ) or ("CAMPAIGN_MEASUREMENT_STATUS",),
        }))
        uncertain_ids = {value.reasoning_id for value in assessment.uncertainties_and_contradictions}
        for finding in assessment.key_findings:
            data = asdict(finding)
            data["source_ids"] = cls._source_ids(finding.provenance)
            data["uncertain"] = finding.reasoning_id in uncertain_ids
            values.append(cls._object("REASONING", finding.reasoning_id, data))
        for action in assessment.currently_applicable_controlled_actions + assessment.actions_not_yet_justified:
            data = asdict(action)
            data["source_ids"] = cls._source_ids(action.provenance)
            values.append(cls._object("ACTION", action.action_id, data))
        if assessment.recommended_next_step is not None:
            step = assessment.recommended_next_step
            data = asdict(step)
            data["source_ids"] = cls._source_ids(step.provenance)
            data["prerequisites"] = assessment.prerequisites
            values.append(cls._object("EVIDENCE_ACQUISITION_PLAN", step.plan_id, data))
        for index, boundary in enumerate(assessment.scientific_boundaries, start=1):
            source_id = f"SCIENTIFIC_BOUNDARY:{index}"
            values.append(cls._object("SCIENTIFIC_BOUNDARY", source_id, {
                "statement": boundary, "source_ids": (source_id,),
            }))
        return tuple(values)

    @staticmethod
    def _source_ids(provenance):
        return tuple(dict.fromkeys(value.source_id for value in provenance))

    @staticmethod
    def _object(object_type, object_id, data):
        return AdvisorContextObject(
            object_id=object_id,
            object_type=object_type,
            canonical_json=json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            referenced_object_ids=tuple(data.get("source_ids", ())),
        )

    @staticmethod
    def _data(value):
        return json.loads(value.canonical_json)

    @classmethod
    def _serialized(cls, value):
        data = cls._data(value)
        return {"source_id": value.object_id, "source_ids": data.get("source_ids", []), "data": data}

    @classmethod
    def _label(cls, value):
        data = cls._data(value)
        return str(data.get("title") or data.get("objective") or data.get("statement") or value.object_id)
