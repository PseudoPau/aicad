"""
M3 Phase 1: Component Factory
Generates individual CAD components (uprights, beams, decking) using CadQuery
"""

import cadquery as cq
from typing import Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class UpRightBuilder:
    """
    Builds vertical support columns for warehouse racking
    
    Standard profile: 80mm width x 60mm depth rectangular hollow section
    """
    
    @staticmethod
    def build(height: float, section_size: str = "80x60") -> cq.Solid:
        """
        Create an upright column geometry
        
        Args:
            height: Total height of the column in mm
            section_size: Profile size as "WxD" format, default "80x60"
        
        Returns:
            CadQuery Solid object representing the upright
        
        Example:
            upright = UpRightBuilder.build(6000, "80x60")
        """
        try:
            # Parse section dimensions from "WxD" format
            w, d = map(float, section_size.split('x'))
            
            # Create rectangular solid: width x depth x height
            part = cq.Workplane("XY").box(w, d, height)
            
            logger.debug(f"UpRight created: {w}x{d}x{height}mm")
            return part.val()
            
        except Exception as e:
            logger.error(f"UpRightBuilder.build failed: {e}")
            raise


class BeamBuilder:
    """
    Builds horizontal beams that connect uprights
    
    Standard profile: 50mm height x 100mm length rectangular hollow section
    """
    
    @staticmethod
    def build(length: float, section_size: str = "50x100") -> cq.Solid:
        """
        Create a horizontal beam geometry
        
        Args:
            length: Length of the beam along Y-axis in mm
            section_size: Profile size as "HxW" format, default "50x100"
        
        Returns:
            CadQuery Solid object representing the beam
        
        Example:
            beam = BeamBuilder.build(1000, "50x100")
        """
        try:
            # Parse section dimensions from "HxW" format
            h, w = map(float, section_size.split('x'))
            
            # Create rectangular solid oriented along Y-axis
            # Height (h) is vertical, Width (w) is horizontal extent
            part = cq.Workplane("XY").box(w, length, h)
            
            logger.debug(f"Beam created: {h}x{w}x{length}mm")
            return part.val()
            
        except Exception as e:
            logger.error(f"BeamBuilder.build failed: {e}")
            raise


class DeckingBuilder:
    """
    Builds shelf decking panels
    
    Thin rectangular panels that sit on top of beams
    """
    
    @staticmethod
    def build(width: float, depth: float, thickness: float = 10) -> cq.Solid:
        """
        Create a decking panel geometry
        
        Args:
            width: Width of the panel in mm (along X-axis)
            depth: Depth of the panel in mm (along Y-axis)
            thickness: Thickness of the panel in mm, default 10mm
                      Valid range: 10-50mm
        
        Returns:
            CadQuery Solid object representing the decking panel
        
        Example:
            decking = DeckingBuilder.build(2400, 1000, 10)
        """
        try:
            # Validate thickness
            if not (10 <= thickness <= 50):
                logger.warning(f"Thickness {thickness}mm out of range [10-50], clamping")
                thickness = max(10, min(50, thickness))
            
            # Create rectangular panel: width x depth x thickness
            part = cq.Workplane("XY").box(width, depth, thickness)
            
            logger.debug(f"Decking created: {width}x{depth}x{thickness}mm")
            return part.val()
            
        except Exception as e:
            logger.error(f"DeckingBuilder.build failed: {e}")
            raise


def test_component_factory():
    """Quick sanity check of component builders"""
    try:
        upright = UpRightBuilder.build(6000, "80x60")
        upright_bbox = upright.BoundingBox()
        print(f"Upright OK: {upright_bbox.xlen:.1f}x{upright_bbox.ylen:.1f}x{upright_bbox.zlen:.1f}")
        
        beam = BeamBuilder.build(1000, "50x100")
        beam_bbox = beam.BoundingBox()
        print(f"Beam OK: {beam_bbox.xlen:.1f}x{beam_bbox.ylen:.1f}x{beam_bbox.zlen:.1f}")
        
        decking = DeckingBuilder.build(2400, 1000, 10)
        decking_bbox = decking.BoundingBox()
        print(f"Decking OK: {decking_bbox.xlen:.1f}x{decking_bbox.ylen:.1f}x{decking_bbox.zlen:.1f}")
        
        print("All components generated successfully")
        return True
    except Exception as e:
        print(f"Component factory test failed: {e}")
        return False


if __name__ == "__main__":
    test_component_factory()
