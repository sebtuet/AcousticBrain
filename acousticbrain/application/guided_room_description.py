from dataclasses import dataclass, replace
from hashlib import sha256
import json
import unicodedata

from acousticbrain.analysis.surface_material import SurfaceMaterialAnalyzer
from acousticbrain.catalogs import BuiltInSurfaceMaterialCatalog
from acousticbrain.models import (
    GuidedAllowedValue,
    GuidedAnswerInterpretation,
    GuidedChangeKind,
    GuidedCompletenessProjection,
    GuidedInterpretedFact,
    GuidedInterpretationStatus,
    GuidedQuestionKind,
    GuidedQuestionPriority,
    GuidedRequestedChange,
    GuidedValidationIssue,
    RoomDescription,
    RoomDescriptionChangeProposal,
    RoomDescriptionChangeProposalStatus,
    RoomDescriptionQuestionPlan,
    SurfaceMaterialAssignment,
    SurfaceMaterialDescriptionSource,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec
from acousticbrain.validation import RoomDescriptionValidator


class RoomDescriptionQuestionPlanner:
    """Choisit une seule question utile sans formulation conversationnelle."""

    ROLE_ORDER = (
        "LEFT_WALL", "RIGHT_WALL", "FRONT_WALL", "REAR_WALL", "FLOOR", "CEILING"
    )

    def __init__(self, catalog=None):
        self.catalog = catalog or BuiltInSurfaceMaterialCatalog()

    def plan(self, description):
        if not isinstance(description, RoomDescription):
            raise TypeError("Question planning requires RoomDescription.")
        assigned = {
            (item.target_kind, item.target_id)
            for item in description.material_assignments
        }
        targets = self._targets(description)
        missing = [item for item in targets if item[:2] not in assigned]
        if not missing:
            return None
        by_role = {}
        for kind, target_id, role in missing:
            by_role.setdefault((kind, role), []).append(target_id)
        kind, role = min(
            by_role,
            key=lambda item: (
                self.ROLE_ORDER.index(item[1]) if item[1] in self.ROLE_ORDER else 99,
                item[0], item[1],
            ),
        )
        candidates = tuple(sorted(by_role[(kind, role)]))
        target_id = candidates[0] if len(candidates) == 1 else None
        values = tuple(
            GuidedAllowedValue(
                value_id=item.material_type,
                display_name=item.display_name,
                catalog_entry_id=item.catalog_entry_id,
            )
            for item in self.catalog.entries
        ) + (GuidedAllowedValue("OTHER", "Other"),)
        return RoomDescriptionQuestionPlan(
            question_id=f"material.{kind.lower()}.{role.lower()}",
            question_kind=GuidedQuestionKind.MATERIAL_ASSIGNMENT,
            fact_code=f"surface_material.assignment.{kind}.{role}",
            priority=GuidedQuestionPriority.HIGH,
            target_kind=kind,
            target_id=target_id,
            target_role=role,
            target_candidates=candidates,
            allowed_values=values,
            validation_constraints=(
                "VALUE_MUST_BE_ALLOWED",
                "TARGET_MUST_BE_UNIQUE_OR_CONFIRMED",
                "CATALOG_ENTRY_VERSION_MUST_BE_EXPLICIT",
            ),
            unknown_consequences=(
                "MATERIAL_PROFILE_REMAINS_UNAVAILABLE",
                "NO_PROTOCOL_ELIGIBILITY_IS_PROMISED",
            ),
            requires_target_confirmation=len(candidates) > 1,
        )

    @classmethod
    def _targets(cls, description):
        if description.planar_surfaces:
            surfaces = tuple(
                ("SURFACE", item.surface_id, item.role.value)
                for item in description.planar_surfaces
            )
        else:
            surfaces = tuple(
                ("SURFACE", role.lower(), role) for role in cls.ROLE_ORDER
            )
        regions = tuple(
            ("REGION", item.region_id, item.role.value)
            for item in description.planar_regions
        )
        return tuple(sorted((*surfaces, *regions), key=lambda item: (item[0], item[2], item[1])))


class StructuredRoomDescriptionInterpreter:
    """Mode déterministe de saisie, sans LLM."""

    def interpret(self, question, value_id, *, target_id=None, confidence=100.0):
        allowed = {item.value_id for item in question.allowed_values}
        status = (
            GuidedInterpretationStatus.CANDIDATE
            if value_id in allowed else GuidedInterpretationStatus.INSUFFICIENT
        )
        ambiguities = () if status is GuidedInterpretationStatus.CANDIDATE else (
            "VALUE_NOT_ALLOWED",
        )
        return GuidedAnswerInterpretation(
            status=status,
            candidate_value_ids=(value_id,) if value_id in allowed else (),
            target_id=target_id,
            confidence=confidence,
            ambiguity_codes=ambiguities,
            provenance_codes=("USER_STRUCTURED_INPUT",),
        )


class ControlledVocabularyRoomDescriptionInterpreter:
    """Interprète quelques libellés exacts sans inférence acoustique."""

    VALUE_ALIASES = {
        "beton": "CONCRETE",
        "brique": "BRICK",
        "plaque de platre": "GYPSUM_BOARD_PAINTED",
        "plaque de platre peinte": "GYPSUM_BOARD_PAINTED",
        "placo": "GYPSUM_BOARD_PAINTED",
        "placo peint": "GYPSUM_BOARD_PAINTED",
        "bois": "WOOD",
        "verre": "GLAZING",
        "vitrage": "GLAZING",
        "inconnu": "UNKNOWN",
    }

    def interpret(self, question, answer, *, target_id=None):
        if not isinstance(answer, str) or not answer.strip():
            return self._unresolved(
                GuidedInterpretationStatus.INSUFFICIENT,
                "MATERIAL_DESCRIPTION_MISSING",
                target_id,
            )
        normalized = self._normalize(answer)
        value_id = self.VALUE_ALIASES.get(normalized)
        allowed = {item.value_id for item in question.allowed_values}
        if value_id is None or value_id not in allowed:
            return self._unresolved(
                GuidedInterpretationStatus.AMBIGUOUS,
                "MATERIAL_DESCRIPTION_AMBIGUOUS",
                target_id,
            )
        return GuidedAnswerInterpretation(
            status=GuidedInterpretationStatus.CANDIDATE,
            candidate_value_ids=(value_id,),
            target_id=target_id,
            confidence=100.0,
            ambiguity_codes=(),
            provenance_codes=("USER_DESCRIPTION_INTERPRETED",),
        )

    @staticmethod
    def _normalize(value):
        decomposed = unicodedata.normalize("NFKD", value.strip().lower())
        return " ".join(
            "".join(
                character
                for character in decomposed
                if not unicodedata.combining(character)
            )
            .replace("-", " ")
            .split()
        )

    @staticmethod
    def _unresolved(status, code, target_id):
        return GuidedAnswerInterpretation(
            status=status,
            candidate_value_ids=(),
            target_id=target_id,
            confidence=0.0,
            ambiguity_codes=(code,),
            provenance_codes=("USER_DESCRIPTION_INTERPRETED",),
        )


class RoomDescriptionProposalService:
    def __init__(self, catalog=None, validator=None):
        self.catalog = catalog or BuiltInSurfaceMaterialCatalog()
        self.validator = validator or RoomDescriptionValidator()

    def propose(self, description, question, interpretation):
        if not isinstance(interpretation, GuidedAnswerInterpretation):
            raise TypeError("Proposal construction requires a guided interpretation.")
        ambiguities = list(interpretation.ambiguity_codes)
        allowed = {item.value_id: item for item in question.allowed_values}
        candidates = tuple(
            item for item in interpretation.candidate_value_ids if item in allowed
        )
        if len(candidates) != 1:
            ambiguities.append("MATERIAL_VALUE_REQUIRES_CLARIFICATION")
        target_id = interpretation.target_id or question.target_id
        if target_id not in question.target_candidates:
            ambiguities.append("TARGET_REQUIRES_CLARIFICATION")
        elif question.requires_target_confirmation and interpretation.target_id is None:
            ambiguities.append("TARGET_REQUIRES_EXPLICIT_CONFIRMATION")
        if candidates and candidates[0] == "OTHER":
            ambiguities.append("OTHER_MATERIAL_REQUIRES_DESCRIPTION")

        requested = ()
        facts = ()
        issues = ()
        if not ambiguities:
            value = allowed[candidates[0]]
            requested = (GuidedRequestedChange(
                change_kind=GuidedChangeKind.ASSIGN_CATALOG_MATERIAL,
                target_kind=question.target_kind,
                target_id=target_id,
                value_id=value.value_id,
                catalog_entry_id=value.catalog_entry_id,
            ),)
            facts = (GuidedInterpretedFact(
                fact_code=question.fact_code,
                value=value.value_id,
                confidence=interpretation.confidence,
                provenance_codes=interpretation.provenance_codes,
            ),)
            if value.catalog_entry_id is None:
                issues = (GuidedValidationIssue(
                    code="CATALOG_ENTRY_REQUIRED", field="catalog_entry_id"
                ),)

        before, after = self._project_completeness(description, bool(requested and not issues))
        status = RoomDescriptionChangeProposalStatus.NEEDS_CLARIFICATION
        if issues:
            status = RoomDescriptionChangeProposalStatus.INVALID
        elif requested:
            status = RoomDescriptionChangeProposalStatus.READY_FOR_CONFIRMATION
        proposal_id = self._proposal_id(question.question_id, interpretation, target_id)
        return RoomDescriptionChangeProposal(
            proposal_id=proposal_id,
            target_kind=question.target_kind,
            target_id=target_id,
            requested_changes=requested,
            interpreted_facts=facts,
            unresolved_ambiguities=tuple(dict.fromkeys(ambiguities)),
            validation_issues=issues,
            predicted_completeness_change=GuidedCompletenessProjection(before, after),
            potentially_unblocked_capabilities=(
                ("POTENTIALLY_COMPLETE_SURFACE_MATERIAL_ASSIGNMENTS",)
                if after == 100.0 and after > before else ()
            ),
            requires_confirmation=status is RoomDescriptionChangeProposalStatus.READY_FOR_CONFIRMATION,
            status=status,
            provenance=interpretation.provenance_codes,
        )

    @staticmethod
    def confirm(proposal):
        if proposal.status is not RoomDescriptionChangeProposalStatus.READY_FOR_CONFIRMATION:
            raise ValueError("Only ready proposals can be confirmed.")
        return replace(
            proposal,
            status=RoomDescriptionChangeProposalStatus.CONFIRMED,
            requires_confirmation=False,
        )

    @staticmethod
    def reject(proposal):
        if proposal.status is RoomDescriptionChangeProposalStatus.APPLIED:
            raise ValueError("Applied proposals cannot be rejected.")
        return replace(
            proposal,
            status=RoomDescriptionChangeProposalStatus.REJECTED,
            requires_confirmation=False,
        )

    def apply(self, description, proposal):
        if proposal.status is not RoomDescriptionChangeProposalStatus.CONFIRMED:
            raise ValueError("Only confirmed proposals can be applied.")
        materials = list(description.materials)
        assignments = list(description.material_assignments)
        by_material_id = {item.material_id for item in materials}
        fact = proposal.interpreted_facts[0]
        for change in proposal.requested_changes:
            entry = self.catalog.get(change.catalog_entry_id)
            if entry is None:
                raise ValueError("Confirmed proposal references an unknown catalog entry.")
            if entry.material.material_id not in by_material_id:
                materials.append(entry.material)
                by_material_id.add(entry.material.material_id)
            assignment_id = f"guided:{change.target_kind.lower()}:{change.target_id}"
            assignments.append(SurfaceMaterialAssignment(
                assignment_id=assignment_id,
                material_id=entry.material.material_id,
                surface_id=change.target_id if change.target_kind == "SURFACE" else None,
                region_id=change.target_id if change.target_kind == "REGION" else None,
                description_source=self._description_source(proposal.provenance),
                description_confidence=fact.confidence,
                provenance_codes=proposal.provenance,
            ))
        updated = replace(
            description,
            materials=tuple(sorted(materials, key=lambda item: item.material_id)),
            material_assignments=tuple(sorted(assignments, key=lambda item: item.assignment_id)),
        )
        validation = self.validator.validate(updated)
        if not validation.is_valid:
            raise ValueError("Confirmed proposal produced an invalid RoomDescription.")
        return updated, replace(
            proposal,
            status=RoomDescriptionChangeProposalStatus.APPLIED,
            requires_confirmation=False,
        )

    @staticmethod
    def _description_source(provenance):
        if "USER_STRUCTURED_INPUT" in provenance:
            return SurfaceMaterialDescriptionSource.USER_STRUCTURED_INPUT
        return SurfaceMaterialDescriptionSource.USER_DESCRIPTION_INTERPRETED

    @staticmethod
    def _proposal_id(question_id, interpretation, target_id):
        payload = json.dumps({
            "question_id": question_id,
            "candidate_value_ids": interpretation.candidate_value_ids,
            "target_id": target_id,
            "confidence": interpretation.confidence,
            "provenance": interpretation.provenance_codes,
        }, sort_keys=True, separators=(",", ":"))
        return f"proposal:sha256:{sha256(payload.encode()).hexdigest()}"

    @staticmethod
    def _project_completeness(description, adds_assignment):
        target_count = len(RoomDescriptionQuestionPlanner._targets(description))
        assigned_count = len(description.material_assignments)
        before = 100.0 * assigned_count / target_count if target_count else 0.0
        after_count = min(target_count, assigned_count + int(adds_assignment))
        after = 100.0 * after_count / target_count if target_count else 0.0
        return before, after


@dataclass(frozen=True)
class GuidedRoomDescriptionApplyResult:
    description: RoomDescription
    proposal: RoomDescriptionChangeProposal
    serialized_room_description: str
    analysis_result: object
    full_analysis_triggered: bool


class GuidedRoomDescriptionWorkflow:
    """Persiste via le codec puis impose une nouvelle analyse complète."""

    def __init__(self, proposal_service=None, codec=None):
        self.proposal_service = proposal_service or RoomDescriptionProposalService()
        self.codec = codec or RoomDescriptionJsonCodec()

    def apply(self, project, proposal, analyzer):
        if not callable(analyzer):
            raise TypeError("Guided workflow requires a full-analysis callable.")
        updated, applied = self.proposal_service.apply(
            project.room_description, proposal
        )
        payload = self.codec.dumps(updated, indent=2)
        persisted = self.codec.loads(payload)
        if not persisted.is_success:
            raise ValueError("Applied room description failed persistence validation.")
        project.room_description = persisted.description
        analysis_result = analyzer(project)
        return GuidedRoomDescriptionApplyResult(
            description=persisted.description,
            proposal=applied,
            serialized_room_description=payload,
            analysis_result=analysis_result,
            full_analysis_triggered=True,
        )
