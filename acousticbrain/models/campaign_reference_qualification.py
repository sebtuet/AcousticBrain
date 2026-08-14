from dataclasses import dataclass
from enum import Enum


class CampaignReferenceAssertionStatus(Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CampaignReferenceDeclarationStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class CampaignReferenceQualificationStatus(Enum):
    QUALIFIED = "QUALIFIED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CampaignReferenceCriterionStatus(Enum):
    SATISFIED = "SATISFIED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CampaignReferenceQualificationValidationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class CampaignReferenceQualificationDeclaration:
    schema_version: int
    qualification_id: str
    experiment_id: str
    intended_protocol_id: str
    intended_protocol_version: int
    intended_campaign_instance_id: str | None
    reference_role: str
    configuration_state: tuple[
        tuple[str, CampaignReferenceAssertionStatus], ...
    ]
    controlled_variable_assertions: tuple[
        tuple[str, CampaignReferenceAssertionStatus], ...
    ]
    required_measurement_assertions: tuple[str, ...]
    declaration_source: str
    declaration_version: int
    notes: str | None

    CURRENT_SCHEMA_VERSION = 1

    def __post_init__(self):
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != self.CURRENT_SCHEMA_VERSION
        ):
            self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                "Unsupported reference qualification schema version.",
            )
        for label, value in (
            ("qualification_id", self.qualification_id),
            ("experiment_id", self.experiment_id),
            ("intended_protocol_id", self.intended_protocol_id),
            ("reference_role", self.reference_role),
            ("declaration_source", self.declaration_source),
        ):
            if not isinstance(value, str) or not value:
                self._invalid(
                    "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                    f"Reference qualification {label} is required.",
                )
        if (
            not isinstance(self.intended_protocol_version, int)
            or isinstance(self.intended_protocol_version, bool)
            or self.intended_protocol_version < 1
            or not isinstance(self.declaration_version, int)
            or isinstance(self.declaration_version, bool)
            or self.declaration_version < 1
        ):
            self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                "Reference qualification versions must be positive integers.",
            )
        if self.intended_campaign_instance_id is not None and (
            not isinstance(self.intended_campaign_instance_id, str)
            or not self.intended_campaign_instance_id
        ):
            self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                "Intended campaign instance id must be a non-empty string or null.",
            )
        if self.reference_role != "REFERENCE":
            self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                "Reference qualification role must be REFERENCE.",
            )
        if self.notes is not None and not isinstance(self.notes, str):
            self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                "Reference qualification notes must be a string or null.",
            )
        self._validate_assertions(
            self.configuration_state, "configuration_state"
        )
        self._validate_assertions(
            self.controlled_variable_assertions,
            "controlled_variable_assertions",
        )
        if (
            not isinstance(self.required_measurement_assertions, tuple)
            or not self.required_measurement_assertions
            or any(
                not isinstance(item, str) or not item
                for item in self.required_measurement_assertions
            )
            or len(self.required_measurement_assertions)
            != len(set(self.required_measurement_assertions))
        ):
            self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                "Required measurement assertions must be unique strings.",
            )
        if dict(self.configuration_state) != dict(
            self.controlled_variable_assertions
        ):
            self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                "Configuration state and controlled assertions must agree exactly.",
            )

    @staticmethod
    def _validate_assertions(values, label):
        if (
            not isinstance(values, tuple)
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or not isinstance(item[1], CampaignReferenceAssertionStatus)
                for item in values
            )
            or len(values) != len({item[0] for item in values})
        ):
            raise CampaignReferenceQualificationValidationError(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                f"Reference qualification {label} is invalid.",
            )

    @staticmethod
    def _invalid(code, message):
        raise CampaignReferenceQualificationValidationError(code, message)


@dataclass(frozen=True)
class CampaignReferenceQualificationDeclarationAnalysis:
    status: CampaignReferenceDeclarationStatus
    declaration: CampaignReferenceQualificationDeclaration | None
    blocking_reasons: tuple[str, ...]
    validation_messages: tuple[str, ...]
    source_path: str | None

    def __post_init__(self):
        if not all(
            isinstance(item, tuple)
            for item in (self.blocking_reasons, self.validation_messages)
        ):
            raise ValueError("Reference declaration validation details must be tuples.")
        if self.status is CampaignReferenceDeclarationStatus.VALID and (
            self.declaration is None
            or self.blocking_reasons
            or self.validation_messages
        ):
            raise ValueError("A VALID reference declaration cannot contain errors.")
        if self.status is CampaignReferenceDeclarationStatus.INVALID and (
            not self.blocking_reasons or not self.validation_messages
        ):
            raise ValueError("An INVALID reference declaration requires errors.")


@dataclass(frozen=True)
class CampaignReferenceQualification:
    qualification_id: str | None
    experiment_id: str | None
    intended_protocol_id: str | None
    intended_protocol_version: int | None
    intended_campaign_instance_id: str | None
    reference_role: str | None
    status: CampaignReferenceQualificationStatus
    supporting_fact_codes: tuple[str, ...]
    contradicting_fact_codes: tuple[str, ...]
    missing_fact_codes: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    required_measurements_status: CampaignReferenceCriterionStatus
    controlled_variables_status: CampaignReferenceCriterionStatus
    protocol_compatibility_status: CampaignReferenceCriterionStatus
    campaign_instance_compatibility_status: CampaignReferenceCriterionStatus
    qualified_controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    causality_status: str
    source_path: str | None

    def __post_init__(self):
        collections = (
            self.supporting_fact_codes,
            self.contradicting_fact_codes,
            self.missing_fact_codes,
            self.blocking_reasons,
            self.qualified_controlled_variables,
            self.required_measurements,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Reference qualification collections must be tuples.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Reference qualification cannot establish causality.")
        if self.status is CampaignReferenceQualificationStatus.QUALIFIED and (
            self.blocking_reasons
            or self.contradicting_fact_codes
            or self.missing_fact_codes
            or not self.qualification_id
            or not self.experiment_id
        ):
            raise ValueError("A QUALIFIED reference must have complete evidence.")
        if self.status in {
            CampaignReferenceQualificationStatus.BLOCKED,
            CampaignReferenceQualificationStatus.INVALID,
        } and not self.blocking_reasons:
            raise ValueError("A blocked reference qualification needs a reason.")
