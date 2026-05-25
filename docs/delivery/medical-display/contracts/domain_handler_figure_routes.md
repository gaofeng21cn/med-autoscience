# Sidecar Bridge 与 Figure Routes 指南

Owner: `MedAutoScience`
Purpose: `Explain the human-readable medical-display contract and audit boundary for MAS delivery work.`
State: `active_support`
Machine boundary: Human-readable delivery contract support only; enforceable truth remains in source, tests, machine-readable contracts, generated artifacts, and audit receipts.

> 这个指南可以从 [`../../../runtime/contracts/agent_runtime_interface.md`](../../../runtime/contracts/agent_runtime_interface.md) 中的“domain-handler provider 与 figure routes 指南”入口访问，是对运行层中 domain-handler / figure route 边界的稳定说明。

## 1. Sidecar bridge 在 MedAutoScience 的定位

1. **主线 runtime 控制面默认归 OPL；MAS 保留 artifact/quality/domain authority surfaces。** Sidecar bridge 只是让 OPL provider-backed family runtime 进入 MAS owner surface 的受控入口，不能取代 MAS artifact/quality/domain owner chain 处理模型训练、评估或结果收敛授权。外部 `MedDeepScientist` 只可作为显式 backend audit、historical fixture / explicit archive import reference 或 parity oracle reference，不是默认执行前置。
2. **Sidecar 不是随意“绕过主线”的后门。** 任何 domain-handler 调用都应报告其 trigger、task ref、owner route 与 dispatch receipt，这样人类审阅者可以追溯为什么进入 domain-handler bridge 以及它的输出对主线决策有哪些影响。

## 2. Sidecar bridge 契约

Sidecar 运行必须遵守下列核心契约条款：

- **统一 bridge 入口。** MAS 仓内活跃 domain-handler 入口是 `domain-handler export` / `domain-handler dispatch`。Generic provider recommendation / provisioning / import lifecycle 已迁出 MAS 活跃面，不再由 `recommend-domain-handler`、`provision-domain-handler`、`import-domain-handler` 或 provider registry 承担。
- **OPL owns transport.** OPL provider 可以承载 stage attempt、queue/wakeup、retry/dead-letter、human-gate signal、attempt receipt 和 projection；MAS 只接受 allowlisted task refs 并返回 owner receipt、typed blocker 或 refs-only dispatch receipt。
- **Domain authority preserved.** Sidecar bridge 不得写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal/`、`manuscript/current_package/`、source body、memory body 或 artifact body。
- **Refs and receipts only.** Sidecar bridge 的输入输出必须是 task refs、source refs、artifact refs、receipt refs 或 typed blockers；如果需要外部 research/analysis progression，先由 publication aftercare 或 OPL provider 形成 owner-route task，再经 MAS owner chain 处理。

## 3. Figure illustration 的平台边界

1. **说明性图统一走程序化绘图。** 当前平台只保留 `figure_illustration_program:<figure-id>` 这一路由来处理 `method_overview`、`study_workflow`、`graphical_abstract`、`cohort_schema` 等说明性图。它们可以承担“方法说明、研究流程、图形摘要、队列结构示意”等角色，但不能承载核心结果证据。
2. **不再假定外部绘图 domain-handler。** MedAutoScience 不再为说明性图保留独立外部绘图 runtime、provider registry 或 bootstrap 入口。说明性图的质量控制由平台自己的程序化绘图规范、脚本审计面和 manuscript surface 共同承担。
3. **禁止范围。** 程序化说明性图不得进入 `metric_number_editing`、`claim_change`、`result_plot_generation` 三类 scope。也就是说，严禁用说明性图路线修改任何数值证据、结果图（如 ROC、KM、校准、DCA、forest、SHAP、亚组统计图）、claim 文字或结论性结果标注。
4. **结果图必须保留原始 artifact。** 如果结果图需要修正，应通过 MAS-owned artifact/quality route 输出新的 artifact，然后在 audit surface 中写明差异、原因、责任人；必要时可显式调用 legacy MDS oracle 做对照，但不能把外部 MDS 恢复成默认图件生成依赖，更不能借助说明性图路线偷换 claim 数据。
5. **renderer family 也是正式 contract。** 路由只回答“这是证据图修复还是说明性图绘制”；真正的渲染技术栈还必须在 `paper/figure_semantics_manifest.json` 里锁定。允许矩阵是：`evidence -> python | r_ggplot2`，`illustration -> python | r_ggplot2 | html_svg`。其中 `html_svg` 永远不能用于证据型图。
6. **严禁 failure-driven renderer switch。** 不允许因为环境缺包、依赖损坏、R/Python 运行失败、浏览器导出失败等原因，从一个 renderer family 偷偷切到另一个 family。正确动作只有阻断并修环境，即 `fallback_on_failure=false` 且 `failure_action=block_and_fix_environment`。

## 4. Figure routes：两类显式路由

- **figure_script_fix:<figure-id>** 适用于 MAS 主线已经定义好的 figure artifact，但当前图的脚本、模板、导出层或排版层存在问题，需要在冻结数据与冻结脚本边界内重新生成。它服务的是“证据型图修复”，不是“插图美化”，因此应保留结果图与其脚本的直接对应关系。
- **figure_illustration_program:<figure-id>** 适用于说明性图，由独立程序绘图路线生成 manuscript-safe 的方法图、流程图、schema 图。它同样不能承载结果证据，也不依赖任何外部绘图 runtime。
- **适用边界对照。** 如果要改动的图是直接支撑 claim/结果的 artifact，应走 `figure_script_fix` 由 MAS artifact route 产生，并把 renderer family 锁定为 `python` 或 `r_ggplot2`；如果图只是说明性图，则走 `figure_illustration_program`，renderer family 可为 `python`、`r_ggplot2` 或 `html_svg`。旧的 `figure_illustration_domain-handler` 和任何外部绘图 domain-handler 路由都属于已废弃歧义入口，不应再使用。

## 5. 审计与人类复核要求

Sidecar 产出的 figures 与说明文案必须至少能追溯这几层内容：为什么进入 domain-handler、冻结输入是什么、handoff 里交了什么、导入后的 artifact 在哪里。人类复核时，优先检查 `recommendation.json`、`input_contract.json`、`domain_handler_state.json`、`handoff/domain_handler_manifest.json`，以及导入后的 `artifacts/<domain>/<provider>/<instance-id>/`。只有当这些环节都闭合时，domain-handler 才是可接受的 bounded route；否则它只是未审计的旁路。

另外，论文面向的 figure/caption 不得混入工具广告、服务链接、`Sources:`、`Why this matters` 这类海报化标注。此类文案应在 manuscript-facing surface 上被直接阻断，而不是靠人工事后删改。

## 参考链接

- [`../../../runtime/contracts/agent_runtime_interface.md`](../../../runtime/contracts/agent_runtime_interface.md)：Agent Runtime Interface 提供整个运行层的入口路径。
