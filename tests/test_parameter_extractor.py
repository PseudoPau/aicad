import json
from parameter_extractor import extract_from_image_description


def test_extract_fenced_json():
    desc = '''Some analysis text
```json
{
  "estimates": {"bay_width_mm": 2400, "bay_depth_mm": 1000, "level_height_mm": 1800},
  "vertical_components": {"count": 1, "section": "80x60", "color": "blue"},
  "beams": {"type": "P-beam", "section": "50x100", "connection": "hooked"}
}
```
more text'''

    result = extract_from_image_description(desc)
    rs = result.get("racking_system")
    assert rs is not None
    dims = rs.get("dimensions")
    assert dims["bay_width"] == 2400.0
    assert dims["bay_depth"] == 1000.0


def test_extract_inline_json():
    desc = 'Analysis: {"estimates":{"bay_width":3000,"bay_depth":1200,"level_height":2000},"vertical_components":{"count":2}} end'
    result = extract_from_image_description(desc)
    rs = result.get("racking_system")
    assert rs is not None
    dims = rs.get("dimensions")
    assert dims["bay_width"] == 3000.0
    assert dims["bay_depth"] == 1200.0


def test_extract_malformed_fallback():
    desc = 'A messy description without JSON at all; some words and numbers 2400 1000'
    result = extract_from_image_description(desc)
    # Should return a dict with racking_system and defaults
    assert isinstance(result, dict)
    assert "racking_system" in result
    dims = result["racking_system"]["dimensions"]
    assert dims["bay_width"] > 0
