# PRD2：基于当前实现的交付优先级说明（中文）

版本说明：本文件为在当前代码库状态（2025-11-23 快照）基础上反向整理的产品需求文档（PRD2），聚焦可交付的 MVP 范围、已完成/未完成项、验收标准与短期路线。

一、目标概述
- 产品：AI 驱动的参数化仓库货架建模工具（Web 前端 + 后端 CAD 生成），输入为图片或 JSON，输出工业兼容的 STEP 文件及可复用部件文件。
- 目标：在现有代码基础上快速交付可演示的 MVP 并保证可重复（可在本地/演示机上运行）。

二、MVP 范围（必须达成）
- 上传图片（JPG/PNG）并保存；
- AI/规则分析 → 提取参数（JSON）；
- 参数校验与补全（规则引擎）；
- 单排单层货架建模：生成独立部件（upright、beam、decking）的 STEP 文件，并生成装配体 `warehouse_assembly.step`；
- 前端（Streamlit）支持从上传到生成的端到端演示流程，能下载最终 STEP 文件；
- 产出诊断文件：`cadquery_called.txt`、`assembly_info.json`、`metadata.json`、`generation.log`。

三、已完成（当前仓库状态）
- 文件上传与 Streamlit UI 框架：`frontend/app.py`（上传、保存、预览、UI 步骤已就绪）；
- 参数提取器（规则/JSON 感知）：根目录 `parameter_extractor.py` 能解析 fenced/inline JSON 并提供 fallback；
- 参数校验器：`backend/M2/parameter_validator.py` 实现范围检查、逻辑校验与默认值填充；
- CAD 组件生成与装配：`backend/M3/component_factory.py` 與 `backend/M3/assembly_manager.py` 已实现并经 headless 验证；
- 按部件导出与 metadata：`assembly_manager.export_step()` 已扩展为导出 `components/` 下的单件 STEP，并生成 `metadata.json`；
- 单元测试：`tests/test_parameter_extractor.py` 已修复并通过；
- 启动脚本与日志：`scripts/start_streamlit_with_log.ps1` 可启动 Streamlit 并记录 `output/analysis/streamlit_run.log`。

四、未完成 / 风险点
- UI 交互完整验证：需在浏览器中手动执行上传→Analyze→Generate 全流程确认（当前已启动服务，但需要人工点击验证）；
- 参数联动（实时调整）与 preview：尚未实现 `bay_width` 等参数在 UI 上可交互调整并实时预览（应作为 P0 增强）；
- API 服务：尚未提供 REST API（`/api/v1/generate`），需为自动化/Agent 提供接口；
- CI 与测试覆盖率：缺少 CI 工作流和充足的测试覆盖（PRD 要求 ≥70%），CadQuery 相关测试在非本地 runner 上可能不稳定；
- AI 后端依赖：集成点已存在但需 API Key 或本地模型（建议演示时用 mock 或规则提取兜底）；
- 原生库/运行时稳定性：某些 headless 运行会返回 native 非零退出码（虽然文件正常生成），可能导致自动化误报。

五、验收标准（MVP）
- F1：用户在浏览器上传图片並能看到預覽（通过 `frontend/app.py`），Upload 成功並保存到 `output/uploads/`；
- F2：点击 Analyze 后能得到 AI/规则返回的描述文本，并能在 UI 中看到提取的参数 JSON；
- F3：点击 Generate（或 Build CAD）后，生成以下文件在同一 `output/analysis/<timestamp>/` 目录下：
  - `warehouse_assembly.step`（>1KB 且能由 CAD 软件打开）
  - `components/*.step`（每个部件独立 STEP）
  - `metadata.json`（记录 assembly 与 components 信息）
  - `assembly_info.json`（装配 bbox）
  - `cadquery_called.txt`（cadquery 标记）
- F4：参数校验通过或返回可视化的校验信息（`ParameterValidator` 的 `validation_errors` 可以在 UI 显示）；
- F5：在无 AI 后端时，规则提取器能作为兜底方案并完成整个流程（用于离线演示）。

六、数据格式（输入/输出）
- 输入（API / UI）示例：
```
{
  "input_type": "image_url | base64 | file_path",
  "image_data": "...",
  "user_prompt": "... (optional)",
  "override_params": {"bay_width": 2400.0, "levels": 3}
}
```
- 规范输出（M2→M3）保留现有字段：`warehouse_config`、`racking_system.dimensions`、`racking_system.structure`、`components`、`connection_details`。

七、API 设计（简要，供实现参考）
- POST `/api/v1/generate` — 请求体为上面的 JSON，返回：
```
{ "task_id": "<id>", "status": "queued|running|finished|failed", "result_url": "<optional>" }
```
- GET `/api/v1/status/{task_id}` — 返回任务当前状态与 result_url（如就绪）；
- 说明：可先实现同步版本（直接返回 file path），再迭代异步/队列化。

八、非功能性需求
- 运行环境：Python ≥3.10、内存 ≥4GB（推荐 8GB）、磁盘空间 ≥500MB 可用；
- 性能目标（MVP）：单次 headless 生成 < 30s（取决于 CadQuery 与模型响应）；
- 可靠性：AI 调用应有重试与缓存策略（同一图片复用结果）；
- 兼容性：输出 STEP 应符合通用格式（AP203/AP214），能在 FreeCAD/Fusion 里打开。

九、优先级与短期路线（基于当前实现）
- P0（现在做）：
  1. 在 `frontend/app.py` 添加最少量参数控件（`bay_width`、`levels`），并把 `override_params` 传入 `generate_warehouse_step()`；
  2. 手动在浏览器中完成一次端到端演示並记录路径与产出目录；
  3. 统一 `parameter_extractor` 的实现（保留根目录实现作为单一源）。
- P1（2–5 天）：
  1. Scaffold FastAPI `/api/v1/generate`（同步或异步）；
  2. 增加缓存/重试与成本控制策略；
  3. 补充单元测试并添加 CI（跳过或 mock CadQuery 测试在无原生依赖时）。
- P2（长期）：批量变体、细化连接细节、在线 3D 预览等。

十、短期验收清单（执行者检查项）
1. `streamlit run app.py`，通过 UI 上传图片并点击 Analyze 与 Generate（验收 F1-F3）；
2. 检查 `output/analysis/<timestamp>/` 是否包含上述文件；
3. 在 README 或 docs 中记录运行步骤与已知问题（native exit code 风险说明）。

十一、负责人建议
- 前端（UI）与演示：负责修复与添加参数控件（前端或全栈）；
- 后端（API & 任务）：负责 FastAPI 与异步队列（后端）；
- 测试与 CI：负责创建 Actions，处理 CadQuery 测试策略（DevOps/维护者）。

——

说明：本 PRD2 旨在把当前实现与 PRD 要求对齐，突出可交付的最小工作集与短期优先级。若你同意我可以：
- 立刻修改 `frontend/app.py` 添加参数控件（P0），並做一次 headless 验证；
- 或先 scaffold 一个同步的 `/api/v1/generate` 以便自动化调用。
