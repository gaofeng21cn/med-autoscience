# MAS Single-Project MDS Absorb Program

Status: `long-line execution program; workspace layout, quest/root Git retirement, profile/entry retirement, repo-level no-history physical absorb and functional monolith completion landed; future upstream source intake remains triggerable`
Date: `2026-05-08`
Owner: `MedAutoScience`

## 结论

MAS 长线应成为唯一项目、唯一研究入口和唯一运行治理 owner；MDS 不应继续作为独立日常项目存在。目标不是把 `med-deepscientist` 原样搬进来，而是把 MDS 解构为 MAS 内部可验证能力：能被 MAS 直接拥有的能力进入 MAS owner 模块；仍需对照的能力降级为 fixture-only / historical oracle；没有长期价值的入口、目录和命名退休。

这个 program 一步到位定义最终可用状态：repo、运行入口、真实论文 workspace layout、兼容导出、GitHub contributor footprint、验证与清理规则都必须一起收敛。执行可以并行开 worktree，但每条 lane 必须有明确 write set、验证和吸收顺序；没有 parity proof 和 rollback surface 的能力不得物理吸收。

2026-05-06 的状态管理与文件分层重构不改变本 program 的方向，但提高了吸收门槛：MDS 吸收必须同时尊重 `current truth`、SQLite runtime authority、workspace memory 和 canonical paper authority 四层边界。任何 lane 如果把运行索引、学习记忆、交付镜像或 MDS oracle 升格为 study / quality / publication truth，都不能进入 cutover。

2026-05-06 追加落地：新建 workspace 的默认 writer 已切到 MAS-first layout：`runtime/quests/`、`runtime/archives/`、`runtime/restore_index/`、`artifacts/runtime/` 与 `ops/mas/`。旧 `ops/med-deepscientist/runtime/quests/` 仍由 compatibility reader 和 Git ignore 规则识别，但不再是默认 scaffold 或新 writer 目标。

2026-05-07 当前进度判断：Git 退役已经完成 repo-side contract、默认 layout、SQLite authority 边界、workspace Git boundary guard、current eligible disease workspace 的 restore-proof storage compaction、SQLite lineage/snapshot/allocation writer、SQLite-only reader projection、plain quest materializer CLI、quest Git inventory、默认 fallback retirement、legacy runtime reader cutover、显式 historical fixture / explicit archive import reference、safe quest Git cutover CLI 和 workspace root Git retirement CLI。真实 workspace active-path cutover ledger 已推进到 NF-PitNET、AS biologics、HeRR、DM-CVD verified；DM-CVD 剩余 DM002/DM003 已在无 live worker 窗口经 `pause-runtime` 进入 safe state 后 archive/remove。后续论文项目默认 no root Git / no quest Git，不再接触 MDS/DS 路径、quest `.git` 或 `.ds/worktrees` 日常 lifecycle；NF-PitNET、DM-CVD / DPCC 和 AS biologics 的已有 workspace root Git 已按 restore-proof inventory/archive/remove/verify 退役，HeRR 原本 no root Git。

2026-05-08 closeout：近期模块化治理、runtime/control 边界和 progress projection 收口不要求调整本 program 的终局目标，也不需要新增“全仓重构”计划。`workspace_layout_de_mds_ds` 已处理 still-visible MDS/DS surfaces：`profiles/workspace.profile.template.toml` 改为 MAS-owned `runtime/quests` / `runtime`，doctor/show-profile 把旧 `med_deepscientist_*` 字段显示为 historical fixture / explicit archive import reference / backend-audit ref，bootstrap/quickstart/agent runtime 文档也对齐 no root Git / no quest Git / SQLite lifecycle / explicit archive import only。`profile_entry_compat_retirement` 已把默认入口继续收紧：MCP `doctor_audit` 只接受 `backend_audit`，旧 `med_deepscientist_upgrade` mode fail-closed；profile JSON 顶层改为 `source_provenance`、`historical_fixture_ref` 与 `explicit_archive_import_ref`；workspace contract 改用 `managed_runtime_*` 与 `controlled_backend_*`；product-entry / progress 的默认 executor owner 改为 `controlled_research_backend`。最终 `no_history_physical_absorb` campaign 已把 source provenance、author audit、capability parity fixtures、MAS-owned retained capability absorb、external runtime dependency retirement 和 docs closeout 落到 repo-level guard；外部 `med-deepscientist` checkout 不再是 MAS 默认 study/status/progress/cockpit operation 的运行必需依赖，只保留为显式 backend audit、historical fixture / explicit archive import reference、upstream intake 和 parity oracle。

2026-05-08 functional monolith correction：上面的 closeout 不是函数级、模块级或 workflow 级 1:1 吸收完成。当前 parity matrix 固定 `runtime_execution`、`artifact_inventory`、`paper_contract_health`、`manuscript_coverage`、`prompt_stage_discipline`、`memory_and_lesson_store` 六类 retained capability，并新增 `mds_remaining_surface_inventory` 覆盖 runtime core daemon、quest、runner、transport、MCP、TUI/Web、gitops、skills、team、upstream archive 等 remaining surface。机器分类只允许 `mas_owned` / `rewrite_in_mas` / `fixture_only` / `retire` / `external_source_archive_only`；旧 `absorb` / `oracle` / `compat` 不再作为 cutover contract 值。后续目标从“MAS 是唯一入口”升级为“MAS 是实际 monolith”：默认 operation、可视化、运行 core、诊断、学习和保留能力都由 `med-autoscience` 内部 MAS-owned modules 承接；外部 MDS repo 只可作为 source archive / provenance reference，不作为运行、WebUI 或 contributor source。

