# 项目定位与长期目标

Med Auto Science（MAS）是 OPL 家族中的医学研究 domain agent：canonical agent/package id 为 `mas`，machine domain id 为 `medautoscience`，仓库与 Codex Plugin locator 为 `med-autoscience`。

MAS 将研究问题、数据、分析、证据、稿件和独立审阅组织成可持续推进的研究线。MAS 持有医学 study、quality、publication、artifact、memory 与 owner receipt authority；OPL Framework 持有通用执行、生命周期和生成接口，专业能力由 required dependency `mas-scholar-skills` 提供。

实现形式是 declarative medical research pack、OPL generated/hosted surfaces 与 registry-bound authority functions。组件关系与产品表面见 [架构](./architecture.md)，使用入口见 [README](../README.zh-CN.md)，当前证据边界见 [状态](./status.md)。

## 长期研究目标

Owner: `MedAutoScience` · Purpose: `long_term_research_outcomes` · State: `support_reference`（定义长期研究效果，不声明当前实现或真实论文完成）。

- **从临床问题到可追溯交付**：单人研究者从临床问题与实际数据出发，持续形成可审阅证据、受限 claim、可复现分析、医学稿件与交付物；Agent 自主选择方法与工具并保留来源、判断与失败经验，人类只在缺失关键事实、真实权限、价值判断或不可逆提交边界介入。
- **清晰可接力的研究体验**：研究者可直接看见当前问题、证据变化、质量债、下一 owner 和待决事项；暂停、里程碑交付与停止不会被历史 runtime 或 telemetry 覆盖，论文 trajectory、运行状态与实际用量各自独立可追溯；工作区经验按需检索，不变成 route scorer 或全量 prompt。
- **可验收的结果**：不同 study 类型均可产出医学可读的严谨稿件，负结果、失败假设与修订保留可消费 evidence，独立 Review、artifact currentness、修订消费与 publication authority 在真实论文中成立，Package、executor 与 App 可独立演进且不中断研究 identity。

当前开放外部验收差距统一由 [开放计划](./active/mas-ideal-state-gap-plan.md) 维护。
