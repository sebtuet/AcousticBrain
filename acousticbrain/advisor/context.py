import hashlib
import json

from acousticbrain.models import (
    AdvisorAudience,
    AdvisorContextObject,
    AdvisorDetailLevel,
    AdvisorDeterministicContext,
    AdvisorRequest,
)


class AdvisorContextBuilder:
    SCHEMA_VERSION = "advisor-context.v1"
    REQUEST_SCHEMA_VERSION = "advisor-request.v1"

    def build(self, report, *, selected_object_ids=()):
        objects = self._all_objects(report)
        by_id = {value.object_id: value for value in objects}
        requested = tuple(selected_object_ids) or tuple(
            value.object_id for value in objects if value.object_type == "EVIDENCE_WEIGHT"
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
        return AdvisorDeterministicContext(
            schema_version=self.SCHEMA_VERSION,
            project_id=str(report.project_name),
            objects=objects,
            blocking_factors=blocking,
            contradictions=contradictions,
            limitations=limitations,
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
    ):
        context = self.build(report, selected_object_ids=selected_object_ids)
        identity = json.dumps(
            {
                "question": question,
                "audience": audience.value,
                "detail": detail_level.value,
                "project": context.project_id,
                "objects": [value.object_id for value in context.objects],
                "provider": provider_configuration_reference,
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
        }[object_type]
        return tuple(
            dict.fromkeys(value for key in keys for value in data.get(key, ()))
        )

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
