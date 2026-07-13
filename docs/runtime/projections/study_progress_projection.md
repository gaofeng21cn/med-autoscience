# Study Progress Projection

Owner: `MedAutoScience`
Purpose: `Explain the migration boundary for legacy MAS progress projections.`
State: `migration_support`
Machine boundary: 本文只解释迁移期 internal projection。当前运行与用户状态真相归 OPL StageRun/current-control/hosted workbench、MAS owner outputs、runtime artifacts、ledgers 与 owner receipts；`study_progress` / `study_state_matrix` 不在 V2 public action catalog 中。

## 当前结论

V2 不再把 MAS 私有 `study_progress` 或 `study_state_matrix` 作为 generated action、runtime owner 或 App authority。正式读链路是：

`OPL StageRun/current-control identity -> MAS Stage/owner refs -> OPL hosted projection/workbench`

现有 controller/read-model code 仍被若干 internal diagnostic、replay、operator drilldown 与 legacy tests 调用，因此本轮只完成 public/default cutover，不宣称物理删除。它们必须保持：

- read-only；
- `authority=false`；
- same-identity/currentness aware；
- 不选择 Stage、owner、next action 或 provider admission；
- 不写 runtime、paper/package、artifact/memory body、owner receipt、typed blocker 或 human gate。

## Public read path

| 需求 | 当前 owner surface |
| --- | --- |
| Stage/attempt/worker/provider 状态 | OPL StageRun/current-control/Temporal-backed runtime |
| 当前研究目标与 Stage result | V2 Stage action output + MAS domain refs |
| 医学 truth / quality / publication decision | MAS owner receipt、typed blocker、human gate、quality/publication authority |
| 用户状态、freshness、blocker 与 next safe action | OPL hosted status/workbench，从上述同一 identity 投影 |
| 深度诊断 | OPL operator drilldown；必要时可读取 legacy MAS projection，但不得升格为 authority |

用户和 Agent 不直接调用 `study_progress`、`study_state_matrix`、`paper_mission`、`launch_study` 或 `submit_study_task`。公开执行只走 V2 六个 Stage actions；host-only authority 只走 closed `paper_mission_authority_evaluate` binding。

## Internal diagnostic shape

迁移期 `study_progress` 可以只读下列来源：

- OPL current-control/attempt refs；
- `progress_projection`；
- current study task/artifact/source refs；
- `publication_eval/latest.json` 与 `controller_decisions/latest.json`；
- owner receipt、typed blocker、human gate、route-back refs；
- runtime health/escalation refs；
- explicit legacy archive/provenance refs。

它可以生成 `study_macro_state`、`user_visible_projection`、freshness、blocker summary、deliverable/paper/platform-repair delta classification、diagnostic refs 与 no-authority boundary。所有字段都是 read model：

- queue empty、provider complete、active run id、trace visible 或 projection fresh 不等于 paper progress；
- runtime repair 必须与 deliverable/paper delta 分区；
- stale/conflicting identity 必须显式 `inspect/conflict`，不得猜测；
- owner route、typed blocker、quality/publication verdict 只能引用真实 MAS owner output；
- retry/review/repair budget 耗尽本身不关闭 Stage，也不自动生成 blocker。

## User projection rules

OPL hosted projection面向用户只展示当前阶段、最近可核查增量、阻塞原因、下一安全动作与是否需要人工判断。维护者 drilldown 可以展示 provider/attempt、lineage、staleness、route-back、artifact drift 与 legacy projection refs。

任何 projection 都不得：

- 从旧 queue、transition table、`current_work_unit`、`current_execution_envelope` 或 cached module object 重新选择 next action；
- 把 `current_owner_delta`、PaperRecovery 或 operator card 当 Stage authority；
- 把 docs/status prose、Git state、workspace-local service 或 historical MDS/Hermes state 当 current runtime truth；
- 直接授权 publication-ready、submission-ready、artifact mutation 或 `current_package` 更新。

## Retirement gate

Legacy progress source 只有在以下条件全部成立后才能物理删除：

1. OPL hosted projection覆盖所有 current product/operator caller；
2. StageRun/current-control + MAS owner refs 能提供 replacement parity；
3. `domain_entry_contract`、mainline status、paper mission、owner-route handoff 等 caller 已迁移；
4. no-active-caller、no-forbidden-write、source-closure 和 residue decision fresh green；
5. 相关 tests 改为保护 V2 Stage/hosted projection boundary，而不是固定 V1 action；
6. history/tombstone 保留且无 alias/no-resurrection 回退。

在此之前，正确状态是 `internal_migration_residue`，不是 current public surface，也不是 fully retired。

## 验证边界

Focused projection tests只能证明 read-only、same-identity、no-second-decision 与 no-forbidden-write。它们不能证明 OPL runtime live、paper progress、publication quality、owner acceptance 或 App production readiness。最终 public/default 关闭还需要 V2 interfaces、source-closure、conformance、default-callers 与 residue-decisions fresh readback。
