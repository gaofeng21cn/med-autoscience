# MAS Single-Project MDS Absorb Program

Status: `long-line execution program; L1 default workspace writer, doctor-visible layout, repo-level quest lifecycle replacement/inventory/diagnostic/cutover surfaces landed; current-project quest/root Git retired; profile/entry retirement landed; physical absorb pending`
Date: `2026-05-08`
Owner: `MedAutoScience`

## 结论

MAS 长线应成为唯一项目、唯一研究入口和唯一运行治理 owner；MDS 不应继续作为独立日常项目存在。目标不是把 `med-deepscientist` 原样搬进来，而是把 MDS 解构为 MAS 内部可验证能力：能被 MAS 直接拥有的能力进入 MAS owner 模块；仍需对照的能力降级为 oracle fixture；没有长期价值的入口、目录和命名退休。

这个 program 一步到位定义最终可用状态：repo、运行入口、真实论文 workspace layout、兼容导出、GitHub contributor footprint、验证与清理规则都必须一起收敛。执行可以并行开 worktree，但每条 lane 必须有明确 write set、验证和吸收顺序；没有 parity proof 和 rollback surface 的能力不得物理吸收。

2026-05-06 的状态管理与文件分层重构不改变本 program 的方向，但提高了吸收门槛：MDS 吸收必须同时尊重 `current truth`、SQLite runtime authority、workspace memory 和 canonical paper authority 四层边界。任何 lane 如果把运行索引、学习记忆、交付镜像或 MDS oracle 升格为 study / quality / publication truth，都不能进入 cutover。

2026-05-06 追加落地：新建 workspace 的默认 writer 已切到 MAS-first layout：`runtime/quests/`、`runtime/archives/`、`runtime/restore_index/`、`artifacts/runtime/` 与 `ops/mas/`。旧 `ops/med-deepscientist/runtime/quests/` 仍由 compatibility reader 和 Git ignore 规则识别，但不再是默认 scaffold 或新 writer 目标。

2026-05-07 当前进度判断：Git 退役已经完成 repo-side contract、默认 layout、SQLite authority 边界、workspace Git boundary guard、current eligible disease workspace 的 restore-proof storage compaction、SQLite lineage/snapshot/allocation writer、SQLite-only reader projection、plain quest materializer CLI、quest Git inventory、默认 fallback retirement、legacy runtime reader cutover、显式 legacy restore/import diagnostic、safe quest Git cutover CLI 和 workspace root Git retirement CLI。真实 workspace active-path cutover ledger 已推进到 NF-PitNET、AS biologics、HeRR、DM-CVD verified；DM-CVD 剩余 DM002/DM003 已在无 live worker 窗口经 `pause-runtime` 进入 safe state 后 archive/remove。后续论文项目默认 no root Git / no quest Git，不再接触 MDS/DS 路径、quest `.git` 或 `.ds/worktrees` 日常 lifecycle；NF-PitNET、DM-CVD / DPCC 和 AS biologics 的已有 workspace root Git 已按 restore-proof inventory/archive/remove/verify 退役，HeRR 原本 no root Git。剩余大项是 workspace 用户可见 layout 去 MDS/DS 化、profile/entry compatibility retirement 和 MDS 物理代码 no-history absorb。

2026-05-08 校准：近期模块化治理、runtime/control 边界和 progress projection 收口不要求调整本 program 的终局目标，也不需要新增“全仓重构”计划。`workspace_layout_de_mds_ds` 已处理 still-visible MDS/DS surfaces：`profiles/workspace.profile.template.toml` 改为 MAS-owned `runtime/quests` / `runtime`，doctor/show-profile 把旧 `med_deepscientist_*` 字段显示为 legacy diagnostic / backend-audit alias，bootstrap/quickstart/agent runtime 文档也对齐 no root Git / no quest Git / SQLite lifecycle / legacy diagnostic only。`profile_entry_compat_retirement` 已把默认入口继续收紧：MCP `doctor_audit` 只接受 `backend_upgrade`，旧 `med_deepscientist_upgrade` mode fail-closed；profile JSON 顶层不再直出 `med_deepscientist_*`，只在 `legacy_diagnostic.read_only` 暴露；workspace contract 改用 `managed_runtime_*` 与 `controlled_backend_*`；product-entry / progress 的默认 executor owner 改为 `controlled_research_backend`。物理 no-history absorb 仍不能提前开始；必须等 source provenance、author audit、capability parity fixtures、rollback surface 与 no-history import gate 成立。

