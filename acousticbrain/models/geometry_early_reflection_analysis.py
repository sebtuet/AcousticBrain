from dataclasses import dataclass

from .geometry_reflection_path import GeometryReflectionPath


@dataclass(frozen=True)
class GeometryEarlyReflectionAnalysis:
    paths: tuple[GeometryReflectionPath, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.paths, tuple) or any(
            not isinstance(item, GeometryReflectionPath) for item in self.paths
        ):
            raise ValueError("Geometry reflection paths must be a typed tuple.")
        if any(
            not isinstance(values, tuple)
            for values in (self.source_analysis_codes, self.applied_rule_codes)
        ):
            raise ValueError("Geometry reflection trace collections must be tuples.")
