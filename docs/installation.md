# aicad 安装与平台说明

## 推荐路径

aicad 的前置链路只需要 Python、`jsonschema` 和 `python-dotenv`。真实 CAD 预览与 STEP 导出需要 CadQuery 及其 Open Cascade 依赖。项目把两者分成 `Base` 与 `CAD` 两种 profile，便于先验证输入、参数和 Layout，再补齐 CAD 环境。

### Windows PowerShell

```powershell
cd D:\Sandbox\aicad
.\setup_env.ps1 -Profile Base
.\start_local.ps1 -Port 8766
```

需要 CAD：

```powershell
.\setup_env.ps1
.\start_local.ps1 -Port 8766
```

如果团队使用 Miniforge/mamba，CAD 环境也可以按 [environment.yml](../environment.yml) 创建：

```powershell
mamba env create -f environment.yml
mamba activate aicad
python ui_server.py --port 8766
```

### macOS / Linux

```bash
cd /path/to/aicad
bash ./setup_env.sh --profile Base
bash ./start_local.sh --port 8766
```

需要 CAD：

```bash
bash ./setup_env.sh --profile CAD
bash ./start_local.sh --port 8766
```

如果使用 Apple Silicon，优先使用原生 arm64 的 Python/Miniforge，避免让 Python、OCP 和 CAD 编辑器混用 Rosetta 与 arm64。CadQuery 官方文档说明 pip 可用于 Windows、macOS 和 Linux；conda/mamba 是更成熟的安装路径。当前项目的 pip profile 仍保留；发布时建议把 conda-forge 的 `environment.yml` 作为 CAD 主路径，并在 Windows x86_64、macOS arm64 和 macOS x86_64 至少各完成一次 CAD 成功路径验收。

## 文档应放在哪里

README 只保留项目定位、快速启动和能力边界；安装、平台差异、依赖失败处理和手动验收放在本目录的安装/验收文档中。发布包还需要明确：

- Base、CAD、Vision 三种能力分别需要什么；
- 生成 STEP 前如何确认 CadQuery 已加载；
- macOS Apple Silicon、macOS Intel、Windows x86_64 的安装入口；
- 输出目录没有写权限时如何指定 `--output-dir`；
- 没有 CAD 时，浏览器仍可用 Layout manifest 预览，但不能下载 STEP。

## 发布前的 CAD 选择

CadQuery 2.8.0 仍是当前 aicad 的合理默认后端：它适合 Python 参数化建模、无界面运行和 STEP 输出，且当前项目已经有 `core/translator.py` 适配层。它不是不可替换的产品依赖。后续可以用同一份 `Layout` 契约接入 build123d 或 FreeCAD adapter，再用相同 fixture 比较实体有效性、STEP 输出和安装稳定性。

build123d 也是基于 Open Cascade 的 Python 方案，安装路径和 macOS/Windows/Linux 覆盖较清晰，适合作为下一候选；FreeCAD 更适合需要桌面 CAD 检查、人工编辑和更完整工程工作台的场景，但会带来更重的桌面运行时。当前不建议为了替换而替换，先把 CadQuery 成功路径验收完成，再做 adapter 级比较。
