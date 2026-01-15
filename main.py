import os
import json
from pathlib import Path
from dotenv import load_dotenv
from cadquery import exporters

from core.vision_agent import VisionAgent
from core.validator import validate_cad_data
from core.translator import run_translation

load_dotenv()

# --- 路径配置 (严格区分输入与输出) ---
BASE_DIR = Path(__file__).resolve().parent

# 输入区 (只读)
SCHEMA_PATH = BASE_DIR / "schema" / "assembly_schema.json"
FEW_SHOT_PATH = BASE_DIR / "tests" / "shelf_instance.json"  # 仅作为 AI 参考模板
INPUT_IMAGE = BASE_DIR / "tests" / "rack_photo.jpg"

# 输出区 (存储识别结果与模型)
OUTPUT_DIR = BASE_DIR.parent / "output"
RESULT_JSON_PATH = OUTPUT_DIR / "extracted_instance.json"    # AI 识别后的新文件
OUTPUT_STEP_FILE = str(OUTPUT_DIR / "assembly_result.step")

def run_ai_cad_pipeline():
    print("🚀 启动 AI CAD 全链路系统 (逻辑修正版)...")
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 资源准备
    api_key = os.getenv("ZHIPU_API_KEY")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_text = f.read()
    with open(FEW_SHOT_PATH, 'r', encoding='utf-8') as f:
        few_shot_text = f.read()

    # 2. 阶段 1: AI 视觉参数提取 (存入新路径)
    print(f"📸 正在识别图片并参考模板: {FEW_SHOT_PATH.name}")
    agent = VisionAgent(api_key)
    try:
        extracted_data = agent.extract_params(str(INPUT_IMAGE), schema_text, few_shot_text)
        
        # 核心改动：写入 output 文件夹，不覆盖原始 tests 文件
        with open(RESULT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        print(f"✅ AI 识别数据已生成: {RESULT_JSON_PATH}")
    except Exception as e:
        print(f"💥 AI 识别环节失败: {e}")
        return

    # 3. 阶段 2: 验证 AI 生成的新 JSON
    print(f"🛡️ 正在验证新生成的 JSON 文件...")
    if not validate_cad_data(str(RESULT_JSON_PATH), str(SCHEMA_PATH)):
        print("❌ AI 提取的数据不符合规范，无法建模。")
        return

    # 4. 阶段 3: 基于新 JSON 生成模型
    print("🛠️ 正在翻译为 3D 几何体...")
    try:
        assembly = run_translation(str(RESULT_JSON_PATH))
        exporters.export(assembly.toCompound(), OUTPUT_STEP_FILE)
        
        print("-" * 50)
        print(f"🎉 流程全部跑通！")
        print(f"📂 识别数据: {RESULT_JSON_PATH}")
        print(f"📦 3D 模型: {OUTPUT_STEP_FILE}")
        print("-" * 50)
    except Exception as e:
        print(f"💥 几何建模环节失败: {e}")

if __name__ == "__main__":
    run_ai_cad_pipeline()