"""Pure-Python geometry contract used before the CadQuery translator."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


class GeometryContractError(ValueError):
    """Raised when an assembly cannot be constructed safely."""


@dataclass(frozen=True)
class Layout:
    width: float
    height: float
    depth: float
    bay_count: int
    layers: int
    rows: tuple[tuple[float, float], ...]
    frame_x: tuple[float, ...]
    beam_z: tuple[float, ...]
    bracing_margin: float
    brace_height: float
    brace_segments: int
    counts: dict[str, int]
    planned_counts: dict[str, int]


def _positive(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GeometryContractError(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise GeometryContractError(f"{name} must be greater than zero")
    return value


def _component_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = data.get("components")
    if not isinstance(components, list):
        raise GeometryContractError("components must be a list")
    result: dict[str, dict[str, Any]] = {}
    for item in components:
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            raise GeometryContractError("each component needs a type and parameters")
        kind = item["type"]
        if kind in result:
            raise GeometryContractError(f"duplicate component type: {kind}")
        params = item.get("parameters")
        if not isinstance(params, dict):
            raise GeometryContractError(f"{kind}.parameters must be an object")
        result[kind] = params
    missing = {"column", "beam", "bracing"} - result.keys()
    if missing:
        raise GeometryContractError(f"missing required components: {', '.join(sorted(missing))}")
    return result


def build_layout(
    data: dict[str, Any],
    *,
    bottom_offset: float = 300.0,
    top_clearance: float = 400.0,
    panel_thickness: float = 20.0,
    # Total clearance removed from the top and bottom of the brace run.
    bracing_margin: float = 100.0,
    bracing_target_spacing: float = 650.0,
) -> Layout:
    """Validate an instance and return its deterministic construction plan."""
    if not isinstance(data, dict):
        raise GeometryContractError("assembly must be an object")
    gc = data.get("global_constraints")
    if not isinstance(gc, dict):
        raise GeometryContractError("global_constraints must be an object")
    width = _positive("global_constraints.width", gc.get("width"))
    height = _positive("global_constraints.height", gc.get("height"))
    depth = _positive("global_constraints.depth", gc.get("depth"))
    bay_count = gc.get("bay_count")
    if isinstance(bay_count, bool) or not isinstance(bay_count, int) or bay_count < 1:
        raise GeometryContractError("global_constraints.bay_count must be an integer >= 1")
    is_double = gc.get("is_double_row")
    if not isinstance(is_double, bool):
        raise GeometryContractError("global_constraints.is_double_row must be boolean")
    spacer = gc.get("spacer_length", 200.0)
    if isinstance(spacer, bool) or not isinstance(spacer, (int, float)) or spacer < 0:
        raise GeometryContractError("global_constraints.spacer_length must be >= 0")
    spacer = float(spacer)

    components = _component_map(data)
    column = components["column"]
    beam = components["beam"]
    bracing = components["bracing"]
    for field in ("width", "depth", "thickness"):
        _positive(f"column.{field}", column.get(field))
    for field in ("width", "height"):
        _positive(f"beam.{field}", beam.get(field))
    layers = beam.get("layers")
    if isinstance(layers, bool) or not isinstance(layers, int) or layers < 1:
        raise GeometryContractError("beam.layers must be an integer >= 1")
    for field in ("width", "thickness"):
        _positive(f"bracing.{field}", bracing.get(field))

    bottom_offset = _positive("bottom_offset", bottom_offset)
    top_clearance = _positive("top_clearance", top_clearance)
    panel_thickness = _positive("panel_thickness", panel_thickness)
    bracing_margin = _positive("bracing_margin", bracing_margin)
    bracing_target_spacing = _positive("bracing_target_spacing", bracing_target_spacing)
    if bottom_offset >= height:
        raise GeometryContractError("bottom_offset must be below total height")
    if layers > 1 and bottom_offset + top_clearance >= height:
        raise GeometryContractError("bottom_offset + top_clearance leaves no layer span")
    if width <= column["width"] + 10:
        raise GeometryContractError("width leaves no usable panel span after column clearance")
    if height <= bracing_margin:
        raise GeometryContractError("height leaves no room for bracing")

    row_count = 2 if is_double else 1
    rows: list[tuple[float, float]] = [(0.0, depth)]
    if is_double:
        rows.append((depth + spacer, 2 * depth + spacer))
    frame_x = tuple(i * width for i in range(bay_count + 1))
    if layers == 1:
        beam_z = (bottom_offset,)
    else:
        gap = (height - bottom_offset - top_clearance) / (layers - 1)
        beam_z = tuple(bottom_offset + i * gap for i in range(layers))
    if any(z <= 0 or z >= height for z in beam_z):
        raise GeometryContractError("beam levels must be inside the total height")

    brace_height = height - bracing_margin
    brace_segments = max(1, math.ceil(brace_height / bracing_target_spacing))
    counts = {
        "columns": row_count * (bay_count + 1) * 2,
        "base_plates": row_count * (bay_count + 1) * 2,
        "beams": row_count * bay_count * layers * 2,
        "panels": row_count * bay_count * layers,
        "braces": row_count * 2 * brace_segments,
        # The current CadQuery translator does not create spacer solids yet.
        # Keep generated counts honest and expose the intended extension separately.
        "spacers": 0,
    }
    planned_counts = {
        "spacers": (bay_count + 1) * layers if is_double else 0,
    }
    return Layout(
        width=width,
        height=height,
        depth=depth,
        bay_count=bay_count,
        layers=layers,
        rows=tuple(rows),
        frame_x=frame_x,
        beam_z=beam_z,
        bracing_margin=bracing_margin,
        brace_height=brace_height,
        brace_segments=brace_segments,
        counts=counts,
        planned_counts=planned_counts,
    )


def layout_from_json(path: str) -> Layout:
    import json
    with open(path, "r", encoding="utf-8") as handle:
        return build_layout(json.load(handle))


def inspect_instance(data: dict[str, Any]) -> dict[str, Any]:
    """Return a UI-friendly inspection result without importing CadQuery."""
    try:
        layout = build_layout(data)
    except GeometryContractError as exc:
        return {"status": "error", "message": str(exc)}
    return {
        "status": "ok",
        "layout": {
            "width": layout.width,
            "height": layout.height,
            "depth": layout.depth,
            "bay_count": layout.bay_count,
            "layers": layout.layers,
            "rows": layout.rows,
            "frame_x": layout.frame_x,
            "beam_z": layout.beam_z,
            "bracing_margin": layout.bracing_margin,
            "brace_height": layout.brace_height,
            "brace_segments": layout.brace_segments,
            "counts": layout.counts,
            "planned_counts": layout.planned_counts,
        },
    }
