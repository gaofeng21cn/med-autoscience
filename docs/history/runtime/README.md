# Runtime 历史归档

Status: `history archive`
Owner: `MedAutoScience documentation`
Purpose: `runtime_history_index`
State: `history_index`
Machine boundary: 人读 runtime 历史索引。当前 runtime truth 继续归 `docs/runtime/`、contracts、source、CLI/API payload、sidecar receipts、OPL current-control-state / StageAttempt refs、MAS runtime/controller durable surfaces 和 owner receipts。

本目录保存运行时 implementation plan、legacy boundary 记录和不再拥有当前运行行为的 provenance。

Superseded read rule：历史 runtime 文档里的旧 producer/gate/transport queue/attempt/current-work-unit 语言只保留 provenance。当前 route/transition 边界只读 [Stage / Route / Handoff](../../runtime/stage_route_handoff_standard.md)、Stage manifest 与 OPL controller receipt。

当前运行时真相从 [runtime 文档入口](../../runtime/README.md) 开始：

- `docs/runtime/contracts/`：稳定合同与 owner boundary。
- `docs/runtime/control/`：controller、supervision、orchestration 与 runtime action surface。
- `docs/runtime/projections/`：读模型和用户可见投影。
- `docs/product/`：OPL hosted workbench / App shell 消费 MAS refs-only projection 的产品边界。
- `docs/runtime/designs/`：尚未提升为稳定合同的活跃设计。

| file | historical role | current owner surface |
| --- | --- | --- |
| [historical framework positioning](historical_framework_positioning.md) | `Domain Gateway` / `Domain Harness OS` 时代的 runtime/framework positioning 草案。 | [status](../../status.md)、[architecture](../../architecture.md)、[MAS ideal-state gap plan](../../active/mas-ideal-state-gap-plan.md) 与 [runtime boundary](../../runtime/contracts/runtime_boundary.md)。 |
| [OPL unique control plane boundary contract](opl_unique_control_plane_boundary_contract.md) | retired MAS CLI surface / OPL current-control-state handoff tombstone。 | OPL current-control-state / provider attempt ledger 与 MAS owner receipt / typed blocker refs。 |

其余逐项 runtime tombstone、migration inventory 与 implementation plan 已从 tracked
tree 退役；精确历史读取 Git history，当前 owner 读取本页列出的 contract/control/projection。

## Tombstone / Provenance Index

以下索引是退役残留的唯一维护入口；不要再新增逐项 closeout 文档来重复这些口径。

| retired surface family | tombstone owner | current read rule |
| --- | --- | --- |
| old domain-health diagnostic / owner-route / domain-owner dispatch / default-executor / Progress Portal control-plane wording | `contracts/runtime/legacy-active-path-tombstones.json` | 只能作为 diagnostics、migration input、history provenance、consume/readback evidence 或 no-resurrection guard；不得恢复为 PaperMission 默认主线、runtime readiness、paper progress、owner receipt、typed blocker 或 publication-ready 证据。 |
| legacy next-action surfaces: PaperRecovery, `current_executable_owner_action`, domain transition, provider admission, OPL queue / attempt, current-work-unit / current-execution-envelope selectors | [Stage / Route / Handoff](../../runtime/stage_route_handoff_standard.md) and `contracts/runtime/legacy-active-path-tombstones.json` | 只能作为 provenance、diagnostic、migration input、receipt/readback evidence 或 no-resurrection guard；当前 route 必须来自 declared Stage、decisive Attempt、OPL transition receipt 与 MAS owner consumption，缺当前 owner result 时 fail closed。 |
| MAS private runtime substrate, local carrier persistence, owner-callable/default-executor carriers, runtime health/workbench/capability projections, runtime lifecycle/storage maintenance | Git history、[status](../../status.md) 与 [MAS ideal-state gap plan](../../active/mas-ideal-state-gap-plan.md) | repo-source retirement 与 live-runtime readiness 分账读取；旧 module / CLI alias / wrapper / compat shim 不再作为 active public surface。允许残留只限 OPL-authorized adapter、MAS minimal authority adapter、body-free projection、tombstone/provenance 或 no-resurrection guard。 |
| legacy public helper retirements such as `progress-projection`, `legacy-control-surface-clean-migration`, `legacy-ds-retire`, and runtime supervisor test helper shims | this index plus theme-level [program history index](../program/README.md) | 只保留退役事实和当前 owner surface 指向；不要维护多份 dated active-looking closeout。需要当前命令或测试入口时读取 active docs、parser/source、workspace renderer 和 focused tests。 |

Runtime 历史只保留 provenance。它可以解释当前合同为什么这样设计，但不能重开旧 MDS daemon、WebUI、workspace-local service 或已退役 scheduler 路径。活跃 runtime 变更必须先更新当前 contract / control / projection / display 层。
