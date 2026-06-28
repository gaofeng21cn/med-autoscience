# Runtime 历史归档

Status: `history archive`
Owner: `MedAutoScience documentation`
Purpose: `runtime_history_index`
State: `history_index`
Machine boundary: 人读 runtime 历史索引。当前 runtime truth 继续归 `docs/runtime/`、contracts、source、CLI/API payload、sidecar receipts、OPL current-control-state / provider attempt refs、MAS runtime/controller durable surfaces 和 owner receipts。

本目录保存运行时 implementation plan、legacy boundary 记录和不再拥有当前运行行为的 provenance。

当前运行时真相从 [runtime 文档入口](../../runtime/README.md) 开始：

- `docs/runtime/contracts/`：稳定合同与 owner boundary。
- `docs/runtime/control/`：controller、supervision、orchestration 与 runtime action surface。
- `docs/runtime/projections/`：读模型和用户可见投影。
- `docs/product/`：OPL hosted workbench / App shell 消费 MAS refs-only projection 的产品边界。
- `docs/runtime/designs/`：尚未提升为稳定合同的活跃设计。

| file | historical role | current owner surface |
| --- | --- | --- |
| [historical framework positioning](historical_framework_positioning.md) | `Domain Gateway` / `Domain Harness OS` 时代的 runtime/framework positioning 草案。 | [status](../../status.md)、[architecture](../../architecture.md)、[MAS ideal-state gap plan](../../active/mas-ideal-state-gap-plan.md) 与 [runtime boundary](../../runtime/contracts/runtime_boundary.md)。 |
| [legacy active path tombstones](legacy_active_path_tombstones.md) | Hermes scheduler、generic hosted-runtime binding 和 workspace-local scheduler 的 tombstone context。 | `contracts/runtime/legacy-active-path-tombstones.json`、OPL/Temporal hosted runtime 与 MAS domain authority refs。 |
| [legacy control surface clean migration public helper retirement](legacy_control_surface_clean_migration_public_helper_retirement_2026_06_07.md) | 旧 legacy control clean migration public CLI / workspace wrapper 退役 closeout。 | Internal controller tombstone/receipt migration implementation；active public runtime helper surfaces。 |
| [legacy runtime boundary](legacy_runtime_boundary.md) | 早期 `med-deepscientist` / `runtime_transport` runtime boundary 快照。 | [runtime boundary](../../runtime/contracts/runtime_boundary.md)。 |
| [legacy `.ds` public CLI retirement](legacy_ds_retire_public_cli_retirement_2026_06_28.md) | 旧 `runtime legacy-ds-retire` public CLI / parser / controller 退役 tombstone。 | Canonical runtime state、OPL storage maintenance、`runtime maintain-storage` / `runtime storage-audit`、historical retention 与 semantic cold-store retention。 |
| [MAS private surface physical retirement](mas-private-surface-retirement.md) | MAS 私有控制面物理退役 tombstone；记录旧 module / CLI alias / workspace wrapper / compat shim 的 repo-source 删除、合法残留角色和 live-runtime readiness 分账边界。 | `contracts/runtime/mas-runtime-surface-retirement-inventory.json`、[status](../../status.md) 与 [MAS ideal-state gap plan](../../active/mas-ideal-state-gap-plan.md)。 |
| [MAS console display provenance](live_console_ui_contract.md) | 已退役的 MAS 私有 console / terminal attach / display 合同记录。 | OPL current-control-state / provider attempt projection；MAS active 面为 [study progress projection](../../runtime/projections/study_progress_projection.md) 与 [product/workbench boundary](../../product/README.md)。 |
| [MAS console MDS WebUI parity plan](mas_live_console_mds_webui_parity_plan.md) | 已退役的 clean-room parity 实施记录。 | OPL runtime workbench / terminal transport；MAS active 面为 [study progress projection](../../runtime/projections/study_progress_projection.md) 与 [product/workbench boundary](../../product/README.md)。 |
| [hyphenated private implementation migration inventory](opl-private-implementation-migration-inventory.md) | 私有平台化 surface 迁移历史快照。 | `contracts/functional_privatization_audit.json`、production acceptance contract 与当前 active gap plan。 |
| [standard OPL Agent private implementation inventory](opl_private_implementation_migration_inventory.md) | 标准 OPL Agent private-surface 台账历史快照。 | `contracts/functional_privatization_audit.json`、`contracts/generated_surface_handoff.json`、`contracts/pack_compiler_input.json` 与当前 active gap plan。 |
| [OPL unique control plane boundary contract](opl_unique_control_plane_boundary_contract.md) | retired MAS CLI surface / OPL current-control-state handoff tombstone。 | OPL current-control-state / provider attempt ledger 与 MAS owner receipt / typed blocker refs。 |
| [outer-loop wakeup and decision loop](outer_loop_wakeup_and_decision_loop.md) | 旧 outer-loop wakeup 设计说明；保留术语 provenance。 | [study runtime control surface](../../runtime/control/study_runtime_control_surface.md) 与 [runtime event and outer-loop input contract](../../runtime/contracts/runtime_event_and_outer_loop_input_contract.md)。 |
| [runtime core convergence and controlled cutover implementation plan](runtime_core_convergence_and_controlled_cutover_implementation_plan.md) | 旧 runtime core convergence / cutover 实施计划。 | [runtime boundary](../../runtime/contracts/runtime_boundary.md)、[study runtime control surface](../../runtime/control/study_runtime_control_surface.md) 与 [runtime core convergence contract](../../runtime/contracts/runtime_core_convergence_and_controlled_cutover.md)。 |
| [runtime event and outer-loop input implementation plan](runtime_event_and_outer_loop_input_implementation_plan.md) | 已完成的 native runtime truth / outer-loop input 实施计划。 | [runtime event and outer-loop input contract](../../runtime/contracts/runtime_event_and_outer_loop_input_contract.md)。 |
| [runtime supervision loop](runtime_supervision_loop.md) | 旧 MAS supervision loop tombstone 与 owner receipt provenance。 | OPL current-control-state / provider attempt projection；MAS active 面为 owner receipt、typed blockers、domain authority refs 与 refs-only projection。 |
| [workspace knowledge and literature implementation plan](workspace_knowledge_and_literature_implementation_plan.md) | 已完成的 workspace knowledge / literature 实施计划。 | [workspace knowledge and literature contract](../../runtime/contracts/workspace_knowledge_and_literature_contract.md)。 |

