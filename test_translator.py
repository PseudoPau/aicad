import sys
from pathlib import Path
from cadquery import exporters

# 确保能导入 core 文件夹下的模块
sys.path.append(str(Path(__file__).parent))

from core.translator import run_translation

def test_single_json():
    # 1. 配置路径 (指向你已经生成的 JSON)
    BASE_DIR = Path(__file__).resolve().parent
    JSON_PATH = BASE_DIR.parent / "output" / "extracted_instance.json"
    OUTPUT_STEP = BASE_DIR.parent / "output" / "test_result.step"

    print(f"🛠️ 正在从缓存读取数据: {JSON_PATH}")
    
    if not JSON_PATH.exists():
        print(f"❌ 错误: 未找到 {JSON_PATH}。请确认文件已生成。")
        return

    # 2. 调用翻译引擎
    try:
        print("🏗️ 正在生成几何模型 (双排 + Z型斜撑)...")
        assembly = run_translation(str(JSON_PATH))
        
        # 3. 导出模型
        exporters.export(assembly.toCompound(), str(OUTPUT_STEP))
        print(f"✅ 测试成功！模型已保存至: {OUTPUT_STEP}")
        
    except Exception as e:
        print(f"💥 建模测试失败: {e}")

if __name__ == "__main__":
    test_single_json()