import cadquery as cq

class WarehouseBuilder:
    def __init__(self):
        self.assembly = cq.Assembly()
        # 预定义颜色表
        self.colors = {
            "blue": cq.Color(0.1, 0.1, 0.8, 1),
            "orange": cq.Color(1, 0.5, 0, 1),
            "gray": cq.Color(0.8, 0.8, 0.8, 1)
        }

    def _create_upright(self, height, color_name="blue"):
        # 80x60mm 截面立柱
        profile = (
            cq.Workplane("XY")
            .rect(80, 60)
            .rect(70, 50)
            .extrude(height)
        )
        return profile

    def _create_beam(self, length, color_name="orange"):
        # 50x100mm 截面横梁
        profile = (
            cq.Workplane("YZ")
            .rect(50, 100)
            .extrude(length)
        )
        return profile

    def _create_decking(self, width, depth):
        # 20mm 厚层板
        panel = (
            cq.Workplane("XY")
            .box(width, depth, 20)
        )
        return panel

    def build_from_json(self, config_json):
        # 解析 JSON，循环装配
        try:
            layout = config_json["warehouse_config"]["overall_layout"]
            rack = config_json["racking_system"]
            dims = rack["dimensions"]
            struct = rack["structure"]
            comp = rack["components"]

            rows = layout.get("rows", 1)
            row_spacing = layout.get("row_spacing", 2000.0)
            bay_width = dims.get("bay_width", 2200.0)
            bay_depth = dims.get("bay_depth", 1000.0)
            total_height = dims.get("total_height", 4500.0)
            levels = struct.get("levels", 3)
            first_beam_height = struct.get("first_beam_height", 300.0)
            upright_color = comp.get("upright_color", "blue")
            beam_color = comp.get("beam_color", "orange")
            has_decking = comp.get("has_decking", True)

            # 只做单排多组货架示例
            for row in range(rows):
                x_offset = row * row_spacing
                # 两根立柱
                upright1 = self._create_upright(total_height, upright_color)
                upright2 = self._create_upright(total_height, upright_color)
                self.assembly.add(upright1, name=f"upright_L_{row}", loc=cq.Location(cq.Vector(x_offset, 0, 0)), color=self.colors[upright_color])
                self.assembly.add(upright2, name=f"upright_R_{row}", loc=cq.Location(cq.Vector(x_offset, bay_width, 0)), color=self.colors[upright_color])
                # 横梁和层板
                for level in range(levels):
                    z = first_beam_height + level * ((total_height - first_beam_height) / levels)
                    beam = self._create_beam(bay_width, beam_color)
                    self.assembly.add(beam, name=f"beam_{row}_{level}", loc=cq.Location(cq.Vector(x_offset, 0, z)), color=self.colors[beam_color])
                    if has_decking:
                        deck = self._create_decking(bay_width, bay_depth)
                        self.assembly.add(deck, name=f"deck_{row}_{level}", loc=cq.Location(cq.Vector(x_offset, bay_width/2, z+10)), color=self.colors["gray"])
        except Exception as e:
            raise ValueError(f"Invalid config_json: {e}")

    def export(self, filename="warehouse_output.step"):
        # 导出 STEP 文件
        self.assembly.save(filename)

# 独立测试
if __name__ == "__main__":
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