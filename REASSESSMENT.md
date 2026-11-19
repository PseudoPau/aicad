# aicad 重新评估入口

核对日期：2026-11-19。当前本地副本来自远端提交 4074c80。

## 当前定位

先验证一个窄任务：货架方案设计或现场测绘人员用一到两张现场照片和少量确认尺寸，得到可校正、可检查、可导出的货架几何草案，用于复核、报价或 CAD/加工交接。暂不承诺生产级结构设计或通用图生 CAD。

## 证据状态

- E0：视觉参数提取、Schema 校验、CadQuery 翻译和 STEP 导出代码存在。
- E1（局部）：tests/shelf_instance.json 在当前 Python 3.12 + jsonschema 下可通过校验。
- 未成立：当前环境没有 CadQuery 和智谱 SDK；没有真实模型调用、几何检查、实物尺寸或目标用户验证。
- 主要断点：环境变量和依赖口径、写死的输入路径、硬编码尺寸、Schema 业务约束、README 超出实现的宣传描述。

## 首轮工作包

1. A1：固定依赖、入口、输入输出和无模型验证。
2. B1：单排/双排 fixture、Schema/组件/层高检查和 STEP 产物检查。
3. A/B 通过后再做示例文档，再评审上传、校正、预览、修改、检查和导出的交互闭环。
4. 真实模型调用和目标用户任务另行记录，不把代码测试当成产品价值证据。

完整的输入、动作、验收、暂停和恢复点保存在本轮工作区的 PLAN.md：
C:\Users\wei.zhang\Documents\Codex\2026-11-19\aicad-iteration\PLAN.md

本文件是本地恢复锚点，不代表已完成自主迭代，也没有改变远端公开状态。

## 2026-11-19 首轮切片状态

已完成：

- A1 离线入口：main.py --fixture 可运行，输出 validated_instance.json 和 preview_manifest.json；输入和输出路径可配置。
- B1 几何契约：core/geometry_contract.py 统一行列、层高、斜撑和组件计数规则；core/pipeline.py 与其共用布局。
- 构造回归：tests/test_geometry_contract.py 与 tests/test_pipeline.py 共 8 项 unittest 全部通过。
- UI 垂直切片已接入同一 validate_instance/build_preview 接口；真实三角网格和 STEP 仍以 CadQuery 为准。
- requirements-minimal.txt 区分离线依赖与可选 CadQuery/智谱依赖。

当前阻塞：

- 当前 Python 环境没有 CadQuery；pip 访问 pypi.org 也因 DNS 失败，STEP 尚未在本机重现。
- 真实 GLM 调用尚未执行；没有把 preview manifest 当作 STEP 或生产级结构证明。

下一包：

1. 在可安装 CadQuery 的环境跑固定 fixture，检查 STEP 是否生成、组件位置是否与 geometry_contract 一致。
2. 在 UI 中完成参数来源、校正、预览、检查、导出状态闭环。
3. 用一个单排 fixture 证明第二种布局仍走同一 geometry_contract，作为拓展性验收。

架构补充：

- core/translator.py 现在直接消费 geometry_contract.Layout，不再重复计算 rows、beam_z 或 brace_segments。
- UI 的 preview manifest 和 CadQuery translator 因此共享同一布局契约；新增单排/双排等变体时，先扩展 contract，再由两个适配层消费。
