"""
backend/parameter_extractor.py

JSON-aware extractor shared by backend modules. Attempts to parse structured
JSON from the model output and map it into the racking parameter format used
by M3. Falls back to conservative defaults if parsing fails.
"""
import json
import re
from typing import Dict, Any, Optional


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # Fallback: find first balanced JSON object
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                candidate = text[start:i+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    return None
    return None


def extract_from_image_description(description: str) -> Dict[str, Any]:
    parsed = _extract_json_from_text(description)

    defaults = {"bay_width": 2400.0, "bay_depth": 1000.0, "level_height": 1800.0, "levels": 3}

    if not parsed:
        return {
            "warehouse_config": {"overall_layout": {"rows": 2, "row_spacing": 3000.0, "orientation": "north-south"}},
            "racking_system": {
                "dimensions": {"bay_width": defaults["bay_width"], "bay_depth": defaults["bay_depth"], "total_height": defaults["level_height"] * defaults["levels"]},
                "structure": {"levels": defaults["levels"], "first_beam_height": 200.0, "beam_spacing": defaults["level_height"]},
                "components": {
                    "upright": {"type": "upright", "section_size": "80x60", "color": "blue", "material": "steel"},
                    "beam": {"type": "beam", "section_size": "50x100", "color": "orange", "connection_type": "hooked"},
                    "decking": {"has_decking": True, "type": "wire-mesh", "thickness": 30.0}
                },
                "connection_details": {"beam_to_upright": {"method": "hooked", "bolt_count": 0, "weld_length": 0.0}, "decking_to_beam": {"method": "clip", "clip_spacing": 400.0}}
            }
        }

    estimates = parsed.get("estimates", {}) if isinstance(parsed, dict) else {}
    vertical = parsed.get("vertical_components", {}) if isinstance(parsed, dict) else {}
    beams = parsed.get("beams", {}) if isinstance(parsed, dict) else {}
    decking = parsed.get("decking", {}) if isinstance(parsed, dict) else {}
    colors = parsed.get("colors", {}) if isinstance(parsed, dict) else {}

    bay_width = estimates.get("bay_width_mm") or estimates.get("bay_width") or defaults["bay_width"]
    bay_depth = estimates.get("bay_depth_mm") or estimates.get("bay_depth") or defaults["bay_depth"]
    level_h = estimates.get("level_height_mm") or estimates.get("level_height") or defaults["level_height"]
    levels = vertical.get("count") or defaults["levels"]
    try:
        levels = int(levels)
    except Exception:
        levels = defaults["levels"]

    total_height = float(level_h) * levels if level_h else defaults["level_height"] * levels

    racking = {
        "dimensions": {"bay_width": float(bay_width), "bay_depth": float(bay_depth), "total_height": float(total_height)},
        "structure": {"levels": levels, "first_beam_height": float(level_h), "beam_spacing": float(level_h)},
        "components": {
            "upright": {"type": vertical.get("section", "upright"), "section_size": vertical.get("section", "80x60"), "color": vertical.get("color") or colors.get("frame") or "UNKNOWN", "material": vertical.get("material", "steel")},
            "beam": {"type": beams.get("type", "beam"), "section_size": beams.get("section", "50x100"), "color": beams.get("color") or colors.get("frame") or "UNKNOWN", "connection_type": beams.get("connection", beams.get("connection_type", "hooked"))},
            "decking": {"has_decking": bool(decking), "type": decking.get("type", "wire-mesh"), "thickness": decking.get("thickness", 30.0)}
        },
        "connection_details": {"beam_to_upright": {"method": beams.get("connection", "hooked"), "bolt_count": 0, "weld_length": 0.0}, "decking_to_beam": {"method": decking.get("method", "clip"), "clip_spacing": decking.get("clip_spacing", 400.0)}}
    }

    return {"warehouse_config": {"overall_layout": {"rows": 1, "row_spacing": 3000.0, "orientation": "unknown"}}, "racking_system": racking}


def merge_with_overrides(base_params: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not overrides:
        return base_params
    result = json.loads(json.dumps(base_params))

    def merge_dict(target, source):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                merge_dict(target[key], value)
            else:
                target[key] = value

    merge_dict(result, overrides)
    return result
