# Runtime 文档生命周期

Status: `active runtime docs index`
Owner: `MedAutoScience`
Purpose: `runtime_docs_index`
State: `active_support`
Machine boundary: 本目录是 MAS domain runtime-facing 文档索引。机器真相继续归 contracts、schema、CLI/MCP/API payload、product-entry manifest、sidecar receipt、runtime/controller durable surfaces 和真实 workspace artifact。

`docs/runtime/` 按生命周期角色组织。

当前口径：MAS runtime docs 只定义医学研究 domain agent 的 runtime-facing owner surfaces、controller truth、typed blocker、owner receipt、artifact locator 和 projection/display contract。通用 stage attempt、provider workflow、queue、wakeup、retry/dead-letter、resume、human gate transport、attempt ledger、generic state-machine runner、generic memory/artifact/workbench primitive 与跨 domain projection 属于 OPL Framework / shared family layer。MAS local scheduler / LaunchAgent 已物理退役为 tombstone/provenance refs，不再作为 active diagnostic bridge、cleanup command 或 generic runtime platform；MAS direct/local 诊断只能读取 MAS domain truth、owner receipt、typed blocker 和 projection，不能启动或替代 hosted autonomy。

私有/历史 runtime 面的当前边界：`runtime_lifecycle.sqlite`、terminal attach / Live Console terminal refs、storage maintenance / artifact storage audit 只能作为 MAS 侧 refs-only adapter 与 provenance surface 保留。它们可以暴露 owner receipt ref、study runtime status ref、terminal/log source ref、storage/artifact locator ref、cleanup receipt ref 或 typed blocker；不能声明 generic runtime owner、generic persistence/lifecycle engine、generic terminal attach runtime、generic cleanup policy、restore-ready verdict 或 paper closure verdict。OPL / shared family layer 持有通用 lifecycle index、provider attempt ledger、terminal transport shell、storage lifecycle policy、queue/retry/dead-letter 和 workbench primitive；MAS 只保留 domain truth、quality/artifact authority、owner receipt 与 blocker 语义。

| 目录 | 角色 |
| --- | --- |
| [contracts](./contracts/) | MAS runtime-facing contracts、owner boundary、durable surface、artifact authority 和 backend/interface 规则。 |
| [control](./control/) | MAS controller、domain supervision、domain transition control、direct/local diagnostic scheduler 与 runtime action surface。通用 provider/queue/attempt 归 OPL。 |
| [projections](./projections/) | Read model、用户可见状态、observability 和非权威摘要。 |
| [display](./display/) | Progress Portal 与 Live Console 的展示合同。 |
| [designs](./designs/) | 尚未稳定成 contract 的活跃设计。 |

## 主入口

- [Runtime boundary](./contracts/runtime_boundary.md)
- [Agent runtime interface](./contracts/agent_runtime_interface.md)
- [Runtime handle and durable surface contract](./contracts/runtime_handle_and_durable_surface_contract.md)
- [MAS Stage / Route / Handoff 标准](./stage_route_handoff_standard.md)：解释 stage、route、handoff、owner route 与 OPL stage graph 的关系；route 不是 MAS 私有小 stage，route 间调度归 OPL runtime manager / transition runner。
- [Runtime supervision loop](./control/runtime_supervision_loop.md)：MAS domain supervision / read-model / owner receipt 入口；不作为 generic scheduler/platform owner。
- [Domain SLO scheduler projection contract](./control/domain_slo_scheduler_projection_contract.md)：MAS domain SLO / owner receipt projection 入口；local scheduler active path 已退役为 tombstone/provenance，OPL-hosted production provider 生命周期归 OPL。
- [Study runtime control surface](./control/study_runtime_control_surface.md)
- [MAS 私有实现与 OPL 迁移台账](./opl_private_implementation_migration_inventory.md)：记录 MAS 私有控制面、runtime/watch/status/CLI/lifecycle/workbench 面向 OPL 标准智能体目标态的当前分类、caller、退役门和验证入口。
- [Study progress projection](./projections/study_progress_projection.md)
- [Progress Portal](./display/progress_portal.md)
- [Live Console UI contract](./display/live_console_ui_contract.md)

## 历史

已完成 runtime implementation plans 和旧 outer-loop 设计说明归档到 [history/runtime](../history/runtime/)。这些材料只作 provenance，不是 active backlog，也不能用来重开旧 MDS daemon、WebUI、retired Hermes default-provider path、workspace-local service path 或 MAS-owned generic runtime/platform work。

## 规则

Contracts/control docs 可以描述 authority。Projection/display docs 只能描述既有 truth 如何被读取或展示。新增 runtime docs 必须进入上方子目录之一，并写明 owner、purpose、state 和 machine boundary。

如果 runtime 文档需要 generic scheduling、queue、attempt、memory、artifact lifecycle、workbench 或 observability primitive，必须写成 OPL / shared-family owner requirement；MAS 只维护 domain transition spec、owner receipt、typed blocker、quality/artifact authority 和 runtime-facing projection。
