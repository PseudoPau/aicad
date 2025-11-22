import cadquery as cq
import json

class WarehouseBuilder:
    def __init__(self):
        self.assembly = cq.Assembly()
        # 预定义颜色表 (用于 Web 端展示区分部件)
        self.colors = {
            "blue": cq.Color(0.1, 0.1, 0.8, 1),
            "orange": cq.Color(1, 0.5, 0, 1),
            "gray": cq.Color(0.8, 0.8, 0.8, 1)
        }

    def _create_upright(self, height, color_name="blue"):
        """
        生成立柱组件：简单的矩形挤压，模拟 L 型钢或方管
        """
        # 80x60mm 截面
        profile = (
            cq.Workplane("XY")
            .rect(80, 60)
            .rect(70, 50) # 挖空内部，做成管状或槽钢感
            .extrude(height)
        )
        return profile, self.colors.get(color_name, self.colors["blue"])

    def _create_beam(self, length, color_name="orange"):
        """
        生成横梁组件：P型梁截面
        """
        # 50x100mm 截面
        profile = (
            cq.Workplane("YZ") # 注意在 YZ 平面画，方便后续拉伸
            .rect(50, 100)
            .extrude(length)   # 默认沿 X 轴拉伸
        )
        return profile, self.colors.get(color_name, self.colors["orange"])

    def _create_decking(self, width, depth):
        """
        生成层板：简单的平板
        """
        panel = (
            cq.Workplane("XY")
            .box(width, depth, 20) # 20mm 厚度
        )
        return panel, self.colors["gray"]

    def build_from_json(self, config_json):
        """
        【核心逻辑】解析 JSON -> 循环装配
        """
        # 1. 安全解析 JSON 参数 (带默认值防崩)
        wh_conf = config_json.get("warehouse_config", {})
        rack_conf = config_json.get("racking_system", {})
        dim_conf = rack_conf.get("dimensions", {})
        struct_conf = rack_conf.get("structure", {})
        comp_conf = rack_conf.get("components", {})

        # 布局参数
        rows = wh_conf.get("overall_layout", {}).get("rows", 1)
        row_spacing = wh_conf.get("overall_layout", {}).get("row_spacing", 1500)
        
        # 尺寸参数
        bay_width = dim_conf.get("bay_width", 2500)
        bay_depth = dim_conf.get("bay_depth", 1000)
        total_height = dim_conf.get("total_height", 5000)
        
        # 结构参数
        levels = struct_conf.get("levels", 3)
        first_h = struct_conf.get("first_beam_height", 200)
        
        # 2. 重置装配体
        self.assembly = cq.Assembly()
        
        # --- 开始组装循环 ---
        # 循环：排 (Rows)
        for r in range(rows):
            y_offset = r * (bay_depth + row_spacing)
            
            # 放置左立柱
            upright_geo, upright_col = self._create_upright(total_height, comp_conf.get("upright_color", "blue"))
            self.assembly.add(
                upright_geo, 
                loc=cq.Location(cq.Vector(0, y_offset, 0)),
                name=f"Row{r}_Upright_L", 
                color=upright_col
            )
            
            # 放置右立柱
            self.assembly.add(
                upright_geo, 
                loc=cq.Location(cq.Vector(bay_width, y_offset, 0)),
                name=f"Row{r}_Upright_R", 
                color=upright_col
            )

            # 循环：层 (Levels)
            beam_step = (total_height - first_h) / levels
            
            for L in range(levels):
                z_height = first_h + (L * beam_step)
                
                # 生成并放置横梁
                beam_geo, beam_col = self._create_beam(bay_width, comp_conf.get("beam_color", "orange"))
                
                # 前横梁
                self.assembly.add(
                    beam_geo,
                    loc=cq.Location(cq.Vector(0, y_offset, z_height)),
                    name=f"Row{r}_Lvl{L}_Beam_F",
                    color=beam_col
                )
                
                # 后横梁
                self.assembly.add(
                    beam_geo,
                    loc=cq.Location(cq.Vector(0, y_offset + bay_depth, z_height)),
                    name=f"Row{r}_Lvl{L}_Beam_B",
                    color=beam_col
                )
                
                # 可选：放置层板
                if comp_conf.get("has_decking", False):
                    deck_geo, deck_col = self._create_decking(bay_width, bay_depth)
                    self.assembly.add(
                        deck_geo,
                        loc=cq.Location(cq.Vector(bay_width/2, y_offset + bay_depth/2, z_height + 50)),
                        name=f"Row{r}_Lvl{L}_Deck",
                        color=deck_col
                    )

        return self.assembly

    def export(self, filename="warehouse_output.step"):
        """导出为 STEP 格式"""
        self.assembly.save(filename, exportType="STEP")
        print(f"✅ Model exported to {filename}")

# ==========================================
# 本地测试块 (Self-Test)
# 直接运行此文件即可测试，无需 Web UI
# ==========================================
if __name__ == "__main__":
    # 模拟 AI 可能生成的 JSON
    mock_json = {
      "warehouse_config": {
        "overall_layout": { "rows": 2, "row_spacing": 1200.0 }
      },
      "racking_system": {
        "dimensions": { "bay_width": 2200.0, "bay_depth": 1000.0, "total_height": 4500.0 },
        "structure": { "levels": 3, "first_beam_height": 300.0 },
        "components": { "upright_color": "blue", "beam_color": "orange", "has_decking": True }
      }
    }

    print("🔧 Testing WarehouseBuilder...")
    builder = WarehouseBuilder()
    builder.build_from_json(mock_json)
    builder.export("test_warehouse.step")
    print("🚀 Test Complete! Check test_warehouse.step in your folder.")