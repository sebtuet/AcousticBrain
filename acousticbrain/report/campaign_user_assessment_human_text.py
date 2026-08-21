class CampaignUserAssessmentHumanText:
    """Closed deterministic vocabulary for rendering existing V1 states."""

    FINDING_TITLES = {
        "ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING": (
            "Left/right speaker-room interaction"
        ),
        "MODAL_BASS_PERSISTENCE_REASONING": "Bass persistence",
        "DOMINANT_EARLY_REFLECTION_INTERACTION_REASONING": "Early reflections",
        "SBIR_PLACEMENT_INTERACTION_REASONING": "SBIR and placement interaction",
    }
    CONCLUSIONS = {
        "SUPPORTED": (
            "The available observations support the existing hypothesis."
        ),
        "PARTIALLY_SUPPORTED": (
            "The available observations provide partial support, but the "
            "conclusion remains limited."
        ),
        "CONTRADICTED": (
            "The available observations contradict the existing hypothesis."
        ),
        "INSUFFICIENT_EVIDENCE": (
            "The available information is insufficient to reach a conclusion."
        ),
        "CONTRADICTORY_EVIDENCE": (
            "The available information is contradictory and does not yet "
            "support one unique conclusion."
        ),
        "NON_DISCRIMINATED": (
            "The current measurements do not yet distinguish between the "
            "possible explanations."
        ),
        "NO_APPLICABLE_RULE": (
            "No existing deterministic rule can qualify this hypothesis from "
            "the available information."
        ),
    }
    ACTION_APPLICABILITY = {
        "APPLICABLE": "A controlled verification is currently available.",
        "CONDITIONALLY_APPLICABLE": (
            "This controlled verification still requires stated conditions."
        ),
        "BLOCKED_BY_CONTRADICTION": (
            "No action should be selected while the recorded contradiction "
            "remains unresolved."
        ),
        "BLOCKED_BY_MISSING_PARAMETERS": (
            "Required information is missing before this action can proceed."
        ),
        "BLOCKED_BY_HISTORY": (
            "The recorded experiment history currently blocks this action."
        ),
        "ALREADY_TESTED": "This action is already recorded as tested.",
        "NOT_SUPPORTED": (
            "The existing deterministic results do not support this action."
        ),
        "NO_ACTION_REQUIRED": (
            "The existing deterministic result requires no action."
        ),
    }
    PLAN_STATUSES = {
        "READY": (
            "The measurement plan is defined for its current planning state; "
            "this does not mean the experiment is ready to execute."
        ),
        "PROPOSED": (
            "The measurement plan is proposed but is not yet structurally ready."
        ),
        "BLOCKED": "The measurement plan is blocked by existing requirements.",
    }
    PREREQUISITE_STATUSES = {
        "AVAILABILITY_NOT_VERIFIED": (
            "These prerequisites still need to be confirmed."
        ),
        "NO_REQUIRED_INPUTS": (
            "This plan declares no required pre-acquisition inputs."
        ),
    }
    ANALYSIS_STATUSES = {
        "AVAILABLE": "available",
        "AVAILABLE_WITH_RESERVATIONS": "available with reservations",
        "BLOCKED": "blocked",
    }
    ANALYSIS_FAMILIES = {
        "FREQUENCY": "frequency response",
        "RT60": "reverberation time",
        "ETC": "energy-time curve",
        "CLARITY": "clarity",
        "SPATIAL": "spatial analysis",
        "DIRECT_REVERBERANT": "direct-to-reverberant balance",
        "BASS_DECAY": "bass decay",
    }
    TEST_TYPES = {
        "REPEAT_MEASUREMENT": "repeat measurement",
        "CHANNEL_ISOLATION": "separate left/right channel measurement",
        "CONTROLLED_SPEAKER_DISPLACEMENT": "controlled speaker displacement",
        "CONTROLLED_MICROPHONE_DISPLACEMENT": (
            "controlled microphone displacement"
        ),
        "GEOMETRY_ACQUISITION": "geometry acquisition",
        "PROTOCOL_EXECUTION": "declared protocol execution",
        "ADDITIONAL_OBSERVATION": "additional observation",
        "COMPARATIVE_MEASUREMENT": "comparative measurement",
        "PARAMETER_COMPLETION": "parameter completion",
    }
    PREREQUISITES = {
        "documented_microphone_position": "the documented microphone position",
        "existing_acquisition_settings": (
            "the acquisition settings that must remain unchanged"
        ),
    }
    LIMITATIONS = {
        "StereoAnalysis exposes no confidence value.": (
            "No confidence value is available for the stereo analysis."
        ),
    }

    @classmethod
    def finding_title(cls, finding):
        return cls.FINDING_TITLES.get(finding.reasoning_id, finding.title)

    @classmethod
    def conclusion(cls, value):
        return cls.CONCLUSIONS.get(
            value,
            "No human-readable meaning is defined for this existing conclusion.",
        )

    @classmethod
    def action_applicability(cls, value):
        return cls.ACTION_APPLICABILITY.get(
            value,
            "No human-readable meaning is defined for this action state.",
        )

    @classmethod
    def plan_status(cls, value):
        return cls.PLAN_STATUSES.get(
            value,
            "No human-readable meaning is defined for this planning state.",
        )

    @classmethod
    def prerequisite_status(cls, value):
        return cls.PREREQUISITE_STATUSES.get(
            value,
            "No human-readable meaning is defined for this prerequisite state.",
        )

    @classmethod
    def analysis_family(cls, value):
        return cls.ANALYSIS_FAMILIES.get(value, value.replace("_", " ").lower())

    @classmethod
    def analysis_status(cls, value):
        return cls.ANALYSIS_STATUSES.get(value, value.replace("_", " ").lower())

    @classmethod
    def test_type(cls, value):
        return cls.TEST_TYPES.get(value, value.replace("_", " ").lower())

    @classmethod
    def prerequisite(cls, value):
        return cls.PREREQUISITES.get(value, value.replace("_", " "))

    @classmethod
    def limitation(cls, value):
        return cls.LIMITATIONS.get(value, value)
