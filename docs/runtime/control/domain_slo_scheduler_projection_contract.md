# Domain SLO Scheduler Projection Contract

Status: `OPL replacement default / MAS local tombstone / Hermes cleanup-only`
Owner: `OPL provider/runtime manager for scheduler lifecycle; MAS for domain SLO and receipts`
Date: `2026-05-18`

## 入口结论

默认 outer supervision scheduler owner 是 `opl_provider_runtime_manager`，默认 adapter 是 `opl_family_runtime_provider`。`runtime-supervision-status`、`runtime-ensure-supervision` 与 `runtime-remove-supervision` 默认只投影或委托 OPL replacement，不安装、不刷新、不触发 MAS-owned OS scheduler。

MAS 保留的是 paper-progress SLO 解释、domain tick payload、owner receipt、typed blocker、safe action refs 和 no-forbidden-write evidence。MAS-owned `local` scheduler / LaunchAgent install path 已物理退役；公开 CLI manager choices 不再包含 `local`，只保留 `local_launchd_retired_tombstone` projection 与 history/tombstone/provenance refs。

显式 `--manager hermes` 只保留在 `runtime-supervision-status` 和 `runtime-remove-supervision`，用于旧 Hermes gateway cron 的 job registry、session history、latest run、gateway liveness projection 和旧 job/script cleanup。`runtime-ensure-supervision --manager hermes` 不再是公开入口；controller direct call 也只返回 retired tombstone，不写 tick script、不 create/edit/resume/run cron job。Hermes 不持有 study truth、runtime truth、publication verdict、quality verdict 或 artifact authority。

## 三层边界

| layer | owner | responsibility |
| --- | --- | --- |
| Generic Runtime Core | `OPL provider-backed stage runtime` | 持有 durable attempt、queue、wakeup、worker residency、retry/dead-letter、transition runner、provider transport 和 generic lifecycle/index。 |
| MAS Domain Runtime Adapter | `MAS Runtime OS` / `mas_runtime_core` | 持有 MAS domain tick contract、owner receipt、typed blocker、runtime event refs、guarded apply 和 standalone diagnostic。 |
| Supervisor Scheduler | `OPL provider/runtime manager` | 持有 scheduler lifecycle、cadence、provider SLO、attempt queue、retry/dead-letter、operator projection 和 lifecycle index。 |
| Product Projection | `Progress Portal` / `Live Console` / `study-progress` / cockpit | 只读展示 MAS/OPL refs、freshness、blocker 和 safe action refs，不执行 runtime action。 |

## Scheduler Surface

默认 CLI 形态：

```bash
medautosci runtime-supervision-status --profile <profile>
medautosci runtime-ensure-supervision --profile <profile>
medautosci runtime-remove-supervision --profile <profile>
```

默认输出必须包含：

- `scheduler_owner=opl_provider_runtime_manager`
- `adapter_id=opl_family_runtime_provider`
- `manager=opl`
- MAS retained role：`paper_progress_slo_semantics`、`owner_receipt`、`typed_blocker`、`safe_action_refs`、`no_forbidden_write_evidence`

默认输出不得写 MAS study truth、memory body、publication quality verdict、artifact body 或 artifact export authorization。

## Local Tombstone

`local` 当前不是 active manager。`domain_slo_scheduler_projection` controller 可以返回 `workspace_runtime_supervision_legacy_tombstone` 作为 provenance projection，但 CLI、MCP、product-entry、sidecar 和 workspace bootstrap 不得把 `local` 暴露成 status/remove/ensure command。

Local tombstone 必须满足：

- `adapter_id=local_launchd_retired_tombstone`
- `active_path_role=physical_retired_tombstone_provenance_only`
- `install_allowed=false`
- `status_allowed=false`
- `remove_allowed=false`
- `trigger_allowed=false`
- `write_install_proof=false`
- `body_included=false`

Retained refs:

- `contracts/runtime/legacy-active-path-tombstones.json`
- `docs/history/runtime/legacy_active_path_tombstones.md`

## Legacy Hermes Diagnostic Adapter

`--manager hermes` 只表示显式 legacy proof / diagnostic cleanup adapter。它可以读取历史 Hermes cron/session/gateway 证据，也可以通过 `runtime-remove-supervision --manager hermes` 移除旧 cron job、旧 script 和 retired legacy service evidence；它不得 create/edit/resume/run cron job，不得写 MAS tick script，也不得成为新 scheduler template、provider fallback 或长期保留接口。

Hermes adapter 不得成为：

- MAS 默认 scheduler owner
- MAS runtime truth owner
- MAS executor kind owner
- publication quality / source readiness / artifact mutation authority
- OPL Full online readiness 的替代证据
- MAS-owned active scheduler install / refresh / trigger path

## Done Criteria

- `local` 不在公开 CLI manager choices 中。
- `runtime-ensure-supervision` 的公开 manager choices 只包含 `opl`；Hermes ensure direct-call 返回 retired tombstone，不执行 install / refresh / trigger。
- 默认 scheduler projection 不依赖 Hermes 或 MAS local LaunchAgent。
- MAS product-entry、sidecar、Portal 和 Live Console 只展示 OPL default projection、Hermes diagnostic projection 或 local tombstone/provenance refs。
- No-active-caller proof 显示 default caller count 为 `0`，explicit local callers forbidden。
- 后续真实 paper-line provider soak、memory/artifact receipt scaleout 和 provider SLO long soak作为 evidence gate 单独推进。
