import json

import pytest

import main as acousticbrain_main
from test_sbir_room_geometry_preview_cli import campaign


def test_guide_lists_exact_required_measurements_without_writing(tmp_path, capsys):
    root, _, manifest = campaign(tmp_path)
    before = manifest.read_bytes()
    assert acousticbrain_main.main([
        "--measurements-root", str(root),
        "--sbir-room-geometry-guide",
    ]) == 0
    output = capsys.readouterr().out
    assert "SBIR ROOM GEOMETRY GUIDE — baseline" in output
    assert "Contrat canonique : ABSENT" in output
    assert "Enceinte LEFT : x, y, z." in output
    assert "LISTENING_POSITION : x, y, z." in output
    assert "front_wall, rear_wall, left_wall" in output
    assert "ne la reconstruit pas" in output
    assert "Faire mesurer et documenter" in output
    assert manifest.read_bytes() == before


def test_guide_recognizes_existing_valid_contract(tmp_path, capsys):
    root, source, manifest = campaign(tmp_path)
    assert acousticbrain_main.main([
        "--measurements-root", str(root),
        "--declare-sbir-room-geometry", str(source),
    ]) == 0
    capsys.readouterr()
    before = manifest.read_bytes()
    assert acousticbrain_main.main([
        "--measurements-root", str(root),
        "--sbir-room-geometry-guide",
    ]) == 0
    output = capsys.readouterr().out
    assert "Contrat canonique : PRÉSENT" in output
    assert "Empreinte : " in output
    assert "Aucune action : une déclaration canonique valide existe déjà." in output
    assert manifest.read_bytes() == before


def test_guide_revalidates_existing_contract(tmp_path, capsys):
    root, source, manifest = campaign(tmp_path)
    acousticbrain_main.main([
        "--measurements-root", str(root),
        "--declare-sbir-room-geometry", str(source),
    ])
    capsys.readouterr()
    value = json.loads(manifest.read_text())
    value["room_description_contract"]["room_description_fingerprint"] = "0" * 64
    manifest.write_text(json.dumps(value) + "\n")
    with pytest.raises(SystemExit):
        acousticbrain_main.main([
            "--measurements-root", str(root),
            "--sbir-room-geometry-guide",
        ])
    assert "fingerprint is invalid" in capsys.readouterr().err


def test_guide_is_exclusive_with_preview(tmp_path, capsys):
    root, source, _ = campaign(tmp_path)
    with pytest.raises(SystemExit):
        acousticbrain_main.main([
            "--measurements-root", str(root),
            "--sbir-room-geometry-guide",
            "--preview-sbir-room-geometry", str(source),
        ])
    assert "mutually exclusive" in capsys.readouterr().err
