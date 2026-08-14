from dataclasses import dataclass
from pathlib import Path

from acousticbrain.models import CausalProtocolStep, ExperimentKind
from acousticbrain.persistence import MeasurementRepository


@dataclass(frozen=True)
class _StepContract:
    index: int
    required_changed: tuple[str, ...]
    required_controlled: tuple[str, ...]
    observation_codes: tuple[str, ...]


class CausalProtocolStepDeclarationService:
    """Persiste une étape causale explicitement déclarée par l'utilisateur."""

    PROTOCOL_CODE = "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    STEP_CONTRACTS = {
        "STEP_0_BASELINE": _StepContract(
            index=0,
            required_changed=(),
            required_controlled=("MEASUREMENT_LEVEL", "ROOM_CONFIGURATION"),
            observation_codes=("ANOMALY_NOT_REPRODUCIBLE",),
        ),
        "STEP_1_LEFT_RIGHT_REMEASUREMENT": _StepContract(
            index=1,
            required_changed=("MEASUREMENT_ACQUISITION",),
            required_controlled=(
                "LOUDSPEAKER_ASSIGNMENT",
                "MICROPHONE_POSITION",
                "ROOM_SIDE",
                "SIGNAL_CHAIN_ASSIGNMENT",
            ),
            observation_codes=(
                "ANOMALY_NOT_REPRODUCIBLE",
                "CHANNEL_SPECIFIC_PATTERN_CHANGED",
                "CHANNEL_SPECIFIC_PATTERN_STABLE",
                "LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE",
            ),
        ),
        "STEP_2_SPEAKER_SWAP": _StepContract(
            index=2,
            required_changed=("LOUDSPEAKER_ASSIGNMENT",),
            required_controlled=("ROOM_SIDE", "SIGNAL_CHAIN_ASSIGNMENT"),
            observation_codes=(
                "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER",
                "ANOMALY_NOT_REPRODUCIBLE",
                "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP",
            ),
        ),
        "STEP_3_SIGNAL_CHAIN_SWAP": _StepContract(
            index=3,
            required_changed=("SIGNAL_CHAIN_ASSIGNMENT",),
            required_controlled=("LOUDSPEAKER_ASSIGNMENT", "ROOM_SIDE"),
            observation_codes=(
                "ANOMALY_MOVED_WITH_SWAPPED_SIGNAL_CHAIN",
                "ANOMALY_NOT_REPRODUCIBLE",
                "ANOMALY_REMAINED_WITH_LOUDSPEAKER_AFTER_SIGNAL_CHAIN_SWAP",
                "ANOMALY_REMAINED_WITH_LOUDSPEAKER_OR_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP",
                "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP",
            ),
        ),
    }

    def __init__(self, repository=None):
        self.repository = repository or MeasurementRepository()

    def declare(
        self,
        measurement_root,
        *,
        experiment_code,
        protocol_code,
        step_code,
        step_index=None,
        changed_variable_codes=(),
        controlled_variable_codes=(),
        unknown_variable_codes=(),
        observation_codes=(),
        user_note=None,
        provenance_source="USER_CLI",
    ):
        root = Path(measurement_root)
        directory = root / experiment_code
        if not directory.is_dir():
            raise ValueError(f"Unknown experiment directory: {experiment_code}")
        manifest = self.repository.load_manifest(directory)
        if manifest is None:
            raise ValueError(f"Missing or invalid manifest: {experiment_code}")
        if manifest.get("state") != "READY":
            raise ValueError(f"Experiment is not READY: {experiment_code}")
        if protocol_code != self.PROTOCOL_CODE:
            raise ValueError(f"Unsupported causal protocol: {protocol_code}")
        contract = self.STEP_CONTRACTS.get(step_code)
        if contract is None:
            raise ValueError(f"Unsupported causal protocol step: {step_code}")
        effective_index = contract.index if step_index is None else step_index
        if effective_index != contract.index:
            raise ValueError(
                f"Incorrect step index for {step_code}: expected {contract.index}"
            )

        changed = self._codes(changed_variable_codes)
        controlled = self._codes(controlled_variable_codes)
        unknown = self._codes(unknown_variable_codes)
        observations = self._codes(observation_codes)
        missing_changed = set(contract.required_changed) - set(changed)
        missing_controlled = set(contract.required_controlled) - set(controlled)
        if missing_changed:
            raise ValueError(
                "Missing required changed variable(s): "
                + ", ".join(sorted(missing_changed))
            )
        if step_code == "STEP_0_BASELINE" and changed:
            raise ValueError("STEP_0_BASELINE cannot declare a changed variable.")
        if missing_controlled:
            raise ValueError(
                "Missing required controlled variable(s): "
                + ", ".join(sorted(missing_controlled))
            )
        self._validate_observations(step_code, observations)
        self._validate_experiment_declaration(
            manifest,
            changed=changed,
            controlled=controlled,
            unknown=unknown,
        )

        step = CausalProtocolStep(
            protocol_code=protocol_code,
            step_code=step_code,
            step_index=effective_index,
            experiment_id=experiment_code,
            controlled_variable_codes=controlled,
            changed_variable_codes=changed,
            unknown_variable_codes=unknown,
            observation_codes=observations,
        )
        manifest["causal_protocol_step"] = {
            "protocol_code": step.protocol_code,
            "step_code": step.step_code,
            "step_index": step.step_index,
            "controlled_variable_codes": list(step.controlled_variable_codes),
            "changed_variable_codes": list(step.changed_variable_codes),
            "unknown_variable_codes": list(step.unknown_variable_codes),
            "observation_codes": list(step.observation_codes),
        }
        if user_note is not None:
            self._set_explicit_user_note(
                manifest,
                user_note=user_note,
                provenance_source=provenance_source,
            )
        self.repository.save_manifest(directory, manifest)
        return step

    @classmethod
    def _validate_observations(cls, step_code, observations):
        known = {
            code
            for contract in cls.STEP_CONTRACTS.values()
            for code in contract.observation_codes
        }
        allowed = set(cls.STEP_CONTRACTS[step_code].observation_codes)
        for code in observations:
            if code not in known:
                raise ValueError(f"Unknown causal observation: {code}")
            if code not in allowed:
                raise ValueError(
                    f"Causal observation {code} does not belong to {step_code}"
                )

    @staticmethod
    def _validate_experiment_declaration(
        manifest,
        *,
        changed,
        controlled,
        unknown,
    ):
        declaration = manifest.get("experiment_declaration")
        if declaration is None:
            return
        if not isinstance(declaration, dict):
            raise ValueError("Invalid experiment_declaration in manifest.")
        try:
            kind = ExperimentKind(declaration.get("experiment_kind", "UNKNOWN"))
        except ValueError as error:
            raise ValueError("Invalid experiment_declaration kind.") from error
        if kind is ExperimentKind.UNKNOWN:
            return
        declared_modified = set(declaration.get("modified_variables", ()))
        declared_controlled = set(declaration.get("controlled_variables", ()))
        if set(changed) != declared_modified:
            raise ValueError(
                "Causal changed variables do not match experiment_declaration "
                "modified_variables."
            )
        if not set(controlled).issubset(declared_controlled):
            missing = set(controlled) - declared_controlled
            raise ValueError(
                "Causal controlled variables are not declared as controlled: "
                + ", ".join(sorted(missing))
            )
        if set(unknown) & (declared_modified | declared_controlled):
            raise ValueError(
                "Causal unknown variables conflict with experiment_declaration."
            )

    @staticmethod
    def _set_explicit_user_note(manifest, *, user_note, provenance_source):
        declaration = manifest.get("experiment_declaration")
        if not isinstance(declaration, dict):
            raise ValueError(
                "--note requires an existing experiment_declaration."
            )
        note = user_note.strip() if isinstance(user_note, str) else ""
        declaration["user_note"] = note or None
        provenance = declaration.get("field_provenance", {})
        if not isinstance(provenance, dict):
            provenance = {}
        provenance["user_note"] = provenance_source
        declaration["field_provenance"] = provenance

    @staticmethod
    def _codes(values):
        normalized = []
        for raw in values:
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError("Causal protocol codes must be non-empty strings.")
            normalized.append(raw.strip())
        return tuple(sorted(set(normalized)))
