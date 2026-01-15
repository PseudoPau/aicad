import cadquery as cq

def create_omega_column(w, d, t, h):
    """
    生成工业货架专用的 Omega 型截面立柱
    """
    # 简化版 Omega 截面路径
    pts = [
        (0, 0), (w, 0), (w, d), (w*0.8, d), 
        (w*0.8, t), (w*0.2, t), (w*0.2, d), (0, d)
    ]
    return cq.Workplane("XY").polyline(pts).close().extrude(h)

def create_box_beam(w, h, length):
    """
    生成矩形横梁
    """
    return cq.Workplane("XY").box(length, w, h)

def create_panel(w, d, t):
    """
    生成层板
    """
    return cq.Workplane("XY").box(w, d, t)

if __name__ == "__main__":
    # 测试生成一个 Omega 立柱
    column = create_omega_column(w=90, d=70, t=2, h=1000)
    # 导出到本地查看
    from cadquery import exporters
    exporters.export(column, "test_column.step")
    print("✅ components.py: Omega立柱生成并导出成功。")