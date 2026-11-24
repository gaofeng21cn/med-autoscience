# AI-First 质量边界、证据审阅与论文自治验收

Owner: `MedAutoScience`
Purpose: `ai_first_quality_evidence_review_and_acceptance_ssot`
State: `active_policy`
Machine boundary: `contracts/stage_quality_cycle_policy.json`、`agent/stages/stage_route_contract.yaml`、independent Review receipts、MAS owner result、workspace artifacts 与 OPL StageRun/readback 持有机器事实。

## AI-First 判断 Owner 与证据边界

医学意义、可发表性、claim restraint、读者理解与视觉叙事由独立 reviewer 判断。程序只验证 identity、Schema、allowed writes、资源完整性、引用及 exact bytes；不能用 regex、固定分数、模板、章节覆盖、schema pass、provider completion 或 UI 状态签发 quality/publication verdict。

- Producer 同线程检查只构成 `in_thread_refinement`。正式 reviewer、repairer 与 re-reviewer 必须使用独立 Attempt/session（输入只有当前 clinical question、设计、数据、方法、产物、rubric 与必要 lineage，不继承 producer conversation）；Framework 校验角色与输入闭包并生成 Review receipt，MAS 消费它作领域判断。
- Meta Review 负责跨 Stage 缺陷归属，不得在 reviewer 会话内顺手改稿，缺陷一律指向最窄 canonical owner（方法/数据回到分析或证据 Stage，表述回到 authoring）。专业要求按研究类型选择（[Study Archetypes](../study-workflow/study_archetypes.md)）；Agent Lab / OMA 消费的机制缺陷与测试通过不构成当前 study verdict，外部 Skill/工具只提供输入而无 MAS authority。
- Review currentness、revision finding consumption 与 generation binding 由 [质量循环](../../runtime/progress_first_quality_loop.md) 持有，初稿质量门槛见 [初稿质量门槛](./medical_manuscript_first_draft_quality.md)。

## 独立审阅校准情境

Reviewer 结合具体证据而非关键词或阈值判断以下常见失效情境（目标期刊与近邻论文仅作体裁与表达参考，不得替代本研究 claim 或覆盖 evidence ledger）：

| 情境 | Reviewer 核对重点 |
| --- | --- |
| 机械完整但缺独立审阅 | 文件、checklist 与 coverage 是否被冒充质量结论 |
| 数据丰富但初稿过薄 | 现有证据是否支持更有意义且未超出 charter 的研究问题 |
| Claim 强于证据 | endpoint、设计、误差与外推边界是否支持实际措辞 |
| Prose 失去医学读者 | Methods 是否可复现、Results 是否直接回答发现、Discussion 是否解释结果 |
| Reviewer input 已变 / 新旧不匹配 | 新分析/claim/source 是否使 review scope stale；generation/manifest/交付字节是否绑定；finding/repair/re-review lineage 是否闭合 |

## 证据链与引用审阅要求

- **最小证据链**：研究 handoff 须定位 study/Stage identity、clinical question 与 claim boundary、输入/变更 artifact、source/evidence/review refs、验收标准、未闭合 finding 与下一 owner（聊天总结、terminal prose、memory 或截图不能单独证明结果）。Charter 声明的 evidence/review expectation 须在 ledger 中留下唯一 closure；阴性或不稳定结果保留失败证据用于降级 claim、调整路线或停止 hypothesis。
- **新分析门槛**：研究资产足以支持更有意义的分析且在 charter 边界内时，须明确分析 owner、hypothesis、endpoint、cohort、数据质量、方法、multiplicity、subgroup、acceptance/failure 条件与样本量/feasibility 理由，不能靠 prose 扩张结论。
- **文献与生命科学数据**：文献记录保留 query、来源层级、identifier、metadata match、claim support、checked time、stale 条件与冲突，区分 metadata-only / abstract-only 与全文阅读，未验证引用不得宣称 publication-ready；life-science 数据保留 entity/accession、cohort、tissue、ancestry、version、license、cross-source conflict 与 caveat（外部 API/cache/receipt 不签 source readiness）。

## 论文自治验收（Paper Autonomy Closure）

一次真实 paper-line 验收不要求 MAS 维护第二套 runtime/controller/queue，必须通过读取 StageRun replay、provider long-soak、artifact delta、independent Review receipt、MAS owner acceptance 与 publication/submission readback，以以下之一合法关闭（缺失 evidence 时在 [开放计划](../../active/mas-ideal-state-gap-plan.md) 保持未验证，并说明接收 owner）：

- accepted owner receipt + reviewed artifact semantic delta；
- route-back + exact defect owner / evidence refs；
- stable typed blocker 或 legitimate human gate；
- `completed_with_quality_debt` + consumable artifact + blocked ready claims。

角色、三轮修复预算与终局路由详见 [Stage / Route / Handoff](../../runtime/stage_route_handoff_standard.md)。