## Program Coordination With Runtime Lifecycle Cutover

本文件是 MAS 吸收 MDS 的总执行计划；[Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) 是本计划下的 runtime persistence / quest Git retirement 子计划，不是另一条独立并行路线。

协同判断固定如下：

- MAS absorb 负责产品入口、owner 边界、代码归属、workspace layout、no-history import、真实项目 cutover 和 compatibility retirement。
- Runtime lifecycle SQLite program 负责 runtime lifecycle authority、lineage、workspace allocation、snapshot metadata、diff / Canvas read model、retention ledger、archive refs、restore proof 和 quest-level Git retirement。
- 两条线可以按 disjoint write set 并行实现，但必须共享同一 owner matrix、SQLite schema contract、migration ledger、restore proof 和 compatibility retirement gate。
- `runtime_lifecycle_sqlite_migration_program.md` 的 `Q0-Q6` lane 对应本计划的 `L3_runtime_absorb`、`L4_artifact_and_storage_absorb`、`L6_entrypoint_retirement` 和 `L8_real_workspace_cutover`；其中 `Q0_sqlite_authority_contract` 必须先于任何 Git writer / worktree writer 退役。
- 当前项目的 SQLite-backed runtime cutover 已完成到 quest/root Git retired 口径；MDS Git compatibility reader 不再是默认安全阀。后续只保留显式 legacy restore/import diagnostic 和 parity oracle，直到 profile/entry retirement 与 no-history absorb gates 完成。

Git 退役、真实 workspace layout 迁移和兼容接口退役是本 program 的加速子目标，可以先于 MDS 物理代码吸收完成。执行优先级固定为：

1. `Q1-Q4` 和 repo-default `Q6` 已进入 landed 口径：repo-level schema/writer/read-model/plain materializer、inventory、legacy diagnostic、default fallback retirement 和 default reader cutover 已可用。
2. `Q5` 已完成 current-project active-path cutover：registry-discovered 真实 workspace 已有 Git-era inventory、safe cutover apply、restore-proof archive、projection verification 和 controller-authorized cutover ledger。
3. 项目级 `Q6` 已完成 default runtime path closeout：默认 fallback 已删除，只保留显式 `restore_legacy_git_archive` / `import_legacy_git_archive` 诊断入口。
4. 后续论文项目按 MAS-only workspace 规则展开：新 scaffold 无 `ops/med-deepscientist`、无 `.ds` 默认目录、无 quest `.git` 日常 lifecycle，也无 workspace root Git 默认要求；用户/医生可见路径已按 MAS-owned layout 显示。

后续 program portfolio 管理见 [Program Portfolio Consolidation](./program_portfolio_consolidation.md)。新增长线计划必须先映射到该 portfolio 的 active owner doc；不得再新建一套 runtime authority、lineage 或 projection 管理路线。

