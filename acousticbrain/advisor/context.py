import hashlib
import json

from acousticbrain.models import (
    AdvisorAudience,
    AdvisorContextObject,
    AdvisorDetailLevel,
    AdvisorDeterministicContext,
    AdvisorRequest,
    AdvisorResponseLanguage,
)


class AdvisorContextBuilder:
    SCHEMA_VERSION = "advisor-context.v2"
    REQUEST_SCHEMA_VERSION = "advisor-request.v2"

    def build(
        self,
        report,
        *,
        selected_object_ids=(),
        expected_response_language=AdvisorResponseLanguage.EN,
    ):
        objects = self._all_objects(report)
        by_id = {value.object_id: value for value in objects}
        requested = tuple(selected_object_ids) or tuple(
            value.object_id
            for value in objects
            if value.object_type in ("EVIDENCE_WEIGHT", "EVIDENCE_ACQUISITION_PLAN")
        )
        unknown = tuple(value for value in requested if value not in by_id)
        if unknown:
            raise ValueError(f"Unknown advisor object ids: {', '.join(unknown)}")
        if requested:
            included = set(requested)
            pending = list(requested)
            while pending:
                current = by_id[pending.pop(0)]
                for reference in current.referenced_object_ids:
                    if reference in by_id and reference not in included:
                        included.add(reference)
                        pending.append(reference)
            objects = tuple(value for value in objects if value.object_id in included)
        blocking, contradictions, limitations = self._preserved(objects)
        requirements = self._requirements(objects)
        return AdvisorDeterministicContext(
            schema_version=self.SCHEMA_VERSION,
            project_id=str(report.project_name),
            objects=objects,
            blocking_factors=blocking,
            contradictions=contradictions,
            limitations=limitations,
            expected_response_language=expected_response_language,
            allowed_object_ids=tuple(value.object_id for value in objects),
            object_labels=tuple(
                (value.object_id, self._label(value)) for value in objects
            ),
            **requirements,
        )

    def request(
        self,
        report,
        *,
        question,
        audience,
        detail_level,
        provider_configuration_reference,
        selected_object_ids=(),
        expected_response_language=AdvisorResponseLanguage.EN,
    ):
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
                "objects": [value.object_id for value in context.objects],
                "provider": provider_configuration_reference,
                "language": expected_response_language.value,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
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
        payload = {
            "schema_version": context.schema_version,
            "project_id": context.project_id,
            "objects": [
                {
                    "object_id": value.object_id,
                    "object_type": value.object_type,
                    "data": json.loads(value.canonical_json),
                    "referenced_object_ids": list(value.referenced_object_ids),
                }
                for value in context.objects
            ],
            "blocking_factors": list(context.blocking_factors),
            "contradictions": list(context.contradictions),
            "limitations": list(context.limitations),
            "expected_response_language": context.expected_response_language.value,
            "required_reasoning_ids": list(context.required_reasoning_ids),
            "required_blocking_factor_ids": list(context.required_blocking_factor_ids),
            "required_ready_plan_ids": list(context.required_ready_plan_ids),
            "required_blocked_plan_ids": list(context.required_blocked_plan_ids),
            "allowed_object_ids": list(context.allowed_object_ids),
            "object_labels": [list(value) for value in context.object_labels],
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _all_objects(self, report):
        values = []
        collections = (
            ("OBSERVATION", report.acoustic_observations, "observations", "observation_id"),
            ("REASONING", report.deterministic_acoustic_reasoning, "reasonings", "reasoning_id"),
            ("ACTION", report.deterministic_corrective_actions, "actions", "action_id"),
            ("EVIDENCE_WEIGHT", report.deterministic_evidence_weighting, "weights", "weight_id"),
            (
                "EVIDENCE_ACQUISITION_PLAN",
                report.evidence_acquisition_plans,
                "plans",
                "plan_id",
            ),
        )
        for object_type, container, attribute, identifier in collections:
            for item in getattr(container, attribute, ()) if container is not None else ():
                data = item.to_dict()
                references = self._references(object_type, data)
                values.append(
                    AdvisorContextObject(
                        object_id=getattr(item, identifier),
                        object_type=object_type,
                        canonical_json=json.dumps(
                            data,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        referenced_object_ids=references,
                    )
                )
        return tuple(values)

    @staticmethod
    def _references(object_type, data):
        keys = {
            "OBSERVATION": (),
            "REASONING": ("observation_ids",),
            "ACTION": ("source_reasoning_ids", "source_observation_ids"),
            "EVIDENCE_WEIGHT": (
                "action_references",
                "reasoning_references",
                "observation_references",
            ),
            "EVIDENCE_ACQUISITION_PLAN": (
                "evidence_weight_id",
                "corrective_action_id",
                "reasoning_id",
            ),
        }[object_type]
        references = []
        for key in keys:
            value = data.get(key, ())
            references.extend(value if isinstance(value, (list, tuple)) else (value,))
        return tuple(dict.fromkeys(references))

    @staticmethod
    def _preserved(objects):
        blocking = []
        contradictions = []
        limitations = []
        for value in objects:
            data = json.loads(value.canonical_json)
            for factor in data.get("blocking_factors", ()):
                sources = ",".join(factor.get("source_object_ids", ()))
                blocking.append(f"{factor['code']}:{sources}")
            contradictions.extend(
                data.get("contradictions", data.get("contradicting_evidence", ()))
            )
            limitations.extend(data.get("limitations", ()))
        return tuple(dict.fromkeys(blocking)), tuple(dict.fromkeys(contradictions)), tuple(
            dict.fromkeys(limitations)
        )

    @staticmethod
    def _requirements(objects):
        reasoning = []
        blocking = []
        ready = []
        blocked = []
        for value in objects:
            data = json.loads(value.canonical_json)
            if value.object_type == "REASONING":
                reasoning.append(value.object_id)
            if value.object_type == "EVIDENCE_WEIGHT":
                blocking.extend(
                    item["factor_id"] for item in data.get("blocking_factors", ())
                )
            if value.object_type == "EVIDENCE_ACQUISITION_PLAN":
                status = data.get("status")
                if status not in ("READY", "BLOCKED"):
                    raise ValueError(
                        f"Advisor plan status is invalid: {value.object_id}:{status}"
                    )
                target = ready if status == "READY" else blocked
                target.append(value.object_id)
        return {
            "required_reasoning_ids": tuple(dict.fromkeys(reasoning)),
            "required_blocking_factor_ids": tuple(dict.fromkeys(blocking)),
            "required_ready_plan_ids": tuple(dict.fromkeys(ready)),
            "required_blocked_plan_ids": tuple(dict.fromkeys(blocked)),
        }

    @staticmethod
    def _label(value):
        data = json.loads(value.canonical_json)
        return str(data.get("title") or data.get("objective") or value.object_id)
