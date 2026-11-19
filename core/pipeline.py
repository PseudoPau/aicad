"""Deterministic, model-free pipeline helpers used by the CLI and the UI.

The vision call is deliberately outside this module.  A fixed JSON instance can
therefore be validated and previewed without an API key, while STEP export
remains an explicit CadQuery-backed operation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .geometry_contract import GeometryContractError, build_layout

try:
    from jsonschema import Draft7Validator
except ImportError:  # pragma: no cover - reported by validate_instance
    Draft7Validator = None


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA_PATH = ROOT_DIR / "schema" / "assembly_schema.json"
DEFAULT_INSTANCE_PATH = ROOT_DIR / "tests" / "shelf_instance.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output"

PANEL_THICKNESS = 20.0
BOTTOM_OFFSET = 300.0
TOP_CLEARANCE = 400.0
BRACING_TARGET_SPACING = 650.0
BRACING_MARGIN = 50.0
BASE_PLATE_THICKNESS = 5.0


def load_instance(instance_path: str | Path = DEFAULT_INSTANCE_PATH) -> dict[str, Any]:
    with Path(instance_path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("instance must be a JSON object")
    return value


def _positive(report: dict[str, Any], value: Any, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        report["errors"].append(f"{name} must be a positive number")


def validate_instance(
    instance: dict[str, Any],
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Validate schema plus the semantic constraints required by translation."""
    report: dict[str, Any] = {"ok": True, "errors": [], "warnings": []}
    if not isinstance(instance, dict):
        report["errors"].append("instance must be a JSON object")
        report["ok"] = False
        return report

    schema_file = Path(schema_path)
    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        if Draft7Validator is None:
            report["warnings"].append("jsonschema is unavailable; schema validation skipped")
        else:
            validator = Draft7Validator(schema)
            for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
                location = ".".join(str(part) for part in error.path) or "$"
                report["errors"].append(f"{location}: {error.message}")
    except Exception as exc:
        report["errors"].append(f"schema validation failed: {exc}")

    constraints = instance.get("global_constraints")
    if not isinstance(constraints, dict):
        report["errors"].append("global_constraints is required")
        constraints = {}
    for name in ("width", "height", "depth"):
        _positive(report, constraints.get(name), f"global_constraints.{name}")
    bay_count = constraints.get("bay_count")
    if not isinstance(bay_count, int) or isinstance(bay_count, bool) or bay_count < 1:
        report["errors"].append("global_constraints.bay_count must be an integer >= 1")
    if not isinstance(constraints.get("is_double_row"), bool):
        report["errors"].append("global_constraints.is_double_row must be boolean")
    if constraints.get("is_double_row"):
        _positive(
            report,
            constraints.get("spacer_length", 200),
            "global_constraints.spacer_length",
        )

    components = instance.get("components")
    if not isinstance(components, list):
        report["errors"].append("components is required and must be an array")
        components = []
    by_type: dict[str, dict[str, Any]] = {}
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            report["errors"].append(f"components[{index}] must be an object")
            continue
        kind = component.get("type")
        params = component.get("parameters")
        if kind in by_type:
            report["warnings"].append(f"duplicate component type: {kind}")
        if isinstance(kind, str) and isinstance(params, dict):
            by_type[kind] = params
            for key, value in params.items():
                if key != "pattern" and key != "layers":
                    _positive(report, value, f"components[{index}].parameters.{key}")
            if "layers" in params and (
                not isinstance(params["layers"], int) or params["layers"] < 1
            ):
                report["errors"].append(
                    f"components[{index}].parameters.layers must be an integer >= 1"
                )
    for required in ("column", "beam", "bracing"):
        if required not in by_type:
            report["errors"].append(f"missing required component: {required}")

    if isinstance(constraints.get("height"), (int, float)) and "beam" in by_type:
        layers = by_type["beam"].get("layers")
        if isinstance(layers, int) and layers > 1:
            usable_height = constraints["height"] - BOTTOM_OFFSET - TOP_CLEARANCE
            if usable_height <= 0:
                report["errors"].append(
                    "height must exceed bottom_offset + top_clearance for multiple layers"
                )

    report["warnings"].append(
        "preview uses explicit assumptions for panel thickness, offsets, and bracing spacing"
    )
    try:
        build_layout(instance)
    except GeometryContractError as exc:
        report["errors"].append(str(exc))
    report["ok"] = not report["errors"]
    return report


def _box(
    item_id: str,
    kind: str,
    origin: tuple[float, float, float],
    size: tuple[float, float, float],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "kind": kind,
        "origin": [round(value, 3) for value in origin],
        "size": [round(value, 3) for value in size],
        **extra,
    }


