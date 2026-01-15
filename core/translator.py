import json
import cadquery as cq
from core.components import create_omega_column, create_box_beam, create_panel

def run_translation(instance_path):
    with open(instance_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 获取全局尺寸
    gc = data['global_constraints']
    W, H, D = gc['width'], gc['height'], gc['depth']
    assembly = cq.Assembly(name="Industrial_Rack_v2")

    # 2. 核心：遍历组件并实现“真·三维”放置
    for comp in data['components']:
        params = comp['parameters']
        c_type = comp['type']
        color = cq.Color(params.get('color', 'gray'))

        # --- 立柱：四个角点 ---
        if c_type == 'column':
            col_shape = create_omega_column(params['width'], params['depth'], params['thickness'], H)
            corners = [(0, 0), (W, 0), (0, D), (W, D)]
            for i, (px, py) in enumerate(corners):
                assembly.add(col_shape, loc=cq.Location(cq.Vector(px, py, 0)), name=f"upright_{i}", color=color)

        # --- 横梁：前后左右全包围 ---
        elif c_type == 'beam':
            layers = params.get('layers', 1)
            # 长横梁 (跨度 W)
            long_beam = create_box_beam(params['width'], params['height'], W)
            # 短横梁/侧撑 (深度 D - 这里假设你需要侧向连接)
            short_beam = create_box_beam(params['width'], params['height'], D)
            
            for i in range(layers):
                z_pos = (H / (layers + 1)) * (i + 1)
                # 添加前排与后排长梁
                assembly.add(long_beam, loc=cq.Location(cq.Vector(W/2, 0, z_pos)), color=color)
                assembly.add(long_beam, loc=cq.Location(cq.Vector(W/2, D, z_pos)), color=color)
                # 添加左侧与右侧短梁 (这就是把梯子变框架的关键)
                assembly.add(short_beam, loc=cq.Location(cq.Vector(0, D/2, z_pos), cq.Vector(0, 0, 1), 90), color=color)
                assembly.add(short_beam, loc=cq.Location(cq.Vector(W, D/2, z_pos), cq.Vector(0, 0, 1), 90), color=color)

        # --- 层板：水平面 ---
        elif c_type == 'panel':
            # 创建一个覆盖整个 W x D 的板
            panel_shape = create_panel(W, D, params['thickness'])
            # 同样根据横梁层数生成
            for i in range(4): # 假设与横梁层数一致
                z_pos = (H / (4 + 1)) * (i + 1) + (params['thickness'] / 2)
                assembly.add(panel_shape, loc=cq.Location(cq.Vector(W/2, D/2, z_pos)), color=color)

    return assembly