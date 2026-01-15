# 🛠 环境配置与依赖说明 (Environment & Setup)
本项目基于 CadQuery 构建参数化建模引擎，并采用 Multi-agent 架构进行逻辑编排。为确保几何内核（OpenCASCADE）的稳定性，必须使用 conda 进行环境隔离。

# 0. 快速开始 (Quick Start): 
本项目提供自动化环境配置脚本。在新电脑上克隆代码后，只需在 PowerShell 中运行 ./setup_env.ps1 即可完成所有 CadQuery 及预览环境的搭建。

# 1. 基础环境 (Prerequisites)
Conda 管理器: 推荐使用 Miniconda。

Python 版本: 3.10 (兼顾 AI 库与 CadQuery 的最佳版本)。

# 2. 开发环境搭建 (Installation)
在终端执行以下命令以创建并配置名为 cad 的专用环境：


### 1. 创建环境
```
conda create -n cad python=3.10 -y
```

### 2. 安装核心几何引擎 (建议使用国内镜像源以加速)
```
conda install -n cad cadquery -c conda-forge -y
```

### 3. 安装 VS Code 预览桥接库
```
conda activate cad
pip install ocp-vscode
```

# 3. VS Code 插件配置 (Extensions)
为实现“代码即模型”的实时反馈，需在 VS Code 中安装以下插件：

```
Python: (Microsoft) 提供代码补全与调试。

OCP CAD Viewer: 核心 3D 预览插件。
```

# 4. 运行与调试 (Usage)
选择解释器: Ctrl + Shift + P -> Python: Select Interpreter -> 选择路径中含有 envs\cad 的项。

开启预览窗口: Ctrl + Shift + P -> OCP: Open Viewer。

执行脚本:

```PowerShell
python tests/tabletest.py
```

#  📐 核心架构衔接 (Architecture Integration)

在重构过程中，环境与代码逻辑的对应关系如下：

```
CadQuery: 作为 Agent 3 (Assembly) 的执行层，负责将参数转化为 B-Rep 实体几何。

ocp-vscode: 作为开发阶段的 反馈环，用于验证 Agent 2 翻译生成的代码是否符合建筑构造逻辑。

Conda Environment: 确保了从视觉分析到几何生成的全链路在不同设备（如当前的新电脑）上的 环境一致性。
```

