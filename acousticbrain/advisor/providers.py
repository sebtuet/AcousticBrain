import json
import socket
from abc import ABC, abstractmethod
from enum import Enum
from urllib import error, request as urlrequest

from acousticbrain.models import AdvisorClaim, AdvisorProviderOutput

from .errors import (
    AdvisorConfigurationError,
    AdvisorProviderResponseError,
    AdvisorProviderUnavailableError,
    AdvisorResponseSchemaError,
    AdvisorTimeoutError,
)
from .prompt import ADVISOR_SYSTEM_PROMPT, ADVISOR_SYSTEM_PROMPT_ID


class AdvisorProvider(ABC):
    provider_id = "abstract"
    model_id = None

    @abstractmethod
    def is_available(self):
        raise NotImplementedError

    @abstractmethod
    def generate(self, request, context_projection):
        raise NotImplementedError


class JsonHttpClient(ABC):
    @abstractmethod
    def post_json(self, url, *, headers, payload, timeout_seconds):
        raise NotImplementedError


class UrllibJsonHttpClient(JsonHttpClient):
    def post_json(self, url, *, headers, payload, timeout_seconds):
        encoded = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(url, data=encoded, headers=headers, method="POST")
        try:
            with urlrequest.urlopen(req, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (TimeoutError, socket.timeout) as exc:
            raise AdvisorTimeoutError("Advisor provider request timed out.") from exc
        except error.HTTPError as exc:
            raise AdvisorProviderResponseError(
                f"Advisor provider returned HTTP {exc.code}."
            ) from exc
        except error.URLError as exc:
            raise AdvisorProviderUnavailableError(
                "Advisor provider is unavailable."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdvisorResponseSchemaError(
                "Advisor provider returned invalid JSON."
            ) from exc


class MockAdvisorMode(Enum):
    COMPLIANT = "compliant"
    HALLUCINATION = "hallucination"
    UNKNOWN_REFERENCE = "unknown_reference"
    OMIT_BLOCKING = "omit_blocking"
    CONTRADICT_BLOCKING = "contradict_blocking"
    RESOLVE_CONTRADICTION = "resolve_contradiction"
    GLOBAL_SCORE = "global_score"
    NEW_ACTION = "new_action"
    DENY_LIMITATION = "deny_limitation"
    INVENT_GEOMETRY = "invent_geometry"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class MockAdvisorProvider(AdvisorProvider):
    provider_id = "mock"
    model_id = "mock-deterministic-v1"

    def __init__(self, mode=MockAdvisorMode.COMPLIANT):
        self.mode = mode

    def is_available(self):
        return True

    def generate(self, request, context_projection):
        if self.mode is MockAdvisorMode.FAILURE:
            raise AdvisorProviderResponseError("Simulated advisor provider failure.")
        if self.mode is MockAdvisorMode.TIMEOUT:
            raise AdvisorTimeoutError("Simulated advisor provider timeout.")
        context = request.deterministic_context
        object_ids = tuple(value.object_id for value in context.objects)
        weights = tuple(
            value.object_id for value in context.objects if value.object_type == "EVIDENCE_WEIGHT"
        )
        support = weights or object_ids[:1]
        output = AdvisorProviderOutput(
            answer=self._answer(request),
            referenced_object_ids=object_ids,
            claims=(
                AdvisorClaim(
                    text="The answer restates only the supplied deterministic objects.",
                    supporting_object_ids=support,
                    asserted_blocking_factors=context.blocking_factors,
                    asserted_contradictions=context.contradictions,
                    asserted_limitations=context.limitations,
                ),
            ) if support else (),
            blocking_factors=context.blocking_factors,
            contradictions=context.contradictions,
            limitations=context.limitations,
        )
        if self.mode is MockAdvisorMode.HALLUCINATION:
            return AdvisorProviderOutput(
                **{**output.__dict__, "claims": (
                    AdvisorClaim(
                        "An ungrounded scientific claim.",
                        ("UNKNOWN_EVIDENCE",),
                        asserted_evidence=("invented.evidence",),
                    ),
                )}
            )
        if self.mode is MockAdvisorMode.UNKNOWN_REFERENCE:
            return AdvisorProviderOutput(
                **{**output.__dict__, "referenced_object_ids": (*object_ids, "UNKNOWN_OBJECT")}
            )
        if self.mode is MockAdvisorMode.OMIT_BLOCKING:
            return AdvisorProviderOutput(**{**output.__dict__, "blocking_factors": ()})
        if self.mode is MockAdvisorMode.CONTRADICT_BLOCKING:
            blocked_actions = self._blocked_actions(context)
            claim = AdvisorClaim(
                "A blocked action is applicable.",
                support,
                asserted_action_applicability=tuple(
                    (value, "APPLICABLE") for value in blocked_actions
                ),
            )
            return AdvisorProviderOutput(**{**output.__dict__, "claims": (claim,)})
        if self.mode is MockAdvisorMode.RESOLVE_CONTRADICTION:
            return AdvisorProviderOutput(**{**output.__dict__, "contradictions": ()})
        if self.mode is MockAdvisorMode.GLOBAL_SCORE:
            return AdvisorProviderOutput(
                **{**output.__dict__, "introduced_scores": ("global_confidence=92%",)}
            )
        if self.mode is MockAdvisorMode.NEW_ACTION:
            return AdvisorProviderOutput(
                **{**output.__dict__, "proposed_action_ids": ("ACTION_INVENTED",)}
            )
        if self.mode is MockAdvisorMode.DENY_LIMITATION:
            return AdvisorProviderOutput(
                **{**output.__dict__, "answer": "The limitation is resolved."}
            )
        if self.mode is MockAdvisorMode.INVENT_GEOMETRY:
            return AdvisorProviderOutput(
                **{**output.__dict__, "answer": "Move the treatment by 40 cm."}
            )
        return output

    @staticmethod
    def _answer(request):
        context = request.deterministic_context
        if not context.objects:
            return "The deterministic engine does not provide information for this question."
        if context.blocking_factors:
            return (
                "The deterministic evidence remains subject to these blocking factors: "
                + "; ".join(context.blocking_factors)
                + ". No blocked action is presented as applicable."
            )
        return "The supplied deterministic objects contain no preserved blocking factor."

    @staticmethod
    def _blocked_actions(context):
        values = []
        for item in context.objects:
            if item.object_type != "ACTION":
                continue
            data = json.loads(item.canonical_json)
            if data.get("applicability", "").startswith("BLOCKED"):
                values.append(item.object_id)
        return tuple(values)


class _HttpAdvisorProvider(AdvisorProvider):
    def __init__(self, *, endpoint, model_id, timeout_seconds=30.0, http_client=None):
        self.endpoint = endpoint
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client or UrllibJsonHttpClient()
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise AdvisorConfigurationError("Advisor timeout must be positive.")

    def is_available(self):
        return bool(self.endpoint and self.model_id)

    def _require_configuration(self):
        if not self.is_available():
            raise AdvisorConfigurationError(
                f"{self.provider_id} advisor configuration is incomplete."
            )


class OllamaAdvisorProvider(_HttpAdvisorProvider):
    provider_id = "ollama"

    def generate(self, request, context_projection):
        self._require_configuration()
        grounding_values = self._required_grounding_values(request)
        response_schema = provider_output_json_schema(grounding_values)
        response = self.http_client.post_json(
            self.endpoint.rstrip("/") + "/api/generate",
            headers={"Content-Type": "application/json"},
            payload={
                "model": self.model_id,
                "system": ADVISOR_SYSTEM_PROMPT,
                "prompt": self._user_prompt(
                    request,
                    context_projection,
                    response_schema=response_schema,
                    grounding_values=grounding_values,
                ),
                "format": response_schema,
                "stream": False,
            },
            timeout_seconds=self.timeout_seconds,
        )
        raw = response.get("response")
        if not isinstance(raw, str) or not raw.strip():
            raise AdvisorProviderResponseError("Ollama returned an empty response.")
        return parse_provider_output(raw)

    @staticmethod
    def _user_prompt(
        request,
        context_projection,
        *,
        response_schema=None,
        grounding_values=None,
    ):
        payload = {
            "prompt_id": ADVISOR_SYSTEM_PROMPT_ID,
            "question": request.question,
            "audience": request.requested_audience.value,
            "detail": request.requested_detail_level.value,
            "deterministic_context": json.loads(context_projection),
        }
        if response_schema is not None:
            payload["required_response_schema"] = response_schema
            payload["required_grounding_values"] = grounding_values
            payload["response_rules"] = (
                "Copy required_grounding_values exactly into the corresponding "
                "response fields. Do not shorten, translate, reorder or extend "
                "those arrays. Use the exact supplied claim object. Write answer "
                "using only those preserved facts and object ids. Do not introduce "
                "numbers, measurements, scores, actions or scientific facts."
            )
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        )

    @staticmethod
    def _required_grounding_values(request):
        context = request.deterministic_context
        object_ids = tuple(value.object_id for value in context.objects)
        supporting_ids = tuple(
            value.object_id
            for value in context.objects
            if value.object_type == "EVIDENCE_WEIGHT"
        ) or object_ids[:1]
        claims = []
        if supporting_ids:
            claims.append(
                {
                    "text": (
                        "The answer restates only the supplied deterministic objects."
                    ),
                    "supporting_object_ids": list(supporting_ids),
                    "asserted_action_applicability": [],
                    "asserted_weight_dimensions": [],
                    "asserted_evidence": [],
                    "asserted_blocking_factors": list(context.blocking_factors),
                    "asserted_contradictions": list(context.contradictions),
                    "asserted_limitations": list(context.limitations),
                }
            )
        return {
            "referenced_object_ids": list(object_ids),
            "claims": claims,
            "blocking_factors": list(context.blocking_factors),
            "contradictions": list(context.contradictions),
            "limitations": list(context.limitations),
            "proposed_action_ids": [],
            "introduced_scores": [],
        }


class OpenAIAdvisorProvider(_HttpAdvisorProvider):
    provider_id = "openai"

    def __init__(self, *, api_key, endpoint, model_id, timeout_seconds=30.0, http_client=None):
        super().__init__(
            endpoint=endpoint,
            model_id=model_id,
            timeout_seconds=timeout_seconds,
            http_client=http_client,
        )
        self._api_key = api_key

    def is_available(self):
        return bool(self._api_key) and super().is_available()

    def generate(self, request, context_projection):
        self._require_configuration()
        response = self.http_client.post_json(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            payload={
                "model": self.model_id,
                "input": [
                    {"role": "system", "content": ADVISOR_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": OllamaAdvisorProvider._user_prompt(
                            request, context_projection
                        ),
                    },
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "advisor_provider_output",
                        "strict": True,
                        "schema": provider_output_json_schema(),
                    }
                },
            },
            timeout_seconds=self.timeout_seconds,
        )
        raw = response.get("output_text") or self._nested_output_text(response)
        if not isinstance(raw, str) or not raw.strip():
            raise AdvisorProviderResponseError("OpenAI returned an empty response.")
        return parse_provider_output(raw)

    @staticmethod
    def _nested_output_text(response):
        for output in response.get("output", ()):
            for content in output.get("content", ()):
                if content.get("type") == "output_text":
                    return content.get("text")
        return None


