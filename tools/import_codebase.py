#!/usr/bin/env python3

"""
AcousticBrain Codebase Importer

Compatible avec :

    ACOUSTICBRAIN CODEBASE
    ACOUSTICBRAIN PATCH
"""

from pathlib import Path
import argparse
import sys

START = "<<<FILE:"
END = "<<<END FILE>>>"

PROJECT_PACKAGE = "acousticbrain"


# ----------------------------------------------------------
# Recherche automatique de la racine Git
# ----------------------------------------------------------

def find_project_root():

    current = Path.cwd().resolve()

    while current != current.parent:

        if (current / ".git").exists():

            return current

        current = current.parent

    return Path.cwd().resolve()


PROJECT_ROOT = find_project_root()


# ----------------------------------------------------------
# Normalisation des chemins
# ----------------------------------------------------------

def normalize(path: str) -> Path:

    path = path.replace("\\", "/")

    #
    # init.py -> __init__.py
    #

    if path.endswith("/init.py"):

        path = path[:-7] + "/__init__.py"

    elif path == "init.py":

        path = "__init__.py"

    #
    # Ajout automatique de acousticbrain/
    #

    if not path.startswith(PROJECT_PACKAGE + "/"):

        prefixes = (

            "analysis/",
            "analyzers/",
            "assistant/",
            "brain/",
            "classifiers/",
            "diagnostics/",
            "importers/",
            "knowledge/",
            "models/",
            "physics/",
            "project/",
            "report/",
            "utils/",
        )

        for prefix in prefixes:

            if path.startswith(prefix):

                path = PROJECT_PACKAGE + "/" + path

                break

    return PROJECT_ROOT / Path(path)


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(

    "file",

    help="Patch ou Codebase",

)

parser.add_argument(

    "--force",

    action="store_true",

)

args = parser.parse_args()

source = Path(args.file)

if not source.exists():

    print("Fichier introuvable :", source)

    sys.exit(1)

text = source.read_text(

    encoding="utf-8",

    errors="ignore",

)

is_patch = "ACOUSTICBRAIN PATCH" in text
is_codebase = "ACOUSTICBRAIN CODEBASE" in text

if not (is_patch or is_codebase):

    print("Format inconnu.")

    sys.exit(1)

if not args.force:

    if is_patch:

        answer = input(

            "Importer le PATCH ? (y/N) "

        )

    else:

        answer = input(

            "Reconstruire toute la codebase ? (y/N) "

        )

    if answer.lower() != "y":

        sys.exit(0)

current = None

buffer = []

modified = 0

created = 0

for line in text.splitlines():

    if line.startswith(START):

        current = line[len(START):-3].strip()

        buffer = []

        continue

    if line == END:

        destination = normalize(current)

        destination.parent.mkdir(

            parents=True,

            exist_ok=True,

        )

        existed = destination.exists()

        destination.write_text(

            "\n".join(buffer),

            encoding="utf-8",

        )

        if existed:

            print("UPDATE :", destination.relative_to(PROJECT_ROOT))

            modified += 1

        else:

            print("CREATE :", destination.relative_to(PROJECT_ROOT))

            created += 1

        current = None

        continue

    if current is not None:

        buffer.append(line)

print()

print("--------------------------------------------------")

if is_patch:

    print("PATCH IMPORT")

else:

    print("CODEBASE IMPORT")

print("--------------------------------------------------")

print(f"Created : {created}")

print(f"Updated : {modified}")

print(f"Total   : {created + modified}")

print("--------------------------------------------------")