# Workspace Autoscience Rules

Owner: `MedAutoScience`
Purpose: `Define stable MAS study workflow, workspace, source, and submission operating policy.`
State: `active_policy`
Machine boundary: Human-readable study-workflow policy only; study truth remains in workspace artifacts, source contracts, runtime/controller outputs, generated artifacts, and owner receipts.

这份规则用于描述 `MedAutoScience` 在具体医学 workspace 中的默认运行原则。

它是 workspace 侧摘要，平台级的总操作模型见：

- [platform_operating_model.md](../runtime-governance/platform_operating_model.md)

## 默认目标

- 以 Q2+ 医学论文为第一目标
- MAS 做医学研究 domain owner
- Codex CLI 做 stage 内默认 concrete executor
- OPL 可以作为外层 stage-led runtime framework 承担唤醒、队列、恢复、审批和投影
- ToolUniverse 只在功能分析 / 知识检索需要时挂接
- MedDeepScientist / DeepScientist 只作为历史来源、显式归档导入、backend audit、upstream intake 或 parity oracle，不作为默认运行或诊断依赖
- workspace literature、data asset registry、ToolUniverse 输出和 workspace memory 只能作为 stage context、evidence input、diagnostic 或 route-back 线索；source readiness、publication quality、submission readiness、artifact mutation、`current_package` 更新和 controller decision 仍必须回到 MAS owner surface、AI-first gate、owner receipt 或 typed blocker。

## 默认约束

- 优先选择高可塑性、可继续优化证据面的研究路线
- 在弱结果方向上尽快止损，而不是默认把流程跑完
- 数据、门控、交付等状态更新优先通过平台 controller 完成
- 人类主要看 summary、report、draft、final delivery，不手工维护底层 registry
- OPL provider / App / projection 可以显示 refs、freshness、attempt 和 blocker，但不能把 provider completion、file presence、package freshness、test pass、read model 或 inventory 解释为 MAS paper closure、domain ready、quality verdict 或 artifact authority。

当前这份规则是从 NF-PitNET workspace 中抽出的第一版通用摘要，后续会继续规范化。
