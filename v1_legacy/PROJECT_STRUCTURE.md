## Project Structure

### 目录说明

```
aicad/
├── frontend/                    # 前端界面 (Streamlit)
│   ├── app.py                  # 主应用入口
│   └── __init__.py
│
├── backend/                     # 后端逻辑
│   ├── component_factory.py     # M3 Phase 1: 部件生成器
│   ├── assembly_manager.py      # M3 Phase 2: 装配与STEP导出
│   ├── parameter_extractor.py   # M2: 参数提取
│   ├── parameter_validator.py   # M2: 参数验证
│   ├── ai_analyzer.py          # M2: Hugging Face图像分析
│   ├── temp.py                 # M2: 多后端AI分析(智谱/硅基/Ollama)
│   ├── utils/                  # 工具函数
│   │   ├── file_manager.py     # 文件操作
│   │   └── logger.py           # 日志管理
│   ├── tests/                  # 单元测试
│   │   ├── test_parameter_validator.py
│   │   ├── test_cad_generation.py
│   │   ├── test_app.py
│   │   └── test_cad_generation.py  (M3测试)
│   └── __init__.py
│
├── output/                      # 输出文件
│   ├── analysis/               # 分析结果
│   └── uploads/                # 上传的图片
│
├── docs/                        # 文档
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION.md
│   ├── PRD.md
│   └── task.md
│
├── scripts/                     # 辅助脚本
│   └── check_deps.py
│
├── run_app.py                   # 应用启动器
├── requirements.txt             # 依赖列表
├── README.md                    # 项目说明
└── QUICKSTART.md               # 快速开始指南
```

### 运行应用

**方式1: 使用启动脚本 (推荐)**
```bash
python run_app.py
```

**方式2: 直接运行streamlit**
```bash
streamlit run frontend/app.py
```

### 运行测试

**所有测试**
```bash
pytest backend/tests/ -v
```

**特定测试**
```bash
pytest backend/tests/test_cad_generation.py -v
pytest backend/tests/test_parameter_validator.py -v
```

### 项目阶段

- **M0**: 技术栈选择 ✅
- **M1**: Streamlit UI框架 ✅
- **M2**: AI分析 & 参数提取/验证 ✅
- **M3**: CAD模型生成 ✅ (13/13 tests passing)
- **M4**: (规划中)

### 关键模块说明

#### 前端 (frontend/)
- `app.py`: Streamlit应用，提供4步工作流
  - Step 1: 图像分析 (多后端支持)
  - Step 2: 参数提取
  - Step 3: 参数验证
  - Step 4: CAD模型生成 & STEP导出

#### 后端 (backend/)
- **M2模块**: 图像→参数
  - `temp.py`: 智谱/硅基流动/Ollama等多后端接口
  - `ai_analyzer.py`: Hugging Face BLIP模型
  - `parameter_extractor.py`: 从描述提取参数JSON
  - `parameter_validator.py`: 验证和补全参数

- **M3模块**: 参数→CAD
  - `component_factory.py`: 生成基础部件 (竖柱/梁/铺板)
  - `assembly_manager.py`: 组装部件并导出STEP

- **工具**: 
  - `utils/logger.py`: 结构化日志
  - `utils/file_manager.py`: 文件和目录管理

### 依赖项

查看 `requirements.txt`:
- streamlit: 前端框架
- cadquery: CAD模型生成
- torch, transformers: AI模型 (可选)
- pytest: 单元测试

### M3 CAD生成测试结果

```
======================= 13 passed, 2 warnings in 1.27s ========================

✅ TestComponentFactory (4 tests)
   - test_upright_geometry
   - test_beam_geometry  
   - test_decking_geometry
   - test_decking_thickness_clamping

✅ TestAssemblyBuilder (4 tests)
   - test_assembly_builder_init
   - test_single_bay_assembly
   - test_assembly_bbox
   - test_missing_config_fields

✅ TestStepExport (4 tests)
   - test_step_export_creates_file
   - test_step_export_file_size
   - test_step_export_creates_subdirs
   - test_step_export_invalid_path

✅ TestIntegration (1 test)
   - test_full_pipeline
```

### 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **运行应用**
   ```bash
   python run_app.py
   ```

3. **上传仓库图片** → 自动分析 → 生成3D CAD → 下载STEP文件

4. **在CAD软件中打开** (FreeCAD, Fusion 360等)
