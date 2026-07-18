from dataclasses import FrozenInstanceError
from inspect import getsource
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.advisor import (
    AdvisorContextBuilder,
    AdvisorProviderResponseError,
    AdvisorProviderUnavailableError,
    AdvisorResponseSchemaError,
    AdvisorService,
    AdvisorTimeoutError,
    MockAdvisorMode,
    MockAdvisorProvider,
    OllamaAdvisorProvider,
    OpenAIAdvisorProvider,
)
from acousticbrain.advisor.providers import parse_provider_output
from acousticbrain.models import (
    AdvisorAudience,
    AdvisorDetailLevel,
    AdvisorValidationStatus,
)
from acousticbrain.report import Report


class Item(SimpleNamespace):
    def to_dict(self):
        return dict(self.__dict__)


def deterministic_report():
    report = Report(project_name="campaign")
    observation = Item(
        observation_id="OBSERVATION_A",
        confidence=80.0,
        supporting_evidence=("evidence.a",),
        contradicting_evidence=("counter.a",),
        limitations=("observation.limit",),
        source_analysis_ids=("AnalysisA",),
    )
    reasoning = Item(
        reasoning_id="REASONING_A",
        observation_ids=("OBSERVATION_A",),
        conclusion="CONTRADICTORY_EVIDENCE",
        supporting_evidence=("evidence.a",),
        contradicting_evidence=("counter.a",),
        limitations=("reasoning.limit",),
    )
    action = Item(
        action_id="ACTION_A",
        source_reasoning_ids=("REASONING_A",),
        source_observation_ids=("OBSERVATION_A",),
        applicability="BLOCKED_BY_MISSING_PARAMETERS",
        required_missing_parameters=("compatible_protocol_or_plan_id",),
        contradictions=("counter.a",),
        limitations=("action.limit",),
    )
    factor = {
        "factor_id": "blocking.action_a.missing",
        "code": "MISSING_PARAMETERS",
        "source_object_ids": ("compatible_protocol_or_plan_id",),
        "justification": "Existing upstream state exposes missing parameters.",
    }
    weight = Item(
        weight_id="EVIDENCE_WEIGHT_ACTION_A",
        evidence_strength="HIGH",
        source_consistency="LOW",
        discriminative_power="HIGH",
        parameter_completeness="LOW",
        action_applicability="BLOCKED",
        action_references=("ACTION_A",),
        reasoning_references=("REASONING_A",),
        observation_references=("OBSERVATION_A",),
        supporting_evidence=("evidence.a",),
        contradicting_evidence=("counter.a",),
        limitations=("weight.limit",),
        blocking_factors=(factor,),
    )
    report.acoustic_observations = SimpleNamespace(observations=(observation,))
    report.deterministic_acoustic_reasoning = SimpleNamespace(reasonings=(reasoning,))
    report.deterministic_corrective_actions = SimpleNamespace(actions=(action,))
    report.deterministic_evidence_weighting = SimpleNamespace(weights=(weight,))
    return report


def advise(mode=MockAdvisorMode.COMPLIANT):
    return AdvisorService().advise(
        deterministic_report(),
        question="Why is this action blocked?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider=MockAdvisorProvider(mode),
    )


def test_request_context_and_response_are_immutable_and_stable():
    builder = AdvisorContextBuilder()
    first = builder.request(
        deterministic_report(),
        question="Why?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider_configuration_reference="advisor-provider.mock",
    )
    second = builder.request(
        deterministic_report(),
        question="Why?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider_configuration_reference="advisor-provider.mock",
    )

    assert first == second
    assert builder.serialize(first.deterministic_context) == builder.serialize(
        second.deterministic_context
    )
    with pytest.raises(FrozenInstanceError):
        first.question = "changed"
    response = advise()
    with pytest.raises(FrozenInstanceError):
        response.answer_text = "changed"


def test_context_selection_follows_weight_to_full_upstream_chain():
    context = AdvisorContextBuilder().build(
        deterministic_report(), selected_object_ids=("EVIDENCE_WEIGHT_ACTION_A",)
    )

    assert tuple(value.object_id for value in context.objects) == (
        "OBSERVATION_A",
        "REASONING_A",
        "ACTION_A",
        "EVIDENCE_WEIGHT_ACTION_A",
    )
    assert context.blocking_factors == (
        "MISSING_PARAMETERS:compatible_protocol_or_plan_id",
    )
    assert context.contradictions == ("counter.a",)
    assert context.limitations == (
        "observation.limit",
        "reasoning.limit",
        "action.limit",
        "weight.limit",
    )


def test_context_rejects_unknown_explicit_selection():
    with pytest.raises(ValueError, match="Unknown advisor object"):
        AdvisorContextBuilder().build(
            deterministic_report(), selected_object_ids=("UNKNOWN",)
        )


