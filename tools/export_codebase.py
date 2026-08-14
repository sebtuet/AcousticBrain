#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import platform

def find_project_root() -> Path:
    current = Path(__file__).resolve().parent

    while current != current.parent:

        if (current / ".git").exists():
            return current

        current = current.parent

    raise RuntimeError(
        "Impossible de trouver la racine du projet (.git)"
    )

PROJECT_ROOT = find_project_root()


OUTPUT_DIR = PROJECT_ROOT / "exchanges"
OUTPUT_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

OUTPUT_FILE = OUTPUT_DIR / f"AcousticBrain_{timestamp}.codebase"

EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
}

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "docs",
    "exchanges",
    "knowledge",
    "tools",
    "ARCHITECTURE.md",
    "README.md",
    "requirements.txt",
    "ROADMAP.md",
    "exchanges",
    "measurements"
}

IGNORE_FILES = {
    "AcousticBrain.codebase",
}


def ignored(path: Path):

    for part in path.parts:
        if part in IGNORE_DIRS:
            return True

    if path.name in IGNORE_FILES:
        return True

    if path.suffix not in EXTENSIONS:
        return True

    return False


def tree(files):

    lines = []

    for file in files:
        lines.append(file.as_posix())

    return "\n".join(lines)


def main():

    files = []

    for file in PROJECT_ROOT.rglob("*"):

        if file.is_file() and not ignored(file):

            files.append(file.relative_to(PROJECT_ROOT))

    files.sort()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

        out.write("#" * 80 + "\n")
        out.write("ACOUSTICBRAIN CODEBASE\n")
        out.write("#" * 80 + "\n\n")

        out.write(f"Generated : {datetime.now()}\n")
        out.write(f"Python    : {platform.python_version()}\n")
        out.write(f"Files     : {len(files)}\n\n")

        out.write("#" * 80 + "\n")
        out.write("TREE\n")
        out.write("#" * 80 + "\n\n")

        out.write(tree(files))

        out.write("\n\n")

        out.write("#" * 80 + "\n")
        out.write("FILES\n")
        out.write("#" * 80 + "\n\n")

        for file in files:

            print(file)

            out.write(f"<<<FILE:{file.as_posix()}>>>\n")

            content = file.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            out.write(content)

            if not content.endswith("\n"):
                out.write("\n")

            out.write("<<<END FILE>>>\n\n")

    print()
    print("Export terminé.")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()