# MAS Adoption of OPL Family Contracts

## Purpose

这份薄适配声明说明 `MAS` 如何满足 `OPL` family runtime / quality / incident / operator projection 合同。它不把 `OPL` 变成医学研究 owner，也不把 family 合同复制成第二套 MAS runtime。

## Runtime Attempt Projection

`MAS` 通过以下 domain-owned surface 映射 `opl_family_runtime_attempt_contract.v1`：

- `progress_projection`
- `domain_health_diagnostic`
- `controller_decisions/latest.json`

这些 surface 可以向 `OPL` 投影 attempt state、attempt count、retry/backoff、workspace boundary、failure reason、reconciliation status 和 last observed projection。2026-05-16 起，MAS adoption contract 还接受 `opl_family_runtime_attempt_contract.v1` 的 stability projection 字段：`control_loop_summary`、`usage_projection`、`resource_pressure` 和 `observability_export`。这些字段只能作为 read-only operator stability projection；它们不能执行 domain action、切换 executor、自动降级、写 study truth / memory body、授权 domain ready 或关闭 quality verdict。`OPL Runtime Manager` 只能读取和索引；study runtime truth、controller decision、workspace write authority 继续由 `MAS` 持有。

`quest_waiting_opl_runtime_owner_route` 是 refs-only handoff，不是 MAS runtime state mutation。MAS 只把 handoff 写入 `artifacts/supervision/owner_route_handoff/latest.json`，并由 `sidecar export` 投影为 `domain_route/reconcile-apply` pending family task；`.ds/runtime_state.json`、`.ds/events.jsonl`、active run liveness、provider worker 状态、queue retry/dead-letter 均归 OPL runtime manager / provider。

## Quality Projection

`MAS` 通过以下医学质量 surface 映射 `opl_family_domain_quality_projection_contract.v1`：

- `study_charter`
- `evidence_ledger`
- `review_ledger`
- AI reviewer-backed `publication_eval/latest.json`

`publication_eval/latest.json` 是医学论文质量投影的关键出口，但只有 AI reviewer-backed 记录可以关闭 reviewer-first ready / finalize-ready 判断。`claim-only ready`、generic persona QA、non-medical QA gate、OPL projection-only 状态都不能成为 MAS medical paper quality authority。

OPL 托管 stage attempt 时也必须保持 executor/reviewer 分离：执行 agent 只产生 stage work、execution receipt 和 artifact/source refs；reviewer/auditor agent 必须以独立 invocation 读取这些 refs，使用独立 context/task record 生成 AI reviewer / audit receipt。把同一 executor 的“执行后自评”包装成 reviewer record 不能关闭 MAS quality projection。

## Incident Projection

`MAS` 通过 `domain_health_diagnostic`、`artifacts/autonomy/slo_status/latest.json`、`artifacts/autonomy/ai_doctor_requests/*.json`、`artifacts/autonomy/ai_doctor_diagnoses/*.json`、`artifacts/autonomy/repair_actions/*.json`、autonomy incident records 和 `controller_decisions/latest.json` 映射 `opl_family_incident_learning_loop.v1`。真实 incident 必须回流成 guard、test、contract、runbook、taxonomy update 或 operator projection；domain-specific failure 必须有 MAS-owned closure ref。`OPL` 可以消费 runtime_slo_observer、ai_doctor_request 与 repair_action 投影，但不持有 MAS 医学 truth 或 repair closure。

## Product Operator Projection

`MAS` 通过 `product-entry-status`、`workspace-cockpit`、`study-progress` 与 `build-product-entry.return_surface_contract` 映射 `opl_family_product_operator_projection.v1`。这些投影必须保留 source refs、freshness、owner split、next surface ref、human gate reason、autonomy_slo、ai_doctor_state、repair_recommendation，以及 OPL 新增的 `control_loop_summary`、`usage_projection`、`resource_pressure` 和 `observability_export` 字段。

`opl runtime observability-export` 是 OPL-owned read-only export surface，MAS 只消费 source refs、freshness、owner split、domain-owned projection refs、owner receipt refs 和 typed blocker refs。它不能被 MAS 解释成 domain action authorization、executor switch authorization、auto-degrade authorization、domain truth write、memory body write、publication quality verdict 或 paper/artifact closure。

## Domain Memory Descriptor

`MAS` 通过 product-entry manifest 的 `domain_memory_descriptor` 暴露 `publication_route_memory` 的 OPL family locator。这个 descriptor 指向 MAS-owned policy、Markdown canonical body ref、seed index、workspace memory locator、`stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt` 和 `stage_recall_index`。

2026-05-12 fresh OPL read model 已解析 `mas_publication_route_memory`，并把 MAS 的 `migration_readiness.status` 读为 `workspace_apply_closure_ready`。这说明 MAS 侧 Markdown canonical library、seed index、workspace apply、workspace memory pack locator、stage entry refs、typed closeout writeback 和 writeback receipt locator 已能作为 domain-owned memory surface 被 OPL 发现。

`OPL` 可以读取、索引、投影和携带这个 locator 进入 stage attempt；MAS 继续持有 route-memory 正文、retrieval、writeback accept/reject、publication route decision、evidence/review/controller truth、publication gate 和 artifact/package authority。维护者查看当前 workspace memory inventory 时使用 `medautosci publication route-memory-inventory --workspace-root <workspace>`，默认输出 body-free，适合 OPL/Aion ref-only grouping；正文审查必须显式请求 body 并留在 MAS owner 语境。

当前 OPL family-runtime 的 production required provider 是 `temporal`；fresh read model 已把默认 provider 选到 Temporal，并证明 managed service / worker residency 可用。`local_sqlite` 只在显式选择时作为 dev/CI/offline diagnostic baseline，不能替代 production provider、domain daemon replacement 或 paper-line readiness。MAS domain memory 可以被 OPL 以 body-free locator / refs 投影和索引，但真实 memory body、writeback accept/reject、paper-line live apply、human gate/resume 和 publication authority 继续由 MAS owner surfaces 持有。

## Monolith And Companion Retirement Projection

`MAS` 已完成 no-history physical absorb 与 default-runtime-retirement closeout。OPL family contract adoption 读取的是 MAS-owned projections 和 retained capability surfaces，不要求外部 `med-deepscientist` checkout 作为默认运行依赖。

MDS / DeepScientist 相关引用只能作为以下显式 refs 暴露：

- backend audit target
- legacy restore/import diagnostic
- upstream intake source
- parity oracle fixture

任何未来继续吸收 MDS / DeepScientist 能力的 lane 都必须先记录 source ref/hash、snapshot checksum、license refs、capability classification、MAS owner、authority boundary、tests、parity proof 与 no-history contributor audit。

## Boundaries

- `OPL` 只消费 MAS projection，不持有 study truth。
- `OPL` 不关闭 `publication_eval/latest.json`。
- `OPL` 不拥有 `publication_route_memory` 正文，也不接受或拒绝 memory writeback。
- `OPL` 不替代 evidence ledger、review ledger 或 medical reviewer judgment。
- `Hermes-Agent`、Symphony scheduler、Linear 或外部 issue tracker 都不是 MAS 必需入口。
- 外部 `med-deepscientist` checkout 也不是 MAS 默认 operation 依赖；只保留 MAS 显式声明的 diagnostic / intake / oracle refs。
