# AI Reviewer Calibration Corpus

Owner: `MedAutoScience`
Purpose: `reviewer_calibration_cases`
State: `active_policy`
Machine boundary: 本页提供 reviewer 校准情境；当前 Review 身份、scope 和 receipt 合同持有机器事实。

## 校准情境

| 情境 | Reviewer 应判断什么 |
| --- | --- |
| 机械完整但没有独立审阅 | 文件、checklist 和 coverage 是否被冒充质量结论 |
| 数据丰富但初稿过薄 | 现有证据是否支持更有意义且未超出 charter 的研究问题 |
| claim 强于证据 | endpoint、设计、误差和外推边界是否支持实际措辞 |
| prose 失去医学读者 | Methods 是否可复现，Results 是否报告发现，Discussion 是否解释结果 |
| reviewer input 已变 | 新分析、claim 或 source 是否使相关 review scope stale |
| 新 verdict 配旧交付包 | generation、manifest 和 exact delivery bytes 是否仍绑定 |
| 返修反馈没有被消费 | finding、repair 与 re-review lineage 是否闭合 |

这些情境来自历史返工，供 Agent 结合具体证据判断；不能用关键词、模板或评分阈值
自动裁决医学质量。新 case 只有具有独特失败语义才加入，重复例子合并到既有情境。

## 校准材料

目标期刊与近邻论文仅提供体裁、结构和表达参考，不能提供本研究 claim 或覆盖
evidence ledger。Reviewer 需看到当前 clinical question、设计、数据、方法、产物、
rubric 和必要 lineage，而不继承 producer conversation。

真实 study 验证应覆盖正常推进、负结果、route-back、修订恢复和最终交付。
软件回归只证明相应行为；实际论文质量仍由独立 reviewer 和 MAS owner 消费。

权限规则见 [AI-first Boundary](./ai_first_quality_boundary.md)，
currentness 与修订消费见 [Quality Loop](../../runtime/control/progress_first_quality_loop.md)。
