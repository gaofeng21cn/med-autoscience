# Runtime 文档生命周期

Status: `active runtime docs index`
Owner: `MedAutoScience`
Purpose: `runtime_docs_index`
State: `active_support`
Machine boundary: 本目录是 MAS domain runtime-facing 文档索引。机器真相继续归 contracts、schema、CLI/MCP/API payload、product-entry manifest、owner receipt、runtime/controller durable surfaces 和真实 workspace artifact。

`docs/runtime/` 按生命周期角色组织。

当前口径：MAS runtime docs 只定义医学研究 domain agent 的 domain-authority refs surfaces、controller truth、typed blocker、owner receipt、artifact locator 和 projection/display contract。通用 stage attempt、provider workflow、queue、wakeup、retry/dead-letter、resume、human gate transport、attempt ledger、generic state-machine runner、generic memory/artifact/workbench primitive 与跨 domain projection 属于 OPL Framework / shared family layer。MAS direct/local 诊断只能读取 MAS domain truth、owner receipt、typed blocker 和 projection，不能启动或替代 hosted autonomy。

Hypothesis portfolio / evidence pack 进入 runtime 读面时，只能表现为 MAS owner refs、advisory ranking/proximity projection、missing ref family、typed blocker、reviewer/human gate refs 或 owner receipt refs。OPL runtime 可以调度探索 stage、运输 refs、投影候选排序和显示证据包完整性；不能把 Elo、ranking、proximity、queue completion、attempt ledger 或 workbench 可见性升级成 source readiness、quality verdict、publication gate closeout、artifact authority 或 human/expert approval。

历史 MAS-local scheduler、Hermes/MDS、runtime lifecycle/SQLite、workspace-local wrapper 与旧 alias 仅作为 [history/runtime](../history/runtime/) provenance、explicit archive/import reference 或 parity oracle 读取；当前默认面是 OPL/Temporal hosted runtime + MAS domain authority refs、owner receipts、typed blockers 和 minimal authority functions。

| 目录 | 角色 |
| --- | --- |
| [contracts](./contracts/) | MAS runtime-facing contracts、owner boundary、durable surface、artifact authority 和 backend/interface 规则。 |
| [control](./control/) | MAS controller、domain transition control、owner route、safe action 和 runtime action surface。通用 provider/queue/attempt 归 OPL。 |
| [projections](./projections/) | Read model、用户可见状态、observability 和非权威摘要。 |
| [display](./display/) | Progress Portal 等 active 展示合同。 |
| [designs](./designs/) | 活跃 / 已落地 runtime design support。它们解释目标边界、已落地支撑和剩余设计判断，但不替代 source、contracts、tests、CLI/read-model 或 runtime receipts。 |

## 主入口

- [Runtime boundary](./contracts/runtime_boundary.md)
- [Agent runtime interface](./contracts/agent_runtime_interface.md)
- [Runtime handle and durable surface contract](./contracts/runtime_handle_and_durable_surface_contract.md)
- [MAS Stage / Route / Handoff 标准](./stage_route_handoff_standard.md)：解释 stage、route、handoff、owner route 与 OPL stage graph 的关系；route 不是 MAS 私有小 stage，route 间调度归 OPL runtime manager / transition runner。
- [Study runtime control surface](./control/study_runtime_control_surface.md)
- [Study runtime orchestration](./control/study_runtime_orchestration.md)
- [Domain Authority Refs Index Guard](./domain_authority_refs_index_guard.md)：domain authority refs、owner receipt、typed blocker、restore/archive provenance refs 和 SQLite/file boundary guard。
- [Study progress projection](./projections/study_progress_projection.md)
- [Progress Portal](./display/progress_portal.md)

`designs/` 下的文档可以记录已经落地的 runtime support 设计，例如 journal requirements / journal package controller 边界；当前实现和 readiness 判断仍以对应 source、contracts、tests 和 CLI/read-model 为准。

## 历史

已完成 runtime implementation plans、旧 outer-loop 设计说明、runtime supervision loop tombstone 和 private implementation migration inventories 归档到 [history/runtime](../history/runtime/)。这些材料只作 provenance，不是 active backlog，也不能用来重开旧 MDS daemon、WebUI、retired default-provider path、workspace-local service path 或 MAS-owned generic runtime/platform work。

## 规则

Contracts/control docs 可以描述 authority。Projection/display docs 只能描述既有 truth 如何被读取或展示。新增 runtime docs 必须进入上方子目录之一，并写明 owner、purpose、state 和 machine boundary。

如果 runtime 文档需要 generic scheduling、queue、attempt、memory、artifact lifecycle、workbench 或 observability primitive，必须写成 OPL / shared-family owner requirement；MAS 只维护 domain transition spec、owner receipt、typed blocker、quality/artifact authority 和 runtime-facing projection。
