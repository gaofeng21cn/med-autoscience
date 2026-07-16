# Progress-First Quality Loop

Owner: `MedAutoScience`
Purpose: `progress_first_review_repair_carry_forward_quality_loop`
State: `active_runtime_support`
Machine boundary: 本文是 MAS Progress-first review / repair / carry-forward 的人读政策。机器 truth 继续归 `agent/stages/stage_route_contract.yaml`、`contracts/stage_run_kernel_profile.json`、MAS owner receipt、typed blocker、human gate、route-back evidence、publication eval、controller decision、OPL current-control / StageRun readback 和真实 workspace artifact。本文不授权手写 study truth、paper body、artifact body、memory body、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 `current_package`。

## 结论

Review / repair 是 Progress-first 的有界质量循环，不是默认安全截停机制。普通路线先产出可接力的 paper / evidence / reviewer / gate delta；review / repair 在当前 work unit 或下一 owner 中定位质量差距、限定修复预算，并把结果折回 `ProgressDeltaReceipt`、`OwnerReceipt`、`TypedBlocker`、`human_gate_ref`、`route_back_ref` 或 `CarryForwardRiskReceipt`。

预算耗尽本身不是 safe terminal stop。预算耗尽只触发 severity-based decision：

- `fatal_blocker`：生成 stable `TypedBlocker`、`human_gate_ref` 或 route redesign / owner redesign；不得 carry forward。
- 非 fatal：生成 `CarryForwardRiskReceipt`，把风险、影响面、下一 owner 和后续修复条件带到下一 route / owner action；不得重复同一 repair loop。

`terminal_stop_loss`、`anti_loop_budget_exhausted` 和 DM002 / DM003 类 stop-loss 是当前过渡状态样本，不是理想终态。目标态必须能给出 successor work-unit、carry-forward receipt、owner receipt、human gate、route-back evidence 或 stable typed blocker，而不是把队列为空、预算耗尽或同义 repair 失败写成默认完成。

## Severity Taxonomy

| severity | 含义 | 预算耗尽后的决策 |
| --- | --- | --- |
| `fatal_blocker` | 当前 delta 会破坏医学 truth、source/data/evidence 可用性、owner-route identity、forbidden write boundary、artifact/package/memory authority、human/safety gate、不可逆 mutation 或 publication/submission claim；继续推进会制造错误权威或不可接受风险。 | 阻断当前 route。必须输出 stable `TypedBlocker`、`human_gate_ref`、route redesign / owner redesign，或明确的 authority repair owner。 |
| `must_fix_before_current_gate` | 当前 gate 要求在本轮 bounded repair loop 内优先修复，否则不能声称当前 gate clean；但缺口尚未达到 fatal，且可以被下一 owner 继续追踪。 | 先用当前 repair 预算处理。预算耗尽时必须复判：若升级为 fatal，按 fatal 处理；否则降为带条件的 `CarryForwardRiskReceipt` 并推进下一 owner，不能无限重跑同一 repair。 |
| `carry_forward_advisory` | 已知质量风险、证据尾项、reviewer concern 或 polish debt；它影响后续修订优先级，但不破坏当前 ordinary progress、owner handoff 或非终局 route admission。 | 生成 `CarryForwardRiskReceipt`，继续下一 route / owner action。 |
| `optional_polish` | 语言、格式、风格、冗余、局部图表润色或低优先级 consistency debt；不影响当前 owner output 的可消费性。 | 可记录为 advisory / backlog refs；默认不需要阻断或专门 repair loop。 |

`must_fix_before_current_gate` 只表示当前 gate 的质量压力，不等于 route-level fatal blocker。只有复判为 `fatal_blocker` 的问题才阻断 Progress-first 推进。非 fatal 缺口可以降低当前 gate 的清洁度声明，但必须通过 carry-forward receipt 让下一 owner 可见，而不是把系统困在同一 review / repair loop。

## Budget Exhausted Decision

当 review / repair 预算耗尽时，MAS owner / reviewer 必须产生一个显式 decision，而不是只写 `budget_exhausted=true`：

1. 读取 current work-unit identity、target surface、source/currentness refs、reviewer/gate refs、已执行 repair refs 和剩余 gap refs。
2. 给每个剩余 gap 标注 severity，必要时把多个 gap 聚合为一个 owner-facing decision。
3. 若任一 gap 是 `fatal_blocker`，输出 stable `TypedBlocker`、`human_gate_ref` 或 route redesign / owner redesign，并说明禁止继续推进的 authority reason。
4. 若剩余 gap 均非 fatal，输出 `CarryForwardRiskReceipt`，关闭本轮 bounded repair loop，并把下一 owner / next required delta 投影出来。
5. read-model / operator surface 必须显示这是 ordinary progress carry-forward，不是 publication-ready、submission-ready、quality-clean 或 paper closure。

