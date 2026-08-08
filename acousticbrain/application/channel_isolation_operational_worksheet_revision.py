from dataclasses import dataclass

from acousticbrain.models import AcquisitionSettingsReuseDeclaration

from .channel_isolation_operational_record_preview import (
    ChannelIsolationOperationalRecordPreviewService,
)


@dataclass(frozen=True)
class ChannelIsolationOperationalFieldGuidance:
    path: str
    question: str
    limitation: str
    allowed_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChannelIsolationOperationalWorksheetRevision:
    plan_id: str
    microphone_position: dict
    acquisition_settings: dict
    changed_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    documentation_status: str
    field_guidance: tuple[ChannelIsolationOperationalFieldGuidance, ...]


class ChannelIsolationOperationalWorksheetRevisionService:
    """Fills explicit worksheet fields without interpreting documentation."""

    PLACEHOLDER_PREFIX = "REPLACE_WITH_"
    GUIDANCE = (
        ChannelIsolationOperationalFieldGuidance(
            path="microphone_position.reference_geometry",
            question="Quel repère géométrique écrit permettra de retrouver la position ?",
            limitation="AcousticBrain ne vérifie ni le repère physique ni sa précision.",
        ),
        ChannelIsolationOperationalFieldGuidance(
            path="microphone_position.position_description",
            question="Comment la position du microphone est-elle décrite explicitement ?",
            limitation="Aucune coordonnée ou tolérance n’est déduite du texte.",
        ),
        ChannelIsolationOperationalFieldGuidance(
            path="microphone_position.orientation_description",
            question="Comment l’orientation du microphone est-elle documentée ?",
            limitation="L’orientation physique réelle n’est pas inspectée.",
        ),
        ChannelIsolationOperationalFieldGuidance(
            path="acquisition_settings.gain",
            question="Quelle trace écrite identifie le gain qui sera réutilisé ?",
            limitation="Aucune valeur de gain appropriée n’est recommandée.",
        ),
        ChannelIsolationOperationalFieldGuidance(
            path="acquisition_settings.time_window",
            question="Quelle fenêtre temporelle d’acquisition est explicitement consignée ?",
            limitation="Aucune fenêtre n’est calculée ou validée.",
        ),
        ChannelIsolationOperationalFieldGuidance(
            path="acquisition_settings.signal_chain",
            question="Quelle chaîne du signal est explicitement consignée ?",
            limitation="Aucun appareil, routage ou logiciel n’est détecté.",
        ),
        ChannelIsolationOperationalFieldGuidance(
            path="acquisition_settings.reuse_declaration",
            question="Les mêmes réglages sont-ils destinés à être réutilisés ?",
            limitation="Cette réponse décrit une intention et non la réutilisation réelle.",
            allowed_values=tuple(
                value.value for value in AcquisitionSettingsReuseDeclaration
            ),
        ),
    )
    ALLOWED_PATHS = frozenset(value.path for value in GUIDANCE)
    TEXT_FIELDS = {
        "microphone_position": (
            "record_id",
            "plan_id",
            "reference_geometry",
            "position_description",
            "orientation_description",
            "documentation_source",
        ),
        "acquisition_settings": (
            "record_id",
            "plan_id",
            "gain",
            "time_window",
            "signal_chain",
            "documentation_source",
        ),
    }

    def __init__(self, preview_service=None):
        self.preview_service = (
            preview_service or ChannelIsolationOperationalRecordPreviewService()
        )

    def revise(self, plan_id, microphone, settings, assignments, *, plans):
        if not isinstance(assignments, dict) or not assignments:
            raise ValueError("At least one explicit operational field is required.")
        if any(not isinstance(path, str) for path in assignments):
            raise TypeError("Operational assignment paths must be strings.")
        unknown = tuple(sorted(set(assignments) - self.ALLOWED_PATHS))
        if unknown:
            raise ValueError(
                "Unknown operational assignment paths: " + ", ".join(unknown)
            )
        microphone_copy = dict(microphone) if isinstance(microphone, dict) else microphone
        settings_copy = dict(settings) if isinstance(settings, dict) else settings
        self.preview_service.preview(
            plan_id, microphone_copy, settings_copy, plans=plans
        )
        self._validate_values(microphone_copy, settings_copy)
        documents = {
            "microphone_position": microphone_copy,
            "acquisition_settings": settings_copy,
        }
        for path, value in assignments.items():
            self._assignment(path, value)
            document, field = path.split(".", 1)
            documents[document][field] = value
        self._validate_values(microphone_copy, settings_copy)
        preview = self.preview_service.preview(
            plan_id, microphone_copy, settings_copy, plans=plans
        )
        return ChannelIsolationOperationalWorksheetRevision(
            plan_id=plan_id,
            microphone_position=microphone_copy,
            acquisition_settings=settings_copy,
            changed_fields=tuple(sorted(assignments)),
            missing_fields=preview.missing_fields,
            documentation_status=preview.status,
            field_guidance=self.GUIDANCE,
        )

    def _validate_values(self, microphone, settings):
        for label, value in (
            ("microphone_position", microphone),
            ("acquisition_settings", settings),
        ):
            if not isinstance(value.get("schema_version"), int) or isinstance(
                value.get("schema_version"), bool
            ) or value["schema_version"] != 1:
                raise ValueError(f"{label}.schema_version must be exactly 1.")
            for field in self.TEXT_FIELDS[label]:
                content = value[field]
                path = f"{label}.{field}"
                if isinstance(content, str) and content.startswith(
                    self.PLACEHOLDER_PREFIX
                ):
                    if path in self.ALLOWED_PATHS:
                        continue
                    raise ValueError(f"{path} cannot be a placeholder.")
                self._exact_text(path, content)
            note = value["user_note"]
            if note is not None:
                self._exact_text(f"{label}.user_note", note)
        reuse = settings["reuse_declaration"]
        if isinstance(reuse, str) and reuse.startswith(self.PLACEHOLDER_PREFIX):
            return
        else:
            try:
                AcquisitionSettingsReuseDeclaration(reuse)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "acquisition_settings.reuse_declaration is invalid."
                ) from error

    def _assignment(self, path, value):
        self._exact_text(path, value)
        if value.startswith(self.PLACEHOLDER_PREFIX):
            raise ValueError("Operational assignments cannot restore placeholders.")
        if path == "acquisition_settings.reuse_declaration":
            try:
                AcquisitionSettingsReuseDeclaration(value)
            except ValueError as error:
                allowed = ", ".join(
                    item.value for item in AcquisitionSettingsReuseDeclaration
                )
                raise ValueError(
                    "Invalid reuse declaration; allowed values: " + allowed
                ) from error

    @staticmethod
    def _exact_text(label, value):
        if not isinstance(value, str) or not value or value != value.strip():
            raise ValueError(f"{label} must be exact non-empty text.")
