import json

import pytest

import main as acousticbrain_main
from acousticbrain.persistence import SBIRRoomGeometryDeclarationInputJsonLoader
from test_sbir_room_geometry_resolution import declaration


def campaign(tmp_path, manifest=None):
    root = tmp_path / "measurements"
    baseline = root / "baseline"
    baseline.mkdir(parents=True)
    path = baseline / "manifest.json"
    path.write_text(
        json.dumps({"state": "READY"} if manifest is None else manifest) + "\n",
        encoding="utf-8",
    )
    source = tmp_path / "room-geometry.json"
    source.write_text(
        SBIRRoomGeometryDeclarationInputJsonLoader().dumps(declaration()) + "\n",
        encoding="utf-8",
    )
    return root, source, path


def test_cli_previews_complete_contract_without_writing(tmp_path, capsys):
    root, source, manifest = campaign(tmp_path)
    before = manifest.read_bytes()
    assert acousticbrain_main.main([
        "--measurements-root", str(root),
        "--preview-sbir-room-geometry", str(source),
    ]) == 0
    output = capsys.readouterr().out
    assert "SBIR ROOM GEOMETRY PREVIEW — sbir-room-geometry-001" in output
    assert "Géométrie legacy : absente" in output
    assert "SBIR_GEOMETRY_DECLARATION_READY" in output
    assert "Aucune géométrie enregistrée" in output
    assert manifest.read_bytes() == before


def test_cli_reports_unknown_baseline_without_creating_it(tmp_path, capsys):
    root, source, _ = campaign(tmp_path)
    (root / "baseline" / "manifest.json").unlink()
    (root / "baseline").rmdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main([
            "--measurements-root", str(root),
            "--preview-sbir-room-geometry", str(source),
        ])
    assert "BASELINE_UNKNOWN" in capsys.readouterr().err
    assert not (root / "baseline").exists()


def test_geometry_preview_rejects_combined_report_mode(tmp_path, capsys):
    root, source, _ = campaign(tmp_path)
    with pytest.raises(SystemExit):
        acousticbrain_main.main([
            "--measurements-root", str(root),
            "--preview-sbir-room-geometry", str(source),
            "--full-assessment",
        ])
    assert "cannot be combined" in capsys.readouterr().err
