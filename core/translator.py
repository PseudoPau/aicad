import json
import math
import cadquery as cq
from pathlib import Path

# 导入组件库
from .components import (
    create_omega_column, create_box_beam, 
    create_bracing, create_base_plate, create_panel
)

def run_translation(instance_path):
    """
    支持双排、Z型斜撑与层板系统的工业级翻译引擎
    """
    with open(instance_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 提取全局参数
    gc = data['global_constraints']
    W, H, D = gc['width'], gc['height'], gc['depth']
    bay_count = gc.get('bay_count', 1)
    is_double = gc.get('is_double_row', False)
    spacer = gc.get('spacer_length', 200.0)
    
    # 2. 提取组件参数
    comp_map = {c['type']: c['parameters'] for c in data['components']}
    col_p, beam_p = comp_map.get('column'), comp_map.get('beam')
    brac_p, panel_p = comp_map.get('bracing'), comp_map.get('panel', {"thickness": 20})

    assembly = cq.Assembly(name="Advanced_Racking_System")

    # 预生成静态构件
    col_shape = create_omega_column(col_p['width'], col_p['depth'], col_p['thickness'], H)
    beam_shape = create_box_beam(beam_p['width'], beam_p['height'], W - col_p['width'])
    base_plate = create_base_plate(col_p['width'], col_p['depth'])
    panel_shape = create_panel(W - col_p['width'], D - 10, panel_p.get('thickness', 20))

    # --- 辅助逻辑：计算 Y 轴位置 ---
    # 第一排位置: [0, D]
    # 第二排位置: [D + spacer, 2D + spacer]
    rows_y = [[0, D]]
    if is_double:
        rows_y.append([D + spacer, 2*D + spacer])

    # ---------------------------------------------------------
    # 3. 构造循环
    # ---------------------------------------------------------
    for r_idx, y_coords in enumerate(rows_y):
        for i in range(bay_count + 1):
            x_offset = i * W
            
            # A. 放置立柱与底板
            for y in y_coords:
                assembly.add(base_plate, loc=cq.Location(cq.Vector(x_offset, y, 0)), name=f"base_{r_idx}_{i}_{y}")
                assembly.add(col_shape, loc=cq.Location(cq.Vector(x_offset, y, 0)), name=f"col_{r_idx}_{i}_{y}", color=cq.Color("blue"))

            # B. 放置 Z 型连续斜撑 (仅在排头排尾)
            if i == 0 or i == bay_count:
                segs = 4
                seg_h = H / segs
                brac_len = math.sqrt(D**2 + seg_h**2)
                angle = math.degrees(math.atan(seg_h / D))
                single_brac = create_bracing(brac_len, brac_p['width'], brac_p['thickness'])
                
                y_center = (y_coords[0] + y_coords[1]) / 2
                for s in range(segs):
                    z_mid = s * seg_h + seg_h / 2
                    # Z型逻辑：每层反转角度
                    cur_angle = angle if s % 2 == 0 else -angle
                    assembly.add(
                        single_brac,
                        loc=cq.Location(cq.Vector(x_offset, y_center, z_mid), cq.Vector(1, 0, 0), cur_angle),
                        name=f"brac_{r_idx}_{i}_{s}", color=cq.Color("silver")
                    )

        # C. 放置横梁与层板
        layer_dist = H / (beam_p['layers'] + 1)
        for b in range(bay_count):
            x_center = b * W + W/2
            for layer in range(1, beam_p['layers'] + 1):
                z_pos = layer * layer_dist
                # 前后横梁
                assembly.add(beam_shape, loc=cq.Location(cq.Vector(x_center, y_coords[0], z_pos)), name=f"bm_f_{r_idx}_{b}_{layer}", color=cq.Color("orange"))
                assembly.add(beam_shape, loc=cq.Location(cq.Vector(x_center, y_coords[1], z_pos)), name=f"bm_r_{r_idx}_{b}_{layer}", color=cq.Color("orange"))
                # 补全层板
                assembly.add(panel_shape, loc=cq.Location(cq.Vector(x_center, (y_coords[0]+y_coords[1])/2, z_pos)), name=f"pnl_{r_idx}_{b}_{layer}", color=cq.Color("white"))

    # 4. 双排背拉杆 (Spacer Bars)
    if is_double:
        spacer_bar = cq.Workplane("XY").box(50, spacer, 20) # 简易连接杆
        for i in range(bay_count + 1):
            x_off = i * W
            for s in range(1, 3): # 垂直方向放两个连接杆
                z_off = s * (H / 3)
                assembly.add(spacer_bar, loc=cq.Location(cq.Vector(x_off, D + spacer/2, z_off)), name=f"spacer_{i}_{s}", color=cq.Color("gray"))

    return assembly