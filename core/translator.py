import json
import math
import cadquery as cq
from .components import *

def run_translation(instance_path):
    with open(instance_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 参数提取
    gc = data['global_constraints']
    W, H, D = gc['width'], gc['height'], gc['depth']
    bay_count, is_double = gc.get('bay_count', 1), gc.get('is_double_row', False)
    spacer = gc.get('spacer_length', 200.0)
    
    comp_map = {c['type']: c['parameters'] for c in data['components']}
    col_p, beam_p, brac_p = comp_map['column'], comp_map['beam'], comp_map['bracing']
    panel_thick = 20.0 # 预设层板厚度

    assembly = cq.Assembly(name="Tectonic_Racking_System")

    # 2. 预生成构件（居中化设计，方便偏置计算）
    col_shape = create_omega_column(col_p['width'], col_p['depth'], col_p['thickness'], H)
    beam_shape = create_box_beam(beam_p['width'], beam_p['height'], W - col_p['width'])
    base_plate = create_base_plate(col_p['width'], col_p['depth'])
    
    # 层板长度留出 10mm 安全间隙，避免碰撞立柱
    panel_shape = create_panel(W - col_p['width'] - 10, D, panel_thick)
    horiz_brac = create_horizontal_bar(D, brac_p['width'], brac_p['thickness'])

    # 3. 计算垂直分配逻辑 (解决扫地高度问题)
    # 参考原图：第一层扫地高约 300mm，顶部留白约 400mm
    bottom_offset = 300.0
    top_clearance = 400.0
    layers = beam_p['layers']
    z_gap = (H - bottom_offset - top_clearance) / (layers - 1) if layers > 1 else 0

    # 定义 Y 轴排布序列
    rows_y = [[0, D]]
    if is_double: 
        rows_y.append([D + spacer, 2*D + spacer])

    # ---------------------------------------------------------
    # 4. 几何装配循环
    # ---------------------------------------------------------
    for r_idx, y_coords in enumerate(rows_y):
        y_mid = (y_coords[0] + y_coords[1]) / 2
        
        for i in range(bay_count + 1):
            x_off = i * W
            
            # A. 立柱与底板
            for y in y_coords:
                assembly.add(base_plate, loc=cq.Location(cq.Vector(x_off, y, 0)), name=f"base_{r_idx}_{i}_{y}")
                assembly.add(col_shape, loc=cq.Location(cq.Vector(x_off, y, 0)), name=f"col_{r_idx}_{i}_{y}", color=cq.Color("blue"))

            # B. 动态斜撑 (基于 H 模数自动分段) [cite: 2026-01-20]
            if i == 0 or i == bay_count:
                target_spacing = 650.0 # 目标间距
                segs = math.ceil((H - 100) / target_spacing)
                seg_h = (H - 100) / segs
                
                brac_len = math.sqrt(D**2 + seg_h**2)
                angle_deg = math.degrees(math.atan(seg_h / D))
                single_brac = create_bracing(brac_len, brac_p['width'], brac_p['thickness'])
                
                for s in range(segs):
                    z_mid = 50 + s * seg_h + seg_h / 2
                    base_angle = 90 - angle_deg
                    total_angle = base_angle if s % 2 == 0 else -base_angle
                    assembly.add(
                        single_brac,
                        loc=cq.Location(cq.Vector(x_off, y_mid, z_mid), cq.Vector(1, 0, 0), total_angle),
                        name=f"zbrac_{r_idx}_{i}_{s}", color=cq.Color("gray")
                    )

        # C. 横梁与层板 (核心对位逻辑修正)
        for b in range(bay_count):
            x_c = b * W + W/2
            for l in range(layers):
                z_beam = bottom_offset + (l * z_gap)
                
                # 前后横梁：挂载在立柱对应的 Y 坐标上
                assembly.add(beam_shape, loc=cq.Location(cq.Vector(x_c, y_coords[0], z_beam)), name=f"bmf_{r_idx}_{b}_{l}", color=cq.Color("orange"))
                assembly.add(beam_shape, loc=cq.Location(cq.Vector(x_c, y_coords[1], z_beam)), name=f"bmr_{r_idx}_{b}_{l}", color=cq.Color("orange"))
                
                # --- 层板对位：解决穿模问题 ---
                # z_panel = 横梁中心高度 + 横梁半高 + 层板半厚 [cite: 2026-01-28]
                z_panel = z_beam + (beam_p['height'] / 2) + (panel_thick / 2)
                
                assembly.add(
                    panel_shape, 
                    loc=cq.Location(cq.Vector(x_c, y_mid, z_panel)), 
                    name=f"pnl_{r_idx}_{b}_{l}", 
                    color=cq.Color("white")
                )

    return assembly