import cadquery as cq
from ocp_vscode import show  # 确保你已经执行了 pip install ocp-vscode

def generate_parametric_table(params):
    """
    根据参数字典生成桌子模型
    这种逻辑结构方便后续与 Multi-agent 系统对接
    """
    # 提取参数
    L = params.get("length", 1200.0)
    W = params.get("width", 700.0)
    H = params.get("height", 750.0)
    t = params.get("thickness", 30.0)
    leg_s = params.get("leg_size", 50.0)
    inset = params.get("inset", 20.0)

    # 1. 创建桌面 (Table Top)
    # 使用中心对齐，方便后续定位
    table_top = cq.Workplane("XY").box(L, W, t)

    # 2. 创建桌腿 (Table Legs)
    leg_h = H - t
    leg = cq.Workplane("XY").box(leg_s, leg_s, leg_h)

    # 3. 组装模型 (Assembly)
    # 这部分对应编排思路图中的 Agent 3 逻辑
    model = cq.Assembly(name="Parametric_Table")

    # 添加桌面：将其移动到总高度 H 减去板厚一半的位置
    model.add(
        table_top, 
        name="top", 
        loc=cq.Location(cq.Vector(0, 0, H - t/2)),
        color=cq.Color("burlywood")
    )

    # 计算四根桌腿的中心坐标偏移量
    x_off = L/2 - inset - leg_s/2
    y_off = W/2 - inset - leg_s/2
    z_pos = leg_h / 2

    # 四角坐标位置
    corners = [
        (x_off, y_off), (-x_off, y_off),
        (x_off, -y_off), (-x_off, -y_off)
    ]

    # 循环添加桌腿
    for i, (cx, cy) in enumerate(corners):
        model.add(
            leg,
            name=f"leg_{i+1}",
            loc=cq.Location(cq.Vector(cx, cy, z_pos)),
            color=cq.Color("saddlebrown")
        )

    return model

# --- 执行区 ---
if __name__ == "__main__":
    # 这里模拟了从 Agent 1/2 传来的结构化数据
    table_config = {
        "length": 1500.0,
        "width": 800.0,
        "height": 750.0,
        "thickness": 35.0,
        "leg_size": 60.0,
        "inset": 30.0
    }

    # 调用生成函数
    table_assembly = generate_parametric_table(table_config)

    # 在 OCP CAD Viewer 中显示
    # 请确保在 VS Code 中已经通过 Ctrl+Shift+P 开启了 OCP: Open Viewer
    print("正在生成 3D 模型预览...")
    show(table_assembly)