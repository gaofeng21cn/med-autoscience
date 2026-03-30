# Sidecar Provider 与 Figure Routes 指南

> 这个指南可以从 [`agent_runtime_interface.md`](./agent_runtime_interface.md) 中的“sidecar provider 与 figure routes 指南”入口访问，是对运行层中 sidecar 周期的稳定说明。

## 1. Sidecar provider 在 MedAutoScience 的定位

1. **主线 runtime 仍然是 DeepScientist。** Sidecar provider 只是为 DeepScientist 提供受控扩展的 bounded route，不能取代 DeepScientist 处理模型训练、评估或结果收敛流程。Sidecar 的执行上下文必须在 DeepScientist 任务框架内被调度、监控与审计。
2. **Sidecar 不是随意“绕过主线”的后门。** 任何 sidecar 调用都应报告其 trigger、recommendation gate 结论，以及最终 handoff root，这样人类审阅者可以追溯为什么选择 sidecar 以及它的输出对主线决策有哪些影响。

## 2. Sidecar provider 契约

Sidecar 运行必须遵守下列核心契约条款：

- **Recommendation gate。** Sidecar 不得自行决定何时执行。它必须先经过 recommendation gate；当 gate 为推荐态时，结论会落到 `runtime/quests/<quest-id>/sidecars/<provider>/<instance-id>/recommendation.json`，等待明确确认后才能继续。
- **Frozen input contract。** Sidecar 接受的输入必须冻结为只读 contract，并落到 `runtime/quests/<quest-id>/sidecars/<provider>/<instance-id>/input_contract.json`。Sidecar 不得直接改写源数据、模型 checkpoint、registry 或主线结果文件。
- **Handoff root 明确。** Sidecar 执行阶段只能向 `runtime/quests/<quest-id>/sidecars/<provider>/<instance-id>/handoff/` 产生产物。调用方只读取这个 handoff root，而不是从临时目录、对话附件或未登记缓存中“顺手拿结果”。
- **Manifest/Hash 对齐。** Handoff 内必须提供 `sidecar_manifest.json`，并且其中的 `input_contract_hash`、`artifacts_generated` 等字段需要与冻结 contract 和真实产物对齐。导入时如果 hash 不一致，必须直接阻断，而不是静默兼容。
- **Import into audit surface。** Sidecar 的可消费结果必须再导入到 `runtime/quests/<quest-id>/artifacts/<domain>/<provider>/<instance-id>/`。也就是说，`sidecars/` 是受控执行与交接面，`artifacts/` 才是供主线审阅、复核和交付引用的审计面。

## 3. AutoFigure-Edit 的使用边界

1. **允许范围。** 当前 provider registry 只允许 AutoFigure-Edit 处理非证据型图，并把 figure type 限定为 `method_overview`、`study_workflow`、`graphical_abstract`、`cohort_schema`。这类图可以承担“方法说明、研究流程、图形摘要、队列结构示意”等角色，但不能承载核心结果证据。
2. **禁止范围。** 当前 registry 明确禁止 AutoFigure-Edit 进入 `metric_number_editing`、`claim_change`、`result_plot_generation` 三类 scope。也就是说，严禁用它修改任何数值证据、结果图（如 ROC、KM、校准、DCA、forest、SHAP、亚组统计图）、claim 文字或结论性结果标注。
3. **结果图必须保留原始 artifact。** 如果确需对结果图做微调，应通过 DeepScientist 本体输出新的 artifact，然后在 audit surface 中写明差异、原因、责任人；绝不能借助 AutoFigure-Edit 偷换 claim 数据。

## 4. Figure routes：figure_script_fix 与 figure_illustration_sidecar 区别

- **figure_script_fix:<figure-id>** 适用于 DeepScientist 主线已经定义好的 figure artifact，但当前图的脚本、模板、导出层或排版层存在问题，需要在冻结数据与冻结脚本边界内重新生成。它服务的是“证据型图修复”，不是“插图美化”，因此应保留结果图与其脚本的直接对应关系。
- **figure_illustration_sidecar:<figure-id>** 适用于非证据型插图，允许通过 sidecar provider 独立生成或修订，但输入仍然要冻结、handoff 仍然要走 manifest/hash、结果仍然要导入 `artifacts/` 审计面。它服务的是“说明性图产物”，不是主线结果图替代品。
- **适用边界对照。** 如果要改动的图是直接支撑 claim/结果的 artifact，应走 `figure_script_fix` 由 DeepScientist 原生 pipeline 产生；如果图只是说明性、或为 paper/slide 提供视觉辅助，可以用 `figure_illustration_sidecar`，但仍须注明这是 sidecar 产物并保持独立版本控制。

## 5. 审计与人类复核要求

Sidecar 产出的 figures 与说明文案必须至少能追溯这几层内容：为什么进入 sidecar、冻结输入是什么、handoff 里交了什么、导入后的 artifact 在哪里。人类复核时，优先检查 `recommendation.json`、`input_contract.json`、`sidecar_state.json`、`handoff/sidecar_manifest.json`，以及导入后的 `artifacts/<domain>/<provider>/<instance-id>/`。只有当这些环节都闭合时，sidecar 才是可接受的 bounded route；否则它只是未审计的旁路。

## 参考链接

- [`guides/agent_runtime_interface.md`](./agent_runtime_interface.md)：Agent Runtime Interface 提供整个运行层的入口路径。
