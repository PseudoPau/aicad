# PRD: AI CAD 立体仓库建模系统

## 1. 产品概述

### 1.1 产品定位
基于多模态AI输入的参数化立体仓库CAD建模工具，支持从参考图片自动提取结构参数并生成可编辑的3D模型。

### 1.2 核心价值
- **自动化建模**: 图片输入 → AI分析 → 参数提取 → 参数验证 → CAD生成（<30s）
- **参数化设计**: 尺寸、数量可联动调整，支持批量变体生成
- **模块化装配**: 部件独立存储，支持复用与替换
- **工业标准**: 输出STEP格式，兼容FreeCAD/SolidWorks/CATIA
- **灵活推理**: 支持多种AI后端（智谱 GLM-4V、硅基流动 Qwen2-VL、本地 Ollama、Hugging Face BLIP）

## 2. 功能需求

### 2.1 核心功能清单

| 功能ID | 功能名称 | 优先级 | 验收标准 |
|--------|---------|--------|----------|
| F001 | 多模态图片输入 | P0 | 支持JPG/PNG，最大10MB，解析率≥1920x1080 |
| F002 | AI视觉分析 | P0 | 智谱 GLM-4V / 硅基流动 Qwen2-VL / Ollama / Hugging Face BLIP，响应时间<15s，中文描述输出 |
| F003 | 参数提取与验证 | P0 | 从AI描述提取准确率≥80%，规则引擎验证，缺失参数自动补全 |
| F004 | 部件独立建模 | P0 | 每个部件生成独立STEP文件，命名规范：`{component_type}_{id}.step` |
| F005 | 装配体生成 | P0 | 引用部件文件组装，支持位置/旋转/约束关系 |
| F006 | 参数联动调整 | P1 | 修改bay_width时，beam长度自动更新，响应时间<2s |
| F007 | 搭接细节识别 | P1 | AI识别搭接方式（焊接/螺栓/卡扣），准确率≥80% |
| F008 | Web界面操作 | P1 | Streamlit UI，操作步骤≤3步，支持实时预览 |
| F009 | API接口调用 | P1 | RESTful API，支持JSON输入，响应时间<30s |
| F010 | 批量参数变体 | P2 | 支持CSV批量输入，生成N个变体模型 |

### 2.2 非功能需求

| 需求类型 | 指标 | 目标值 |
|---------|------|--------|
| 性能 | 单次生成耗时 | <30s（含AI调用） |
| 性能 | 模型文件大小 | <50MB（单仓库） |
| 可靠性 | AI调用失败率 | <5%（含重试机制） |
| 兼容性 | CAD软件兼容 | STEP AP203/AP214标准 |
| 可维护性 | 代码覆盖率 | ≥70% |

## 3. 用户故事

### 3.1 主要用户角色
- **工业设计师**: 需要快速从现场照片生成CAD模型
- **AI Agent**: 通过API调用自动生成仓库模型

### 3.2 用户故事

**US-001**: 作为工业设计师，我希望上传仓库照片后自动生成CAD模型，以便快速进行数字化设计。

**验收条件**:
- 上传JPG/PNG图片
- 系统在30s内生成STEP文件
- 模型尺寸与图片比例一致（误差<5%）

**US-002**: 作为AI Agent，我希望通过API传入图片URL和参数，获取模型文件下载链接。

**验收条件**:
- POST `/api/v1/generate` 接口
- 返回JSON包含`model_url`字段
- 支持异步任务，返回`task_id`

## 4. 数据模型

### 4.1 输入数据结构

```json
{
  "input_type": "image_url | base64 | file_path",
  "image_data": "string",
  "user_prompt": "string (optional, max 500 chars)",
  "override_params": {
    "bay_width": "float (mm, optional)",
    "bay_depth": "float (mm, optional)",
    "levels": "int (optional)"
  }
}
```

### 4.2 AI输出数据结构（标准协议）

```json
{
  "warehouse_config": {
    "overall_layout": {
      "rows": "int (1-20)",
      "row_spacing": "float (mm, 1000-5000)",
      "orientation": "string (north-south | east-west)"
    }
  },
  "racking_system": {
    "dimensions": {
      "bay_width": "float (mm, 1000-4000)",
      "bay_depth": "float (mm, 800-2000)",
      "total_height": "float (mm, 2000-10000)"
    },
    "structure": {
      "levels": "int (2-10)",
      "first_beam_height": "float (mm, 100-500)",
      "beam_spacing": "float (mm, 400-2000)"
    },
    "components": {
      "upright": {
        "type": "string (L-beam | C-channel | square-tube)",
        "section_size": "string (80x60 | 100x100)",
        "color": "string (blue | orange | gray | custom_hex)",
        "material": "string (steel | aluminum)"
      },
      "beam": {
        "type": "string (P-beam | box-beam)",
        "section_size": "string (50x100 | 60x120)",
        "color": "string",
        "connection_type": "string (welded | bolted | clip-on)"
      },
      "decking": {
        "has_decking": "bool",
        "type": "string (wire-mesh | solid-sheet | bar-grating)",
        "thickness": "float (mm, 10-50)"
      }
    },
    "connection_details": {
      "beam_to_upright": {
        "method": "string (welded | bolted | clip)",
        "bolt_count": "int (0-8)",
        "weld_length": "float (mm, 0-200)"
      },
      "decking_to_beam": {
        "method": "string (clip | weld | rest)",
        "clip_spacing": "float (mm, 200-600)"
      }
    }
  }
}
```

