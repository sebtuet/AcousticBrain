from acousticbrain.analysis import RoomGeometryBuilder
from acousticbrain.models import (
    ExperimentDescriptor,
    ExperimentType,
    SBIRRoomGeometryDeclarationInput,
    SBIRRoomGeometryResolution,
)


class SBIRRoomGeometryResolver:
    """Resolve and validate one declared baseline geometry without recording it."""

    EXPECTED_SPEAKER_IDS = frozenset(("LEFT", "RIGHT"))
    EXPECTED_LISTENING_POSITION_IDS = frozenset(("LISTENING_POSITION",))
    EXPECTED_QUALITY_IDS = frozenset(
        (
            "LEFT",
            "RIGHT",
            "LISTENING_POSITION",
            "front_wall",
            "rear_wall",
            "left_wall",
            "right_wall",
            "floor",
            "ceiling",
        )
    )

    def __init__(self, geometry_builder=None):
        self.geometry_builder = geometry_builder or RoomGeometryBuilder()

    def resolve(self, declaration_input, *, experiments):
        if not isinstance(
            declaration_input, SBIRRoomGeometryDeclarationInput
        ):
            raise TypeError("SBIRRoomGeometryDeclarationInput is required.")
        experiments = self._typed_experiments(experiments)
        baseline = self._resolve_baseline(
            experiments, declaration_input.target_experiment_id
        )

        description = declaration_input.room_description
        self._require_exact_set(
            actual=(item.speaker_id for item in description.speakers),
            expected=self.EXPECTED_SPEAKER_IDS,
            label="SPEAKERS",
        )
        self._require_exact_set(
            actual=(
                item.position_id for item in description.listening_positions
            ),
            expected=self.EXPECTED_LISTENING_POSITION_IDS,
            label="LISTENING_POSITIONS",
        )

        validation = self.geometry_builder.validator.validate(description)
        if not validation.is_valid:
            details = "; ".join(
                self._validation_error_text(error)
                for error in validation.errors
            )
            raise ValueError(
                "SBIR_ROOM_GEOMETRY_RELATIONALLY_INVALID: " + details
            )
        room_geometry = self.geometry_builder.from_description(description)

        self._require_exact_set(
            actual=(item.datum_id for item in description.geometry_data_quality),
            expected=self.EXPECTED_QUALITY_IDS,
            label="QUALITY",
        )

        return SBIRRoomGeometryResolution(
            declaration_input=declaration_input,
            baseline_experiment=baseline,
            room_geometry=room_geometry,
            decisions=SBIRRoomGeometryResolution.EXPECTED_DECISIONS,
        )

    @staticmethod
    def _typed_experiments(experiments):
        if not isinstance(experiments, tuple):
            raise TypeError(
                "SBIR room-geometry experiments must be a typed tuple."
            )
        if any(
            not isinstance(experiment, ExperimentDescriptor)
            for experiment in experiments
        ):
            raise TypeError(
                "SBIR room-geometry experiments contain an invalid object."
            )
        return experiments

    @staticmethod
    def _resolve_baseline(experiments, expected_id):
        matches = tuple(
            experiment
            for experiment in experiments
            if experiment.experiment_id == expected_id
        )
        if not matches:
            raise ValueError(
                f"SBIR_ROOM_GEOMETRY_BASELINE_UNKNOWN: {expected_id}."
            )
        if len(matches) != 1:
            raise ValueError(
                f"SBIR_ROOM_GEOMETRY_BASELINE_AMBIGUOUS: {expected_id}."
            )
        baseline = matches[0]
        if baseline.experiment_type is not ExperimentType.BASELINE:
            raise ValueError(
                f"SBIR_ROOM_GEOMETRY_BASELINE_TYPE_MISMATCH: {expected_id}."
            )
        return baseline

    @classmethod
    def _require_exact_set(cls, *, actual, expected, label):
        actual = frozenset(actual)
        if actual == expected:
            return
        missing = ",".join(sorted(expected - actual)) or "none"
        extra = ",".join(sorted(actual - expected)) or "none"
        raise ValueError(
            f"SBIR_ROOM_GEOMETRY_{label}_NOT_EXACT: "
            f"missing={missing}; extra={extra}."
        )

    @staticmethod
    def _validation_error_text(error):
        entity_ids = ",".join(error.entity_ids)
        fields = ",".join(error.fields) or "none"
        return (
            f"{error.code.value}[{error.entity_type.value}:{entity_ids};"
            f"fields={fields}]"
        )
