import cadquery as cq

def create_omega_column(w, d, t, h):
    half_w, half_d = w / 2, d / 2
    pts = [
        (-half_w, -half_d), (half_w, -half_d), 
        (half_w, half_d), (half_w*0.6, half_d), 
        (half_w*0.6, -half_d + t), (-half_w*0.6, -half_d + t), 
        (-half_w*0.6, half_d), (-half_w, half_d)
    ]
    return cq.Workplane("XY").polyline(pts).close().extrude(h)

def create_box_beam(w, h, length):
    return cq.Workplane("XY").box(length, w, h)

# --- 修正：将斜撑改为 Z 轴向上生成，这是 CadQuery 最稳定的旋转基准 ---
def create_bracing(length, width=30, thickness=2.0):
    return cq.Workplane("XY").rect(width, thickness).extrude(length).translate((0, 0, -length/2))

def create_base_plate(col_w, col_d):
    return cq.Workplane("XY").rect(col_w + 40, col_d + 40).extrude(5.0)

def create_panel(length, width, thickness=20.0):
    return cq.Workplane("XY").box(length, width, thickness).edges("|Z").fillet(2.0)

def create_spacer_bar(length):
    # 保持沿 Y 轴生成
    return cq.Workplane("XY").box(40, length, 20)