当前执行队列由 portfolio 固定为：no-history physical absorb readiness -> no-history physical absorb。workspace root Git full retirement、workspace layout de-MDS/DS 和 profile/entry compatibility retirement 已由 runtime lifecycle / layout / compat 子计划执行并把 ledger / proof 回写到本 program 的 workspace cutover gate。

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
| `L2_mds_inventory_and_classification` | `codex/mas-mds-capability-inventory` | migration inventory tooling、capability matrix、source snapshot manifest | 盘点 MDS 能力，逐项标记 `absorb` / `oracle` / `retire`。 |
| `L3_runtime_absorb` | `codex/mas-runtime-os-absorb` | Runtime OS、runtime_protocol、recovery tests | 吸收 execution/recovery/quest lifecycle，保留 MDS trace replay oracle。 |
| `L4_artifact_and_storage_absorb` | current-project storage/Git retirement landed | Artifact OS、runtime lifecycle SQLite、storage migration tests | 吸收 artifact inventory、storage audit、cold archive / restore proof，同时保持 canonical paper truth 优先；quest Git inventory / safe cutover CLI 已落地，真实 workspace Q5/Q6 ledger 已完成。 |
| `L5_quality_oracle_absorb` | `codex/mas-quality-oracle-absorb` | Quality OS、publication eval、AI reviewer fixtures | paper health / coverage 变成 mechanical oracle，不授权 ready。 |
| `L6_entrypoint_retirement` | profile/entry retirement landed | CLI/MCP/product-entry/skill docs/tests | MCP legacy doctor audit mode、profile JSON 旧字段直出、workspace contract 旧命名、product/progress 默认 executor owner 已退到 legacy diagnostic / controlled backend audit；MDS product entry 不再是默认入口。 |
| `L7_contributor_and_license_guard` | `codex/mas-no-history-import-guard` | scripts/tests/docs/legal or provenance records | no-history import guard、author audit、license/provenance snapshot。 |
| `L8_real_workspace_cutover` | quest Git, workspace root Git, user-visible layout and profile/entry compatibility cutover landed for current projects / new scaffold | real workspace migration ledgers only | NF-PitNET、DM-CVD、DPCC 等 workspace dry-run、apply、compat export、restore proof 已完成 quest `.git` active-path retirement；NF-PitNET、DM-CVD / DPCC 和 AS biologics 已完成 workspace root Git restore-proof retirement，HeRR 原本 no root Git；后续聚焦 no-history physical absorb readiness。 |

## Execution Order

1. `L0` 先吸收，作为所有后续 lane 的 contract baseline。
2. `L1`、`L2`、`L7` 可并行；它们分别冻结 layout、inventory 和 contributor guard。
3. `L3`、`L4`、`L5` 依赖 `L1/L2`，可以按 disjoint write set 并行。
4. `L6` 只能在 MAS 入口 parity 通过后执行。
5. `L8` 只能在 repo capability 通过后对真实 workspace 做 controller-authorized migration。

## Workspace Layout Migration Rule

新 workspace：

- 默认生成 `portfolio/research_memory/`、`studies/<study_id>/artifacts/controller/`、`studies/<study_id>/artifacts/runtime/`、`studies/<study_id>/paper/`、`studies/<study_id>/manuscript/`、`artifacts/runtime/runtime_lifecycle.sqlite`、`runtime/quests/`、`runtime/archives/`、`runtime/restore_index/`、`ops/mas/`。
- 不生成 `.ds`、`ops/med-deepscientist` 或 MDS-first path。
- 不默认初始化 workspace root Git；root Git 不接管 runtime、quest、delivery 或 publication truth。维护者若通过 legacy restore diagnostic 临时恢复 root Git，必须重新走 restore-proof retirement 或明确留在外部 maintenance audit，不得让它回到默认状态面。
- Agent 查状态、做 lifecycle 操作或恢复 runtime 时，不读取 root Git / quest Git 作为默认状态面；优先使用 file authority、`study_macro_state` / `owner_route`、`artifacts/runtime/runtime_lifecycle.sqlite`、`artifacts/runtime/lifecycle_migration` ledger、`runtime/quests` manifest 和 `runtime/restore_index`。
- `study-progress`、`runtime_watch`、`product-entry-status`、MCP 都只暴露 MAS layout，并按 file authority -> macro state / owner route -> SQLite runtime authority -> compatibility reader 的顺序读取。
- `init_workspace` dry-run 和 apply 都应体现上述目录；`watch-runtime` 默认指向 `${WORKSPACE_ROOT}/runtime/quests`，workspace-level Git 默认忽略 `runtime/quests/`、`runtime/archives/**`、`runtime/restore_index/**` 和 `artifacts/runtime/`。
- `runtime quest-materialize --workspace-root <workspace> --quest-id <quest> --node-id <node>` 是 repo-level plain quest materializer 入口；apply 只创建 `runtime/quests/<quest_id>` 普通目录和 `artifacts/runtime/materialization_manifest.json`，manifest 必须记录 `git_runtime_used=false`、`quest_git_active_path_retired=true`，旧 `ops/med-deepscientist/runtime/quests/<quest_id>` 只能作为 read-only legacy source。
- 如果 active quest root 已存在 `.git`，quest materializer 必须 fail-closed 为 `blocked/audit_only`，直到维护者通过 legacy diagnostic / restore proof 处理；不得把既有 Git repo 接回 active lifecycle。

