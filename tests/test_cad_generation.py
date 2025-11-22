"""
M3 Phase 4: CAD Generation Unit Tests
Tests component generation, assembly, and STEP export
"""

import pytest
from pathlib import Path
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.M3.component_factory import UpRightBuilder, BeamBuilder, DeckingBuilder
from backend.M3.assembly_manager import AssemblyBuilder
import cadquery as cq


class TestComponentFactory:
    """Tests for individual component builders"""
    
    def test_upright_geometry(self):
        """Verify upright column has correct dimensions"""
        height = 6000
        section = "80x60"
        
        upright = UpRightBuilder.build(height, section)
        bbox = upright.BoundingBox()
        
        # Check dimensions (allow 1mm tolerance for floating point)
        assert 79 <= bbox.xlen <= 81, f"Width {bbox.xlen} not in expected range [79-81]"
        assert 59 <= bbox.ylen <= 61, f"Depth {bbox.ylen} not in expected range [59-61]"
        assert 5999 <= bbox.zlen <= 6001, f"Height {bbox.zlen} not in expected range [5999-6001]"
    
    
    def test_beam_geometry(self):
        """Verify beam has correct dimensions"""
        length = 1000
        section = "50x100"
        
        beam = BeamBuilder.build(length, section)
        bbox = beam.BoundingBox()
        
        # Check dimensions
        assert 99 <= bbox.xlen <= 101, f"Width {bbox.xlen} not in expected range [99-101]"
        assert 999 <= bbox.ylen <= 1001, f"Length {bbox.ylen} not in expected range [999-1001]"
        assert 49 <= bbox.zlen <= 51, f"Height {bbox.zlen} not in expected range [49-51]"
    
    
    def test_decking_geometry(self):
        """Verify decking panel has correct dimensions"""
        width = 2400
        depth = 1000
        thickness = 10
        
        decking = DeckingBuilder.build(width, depth, thickness)
        bbox = decking.BoundingBox()
        
        # Check dimensions
        assert 2399 <= bbox.xlen <= 2401, f"Width {bbox.xlen} not near {width}"
        assert 999 <= bbox.ylen <= 1001, f"Depth {bbox.ylen} not near {depth}"
        assert 9 <= bbox.zlen <= 11, f"Thickness {bbox.zlen} not near {thickness}"
    
    
    def test_decking_thickness_clamping(self):
        """Verify thickness is clamped to valid range"""
        # Test too thin
        decking_thin = DeckingBuilder.build(2400, 1000, 5)
        bbox_thin = decking_thin.BoundingBox()
        assert bbox_thin.zlen >= 10, "Thickness should be clamped to minimum 10mm"
        
        # Test too thick
        decking_thick = DeckingBuilder.build(2400, 1000, 100)
        bbox_thick = decking_thick.BoundingBox()
        assert bbox_thick.zlen <= 50, "Thickness should be clamped to maximum 50mm"


class TestAssemblyBuilder:
    """Tests for warehouse assembly"""
    
    @pytest.fixture
    def config(self):
        """Standard test configuration"""
        return {
            "racking_system": {
                "dimensions": {
                    "bay_width": 2400,
                    "bay_depth": 1000,
                    "total_height": 6000
                },
                "structure": {
                    "levels": 3,
                    "first_beam_height": 200,
                    "beam_spacing": 1800
                }
            }
        }
    
    
    def test_assembly_builder_init(self, config):
        """Verify assembly builder initializes with correct parameters"""
        builder = AssemblyBuilder(config)
        
        assert builder.bay_width == 2400
        assert builder.bay_depth == 1000
        assert builder.total_height == 6000
        assert builder.levels == 3
        assert builder.first_beam_height == 200
    
    
    def test_single_bay_assembly(self, config):
        """Verify single bay generates expected components"""
        builder = AssemblyBuilder(config)
        parts = builder.build_single_bay()
        
        # Should have 5 components: 2 uprights, 2 beams, 1 decking
        assert len(parts) == 5, f"Expected 5 parts, got {len(parts)}"
        
        # All parts should be valid CadQuery solids
        for i, part in enumerate(parts):
            bbox = part.BoundingBox()
            assert bbox is not None, f"Part {i} has no bounding box"
            assert bbox.xlen > 0 and bbox.ylen > 0 and bbox.zlen > 0, f"Part {i} has zero dimensions"
    
    
    def test_assembly_bbox(self, config):
        """Verify assembled warehouse has reasonable dimensions"""
        builder = AssemblyBuilder(config)
        assembly = builder.assemble_warehouse()
        
        bbox = assembly.BoundingBox()
        
        # Width should be at least bay_width
        assert bbox.xlen >= config["racking_system"]["dimensions"]["bay_width"] - 100
        
        # Depth should be at least bay_depth
        assert bbox.ylen >= config["racking_system"]["dimensions"]["bay_depth"] - 100
        
        # Height should be at least total_height
        assert bbox.zlen >= config["racking_system"]["dimensions"]["total_height"] - 100
    
    
    def test_missing_config_fields(self):
        """Verify builder handles missing config gracefully"""
        bad_config = {}
        
        # Should raise or use defaults
        try:
            builder = AssemblyBuilder(bad_config)
            # If it doesn't raise, it should have sensible defaults
            assert builder.bay_width > 0
            assert builder.total_height > 0
        except ValueError:
            # Also acceptable - explicit error on bad config
            pass


