# 本地启动与手动验收

安装与平台差异见 [installation.md](installation.md)。本页只负责启动后的手动验收。

项目根目录：`D:\Sandbox\aicad`。当前应用由 Python 本地服务和原生 HTML/CSS/JavaScript 组成，没有前端打包步骤。

## 1. 准备环境

使用 Windows PowerShell，建议 Python 3.12。安装和启动脚本只操作项目内的 `.venv`，不修改全局 Conda 设置。

```powershell
cd D:\Sandbox\aicad
.\setup_env.ps1
.\start_local.ps1
```

默认安装基础依赖与 CadQuery。首次安装需要联网下载依赖。浏览器打开 <http://127.0.0.1:8766>；终端按 `Ctrl+C` 停止服务。

若 PowerShell 阻止执行本地脚本，使用本次进程级方式运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_env.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_local.ps1
```

只验证参数编辑、校验和确定性布局链路：

```powershell
.\setup_env.ps1 -Profile Base
```

安装可选视觉 CLI：

```powershell
.\setup_env.ps1 -WithVision
```

视觉模式还需要在 `.env` 中配置 `ZHIPU_API_KEY`；本地浏览器的照片入口仅供对照，不调用视觉服务。手动验收不需要密钥。

端口冲突时：

```powershell
.\start_local.ps1 -Port 8767
```

## 2. 自动健康检查

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
.\.venv\Scripts\python.exe main.py --fixture --output-dir .\output\local-validation
.\.venv\Scripts\python.exe main.py --fixture --export-step --output-dir .\output\local-validation
```

前两条应通过并生成 `validated_instance.json`、`preview_manifest.json`；第三条还应生成 `assembly_result.step`。不安装 CadQuery 时，第三条应报告缺少 CAD 依赖。如果项目目录的 `output` 没有写权限，把 `--output-dir` 改成用户有写权限的目录。

## 3. 手动验收清单

| 操作 | 应看到的结果 |
|---|---|
| 打开工作台、载入示例 | 参数表单、完整 JSON 与来源说明显示；CAD 环境状态可见 |
| 将立柱高度改为 0，点击“检查参数” | 显示对应参数错误，不能获得可用 STEP |
| 恢复为正数并检查 | 显示参数校验通过 |
| 点击“生成 / 更新预览” | CAD 可用时出现真实几何，生成成功反馈与版本号；缺少 CAD 时出现 Layout manifest 复核预览，STEP 保持禁用 |
| 拖拽、滚轮、重置视角 | 几何能旋转、缩放和复位 |
| 由背靠背双排改为单排并重新生成 | 预览排数变化，构件随布局变化 |
| 修改跨数、层数并重新生成 | 几何与参数一致，不继续展示旧版本交付状态 |
| 已生成后再次改参数 | STEP 下载失效，提示需要重新生成 |
| 下载当前参数 JSON，再导入 | 参数可还原，重新检查和生成 |
| 下载 STEP，在 CAD 软件中打开 | 可读取几何，排数、跨数、层数与预览一致 |
| 添加现场照片 | 浏览器出现照片供对照，参数不会自动改变 |

本地服务只监听 `127.0.0.1`。当前 STEP 下载暂存在服务进程的临时目录；停止服务后需要重新生成。

## 4. 本次验证状态

- 已完成：项目 `.venv` 基础依赖检查、8 项单元测试、Python/JavaScript 语法检查、fixture 校验与 manifest 输出；本地浏览器已走通示例载入和参数检查。
- 已完成：UI 逻辑层验证了合法参数、非法尺寸和缺少 CadQuery 三种状态。
- 已完成：CadQuery 2.8.0 实体有效性、真实 mesh 与 STEP 成功路径；STEP 回读后 132 个实体有效。无 CAD 时的 Layout manifest 预览也可走查。
- 当前构造范围：立柱、横梁、层板、底板、端部斜撑；双排连接杆和底板孔未建模。
- 发布前检查：当前 Windows CAD 路径已通过；仍需完成浏览器手动走查，以及 macOS arm64/Intel 的 CAD 环境验收。