当前 repo-native materialization 行为固定如下：非 fatal `mas_progress_first_budget_exhausted_decision` 只有在 `decision=advance_with_carry_forward_risk`、`fatal=false`、`ordinary_progress_may_advance=true` 且包含 `mas_progress_first_carry_forward_risk_receipt` 时，才会物化 successor owner action。该 successor 是 `run_quality_repair_batch` / `publishability_repair_sprint`，source/authority 固定为 `progress_first_budget_exhausted.carry_forward_risk_receipt`，required delta 为 `carry_forward_risk_repair_delta_or_typed_blocker`，并携带 `carry_forward_risk` 与 `forbidden_claims` 进入 `current_work_unit.state`、domain action materializer 和 Progress Portal operator projection。fatal budget exhausted 不得物化 successor；它必须投影为 stable typed blocker，携带 `fatal_budget_exhausted_risk`、currentness basis 和禁止写入边界。

这条 materializer 路径是 repo-native 可执行合同，不等于 live runtime 已消费。声称 live runtime 自动推进真实下一 work unit 时，仍必须读取 fresh OPL current-control / provider attempt / owner receipt / workspace artifact evidence。

Budget exhaustion 的错误路径包括：重复同一 work unit repair、把 queue empty 写成安全截停、把 focused tests / docs clean 写成质量闭环、把 OPL loop-risk signal 写成 MAS medical severity、把非 fatal reviewer concern 升级成默认 provider block，或把 carry-forward receipt 写成 publication readiness。

## Review Scope Currentness

Generation manifest v2 保留完整 root generation ledger，同时用 MAS-owned review scope policy 为 medical、statistical、reference、display、publication 和 exact-byte-package lane 生成确定性成员清单。每个 v2 generation/review member 必须带 MAS owner 分配的稳定 `member_id`；它是 opaque identity，不得从 `ref`、path 或 locator 推导，也不得仅因移动或改名而变化，root inventory 和 review member inventory 内不得重复。`build_review_scopes(...)` 是 workspace/materializer 可调用的 canonical 纯函数；host 不得自选、删减、重写 identity 或解释成员。

medical、statistical、reference、display 和 publication 的 scope identity 只绑定 policy id/version、lane 以及 canonical `member_id`、`role`、`sha256`、`size_bytes`，保留 `ref` 作为 inventory/provenance，但不把 locator 算入专业复审 identity。因此仅 generation id、root governance receipt 重签或内容不变的 locator rename 不会让科学/专业 lane 失效；`member_id`、内容 hash、byte size 或 lane membership 改变仍会准确失效。`exact_byte_package` 继续绑定完整 root inventory，包括 `ref`，所以最终包路径/identity 变化仍必须经过 exact-byte 复核。

Review currentness v2 逐 lane 记录 `fresh` 或 `reused_unchanged_scope`。fresh receipt 必须绑定当前 generation、manifest 和 candidate admissions；reuse 只能在 receipt 自身 scope identity 与当前 MAS scope identity 完全一致时成立，并保留 origin generation、manifest、review request、review receipt 和 origin candidate receipt provenance。每个 lane 的 `current_rubric_ref` 都携带 rubric 内容哈希；fresh 或 reuse receipt 的 rubric 与当前 rubric 不一致时，只使该 lane 失效。scope 或 rubric 改变只让受影响 lane route back；MAS 在一次判定中聚合全部受影响 lane，并通过稳定排序的 `affected_review_lanes` 给出每个 lane 的 reason 和 resume condition，避免 display、publication、exact-byte-package 等依赖同一变化的 lane 被拆成多轮串行复审。`exact_byte_package` 始终覆盖完整 root inventory，不能缩窄。

OPL 只透明物化通用 stage review transport 及 MAS receipt 的 ref/hash/size。OPL 不解释 scope policy、`member_id` 或 `affected_review_lanes`，也不得因 checkout、generation、locator 或 scope digest 不同而拒绝启动 hosted action。host 应把 exact records 注入 MAS handler并持久化返回结果：伪造或损坏的 receipt bytes 由 MAS 返回 `invalid_host_input`，合法旧 receipt 对当前 scope 不再适用时由 MAS 一次返回聚合的 lane-specific route back。这是 quality/currentness 判定，不是 provider 或 hosted-action liveness gate。

## CarryForwardRiskReceipt

`CarryForwardRiskReceipt` 是 refs-only ordinary-progress handoff。它允许 MAS 带着非 fatal 风险继续推进下一 owner；它不关闭 publication/submission readiness，不签 artifact/package authority，不替代 independent reviewer / auditor verdict，也不授权 paper body 或 package body mutation。

