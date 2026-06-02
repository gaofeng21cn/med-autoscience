# MAS 状态与 Contract 收薄折返记录

Owner: `MedAutoScience`
Purpose: `state_contract_thinning_foldback_record`
State: `closed_folded`
Machine boundary: 本文是人读折返记录。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、domain-handler receipt、runtime/controller durable surfaces、真实 workspace artifact、owner receipt、typed blocker 和 generated artifact proof。
Date: `2026-05-29`

Current owner note: 本文已退出 active 层，只作为 history/provenance 读取。当前控制面行为契约回到 `docs/status.md`、`docs/active/mas-ideal-state-gap-plan.md`、`docs/active/current-development-lines.md`、runtime projection docs、contracts/source 和 focused tests。

## 当前结论

MAS 状态与 contract 收薄已折回当前 runtime docs、gap plan、status 与 focused tests。本文不再维护 active execution plan，也不保存 production evidence tail。

稳定控制面固定为：

`macro_state + owner_route + receipt_or_blocker + evidence_refs`

当前行为契约是：

- 同一输入只能产生一个 current owner route；consumer 必须用当前 route 的 `route_epoch`、`source_fingerprint`、`next_owner`、`allowed_actions` 和 `idempotency_key` 取得执行授权。
- 旧 dispatch、旧 owner route、旧 publication eval、旧 controller decision、旧 runtime state 和旧 OPL attempt 只能生成 typed blocker 或 fail-closed payload，不得重新执行。
- forbidden writes 不发生；`publication_eval/latest.json`、`controller_decisions/latest.json`、paper/body、memory body、artifact body、`current_package` 和 generic runtime queue 不能由 refs-only consumer 或 OPL ledger 写入。
- AI-first quality gate 必须携带独立 reviewer/auditor invocation 的 task/context/receipt refs；executor 自审、同一上下文复核、脚本/regex/scorecard、queue completion 或 provider completion 都不能关闭医学质量判断。

## 折回位置

| 落点 | 当前职责 |
| --- | --- |
| [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) | 持有当前唯一 active truth、剩余 production evidence tail 和禁止误写口径。 |
| [当前状态](../../status.md) | 摘要化当前控制面口径，说明 consumer/dispatch/product-entry/OPL handoff 的授权来源。 |
| [MAS 当前开发线路](../../active/current-development-lines.md) | 把 `state_contract_thinning` 归为 folded guard，不维护第二 backlog。 |
| [Study macro state and owner route](../../runtime/projections/study_macro_state_and_owner_route.md) | 定义 runtime projection 层的稳定状态面与 owner route contract。 |
| [Study runtime orchestration](../../runtime/control/study_runtime_orchestration.md) | 定义 runtime orchestration 中 diagnostic reason 与 execution contract 的分层。 |
| Focused tests | 证明长 reason / supervisor phase / projection-local status 不能绕过 current owner ticket、receipt/blocker、evidence refs、forbidden-write guard 和独立 reviewer/auditor refs。 |

## 不再在本文维护

- 不维护 lane checklist、执行顺序、future implementation tail 或 dated receipt 流水。
- 不新增第二套 state/reason enum 删除计划；后续新增执行判断必须直接进入 owner route、typed blocker、receipt 或 evidence ref。
- 不记录真实 paper-line、memory/artifact/lifecycle、human gate/resume、provider SLO long-soak 或 OPL worklist 计数；这些只保留在 [MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md) 的 production evidence tail。
- 不把 OPL refs-only ledger receipt、provider completion、suite pass 或 descriptor ready 写成 MAS domain-ready、production-ready、publication-ready、artifact mutation authorization 或 `current_package` 更新。
