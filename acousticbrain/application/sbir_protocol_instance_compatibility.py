from acousticbrain.models import (
    LoudspeakerPositioningExperimentProposal,
    SBIRProtocolInstanceCompatibility,
    SBIRProtocolInstanceResolution,
)


class SBIRProtocolInstanceCompatibilityValidator:
    """Validates only exact existing SBIR source continuity."""

    def validate(self, resolution, *, displacement_proposals):
        if not isinstance(resolution, SBIRProtocolInstanceResolution):
            raise TypeError("SBIRProtocolInstanceResolution is required.")

        value = resolution.protocol_instance_input
        candidate = resolution.geometry_candidate
        mismatched = tuple(
            field
            for field, declared, resolved in (
                ("speaker_id", value.speaker_id, candidate.speaker_id),
                ("surface_id", value.surface_id, candidate.surface_id),
            )
            if declared != resolved
        )
        if mismatched:
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_SPEAKER_SURFACE_MISMATCH: "
                "incompatible fields: " + ", ".join(mismatched) + "."
            )

        proposals = self._typed_proposals(displacement_proposals)
        associated = tuple(
            proposal
            for proposal in proposals
            if proposal.source_geometry_candidate_id == candidate.candidate_id
        )
        if not associated:
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_DISPLACEMENT_PROPOSAL_UNKNOWN: "
                f"{candidate.candidate_id}."
            )
        if len(associated) != 1:
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_DISPLACEMENT_PROPOSAL_AMBIGUOUS: "
                f"{candidate.candidate_id}."
            )
        proposal = associated[0]

        incompatible = []
        if proposal.source_surface_id != candidate.surface_id:
            incompatible.append("source_surface_id")
        if proposal.step_distance_m != value.speaker_displacement_m:
            incompatible.append("speaker_displacement_m")
        if incompatible:
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_DISPLACEMENT_SOURCE_MISMATCH: "
                "incompatible fields: " + ", ".join(incompatible) + "."
            )

        return SBIRProtocolInstanceCompatibility(
            resolution=resolution,
            displacement_proposal=proposal,
            decisions=SBIRProtocolInstanceCompatibility.EXPECTED_DECISIONS,
        )

    @staticmethod
    def _typed_proposals(values):
        if not isinstance(values, tuple):
            raise TypeError(
                "SBIR protocol-instance displacement proposals must be a typed tuple."
            )
        if any(
            not isinstance(value, LoudspeakerPositioningExperimentProposal)
            for value in values
        ):
            raise TypeError(
                "SBIR protocol-instance displacement proposals contain an invalid "
                "object."
            )
        return values
