"""
parameter_extractor.py

Extract structured warehouse parameters from image description or use rule-based extraction.
For now, this is a simple mock/rule-based extractor. Future versions can use OpenAI GPT to
parse descriptions into JSON.
"""
import json
from typing import Dict, Any, Optional


def extract_from_image_description(description: str) -> Dict[str, Any]:
    """
    Extract warehouse parameters from Hugging Face BLIP image description.
    
    This is a simplified rule-based extractor. For production, integrate with:
    - OpenAI GPT-4 (vision) API to directly extract JSON from image
    - Or use a structured extraction pipeline (e.g., spaCy NER + rules)
    
    Args:
        description: Natural language description from BLIP or other model
    
    Returns:
        Dictionary with extracted warehouse parameters (may be incomplete)
    """
    # For now, return a representative example structure
    # In practice, you'd parse the description to extract these values
    extracted = {
        "warehouse_config": {
            "overall_layout": {
                "rows": 2,
                "row_spacing": 3000.0,
                "orientation": "north-south"
            }
        },
        "racking_system": {
            "dimensions": {
                "bay_width": 2400.0,
                "bay_depth": 1000.0,
                "total_height": 6000.0
            },
            "structure": {
                "levels": 3,
                "first_beam_height": 200.0,
                "beam_spacing": 1800.0
            },
            "components": {
                "upright": {
                    "type": "L-beam",
                    "section_size": "80x60",
                    "color": "blue",
                    "material": "steel"
                },
                "beam": {
                    "type": "P-beam",
                    "section_size": "50x100",
                    "color": "orange",
                    "connection_type": "clip-on"
                },
                "decking": {
                    "has_decking": True,
                    "type": "wire-mesh",
                    "thickness": 30.0
                }
            },
            "connection_details": {
                "beam_to_upright": {
                    "method": "clip",
                    "bolt_count": 0,
                    "weld_length": 0.0
                },
                "decking_to_beam": {
                    "method": "clip",
                    "clip_spacing": 400.0
                }
            }
        }
    }
    
    # TODO: Parse description to extract actual values
    # For now, just return the template
    return extracted


def merge_with_overrides(base_params: Dict[str, Any], 
                        overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge extracted parameters with user overrides (for UI editing).
    
    Args:
        base_params: Extracted parameters
        overrides: User-provided overrides (flattened dict or nested)
    
    Returns:
        Merged parameters
    """
    if not overrides:
        return base_params
    
    # Simple recursive merge
    result = json.loads(json.dumps(base_params))  # deep copy
    
    def merge_dict(target, source):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                merge_dict(target[key], value)
            else:
                target[key] = value
    
    merge_dict(result, overrides)
    return result
