"""
test_parameter_validator.py

Quick test of ParameterValidator to ensure validation logic works.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parameter_validator import ParameterValidator
import json

validator = ParameterValidator()

# Test 1: Valid complete config
print("=== Test 1: Valid complete config ===")
valid_config = {
    "warehouse_config": {
        "overall_layout": {
            "rows": 3,
            "row_spacing": 2500.0,
            "orientation": "east-west"
        }
    },
    "racking_system": {
        "dimensions": {
            "bay_width": 2000.0,
            "bay_depth": 1200.0,
            "total_height": 5000.0
        },
        "structure": {
            "levels": 3,
            "first_beam_height": 300.0,
            "beam_spacing": 1500.0
        }
    }
}

result, errors = validator.validate_and_complete(valid_config)
print(f"Errors: {errors if errors else 'None'}")
print(f"Result dimensions: bay_width={result['racking_system']['dimensions']['bay_width']}")

# Test 2: Out-of-range parameter (should be clamped)
print("\n=== Test 2: Out-of-range bay_width (should clamp to 4000) ===")
invalid_config = {
    "warehouse_config": {"overall_layout": {}},
    "racking_system": {
        "dimensions": {
            "bay_width": 5000.0,  # exceeds max of 4000
            "bay_depth": 1000.0,
            "total_height": 6000.0
        },
        "structure": {
            "levels": 5,
            "first_beam_height": 200.0,
            "beam_spacing": 1000.0
        }
    }
}

result, errors = validator.validate_and_complete(invalid_config)
print(f"Errors: {len(errors)} message(s)")
for e in errors:
    print(f"  - {e}")
print(f"Clamped bay_width: {result['racking_system']['dimensions']['bay_width']}")

# Test 3: Logic error (total_height < required minimum)
print("\n=== Test 3: Logic error (total_height too low) ===")
logic_error_config = {
    "warehouse_config": {"overall_layout": {}},
    "racking_system": {
        "dimensions": {
            "bay_width": 2000.0,
            "bay_depth": 1000.0,
            "total_height": 3000.0  # too low for 5 levels
        },
        "structure": {
            "levels": 5,
            "first_beam_height": 200.0,
            "beam_spacing": 1000.0
        }
    }
}

result, errors = validator.validate_and_complete(logic_error_config)
print(f"Errors: {len(errors)} message(s)")
for e in errors:
    print(f"  - {e}")

# Test 4: Empty/missing config (should fill defaults)
print("\n=== Test 4: Empty config (should fill defaults) ===")
empty_config = {}

result, errors = validator.validate_and_complete(empty_config)
print(f"Errors: {len(errors)} message(s)")
for e in errors:
    print(f"  - {e}")
print(f"Completed config has {len(result.keys())} top-level keys")
print(f"Defaults filled: bay_width={result['racking_system']['dimensions']['bay_width']}, levels={result['racking_system']['structure']['levels']}")

print("\n=== All tests completed ===")
