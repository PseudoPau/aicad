import io
from pathlib import Path
import streamlit as st
from datetime import datetime

from utils.file_manager import ensure_dir
from utils.logger import get_logger
import json
from parameter_extractor import extract_from_image_description
from parameter_validator import ParameterValidator
from assembly_manager import AssemblyBuilder

# 新的 ImageAnalyzer（支持智谱/硅基流动/Ollama/Hugging Face）
try:
    from temp import ImageAnalyzer
except Exception:
    ImageAnalyzer = None

# 保留 ai_analyzer 作为备选（仅 Hugging Face）
try:
    from ai_analyzer import ImageCaptioner
except Exception:
    ImageCaptioner = None

validator = ParameterValidator()

# ============================================================================
# M3 CAD Generation Function
# ============================================================================

def get_hardcoded_defaults():
    """Return hardcoded warehouse defaults if parameter extraction failed"""
    return {
        "warehouse_config": {
            "name": "Default Warehouse",
            "location": "Unknown"
        },
        "racking_system": {
            "dimensions": {
                "bay_width": 2400,
                "bay_depth": 1000,
                "total_height": 6000
            },
            "structure": {
                "levels": 3,
                "first_beam_height": 200,
                "beam_spacing": 1800
            }
        }
    }


def generate_warehouse_step(validated_params, output_dir: str) -> tuple:
    """
    High-level interface to generate STEP file from warehouse parameters
    
    Args:
        validated_params: Validated parameter dict from M2
        output_dir: Base output directory
    
    Returns:
        Tuple: (success: bool, step_path: str or empty string)
    """
    try:
        # Validate input
        if not validated_params:
            logger.warning("No validated params, using hardcoded defaults")
            validated_params = get_hardcoded_defaults()
        
        # Ensure output directory structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_subdir = Path(output_dir) / "analysis" / timestamp
        ensure_dir(str(output_subdir))
        
        # Create assembly and export
        builder = AssemblyBuilder(validated_params)
        step_path = str(output_subdir / "warehouse_assembly.step")
        
        success = builder.export_step(step_path)
        
        if success:
            logger.info(f"CAD generation successful: {step_path}")
            return (True, step_path)
        else:
            logger.error("STEP export failed")
            return (False, "")
            
    except Exception as e:
        logger.error(f"generate_warehouse_step failed: {e}")
        return (False, "")

# ============================================================================
# Cached loader for huggingface captioner (keeps model in memory across reruns)
if ImageCaptioner is not None:
    @st.cache_resource
    def load_captioner():
        return ImageCaptioner()
else:
    def load_captioner():
        return None

logger = get_logger("app")

st.set_page_config(page_title="AI Warehouse Builder", layout="wide")

with st.sidebar:
    st.header("Settings")
    analyzer_method = st.selectbox(
        "Image analyzer method",
        ["zhipu", "siliconflow", "ollama", "qwen", "huggingface"],
        index=0,
        help="推荐优先级: 智谱GLM-4V > 硅基流动Qwen2-VL > Ollama > Hugging Face"
    )
    output_dir = st.text_input("Output directory", value="output")
    
    # API Key input based on method
    if analyzer_method == "zhipu":
        api_key = st.text_input(
            "智谱 AI API Key",
            type="password",
            help="访问 https://open.bigmodel.cn/ 获取免费 API Key"
        )
    elif analyzer_method == "siliconflow":
        api_key = st.text_input(
            "硅基流动 API Key",
            type="password",
            help="访问 https://siliconflow.cn/ 获取 API Key"
        )
    else:
        api_key = st.text_input("OpenAI / API Key (optional)", type="password")
    
    st.markdown("---")
    st.markdown("**支持方案:**")
    st.markdown("- 🌟 **智谱 AI GLM-4V**: 识别能力强，有免费额度")
    st.markdown("- 🌟 **硅基流动 Qwen2-VL**: 开源模型，价格低，计数好")
    st.markdown("- 💻 **Ollama**: 本地运行（需下载模型）")
    st.markdown("- 📚 **Hugging Face BLIP**: 基础功能，不需API Key")

st.title("🏭 AI Industrial Warehouse Builder")

uploaded_file = st.file_uploader("Upload Warehouse Photo", type=["jpg", "png", "jpeg"])

if uploaded_file is None:
    st.info("Upload a JPG/PNG image to analyze the warehouse photo.")
