import json
import math
import cadquery as cq
from pathlib import Path
from .components import *

def run_translation(instance_path):
    with open(instance_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    gc = data['global_constraints']
    W, H, D = gc['width'], gc['height'], gc['depth']
    bay_count, is_double = gc.get('bay_count', 1), gc.get('is_double_row', False)
    spacer = gc.get('spacer_length', 200.0)
    
    comp_map = {c['type']: c['parameters'] for c in data['components']}
    col_p, beam_p, brac_p = comp_map['column'], comp_map['beam'], comp_map['bracing']

    assembly = cq.Assembly(name="Corrected_Racking_System")

    # 预生成构件
    col_shape = create_omega_column(col_p['width'], col_p['depth'], col_p['thickness'], H)
    beam_shape = create_box_beam(beam_p['width'], beam_p['height'], W - col_p['width'])
    base_plate = create_base_plate(col_p['width'], col_p['depth'])
    panel_shape = create_panel(W - col_p['width'], D - 10, 20.0)

    rows_y = [[0, D]]
    if is_double: rows_y.append([D + spacer, 2*D + spacer])

    for r_idx, y_coords in enumerate(rows_y):
        for i in range(bay_count + 1):
            x_off = i * W
            for y in y_coords:
                assembly.add(base_plate, loc=cq.Location(cq.Vector(x_off, y, 0)), name=f"base_{r_idx}_{i}_{y}")
                assembly.add(col_shape, loc=cq.Location(cq.Vector(x_off, y, 0)), name=f"col_{r_idx}_{i}_{y}", color=cq.Color("blue"))

            # --- 修正后的 Z 型斜撑放置逻辑 ---
            if i == 0 or i == bay_count:
                segs = 4
                seg_h = H / segs
                brac_len = math.sqrt(D**2 + seg_h**2)
                # 计算旋转角度
                angle_rad = math.atan(seg_h / D)
                angle_deg = math.degrees(angle_rad)
                
                # 创建斜撑（此时是垂直的）
                single_brac = create_bracing(brac_len, brac_p['width'], brac_p['thickness'])
                y_mid = (y_coords[0] + y_coords[1]) / 2
                
                for s in range(segs):
                    z_mid = s * seg_h + seg_h / 2
                    # 关键修复：先绕 X 轴旋转 90 度放平到 Y 轴，再叠加上斜率角度
                    # 确保它只在 YZ 平面运动
                    total_angle = 90 + (angle_deg if s % 2 == 0 else -angle_deg)
                    
                    assembly.add(
                        single_brac,
                        loc=cq.Location(cq.Vector(x_off, y_mid, z_mid), cq.Vector(1, 0, 0), total_angle),
                        name=f"brac_{r_idx}_{i}_{s}", color=cq.Color("gray")
                    )

        # 放置横梁与层板
        for b in range(bay_count):
            x_c = b * W + W/2
            for l in range(1, beam_p['layers'] + 1):
                z = l * (H / (beam_p['layers'] + 1))
                assembly.add(beam_shape, loc=cq.Location(cq.Vector(x_c, y_coords[0], z)), name=f"bmf_{r_idx}_{b}_{l}", color=cq.Color("orange"))
                assembly.add(beam_shape, loc=cq.Location(cq.Vector(x_c, y_coords[1], z)), name=f"bmr_{r_idx}_{b}_{l}", color=cq.Color("orange"))
                assembly.add(panel_shape, loc=cq.Location(cq.Vector(x_c, (y_coords[0]+y_coords[1])/2, z)), name=f"pnl_{r_idx}_{b}_{l}", color=cq.Color("white"))

    if is_double:
        spacer_bar = create_spacer_bar(spacer)
        for i in range(bay_count + 1):
            for s in range(1, 3):
                assembly.add(spacer_bar, loc=cq.Location(cq.Vector(i*W, D + spacer/2, s*H/3)), name=f"sp_{i}_{s}", color=cq.Color("gray"))

    return assembly