def build_preview(instance: dict[str, Any]) -> dict[str, Any]:
    """Build the same deterministic placement plan consumed by the CAD translator."""
    report = validate_instance(instance)
    result: dict[str, Any] = {
        "ok": report["ok"],
        "validation": report,
        "units": "mm",
        "items": [],
        "assumptions": {
            "panel_thickness": PANEL_THICKNESS,
            "bottom_offset": BOTTOM_OFFSET,
            "top_clearance": TOP_CLEARANCE,
            "bracing_target_spacing": BRACING_TARGET_SPACING,
            "bracing_margin": BRACING_MARGIN,
            "base_plate_thickness": BASE_PLATE_THICKNESS,
        },
    }
    if not report["ok"]:
        return result

    gc = instance["global_constraints"]
    width, height, depth = gc["width"], gc["height"], gc["depth"]
    bay_count, is_double = gc["bay_count"], gc["is_double_row"]
    spacer = gc.get("spacer_length", 200.0)
    by_type = {component["type"]: component["parameters"] for component in instance["components"]}
    col = by_type["column"]
    beam = by_type["beam"]
    bracing = by_type["bracing"]
    layout = build_layout(instance)
    rows = layout.rows
    layers = layout.layers
    panel_length = width - col["width"] - 10.0
    if panel_length <= 0:
        result["ok"] = False
        result["validation"]["ok"] = False
        result["validation"]["errors"].append("panel length is not positive")
        return result

    items = result["items"]
    for row_index, row in enumerate(rows):
        y_mid = (row[0] + row[1]) / 2
        for column_index in range(bay_count + 1):
            x = column_index * width
            for side, y in enumerate(row):
                items.append(
                    _box(
                        f"base_{row_index}_{column_index}_{side}",
                        "base_plate",
                        (x - (col["width"] + 40) / 2, y - (col["depth"] + 40) / 2, 0),
                        (col["width"] + 40, col["depth"] + 40, BASE_PLATE_THICKNESS),
                    )
                )
                items.append(
                    _box(
                        f"column_{row_index}_{column_index}_{side}",
                        "column",
                        (x - col["width"] / 2, y - col["depth"] / 2, 0),
                        (col["width"], col["depth"], height),
                    )
                )

            if column_index in (0, bay_count):
                segments = layout.brace_segments
                segment_height = layout.brace_height / segments
                for segment in range(segments):
                    z0 = layout.bracing_margin / 2 + segment * segment_height
                    z1 = z0 + segment_height
                    # Match translator.py's alternating X-axis rotations.  The
                    # local brace runs diagonally across the rack depth.
                    direction = -1 if segment % 2 == 0 else 1
                    items.append(
                        {
                            "id": f"brace_{row_index}_{column_index}_{segment}",
                            "kind": "bracing",
                            "start": [
                                round(x, 3),
                                round(y_mid - direction * depth / 2, 3),
                                round(z0, 3),
                            ],
                            "end": [
                                round(x, 3),
                                round(y_mid + direction * depth / 2, 3),
                                round(z1, 3),
                            ],
                            "width": bracing["width"],
                            "thickness": bracing["thickness"],
                        }
                    )

        for bay in range(bay_count):
            x_center = bay * width + width / 2
            for layer, z_beam in enumerate(layout.beam_z):
                beam_length = width - col["width"]
                for side, y in enumerate(row):
                    items.append(
                        _box(
                            f"beam_{row_index}_{bay}_{layer}_{side}",
                            "beam",
                            (x_center - beam_length / 2, y - beam["width"] / 2, z_beam - beam["height"] / 2),
                            (beam_length, beam["width"], beam["height"]),
                        )
                    )
                z_panel = z_beam + beam["height"] / 2 + PANEL_THICKNESS / 2
                items.append(
                    _box(
                        f"panel_{row_index}_{bay}_{layer}",
                        "panel",
                        (x_center - panel_length / 2, y_mid - depth / 2, z_panel - PANEL_THICKNESS / 2),
                        (panel_length, depth, PANEL_THICKNESS),
                    )
                )

    result["bounds"] = {
        "width": layout.width * layout.bay_count,
        "depth": layout.rows[-1][1],
        "height": layout.height,
    }
    result["counts"] = {
        kind: sum(1 for item in items if item["kind"] == kind)
        for kind in ("base_plate", "column", "beam", "panel", "bracing")
    }
    result["layout_counts"] = layout.counts
    result["planned_counts"] = layout.planned_counts
    result["connector_status"] = (
        "not modeled; spacer_length currently affects row placement only"
        if is_double
        else "not applicable for single row"
    )
    return result


def export_step(instance_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Export a validated instance through the existing CadQuery translator."""
    try:
        from cadquery import exporters
        from .translator import run_translation
    except ImportError as exc:
        return {"ok": False, "error": f"CadQuery is unavailable: {exc}"}
    try:
        assembly = run_translation(str(instance_path))
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        exporters.export(assembly.toCompound(), str(output))
        return {"ok": True, "path": str(output)}
    except Exception as exc:
        return {"ok": False, "error": f"STEP export failed: {exc}"}


def run_fixture(
    instance_path: str | Path = DEFAULT_INSTANCE_PATH,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    export_step_file: bool = False,
) -> dict[str, Any]:
    """Run validation and deterministic preview without requiring a model API."""
    instance = load_instance(instance_path)
    validation = validate_instance(instance, schema_path)
    if not validation["ok"]:
        return {"ok": False, "validation": validation}
    preview = build_preview(instance)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    validated_path = output / "validated_instance.json"
    preview_path = output / "preview_manifest.json"
    validated_path.write_text(json.dumps(instance, indent=2, ensure_ascii=False), encoding="utf-8")
    preview_path.write_text(json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8")
    result: dict[str, Any] = {
        "ok": preview["ok"],
        "validation": validation,
        "preview": preview,
        "validated_instance_path": str(validated_path),
        "preview_path": str(preview_path),
    }
    if export_step_file:
        result["step"] = export_step(instance_path, output / "assembly_result.step")
        result["ok"] = result["ok"] and result["step"]["ok"]
    return result
