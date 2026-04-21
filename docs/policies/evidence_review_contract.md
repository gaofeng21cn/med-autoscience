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

## 维护规则

- evidence / review 合同统一维护在 canonical YAML，不在单个 route prose 里重复定义另一套规则。
- 变更 evidence / review 合同属于 contract surface 变更，至少补跑 `tests/test_agent_entry_assets.py` 与 `make test-meta`。
- 任何新写作、finalize、review、submission readiness 规则，都应先回答它属于 `minimum_proof_package`、`reviewer_first_checks`、`claim_evidence_consistency_requirements`、`route_back_policy` 中的哪一类。