最小字段：

| field | required | 含义 |
| --- | --- | --- |
| `receipt_kind` | yes | 固定为 `CarryForwardRiskReceipt`。 |
| `receipt_id` | yes | receipt stable id。 |
| `study_id` | yes | study identity。 |
| `stage_id` | yes | 当前 stage。 |
| `route_id` | yes | 当前 route 或 gate route。 |
| `work_unit_id` | yes | current work unit id。 |
| `work_unit_fingerprint` | yes | current work-unit fingerprint 或等价 currentness identity。 |
| `target_surface_refs` | yes | 受影响 paper / evidence / reviewer / gate / package refs。 |
| `source_currentness_refs` | yes | source、truth、runtime、reviewer 或 gate currentness refs。 |
| `originating_review_refs` | yes | 触发 carry-forward 的 reviewer / auditor / gate / repair refs。 |
| `severity` | yes | `must_fix_before_current_gate`、`carry_forward_advisory` 或 `optional_polish`；不得为 `fatal_blocker`。 |
| `risk_summary` | yes | 面向下一 owner 的短风险说明。 |
| `deferred_gap_refs` | yes | 未在本轮修复的 gap refs。 |
| `why_nonfatal` | yes | 为什么继续推进不会破坏 authority、source/data/evidence、forbidden write、human gate 或不可逆 mutation。 |
| `accepted_forward_boundary` | yes | 允许继续推进的边界，例如 ordinary progress、route-back briefing、reviewer recheck request 或 next owner delta。 |
| `next_owner` | yes | 下一个 owner。 |
| `next_route_or_action` | yes | 下一个 route / owner action。 |
| `next_required_delta` | yes | 下一 owner 必须产出的 delta、receipt、gate replay 或 blocker。 |
| `reentry_condition` | yes | 哪个条件会把风险重新升级为 repair / gate / blocker。 |
| `forbidden_claims` | yes | 至少包含 publication-ready、submission-ready、quality-clean、domain-ready、production-ready 和 artifact/package authority。 |
| `authority_boundary` | yes | MAS 只签医学 severity / carry-forward policy；OPL 只运输、索引和显示 refs。 |
| `evidence_refs` | yes | 支撑本 receipt 的 refs。 |
| `created_at` | yes | 生成时间。 |
| `producer` | yes | MAS owner / reviewer / controller-authorized producer。 |

可选字段包括 `risk_owner`、`deadline_or_target_stage`、`reviewer_recheck_request_ref`、`route_back_candidate_ref`、`human_visibility_required`、`consumer_ack_ref` 和 `supersedes_receipt_refs`。这些字段只帮助下一 owner 消费风险，不改变 authority boundary。

## Authority Boundary

MAS 持有医学 severity policy、reviewer / auditor quality verdict、owner receipt、typed blocker、carry-forward acceptance、artifact/package authority 和 publication/submission gate。OPL Agent Lab 或 OPL runtime 持有通用 loop-risk evaluator、attempt ledger、queue / retry / dead-letter、StageRun transport、provider liveness、refs-only receipt transport 和 App/operator projection。

因此：

- OPL 可以检测同一 identity 重复、budget exhausted、same-tick max passes、stale running projection、duplicate dispatch、missing closeout binding 或 generic loop risk。
- OPL 不能把 generic loop-risk verdict 写成 MAS medical severity、quality verdict、publication readiness、submission readiness、artifact authority、owner receipt 或 stable typed blocker。
- MAS 必须把 OPL loop-risk signal 消费为 severity decision：fatal 才阻断；非 fatal 必须 carry forward 或交给下一 owner。
- `CarryForwardRiskReceipt` 只能由 MAS owner / reviewer / controller-authorized policy surface 产生或接受；OPL 只能保存 ref、显示 ref、调度下一 owner，不能改写 severity。

## Ordinary Progress vs Readiness

普通 progress 的验收对象是可接力 delta：paper / evidence / reviewer / gate delta、next owner handoff、route-back evidence、human gate、stable typed blocker 或 carry-forward risk receipt。它回答“下一 owner 是否能继续推进”。

Publication / submission readiness 的验收对象是终局 authority：MAS owner receipt、independent reviewer / auditor record、publication gate verdict、artifact/package freshness proof、human approval / submission handoff receipt、或 stable blocker。它回答“是否可以声明 ready / handoff / submit”。

`CarryForwardRiskReceipt` 只能证明普通 progress 没有被非 fatal 风险卡死；不能证明 publication-ready、submission-ready、quality-clean、domain-ready、production-ready、artifact mutation authorization 或 `current_package` freshness。
