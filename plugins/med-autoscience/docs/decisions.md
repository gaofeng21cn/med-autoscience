# 关键决策

Owner: `MedAutoScience`
Purpose: `current_decision_rationale`
State: `active_current_truth`
Machine boundary: 本页解释为什么采用当前边界；实现结构由 architecture 与 contracts 持有。

## 声明式领域包

研究方法、提示词、知识和质量规则由 MAS 维护，通用执行生命周期由 Framework 托管。
这样既保留医学 owner 判断，又避免为每个领域复制 scheduler、状态库和用户界面。
只有必须由领域 owner 作出的程序化裁决保留为 registry-bound authority function。

## Package 与执行载体分离

MAS identity 不依赖 GUI、plugin 或 executor。ScholarSkills 独立持有专业能力包，
MAS 声明 required dependency；平台原生 carrier 负责其实际生命周期。
这一分离允许升级或更换执行载体而不改变研究对象和领域权威。

## 质量判断与运行推进分离

独立 Review 需要独立 Attempt/session 与 exact reviewer input。
同线程自检不能证明独立审阅；运行成功不能证明医学质量。
可消费产物附带质量债继续推进，publication/submission/ready 门仍消费领域验收证据。
详细角色、预算和终局路由由 Stage handoff 合同持有，本文不复制状态表。

## 正文与结构化事实分离

自然语言研究经验使用 Markdown，以便人和 Agent 审阅；identity、状态、Schema、
引用和 receipt 使用结构化面。机器校验资源和 authority 边界，不通过词面或文档
章节判断医学质量。历史流水由 Git 保存，只有独特 provenance 才保留独立归档。

## 验证与运行事实分离

pytest 和 source hygiene 证明当前源码行为与边界；真实研究、provider、App 和发布
结果必须读取对应 runtime、artifact 与 owner receipt。保留这一分离可以清楚表达
尚缺什么证据，避免恢复已经退役的私有控制面来制造 readiness 投影。

实现图见 [架构](./architecture.md)，禁止边界见 [约束](./invariants.md)，
文档处理规则见 [生命周期](./docs_portfolio_consolidation.md)。