def test_context_builder_has_no_raw_measurement_file_access():
    source = getsource(AdvisorContextBuilder)

    assert "open(" not in source
    assert "read_text" not in source
    assert "read_bytes" not in source
    assert "measurement_root" not in source


def test_compliant_mock_preserves_block_and_grounding():
    response = advise()

    assert response.validation_status is AdvisorValidationStatus.VALID
    assert "MISSING_PARAMETERS" in response.answer_text
    assert response.preserved_blocking_factors
    assert response.preserved_contradictions == ("counter.a",)
    assert response.referenced_evidence_weight_ids == ("EVIDENCE_WEIGHT_ACTION_A",)


@pytest.mark.parametrize(
    ("mode", "violation"),
    (
        (MockAdvisorMode.HALLUCINATION, "UNGROUNDED_CLAIM"),
        (MockAdvisorMode.UNKNOWN_REFERENCE, "UNKNOWN_REFERENCES"),
        (MockAdvisorMode.OMIT_BLOCKING, "OMITTED_BLOCKING_FACTORS"),
        (MockAdvisorMode.CONTRADICT_BLOCKING, "ACTION_APPLICABILITY_MODIFIED"),
        (MockAdvisorMode.RESOLVE_CONTRADICTION, "OMITTED_CONTRADICTIONS"),
        (MockAdvisorMode.GLOBAL_SCORE, "INTRODUCED_GLOBAL_SCORE"),
        (MockAdvisorMode.NEW_ACTION, "INVENTED_ACTIONS"),
        (MockAdvisorMode.DENY_LIMITATION, "UNGROUNDED_SEMANTIC_OVERRIDE"),
        (MockAdvisorMode.INVENT_GEOMETRY, "INVENTED_GEOMETRY"),
    ),
)
def test_invalid_mock_output_is_intercepted_with_deterministic_safety_response(
    mode, violation
):
    first = advise(mode)
    second = advise(mode)

    assert first == second
    assert first.validation_status is AdvisorValidationStatus.INVALID
    assert first.answer_text.startswith("The advisor could not produce")
    assert any(value.startswith(violation) for value in first.unsupported_claims)
    assert first.preserved_blocking_factors
    assert first.preserved_contradictions


def test_mock_failure_and_timeout_remain_typed_provider_errors():
    with pytest.raises(AdvisorProviderResponseError):
        advise(MockAdvisorMode.FAILURE)
    with pytest.raises(AdvisorTimeoutError):
        advise(MockAdvisorMode.TIMEOUT)


def test_question_outside_empty_context_returns_grounded_unavailable_answer():
    response = AdvisorService().advise(
        Report(project_name="empty"),
        question="Where should a treatment be placed?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.STANDARD,
        provider=MockAdvisorProvider(),
    )

    assert response.validation_status is AdvisorValidationStatus.VALID
    assert "does not provide information" in response.answer_text
    assert response.referenced_object_ids == ()


class RecordingHttpClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post_json(self, url, *, headers, payload, timeout_seconds):
        self.calls.append((url, headers, payload, timeout_seconds))
        return self.response


class RaisingHttpClient:
    def __init__(self, error):
        self.error = error

    def post_json(self, *args, **kwargs):
        raise self.error


def provider_json():
    return {
        "answer": "Grounded answer.",
        "referenced_object_ids": [
            "OBSERVATION_A",
            "REASONING_A",
            "ACTION_A",
            "EVIDENCE_WEIGHT_ACTION_A",
        ],
        "claims": [
            {
                "text": "Grounded claim.",
                "supporting_object_ids": ["EVIDENCE_WEIGHT_ACTION_A"],
                "asserted_action_applicability": [["ACTION_A", "BLOCKED"]],
                "asserted_weight_dimensions": [
                    ["EVIDENCE_WEIGHT_ACTION_A", "EVIDENCE_STRENGTH", "HIGH"]
                ],
                "asserted_evidence": ["evidence.a"],
                "asserted_blocking_factors": [
                    "MISSING_PARAMETERS:compatible_protocol_or_plan_id"
                ],
                "asserted_contradictions": ["counter.a"],
                "asserted_limitations": ["weight.limit"],
            }
        ],
        "blocking_factors": ["MISSING_PARAMETERS:compatible_protocol_or_plan_id"],
        "contradictions": ["counter.a"],
        "limitations": [
            "observation.limit",
            "reasoning.limit",
            "action.limit",
            "weight.limit",
        ],
        "proposed_action_ids": [],
        "introduced_scores": [],
    }


def test_ollama_adapter_uses_injected_http_client_without_real_network():
    client = RecordingHttpClient({"response": __import__("json").dumps(provider_json())})
    provider = OllamaAdvisorProvider(
        endpoint="http://ollama.test",
        model_id="local-model",
        timeout_seconds=4,
        http_client=client,
    )

    response = AdvisorService().advise(
        deterministic_report(),
        question="Why?",
        audience=AdvisorAudience.DEVELOPER,
        detail_level=AdvisorDetailLevel.TECHNICAL,
        provider=provider,
    )

    assert response.validation_status is AdvisorValidationStatus.VALID
    assert client.calls[0][0] == "http://ollama.test/api/generate"
    assert client.calls[0][3] == 4


