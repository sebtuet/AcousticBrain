from dataclasses import dataclass
from pathlib import Path

from acousticbrain.persistence import MeasurementRepository


@dataclass(frozen=True)
class CausalSourceComparisonAssociation:
    experiment_code: str
    parent_experiment_code: str
    source_protocol_id: str
    source_hypothesis_code: str
    causal_step_code: str
    declared_change_codes: tuple[str, ...]
    required_fact_codes: tuple[str, ...]


class CausalSourceComparisonAssociationService:
    """Associe explicitement une comparaison à un protocole causal existant."""

    PROTOCOL_ID = "protocol.verify_speaker_room_asymmetry.v1"
    HYPOTHESIS_CODE = "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"
    CAUSAL_PROTOCOL_CODE = "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    STEP_CHANGE_CODES = {
        "STEP_2_SPEAKER_SWAP": (
            "LOUDSPEAKER_ASSIGNMENT",
            "CONTROLLED_LOUDSPEAKER_SWAP",
        ),
        "STEP_3_SIGNAL_CHAIN_SWAP": (
            "SIGNAL_CHAIN_ASSIGNMENT",
            "CONTROLLED_SIGNAL_CHAIN_SWAP",
        ),
    }
    REQUIRED_FACT_CODES = (
        "bass_decay.left_right.maximum_difference_abs_s",
        "direct_reverberant.left_right.maximum_difference_abs_db",
        "etc.channel_specific_event_count",
        "spatial.left_right.level_difference_abs_db",
    )
    KNOWN_PROTOCOL_IDS = {
        PROTOCOL_ID,
        "protocol.verify_modal_bass_persistence.v1",
        "protocol.temporary_mask_surface.v1",
        "protocol.temporary_move_speaker.v1",
    }
    KNOWN_HYPOTHESIS_CODES = {
        HYPOTHESIS_CODE,
        "DOMINANT_EARLY_REFLECTION_INTERACTION",
        "MODAL_BASS_PERSISTENCE",
        "SBIR_PLACEMENT_INTERACTION",
    }

    def __init__(self, repository=None):
        self.repository = repository or MeasurementRepository()

    def associate(
        self,
        measurement_root,
        *,
        experiment_code,
        source_protocol_id,
        source_hypothesis_code,
        reference_experiment_code=None,
    ):
        directory = Path(measurement_root) / experiment_code
        if not directory.is_dir():
            raise ValueError(f"Unknown experiment directory: {experiment_code}")
        manifest = self.repository.load_manifest(directory)
        if manifest is None:
            raise ValueError(f"Missing or invalid manifest: {experiment_code}")
        if manifest.get("state") != "READY":
            raise ValueError(f"Experiment is not READY: {experiment_code}")
        self._validate_source_codes(source_protocol_id, source_hypothesis_code)

        comparison = manifest.get("comparison")
        if not isinstance(comparison, dict):
            raise ValueError(f"Missing comparison metadata: {experiment_code}")
        parents = self._codes(comparison.get("parent_experiment_ids", ()))
        if not parents:
            raise ValueError("Comparison must declare one parent experiment.")
        if len(parents) != 1:
            raise ValueError("Comparison must declare exactly one parent experiment.")
        parent = parents[0]
        if not (Path(measurement_root) / parent).is_dir():
            raise ValueError(f"Unknown parent experiment directory: {parent}")
        if reference_experiment_code is not None and reference_experiment_code != parent:
            raise ValueError(
                f"Reference experiment contradicts comparison parent: {parent}"
            )

        declaration = self._declaration(manifest, parent)
        step = manifest.get("causal_protocol_step")
        if not isinstance(step, dict):
            raise ValueError(f"Missing causal_protocol_step: {experiment_code}")
        if step.get("protocol_code") != self.CAUSAL_PROTOCOL_CODE:
            raise ValueError("Causal protocol step is incompatible with source protocol.")
        step_code = step.get("step_code")
        contract = self.STEP_CHANGE_CODES.get(step_code)
        if contract is None:
            raise ValueError(f"Unsupported causal source comparison step: {step_code}")
        expected_variable, declared_change = contract
        changed = set(self._codes(step.get("changed_variable_codes", ())))
        modified = set(self._codes(declaration.get("modified_variables", ())))
        if expected_variable not in changed:
            raise ValueError(
                f"{step_code} must change {expected_variable} in causal_protocol_step."
            )
        if expected_variable not in modified:
            raise ValueError(
                f"{step_code} must change {expected_variable} in experiment_declaration."
            )
        if changed != modified:
            raise ValueError(
                "causal_protocol_step changed variables do not match "
                "experiment_declaration modified variables."
            )

        self._reject_conflicting_source(
            comparison,
            key="source_protocol_id",
            expected=source_protocol_id,
        )
        self._reject_conflicting_source(
            comparison,
            key="source_hypothesis_code",
            expected=source_hypothesis_code,
        )
        existing_changes = set(
            self._codes(comparison.get("declared_change_codes", ()))
        )
        incompatible_changes = (
            {value[1] for value in self.STEP_CHANGE_CODES.values()}
            - {declared_change}
        ) & existing_changes
        if incompatible_changes:
            raise ValueError(
                "Comparison already declares an incompatible causal change: "
                + ", ".join(sorted(incompatible_changes))
            )
        parameters = comparison.get("parameters")
        if parameters is not None and not isinstance(parameters, dict):
            raise ValueError("Experiment comparison parameters must be an object.")

        comparison["parent_experiment_ids"] = [parent]
        comparison["source_protocol_id"] = source_protocol_id
        comparison["source_hypothesis_code"] = source_hypothesis_code
        comparison["declared_change_codes"] = sorted(
            existing_changes | {declared_change}
        )
        comparison["required_fact_codes"] = sorted(
            set(self._codes(comparison.get("required_fact_codes", ())))
            | set(self.REQUIRED_FACT_CODES)
        )
        manifest["comparison"] = comparison
        self.repository.save_manifest(directory, manifest)
        return CausalSourceComparisonAssociation(
            experiment_code=experiment_code,
            parent_experiment_code=parent,
            source_protocol_id=source_protocol_id,
            source_hypothesis_code=source_hypothesis_code,
            causal_step_code=step_code,
            declared_change_codes=tuple(comparison["declared_change_codes"]),
            required_fact_codes=tuple(comparison["required_fact_codes"]),
        )

    def _validate_source_codes(self, protocol_id, hypothesis_code):
        if protocol_id not in self.KNOWN_PROTOCOL_IDS:
            raise ValueError(f"Unknown source protocol: {protocol_id}")
        if hypothesis_code not in self.KNOWN_HYPOTHESIS_CODES:
            raise ValueError(f"Unknown source hypothesis: {hypothesis_code}")
        if (protocol_id, hypothesis_code) != (
            self.PROTOCOL_ID,
            self.HYPOTHESIS_CODE,
        ):
            raise ValueError(
                "Source protocol and hypothesis are not a supported association."
            )

    @staticmethod
    def _declaration(manifest, parent):
        declaration = manifest.get("experiment_declaration")
        if not isinstance(declaration, dict):
            raise ValueError("Missing experiment_declaration.")
        if declaration.get("experiment_kind") != "CONTROLLED_INTERVENTION":
            raise ValueError(
                "Causal source comparison requires CONTROLLED_INTERVENTION."
            )
        if declaration.get("reference_experiment_code") != parent:
            raise ValueError(
                "experiment_declaration reference contradicts comparison parent."
            )
        return declaration

    @staticmethod
    def _reject_conflicting_source(comparison, *, key, expected):
        existing = comparison.get(key)
        if existing is not None and existing != expected:
            raise ValueError(f"Comparison {key} contradicts requested association.")

    @staticmethod
    def _codes(values):
        if isinstance(values, str):
            values = (values,)
        if not isinstance(values, (list, tuple)):
            return ()
        return tuple(sorted(set(
            item.strip()
            for item in values
            if isinstance(item, str) and item.strip()
        )))
