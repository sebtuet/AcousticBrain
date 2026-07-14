from dataclasses import dataclass
from math import sqrt


PLANAR_TOLERANCE_M = 1e-7


def _coordinates(point):
    return float(point.x_m), float(point.y_m), float(point.z_m)


def _subtract(first, second):
    return tuple(a - b for a, b in zip(first, second))


def _dot(first, second):
    return sum(a * b for a, b in zip(first, second))


def _cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _norm(vector):
    return sqrt(_dot(vector, vector))


def _normalize(vector):
    magnitude = _norm(vector)
    if magnitude <= PLANAR_TOLERANCE_M:
        raise ValueError("Planar vector magnitude is insufficient.")
    return tuple(value / magnitude for value in vector)


@dataclass(frozen=True)
class PlanarBasis:
    origin: tuple[float, float, float]
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    normal: tuple[float, float, float]
    area_m2: float


def derive_planar_basis(vertices, *, tolerance=PLANAR_TOLERANCE_M):
    points = tuple(_coordinates(item) for item in vertices)
    if len(points) < 3:
        raise ValueError("A plane requires at least three vertices.")
    origin = points[0]
    first_edge = None
    normal_vector = None
    for index in range(1, len(points)):
        candidate = _subtract(points[index], origin)
        if _norm(candidate) <= tolerance:
            continue
        if first_edge is None:
            first_edge = candidate
            continue
        cross = _cross(first_edge, candidate)
        if _norm(cross) > tolerance:
            normal_vector = cross
            break
    if first_edge is None or normal_vector is None:
        raise ValueError("Planar polygon has zero area.")
    u_axis = _normalize(first_edge)
    normal = _normalize(normal_vector)
    v_axis = _cross(normal, u_axis)
    for point in points:
        if abs(_dot(_subtract(point, origin), normal)) > tolerance:
            raise ValueError("Planar polygon vertices are not coplanar.")
    projected = tuple(
        (
            _dot(_subtract(point, origin), u_axis),
            _dot(_subtract(point, origin), v_axis),
        )
        for point in points
    )
    area = abs(sum(
        first[0] * second[1] - second[0] * first[1]
        for first, second in zip(projected, projected[1:] + projected[:1])
    )) / 2.0
    if area <= tolerance:
        raise ValueError("Planar polygon has zero area.")
    return PlanarBasis(origin, u_axis, v_axis, normal, area)


def project_point(point, basis):
    coordinates = _coordinates(point) if hasattr(point, "x_m") else tuple(point)
    relative = _subtract(coordinates, basis.origin)
    return (
        _dot(relative, basis.u_axis),
        _dot(relative, basis.v_axis),
        _dot(relative, basis.normal),
    )


def polygon_is_convex(vertices_2d, *, tolerance=PLANAR_TOLERANCE_M):
    points = tuple(vertices_2d)
    if len(points) < 3 or len(set(points)) != len(points):
        return False
    sign = 0
    for index in range(len(points)):
        first = points[index]
        second = points[(index + 1) % len(points)]
        third = points[(index + 2) % len(points)]
        turn = (
            (second[0] - first[0]) * (third[1] - second[1])
            - (second[1] - first[1]) * (third[0] - second[0])
        )
        if abs(turn) <= tolerance:
            continue
        current = 1 if turn > 0.0 else -1
        if sign and current != sign:
            return False
        sign = current
    return sign != 0


def point_in_convex_polygon(point, polygon, *, tolerance=PLANAR_TOLERANCE_M):
    sign = 0
    for first, second in zip(polygon, polygon[1:] + polygon[:1]):
        cross = (
            (second[0] - first[0]) * (point[1] - first[1])
            - (second[1] - first[1]) * (point[0] - first[0])
        )
        if abs(cross) <= tolerance:
            continue
        current = 1 if cross > 0.0 else -1
        if sign and current != sign:
            return False
        sign = current
    return True
