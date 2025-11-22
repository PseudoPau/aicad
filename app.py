import streamlit as st
import json
import os
import base64
from dotenv import load_dotenv
from warehouse_builder import WarehouseBuilder

# 1. 加载环境变量
load_dotenv()

st.set_page_config(page_title="AI Warehouse Generator", page_icon="🏭", layout="wide")

# ==========================================
# 辅助函数：图片转 Base64 (给 AI 看)
# ==========================================
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# ==========================================
# 核心函数：呼叫 AI (The Brain)
# ==========================================
def get_ai_parameters(api_key, base64_image, user_prompt):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # 系统提示词：强制 AI 输出 Sprint 1 定义的 JSON 协议
    system_prompt = """
    You are an Industrial AI Expert. Analyze the user's warehouse image.
    Output ONLY a valid JSON object matching this exact schema (no markdown, no comments):
    {
      "warehouse_config": {
        "overall_layout": { "rows": "int (count of racks)", "row_spacing": "float (mm)" }
      },
      "racking_system": {
        "dimensions": { "bay_width": "float", "bay_depth": "float", "total_height": "float" },
        "structure": { "levels": "int", "first_beam_height": "float" },
        "components": { "upright_color": "string (blue/orange/gray)", "beam_color": "string", "has_decking": "bool" }
      }
    }
    Estimate dimensions based on standard industrial pallets (1.2m x 1.0m) if not specified.
    """

    response = client.chat.completions.create(
        model="gpt-4o", # 必须支持视觉的模型
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        response_format={ "type": "json_object" }, # 强制 JSON 模式
        temperature=0.1 # 降低随机性
    )
    return json.loads(response.choices[0].message.content)

# ==========================================
# UI 界面 (The Face)
# ==========================================
st.title("🏭 AI Industrial Warehouse Builder")
st.markdown("**Hackathon MVP Mode**: Upload Image -> Extract Logic -> Generate CAD")

# Sidebar: 配置区
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    use_demo_mode = st.checkbox("🔧 Demo Mode (No API Cost)", value=False, help="Use hardcoded JSON for testing UI flow")

# Main: 操作区
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Input")
    uploaded_file = st.file_uploader("Upload Warehouse Photo", type=["jpg", "png", "jpeg"])
    prompt = st.text_area("Additional Requirements", "Analyze this warehouse structure and rebuild it.", height=100)
    
    generate_btn = st.button("🚀 Generate Digital Twin", type="primary")

if generate_btn:
    if not uploaded_file:
        st.error("Please upload an image first!")
    else:
        with st.spinner("🤖 AI is analyzing structure (Vision Processing)..."):
            try:
                # A. 获取参数 (AI vs Demo)
                if use_demo_mode:
                    import time
                    time.sleep(1) # 模拟 AI 思考
                    # 模拟数据
                    config_data = {
                        "warehouse_config": { "overall_layout": { "rows": 2, "row_spacing": 2000.0 } },
                        "racking_system": {
                            "dimensions": { "bay_width": 2500.0, "bay_depth": 1000.0, "total_height": 6000.0 },
                            "structure": { "levels": 4, "first_beam_height": 200.0 },
                            "components": { "upright_color": "blue", "beam_color": "orange", "has_decking": True }
                        }
                    }
                    st.success("Simulation Data Loaded (Demo Mode)")
                else:
                    if not api_key_input:
                        st.error("API Key missing! Use Demo Mode or enter Key.")
                        st.stop()
                    
                    # 真实 AI 调用
                    base64_img = encode_image(uploaded_file)
                    config_data = get_ai_parameters(api_key_input, base64_img, prompt)
                    st.success("✅ AI Analysis Complete")

                # B. 展示提取的参数 (Human-in-the-loop)
                with col2:
                    st.subheader("2. AI Extracted Logic")
                    st.json(config_data, expanded=False)

                # C. 调用几何引擎 (The Engine)
                with st.spinner("⚙️ Parametric Engine Building CAD..."):
                    builder = WarehouseBuilder()
                    builder.build_from_json(config_data)
                    
                    output_file = "ai_generated_warehouse.step"
                    builder.export(output_file)

                # D. 交付结果
                with col2:
                    st.subheader("3. Result")
                    st.success("🎉 CAD Model Generated!")
                    
                    # 读取文件生成下载链接
                    with open(output_file, "rb") as f:
                        st.download_button(
                            label="📥 Download .STEP File (Manufacturing Ready)",
                            data=f,
                            file_name=output_file,
                            mime="application/octet-stream"
                        )
                    
                    st.info("💡 Tip: Open this file in FreeCAD, SolidWorks, or standard CAD viewer.")

            except Exception as e:
                st.error(f"🔥 Critical Error: {str(e)}")