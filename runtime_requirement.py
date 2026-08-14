import sys


MINIMUM_PYTHON_VERSION = (3, 10)


def require_supported_python(version_info=None):
    """Reject unsupported interpreters without importing AcousticBrain."""

    current = sys.version_info if version_info is None else version_info
    if tuple(current[:2]) < MINIMUM_PYTHON_VERSION:
        raise RuntimeError(
            "AcousticBrain requires Python 3.10 or newer. "
            f"Current version: {current[0]}.{current[1]}."
        )


def enforce_supported_python(version_info=None):
    try:
        require_supported_python(version_info)
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
