# Academic Research Skills Learning Intake

Owner: `MedAutoScience`
Purpose: `external_pattern_learning_reference`
State: `active_support`
Machine boundary: 人读学习记录。机器可读投影见 `src/med_autoscience/ars_learning_projection.py`、`product_entry_manifest.ars_learning_projection`、`domain_handler_export.ars_learning_projection` 和 `contracts/opl-framework/family-contract-adoption.json#academic_research_skills_learning_projection`。

Landing boundary: 本 reference 记录 ARS pattern 与 MAS-native projection；它不单独证明 worker / executor / owner callable 已落地。是否可写成 landed，按 [External Learning Adoption Closure Runbook](../../runtime/control/external_learning_adoption_closure.md) 的 landing status 判断；缺 owner surface、read-model consumer、worker/sidecar slot、callable/action catalog 或验证时必须继续标为 gap。

## 来源

- Source: `https://github.com/Imbad0202/academic-research-skills`
- Snapshot: `d564d26da39de039ba71d9b51f43e6a25fe9b149`
- Observed release context: `v3.8.0`

该项目本轮只作为 external pattern source。MAS 不引入它作为 runtime dependency、skill dependency、paper-writing owner、publication gate、citation body store 或 reviewer authority。

## 吸收范围

MAS 只吸收四类模式：

1. `claim_citation_support_audit`
   - 映射为 MAS 的 claim/evidence support projection。
   - 权威输入继续来自 `study_charter`、`evidence_ledger`、`review_ledger` 和 AI reviewer-backed `publication_eval/latest.json`。
   - OPL 只能消费 refs、metadata、freshness、typed blockers 和 owner boundary。

2. `data_access_and_oversight_metadata`
   - 映射为 stage / source readiness / human gate 可读 metadata。
   - 权威输入继续来自 `study_charter`、`evidence_ledger`、`review_ledger`、`progress_projection` 和 `domain_health_diagnostic`。
   - 该 metadata 不授予 OPL raw data access、source body access 或 write permission。

3. `evidence_handoff_passport`
   - 映射为 body-free evidence handoff ref pack。
   - MAS 使用 `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt`、`controller_decisions/latest.json` 和 `domain_health_diagnostic` 表达 handoff / closeout / receipt。
   - ARS passport 不成为 MAS truth，也不导出 passport body。

4. `medical_material_passport_source_handoff`
   - 映射为 MAS-native `medical_material_passport` refs-only projection 与 source adapter rejection-log contract。
   - passport 只携带 `source_readiness_refs`、`claim_evidence_refs`、`review_contract_refs`、`artifact_rebuild_refs`、`human_decision_refs` 和 `owner_receipt_refs`。
   - source adapter 只能产出 records 与 `rejection_log`；entry-level reject 进入 log 后继续，adapter-level failure 必须 loud fail，不写 MAS truth。

## OPL 边界

OPL 对应的上收目标是通用 `family-stage-integrity-metadata.v1` primitive：stage-level integrity、citation-support、evidence-handoff、data-access 和 human-checkpoint metadata。这个 primitive 应归 OPL Framework；MAS 只发布医学研究 domain projection / thin adapter。

OPL 可以：

- index refs
- display missing support
- carry typed blockers
- route human checkpoints
- transport handoff receipts

OPL 不可以：

- 写 `publication_eval/latest.json`
- 写 `controller_decisions/latest.json`
- 写 evidence / review ledger body
- 读取或迁移 MAS memory body
- 生成 publication quality verdict
- 授权 submission readiness
- 修改 manuscript / package / artifact body
- 替代 MAS direct app skill path

## 当前落点

- `build_ars_learning_projection()` 生成 MAS-owned projection。
- `build_medical_material_passport()` 生成 refs-only source/workspace evidence handoff projection；`build_source_adapter_output()` 固定 records + rejection-log 输出边界。
- Product-entry manifest 暴露 `ars_learning_projection`。
- Family stage control-plane descriptor 内嵌同一 projection，供 OPL stage discovery 读取。
- Sidecar export 暴露同一 projection，供 OPL provider/workbench 读取。
- `family-contract-adoption.json` 固定 source snapshot、absorbed pattern ids、source adapter rejection-log contract、allowed export、forbidden export 和 authority boundary。

该状态表示模式吸收和边界投影已经落地；它不表示 claim-support audit 的所有医学执行路径已经完成，也不表示 OPL 已拥有 domain truth。
