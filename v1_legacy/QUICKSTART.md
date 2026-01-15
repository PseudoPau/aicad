# 快速开始指南

## 环境准备

### 1. 激活 conda 环境
```powershell
conda activate aicad_hackathon
```

### 2. 安装基础依赖
```powershell
pip install streamlit requests python-dotenv
```

### 3. 可选：安装 Hugging Face 支持（备选方案）
```powershell
pip install transformers pillow torch
# 或按官网选择合适的 CUDA 版本
```

---

## 配置 API Key

### 方式 1: 使用 Streamlit UI（推荐，无需配置）
1. 运行 `streamlit run app.py`
2. 在侧栏选择分析方法
3. 在侧栏输入对应的 API Key
4. 上传图片进行分析

### 方式 2: 创建 .env 文件（自动读取）
```bash
# 复制 .env.example 为 .env
cp .env.example .env

# 编辑 .env，填入你的 API Key
# ZHIPU_API_KEY=your_key_here
# SILICONFLOW_API_KEY=your_key_here
```

---

## 快速测试

### 步骤 1: 启动应用
```powershell
streamlit run app.py
```

### 步骤 2: 选择分析方法
侧栏中优先级顺序：
1. 🌟 **智谱 AI GLM-4V** - 识别能力强（推荐）
2. 🌟 **硅基流动 Qwen2-VL** - 开源模型，价格低（推荐）
3. 💻 **Ollama** - 本地运行
4. 📚 **Hugging Face BLIP** - 备选

### 步骤 3: 上传图片
上传一张仓库或货架的图片（JPG/PNG）

### 步骤 4: 点击 "Analyze Image"
系统会自动：
1. **Step 1** - 生成图片描述（AI 分析）
2. **Step 2** - 提取结构化参数（规则引擎）
3. **Step 3** - 验证参数并补全缺失值
4. 保存结果到 `output/analysis/`

---

## 获取 API Key

### 智谱 AI GLM-4V（推荐）
1. 访问 https://open.bigmodel.cn/
2. 注册账号
3. 进入"API Keys"页面创建密钥
4. **有免费额度**，识别能力强

### 硅基流动 Qwen2-VL（推荐）
1. 访问 https://siliconflow.cn/
2. 注册账号
3. 获取 API Key
4. **价格极低**，Qwen2-VL 对计数支持好

### Ollama（本地，无需 Key）
1. 下载：https://ollama.ai/download
2. 安装后运行：`ollama pull llava` 或 `ollama pull qwen2-vl`
3. Ollama 会在后台运行服务（http://localhost:11434）

---

## 输出文件说明

分析完成后，输出文件保存在 `output/analysis/` 目录：

```
output/analysis/
├── image_001_description.txt       # 图片描述（纯文本）
├── image_001_parameters.json       # 提取的参数（JSON 格式）
└── ...
```

### image_001_parameters.json 结构示例
```json
{
  "warehouse_config": {
    "overall_layout": {
      "rows": 2,
      "row_spacing": 3000.0,
      "orientation": "north-south"
    }
  },
  "racking_system": {
    "dimensions": {
      "bay_width": 2400.0,
      "bay_depth": 1000.0,
      "total_height": 6000.0
    },
    "structure": {
      "levels": 3,
      "first_beam_height": 200.0,
      "beam_spacing": 1800.0
    },
    "components": { ... },
    "connection_details": { ... }
  }
}
```

---

## 常见问题

### Q: 我应该用哪个分析方法？
**A:** 推荐顺序（按识别能力和性价比）：
- 🥇 **智谱 AI** - 识别能力最强（推荐首选）
- 🥈 **硅基流动** - 开源模型，价格最低
- 🥉 **Ollama** - 完全本地，隐私第一

### Q: 没有 API Key 怎么办？
**A:** 选择 **Ollama** 或 **Hugging Face BLIP**（都不需要 API Key）

### Q: Hugging Face 方案需要什么？
**A:** 
```powershell
pip install transformers pillow torch
# 首次运行会下载 1GB 模型（BLIP），之后会缓存
```

### Q: 可以离线使用吗？
**A:** 是的，使用 **Ollama** 方案可以完全离线：
```powershell
ollama pull llava
# 之后完全本地运行，无需网络
```

---

## 下一步

M2 阶段已完成（AI 分析 + 参数提取 + 验证）

接下来：
- **M3**: 实现 CAD 模型生成（部件独立生成、装配体组装）
- **M4**: 搭接细节识别与模型优化
- **M5**: REST API 开发与文件管理

---

## 技术栈版本

| 组件 | 版本 | 备注 |
|------|------|------|
| Python | 3.10+ | 推荐 3.10.19 |
| Streamlit | 1.28+ | Web UI |
| PyTorch | 2.0+ | 可选（仅 Hugging Face） |
| Transformers | 4.30+ | 可选（仅 Hugging Face） |
| Requests | 2.28+ | HTTP 客户端 |

