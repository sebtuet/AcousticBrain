import ast
from pathlib import Path

import pytest

from runtime_requirement import enforce_supported_python, require_supported_python


def test_supported_python_version_is_accepted():
    assert require_supported_python((3, 10, 0)) is None
    assert enforce_supported_python((3, 14, 0)) is None


def test_unsupported_python_version_has_an_explicit_error():
    with pytest.raises(SystemExit) as error:
        enforce_supported_python((3, 9, 0))

    assert error.value.code == (
        "AcousticBrain requires Python 3.10 or newer. Current version: 3.9."
    )


def test_runtime_requirement_imports_no_acousticbrain_module():
    tree = ast.parse(Path("runtime_requirement.py").read_text(encoding="utf-8"))
    assert all(
        not isinstance(node, ast.ImportFrom)
        or node.module is None
        or not node.module.startswith("acousticbrain")
        for node in tree.body
    )


def test_main_enforces_the_runtime_requirement_before_acousticbrain_imports():
    tree = ast.parse(Path("main.py").read_text(encoding="utf-8"))
    guard_line = next(
        node.lineno
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "enforce_supported_python"
    )
    first_acousticbrain_import_line = next(
        node.lineno
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("acousticbrain")
    )

    assert guard_line < first_acousticbrain_import_line
