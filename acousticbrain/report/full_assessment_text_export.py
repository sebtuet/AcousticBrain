from contextlib import suppress
import os
from pathlib import Path
import tempfile


class FullAssessmentTextExportError(ValueError):
    """Raised when the deterministic full assessment cannot be exported."""


class FullAssessmentTextExporter:
    """Writes one captured full-assessment rendering without replacing files."""

    def __init__(self, path):
        self.path = Path(path)

    def write(self, data):
        temporary_path = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.link(temporary_path, self.path)
        except FileExistsError as error:
            raise FullAssessmentTextExportError(
                f"Full assessment output already exists: {self.path}"
            ) from error
        except OSError as error:
            raise FullAssessmentTextExportError(
                f"Cannot write full assessment output: {self.path}: {error}"
            ) from error
        finally:
            if temporary_path is not None:
                with suppress(OSError):
                    temporary_path.unlink()