旧 workspace：

- 第一次 maintenance 生成 `artifacts/runtime/layout_migration/latest.json`。
- live quest 只允许 audit/index，不移动或删除。
- stopped/cold quest 允许 dry-run、archive、restore proof、compat export、apply。
- 旧 `.ds` 内容迁入 `runtime/archives/` 或 `runtime/quests/` 后，必须写 restore index、source checksum、compatibility reader proof。
- old reader 必须能解释旧路径，但新 writer 不得继续写旧路径。
- 旧路径里的 paper package、memory、runtime report 或 artifact inventory 只能迁入对应 MAS layer；不能平铺进一个通用 legacy bucket 后继续被多个入口各自解释。
- 未来若发现外部/旧 workspace 仍带 root Git，必须完成 inventory、archive、restore command、sha256 和 verify ledger 后才允许 remove；有 remotes、locks 或 linked worktrees 时继续 block 到 maintainer audit。root Git 不再作为 MAS workspace 的可选日常维护模式。

## Repo Import Rule

所有从 MDS 进入 MAS 的代码必须走 snapshot import：

1. 从受控 MDS ref 生成 source snapshot。
2. 删除不吸收的 provider/UI/global skill/old product entry。
3. 写 `source_provenance.json`，包括 upstream repo/ref、snapshot sha256、license refs、capability classification。
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
- `study_macro_state` 与 `owner_route` 不被 legacy reader 或 SQLite runtime authority 反向覆盖
- `portfolio/research_memory`、incident learning 和 AI reviewer calibration 只作为 memory / observability 被消费
- `current_package`、`submission_minimal`、delivery README 和 archive export 不被当作 edit source 或 publication authority

Contributor gates：

- no unwanted upstream author in new MAS commits
- no upstream co-author trailers in MAS import commits
- GitHub default-branch contributor surface checked after push
- provenance retained outside contributor graph

## Definition Of Done

这个 program 完成时必须同时满足：

- `med-autoscience` 是唯一日常 repo 和唯一用户入口。
- 新 workspace 完全使用 MAS layout。
- 新 workspace 默认 no root Git / no quest Git；current workspace root Git 已经经 restore-proof full retirement 退出默认 workspace 状态面。
- 旧 workspace 有 migration ledger、compat export 和 restore proof。
- 新 quest materialization 不依赖 quest `.git`、`.ds/worktrees` 或旧 MDS path；旧路径只在 migration ledger、restore proof 或 maintainer diagnostic 中出现。
- MDS 独立 repo 不再是运行必需 owner。
- 所有保留的 DeepScientist 资产都位于 `legacy` / `compat` / `oracle` 语义下。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch` 等 MAS truth surface 不被 MDS 写回。
- GitHub contributor graph 不因 no-history import 出现上游 DeepScientist contributor。
- 真实论文线至少完成一个 stopped/cold workspace apply 和一个 live workspace audit-only 验证。

## Non-Goals

- 不把 MDS 原始历史接入 MAS `main`。
- 不把 `.ds` 作为新 layout 的隐藏默认目录。
- 不用 MDS mechanical oracle 授权医学论文 ready。
- 不在 live quest 上做破坏性 layout migration。
- 不把文档计划写成 repo capability 或真实 workspace cutover 已完成。