## Tombstone / Provenance Index

以下索引是退役残留的唯一维护入口；不要再新增逐项 closeout 文档来重复这些口径。

| retired surface family | tombstone owner | current read rule |
| --- | --- | --- |
| old domain-health diagnostic / owner-route / domain-owner dispatch / default-executor / Progress Portal control-plane wording | `contracts/runtime/legacy-active-path-tombstones.json` and [legacy active path tombstones](legacy_active_path_tombstones.md) | 只能作为 diagnostics、migration input、history provenance、consume/readback evidence 或 no-resurrection guard；不得恢复为 PaperMission 默认主线、runtime readiness、paper progress、owner receipt、typed blocker 或 publication-ready 证据。 |
| MAS private runtime substrate, local carrier persistence, owner-callable/default-executor carriers, runtime health/workbench/capability projections, runtime lifecycle/storage maintenance | `contracts/runtime/mas-runtime-surface-retirement-inventory.json` and [MAS private surface physical retirement](mas-private-surface-retirement.md) | repo-source retirement 与 live-runtime readiness 分账读取；旧 module / CLI alias / wrapper / compat shim 不再作为 active public surface。允许残留只限 OPL-authorized adapter、MAS minimal authority adapter、body-free projection、tombstone/provenance 或 no-resurrection guard。 |
| legacy public helper retirements such as `progress-projection`, `legacy-control-surface-clean-migration`, `legacy-ds-retire`, and runtime supervisor test helper shims | this index plus theme-level [program history index](../program/README.md) | 只保留退役事实和当前 owner surface 指向；不要维护多份 dated active-looking closeout。需要当前命令或测试入口时读取 active docs、parser/source、workspace renderer 和 focused tests。 |

Runtime 历史只保留 provenance。它可以解释当前合同为什么这样设计，但不能重开旧 MDS daemon、WebUI、workspace-local service 或已退役 scheduler 路径。活跃 runtime 变更必须先更新当前 contract / control / projection / display 层。