2026-05-08 behavior equivalence correction：本 program 的 monolith 完成口径进一步收紧为 `default_independence_not_full_behavior_equivalence`。MAS 可以不运行 MDS repo、MDS daemon、MDS runtime root 或 MDS WebUI 完成默认日常 operation；但旧 MDS resident daemon 的低延迟会话、WebSocket terminal、connector background delivery、daemon lifecycle control 和 GitOps runtime lifecycle 没有被声明为 1:1 等价实现。默认监管由 `Hermes gateway cron` 每 300 秒执行一次 `ops/medautoscience/bin/watch-runtime --interval-seconds 300 --max-ticks 1`。旧 workspace-local launchd/systemd/cron/docker service scaffold 已退役，发现后只作为 cleanup evidence，不作为 active scheduler 选项。

2026-05-08 runtime continuity correction：为补齐 daemon 退役后对用户最敏感的连续性缺口，MAS 已把 session/worker tracking 与 crash recovery intent 落成 MAS-owned surface。`runtime_session` read model 统一投影 worker state、active/last-known run、last seen、event cursor、stdout ref 与 freshness；`recovery_intent` ledger 记录恢复原因、next owner、retry budget、dedupe fingerprint、last attempt/result 与 `current_action`；`runtime_reconcile_trigger` 只在 safe 条件下给读入口展示一次 reconcile 推荐；`runtime_continuity` 投到 study-progress、workspace cockpit、product-entry、Progress Portal、MCP 和 OPL handoff。这仍然不是 MDS resident daemon 1:1 复刻，恢复动作必须继续通过 `RuntimeHealthKernel -> owner_route -> executor -> rescan`。

2026-05-08 current behavior reassessment：此前“日常科研运行目的等价 + 部分实时/交互能力退役或替换”的结论需要细化。当前 MAS 已把最关键的 `continuous turn loop` 从目的等价推进到行为等价：runner 返回后由 MAS kernel 归一化状态、清理 live flags、优先 drained queued user messages，并按 `continuation_policy=auto` 低延迟调度下一 turn；这条内生主循环不再受 `Hermes gateway cron` 的 300 秒 tick 限制。300 秒 tick 仍然存在，但现在只作为 outer supervision、drift detection、stale recovery 和 read-model refresh 的默认 cadence。terminal/log observation 已由 MAS-owned read-only Live Console 承接为 purpose parity。旧 resident WebSocket terminal attach、terminal input/resize/detach 和 UI-issued runtime control 不是当前 read-only landed scope，也不应写成已放弃；它们属于后续 interactive parity candidate，必须通过 MAS-native safety / owner / idempotency / audit gate 后才能进入默认行为。connector background delivery、旧 in-memory session API 和 MDS daemon lifecycle controls 仍不作为默认 MAS 行为恢复。

2026-05-08 live console UI shell update：`M3b_live_console_parity` 的 Lane D/E 非 Portal 主逻辑已落到 MAS-authored read-only UI shell contract。`runtime_live_console_ui` 负责把 live-console snapshot 渲染为 `ops/mas/live-console/index.html` 所需 payload/HTML，页面展示 workspace/study/run、状态 timeline、terminal/log tail 与 artifact/event refs。Portal 只承担 thin entry/return ref，不解释 live-console 状态，也不拥有 terminal/log stream 或 run/session 语义。

2026-05-08 WebUI user parity correction：Progress Portal 的固定入口已经 landed，但用户体验等价仍不完整。旧 MDS WebUI 的强点是 per-project/per-quest workspace，用户按一篇论文/quest 查看 stage、文件、执行对话和 terminal；当前 MAS Portal 默认 workspace overview 会把多篇论文放在同一页，容易混淆。后续 Portal UX parity 的 P0 是 study-scoped IA、per-study deep link 和单篇论文 Overview / Path / Runtime / Conversation / Terminal / Artifacts 工作台。调研与后续 lane 见 `docs/references/mds_webui_user_parity_gap_review.md`。

2026-05-08 paper autonomy stability correction：functional monolith landed 不自动等价于真实论文自治稳定性 landed。真实 paper autonomy 需要另一组证据：所有 `/Users/gaofeng/workspace/Yang/*/ops/medautoscience/profiles/*.toml` 可枚举且 profile 可读；每个 workspace 的 study status/progress surfaces 可读；active / parked / completed 原因可解释；legacy MDS launcher/default runner evidence 可见且只作为 diagnostic；supervisor reconcile、workspace migration dry-run 与 real-paper soak 均有只读或 controller-authorized evidence。Lane 5/6 的 `real_paper_autonomy_soak_inventory` 只提供 dry-run/inventory harness，不 apply migration、不实现 reconcile CLI、不改 owner_route schema、不写 `current_package` / `submission_minimal` / publication gate。

