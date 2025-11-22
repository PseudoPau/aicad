import io
from pathlib import Path
import streamlit as st
from datetime import datetime
import sys

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from utils.file_manager import ensure_dir
from utils.logger import get_logger
import json
from parameter_extractor import extract_from_image_description
from backend.M2.parameter_validator import ParameterValidator
from backend.M3.assembly_manager import AssemblyBuilder

# 新的 ImageAnalyzer（支持智谱/硅基流动/Ollama/Hugging Face）
try:
    from backend.M2.temp import ImageAnalyzer, default_analysis_prompt
except Exception:
    ImageAnalyzer = None
    default_analysis_prompt = None

# 保留 ai_analyzer 作为备选（仅 Hugging Face）
try:
    from backend.M2.ai_analyzer import ImageCaptioner
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
        Tuple: (success: bool, step_path: str or empty string, error_msg: str)
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

        # Write generation log for diagnostics
        try:
            gen_log = output_subdir / "generation.log"
            with open(gen_log, "w", encoding="utf-8") as gl:
                if success:
                    gl.write(f"SUCCESS: STEP exported to {step_path}\n")
                    logger.info(f"CAD generation successful: {step_path}")
                else:
                    gl.write(f"FAIL: STEP export failed for path {step_path}\n")
                    logger.error("STEP export failed")
        except Exception as e:
            logger.warning(f"Failed to write generation.log: {e}")

        if success:
            return (True, step_path, "")
        else:
            error_msg = "STEP export failed"
            return (False, "", error_msg)
            
    except Exception as e:
        import traceback as _tb
        tb = _tb.format_exc()
        error_msg = f"CAD generation error: {str(e)}"
        logger.error(error_msg)
        # attempt to write error to generation.log
        try:
            output_subdir = Path(output_dir) / "analysis" / datetime.now().strftime("%Y%m%d_%H%M%S")
            ensure_dir(str(output_subdir))
            gen_log = output_subdir / "generation.log"
            with open(gen_log, "w", encoding="utf-8") as gl:
                gl.write(error_msg + "\n")
                gl.write(tb)
        except Exception:
            pass
        return (False, "", error_msg)

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
    st.image(uploaded_file, caption="Uploaded Image", width='stretch')

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
        # 使用后端提供的默认精细提示词以保证前后端一致
        if default_analysis_prompt is not None:
            prompt = default_analysis_prompt()
        else:
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
                        # Check if validated_params is available
                        if 'validated_params' not in locals():
                            st.error("❌ No validated parameters available. Please complete Step 3 first.")
                        else:
                            if st.button("Generate 3D Model (STEP)", width='stretch'):
                                # Immediately write a UI invocation marker so we can detect the button press
                                try:
                                    from datetime import datetime
                                    ui_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    ui_dir = out_base / "analysis"
                                    ensure_dir(ui_dir)
                                    ui_marker = ui_dir / f"ui_invoke_{ui_ts}.txt"
                                    with open(ui_marker, "w", encoding="utf-8") as um:
                                        um.write(f"button_pressed: {ui_ts}\n")
                                        um.write(f"output_dir: {output_dir}\n")
                                        um.write(f"validated_params_present: {bool(validated_params)}\n")
                                except Exception as e:
                                    logger.warning(f"Failed to write UI invoke marker: {e}")

                                with st.spinner("Generating 3D CAD model..."):
                                    success, step_file, error_msg = generate_warehouse_step(validated_params, output_dir)
                                    
                                    if success and step_file:
                                        st.success("✅ 3D Model Generated Successfully!")
                                        
                                        # Display file info
                                        step_path_obj = Path(step_file)
                                        if step_path_obj.exists():
                                            file_size_kb = step_path_obj.stat().st_size / 1024
                                            st.info(f"STEP file: {step_path_obj.name} ({file_size_kb:.1f} KB)")
                                        else:
                                            st.warning("STEP reported as generated but file not found at the reported path.")
                                            step_path_obj = None

                                        # Show CadQuery marker files if present
                                        marker_path = step_path_obj.parent / "cadquery_called.txt"
                                        info_path = step_path_obj.parent / "assembly_info.json"
                                        with st.expander("CAD generation details", expanded=False):
                                            if marker_path.exists():
                                                try:
                                                    with open(marker_path, "r", encoding="utf-8") as mf:
                                                        st.text_area("cadquery_called.txt", value=mf.read(), height=120)
                                                except Exception as e:
                                                    st.error(f"Failed to read marker file: {e}")
                                            else:
                                                st.warning("Marker file `cadquery_called.txt` not found.")

                                            if info_path.exists():
                                                try:
                                                    import json as _json
                                                    with open(info_path, "r", encoding="utf-8") as jf:
                                                        data = _json.load(jf)
                                                    st.json(data)
                                                except Exception as e:
                                                    st.error(f"Failed to read assembly info: {e}")
                                            else:
                                                st.info("No `assembly_info.json` found.")

                                                # Show generation.log if present (contains success/failure and traceback)
                                                gen_log_path = step_path_obj.parent / "generation.log"
                                                if gen_log_path.exists():
                                                    try:
                                                        with open(gen_log_path, "r", encoding="utf-8") as gl:
                                                            st.text_area("generation.log", value=gl.read(), height=220)
                                                    except Exception as e:
                                                        st.error(f"Failed to read generation.log: {e}")
                                                else:
                                                    st.info("No `generation.log` found in output directory.")

                                        # Download button
                                        # Offer download: prefer the reported file, fallback to latest .step in output/analysis
                                        downloaded = False
                                        if step_path_obj is not None and step_path_obj.exists():
                                            try:
                                                with open(step_path_obj, "rb") as f:
                                                    st.download_button(
                                                        label="Download warehouse.step",
                                                        data=f.read(),
                                                        file_name=step_path_obj.name,
                                                        mime="application/step"
                                                    )
                                                downloaded = True
                                            except Exception as e:
                                                st.error(f"Failed to open STEP file for download: {e}")

                                        if not downloaded:
                                            # search for latest .step under out_base/analysis
                                            try:
                                                analysis_dir = out_base / "analysis"
                                                if analysis_dir.exists():
                                                    dirs = [d for d in analysis_dir.iterdir() if d.is_dir()]
                                                    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                                    found_step = None
                                                    for d in dirs:
                                                        candidates = list(d.glob("*.step"))
                                                        if candidates:
                                                            # prefer a file named warehouse_assembly.step
                                                            pref = next((c for c in candidates if c.name == "warehouse_assembly.step"), None)
                                                            found_step = pref or candidates[0]
                                                            break
                                                    if found_step is not None:
                                                        try:
                                                            with open(found_step, "rb") as f:
                                                                st.info(f"Found STEP in: {found_step}")
                                                                st.download_button(
                                                                    label="Download latest STEP",
                                                                    data=f.read(),
                                                                    file_name=found_step.name,
                                                                    mime="application/step"
                                                                )
                                                            downloaded = True
                                                        except Exception as e:
                                                            st.error(f"Failed to read fallback STEP file: {e}")
                                                    else:
                                                        st.warning("No STEP file found in output/analysis to download.")
                                                else:
                                                    st.warning("No analysis output directory found for fallback STEP search.")
                                            except Exception as e:
                                                st.error(f"Error while searching for fallback STEP: {e}")
                                    else:
                                        if error_msg:
                                            st.error(f"Failed to generate STEP: {error_msg}")
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