class TestStepExport:
    """Tests for STEP file export"""
    
    @pytest.fixture
    def config(self):
        """Standard test configuration"""
        return {
            "racking_system": {
                "dimensions": {
                    "bay_width": 2400,
                    "bay_depth": 1000,
                    "total_height": 6000
                },
                "structure": {
                    "levels": 3,
                    "first_beam_height": 200,
                    "beam_spacing": 1800
                }
            }
        }
    
    
    def test_step_export_creates_file(self, config):
        """Verify STEP export creates a file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = AssemblyBuilder(config)
            step_path = Path(tmpdir) / "test_warehouse.step"
            
            success = builder.export_step(str(step_path))
            
            assert success, "STEP export should return True"
            assert step_path.exists(), f"STEP file not created at {step_path}"
    
    
    def test_step_export_file_size(self, config):
        """Verify exported STEP file has reasonable size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = AssemblyBuilder(config)
            step_path = Path(tmpdir) / "test_warehouse.step"
            
            success = builder.export_step(str(step_path))
            
            assert success, "STEP export should succeed"
            
            file_size = step_path.stat().st_size
            assert file_size > 1024, f"STEP file too small ({file_size} bytes), expected > 1KB"
            assert file_size < 10 * 1024 * 1024, f"STEP file too large ({file_size} bytes)"
    
    
    def test_step_export_creates_subdirs(self, config):
        """Verify export creates parent directories if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = AssemblyBuilder(config)
            step_path = Path(tmpdir) / "deep" / "nested" / "path" / "warehouse.step"
            
            success = builder.export_step(str(step_path))
            
            assert success, "STEP export should succeed with nested path"
            assert step_path.exists(), "File should exist in nested directory"
    
    
    def test_step_export_invalid_path(self, config):
        """Verify graceful handling of invalid export paths"""
        builder = AssemblyBuilder(config)
        # Use invalid path (e.g., read-only or invalid characters)
        # Windows: NUL is a reserved device
        step_path = "NUL:/invalid/path.step"
        
        success = builder.export_step(step_path)
        
        # Should return False for invalid path, not crash
        assert not success, "Export to invalid path should return False"


class TestIntegration:
    """End-to-end integration tests"""
    
    def test_full_pipeline(self):
        """Test complete pipeline: config -> build -> export"""
        config = {
            "warehouse_config": {
                "name": "Test Warehouse",
                "location": "Test Location"
            },
            "racking_system": {
                "dimensions": {
                    "bay_width": 2400,
                    "bay_depth": 1000,
                    "total_height": 6000
                },
                "structure": {
                    "levels": 3,
                    "first_beam_height": 200,
                    "beam_spacing": 1800
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create builder
            builder = AssemblyBuilder(config)
            
            # Generate single bay
            parts = builder.build_single_bay()
            assert len(parts) == 5
            
            # Assemble warehouse
            assembly = builder.assemble_warehouse()
            bbox = assembly.BoundingBox()
            assert bbox.xlen > 0 and bbox.ylen > 0 and bbox.zlen > 0
            
            # Export to STEP
            step_path = str(Path(tmpdir) / "integration_test.step")
            success = builder.export_step(step_path)
            assert success
            
            # Verify file
            assert Path(step_path).exists()
            assert Path(step_path).stat().st_size > 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
