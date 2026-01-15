"""
M3 Phase 2: Assembly Manager
Assembles individual components into complete warehouse structures and exports to STEP

功能模块:
- AssemblyBuilder: 主类，负责装配和导出
  - __init__: 从配置参数初始化装配器
  - build_single_bay: 生成单个货架单元 (5个部件)
  - assemble_warehouse: 将部件并集成一个完整的3D模型
  - export_step: 导出为STEP CAD文件

工作流程:
1. AssemblyBuilder(config) 初始化 - 读取货架尺寸和结构参数
2. build_single_bay() 生成部件 - 创建竖柱、梁、铺板
3. assemble_warehouse() 装配 - 使用union操作合并所有部件
4. export_step(path) 导出 - 保存为STEP文件供CAD软件打开

坐标系说明:
- X轴: 货架宽度方向 (0 → bay_width)
- Y轴: 货架深度方向 (0 → bay_depth)
- Z轴: 货架高度方向 (0 → total_height)
"""

import cadquery as cq
from pathlib import Path
from typing import List, Tuple, Dict, Any
from backend.M3.component_factory import UpRightBuilder, BeamBuilder, DeckingBuilder
from utils.logger import get_logger

logger = get_logger(__name__)


class AssemblyBuilder:
    """
    Assembles warehouse racking components and manages STEP export
    
    Takes validated parameter config and builds complete 3D model
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize assembly builder with warehouse parameters
        
        Args:
            config: Validated parameter dictionary from M2 output
                   Must contain: racking_system.dimensions and structure
        
        Raises:
            ValueError: If required config fields are missing
        """
        try:
            # Extract key dimensions from config
            dimensions = config.get("racking_system", {}).get("dimensions", {})
            structure = config.get("racking_system", {}).get("structure", {})
            
            self.bay_width = dimensions.get("bay_width", 2400)
            self.bay_depth = dimensions.get("bay_depth", 1000)
            self.total_height = dimensions.get("total_height", 6000)
            
            self.levels = structure.get("levels", 3)
            self.first_beam_height = structure.get("first_beam_height", 200)
            self.beam_spacing = structure.get("beam_spacing", 1800)
            
            logger.info(f"AssemblyBuilder initialized: {self.bay_width}x{self.bay_depth}x{self.total_height}mm")
            
        except Exception as e:
            logger.error(f"AssemblyBuilder init failed: {e}")
            raise ValueError(f"Invalid config structure: {e}")
    
    
    def build_single_bay(self) -> List[cq.Solid]:
        """
        Build a single warehouse bay (MVP: single level only)
        
        Structure:
        - 2 uprights (left and right)
        - 2 beams (connecting uprights)
        - 1 decking panel (on top of beams)
        
        Returns:
            List of 5 CadQuery Solid objects
            Order: [upright_left, upright_right, beam_front, beam_back, decking]
        
        Coordinate system:
        - X-axis: width (0 to bay_width)
        - Y-axis: depth (0 to bay_depth)  
        - Z-axis: height (0 to total_height)
        """
        try:
            parts = []
            
            # 1. Create left upright at origin (0, 0, 0)
            upright_left = UpRightBuilder.build(self.total_height, "80x60")
            upright_left = upright_left.translate((0, 0, 0))
            parts.append(upright_left)
            logger.debug("Left upright positioned at (0, 0, 0)")
            
            # 2. Create right upright at (bay_depth, 0, 0)
            # Note: positioned along Y-axis to span the bay depth
            upright_right = UpRightBuilder.build(self.total_height, "80x60")
            upright_right = upright_right.translate((0, self.bay_depth, 0))
            parts.append(upright_right)
            logger.debug(f"Right upright positioned at (0, {self.bay_depth}, 0)")
            
            # 3. Create front beam at first_beam_height
            # Beams run along Y-axis (depth direction)
            beam_front = BeamBuilder.build(self.bay_depth, "50x100")
            beam_front = beam_front.translate((0, 0, self.first_beam_height))
            parts.append(beam_front)
            logger.debug(f"Front beam positioned at Z={self.first_beam_height}mm")
            
            # 4. Create back beam at first_beam_height (offset along X)
            # For MVP, create second beam at same height but different X position
            # This assumes beams are spaced along the width direction
            beam_spacing_x = self.bay_width / 2  # Simplified: put at mid-width
            beam_back = BeamBuilder.build(self.bay_depth, "50x100")
            beam_back = beam_back.translate((beam_spacing_x, 0, self.first_beam_height))
            parts.append(beam_back)
            logger.debug(f"Back beam positioned at (X={beam_spacing_x}, Z={self.first_beam_height})")
            
            # 5. Create decking panel on top of beams
            # Panel dimensions match bay width x depth
            # Positioned at Z = first_beam_height + beam_height
            beam_height = 50  # Standard beam profile height
            decking_z = self.first_beam_height + beam_height
            
            decking = DeckingBuilder.build(self.bay_width, self.bay_depth, 10)
            decking = decking.translate((0, 0, decking_z))
            parts.append(decking)
            logger.debug(f"Decking positioned at Z={decking_z}mm")
            
            logger.info(f"Single bay assembled: {len(parts)} components")
            return parts
            
        except Exception as e:
            logger.error(f"build_single_bay failed: {e}")
            raise
    
    
    def assemble_warehouse(self) -> cq.Solid:
        """
        Combine all bay components into a single warehouse compound geometry
        
        Returns:
            Single CadQuery Solid representing complete assembly
        """
        try:
            parts = self.build_single_bay()
            
            if not parts:
                raise ValueError("No parts generated")
            
            # Convert all solids to Workplane objects for union operation
            # Start with first part as a Workplane
            assembly_wp = cq.Workplane("XY").add(parts[0])
            
            # Union remaining parts one by one
            for part in parts[1:]:
                # Union: convert solid to workplane, then combine
                temp_wp = cq.Workplane("XY").add(part)
                assembly_wp = assembly_wp.union(temp_wp)
                logger.debug(f"Part unioned to assembly")
            
            logger.info("Warehouse assembly complete")
            # Return the underlying solid from the workplane
            return assembly_wp.val()
            
        except Exception as e:
            logger.error(f"assemble_warehouse failed: {e}")
            raise
    
    
    def export_step(self, output_path: str) -> bool:
        """
        Export assembled warehouse to STEP format
        
        Args:
            output_path: Full path to output STEP file
        
        Returns:
            True if export successful and file exists with size > 1KB, False otherwise
        """
        try:
            # Ensure parent directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Generate assembly
            assembly = self.assemble_warehouse()
            
            # Export to STEP format
            # assembly is a Solid/Compound, directly call exportStep
            if hasattr(assembly, 'exportStep'):
                assembly.exportStep(output_path)
            else:
                # If it's wrapped in Workplane, extract the shape
                assembly = cq.Workplane("XY").add(assembly).val()
                assembly.exportStep(output_path)
            
            # Verify export
            output_file = Path(output_path)
            if not output_file.exists():
                logger.error(f"STEP file not created: {output_path}")
                return False
            
            file_size = output_file.stat().st_size
            
            if file_size < 1024:
                logger.warning(f"STEP file too small ({file_size} bytes): {output_path}")
                return False
            
            logger.info(f"STEP exported successfully: {output_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"export_step failed: {e}")
            return False


def test_assembly_builder():
    """Quick sanity check of assembly builder"""
    try:
        # Create minimal config
        config = {
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
        
        builder = AssemblyBuilder(config)
        parts = builder.build_single_bay()
        print(f"Single bay: {len(parts)} components generated")
        
        assembly = builder.assemble_warehouse()
        bbox = assembly.BoundingBox()
        print(f"Assembly dimensions: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}mm")
        
        # Test export to temp location
        output_path = "output/test_assembly.step"
        success = builder.export_step(output_path)
        print(f"STEP export: {'OK' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"Assembly builder test failed: {e}")
        return False


if __name__ == "__main__":
    test_assembly_builder()
