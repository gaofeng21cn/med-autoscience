# MAS Adoption of OPL Family Contracts

Owner: `MedAutoScience`
Purpose: `family_contract_consumer_mapping`
State: `support_reference`
Machine boundary: 本页映射 MAS 消费入口；Framework 合同和真实 consumer 持有平台实现。

## 消费边界

| MAS 声明 | Framework 消费内容 | MAS 保留的 authority |
| --- | --- | --- |
| `contracts/domain_descriptor.json` | Package/domain identity、workspace binding、inventory projection | 论文库存、业务状态、study root |
| `contracts/action_catalog.json` 与 handler registry | Stage interface 与 closed authority dispatch | 医学结果、receipt 与 forbidden-write 判断 |
| `contracts/stage_quality_cycle_policy.json` | Attempt 角色、预算、Review protocol | rubric、finding、领域路由和 quality 判断 |
| `contracts/memory_descriptor.json` | policy/body locator、body-free metadata、receipt refs | memory 正文、accept/reject 与研究策略 |
| `contracts/runtime_detail_contribution_contract.json` | selected-work-item identity 与 activity-log 结果 | 研究 trajectory 与业务状态 |
| `contracts/foundry_agent_series.json` | canonical policy refs、fingerprint 与领域 delta | 医学领域扩展 |

Framework 持有通用 runtime、provider、telemetry、Package aggregation 和 hosted projection；
MAS 不再从私有 progress projection、AI doctor、autonomy incident store 或本地
controller 构造第二套平台真相。

## 验收

结构验证检查 descriptor、Schema、binding 和 forbidden writes。
真实运行需 same-identity StageRun/Attempt、Review、MAS owner result 和 artifact。
历史 Temporal residency、memory migration 或 App projection receipt 不证明当前部署；
必须在实际 consumer 上重新读取。

App 具体输入与渲染要求见 [Runtime Detail](./mas-runtime-detail-contribution.md)，
memory 规则见 [Memory Policy](../../policies/study-workflow/publication_route_memory_policy.md)，
外部来源边界见 [MAS/MDS](../../policies/runtime-governance/mas_mds_owner_boundary_contract.md)。
