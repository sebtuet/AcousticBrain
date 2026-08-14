from .context import AdvisorContextBuilder
from .errors import AdvisorProviderUnavailableError
from .validation import AdvisorResponseValidator
from acousticbrain.models import AdvisorResponseLanguage


class AdvisorService:
    def __init__(self, *, context_builder=None, validator=None):
        self.context_builder = context_builder or AdvisorContextBuilder()
        self.validator = validator or AdvisorResponseValidator()

    def advise(
        self,
        report,
        *,
        question,
        audience,
        detail_level,
        provider,
        selected_object_ids=(),
        expected_response_language=None,
    ):
        if not provider.is_available():
            raise AdvisorProviderUnavailableError(
                f"Advisor provider '{provider.provider_id}' is unavailable."
            )
        expected_response_language = (
            expected_response_language or self._language_from_question(question)
        )
        request = self.context_builder.request(
            report,
            question=question,
            audience=audience,
            detail_level=detail_level,
            provider_configuration_reference=f"advisor-provider.{provider.provider_id}",
            selected_object_ids=selected_object_ids,
            expected_response_language=expected_response_language,
        )
        projection = self.context_builder.serialize(request.deterministic_context)
        output = provider.generate(request, projection)
        return self.validator.validate(request, provider, output)

    @staticmethod
    def _language_from_question(question):
        normalized = question.casefold()
        markers = (
            "é", "è", "à", "ç", "ù", "résume", "explique", "pourquoi",
            "aucune", "quel", "quelle", "prêt", "bloqué", "français",
        )
        return (
            AdvisorResponseLanguage.FR
            if any(value in normalized for value in markers)
            else AdvisorResponseLanguage.EN
        )
