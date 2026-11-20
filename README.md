# aicad · 工业仓储货架方案工作台

## 项目说明

aicad 是一项面向工业仓储货架方案的 agent 编排实验，时间约为 2025 年 10 月。它把现场照片、测量记录和已有参数整理为可复核的货架布局，并将确认后的参数交给几何构造和 CAD 交接流程。目标用户是做货架方案、现场测绘和项目交接的人员：他们经常在照片、表格和旧图纸之间反复对照，补录排数、跨数、层高和构件尺寸；当需求改变时，又要重新建模并确认假设，容易出现遗漏、口径不一致和交付文件与参数不一致。

本项目的输入分为照片、示例或参数 JSON，以及用户确认的布局和构件尺寸。agent 负责从资料中形成候选参数、标记不确定项；校验模块检查字段、单位和范围；几何契约把排布、框架位置、层高和斜撑分段统一为 Layout；构造模块据此生成布局清单，并在具备 CadQuery 时导出 mesh/STEP。界面把输入、参数确认、构造复核和交付放在同一条流程中，用户可修改参数、重新检查和下载当前版本。照片识别结果必须经过人工确认，示例值只用于体验。

我在项目中负责场景洞察、需求评估、功能设计、agent 编排、协议制定、skill 整合和基础交互框架搭建。过程先界定工业仓储现场的任务边界，再拆分资料整理、候选提取、参数校验、几何构造和文件交付等职责，制定统一的数据协议和状态规则；随后用同一套 Layout 约束 CLI、网页预览和 CAD translator，补充固定 fixture 与测试，最后用本地 UI 串起输入到输出。当前结果是离线 fixture → 校验 → manifest 链路可运行，参数错误和环境阻塞有明确反馈，8 项纯 Python 测试通过。CadQuery 环境不可用时仍可验证参数、Layout manifest 和浏览器布局预览；双排连接杆、真实尺寸资料、承载和生产可行性尚待补充，因此它是可继续验证的方案工具原型。

产品页面与跳转基准见 [docs/aicad-product-flow-outline.md](docs/aicad-product-flow-outline.md)。

## 输入、输出与工作流

| 输入 | 用途与要求 |
|---|---|
| 现场参考照片 | 在浏览器中与参数对照；当前 UI 不做自动识别 |
| 示例或参数 JSON | 作为方案起点，可通过表单和完整 JSON 修改 |
| 布局尺寸 | 每跨轴线宽度、立柱高度、单排轴线深度、跨数、层数、排布及双排间距；单位 mm |
| 构件尺寸 | 立柱、横梁、斜撑的截面参数；需使用测量或规格资料确认 |

每跨轴线宽度不是货架总外宽，单排轴线深度也不是最大外轮廓。照片无法确定的数值需要补测，示例值只用于体验。

| 输出 | 当前用途与状态 |
|---|---|
| 参数 JSON | 保存方案，交接或再次导入；UI 可下载 |
| 布局 manifest | 复核构件数量、位置、层高和默认假设；离线 CLI 可生成 |
| 三维预览 | 旋转检查当前方案几何；CadQuery 可用时走真实 mesh，缺少 CAD 时走 Layout manifest 预览 |
| STEP | 在其他 CAD 软件中继续处理；由同一预览几何导出；当前 Windows 环境已验收 |

输出用于方案复核与 CAD 交接草案。承载、供应商连接规格和加工可行性需要另行确认。

一次任务按以下顺序完成：载入示例或参数 JSON，加入现场照片对照；修改布局和构件尺寸并检查输入；生成预览后核对排数、跨数、层数和空间关系；确认后下载参数 JSON，几何生成成功时再下载同版本 STEP。修改参数会使旧预览和 STEP 失效。仓库中的 GLM 视觉提取是独立的 CLI 可选入口，尚未接入网页中的人工确认闭环。

## 功能模块与架构

| 产品模块 | 用户动作 | 对应实现 |
|---|---|---|
| 现场资料 | 参考照片、示例/JSON 导入 | `web/index.html`、`web/app.js` |
| 参数方案 | 表单修改、完整参数编辑、尺寸检查 | `web/app.js` → `ui_server.py` → `core/pipeline.py` |
| 构造复核 | 参数转统一布局，再生成几何 | `core/geometry_contract.py` → `core/translator.py`、`core/components.py` |
| 方案交付 | 下载 JSON、生成同版预览与 STEP | `ui_server.py`、`core/pipeline.py` |
| 视觉提取（可选） | 照片转候选参数 | `core/vision_agent.py`，由 `main.py` 调用 |

```text
示例 / 参数 JSON ─────────┐
                        ├→ 校验 → Layout 几何契约 ─┬→ 布局 manifest
照片 → 视觉候选参数（CLI）┘                         └→ CadQuery 构造 → mesh / STEP
                              ↑
                        Web 参数编辑与检查
```

Layout 统一排布、框架位置、层高与斜撑分段；CLI 预览和 CAD translator 使用同一套规则。新增输入方式不应改写构造，新增导出格式不应改变参数，新增货架类型需先补几何契约、构件和测试，再接入界面。

## 当前范围与证据

- 离线 fixture → 校验 → 布局 manifest 已跑通；8 项纯 Python 测试通过。
- 浏览器已走查示例加载、参数修改、非法尺寸、检查和环境阻塞反馈。
- 目前生成规则覆盖立柱、横梁、层板、底板和端部斜撑；双排连接杆尚未建模，底板无螺栓孔。
- 层板厚度、起步高度、顶部留白和斜撑间距仍有默认假设；未验证承载、完整连接或加工要求。
- CadQuery 2.8.0 已在当前 Windows 环境安装并通过真实 mesh/STEP 验收；GLM 识别质量和目标用户价值尚未验证。

## 启动与复现

准备项目环境并启动界面：

```powershell
.\setup_env.ps1 -Profile Base
.\start_local.ps1 -Port 8766
```

需要验证真实三维和 STEP 时使用 `.\setup_env.ps1`（默认安装 CAD 依赖）；只验证参数、校验和 manifest 时使用 `-Profile Base`。完整手动验收清单见 [docs/local-validation.md](docs/local-validation.md)。 macOS / Linux 入口见 [docs/installation.md](docs/installation.md)。

浏览器打开 http://127.0.0.1:8766，先从示例开始，核对字段后点击“检查参数”。

离线健康检查无需模型密钥或 CadQuery：

```powershell
.\.venv\Scripts\python.exe main.py --fixture --output-dir .\output
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```

输出 `validated_instance.json` 和 `preview_manifest.json`。输出目录不可写时，使用 `--output-dir` 指向可写位置。

安装兼容的 CadQuery 后，单独验收 STEP：

```powershell
.\.venv\Scripts\python.exe main.py --fixture --export-step --output-dir .\output
```

视觉模式需安装 `zhipuai`，并在 `.env` 中设置 `ZHIPU_API_KEY`。以下命令会把指定图片发给配置的视觉服务，然后尝试构造 STEP：

```powershell
.\.venv\Scripts\python.exe main.py --image .\tests\rack_photo.jpg --output-dir .\output
```

重新进入项目请先读 [REASSESSMENT.md](REASSESSMENT.md)。
