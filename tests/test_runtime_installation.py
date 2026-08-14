import os
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_without_ollama(tmp_path, *arguments):
    blocker = tmp_path / "ollama.py"
    blocker.write_text(
        "raise ModuleNotFoundError(\"No module named 'ollama'\", name='ollama')\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(tmp_path), str(PROJECT_ROOT)))
    return subprocess.run(
        (sys.executable, *arguments),
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_runtime_requirements_are_accepted_by_pip():
    requirements = PROJECT_ROOT / "requirements.txt"
    lines = requirements.read_text(encoding="utf-8").splitlines()

    assert all(not line.strip().startswith("pip install ") for line in lines)
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "pip",
            "install",
            "--dry-run",
            "--no-deps",
            "-r",
            str(requirements),
        ),
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_main_help_starts_without_ollama(tmp_path):
    result = run_without_ollama(tmp_path, "main.py", "--help")

    assert result.returncode == 0, result.stderr
    assert "Analyze an AcousticBrain campaign." in result.stdout


def test_package_imports_without_ollama(tmp_path):
    result = run_without_ollama(tmp_path, "-c", "import acousticbrain")

    assert result.returncode == 0, result.stderr


def test_explicit_legacy_llm_request_reports_missing_optional_ollama(tmp_path):
    result = run_without_ollama(
        tmp_path,
        "-c",
        "from acousticbrain import AcousticAssistant; AcousticAssistant().ask('question')",
    )

    assert result.returncode != 0
    assert "optional Ollama integration is not installed" in result.stderr
    assert "deterministic runtime does not require it" in result.stderr


def test_deterministic_example_campaign_runs_without_ollama(tmp_path):
    result = run_without_ollama(
        tmp_path,
        "main.py",
        "--measurements-root",
        "measurements",
        "--analysis-readiness",
    )

    assert result.returncode == 0, result.stderr
    assert "TECHNICAL ANALYSIS READINESS" in result.stdout
