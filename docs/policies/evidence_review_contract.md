# Evidence Review Contract

本 policy 固定 `MedAutoScience` 在研究 route 之间推进时必须共享的 evidence / review 合同边界。
canonical source 位于 `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml` 的 `evidence_review_contract`。

## 固定字段

当前 evidence / review 合同至少稳定提供以下字段：

- `minimum_proof_package`
- `reviewer_first_checks`
- `claim_evidence_consistency_requirements`
- `route_back_policy`

字段语义固定如下：

- `minimum_proof_package`：当前 route 至少要留下哪些可读、可引用、可交接的证据包
- `reviewer_first_checks`：在把 draft、bundle 或阶段结果视作可推进之前，必须先施加哪些 reviewer-first 压力
- `claim_evidence_consistency_requirements`：claim、caveat、limitation 与 cited evidence 之间必须满足的最低一致性
- `route_back_policy`：一旦发现缺口，当前 line 应该如何正式 route back，而不是继续把问题包进 prose 或临时结论

## 固定纪律

- 任何 route 推进前，都要能把当前 study charter 边界、route recommendation 和 cited evidence refs 一起读清楚。
- 任何 route 离开前，都要留下下一条 route 能直接接住的 durable artifact、ledger、decision record 或等价引用面。
- 只要 study charter 已经显式声明 evidence expectation 或 review expectation，对应 ledger 就必须留下同名 expectation 的显式 closure 记录；没有记录、不合法状态、重复记录，都属于未闭环。
- reviewer-first 检查必须优先暴露 strongest concern，并把 concern 绑定到具体 claim、evidence gap 或 rigor gap。
- 初稿质量检查必须先判断现有数据资产是否被低估，包括时间点、角色/人群、中心/地理、指南对应、亚组/关联分析和现实采用约束；如果字段已验证且仍在锁定 claim 边界内，应 route back 到 `analysis-campaign`，而不是把过轻的描述性初稿直接推进。
- claim wording、cited evidence、caveat、limitation 必须在同一 proof package 里相互对齐。
- 只要当前 claim 失去直接证据支撑，或 reviewer-first 检查暴露出 material gap，就应立即 route back。

## Charter Expectation Closure

当 `study_charter.paper_quality_contract` 已经声明 `evidence_expectations` 或 `review_expectations` 时，`evidence_ledger` / `review_ledger` 除了保持 shape 合法，还必须显式回答这些 expectation 是否已经闭环。

固定口径如下：

- 每条 expectation 都应在对应 ledger 的 `charter_expectation_closures` 中留下唯一记录。
- 合法 `status` 只接受 `closed`、`open`、`in_progress`、`blocked`。
- `closed` 代表该 expectation 已被 ledger 显式收口。
- `open`、`in_progress`、`blocked`、缺失记录、非法状态、重复记录，全部视为 charter expectation closure blocker。
- medical publication surface 必须把这层 blocker 投影成独立 truth，而不是把它吞进一般 prose blocker。

## Tool Usage 规则

学习 `DeepScientist` 的 tool discipline 后，`MAS` 固定采用以下分工：

- artifact / reports 承担 stage truth、route outcome、handoff 和恢复点。
- evidence / review ledgers 承担 claim、rigor、novelty、clinical relevance 与 reviewer concern closure。
- memory 只记录会改变未来默认行为的 reusable lesson。
- execution logs 只作为第一手执行证据，不承担 paper state、baseline state 或 publication gate authority。

因此，任何 proof package 都不能只靠 memory 或 terminal prose 证明过线；必须回到 evidence / review / publication surface。

## Medical Handoff / Evidence Gate

`agency-agents` 里的 structured handoff / evidence-over-claims / QA feedback loop 在 `MAS` 中只能以医学论文质量合同的形式落地。

### Structured Medical Handoff

任何跨 route、跨 agent、跨前后台的交接，都必须留下 structured medical handoff。固定字段如下：

- `from_route`
- `to_route`
- `study_id`
- `quest_id`
- `active_claim_boundary`
- `changed_artifact_refs`
- `evidence_refs`
- `review_refs`
- `acceptance_criteria`
- `next_owner`
- `human_gate_reason`

这些字段必须描述当前 claim 边界、变更过的 artifact、已经引用的 evidence/review surface、接收方验收标准、下一 owner，以及为什么需要或不需要 human gate。缺少这些字段时，只能视为交接未闭环。

### Evidence Refs Authority

`evidence_refs` / `review_refs` 必须指向 durable MAS truth surfaces，包括：

- `evidence_ledger`
- `review_ledger`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- manuscript/package refs

proof package 不能只靠聊天总结、memory 或 terminal prose，也不能把 screenshot-style QA 当成证据面。聊天、memory、terminal prose 和截图式 QA 只能辅助定位上下文，不能替代 evidence ledger、review ledger、publication eval、controller decision 或 manuscript/package 引用。

### Medical QA Feedback Loop

医学版本的 QA feedback loop 只接受三类状态：

- `PASS`
- `FAIL`
- `NEEDS_REVIEW`

每条 QA 结论都必须绑定具体 claim/evidence/rigor/submission hygiene gap。`PASS` 需要说明对应 claim 和 evidence refs 已闭环；`NEEDS_REVIEW` 需要说明缺少哪类 AI reviewer、作者或 human gate 判断；`FAIL` 必须 route back 到能够关闭缺口的最窄 route，避免把 baseline、analysis、writing、finalize 或 submission hygiene 问题包装成泛化 prose。

### AI Reviewer Gate

只有 AI reviewer-backed `publication_eval/latest.json` 可以驱动 reviewer-first ready、finalize-ready 或 submission-facing quality closure。`publication_gate`、`medical_reporting_audit`、deterministic controller surface 或其他 mechanical projection 只能输出 `review_required` / `projection_only`，并要求 AI reviewer 复评；它们不能把机械完整性投影升格为医学论文质量结论。

### Claim-only Ready Ban

禁止 claim-only ready。generic persona library、non-medical QA gate、NEXUS role approval、截图式 QA、screenshot-style QA、聊天总结、memory 和 terminal prose 都不能被升格为 `MAS` owner authority 或 medical paper quality authority。任何 ready/finalize-ready 表达都必须回到 active claim boundary、durable evidence refs、review refs、AI reviewer-backed publication eval 与 controller decision 的组合证据。

## 维护规则

- evidence / review 合同统一维护在 canonical YAML，不在单个 route prose 里重复定义另一套规则。
- 变更 evidence / review 合同属于 contract surface 变更，至少补跑 `tests/test_agent_entry_assets.py` 与 `make test-meta`。
- 任何新写作、finalize、review、submission readiness 规则，都应先回答它属于 `minimum_proof_package`、`reviewer_first_checks`、`claim_evidence_consistency_requirements`、`route_back_policy` 中的哪一类。
