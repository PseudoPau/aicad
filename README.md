# image-to-cad (PoC)

"From Pixels to Tectonics" —— 本项目不仅是视觉识别，更是利用参数化逻辑对空间物理规则的数字化重构。
这是一个基于 AI 视觉识别的参数化建模工具原型。它实现了从**现场照片**到**标准 CAD 几何体**的全自动转化。

<img width="1289" height="718" alt="84237e88549699f01c8c1abc1bfcfb91" src="https://github.com/user-attachments/assets/147858d1-66bc-49ba-ab2d-2172467ad641" />

## 🏗️ 核心演进：从形状到系统

与普通的 3D 生成工具不同，本项目的重点在于解决工业场景中的 **结构建构（Tectonic Logic）** 问题，不仅看起来“像”，而且实际好用：

- **拓扑自动识别**: 能够准确识别并重构“双排背靠背（Back-to-Back）”布局及其物理连接件（Spacer Bars）。
- **物理堆叠逻辑**: 抛弃了简单的几何重心对齐，实现了层板（Panel）与横梁（Beam）的物理支撑对位，消除了 3D 建模中的穿模（Clash）干涉。
- **自适应 Z 型斜撑**: 引入动态模数逻辑，根据货架高度自动计算最优支撑密度（Modular Bracing），实现了斜撑端点与立柱中心线的像素级对齐。
- **扫地高度适配**: 自动复刻工业标准的底部起步高度（Bottom Offset），确保模型符合叉车操作等实际物流工程需求。

## 📐 几何逻辑证明

为了保证生成的 .step 模型可直接用于工业生产，
- 本项目通过严谨的三角函数锁定构件姿态： ```斜撑倾角: $\theta = 90^\circ - \arctan(h/D)$。```
- 通过复合旋转矩阵将垂直杆件锁定在 ```$YZ$``` 平面内。
- **LOD 350 细节**: 模型包含真实的 Omega 立柱截面、底脚板螺栓位及层板边缘倒角。

## 🌟 技术架构
采用“分层解耦”的 Multi-agent 架构，平衡了 AI 的灵活性与 CAD 的严谨性：
- **Vision Agent**: 利用智谱 GLM-4V 提取工业货架的几何参数。
- **Schema Validation**: 采用 JSON Schema 严格校验 AI 提取数据的合法性。
- **CAD Translation**: 使用 CadQuery (OpenCASCADE) 引擎自动生成 3D STEP 模型。

<img width="1293" height="723" alt="250334ce3bba7d52c4fa555856c1557a" src="https://github.com/user-attachments/assets/49fdf83f-9e8f-4e5b-8844-c0932080bdc4" />

## 🛠️ 技术栈
- **Language**: Python 3.10+
- **AI Model**: ZhipuAI (GLM-4V)
- **CAD Engine**: CadQuery
- **Architecture**: Multi-agent Decoupling (Vision, Validator, Translator)

## 📂 项目结构
```
AICAD/
├── aicad/
│   ├── core/           # 包含组件库 (components.py) 与翻译引擎 (translator.py)
│   ├── schema/         # v2.2 工业级 JSON 协议规范
│   └── main.py         # 全链路运行入口
├── output/             # 自动生成识别后的 JSON 与 STEP 模型
└── requirements.txt    # 核心依赖：cadquery, zhipuai
```

## 🚀 快速启动
1. 克隆仓库。
2. 在 `.env` 中填入你的 `AI_API_KEY`。
3. 运行 `python main.py`。


