class AdvisorError(Exception):
    pass


class AdvisorDisabledError(AdvisorError):
    pass


class AdvisorConfigurationError(AdvisorError):
    pass


class AdvisorProviderUnavailableError(AdvisorError):
    pass


class AdvisorTimeoutError(AdvisorError):
    pass


class AdvisorProviderResponseError(AdvisorError):
    pass


class AdvisorResponseSchemaError(AdvisorError):
    pass


class AdvisorUnsupportedReferenceError(AdvisorError):
    pass


class AdvisorGroundingViolationError(AdvisorError):
    pass


class AdvisorBlockingFactorViolationError(AdvisorError):
    pass


class AdvisorContradictionViolationError(AdvisorError):
    pass
