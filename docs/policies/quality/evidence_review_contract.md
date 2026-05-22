# Evidence Review Contract

本 policy 固定 `MedAutoScience` 在研究 route 之间推进时必须共享的 evidence / review 合同边界。
canonical source 位于 `agent/stages/stage_route_contract.yaml` 的 `evidence_review_contract`。

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

外部 skill/workflow 材料中的 source-grounded deliverable、reviewer response、data/table 和 Figure/display pattern 只能 clean-room 吸收到 MAS proof package 规则中。它们可以提高 source refs、figure refs、data refs、reviewer concern closure 和 response-action trace 的表达质量，但不能把外部 vendor、runtime、HTML/export UI、citation helper 或 skill source 升格为 evidence authority。nature-skills 相关模式已经通过 `stage_quality_pack_contract`、stage prompt / quality gate refs、product-entry / descriptor refs 和 tests 落到 repo-level 可用面；proof package 的剩余验收是 live paper-line owner receipts、evidence/review ledger refs、AI reviewer-backed `publication_eval/latest.json`、controller decision、artifact delta / gate replay / typed blocker 和 no external authority proof。nature-skills closeout 记录见 [Nature-skills Learning Intake](../../references/mainline/nature_skills_learning_intake.md)。

academic-search / citation 类外部模式只能作为 `stage_quality_pack_contract` 内的质量输入 descriptor 被消费。`literature_search_source_pack` 可以要求 T1/T2/T3 source tier、MeSH / keyword query、multi-source attempt refs、dedup basis、`checked_at` 和 `expires_or_stale_after`；`journal_policy_currentness_pack` 可以要求 official policy refs、policy scope、currentness state、`checked_at` 和 `expires_or_stale_after`；`citation_verification_pack` 可以要求 claim segment、citation ref、identifier refs、source tier、metadata match、support grade、evidence basis、checked_at、expires/stale 和 unverified blocker。以上字段只能产生 source refs、review refs、typed blocker 或 reference-only record。没有 official/current refs、没有 abstract/publisher-page verification、metadata-only、missing、stale 或 manual-needed 状态时，必须 fail closed 到 blocker/ref，不能授权 `publication_readiness`、`quality_verdict` 或 `submission_readiness`。

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

### Medical Quality OS Hard Gate

`medical_quality_operating_system_contract` 现在把 evidence-over-claims 固定为机器合同：任何 `reviewer_first_ready`、`finalize_ready` 或 `submission_facing_quality_closure` 都必须引用 `study_charter.paper_quality_contract`、`paper/evidence_ledger.json`、`paper/review_ledger.json`、AI reviewer-backed `publication_eval/latest.json` 与 `controller_decisions/latest.json`。

quality-preserving fast lane 只允许独立读投影、bounded analysis unit、可重放 repair unit 和 artifact inventory refresh。它必须在之后 replay `publication_gate`、`quality_closure_truth` 与 `study_progress_projection`；禁止 `skip_publication_eval`、`skip_evidence_ledger`、`skip_review_ledger`、`claim_only_ready` 或把 mechanical projection 冒充 AI reviewer。

## Medical Route Quality Loop

`agency-agents` 的 Dev-QA loop、Reality Checker、Experiment Tracker 和 incident/post-mortem 经验，在 `MAS` 中只吸收为医学 route 质量循环；不吸收 generic production-ready 标签、网站截图 QA 默认值、产品 A/B testing 术语或非医学 persona authority。

### Bounded Medical Repair Loop

任何 reviewer、QA、gate-repair 或 route-back 循环，都必须留下 bounded medical repair loop 记录。固定字段如下：

- `attempt_count`
- `verdict`
- `finding_refs`
- `fix_refs`
- `acceptance_criteria`
- `next_route`
- `escalation_ref`

稳定 verdict 只接受 `PASS`、`FAIL`、`NEEDS_REVIEW`。`FAIL` 可以在显式 retry budget 内重试；retry budget 用尽后，必须先写入 `controller_decisions/latest.json` 或 `runtime_escalation_record.json`，再请求 human gate、route redesign 或更大范围重构。不能无限重试，也不能把同一个缺口反复包装成新的 prose blocker。

### Default Needs Review Gate

manuscript、bundle 或 submission readiness 默认是 `NEEDS_REVIEW`，直到 durable evidence refs、review refs 与 AI reviewer-backed `publication_eval/latest.json` 对 active criteria 做出闭环。`zero issues`、`ready`、`production-ready`、`done` 这类表达没有 linked evidence/review refs 与 owner decision surface 时一律无效。

### Phase Gate Handoff

每次 route 或 phase gate handoff 都必须携带：

- preconditions
- input refs
- output refs
- evidence refs
- acceptance criteria
- gate result
- decision owner
- carry-forward risks
- next route

gate result 缺失、过期或只是 claim-only 时，不能推进到 write、finalize、submission-facing package 或下一条 route。

### Analysis-campaign Statistical Discipline

analysis-campaign 不是泛化“再分析一下”。进入新分析前，必须写清 active hypothesis、endpoint、cohort/data quality constraints、statistical method、subgroup or multiplicity guardrails、acceptance/failure criteria。若 study design 或数据集特征使正式 power calculation 不成立，也要显式给出 sample-size、power、precision 或 feasibility rationale，避免用产品 A/B testing、growth metric 或 generic experiment success label 替代医学证据判断。

### Incident Postmortem Feedback Loop

重复出现的 runtime recovery、publication gate、stale package、evidence-review failure 必须产生 incident-style record，至少包含 timeline、impact、root cause、prevention action、owner 与 follow-up status。incident learning 可以更新 runbook、telemetry、failure taxonomy 或 controller specificity；不能放松 evidence gate、publication gate 或 AI reviewer requirement。

platform incident learning loop 现在显式覆盖 `no_live`、`stalled`、`status_drift`、`wrong_milestone_claim`、`quality_reopen`、`publication_gate_failure`、`runtime_recovery_failure` 与 `surface_ownership_drift`。每个 incident 只能落到 `guard`、`test`、`contract`、`runbook`、`runtime_taxonomy` 或 `strangler_rule`，禁止 prose-only note，也禁止把 incident learning 用作 gate relaxation。

## 维护规则

- evidence / review 合同统一维护在 canonical YAML，不在单个 route prose 里重复定义另一套规则。
- 变更 evidence / review 合同属于 contract surface 变更，至少补跑 `tests/test_stage_route_assets.py` 与 `make test-meta`。
- 任何新写作、finalize、review、submission readiness 规则，都应先回答它属于 `minimum_proof_package`、`reviewer_first_checks`、`claim_evidence_consistency_requirements`、`route_back_policy` 中的哪一类。
