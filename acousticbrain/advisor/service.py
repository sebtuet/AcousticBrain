from .context import AdvisorContextBuilder
from .errors import AdvisorProviderUnavailableError
from .validation import AdvisorResponseValidator


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
    ):
        if not provider.is_available():
            raise AdvisorProviderUnavailableError(
                f"Advisor provider '{provider.provider_id}' is unavailable."
            )
        request = self.context_builder.request(
            report,
            question=question,
            audience=audience,
            detail_level=detail_level,
            provider_configuration_reference=f"advisor-provider.{provider.provider_id}",
            selected_object_ids=selected_object_ids,
        )
        projection = self.context_builder.serialize(request.deterministic_context)
        output = provider.generate(request, projection)
        return self.validator.validate(request, provider, output)
