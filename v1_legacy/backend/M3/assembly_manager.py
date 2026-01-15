"""
M3 Phase 2: Assembly Manager (组装管理器)
功能：将单个组件组装成完整的仓库货架结构并导出为STEP格式

主要职责：
1. 解析验证后的参数配置
2. 构建单个货架单元（包含立柱、横梁、层板等组件）
3. 将所有组件组合成完整的3D模型
4. 导出为STEP格式文件
"""

import cadquery as cq
from pathlib import Path
from typing import List, Tuple, Dict, Any
# Import moved component factory from M3 package
from backend.M3.component_factory import UpRightBuilder, BeamBuilder, DeckingBuilder
from utils.logger import get_logger

logger = get_logger(__name__)


class AssemblyBuilder:
    """
    仓库货架组装构建器
    """
    
    def __init__(self, config: Dict[str, Any]):
        try:
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


    def build_single_bay(self) -> List[Tuple[str, cq.Solid]]:
        try:
            parts = []
            upright_left = UpRightBuilder.build(self.total_height, "80x60")
            upright_left = upright_left.translate((0, 0, 0))
            parts.append(("upright_left", upright_left))
            try:
                bbox = upright_left.BoundingBox()
                logger.debug(f"Left upright bbox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
            except Exception:
                logger.debug("Left upright bbox not available")
            logger.debug("Left upright positioned at (0, 0, 0)")
            
            upright_right = UpRightBuilder.build(self.total_height, "80x60")
            upright_right = upright_right.translate((0, self.bay_depth, 0))
            parts.append(("upright_right", upright_right))
            try:
                bbox = upright_right.BoundingBox()
                logger.debug(f"Right upright bbox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
            except Exception:
                logger.debug("Right upright bbox not available")
            logger.debug(f"Right upright positioned at (0, {self.bay_depth}, 0)")
            
            beam_front = BeamBuilder.build(self.bay_depth, "50x100")
            beam_front = beam_front.translate((0, 0, self.first_beam_height))
            parts.append(("beam_front", beam_front))
            try:
                bbox = beam_front.BoundingBox()
                logger.debug(f"Front beam bbox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
            except Exception:
                logger.debug("Front beam bbox not available")
            logger.debug(f"Front beam positioned at Z={self.first_beam_height}mm")
            
            beam_spacing_x = self.bay_width / 2
            beam_back = BeamBuilder.build(self.bay_depth, "50x100")
            beam_back = beam_back.translate((beam_spacing_x, 0, self.first_beam_height))
            parts.append(("beam_back", beam_back))
            try:
                bbox = beam_back.BoundingBox()
                logger.debug(f"Back beam bbox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
            except Exception:
                logger.debug("Back beam bbox not available")
            logger.debug(f"Back beam positioned at (X={beam_spacing_x}, Z={self.first_beam_height})")
            
            beam_height = 50
            decking_z = self.first_beam_height + beam_height
            
            decking = DeckingBuilder.build(self.bay_width, self.bay_depth, 10)
            decking = decking.translate((0, 0, decking_z))
            parts.append(("decking", decking))
            try:
                bbox = decking.BoundingBox()
                logger.debug(f"Decking bbox: {bbox.xlen:.1f}x{bbox.ylen:.1f}x{bbox.zlen:.1f}")
            except Exception:
                logger.debug("Decking bbox not available")
            logger.debug(f"Decking positioned at Z={decking_z}mm")
            
            logger.info(f"Single bay assembled: {len(parts)} components")
            return parts
            
        except Exception as e:
            logger.error(f"build_single_bay failed: {e}")
            raise


    def assemble_warehouse(self) -> cq.Solid:
        try:
            parts = self.build_single_bay()
            if not parts:
                raise ValueError("No parts generated")
            # parts is a list of (name, solid)
            first_part = parts[0][1]
            assembly_wp = cq.Workplane("XY").add(first_part)
            for _, part in parts[1:]:
                temp_wp = cq.Workplane("XY").add(part)
                assembly_wp = assembly_wp.union(temp_wp)
                logger.debug(f"Part unioned to assembly")
            logger.info("Warehouse assembly complete")
            return assembly_wp.val()
        except Exception as e:
            logger.error(f"assemble_warehouse failed: {e}")
            raise


    def export_step(self, output_path: str) -> bool:
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            out_dir = Path(output_path).parent

            # Build parts and export individual component STEP files
            parts = self.build_single_bay()  # list of (name, solid)
            components_dir = out_dir / "components"
            components_dir.mkdir(parents=True, exist_ok=True)

            metadata = {"components": []}

            for idx, (name, part) in enumerate(parts, start=1):
                try:
                    comp_name = f"{name}_{idx}.step"
                    comp_path = components_dir / comp_name
                    # attempt to export part
                    if hasattr(part, 'exportStep'):
                        part.exportStep(str(comp_path))
                    else:
                        part.val().exportStep(str(comp_path))
                    sz = comp_path.stat().st_size if comp_path.exists() else 0
                    metadata['components'].append({
                        'name': comp_name,
                        'path': str(comp_path),
                        'size_bytes': sz
                    })
                    logger.info(f"Exported component: {comp_path} ({sz} bytes)")
                except Exception as e:
                    logger.warning(f"Failed to export component {name}: {e}")

            # Now assemble full assembly and export
            assembly = self.assemble_warehouse()

            # write a marker file before attempting export so UI can confirm geometry creation
            try:
                from datetime import datetime
                marker_path = out_dir / "cadquery_called.txt"
                with open(marker_path, "w", encoding="utf-8") as mf:
                    mf.write(f"cadquery_invoked: {datetime.now().isoformat()}\n")
                    mf.write(f"assembly_type: {type(assembly)}\n")
                    mf.write(f"has_exportStep: {hasattr(assembly, 'exportStep')}\n")
            except Exception as e:
                logger.warning(f"Failed to write cadquery marker file: {e}")

            # attempt to capture assembly bounding box
            try:
                try:
                    bb = assembly.BoundingBox()
                except Exception:
                    bb = assembly.val().BoundingBox() if hasattr(assembly, 'val') else None
                if bb is not None:
                    import json as _json
                    info = {"xlen": float(bb.xlen), "ylen": float(bb.ylen), "zlen": float(bb.zlen)}
                    info_path = out_dir / "assembly_info.json"
                    with open(info_path, "w", encoding="utf-8") as jf:
                        _json.dump(info, jf, indent=2)
                    logger.info(f"Assembly bbox written to: {info_path}")
            except Exception as e:
                logger.debug(f"Could not determine assembly bounding box: {e}")

            # export assembly STEP
            if hasattr(assembly, 'exportStep'):
                assembly.exportStep(output_path)
            else:
                assembly = cq.Workplane("XY").add(assembly).val()
                assembly.exportStep(output_path)

            # write metadata.json
            try:
                import json as _json
                meta_path = out_dir / 'metadata.json'
                meta = {
                    'assembly': str(output_path),
                    'components_dir': str(components_dir),
                    **metadata
                }
                with open(meta_path, 'w', encoding='utf-8') as mf:
                    _json.dump(meta, mf, indent=2)
                logger.info(f"Wrote metadata: {meta_path}")
            except Exception as e:
                logger.warning(f"Failed to write metadata.json: {e}")

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
    try:
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
        output_path = "output/test_assembly.step"
        success = builder.export_step(output_path)
        print(f"STEP export: {'OK' if success else 'FAILED'}")
        return success
    except Exception as e:
        print(f"Assembly builder test failed: {e}")
        return False


if __name__ == "__main__":
    test_assembly_builder()