def parse_provider_output(raw):
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as exc:
        raise AdvisorResponseSchemaError("Advisor output is not valid JSON.") from exc
    required = {
        "answer",
        "referenced_object_ids",
        "claims",
        "blocking_factors",
        "contradictions",
        "limitations",
        "proposed_action_ids",
        "introduced_scores",
    }
    if not isinstance(data, dict) or set(data) != required:
        raise AdvisorResponseSchemaError("Advisor output schema fields are invalid.")
    try:
        claims = tuple(
            AdvisorClaim(
                text=value["text"],
                supporting_object_ids=tuple(value["supporting_object_ids"]),
                asserted_action_applicability=tuple(
                    tuple(item) for item in value["asserted_action_applicability"]
                ),
                asserted_weight_dimensions=tuple(
                    tuple(item) for item in value["asserted_weight_dimensions"]
                ),
                asserted_evidence=tuple(value["asserted_evidence"]),
                asserted_blocking_factors=tuple(value["asserted_blocking_factors"]),
                asserted_contradictions=tuple(value["asserted_contradictions"]),
                asserted_limitations=tuple(value["asserted_limitations"]),
            )
            for value in data["claims"]
        )
        return AdvisorProviderOutput(
            answer=data["answer"],
            referenced_object_ids=tuple(data["referenced_object_ids"]),
            claims=claims,
            blocking_factors=tuple(data["blocking_factors"]),
            contradictions=tuple(data["contradictions"]),
            limitations=tuple(data["limitations"]),
            proposed_action_ids=tuple(data["proposed_action_ids"]),
            introduced_scores=tuple(data["introduced_scores"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AdvisorResponseSchemaError("Advisor output structure is invalid.") from exc


def provider_output_json_schema(required_grounding_values=None):
    claim = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "text",
            "supporting_object_ids",
            "asserted_action_applicability",
            "asserted_weight_dimensions",
            "asserted_evidence",
            "asserted_blocking_factors",
            "asserted_contradictions",
            "asserted_limitations",
        ],
        "properties": {
            "text": {"type": "string"},
            "supporting_object_ids": {"type": "array", "items": {"type": "string"}},
            "asserted_action_applicability": {
                "type": "array",
                "items": {
                    "type": "array",
                    "prefixItems": [{"type": "string"}, {"type": "string"}],
                    "minItems": 2,
                    "maxItems": 2,
                },
            },
            "asserted_weight_dimensions": {
                "type": "array",
                "items": {
                    "type": "array",
                    "prefixItems": [
                        {"type": "string"},
                        {"type": "string"},
                        {"type": "string"},
                    ],
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
            "asserted_evidence": {"type": "array", "items": {"type": "string"}},
            "asserted_blocking_factors": {"type": "array", "items": {"type": "string"}},
            "asserted_contradictions": {"type": "array", "items": {"type": "string"}},
            "asserted_limitations": {"type": "array", "items": {"type": "string"}},
        },
    }
    string_array = {"type": "array", "items": {"type": "string"}}
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "answer",
            "referenced_object_ids",
            "claims",
            "blocking_factors",
            "contradictions",
            "limitations",
            "proposed_action_ids",
            "introduced_scores",
        ],
        "properties": {
            "answer": {"type": "string"},
            "referenced_object_ids": string_array,
            "claims": {"type": "array", "items": claim},
            "blocking_factors": string_array,
            "contradictions": string_array,
            "limitations": string_array,
            "proposed_action_ids": string_array,
            "introduced_scores": string_array,
        },
    }
    if required_grounding_values is not None:
        expected = set(schema["required"]) - {"answer"}
        if set(required_grounding_values) != expected:
            raise AdvisorConfigurationError(
                "Ollama grounding values do not match the provider schema."
            )
        for field, value in required_grounding_values.items():
            schema["properties"][field] = {"const": value}
    return schema