2026-05-08 runtime evidence closeout：后续三项优化已按本 program 的 authority rules 落地。`outer_supervision_slo` 明确外层 recovery latency：默认 scheduler 仍是 `Hermes gateway cron`，SLO read model 只判断 `fresh/due/stale/missing/blocked` 并推荐 canonical `runtime-supervisor-reconcile --dry-run`；它不是 resident daemon，也不恢复旧 workspace-local `launchd/systemd/cron/docker` service。`portal_console_soak` 为真实 profile 生成只读 Portal/Live Console evidence，写入范围限于 `artifacts/runtime/progress_portal/*`、`artifacts/runtime/live_console/*`、`artifacts/runtime/portal_console_soak/latest.json`、`ops/mas/progress/index.html` 与 `ops/mas/live-console/index.html`。`paper_autonomy_stability_evidence` 把 inventory、reconcile dry-run、migration dry-run 与 real workspace soak monitor 合并为 read-only evidence surface；它可以关闭 repo/read-model 缺口，但真实论文 autonomy 只有在无 blocker 的 evidence 下才能从 `evidence_landed_with_blockers` 提升为 `landed`。

## Program Coordination With Runtime Lifecycle Cutover

本文件是 MAS 吸收 MDS 的总执行计划；[Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) 是本计划下的 runtime persistence / quest Git retirement 子计划，不是另一条独立并行路线。

协同判断固定如下：

- MAS absorb 负责产品入口、owner 边界、代码归属、workspace layout、no-history import、真实项目 cutover 和 compatibility retirement。
- Runtime lifecycle SQLite program 负责 runtime lifecycle authority、lineage、workspace allocation、snapshot metadata、diff / Canvas read model、retention ledger、archive refs、restore proof 和 quest-level Git retirement。
- 两条线可以按 disjoint write set 并行实现，但必须共享同一 owner matrix、SQLite schema contract、migration ledger、restore proof 和 compatibility retirement gate。
- `runtime_lifecycle_sqlite_migration_program.md` 的 `Q0-Q6` lane 对应本计划的 `L3_runtime_absorb`、`L4_artifact_and_storage_absorb`、`L6_entrypoint_retirement` 和 `L8_real_workspace_cutover`；其中 `Q0_sqlite_authority_contract` 必须先于任何 Git writer / worktree writer 退役。
- 当前项目的 SQLite-backed runtime cutover 已完成到 quest/root Git retired 口径；MDS Git compatibility reader 不再是默认安全阀。后续只保留显式 historical fixture / explicit archive import reference、upstream intake 和 parity oracle。

Git 退役、真实 workspace layout 迁移和兼容接口退役是本 program 的加速子目标，可以先于 MDS 物理代码吸收完成。执行优先级固定为：

1. `Q1-Q4` 和 repo-default `Q6` 已进入 landed 口径：repo-level schema/writer/read-model/plain materializer、inventory、historical fixture / explicit archive import reference、default fallback retirement 和 default reader cutover 已可用。
2. `Q5` 已完成 current-project active-path cutover：registry-discovered 真实 workspace 已有 Git-era inventory、safe cutover apply、restore-proof archive、projection verification 和 controller-authorized cutover ledger。
3. 项目级 `Q6` 已完成 default runtime path closeout：默认 fallback 已删除，只保留显式 `restore_legacy_git_archive` / `import_legacy_git_archive` 诊断入口。
4. 后续论文项目按 MAS-only workspace 规则展开：新 scaffold 无 `ops/med-deepscientist`、无 `.ds` 默认目录、无 quest `.git` 日常 lifecycle，也无 workspace root Git 默认要求；用户/医生可见路径已按 MAS-owned layout 显示。

后续 program portfolio 管理见 [Program Portfolio Consolidation](./program_portfolio_consolidation.md)。新增长线计划必须先映射到该 portfolio 的 active owner doc；不得再新建一套 runtime authority、lineage 或 projection 管理路线。

当前 portfolio 队列已经关闭到 no-history physical absorb repo-level closeout。workspace root Git full retirement、workspace layout de-MDS/DS、profile/entry compatibility retirement 和 no-history absorb guard/parity/default-runtime-retirement 已由 runtime lifecycle / layout / compat / absorb 子计划执行并把 ledger / proof 回写到本 program。

## 最终目标形态

目标 repo 拓扑：

```text
med-autoscience/
  src/med_autoscience/
    mas_core/
    quality_os/
    runtime_os/
    artifact_os/
    observability_os/
    runtime_compat/
      legacy_deepscientist/
    backend_oracles/
      deepscientist_legacy/
    migration/
      mds_absorb/
```

目标 workspace 拓扑：

```text
workspace/
  portfolio/
    research_memory/
    data_assets/
  studies/<study_id>/
    artifacts/
      controller/
        study_charter.json
      reference_context/latest.json
      runtime/
        study_macro_state/latest.json
        owner_route/latest.json
    paper/
      evidence_ledger.json
      review/
        review_ledger.json
      submission_minimal/
    manuscript/
      current_package/
      current_package.zip
  artifacts/
    runtime/
      runtime_lifecycle.sqlite
  runtime/
    quests/
    archives/
    restore_index/
  ops/mas/
  delivery/
```

旧布局只作为迁移输入和只读兼容层存在：

```text
ops/med-deepscientist/runtime/.ds/
ops/med-deepscientist/runtime/quests/
<quest>/.ds/worktrees/
```

