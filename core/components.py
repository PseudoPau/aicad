import cadquery as cq

def create_omega_column(w, d, t, h):
    """
    生成工业级 Omega 型截面立柱 (居中版)
    w, d: 截面外包尺寸, t: 壁厚, h: 总高
    """
    half_w, half_d = w / 2, d / 2
    # 构造 Omega 卷边路径，确保中心位于 (0,0)
    pts = [
        (-half_w, -half_d), (half_w, -half_d), 
        (half_w, half_d), (half_w*0.6, half_d), 
        (half_w*0.6, -half_d + t), (-half_w*0.6, -half_d + t), 
        (-half_w*0.6, half_d), (-half_w, half_d)
    ]
    return cq.Workplane("XY").polyline(pts).close().extrude(h)

def create_box_beam(w, h, length):
    """
    生成矩形横梁
    """
    return cq.Workplane("XY").box(length, w, h)

def create_bracing(length, width=30, thickness=2.0):
    """
    生成斜撑型材 (核心改动：改为 Y 轴向生成)
    这样在 translator 中旋转角度 theta = atan(H/D) 时，旋转逻辑更直观
    """
    # 在 XZ 平面绘图并沿 Y 轴拉伸，确保中心对齐
    return (cq.Workplane("XZ")
            .rect(width, thickness)
            .extrude(length)
            .translate((0, -length/2, 0)))

def create_base_plate(col_w, col_d):
    """
    生成立柱底脚板
    """
    plate_w, plate_d = col_w + 40, col_d + 40
    return cq.Workplane("XY").rect(plate_w, plate_d).extrude(5.0)

def create_panel(length, width, thickness=20.0):
    """
    生成货架层板 (新增)
    用于铺设在横梁之间，实现货架的承载功能
    """
    # 增加微小的倒角以提升视觉写实感
    return cq.Workplane("XY").box(length, width, thickness).edges("|Z").fillet(2.0)

def create_spacer_bar(length):
    """
    生成双排货架连接杆 (新增)
    用于连接背靠背的两组立柱，增加系统整体刚度
    """
    return cq.Workplane("XY").box(50, length, 20)

def create_guard_rail(w, d, h=150.0):
    """
    生成橙色防撞导轨 (新增)
    对应照片中底部的安全构造，提升 LOD 350 精度
    """
    # 采用简单的矩形框架模拟
    outer = cq.Workplane("XY").rect(w + 100, d + 100).extrude(h)
    inner = cq.Workplane("XY").rect(w + 60, d + 60).extrude(h)
    return outer.cut(inner)

if __name__ == "__main__":
    # 单元测试
    panel = create_panel(2300, 1000)
    print("✅ components.py: 构件库已更新，包含层板与连接件。")