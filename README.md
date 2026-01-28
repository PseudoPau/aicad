# image-to-cad (PoC)

这是一个基于 AI 视觉识别的参数化建模工具原型。它实现了从**现场照片**到**标准 CAD 几何体**的全自动转化。

## 🌟 核心功能
- **Vision Agent**: 利用智谱 GLM-4V 提取工业货架的几何参数。
- **Schema Validation**: 采用 JSON Schema 严格校验 AI 提取数据的合法性。
- **CAD Translation**: 使用 CadQuery (OpenCASCADE) 引擎自动生成 3D STEP 模型。

## 🛠️ 技术栈
- **Language**: Python 3.10+
- **AI Model**: ZhipuAI (GLM-4V)
- **CAD Engine**: CadQuery
- **Architecture**: Multi-agent Decoupling (Vision, Validator, Translator)

## 📂 项目结构
- `core/`: 核心逻辑（识别、验证、翻译、组件库）
- `schema/`: 数据协议规范
- `tests/`: Few-shot 范例与测试图片

## 🚀 快速启动
1. 克隆仓库。
2. 在 `.env` 中填入你的 `ZHIPU_API_KEY`。
3. 运行 `python main.py`。

<img width="1287" height="722" alt="1b91278c-08c5-4dd1-8a76-d5c67e08a2e7" src="https://github.com/user-attachments/assets/5c81063c-0d5f-455d-a81f-73e3ecd31202" />