新建 workspace 不得再默认生成 `ops/med-deepscientist`、`.ds` 或以 MDS/DS 为第一身份的路径。旧 workspace 可以保留原路径直到迁移完成，但所有新写入必须进入 MAS-owned runtime layout，旧路径只能通过 compatibility reader、restore index 或 explicit import surface 被读取。

## Layering Alignment After The 2026-05-06 Refactor

本 program 继续必要，但必须按下面四层吸收，避免把 MDS 退役过程变成新的混乱来源。

| layer | current MAS authority | MDS absorb rule |
| --- | --- | --- |
| state/current truth | `StudyTruthKernel`、`RuntimeHealthKernel`、`study_macro_state/latest.json`、`owner_route`、consumer/executor receipts | MDS 事件只能作为 reducer input 或 replay oracle；不得写用户宏观状态、owner route、canonical next action 或 runtime recovery decision。 |
| persistence/index | `artifacts/runtime/runtime_lifecycle.sqlite`、migration ledger、restore index、checksum/manifest proof | SQLite 是 runtime lifecycle authority、read model、receipt 和 cursor store；不得替代 paper/manuscript/package、publication eval、controller decision、dataset manifest 或 restore metadata。 |
| workspace memory/learning | `portfolio/research_memory/*`、study reference context、incident learning、AI reviewer calibration read models | memory / lesson store 只能进入 workspace knowledge、calibration 或 observability；不得授权 quality、drafting、finalize、submission 或 route cutover。 |
| paper/artifact truth | study charter、evidence ledger、review ledger、AI reviewer-backed `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical manuscript source、`submission_minimal`、`manuscript/current_package` rebuild proof | MDS paper contract health、coverage、artifact inventory 只能做 mechanical oracle 或 compatibility proof；不得让旧 package、current_package README、SQLite record 或 `.ds` payload 成为 edit source、quality authority 或 submission authority。 |

读路径固定为：先读文件 authority / canonical paper truth，再读 materialized macro state 与 owner route，再用 SQLite 补 history、cursor、retention 和 receipt，最后才读取 MDS compatibility/oracle。写路径固定为：先写 MAS owner authority surface 或 canonical artifact，再写 latest mirror / dispatch receipt，再写 SQLite index，最后写 compatibility export 或 migration proof。MDS compatibility reader 只能补充旧路径可读性，不能隐式写回新 truth。

## Contributor Footprint Rule

repo 吸收必须采用 `no-history import`。

禁止：

- `git merge --allow-unrelated-histories` 吸收 `med-deepscientist`
- `git subtree add` 保留上游历史
- `git filter-repo --to-subdirectory-filter` 后把上游历史接进 MAS `main`
- 把上游 DeepScientist / med-deepscientist commit authorship 带入 `med-autoscience` default branch

允许：

- 用 MAS-authored commit 导入经过审计的代码 snapshot
- 用文档记录 upstream ref、source archive hash、license notice、decision matrix 和 retained/rejected capability
- 把完整上游历史保留在外部 archive、tag、private/reference mirror 或 artifact bundle 中，不接入 `main`

吸收前后必须执行 contributor audit：

1. import 前记录 `git shortlog -sne`、候选 source authors、license/provenance refs。
2. import commit 必须使用 MAS maintainer author/committer identity。
3. import 后检查 `git log --format='%an <%ae>' origin/main..HEAD`，不得出现不想进入 MAS contributor graph 的上游作者。
4. push 后用 GitHub contributors / default-branch history 做可见面验证。
5. 若出现不应出现的 contributor footprint，立即停止后续吸收，修正历史后再推进。

## Authority Rules

- MAS Core 持有 study truth、controller truth、user-visible next action。
- Quality OS 持有 scientific quality、medical writing quality、publication readiness、submission authority。
- Runtime OS 持有 runtime health、durable execution、recovery action。
- Artifact OS 持有 canonical rebuild、package locator、delivery authority。
- Observability OS 只持有 evidence、calibration、provider/runtime drift projection。
- `legacy_deepscientist` 只能是 compat/oracle，不得写 study truth、quality truth、publication truth、delivery truth 或 user-visible next action。
- SQLite lifecycle store 只能持有 index/history/retention/cursor/receipt，不得成为 study、publication、artifact、memory 或 restore authority。
- `portfolio/research_memory` 与 learning read model 只能支撑跨 study 复用、AI reviewer calibration 和 incident learning；不得直接驱动 submission-ready 或 finalize。
- `manuscript/current_package/`、`current_package.zip`、`submission_minimal/` 和 delivery README 是 human handoff / delivery projection；revision 必须回到 canonical paper sources 和 MAS quality/runtime chain。

任何保留 `deepscientist` 字样的模块必须带 `legacy`、`compat` 或 `oracle` 语义，不得成为产品入口、默认 runtime owner 或独立 governance surface。

## Capability Absorb Matrix

| capability | final MAS owner | MDS final status | absorb gate |
| --- | --- | --- | --- |
| runtime execution | Runtime OS | oracle fixture until cutover | execution replay parity、recovery regression、rollback surface |
| quest layout | Runtime OS | compatibility reader | new MAS runtime layout writer、old layout reader、restore proof |
| `.ds` runtime payload | Runtime OS / runtime lifecycle | archived import source | SQLite lifecycle index、cold archive、restore index、no authority writeback |
| artifact inventory | Artifact OS | fixture only | MAS package locator parity、old current_package reader compatibility、canonical rebuild proof |
| paper contract health | Quality OS | mechanical oracle only | AI reviewer / publication eval authority unchanged |
| manuscript coverage | Quality OS | mechanical oracle only | coverage can request review, cannot authorize ready |
| prompt stage discipline | Quality OS / Runtime OS | example and violation fixture | MAS stage contract owns transitions |
| memory / lesson store | Evaluation OS / workspace memory | intake fixture | `portfolio/research_memory` import, incident learning import, observability-only output |
| product entry / CLI / MCP | MAS app skill / MAS CLI / MAS MCP | retired | all active commands route through MAS |
| skills / overlay templates | MAS-owned app skill | legacy template source | no global MDS skill injection |

## Long-Line Lanes

这些 lane 可以并行执行，但必须在吸收回 `main` 前完成对应验证。

| lane | branch suggestion | write set | target |
| --- | --- | --- | --- |
| `L0_target_contract` | `codex/mas-mds-absorb-target-contract` | docs/program、architecture/status references、contract tests | 固定单项目拓扑、no-history import、workspace去 MDS/DS 化规则。 |
| `L1_workspace_layout_contract` | default writer and doctor-visible cleanup landed | workspace layout helpers、runtime protocol layout tests、docs/runtime、profile template、doctor/show-profile docs | 新 workspace 默认写 MAS layout、portfolio memory、paper truth 与 runtime sidecar；旧 `.ds` / `ops/med-deepscientist` 只读兼容；静态 profile 和医生可见输出已去 MDS/DS 化。 |
| `L2_mds_inventory_and_classification` | no-history provenance, parity harness and remaining-surface inventory landed | migration inventory tooling、capability matrix、source snapshot manifest | MDS source provenance 已固定到真实 ref/hash，retained capability 与 remaining surface 已标记 `mas_owned` / `rewrite_in_mas` / `fixture_only` / `retire` / `external_source_archive_only`。 |
| `L3_runtime_absorb` | retained capability absorb landed | Runtime OS、runtime_protocol、recovery tests | execution/recovery/quest lifecycle 的可保留价值已进入 MAS-owned retained capability absorb surface；MDS trace 仅保留 replay oracle。 |
| `L4_artifact_and_storage_absorb` | current-project storage/Git retirement landed | Artifact OS、runtime lifecycle SQLite、storage migration tests | 吸收 artifact inventory、storage audit、cold archive / restore proof，同时保持 canonical paper truth 优先；quest Git inventory / safe cutover CLI 已落地，真实 workspace Q5/Q6 ledger 已完成。 |
| `L5_quality_oracle_absorb` | retained capability absorb landed | Quality OS、publication eval、AI reviewer fixtures | paper health / coverage 已固定为 mechanical oracle，不授权 ready。 |
| `L6_entrypoint_retirement` | profile/entry retirement landed | CLI/MCP/product-entry/skill docs/tests | MCP stale doctor audit mode、profile JSON 旧字段直出、workspace contract 旧命名、product/progress 默认 executor owner 已退到 historical fixture / explicit archive import reference / backend audit；MDS product entry 不再是默认入口。 |
| `L7_contributor_and_license_guard` | no-history provenance guard landed | scripts/tests/docs/legal or provenance records | no-history import guard、author audit、license/provenance snapshot 已落地。 |
| `L8_real_workspace_cutover` | quest Git, workspace root Git, user-visible layout and profile/entry compatibility cutover landed for current projects / new scaffold | real workspace migration ledgers only | NF-PitNET、DM-CVD、DPCC 等 workspace dry-run、apply、compat export、restore proof 已完成 quest `.git` active-path retirement；NF-PitNET、DM-CVD / DPCC 和 AS biologics 已完成 workspace root Git restore-proof retirement，HeRR 原本 no root Git。 |

## Functional Monolith Completion Campaign

这不是新建第二套 program board；它是本 program 在 no-history physical absorb closeout 之后的 functional monolith closeout。验收标准已从“外部 MDS 不再是默认依赖”提升并落地为“同一目的下不需要再运行 MDS WebUI、MDS daemon 或 MDS repo 来获得 MAS 日常能力”。该标准不声明 full daemon behavior equivalence；行为差异由 [MDS Behavior Equivalence Gap Matrix](../references/mds_behavior_equivalence_gap_matrix.md) 持有。

| lane | write set | target | contributor rule |
| --- | --- | --- | --- |
| `M1_remaining_capability_inventory` | source provenance、capability matrix、tests/fixtures | 已清点 MDS daemon、quest、runners、channels/connectors、MCP、TUI/Web、gitops、skills、team、upstream archive 等 remaining surface，标记 `mas_owned` / `rewrite_in_mas` / `fixture_only` / `retire` / `external_source_archive_only`；不再用 unique function name 数量作为完成指标，但覆盖 workflow 语义。 | 只记录 source ref/hash/license/provenance，不导入上游 history。 |
| `M2_runtime_core_ingest` | Runtime OS、runtime_transport、runtime_protocol、controller/runtime tests | 已把默认执行、watch、worker lifecycle、event cursor、daemon/session interaction 收进 MAS-owned runtime modules；默认 runtime binding 与 live task intake 走 `runtime/` / MAS Runtime OS，外部 MDS 只能留下 replay oracle 或 historical fixture。2026-05-08 Runtime Turn Lifecycle correction 又补齐旧 MDS daemon 的连续科研主循环：turn start 写 worker lease / active run / receipt，真实 runner subprocess exit 由 MAS runner monitor 调回 completion normalization，turn completion 归一化状态并按 pending user messages、human gate、`continuation_policy` 和 terminal state 调度下一 turn；`auto_continue` 由 kernel delayed timer 消费，runtime_watch/inspect 只负责 crash-recovery drain，cron/Hermes/supervisor 只做外层 wakeup/reconcile。 | MAS maintainer-authored implementation 或 no-history snapshot，禁止 co-author trailer。 |
| `M2b_runtime_continuity` | Runtime OS、study_progress、progress portal、product-entry、MCP | 已把 durable `runtime_session` read model、`recovery_intent` ledger、safe reconcile trigger 和 user-surface continuity projection 落地；用户可见面能显示 worker/last seen/current recovery action/why not running/next recovery step。parked、completed、human gate、publication gate missing、retry exhausted 或 stale route 均 fail-closed。 | 只读 projection / controller-owned ledger；不导入 MDS daemon，不把 safe trigger 做成执行器。 |
| `M3_visual_status_replacement` | progress portal、workspace scripts、OPL handoff docs/tests | MAS Progress Portal 成为默认可视化入口；新 workspace 的旧 `start-web` 目的默认刷新并打开 MAS Portal，外部 MDS WebUI 只能作为 explicit archive import reference / backend audit，不再让用户在两个进度看板之间判断 truth。OPL App 的最优集成方式也固定在这里：只消费 MAS 的 `opl_handoff` payload refs、freshness、source refs、artifact locators 和 workspace-local Portal deep link，做 family-level dashboard / attention queue / running-recent 聚合，不重解释 study truth。 | 不导入上游 WebUI commit history、branding 或 contributor footprint；不把 OPL App 或 OPL state cache 升级成 MAS progress authority。 |
| `M3b_live_console_parity` | live-console contract、runtime read model、stream bridge、Portal refs、real workspace soak | 已落地为 `landed_read_only_purpose_parity`：docs/test-lane/soak contract、Runtime OS read model、只读 stream bridge、static Live Console shell、snapshot / loopback SSE 和 Lane E Portal thin link-ref 边界已固定。它承接 terminal/log observation，不声明旧 MDS resident WebSocket attach 1:1 复刻；WebSocket attach/input/resize/detach 与 UI-issued runtime control 是后续 gated interactive parity lane，不是 abandoned surface。Progress Portal 继续只负责进度可视化和入口导航。 | 不导入旧 MDS WebUI code/bundle/history；UI 不直接执行 controller action；soak 不写 paper/package/publication/controller/runtime authority。 |
| `M4_entry_and_compat_shrink` | CLI/MCP/product-entry/profile/workspace contracts | 已删除或 fail-closed 仍会把 MDS 当默认 backend、default WebUI、default runner 或 hidden fallback 的兼容面；保留入口显式命名为 historical fixture / explicit archive import reference / backend audit / parity oracle，并保持只读 provenance/reference。 | 每个删除/迁移都带 regression guard，避免恢复默认 MDS dependency。 |
| `M5_quality_and_artifact_supersede` | Quality OS、Artifact OS、publication eval、delivery tests | 已对 paper health、coverage、artifact inventory、package locator 等 MDS mechanical signals 给出 MAS-owned supersede proof；MDS 信号最多触发 review/request，不授权 quality ready。 | 保留 fixture 可以引用 source provenance，但不引入上游 author graph。 |
| `M6_contributor_and_release_audit` | provenance records、author guard、GitHub/default-branch audit docs | local author audit guard 已要求 `git log --format='%an <%ae>' origin/main..HEAD` 不出现上游 MDS/DeepScientist author 或 co-author trailer；push 后仍需做 GitHub contributor surface 复核。 | 这是 hard gate。 |

## Paper Autonomy Stability Evidence Layer

该层服务真实论文自治稳定性，不重开 functional monolith campaign。它的输入是只读 inventory、focused test lane 和后续 controller-owned reconcile/migration/soak 证据；它的输出只能是 readiness/evidence report，不能成为 publication quality、submission readiness 或 artifact authority。

| evidence lane | current status | required evidence | write boundary |
| --- | --- | --- | --- |
| `control-plane-autonomy` | dry-run harness landed | profile discovery、study status/progress readability、active/parked/completed reason、legacy MDS launcher/default runner evidence | read-only inventory；不写真实 workspace。 |
| `supervisor-reconcile` | contract pending | `scan -> consume -> execute-dispatch -> rescan` 的 focused reconcile evidence，owner_route 新鲜且不越权 | 只能写 supervisor/control receipts；不得写 paper package 或 publication gate。 |
| `workspace-monolith-migration` | migration dry-run pending | workspace profile migration readiness、explicit archive import reference evidence、migration skipped/appliable reason | dry-run 先行；apply 另需 Lane 4 migration apply 合同和 restore proof。 |
| `outer-supervision-slo` | landed | `last_tick_at` / `last_reconcile_at` / `next_due_at`、SLO state、safe reconcile dry-run command、authority flags | read-model projection；不执行 reconcile、不写 runtime truth、不恢复 daemon。 |
| `portal-console-soak` | landed | Progress Portal refresh、Live Console 多 study/run 区分、terminal/log refs、source ref cleanliness、MAS-native product identity | read-only display evidence；只写 Portal/Console/soak artifacts，不写 paper/package/publication/controller/runtime SQLite authority。 |
| `paper-autonomy-stability-evidence` | evidence read model landed | profile readability、status/progress readability、supervisor reconcile dry-run、workspace migration dry-run、soak monitor、blockers/next actions | read-only evidence；只在无 blocker 的真实 evidence 下允许 closeout claim。 |

完成口径：runtime evidence closeout 的 repo/read-model 能力已经 landed；`paper_autonomy_stability` 的产品结论仍必须 evidence-gated。只有 focused evidence lane 均有真实 workspace evidence，且 read-only harness 明确报告没有真实 workspace mutation、无 unresolved blocker，才能把 `paper_autonomy_stability` 从 `evidence_landed_with_blockers` 提升到 `landed`。functional monolith、profile/entry retirement、no-history absorb、Portal/Console soak 和 outer SLO 只能作为前置证据，不能替代该层真实论文证据。

完成该 campaign 后，`MDS retained role` 已从 `research_backend / behavior_equivalence_oracle / upstream_intake_buffer` 降为 `external_source_archive / historical_fixture_ref / explicit_archive_import_ref`。任何未来能力如果仍需长期运行外部 MDS daemon 或 WebUI，都不能进入默认 MAS operation，只能作为 future upstream source intake review 或 explicit archive import reference 重新评审。

## Execution Order

1. `L0-L8` 的 repo-level implementation queue 已关闭到 landed/guard 口径；这只关闭 default dependency / layout / compat / no-history closeout。
2. `M1-M2b` 已把默认运行、连续 turn 主循环、runtime continuity 和外层 recovery projection 落为 MAS-owned surface；后续不再把 `cron 能不能连续跑` 作为未解决主循环问题重开。
3. `M3b_live_console_parity` 已关闭为 MAS-owned read-only purpose parity；它只处理 live console/terminal/log 观察，不声明恢复 MDS WebUI 或 resident daemon。当前 Runtime OS read model、stream bridge 和 UI shell 已支撑独立 `ops/mas/live-console/index.html`；Portal 只接 thin link/ref。后续 polish / soak / Portal per-study IA / interactive attach-control 需要分 lane 推进，不得把它扩大成 Portal-owned 状态解释，也不得把旧 daemon 重新设为 owner。
4. connector background delivery、MDS team service、GitOps runtime lifecycle、MDS daemon lifecycle controls 和 in-memory session API 继续保持 retired / fixture / historical fixture 口径；除非未来有新 product requirement 和 owner proof，不作为默认 MAS operation backlog 重开。
5. 后续新能力只能作为 MAS-owned surface、explicit archive import reference、upstream intake 或 parity oracle 进入，不再重开默认 MDS dependency lane。
6. 若未来从外部 `med-deepscientist` 或上游 `DeepScientist` 学习新能力，必须重新记录 source ref/hash、capability classification、MAS owner、authority boundary、tests 和 no-history contributor audit；classification 必须使用 `mas_owned` / `rewrite_in_mas` / `fixture_only` / `retire` / `external_source_archive_only`。

## Workspace Layout Migration Rule

新 workspace：

- 默认生成 `portfolio/research_memory/`、`studies/<study_id>/artifacts/controller/`、`studies/<study_id>/artifacts/runtime/`、`studies/<study_id>/paper/`、`studies/<study_id>/manuscript/`、`artifacts/runtime/runtime_lifecycle.sqlite`、`runtime/quests/`、`runtime/archives/`、`runtime/restore_index/`、`ops/mas/`。
- 不生成 `.ds`、`ops/med-deepscientist` 或 MDS-first path。
- 不默认初始化 workspace root Git；root Git 不接管 runtime、quest、delivery 或 publication truth。维护者若通过 explicit archive import reference 临时恢复 root Git，必须重新走 restore-proof retirement 或明确留在外部 maintenance audit，不得让它回到默认状态面。
- Agent 查状态、做 lifecycle 操作或恢复 runtime 时，不读取 root Git / quest Git 作为默认状态面；优先使用 file authority、`study_macro_state` / `owner_route`、`artifacts/runtime/runtime_lifecycle.sqlite`、`artifacts/runtime/lifecycle_migration` ledger、`runtime/quests` manifest 和 `runtime/restore_index`。
- `study-progress`、`runtime_watch`、`product-entry-status`、MCP 都只暴露 MAS layout，并按 file authority -> macro state / owner route -> SQLite runtime authority -> compatibility reader 的顺序读取。
- `init_workspace` dry-run 和 apply 都应体现上述目录；`watch-runtime` 默认指向 `${WORKSPACE_ROOT}/runtime/quests`，workspace-level Git 默认忽略 `runtime/quests/`、`runtime/archives/**`、`runtime/restore_index/**` 和 `artifacts/runtime/`。
- `runtime quest-materialize --workspace-root <workspace> --quest-id <quest> --node-id <node>` 是 repo-level plain quest materializer 入口；apply 只创建 `runtime/quests/<quest_id>` 普通目录和 `artifacts/runtime/materialization_manifest.json`，manifest 必须记录 `git_runtime_used=false`、`quest_git_active_path_retired=true`，旧 `ops/med-deepscientist/runtime/quests/<quest_id>` 只能作为 read-only legacy source。
- 如果 active quest root 已存在 `.git`，quest materializer 必须 fail-closed 为 `blocked/audit_only`，直到维护者通过 explicit archive import reference / restore proof 处理；不得把既有 Git repo 接回 active lifecycle。

旧 workspace：

- 第一次 maintenance 生成 `artifacts/runtime/layout_migration/latest.json`。
- live quest 只允许 audit/index，不移动或删除。
- stopped/cold quest 允许 dry-run、archive、restore proof、compat export、apply。
- 旧 `.ds` 内容迁入 `runtime/archives/` 或 `runtime/quests/` 后，必须写 restore index、source checksum、compatibility reader proof。
- old reader 必须能解释旧路径，但新 writer 不得继续写旧路径。
- 旧路径里的 paper package、memory、runtime report 或 artifact inventory 只能迁入对应 MAS layer；不能平铺进一个通用 legacy bucket 后继续被多个入口各自解释。
- 未来若发现外部/旧 workspace 仍带 root Git，必须完成 inventory、archive、restore command、sha256 和 verify ledger 后才允许 remove；有 remotes、locks 或 linked worktrees 时继续 block 到 maintainer audit。root Git 不再作为 MAS workspace 的可选日常维护模式。

## Repo Import Rule

所有未来继续从 MDS / DeepScientist 进入 MAS 的代码必须走 snapshot import：

1. 从受控 MDS ref 生成 source snapshot。
2. 删除不吸收的 provider/UI/global skill/old product entry。
3. 写或更新 `source_provenance.json`，包括 upstream repo/ref、snapshot sha256、license refs、capability classification 和 `remaining_surface_inventory`；当前 closeout snapshot 为 `med-deepscientist@35976b7d6e3b99b15b57ec44ff5f5d959b342ecc`，archive sha256 为 `f8dc31822dc52ecc6e073f54c8b5c95cd46646e299a67cd1c1f6f7f3764e0d5b`。
4. 以 MAS maintainer 身份创建 import commit。
5. import commit message 只记录 upstream ref 和 provenance file，不带上游 co-author trailers。
6. import 后运行 author audit 和 capability parity tests。

如果需要保留完整历史，只能放在不进入 default branch contributor graph 的外部 reference surface。

## Verification Gates

Repo gates：

- `make test-meta`
- `scripts/verify.sh`
- owner-boundary tests
- runtime layout tests
- MDS capability parity tests
- study macro state / owner route contract tests
- runtime lifecycle SQLite authority contract tests
- canonical artifact rebuild and delivery authority tests
- workspace memory / learning no-authority tests
- contributor author audit
- `git diff --check`

Workspace gates：

- layout inventory ledger
- old path reader compatibility
- new path writer proof
- restore index and checksum proof
- live audit-only proof
- stopped/cold apply proof
- user-facing progress still reads the same study truth
- `study_macro_state` 与 `owner_route` 不被 historical reader / explicit archive import reference 或 SQLite runtime authority 反向覆盖
- `portfolio/research_memory`、incident learning 和 AI reviewer calibration 只作为 memory / observability 被消费
- `current_package`、`submission_minimal`、delivery README 和 archive export 不被当作 edit source 或 publication authority

Contributor gates：

- no unwanted upstream author in new MAS commits
- no upstream co-author trailers in MAS import commits
- GitHub default-branch contributor surface checked after push
- provenance retained outside contributor graph

## Definition Of Done

这个 program 当前 repo-level closeout 满足：

- `med-autoscience` 是唯一日常 repo 和唯一用户入口。
- 新 workspace 完全使用 MAS layout。
- 新 workspace 默认 no root Git / no quest Git；current workspace root Git 已经经 restore-proof full retirement 退出默认 workspace 状态面。
- 旧 workspace 有 migration ledger、compat export 和 restore proof。
- 新 quest materialization 不依赖 quest `.git`、`.ds/worktrees` 或旧 MDS path；旧路径只在 migration ledger、restore proof 或 maintainer diagnostic 中出现。
- MDS 独立 repo 不再是运行必需 owner。
- 所有保留的 DeepScientist 资产都位于 `legacy` / `compat` / `oracle` 语义下。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch` 等 MAS truth surface 不被 MDS 写回。
- GitHub contributor graph 不因 no-history import 出现上游 DeepScientist contributor。
- 真实论文线已经完成 current-project quest/root Git restore-proof cutover；后续真实论文 soak 仍按具体 study/runtime authority 单独验证，不作为 MDS 默认依赖回流条件。

## Non-Goals

- 不把 MDS 原始历史接入 MAS `main`。
- 不把 `.ds` 作为新 layout 的隐藏默认目录。
- 不用 MDS mechanical oracle 授权医学论文 ready。
- 不在 live quest 上做破坏性 layout migration。
- 不把文档计划写成 repo capability 或真实 workspace cutover 已完成。