else:
    # Preview image
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

    # Ensure output directory exists
    out_base = Path(output_dir)
    ensure_dir(out_base)
    uploads_dir = out_base / "uploads"
    ensure_dir(uploads_dir)

    # Save uploaded file to disk
    file_bytes = uploaded_file.read()
    save_path = uploads_dir / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    st.success(f"Saved uploaded file to: {save_path}")

    # Analyze button
    if st.button("Analyze Image"):
        # 根据选择的方法创建分析器
        prompt = "请详细描述这个货架/仓库，包括层数、尺寸、部件和组装方式。"

        with st.spinner("Analyzing image, please wait..."):
            result = None
            
            # 优先级：zhipu > siliconflow > ollama > qwen > huggingface
            if analyzer_method in ["zhipu", "siliconflow", "ollama", "qwen"]:
                if ImageAnalyzer is None:
                    st.error("ImageAnalyzer module not available. Make sure `temp.py` exists.")
                else:
                    try:
                        analyzer = ImageAnalyzer(method=analyzer_method, api_key=api_key)
                        result = analyzer.analyze(str(save_path), prompt=prompt)
                        if "错误:" in result or "Error" in result:
                            st.error(result)
                            result = None
                        else:
                            st.success(f"✅ Analysis completed with {analyzer_method}")
                    except Exception as e:
                        logger.error(f"Analysis failed ({analyzer_method}): {e}")
                        st.error(f"Analysis failed: {e}")
            
            elif analyzer_method == "huggingface":
                if ImageCaptioner is None:
                    st.error("Hugging Face captioner not available. Ensure 'transformers' and 'torch' are installed.")
                else:
                    try:
                        captioner = load_captioner()
                        if captioner is None:
                            st.error("Failed to initialize Hugging Face captioner.")
                        else:
                            device_info = getattr(captioner, "device", None)
                            if device_info:
                                st.caption(f"Model device: {device_info}")
                            result = captioner.generate(str(save_path), prompt=prompt)
                            st.success("✅ Analysis completed with Hugging Face BLIP")
                    except Exception as e:
                        logger.error(f"HuggingFace analysis failed: {e}")
                        st.error(f"HuggingFace analysis failed: {e}")

            if result is not None:
                st.subheader("Step 1: Image Description")
                st.text_area("Description (from AI)", value=result, height=200, disabled=True)
                
                # Step 2: Extract parameters
                st.subheader("Step 2: Parameter Extraction")
                try:
                    extracted_params = extract_from_image_description(result)
                    st.success("Parameters extracted (using rule-based extractor)")
                    
                    # Show extracted JSON
                    st.json(extracted_params)
                    
                    # Step 3: Validate parameters
                    st.subheader("Step 3: Parameter Validation")
                    validated_params, validation_errors = validator.validate_and_complete(extracted_params)
                    
                    if validation_errors:
                        st.warning(f"⚠️ {len(validation_errors)} validation message(s):")
                        for error in validation_errors:
                            st.write(f"  - {error}")
                    else:
                        st.success("✅ All parameters valid!")
                    
                    # Show validated JSON
                    st.json(validated_params)
                    
                    # ================================================================
                    # Step 4: Build CAD Model (M3)
                    # ================================================================
                    st.subheader("Step 4: Build CAD Model")
                    
                    col_build, col_info = st.columns([2, 1])
                    
                    with col_build:
                        if st.button("Generate 3D Model (STEP)", use_container_width=True):
                            with st.spinner("Generating 3D CAD model..."):
                                success, step_file = generate_warehouse_step(validated_params, output_dir)
                                
                                if success and step_file:
                                    st.success("✅ 3D Model Generated Successfully!")
                                    
                                    # Display file info
                                    step_path_obj = Path(step_file)
                                    file_size_kb = step_path_obj.stat().st_size / 1024
                                    st.info(f"STEP file: {step_path_obj.name} ({file_size_kb:.1f} KB)")
                                    
                                    # Download button
                                    with open(step_file, "rb") as f:
                                        st.download_button(
                                            label="Download warehouse.step",
                                            data=f.read(),
                                            file_name="warehouse_assembly.step",
                                            mime="application/step"
                                        )
                                else:
                                    st.warning("Failed to generate STEP file. Please check parameters and try again.")
                    
                    with col_info:
                        st.markdown("""
                        **Model Info:**
                        - Format: STEP (.step)
                        - 3D CAD compatible
                        - Can be opened in FreeCAD, Fusion 360, etc.
                        """)
                    
                    # ================================================================
                    # Save results to file
                    # ================================================================
                    results_dir = out_base / "analysis"
                    ensure_dir(results_dir)
                    
                    desc_path = results_dir / (save_path.stem + "_description.txt")
                    with open(desc_path, "w", encoding="utf-8") as f:
                        f.write(result)
                    
                    params_path = results_dir / (save_path.stem + "_parameters.json")
                    with open(params_path, "w", encoding="utf-8") as f:
                        json.dump(validated_params, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Saved description to: {desc_path}")
                    st.success(f"✅ Saved parameters to: {params_path}")
                    
                    # Offer downloads
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(label="Download image", data=io.BytesIO(file_bytes), file_name=uploaded_file.name, mime=uploaded_file.type)
                    with col2:
                        with open(desc_path, "rb") as f:
                            st.download_button(label="Download description", data=f.read(), file_name=desc_path.name, mime="text/plain")
                    with col3:
                        with open(params_path, "rb") as f:
                            st.download_button(label="Download parameters", data=f.read(), file_name=params_path.name, mime="application/json")
                    
                except Exception as e:
                    logger.error(f"Parameter extraction/validation failed: {e}")
                    st.error(f"Parameter processing failed: {e}")

    # Show small metadata summary
    st.markdown("---")
    st.subheader("File Info")
    st.write({
        "filename": uploaded_file.name,
        "type": uploaded_file.type,
        "size_bytes": len(file_bytes)
    })

    logger.info(f"Uploaded file: {uploaded_file.name}, saved to {save_path}")