### 4.3 输出文件结构

```
output/
├── {timestamp}_{warehouse_id}/
│   ├── components/
│   │   ├── upright_001.step
│   │   ├── upright_002.step
│   │   ├── beam_001.step
│   │   ├── beam_002.step
│   │   └── decking_001.step
│   ├── assembly/
│   │   └── warehouse_assembly.step
│   ├── metadata.json
│   └── preview.png
```

## 5. 界面需求

### 5.1 Web界面布局

```
┌─────────────────────────────────────────────────┐
│  Header: AI Warehouse Builder                   │
├──────────────┬──────────────────────────────────┤
│  Sidebar     │  Main Content Area               │
│  - API Key   │  ┌────────────────────────────┐  │
│  - Settings  │  │ Step 1: Upload Image       │  │
│              │  │ [File Uploader]            │  │
│              │  └────────────────────────────┘  │
│              │  ┌────────────────────────────┐  │
│              │  │ Step 2: AI Analysis        │  │
│              │  │ [JSON Viewer]              │  │
│              │  └────────────────────────────┘  │
│              │  ┌────────────────────────────┐  │
│              │  │ Step 3: Parameter Adjust   │  │
│              │  │ [Sliders/Inputs]           │  │
│              │  └────────────────────────────┘  │
│              │  ┌────────────────────────────┐  │
│              │  │ Step 4: Download Model     │  │
│              │  │ [Download Button]          │  │
│              │  └────────────────────────────┘  │
└──────────────┴──────────────────────────────────┘
```

### 5.2 交互流程

1. 用户上传图片 → 显示预览（<2s）
2. 点击"Generate" → 显示进度条（AI分析中...）
3. 显示提取的参数JSON → 用户可编辑
4. 点击"Build CAD" → 生成模型（<15s）
5. 显示3D预览（可选）→ 下载STEP文件

## 6. 技术约束

### 6.1 技术栈限制
- **图片分析**（优先级排列）:
  - 🥇 智谱 AI GLM-4V - 在线 API，识别能力强，有免费额度
  - 🥈 硅基流动 Qwen2-VL - 开源模型，价格低，计数好
  - 🥉 Ollama - 本地运行（LLaVA 或 Qwen2-VL），隐私安全
  - 📚 Hugging Face BLIP - 备选方案，基础功能
- **参数提取**: 规则引擎（当前）或 LLM（未来）- 可扩展
- **参数验证**: ParameterValidator - 范围检查、逻辑验证、默认补全
- **CAD引擎**: CadQuery (Python) - 支持参数化建模
- **Web框架**: Streamlit - 快速原型，后续可迁移Flask/FastAPI
- **文件格式**: STEP AP203 - 工业标准，兼容性最高

### 6.2 环境要求
- Python ≥3.10
- 内存 ≥4GB（单次生成）
- 磁盘空间 ≥500MB（缓存+输出）

## 7. 验收标准

### 7.1 功能验收
- [ ] 上传图片后30s内生成STEP文件
- [ ] 部件文件独立存在，可单独打开
- [ ] 修改bay_width参数，beam长度自动更新
- [ ] 搭接细节（如螺栓孔）在模型中正确体现
- [ ] API接口返回标准JSON，包含所有必需字段

### 7.2 质量验收
- [ ] 代码通过Pylint检查（score≥8.0）
- [ ] 单元测试覆盖率≥70%
- [ ] 生成模型可在FreeCAD中正常打开
- [ ] 模型尺寸误差<5%（与AI提取值对比）

## 8. 风险与依赖

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| AI提取参数不准确 | 高 | 提供人工编辑界面，支持参数覆盖 |
| CadQuery性能瓶颈 | 中 | 复杂模型采用异步生成，显示进度 |
| STEP文件兼容性 | 中 | 使用AP203标准，多软件测试验证 |
| API调用成本 | 低 | 实现缓存机制，相同图片复用结果 |

## 9. 版本规划

### V1.0 (MVP)
- 基础图片输入 → CAD生成流程
- 3种部件类型（upright, beam, decking）
- Web界面基础功能

### V1.1
- 参数联动调整
- 搭接细节识别
- API接口开放

### V2.0
- 批量变体生成
- 高级部件库（斜撑、安全网等）
- 3D实时预览

