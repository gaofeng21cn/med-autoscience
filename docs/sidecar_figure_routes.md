# Sidecar Provider 与 Figure Routes 指南

> 这个指南可以从 [`agent_runtime_interface.md`](./agent_runtime_interface.md) 中的“sidecar provider 与 figure routes 指南”入口访问，是对运行层中 sidecar 周期的稳定说明。

## 1. Sidecar provider 在 MedAutoScience 的定位

1. **主线 runtime 默认是 MedDeepScientist。** Sidecar provider 只是为 `MedDeepScientist`（仓库名 `med-deepscientist`）提供受控扩展的 bounded route，不能取代主线 runtime 处理模型训练、评估或结果收敛流程。Sidecar 的执行上下文必须在 `MedDeepScientist` 任务框架内被调度、监控与审计。
2. **Sidecar 不是随意“绕过主线”的后门。** 任何 sidecar 调用都应报告其 trigger、recommendation gate 结论，以及最终 handoff root，这样人类审阅者可以追溯为什么选择 sidecar 以及它的输出对主线决策有哪些影响。

## 2. Sidecar provider 契约

Sidecar 运行必须遵守下列核心契约条款：

- **Recommendation gate。** Sidecar 不得自行决定何时执行。它必须先经过 recommendation gate；当 gate 为推荐态时，结论会落到 `runtime/quests/<quest-id>/sidecars/<provider>/<instance-id>/recommendation.json`，等待明确确认后才能继续。
- **Frozen input contract。** Sidecar 接受的输入必须冻结为只读 contract，并落到 `runtime/quests/<quest-id>/sidecars/<provider>/<instance-id>/input_contract.json`。Sidecar 不得直接改写源数据、模型 checkpoint、registry 或主线结果文件。
- **Handoff root 明确。** Sidecar 执行阶段只能向 `runtime/quests/<quest-id>/sidecars/<provider>/<instance-id>/handoff/` 产生产物。调用方只读取这个 handoff root，而不是从临时目录、对话附件或未登记缓存中“顺手拿结果”。
- **Manifest/Hash 对齐。** Handoff 内必须提供 `sidecar_manifest.json`，并且其中的 `input_contract_hash`、`artifacts_generated` 等字段需要与冻结 contract 和真实产物对齐。导入时如果 hash 不一致，必须直接阻断，而不是静默兼容。
- **Import into audit surface。** Sidecar 的可消费结果必须再导入到 `runtime/quests/<quest-id>/artifacts/<domain>/<provider>/<instance-id>/`。也就是说，`sidecars/` 是受控执行与交接面，`artifacts/` 才是供主线审阅、复核和交付引用的审计面。

## 3. Figure illustration 的平台边界

1. **说明性图统一走程序化绘图。** 当前平台只保留 `figure_illustration_program:<figure-id>` 这一路由来处理 `method_overview`、`study_workflow`、`graphical_abstract`、`cohort_schema` 等说明性图。它们可以承担“方法说明、研究流程、图形摘要、队列结构示意”等角色，但不能承载核心结果证据。
2. **不再假定外部绘图 sidecar。** MedAutoScience 不再为说明性图保留独立外部绘图 runtime、provider registry 或 bootstrap 入口。说明性图的质量控制由平台自己的程序化绘图规范、脚本审计面和 manuscript surface 共同承担。
3. **禁止范围。** 程序化说明性图不得进入 `metric_number_editing`、`claim_change`、`result_plot_generation` 三类 scope。也就是说，严禁用说明性图路线修改任何数值证据、结果图（如 ROC、KM、校准、DCA、forest、SHAP、亚组统计图）、claim 文字或结论性结果标注。
4. **结果图必须保留原始 artifact。** 如果结果图需要修正，应通过 `MedDeepScientist` 主线 pipeline 输出新的 artifact，然后在 audit surface 中写明差异、原因、责任人；绝不能借助说明性图路线偷换 claim 数据。
5. **renderer family 也是正式 contract。** 路由只回答“这是证据图修复还是说明性图绘制”；真正的渲染技术栈还必须在 `paper/figure_semantics_manifest.json` 里锁定。允许矩阵是：`evidence -> python | r_ggplot2`，`illustration -> python | r_ggplot2 | html_svg`。其中 `html_svg` 永远不能用于证据型图。
6. **严禁 failure-driven renderer switch。** 不允许因为环境缺包、依赖损坏、R/Python 运行失败、浏览器导出失败等原因，从一个 renderer family 偷偷切到另一个 family。正确动作只有阻断并修环境，即 `fallback_on_failure=false` 且 `failure_action=block_and_fix_environment`。

## 4. Figure routes：两类显式路由

- **figure_script_fix:<figure-id>** 适用于 `MedDeepScientist` 主线已经定义好的 figure artifact，但当前图的脚本、模板、导出层或排版层存在问题，需要在冻结数据与冻结脚本边界内重新生成。它服务的是“证据型图修复”，不是“插图美化”，因此应保留结果图与其脚本的直接对应关系。
- **figure_illustration_program:<figure-id>** 适用于说明性图，由独立程序绘图路线生成 manuscript-safe 的方法图、流程图、schema 图。它同样不能承载结果证据，也不依赖任何外部绘图 runtime。
- **适用边界对照。** 如果要改动的图是直接支撑 claim/结果的 artifact，应走 `figure_script_fix` 由 `MedDeepScientist` 原生 pipeline 产生，并把 renderer family 锁定为 `python` 或 `r_ggplot2`；如果图只是说明性图，则走 `figure_illustration_program`，renderer family 可为 `python`、`r_ggplot2` 或 `html_svg`。旧的 `figure_illustration_sidecar` 和任何外部绘图 sidecar 路由都属于已废弃歧义入口，不应再使用。

## 5. 审计与人类复核要求

Sidecar 产出的 figures 与说明文案必须至少能追溯这几层内容：为什么进入 sidecar、冻结输入是什么、handoff 里交了什么、导入后的 artifact 在哪里。人类复核时，优先检查 `recommendation.json`、`input_contract.json`、`sidecar_state.json`、`handoff/sidecar_manifest.json`，以及导入后的 `artifacts/<domain>/<provider>/<instance-id>/`。只有当这些环节都闭合时，sidecar 才是可接受的 bounded route；否则它只是未审计的旁路。

另外，论文面向的 figure/caption 不得混入工具广告、服务链接、`Sources:`、`Why this matters` 这类海报化标注。此类文案应在 manuscript-facing surface 上被直接阻断，而不是靠人工事后删改。

## 参考链接

- [`docs/agent_runtime_interface.md`](./agent_runtime_interface.md)：Agent Runtime Interface 提供整个运行层的入口路径。
