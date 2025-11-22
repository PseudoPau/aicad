import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import os
from dotenv import load_dotenv
from backend.ai_api import get_ai_parameters
from backend.utils import encode_image
from backend.warehouse_builder import WarehouseBuilder
from backend.warehouse_config import validate_config

st.set_page_config(page_title="AI Warehouse Generator", page_icon="🏭", layout="wide")
load_dotenv()
st.set_page_config(page_title="AI Warehouse Generator", page_icon="🏭", layout="wide")
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
                    time.sleep(1)
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
                    base64_img = encode_image(uploaded_file)
                    config_data = get_ai_parameters(api_key_input, base64_img, prompt)
                    st.success("✅ AI Analysis Complete")

                # 校验参数
                validate_config(config_data)

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