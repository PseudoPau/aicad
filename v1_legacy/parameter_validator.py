"""
parameter_validator.py

Validate and complete warehouse configuration parameters.
Implements range checks, logic validation, and default value filling.
"""
from typing import Dict, Any, Tuple, List


class ParameterValidator:
    """Validate and complete warehouse configuration parameters."""
    
    # Define valid ranges for each parameter
    RANGES = {
        "warehouse_config.overall_layout.rows": (1, 20),
        "warehouse_config.overall_layout.row_spacing": (1000, 5000),
        "racking_system.dimensions.bay_width": (1000, 4000),
        "racking_system.dimensions.bay_depth": (800, 2000),
        "racking_system.dimensions.total_height": (2000, 10000),
        "racking_system.structure.levels": (2, 10),
        "racking_system.structure.first_beam_height": (100, 500),
        "racking_system.structure.beam_spacing": (400, 2000),
        "racking_system.components.decking.thickness": (10, 50),
        "racking_system.connection_details.beam_to_upright.bolt_count": (0, 8),
        "racking_system.connection_details.decking_to_beam.clip_spacing": (200, 600),
    }
    
    # Default values for missing parameters
    DEFAULTS = {
        "warehouse_config.overall_layout.rows": 2,
        "warehouse_config.overall_layout.row_spacing": 3000,
        "warehouse_config.overall_layout.orientation": "north-south",
        "racking_system.dimensions.bay_width": 2400,
        "racking_system.dimensions.bay_depth": 1000,
        "racking_system.dimensions.total_height": 6000,
        "racking_system.structure.levels": 3,
        "racking_system.structure.first_beam_height": 200,
        "racking_system.structure.beam_spacing": 1800,
        "racking_system.components.upright.type": "L-beam",
        "racking_system.components.upright.section_size": "80x60",
        "racking_system.components.upright.color": "blue",
        "racking_system.components.upright.material": "steel",
        "racking_system.components.beam.type": "P-beam",
        "racking_system.components.beam.section_size": "50x100",
        "racking_system.components.beam.color": "orange",
        "racking_system.components.beam.connection_type": "clip-on",
        "racking_system.components.decking.has_decking": True,
        "racking_system.components.decking.type": "wire-mesh",
        "racking_system.components.decking.thickness": 30,
        "racking_system.connection_details.beam_to_upright.method": "clip",
        "racking_system.connection_details.beam_to_upright.bolt_count": 0,
        "racking_system.connection_details.beam_to_upright.weld_length": 0,
        "racking_system.connection_details.decking_to_beam.method": "clip",
        "racking_system.connection_details.decking_to_beam.clip_spacing": 400,
    }
    
    def validate_and_complete(self, config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate and complete configuration.
        
        Args:
            config: Configuration dictionary (may be incomplete or invalid)
        
        Returns:
            Tuple of (completed_config, error_messages)
            If error_messages is empty, validation passed.
        """
        errors = []
        
        # Make a deep copy to avoid modifying input
        import json
        completed = json.loads(json.dumps(config))
        
        # Step 1: Check for required fields
        required_fields = [
            "warehouse_config",
            "racking_system"
        ]
        for field in required_fields:
            if field not in completed:
                completed[field] = {}
                errors.append(f"Missing required section: {field}, using defaults")
        
        # Step 2: Validate ranges and fill defaults
        range_errors = self._validate_and_fill_ranges(completed)
        errors.extend(range_errors)
        
        # Step 3: Validate logic consistency
        logic_errors = self._validate_logic(completed)
        errors.extend(logic_errors)
        
        # Step 4: Fill missing values with defaults
        self._fill_defaults(completed)
        
        return completed, errors
    
    def _validate_and_fill_ranges(self, config: Dict[str, Any]) -> List[str]:
        """Validate parameter ranges and log violations."""
        errors = []
        
        def get_nested(d, path):
            """Get value from nested dict using dot notation."""
            keys = path.split(".")
            val = d
            for key in keys:
                if isinstance(val, dict) and key in val:
                    val = val[key]
                else:
                    return None
            return val
        
        def set_nested(d, path, value):
            """Set value in nested dict using dot notation."""
            keys = path.split(".")
            current = d
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
        
        for path, (min_val, max_val) in self.RANGES.items():
            val = get_nested(config, path)
            if val is not None:
                if not isinstance(val, (int, float)):
                    errors.append(f"{path}: expected number, got {type(val).__name__}")
                elif not (min_val <= val <= max_val):
                    clamped = max(min_val, min(val, max_val))
                    set_nested(config, path, clamped)
                    errors.append(f"{path}: {val} out of range [{min_val}, {max_val}], clamped to {clamped}")
        
        return errors
    
    def _validate_logic(self, config: Dict[str, Any]) -> List[str]:
        """Validate logical consistency between parameters."""
        errors = []
        
        # Access nested values
        def get_val(path):
            keys = path.split(".")
            val = config
            for key in keys:
                if isinstance(val, dict):
                    val = val.get(key)
                else:
                    return None
            return val
        
        # Rule 1: total_height > first_beam_height + levels * beam_spacing
        total_height = get_val("racking_system.dimensions.total_height")
        first_beam_height = get_val("racking_system.structure.first_beam_height")
        levels = get_val("racking_system.structure.levels")
        beam_spacing = get_val("racking_system.structure.beam_spacing")
        
        if all(v is not None for v in [total_height, first_beam_height, levels, beam_spacing]):
            min_required_height = first_beam_height + (levels - 1) * beam_spacing
            if total_height < min_required_height:
                errors.append(
                    f"Logic error: total_height ({total_height}) < "
                    f"first_beam_height ({first_beam_height}) + (levels-1)×beam_spacing "
                    f"({min_required_height}). Consider increasing total_height or decreasing levels."
                )
        
        # Rule 2: bay_depth > 0
        bay_depth = get_val("racking_system.dimensions.bay_depth")
        if bay_depth is not None and bay_depth <= 0:
            errors.append("bay_depth must be > 0")
        
        # Rule 3: levels >= 2
        if levels is not None and levels < 2:
            errors.append("levels must be at least 2")
        
        return errors
    
    def _fill_defaults(self, config: Dict[str, Any]) -> None:
        """Fill missing parameters with defaults."""
        def set_nested(d, path, value):
            keys = path.split(".")
            current = d
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            if keys[-1] not in current:
                current[keys[-1]] = value
        
        for path, default_value in self.DEFAULTS.items():
            set_nested(config, path, default_value)
