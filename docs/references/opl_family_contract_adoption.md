# MAS Adoption of OPL Family Contracts

## Purpose

这份薄适配声明说明 `MAS` 如何满足 `OPL` family runtime / quality / incident / operator projection 合同。它不把 `OPL` 变成医学研究 owner，也不把 family 合同复制成第二套 MAS runtime。

## Runtime Attempt Projection

`MAS` 通过以下 domain-owned surface 映射 `opl_family_runtime_attempt_contract.v1`：

- `study_runtime_status`
- `runtime_watch`
- `controller_decisions/latest.json`

这些 surface 可以向 `OPL` 投影 attempt state、attempt count、retry/backoff、workspace boundary、failure reason、reconciliation status 和 last observed projection。`OPL Runtime Manager` 只能读取和索引；study runtime truth、controller decision、workspace write authority 继续由 `MAS` 持有。

## Quality Projection

`MAS` 通过以下医学质量 surface 映射 `opl_family_domain_quality_projection_contract.v1`：

- `study_charter`
- `evidence_ledger`
- `review_ledger`
- AI reviewer-backed `publication_eval/latest.json`

`publication_eval/latest.json` 是医学论文质量投影的关键出口，但只有 AI reviewer-backed 记录可以关闭 reviewer-first ready / finalize-ready 判断。`claim-only ready`、generic persona QA、non-medical QA gate、OPL projection-only 状态都不能成为 MAS medical paper quality authority。

## Incident Projection

`MAS` 通过 `runtime_watch`、`artifacts/autonomy/slo_status/latest.json`、`artifacts/autonomy/ai_doctor_requests/*.json`、`artifacts/autonomy/ai_doctor_diagnoses/*.json`、`artifacts/autonomy/repair_actions/*.json`、autonomy incident records 和 `controller_decisions/latest.json` 映射 `opl_family_incident_learning_loop.v1`。真实 incident 必须回流成 guard、test、contract、runbook、taxonomy update 或 operator projection；domain-specific failure 必须有 MAS-owned closure ref。`OPL` 可以消费 runtime_slo_observer、ai_doctor_request 与 repair_action 投影，但不持有 MAS 医学 truth 或 repair closure。

## Product Operator Projection

`MAS` 通过 `product-entry-status`、`workspace-cockpit`、`study-progress` 与 `build-product-entry.return_surface_contract` 映射 `opl_family_product_operator_projection.v1`。这些投影必须保留 source refs、freshness、owner split、next surface ref、human gate reason、autonomy_slo、ai_doctor_state 和 repair_recommendation。

## Boundaries

- `OPL` 只消费 MAS projection，不持有 study truth。
- `OPL` 不关闭 `publication_eval/latest.json`。
- `OPL` 不替代 evidence ledger、review ledger 或 medical reviewer judgment。
- `Hermes-Agent`、Symphony scheduler、Linear 或外部 issue tracker 都不是 MAS 必需入口。
