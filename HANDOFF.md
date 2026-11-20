# aicad 交接资料

## 目标与标准

形成“输入→校验→Layout→预览→STEP”链路。标准：错误可定位、结果同版本、安装可复现，再决定发布。承载、安全、GLM 和商业价值未证明。

## 状态与验证

**已完成**：`core/` 统一校验、布局和 CAD 构造；`ui_server.py`/`web/` 实现工作台。Windows 已安装 Python 3.12.9/CadQuery 2.8.0。8 项测试、manifest、STEP 导出及回读通过；回读 STEP 有效，含 132 个实体。

**进行中**：浏览器 CAD 完整手动走查。

**未验证**：macOS、纯隔离 `.venv` 重建、GLM、双排连接杆、承载和生产可行性。

## 决定

Layout 是输入、网页和 translator 的共同契约。CadQuery 2.8.0 为默认后端；`environment.yml` 为 CAD 环境路径。manifest 只作布局预览；改参数即使旧结果失效。

## 必要文件

`README.md`/`HANDOFF.md`：说明；`core/`：链路；`ui_server.py`/`web/`：UI；`main.py`/`tests/`：CLI/测试；`requirements*`、`environment.yml`、`setup_env.*`、`start_local.*`：环境；`docs/`：安装/验收/流程。

## 下一步（最多三项）

1. 保持 `start_local.ps1`，刷新 `http://127.0.0.1:8766`，验证示例、错误、旋转、修改、JSON/STEP。
2. 重建 `.venv`，重跑安装、测试、导出和回读。
3. 按安装文档验收 macOS，再决定发布。

## Git 与接续

分支 `main`，基准 `0aa5a4d`（HEAD）。未提交：`README.md`、`requirements*`、`setup_env.ps1`、`test_translator.py`、`ui_server.py`、`web/`。未跟踪：`HANDOFF.md`、`docs/`、`environment.yml`、`setup_env.sh`、`start_local.*`。需同步这些源文件；运行需 Python 3.11/3.12、CAD 依赖。`output` 不可写时用 `--output-dir`。
