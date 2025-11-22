# AICAD 仓库自动建模平台

## 项目简介
AICAD 是一个基于 Python 和 Streamlit 的 Web 应用，自动生成仓库几何模型（STEP/STL），支持参数化建模和 AI 辅助设计。

## 目录结构

```
AICAD/
├── 📂 output/             # 生成的 .step 和 .stl 文件
├── 📂 docs/               # 演示截图、架构图、参考图片
├── 📂 .streamlit/         # (可选) Streamlit UI 配置
├── .gitignore             # Git 忽略文件
├── app.py                 # Web 界面入口
├── warehouse_builder.py   # 几何引擎核心
├── requirements.txt       # 依赖列表
└── README.md              # 项目说明书
```

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 运行应用：
   ```bash
   streamlit run app.py
   ```

## 主要功能
- 参数化生成仓库模型（STEP/STL）
- 支持 AI 辅助设计
- Web 界面交互

## 依赖
- cadquery
- streamlit
- python-dotenv
- openai

## 贡献
欢迎提交 issue 和 PR！

## License
MIT
