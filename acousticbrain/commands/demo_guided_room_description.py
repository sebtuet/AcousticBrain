import argparse
from hashlib import sha256
import json

from acousticbrain.application import (
    ControlledVocabularyRoomDescriptionInterpreter,
    GuidedRoomDescriptionWorkflow,
    RoomDescriptionProposalService,
    RoomDescriptionQuestionPlanner,
)
from acousticbrain.brain import AcousticBrain
from acousticbrain.models import (
    Measurement,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription,
    Room,
    RoomDescription,
    RoomDimensions,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec
from acousticbrain.project import Measurements, Project


SCENARIO_ANSWERS = {
    "confirmed": "plaque de plâtre",
    "ambiguous": "C'est probablement une cloison légère avec quelque chose dessus.",
}


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Démontre PR-034 en mémoire, sans lire ni modifier measurements/."
        )
    )
    parser.add_argument(
        "--scenario",
        choices=tuple(SCENARIO_ANSWERS),
        default="confirmed",
    )
    return parser


def _description():
    vertices = (
        PlanarVertexDescription(0.0, 0.0, 0.0),
        PlanarVertexDescription(5.0, 0.0, 0.0),
        PlanarVertexDescription(5.0, 0.0, 3.0),
        PlanarVertexDescription(0.0, 0.0, 3.0),
    )
    return RoomDescription(
        "Guided review room",
        RoomDimensions(5.0, 4.0, 3.0),
        planar_surfaces=(
            PlanarSurfaceDescription(
                "LEFT_WALL_PANEL_01",
                PlanarSurfaceRole.LEFT_WALL,
                vertices,
            ),
        ),
    )


def _project(description):
    project = Project(
        "PR-034 isolated demo",
        Room("Synthetic review room", 5.0, 4.0, 3.0),
        room_description=description,
    )
    frequencies = [
        20.0,
        50.0,
        100.0,
        200.0,
        500.0,
        1000.0,
        2000.0,
        5000.0,
        10000.0,
        20000.0,
    ]
    project.add_measurement(
        Measurements.STEREO,
        Measurement(
            "Synthetic stereo",
            frequencies,
            [70.0] * len(frequencies),
            [0.0] * len(frequencies),
        ),
    )
    return project


def _digest(payload):
    return f"sha256:{sha256(payload.encode()).hexdigest()}"


def run_demo(scenario):
    codec = RoomDescriptionJsonCodec()
    description = _description()
    project = _project(description)
    initial_payload = codec.dumps(description, indent=2)

    AcousticBrain().analyze(project)
    planner = RoomDescriptionQuestionPlanner()
    question = planner.plan(description)
    answer = SCENARIO_ANSWERS[scenario]
    interpretation = ControlledVocabularyRoomDescriptionInterpreter().interpret(
        question,
        answer,
    )
    service = RoomDescriptionProposalService()
    proposal = service.propose(description, question, interpretation)
    before_confirmation_payload = codec.dumps(project.room_description, indent=2)

    result = {
        "isolation": {
            "mode": "IN_MEMORY_SYNTHETIC_PROJECT",
            "reads_measurements_directory": False,
            "writes_project_files": False,
        },
        "question": {
            "question_id": question.question_id,
            "prompt": "Quel est le matériau principal du mur gauche ?",
            "priority": question.priority.name,
            "target_candidates": list(question.target_candidates),
            "allowed_value_ids": [item.value_id for item in question.allowed_values],
            "unknown_consequences": list(question.unknown_consequences),
        },
        "answer": answer,
        "interpretation": {
            "status": interpretation.status.value,
            "candidate_value_ids": list(interpretation.candidate_value_ids),
            "ambiguity_codes": list(interpretation.ambiguity_codes),
            "provenance": list(interpretation.provenance_codes),
        },
        "proposal_before_confirmation": {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status.value,
            "requires_confirmation": proposal.requires_confirmation,
            "potentially_unblocked_capabilities": list(
                proposal.potentially_unblocked_capabilities
            ),
            "capability_projection_is_eligibility": False,
            "eligibility_disclaimer": (
                "Potential capabilities are informative; eligibility requires "
                "a complete new analysis."
            ),
        },
        "before_confirmation": {
            "persisted_json_unchanged": initial_payload == before_confirmation_payload,
            "json_digest": _digest(before_confirmation_payload),
            "analysis_rerun_triggered": False,
        },
        "confirmation": None,
        "application": None,
    }

    if proposal.requires_confirmation:
        confirmed = service.confirm(proposal)
        result["confirmation"] = {
            "status": confirmed.status.value,
            "persisted": False,
        }
        analysis_calls = []

        def analyze(candidate_project):
            analysis_calls.append(candidate_project.room_description)
            return AcousticBrain().analyze(candidate_project)

        applied = GuidedRoomDescriptionWorkflow(proposal_service=service).apply(
            project,
            confirmed,
            analyze,
        )
        material = applied.description.materials[0]
        assignment = applied.description.material_assignments[0]
        result["application"] = {
            "status": applied.proposal.status.value,
            "schema_version": json.loads(applied.serialized_room_description)[
                "schema_version"
            ],
            "full_analysis_triggered": applied.full_analysis_triggered,
            "full_analysis_call_count": len(analysis_calls),
            "report_project_name": applied.analysis_result.project_name,
            "material_assignment": {
                "target_id": assignment.target_id,
                "description_source": assignment.description_source.value,
                "description_provenance": list(assignment.provenance_codes),
                "catalog_entry_id": material.catalog_entry_id,
                "catalog_entry_version_is_explicit": (
                    material.catalog_entry_id.endswith(".v1")
                ),
                "profile_source": material.source.value,
                "profile_confidence": material.confidence,
                "profile_provenance": list(material.provenance_codes),
            },
        }
    return result


def main(argv=None):
    arguments = build_parser().parse_args(argv)
    print(
        json.dumps(
            run_demo(arguments.scenario),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