def test_openai_adapter_uses_responses_structured_output_and_hides_key_from_payload():
    client = RecordingHttpClient({"output_text": __import__("json").dumps(provider_json())})
    provider = OpenAIAdvisorProvider(
        api_key="secret-key",
        endpoint="https://api.openai.test/v1/responses",
        model_id="configured-model",
        timeout_seconds=5,
        http_client=client,
    )

    response = AdvisorService().advise(
        deterministic_report(),
        question="Why?",
        audience=AdvisorAudience.GENERAL,
        detail_level=AdvisorDetailLevel.CONCISE,
        provider=provider,
    )

    _, headers, payload, timeout = client.calls[0]
    assert response.validation_status is AdvisorValidationStatus.VALID
    assert headers["Authorization"] == "Bearer secret-key"
    assert "secret-key" not in repr(payload)
    assert payload["text"]["format"]["type"] == "json_schema"
    assert timeout == 5


@pytest.mark.parametrize(
    ("provider", "error_type"),
    (
        (
            OllamaAdvisorProvider(
                endpoint="http://ollama.test",
                model_id="model",
                http_client=RecordingHttpClient({"response": ""}),
            ),
            AdvisorProviderResponseError,
        ),
        (
            OpenAIAdvisorProvider(
                api_key="key",
                endpoint="https://api.openai.test/v1/responses",
                model_id="model",
                http_client=RecordingHttpClient({"output_text": "not-json"}),
            ),
            AdvisorResponseSchemaError,
        ),
        (
            OllamaAdvisorProvider(
                endpoint="http://ollama.test",
                model_id="model",
                http_client=RaisingHttpClient(AdvisorTimeoutError("timeout")),
            ),
            AdvisorTimeoutError,
        ),
        (
            OpenAIAdvisorProvider(
                api_key="key",
                endpoint="https://api.openai.test/v1/responses",
                model_id="model",
                http_client=RaisingHttpClient(
                    AdvisorProviderResponseError("HTTP error")
                ),
            ),
            AdvisorProviderResponseError,
        ),
    ),
)
def test_real_adapters_expose_empty_invalid_timeout_and_http_errors(
    provider, error_type
):
    with pytest.raises(error_type):
        AdvisorService().advise(
            deterministic_report(),
            question="Why?",
            audience=AdvisorAudience.GENERAL,
            detail_level=AdvisorDetailLevel.STANDARD,
            provider=provider,
        )


@pytest.mark.parametrize(
    "provider",
    (
        OllamaAdvisorProvider(endpoint=None, model_id=None),
        OpenAIAdvisorProvider(
            api_key=None,
            endpoint="https://api.openai.com/v1/responses",
            model_id=None,
        ),
    ),
)
def test_real_provider_missing_configuration_is_unavailable(provider):
    with pytest.raises(AdvisorProviderUnavailableError):
        AdvisorService().advise(
            deterministic_report(),
            question="Why?",
            audience=AdvisorAudience.GENERAL,
            detail_level=AdvisorDetailLevel.STANDARD,
            provider=provider,
        )


@pytest.mark.parametrize("raw", ("", "not-json", "{}"))
def test_provider_output_parser_rejects_empty_malformed_or_incomplete_json(raw):
    with pytest.raises(AdvisorResponseSchemaError):
        parse_provider_output(raw)


class RecordingBrain:
    def __init__(self):
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return deterministic_report()


class RecordingReporter:
    def __init__(self):
        self.responses = []

    def print(self, report):
        self.responses.append(report.advisor_response)


def test_cli_advisor_mock_composes_weighting_and_renders_valid_response(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()
    reporter = RecordingReporter()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--advisor", "--question", "Why?"],
        brain=brain,
        reporter=reporter,
        advisor_provider_instance=MockAdvisorProvider(),
    )

    assert brain.calls[0]["synthesize_weighting"] is True
    assert reporter.responses[0].validation_status is AdvisorValidationStatus.VALID


def test_cli_rejects_question_without_advisor_and_advisor_without_question(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main(
            ["--measurements-root", str(campaign), "--question", "Why?"]
        )
    with pytest.raises(SystemExit):
        acousticbrain_main.main(["--measurements-root", str(campaign), "--advisor"])


def test_historical_cli_never_constructs_or_calls_provider(tmp_path, monkeypatch):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()
    monkeypatch.setattr(
        acousticbrain_main,
        "create_advisor_provider",
        lambda value: pytest.fail("provider must not be initialized"),
    )

    acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert "synthesize_weighting" not in brain.calls[0]
