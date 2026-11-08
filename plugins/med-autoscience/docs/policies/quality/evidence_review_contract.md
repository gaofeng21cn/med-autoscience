# Evidence Review Contract

Owner: `MedAutoScience`
Purpose: `research_evidence_and_claim_review`
State: `active_policy`
Machine boundary: `agent/stages/stage_route_contract.yaml` 的 evidence/review 声明、
canonical evidence、Review receipt 与 owner result 持有机器事实。

## 最小证据链

研究 handoff 必须让接收方定位 study/Stage identity、当前 clinical question 和
claim boundary、输入与变更 artifact、source/evidence/review refs、验收标准、
未闭合 finding 和下一 owner。聊天总结、terminal prose、memory 或截图不能
单独证明研究结果和质量。

Charter 明确声明的 evidence/review expectation 应在相应 ledger 中留下唯一 closure：
closed 必须有证据，open/in_progress/blocked 或缺失记录不能解释成质量闭合。
普通 Stage 仍可带质量债推进，ready claim 必须等 owner acceptance。

## 医学审阅

Reviewer 优先指出最强 concern，将每条 concern 绑定具体 claim、证据、方法或
临床适用性。Claim wording、caveat、limitation 与引用证据需一起审阅。
研究资产足以支持更有意义的分析且仍在 charter 边界时，应明确分析 owner 和
所需 delta，不能靠 prose 扩张研究结论。

新分析需明确 hypothesis、endpoint、cohort、数据质量、方法、multiplicity、
subgroup、acceptance/failure 条件与样本量/precision/feasibility 理由。
阴性或不稳定结果保留失败证据，可以降级 claim、调整路线或停止该 hypothesis；
不以固定 marker 或 publication gate 标签自动决定医学止损。

## Source 与引用

文献记录保留 query、来源层级、identifier、metadata match、claim support、
checked time、stale 条件和冲突。Metadata-only、abstract-only 与阅读全文证据
必须区分；reference 不可验证时保留缺口，不能据此宣称 publication-ready。
来源真实性和具体 claim support 是不同判断。

Life-science 数据保留 entity/accession、cohort、tissue、ancestry、version、
license、cross-source conflict 与 caveat。外部 API、cache 或 provider receipt
提供执行与来源证据，不签 source readiness 或医学 verdict。

## 交接与回溯

证据放在 canonical ledger/artifact，运行日志只作执行来源，可复用经验由 memory
owner 接受。Finding 必须沿输入、修复和 re-review 保持 lineage。
修订触及哪个 source/claim scope，就重新判断对应 Review currentness；
不把全仓重跑或机械 completeness 当作证据更新。

角色、预算与终局路由见 [Stage Standard](../../runtime/stage_route_handoff_standard.md)，
质量权威见 [AI-first Boundary](./ai_first_quality_boundary.md)，
稿件要求见 [First Draft](./medical_manuscript_first_draft_quality.md)。
