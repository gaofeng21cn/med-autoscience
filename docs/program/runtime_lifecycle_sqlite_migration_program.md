# Runtime Lifecycle SQLite Migration Program

Status: `current workspace restore-proof migration applied; default MAS-first layout landed`
Date: `2026-05-06`
Owner: `MedAutoScience Runtime OS + MedDeepScientist backend`

## 2026-05-05 restore-proof closeout

本轮在用户确认所有论文 runtime 已处于停止/暂停窗口后完成 current disease workspaces 的 runtime bucket compaction。迁移范围覆盖 NF-PitNET、DM-CVD / DPCC、AS biologics 的 eligible quest；当时 DM002 与 DM003 的盘面 `runtime_state.status` 仍为 `active`，但 `active_run_id=null`，本轮按用户明确确认的 operator-confirmed parked active gate 处理。整个过程中没有 relaunch、resume 或 redrive 任一 study runtime。

本轮仍保留以下边界：

- SQLite 是 runtime/state index layer，继续不替代 Git、paper authority、publication authority 或 artifact authority。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、DOCX/PDF/ZIP、dataset manifest 和 paper/manuscript/package surface 未被迁移过程手工 patch。
- DM001 不应出现 live writer；本轮只迁移其 parked/reentry 与 legacy quest runtime payload。如果后续 MAS/MDS 对 DM001 再显示写入者或自动恢复意图，应归类为状态机问题，而不是迁移任务。
- DM002/DM003 的 `active/null-run` 只因本轮用户确认进入可迁移窗口而放行；通用规则仍是 active quest 必须有 `active_run_id=null` 且显式传入 operator-confirmed gate，不能默认 destructive compaction。2026-05-06 follow-up 前曾发现 DM002/DM003 手动暂停后被外层 watch 自动拉起；该状态机问题由单独会话修复后，本轮重新 fresh gate，确认 DM002 `stopped`、DM003 `paused` 且均为 `active_run_id=null` / `worker_running=false`，再执行 destructive compaction。
- `/Users/gaofeng/workspace/Yang/无功能垂体瘤` 继续只是本机轻量中文 stale alias/scaffold，不作为独立 NF-PitNET workspace。
- repo 默认 workspace layout 已切到 MAS-first：新建 workspace 写 `runtime/quests/`、`runtime/archives/`、`runtime/restore_index/`、`artifacts/runtime/` 与 `ops/mas/`；旧 `ops/med-deepscientist/runtime/quests/` 仅保留兼容读取、restore proof 和 Git ignore。

本轮真实 workspace closeout ledger：

- `/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/artifacts/runtime/lifecycle_migration/runtime-lifecycle-20260505-current-workspace-restore-proof-closeout.json`
- `/Users/gaofeng/workspace/Yang/NF-PitNET/artifacts/runtime/lifecycle_migration/runtime-lifecycle-20260505-current-workspace-restore-proof-closeout.json`
- `/Users/gaofeng/workspace/LinZM/as_biologics_workspace/artifacts/runtime/lifecycle_migration/runtime-lifecycle-20260505-current-workspace-restore-proof-closeout.json`

## 2026-05-06 post-closeout drift note

closeout ledger 证明的是当轮 eligible payload 已完成 restore-proof compaction，不代表之后 live runtime 不会再写入 `.ds`。2026-05-06 用户确认 DPCC004 没有在跑，因此本轮已单独 repeat-compact DPCC004。随后用户确认 DM002/DM003 的手动暂停后自动拉起问题已修复，本轮完成 DM002/DM003 post-closeout follow-up compaction。

| study / quest | current runtime state | current `.ds` files | migration handling |
| --- | --- | ---: | --- |
| DM002 `002-dm-china-us-mortality-attribution` | `stopped`, `active_run_id=null`, `worker_running=false` | 58 | 2026-05-06 follow-up compaction done；fresh gate baseline `20,185` files / `6.5G`，final `58` files / `6.3G`；new restore proofs verified `17,966/17,966` + `2,170/2,170` + `2,813/2,813`，errors `0`。 |
| DM003 `003-dpcc-primary-care-phenotype-treatment-gap` | `paused`, `active_run_id=null`, `worker_running=false` | 52 | 2026-05-06 follow-up compaction done；fresh gate baseline `16,226` files / `4.7G`，final `52` files / `4.5G`；new restore proofs verified `14,159/14,159` + `2,025/2,025` + `736/736`，errors `0`。 |
| DPCC004 `004-dpcc-longitudinal-care-inertia-intensification-gap` | `paused`, `active_run_id=null`, `worker_running=false` | 292 | 2026-05-06 repeat-compaction done；restore proof verified `24,403/24,403`，errors `0`；quest-local `artifacts/runtime/runtime_lifecycle.sqlite` 已从嵌套 Git index 退役并加入 ignore。 |
| NF-PitNET managed 001-004 + legacy roots | paused/completed/null-run mix | 129 relevant files | 保持已处理状态；无需把中文 alias 作为独立 workspace。 |
| AS001 `001-guideline-aligned-triple-trend` | `stopped`, `active_run_id=null`, `worker_running=false` | 56 | 保持已处理状态。 |

因此，当前回答“最初计划是否已经落地”时应区分两个口径：repo capability 已落地；真实 workspace 迁移也已覆盖 NF-PitNET、DM-CVD / DPCC、AS biologics 和当前 follow-up 窗口中的 DM002/DM003 新增 payload。后续若任何论文 runtime 再产生 `.ds` 增量，应按同一 fresh gate + restore-proof compaction 流程维护，不能把新增 live writer 漂移写成迁移计划未完成。

## 结论

引入 SQLite 可行，也有必要。目标形态是 `SQLite runtime authority + file truth authority + Git source control`：Git 继续管理源码、合同、文档和可审阅配置；MAS/MDS 的 publication/study authority surface、restore metadata、paper/manuscript/package/dataset 交付物继续保持文件形态；SQLite 负责 runtime lifecycle 的状态、lineage、workspace allocation、snapshot metadata、索引、历史、游标、摘要、retention ledger 和 compact projection。

这条线应直接按长线目标推进，不按一次只做一个小阶段推进。实现上可以并行展开多个 worktree，但所有 lane 必须共享同一 schema/authority contract，并在吸收回 `main` 前完成兼容导出、真实 workspace dry-run、验证和清理。

## 一步到位目标

本 program 的目标不是只补一个索引文件，也不是只清理某个异常 workspace。完成后的可用状态必须同时满足：

- MAS/MDS repo 已有统一 lifecycle schema、读写 contract、compatibility export、migration CLI / MCP surface、guardrail 和验证入口。
- 所有当前项目先进入 registry-backed inventory，再按 `live_active`、`parked_controller_stop`、`stopped_cold`、`pinned_or_unknown_owner`、`archived_workspace` 分类。
- 所有 eligible stopped/cold quest 完成 baseline、dry-run、apply、compatibility export、restore proof 和 final ledger；所有 live / pinned / unknown owner quest 有明确 skipped reason。
- 旧入口仍能读取 latest authority files、runtime status、storage audit、package locator 和 study progress；新入口能从 SQLite 读取 history、cursor、retention ledger、bucket summary 和 archive refs。
- SQLite runtime DB 的 paper/study truth 影响必须可由文件 authority / archive / export 流程解释；DB 损坏时至少能由 ledger、restore index、archive refs 和 compatibility export 重建 runtime projection。任何不可重建的 publication/study/artifact truth 仍保留在文件 authority 或归档 authority 中。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、DOCX/PDF/ZIP、dataset manifest、restore index 不被迁移过程手工 patch。

后续 Agent 不应把“repo capability landed”写成“项目迁移已完成”。只有真实 workspace ledger、file-count delta、restore proof 和 compatibility verification 都存在时，才能声明某个项目迁移完成。

## 当前问题

百万级文件主要来自 `.ds` 运行态，而不是 Git 源码仓本身。高风险桶包括：

- `bash_exec`：shell session 的 `log.jsonl`、`terminal.log`、`monitor.log` 等。
- `runs`：每个 runtime run 的 prompt、stdout、command、telemetry、状态片段。
- `codex_homes`：每轮隔离 Codex home 的 config、skills、prompts、sessions、tmp。
- `codex_history`：Codex event mirror。
- `worktrees`：expanded paper/research worktree、runtime payload mirror。
- `cold_archive` / `slim_backups`：归档与 restore 成本。
- MAS workspace 侧的 runtime-watch report、storage audit、storage governance history、feedback/action/runtime telemetry 等 timestamped history。

当前已落地的能力包含索引层与 current workspace restore-proof compaction：

- MAS：`artifacts/runtime/runtime_lifecycle.sqlite` 记录 runtime watch state、runtime report、workspace storage audit。
- MDS：`.ds/runtime_index.sqlite` 记录 maintenance run、bucket snapshot、archive ref 与 metadata。
- restore-proof archive：eligible quest 的 `bash_exec`、`runs`、`codex_history`、`codex_homes`、`worktrees` 等 runtime payload 被归档到 `.ds/restore_proof_archives/runtime_bucket_compaction/`，并写入 manifest、archive sha256、restore proof 与 archive ref。
- 默认新 scaffold：`runtime/quests/` 承接 live quest root，`runtime/archives/` 与 `runtime/restore_index/` 承接归档和恢复索引，`artifacts/runtime/` 承接 SQLite runtime DB 与 migration ledger；外层 Git 默认排除这些 generated/runtime 面。

这层能力已经显著降低 current eligible quest 的 `.ds` 小文件数量。后续新增 runtime 对象仍必须继续把 event/run/bash/codex history 的历史 metadata 与 cursor 查询迁入 SQLite，同时把原始大 payload 合并成 gzip/tar/cold archive，并由 SQLite 记录 archive ref、checksum、byte count 与 restore contract。

## 工程依据

SQLite 官方把带 schema 的数据库文件定位为适合持久化应用状态的单文件应用格式，核心能力包括单文件文档、事务更新、增量更新、并发读取和跨语言访问；这与 MAS/MDS 的 runtime lifecycle 索引需求一致。

SQLite 官方小对象基准显示，把大量小 blob 放入数据库可减少 open/close 和 filesystem block padding 成本；这个结论不能直接等价为所有 MAS/MDS payload 都应该进 SQLite，但它支持把大量小元数据、摘要、游标和 compact projection 从散落文件迁入 SQLite。

SQLite WAL 支持读写并发和顺序写入，但同一 WAL 数据库要求在同一 host 上使用，不适合网络文件系统上的跨主机共享写入。因此 MAS/MDS 的 SQLite runtime DB 必须是 workspace-local / quest-local，不作为跨主机中心服务。

SQLite Archive / SQLAR 证明 SQLite 可作为小文件容器，但本 program 不把 SQLite 提升为默认 blob archive。MAS/MDS 默认仍用 gzip/tar/cold archive 保存原始大 payload；SQLite 记录索引与恢复引用。

Git 的 untracked-cache、fsmonitor、sparse-checkout / sparse-index 可以降低 Git working tree 和 index 扫描成本。它们不能解决 MAS/MDS 自己在 `.ds` 内生成的 runtime 小文件生命周期，所以只能作为 Git 兼容优化，而不是本问题的核心解法。

参考：

- SQLite Application File Format: `https://www.sqlite.org/appfileformat.html`
- SQLite Faster Than The Filesystem: `https://www.sqlite.org/fasterthanfs.html`
- SQLite WAL: `https://www.sqlite.org/wal.html`
- SQLite Archive Files: `https://www.sqlite.org/sqlar.html`
- Git worktree: `https://git-scm.com/docs/git-worktree`
- Git bundle: `https://git-scm.com/docs/git-bundle`
- Git update-index: `https://git-scm.com/docs/git-update-index`
- Git sparse-index: `https://git-scm.com/docs/sparse-index`
- Fossil Technical Overview: `https://fossil-scm.org/home/doc/trunk/www/tech_overview.wiki`

## 权威边界

SQLite runtime authority 只能持有 runtime lifecycle 与 read-model 内容：

- append-heavy runtime telemetry 与 historical report index。
- quest lineage、workspace allocation、snapshot metadata、revision diff summary 和 Canvas projection。
- event/run/bash/codex session metadata、状态、cursor、摘要和路径引用。
- retention action ledger、archive ref、checksum、byte count、restore instruction ref。
- workspace storage audit 的 summary、bucket totals、趋势和 migration proof。
- read-model cache、分页索引、compatibility export provenance。

必须继续保留为文件的内容：

- `runtime_binding.yaml`
- `.ds/runtime_state.json` 的 latest mirror，至少在迁移期保留。
- `study_runtime_status`
- `runtime_watch` latest human-readable report。
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- `runtime_escalation_record.json`
- dataset manifest、restore index、checksum manifest。
- `paper/`、`manuscript/`、`current_package/`、`current_package.zip`、DOCX/PDF/图片/表格等交付物。
- 原始 terminal/stdout/Codex session payload 的 gzip/tar/cold archive。
- Git-tracked 源码、测试、文档、合同与配置。

和 L5 audit compaction 的关系：

- 本 program 落地 runtime lifecycle 的 SQLite index、retention ledger、archive refs、compatibility export 和 restore proof；这些是 `L5_natural_boundary_and_audit_compaction` 的前置证据来源之一。
- 本 program 不替代 `mas_l5_audit_compaction_governance`，也不把 maintainability read model 提升为 runtime / study / publication / delivery truth writer。
- 本文里的 stopped/cold `archive compaction` 只指 runtime payload 迁移动作，不等同于 audit_log 大桶治理、结构拆分或 worktree cleanup。
- 若同一 workspace 同时进入 SQLite migration 和 audit compaction，执行顺序固定为 migration ledger / restore proof / compatibility export 先成立，再由 L5 maintainability lane 判断是否允许压缩旧 audit bucket。

禁止事项：

- 不把 SQLite 写成 publication readiness、scientific quality、submission authority 或 artifact authority。
- 不把 SQLite DB 文件纳入 Git 跟踪。
- 不把 SQLite 当作默认巨型 blob store。
- 不在 live quest 上执行破坏性 compaction；live quest 只能 audit/index。
- 不手工 patch `current_package`、`publication_eval/latest.json` 或 `controller_decisions/latest.json` 作为迁移完成证明。

## 文件数量收益预估

收益要按 workspace 和 quest 实测。当前可给出的工程估计如下：

| 层级 | 改动 | 预期文件数影响 | 主要收益 |
| --- | --- | --- | --- |
| `index_only` | 写 SQLite sidecar，同时保留现有文件 | `0-5%` | 查询、审计、定位、后续迁移 proof |
| `history_indexed` | runtime report、storage audit、feedback/action/history 进入 SQLite，保留 latest mirror | `10-30%` | 减少 timestamped report 与 ledger 小文件增长 |
| `event_compacted` | `runs`、`bash_exec`、`codex_history` 的历史元数据进 SQLite，原始 payload 合并为 gzip/tar | `30-70%` | 减少 per-run / per-session 小文件枚举 |
| `cold_payload_archived` | stopped/cold quest 的 expanded payload 与 worktree runtime mirror 归档，SQLite 记录 archive refs | `70-95%` | 明显降低 `.ds` 文件数量与 Finder/Git/rg/du 扫描压力 |
| `workspace_migrated` | 所有 stopped/cold study 完成 dry-run、apply、restore proof 和 compatibility export | 以真实 baseline 为准 | 保持兼容同时减少长期维护成本 |

这些百分比是迁移目标，不是当前已完成事实。后续 Agent 必须先生成 baseline，再报告每个 workspace 的 `files_before`、`files_after`、`bytes_before`、`bytes_after`、`largest_buckets` 和 `skipped_live_or_pinned`。

## Git 兼容策略

Git 继续承担 source control，不承担 runtime lifecycle database authority。

- Repo 侧跟踪代码、测试、文档、schema contract、migration CLI 与 compatibility export 逻辑。
- Workspace 外层 Git 继续保持轻量，generated/runtime/artifact 默认排除，只保留 README、manifest、rules、source contract 这类可审阅文件。
- SQLite runtime DB、WAL、SHM、临时 checkpoint 文件必须在 workspace/runtime `.gitignore` 中排除。
- 旧脚本和旧 Agent 继续读取 latest 文件 mirror；新 reader 优先读 SQLite，没有 SQLite 时只允许进入明确的 compatibility fallback，不得产生第二套 truth。
- 导出命令必须能从 SQLite 重建旧 JSON/Markdown report 形态，用于人工审阅、debug 和历史工具兼容。
- Git 优化项只作为辅助：大型 tracked 源码仓可继续使用 sparse-checkout / sparse-index；runtime `.ds` 文件数量问题必须由 SQLite index + archive/retention policy 解决。

### Quest-level Git retirement and SQLite runtime authority cutover

目标判断：SQLite 可以接管 MDS 目前借 Git 实现的 runtime lifecycle 语义，包括 research route lineage、workspace allocation、checkpoint/revision metadata、diff/read-model 和 Canvas projection。Git 仍然适合源码版本控制，但不应继续作为 quest runtime lifecycle 基础设施。

当前事实：2026-05-06 fresh audit 结论仍成立，workspace 外层 Git 主要服务 Codex 检索性能和 `.gitignore` 边界；MDS quest-level Git 当前仍被 `init_repo`、`checkpoint_repo`、`prepare_branch`、`activate_branch`、Git diff/log/revision reader 和 `.ds/worktrees` 直接使用。后续工作目标不是长期维护这套机制，而是一次性完成 SQLite authority cutover，迁移所有当前项目，验证后退役 quest-level Git compatibility layer。

工程依据：

- SQLite 官方将带 schema 的数据库文件定位为 application file format，适合持久化应用状态，提供单文件、事务、查询、跨平台和多进程并发读取能力。
- SQLite 小对象读写可避免大量 per-file open/close 开销；官方 small-blob 测试显示 SQLite 在许多场景比散文件更快且更省空间，但也提醒冷缓存/具体硬件可能不同。因此 MAS/MDS 只把 metadata、summary、cursor、ledger、小型 read-model 放入 SQLite，大 payload 继续归档为 tar/gzip/SQLAR。
- SQLite WAL 模式要求把 `-wal` 与主 DB 视为同一持久状态的一部分；MAS/MDS 必须使用 workspace-local / quest-local DB、backup API 或 clean checkpoint，不把 WAL/SHM 纳入 Git。
- Git 官方 worktree 文档说明，手工删除 linked worktree 会留下 repository admin metadata，需要 `git worktree prune` 清理；这正是当前 `.ds/worktrees` compaction 后出现大量 stale listed worktrees 的机制原因。
- Fossil 的成熟工程经验可借鉴：SQLite DB 可以保存 repository metadata 和 query read-model；canonical artifacts 与可重建 metadata 分层，metadata schema 可 rebuild。MAS/MDS 采用同样原则：医学/论文 truth 仍在 file authority 与 restore-proof archive，SQLite 保存 runtime authority 与可重建 projection。

目标三层：

| layer | owner | 目标职责 | 文件形态 |
| --- | --- | --- | --- |
| SQLite runtime authority | MAS/MDS runtime | lifecycle state、lineage graph、workspace allocation、checkpoint metadata、diff summary、cursor、retention、archive refs、Canvas read-model | `artifacts/runtime/runtime_lifecycle.sqlite` 与 quest/workspace-local DB |
| Memory / runtime knowledge | MAS/MDS runtime + agent memory | interaction summary、decision rationale、resume packet、agent handoff、session/codex/bash summaries | SQLite rows + compact JSON export；大 payload archive ref |
| Paper / study truth | MAS controller / publication authority | `publication_eval/latest.json`、`controller_decisions/latest.json`、study charter、manuscript、figures、tables、submission package、dataset manifest | 文件 authority、tar/gzip restore-proof archive、latest mirror |

Git 退役后的 runtime 对应关系：

| Git-era 概念 | SQLite-era authority | payload / materialization |
| --- | --- | --- |
| branch 表示 idea/run/paper/analysis route | `lineage_nodes` + `lineage_edges`，带 `node_kind`、`parent_node_id`、`route_state`、`study_id`、`quest_id` | 当前 active node 可导出为 JSON/Markdown route packet |
| worktree 表示隔离执行目录 | `workspace_allocations`，记录 `workspace_id`、`node_id`、`root_ref`、`state`、`pinned_until` | 普通目录或 archive rehydrate 目录，不再要求 Git linked worktree |
| commit/checkpoint 表示可回看快照 | `runtime_snapshots` + `snapshot_file_refs`，记录 manifest、content hash、archive ref、authority surfaces checked | 小文件可 SQLAR；大目录 tar/gzip；paper truth 继续文件 authority |
| Git diff/log 支撑状态视图 | `revision_diffs` + `event_log` + `canvas_nodes` / `canvas_edges` | diff summary、changed path manifest、optional text patch archive |
| Git refs/worktree list 支撑 Canvas | `canvas_projection` read-model，可由 lineage/events/snapshots rebuild | `compat_exports/canvas.latest.json` 只作为导出面 |

一步到位 cutover program：

| lane | branch 建议 | 写入范围 | 目标 |
| --- | --- | --- | --- |
| `Q0_sqlite_authority_contract` | `codex/quest-sqlite-authority-contract` | MAS/MDS schema contract、docs、contract tests | 固定 replacement schema、authority matrix、Git-era to SQLite-era mapping、migration ledger、compat retirement gate。 |
| `Q1_mds_lineage_store` | `codex/mds-lineage-sqlite-store` | MDS artifact service / gitops adapter / tests | 将 `prepare_branch`、`activate_branch`、`create_analysis_campaign`、`checkpoint_repo` 迁到 SQLite lineage/snapshot service；禁止新 quest 默认 `git init`。 |
| `Q2_workspace_materializer` | `codex/mds-sqlite-workspace-materializer` | MDS workspace allocation / runtime storage / restore tests | 用普通目录 + manifest/archive rehydrate 替代 Git linked worktree；active/pinned/recent workspace 由 SQLite gate 管理。 |
| `Q3_canvas_and_reader_projection` | `codex/mds-sqlite-canvas-reader` | MDS diff/canvas/read APIs、MAS cockpit/read surfaces | Canvas、branch list、revision document reader 改读 SQLite projection；旧 JSON/Markdown export 只由显式 compatibility export 生成。 |
| `Q4_project_git_to_sqlite_migrator` | `codex/quest-git-to-sqlite-migrator` | migration CLI、fixture tests、real workspace ledger | 对现有 quest Git refs/log/worktrees/artifacts 做 inventory、import、archive proof、SQLite projection verification。 |
| `Q5_current_workspace_cutover` | `codex/current-quest-git-retirement` | 真实 workspace migration ledger；不改 paper truth | NF-PitNET、DM-CVD/DPCC、AS biologics、registry-discovered workspace 全部迁入 SQLite runtime authority；quest `.git` 生成 restore-proof archive 后移出 active path。 |
| `Q6_compat_layer_retirement` | `codex/mds-git-compat-retirement` | MDS compatibility adapter、tests、docs/status | 所有 current projects 完成 cutover 后删除 default Git path、compat fallback 和 stale Git tests；保留只读 restore/import 工具。 |

吸收策略：`Q0` 必须先吸收；`Q1/Q2/Q3` 可在不重叠 write set 下并行；`Q4` 可先做 read-only inventory，然后在 `Q1-Q3` capability ready 后启用 apply；`Q5` 只写真实 workspace ledger 和 archive，不改医学/论文 truth；`Q6` 是最后吸收点，只有当前所有项目 cutover verified 后执行。

迁移算法：

1. Fresh inventory：枚举所有 MAS workspace、MDS quest roots、quest `.git`、branch/ref、worktree list、missing worktree paths、commit/log、artifact records、current authority surfaces、SQLite runtime DB 状态。
2. Import Git-era lineage：把 branch/ref/log/worktree/artifact records 归一到 `lineage_nodes`、`lineage_edges`、`workspace_allocations`、`runtime_snapshots`、`revision_diffs`、`canvas_projection`。
3. Snapshot and archive：对每个 terminal/stopped/cold quest 生成 refs manifest、commit manifest、Git bundle 或 fast-export archive、sha256、restore command、`git fsck --connectivity-only` proof。
4. Materialize active state：为每个 reopenable quest 生成 SQLite-backed active workspace manifest；如需要继续运行，只通过 workspace materializer 还原普通执行目录。
5. Compatibility proof：用 SQLite projection 重建旧 branch list、Canvas、runtime status、latest export，与 Git-era reader 输出做结构等价校验。
6. Retire active Git：cutover verified 后，将 quest `.git` 移入 restore-proof archive 或删除 active copy；active quest root 不再是 Git repo。
7. Retire code compatibility：所有 current projects verified 后，删除 default Git writer、Git worktree writer、Git diff/log runtime reader；保留只读 archive import / restore diagnostic。

当前项目完成门槛：

- 每个 discovered project 都有 `inventory`、`import`、`archive`、`projection_verify`、`cutover` 或明确 `skipped_reason`。
- NF-PitNET、DM-CVD/DPCC、AS biologics 的已迁移 quest `.ds` 保持几十到数百文件级；quest `.git` 不再留在 active runtime path。
- DM001/DM002/DM003/DM004 等曾发生状态机漂移的项目必须 fresh 判定 `active_run_id=null` / `worker_running=false` 或 controller-owned parked state 后才能 cutover active Git。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper/manuscript/package/dataset manifest 不被迁移过程手工 patch。
- 旧 reader 的所有必要输出都能从 SQLite projection 显式 export；普通 runtime 不再隐式写 Git/branch/worktree。
- `git worktree list` 在 active quest path 不再是 runtime status source；残留 Git archive 只用于 restore diagnostic。

兼容性退役门槛：

- 新建 quest 默认没有 quest-level `.git`，且 runtime smoke 能完成 idea/run/analysis/paper route、workspace allocation、snapshot、Canvas projection。
- MDS/MAS focused tests 证明 Git writer 不在默认路径：`git init`、`git branch`、`git worktree add`、`git log` 不再作为 runtime writer/read-model 前置条件。
- 当前所有项目 cutover ledger verified，restore proof errors 为 `0`，SQLite projection 与 legacy export 结构等价。
- Repo 中 Git compatibility adapter 只剩 `restore_legacy_git_archive` / `import_legacy_git_archive` 这类显式诊断入口；默认 CLI/MCP/controller 不调用。
- `docs/status.md` 明确记录 `quest_git_retired_for_current_projects=true` 后，才允许删除 compatibility tests 和 old Git lifecycle docs。

## 目标 schema 轮廓

所有 schema 必须显式 versioned，并支持只读 introspection。

共享合同必须先于并行实现落地。所有 lane 在写代码前必须引用同一份 contract，并保持以下字段语义稳定：

- identity：`workspace_id`、`study_id`、`quest_id`、`run_id`、`active_run_id`、`session_id`、`object_kind`。
- ownership：`authority_owner`、`source_repo`、`source_surface`、`write_owner`、`migration_owner`。
- lifecycle：`lifecycle_state`、`started_at`、`finished_at`、`last_seen_at`、`cold_since`、`skipped_reason`。
- file metrics：`files_before`、`files_after`、`bytes_before`、`bytes_after`、`bucket_name`、`bucket_policy`。
- archive refs：`archive_path`、`archive_format`、`sha256`、`source_path`、`restore_index_path`、`restore_command_ref`。
- compatibility：`latest_mirror_path`、`export_path`、`export_format`、`exported_at`、`compatibility_fallback_used`。
- migration proof：`migration_run_id`、`mode`、`gate_result`、`rollback_plan_path`、`restore_proof_path`、`verified_at`。

路径字段默认使用 workspace-relative 或 quest-relative path。只有 host-local runtime binding 可记录绝对路径，且必须同时写入 moved-workspace repair hint。

核心表：

- `schema_migrations`：schema version、applied_at、code_version。
- `runtime_objects`：workspace、study、quest、run、session、artifact 的稳定 identity。
- `lineage_nodes`：idea、run、analysis、paper、decision、checkpoint 的 runtime route node。
- `lineage_edges`：parent/child、derived_from、supersedes、continues、reopens 等 route relation。
- `workspace_allocations`：node 到普通执行目录、materialized archive、active/pinned/recent state 的映射。
- `runtime_snapshots`：snapshot id、manifest hash、archive ref、authority surfaces checked、restore proof。
- `snapshot_file_refs`：snapshot 内 path、content hash、size、storage class、archive ref。
- `revision_diffs`：changed path manifest、summary、optional patch archive、source/target snapshot。
- `canvas_projection`：可重建的 Canvas node/edge/read-model，替代 Git refs/worktree/log reader。
- `runtime_events`：event type、timestamp、owner、status、source path、payload hash、cursor。
- `run_summaries`：run_id、active_run_id、status、started_at、finished_at、stdout archive ref、exit summary。
- `bash_exec_sessions`：session_id、command hash、status、log archive ref、terminal summary、line counts。
- `codex_sessions`：run_id、codex_home ref、event archive ref、prompt hash、tool summary。
- `report_index`：runtime-watch/report/storage-audit timestamp、latest mirror path、markdown path、payload hash。
- `storage_audit_runs`：files/bytes by bucket、largest buckets、skip reason、apply mode。
- `retention_actions`：compact/archive/prune/dedupe action、authority owner、safety gate、result.
- `archive_refs`：archive path、format、sha256、bytes、restore index path、source bucket。
- `compatibility_exports`：exported file path、source query、exported_at、schema version。
- `migration_runs`：baseline、dry-run、apply、verification、rollback proof、workspace id。

Schema 不得直接表达医学质量判断。医学质量与投稿判断继续由 MAS quality/publication authority surface 持有。

## Migration ledger 合同

每次 inventory、dry-run、apply、verify、export、rollback-plan 都必须写 migration ledger。ledger 是文件 authority，可被 Git 或人工审阅；SQLite 只登记索引与 provenance。

推荐文件布局：

- `artifacts/runtime/lifecycle_migration/latest.json`
- `artifacts/runtime/lifecycle_migration/<migration_run_id>.json`
- `artifacts/runtime/lifecycle_migration/<migration_run_id>.md`
- `artifacts/runtime/lifecycle_migration/restore_proofs/<quest_id>.json`
- `artifacts/runtime/lifecycle_migration/compat_exports/<surface>.json`

每个 JSON ledger 至少包含：

- `migration_run_id`
- `workspace_root`
- `workspace_id`
- `started_at`
- `finished_at`
- `mode`: `inventory` / `dry_run` / `apply` / `verify` / `export` / `rollback_plan`
- `schema_version`
- `tool_versions`
- `workspace_classification`
- `quest_classifications`
- `bucket_baseline`
- `planned_actions`
- `applied_actions`
- `skipped_items`
- `compatibility_exports`
- `restore_proofs`
- `git_tracking_check`
- `authority_surfaces_checked`
- `errors`
- `next_required_action`

`latest.json` 只能指向最新 migration run，不得替代 per-run ledger。Markdown report 用于人工阅读；机器合同以 JSON 为准。

## 并行落地 lane

这些 lane 可以并行开 worktree，但写入范围必须互不重叠。每条线完成后立刻吸收回对应 `main`，推送并清理本轮 worktree/branch。

| lane | branch 建议 | 写入范围 | 目标 |
| --- | --- | --- | --- |
| `L0_contract_schema` | `codex/mas-lifecycle-schema-contract` | MAS docs/tests/schema helper；MDS docs/tests/schema helper | 固定 schema version、authority matrix、Git ignore contract、export contract、migration run record。 |
| `L1_mas_store_expansion` | `codex/mas-lifecycle-store-expansion` | `src/med_autoscience/runtime_protocol/`、runtime/storage tests | 扩展 MAS `runtime_lifecycle.sqlite`，索引 runtime events、report history、storage governance、feedback/action metadata。 |
| `L2_mds_runtime_index_retention` | `codex/mds-runtime-index-retention` | MDS `runtime_storage.py`、quest service/codex runner tests | 扩展 MDS `.ds/runtime_index.sqlite`，覆盖 run/bash/codex/session metadata、archive refs、cursor pagination 与 stopped/cold retention ledger。 |
| `L3_compatibility_export` | `codex/mas-lifecycle-compat-export` | MAS/MDS read/export adapters 和 tests | 保持旧 latest JSON/Markdown mirror 可重建；旧 reader 不因 SQLite 引入而失效。 |
| `L4_migration_cli_inventory` | `codex/mas-lifecycle-migration-cli` | MAS CLI/MCP/controller audit surfaces；MDS maintenance CLI | 提供 `dry-run`、`apply`、`verify`、`export`、`rollback-plan` 和 project inventory report。 |
| `L5_project_migration` | `codex/mas-current-workspace-migration` | 真实 workspace 的 migration reports；不改 study artifact | 对垂体瘤/NF-PitNET、糖尿病/DM-CVD、DPCC 等当前 workspace 做 baseline、dry-run、apply eligible stopped/cold quests、compat export 和 final verification。 |
| `L6_guardrails_observability` | `codex/mas-lifecycle-guardrails` | tests/meta/docs/status/projection | 加 owner-boundary tests、DB-not-tracked checks、file-count budget alerts、restore proof assertions、read-only live safety gates。 |

吸收顺序按依赖最小化处理：`L0` 最先吸收；`L1/L2/L3/L6` 可并行；`L4` 依赖 `L0` 但可先做 read-only inventory；`L5` 只在 dry-run 和 safety gates 通过后对 stopped/cold quests apply。任何 lane 如果发现 authority drift，必须停止吸收并先修 contract。

### Lane 交付门槛

`L0_contract_schema`

- 进入条件：MAS 与 MDS `main` clean，同步到对应 origin，确认没有其他 active lifecycle schema lane。
- 必交付：schema version file、authority matrix、DB ignore rules、ledger JSON schema、compatibility export contract、migration run contract。
- 退出门槛：MAS/MDS focused schema tests 通过；新增 guard 能证明 `*.sqlite`、`*.sqlite-wal`、`*.sqlite-shm` 默认不进入 Git；文档只描述 contract，不写完成事实。

`L1_mas_store_expansion`

- 进入条件：`L0` 已吸收，MAS runtime lifecycle DB schema 可 introspect。
- 必交付：MAS runtime watch/report/storage/feedback/action history 的 SQLite write path；latest mirror 继续写文件；读入口返回 provenance。
- 退出门槛：旧 latest 文件与新 DB projection 内容一致；SQLite 写失败会明确报错或 fail-closed；MAS `scripts/verify.sh` 和 focused runtime tests 通过。

`L2_mds_runtime_index_retention`

- 进入条件：`L0` 已吸收，MDS maintenance 对 stopped/cold 判断可审计。
- 必交付：MDS `.ds/runtime_index.sqlite` 扩展 run/bash/codex/session metadata、archive refs、cursor pagination、retention action ledger。
- 退出门槛：live quest audit-only；stopped/cold dry-run 不改文件；apply mode 先写 archive/checksum/restore ref 再 prune expanded payload；MDS focused runtime-storage tests 通过。

`L3_compatibility_export`

- 进入条件：`L0` 已吸收，可读取 MAS/MDS schema introspection。
- 必交付：显式 export 命令/API，把 SQLite projection 重建成旧 JSON/Markdown report；普通 read 不隐式写文件。
- 退出门槛：旧 reader、CLI、MCP、study-progress 能继续读 latest authority；export report 包含 source query、schema version、hash、timestamp。

`L4_migration_cli_inventory`

- 进入条件：`L0` 已吸收；`L1/L2` 可以缺席，但 CLI 必须识别 capability gap。
- 必交付：`inventory`、`dry-run`、`apply`、`verify`、`export`、`rollback-plan` 六类动作；project registry discovery；per-workspace ledger。
- 退出门槛：对 fixture workspace 能完成 inventory/dry-run/verify；对缺 DB 的旧 workspace 返回 compatibility fallback；对 live workspace apply fail-closed。

`L5_project_migration`

- 进入条件：`L4` 已吸收；真实 workspace 已完成 inventory；用户或 controller policy 允许对 stopped/cold 项 apply。
- 必交付：NF-PitNET、DM-CVD、DPCC 与 registry-discovered workspace 的 baseline、dry-run、apply/skipped、compat export、restore proof、final report。
- 退出门槛：每个 workspace 有 `latest.json` ledger；live/pinned/unknown owner 只有 audit/skipped 记录；eligible stopped/cold 有 bucket-level delta；至少一个 cold quest 完成 restore proof。

`L6_guardrails_observability`

- 进入条件：可与 `L1/L2/L3/L4` 并行，但不得改同一实现文件。
- 必交付：file-count budget alert、DB-not-tracked check、restore proof assertion、live audit-only guard、migration closeout projection。
- 退出门槛：guardrail 失败能阻断 apply 或 closeout；不会重新引入 Markdown/README prose wording tests。

### 并行执行规则

- 每条 lane 开工前在本文件或 lane closeout 中声明 write set；跨 repo lane 同时声明 MAS 与 MDS 写入范围。
- `L1` 与 `L2` 不共享实现文件；共享 schema 只能通过 `L0` 修改。
- `L3` 不直接修改 migration apply 逻辑；只读 DB 与 authority files，写 compatibility export。
- `L4` 不实现 bucket compaction 细节；调用 MAS/MDS owner API 或 CLI。
- `L5` 不修改 repo 源码；只写真实 workspace migration ledger 和允许的 stopped/cold runtime payload。
- 任一 lane 需要改其他 lane 的 write set，先停止并吸收/同步 contract，避免并行冲突。

## 当前项目迁移规则

全量迁移不是按硬编码项目名手工处理。Agent 必须先通过 MAS profile、workspace cockpit、known workspace roots 和 MDS quest inventory 生成迁移清单，再按状态分类。

项目分类：

- `live_active`：只允许 baseline、index、audit、compatibility export；不允许 archive/prune/compact。
- `parked_controller_stop`：允许 dry-run；apply 需要 controller-owned parked/milestone 状态和 restore proof。
- `stopped_cold`：允许 apply migration、archive compaction、compatibility export 和 restore verification。
- `pinned_or_unknown_owner`：只允许 audit；不得清理或归档。
- `archived_workspace`：允许 cold migration，但必须先确认 restore index 和 source manifest。

每个 workspace 必须产出：

- `artifacts/runtime/lifecycle_migration/<timestamp>.json`
- `artifacts/runtime/lifecycle_migration/latest.json`
- baseline file/byte counts by bucket。
- dry-run action plan。
- apply result for eligible stopped/cold quests。
- skipped live/pinned/unknown owner list。
- SQLite schema/version report。
- compatibility export report。
- restore proof report。
- Git status proof：SQLite/WAL/SHM 未进入 Git tracking。

对当前已知疾病 workspace，后续 Agent 至少要覆盖：

- 垂体瘤 / NF-PitNET 系列 workspace。
- 糖尿病与心血管死亡风险 / DM-CVD 系列 workspace。
- DPCC / primary-care diabetes 系列 workspace。
- 通过 MAS profile registry 或 workspace audit 新发现的其他 active disease workspace。

不要用 broad `find`、`du`、`rg` 盲扫整个百万文件 `.ds` 作为默认策略。优先读已有 runtime index、storage audit、top bucket summary；缺索引时先做窄范围 bucket audit，再逐桶扩展。

### Project inventory 输出

`L4/L5` 的第一步必须产出全项目 inventory，而不是只迁已知路径。inventory 至少包含：

| 字段 | 含义 |
| --- | --- |
| `workspace_root` | workspace 绝对路径，仅用于本机操作 ledger。 |
| `workspace_id` | 稳定 workspace identity。 |
| `registry_source` | MAS profile、workspace cockpit、known roots、MDS quest inventory 或 manual operator list。 |
| `disease_family` | 例如 `pituitary`、`diabetes_cvd`、`dpcc_primary_care`。 |
| `study_ids` | workspace 下可识别 study。 |
| `quest_ids` | MDS quest identity。 |
| `runtime_state` | live、parked、stopped、archived、unknown。 |
| `authority_surfaces_present` | latest authority files、package、dataset manifest、restore index 是否存在。 |
| `largest_buckets` | `.ds` 或 runtime artifacts 的最大桶，来自 index 或窄范围 audit。 |
| `migration_classification` | `live_active` / `parked_controller_stop` / `stopped_cold` / `pinned_or_unknown_owner` / `archived_workspace`。 |
| `allowed_actions` | audit、index、dry-run、apply、export、restore-proof。 |
| `blocked_reason` | 无 owner、live、缺 restore metadata、权限或 schema gap。 |

inventory 写入 `artifacts/runtime/lifecycle_migration/inventory/latest.json`，并在每个 workspace 的 migration ledger 中引用。

### 当前项目 closeout 矩阵

`L5_project_migration` 完成时必须给出矩阵，不能只给文字总结：

| workspace | classification | baseline files/bytes | applied actions | skipped reason | files delta | restore proof | compat export | old readers verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NF-PitNET | `parked_controller_stop` / stopped-cold mix | restore-proof accounted migrated quests: ~110,576 files before; current migrated quest `.ds`: 114 files; current relevant NF quest `.ds` including tiny skipped legacy roots: 129 files | restore-proof bucket compaction for managed 001-004 and legacy `002-early-residual-risk`; no relaunch | tiny legacy `001-lineage-pfs` and `003-endocrine-burden-followup` remain 8 / 7 files and were not worth destructive apply; cross-workspace DM orphan skipped | migrated quest delta about `-110,462` files; relevant NF `.ds` now 129 files | verified; largest proof NF003 `93,135/93,135`, legacy NF002 `17,307/17,307`, errors `0` | `artifacts/runtime/lifecycle_migration/compat_exports/workspace_storage_audit.latest.json` exists; SQLite sidecar ignored/untracked | latest file authority remains file-shaped; migration ledger points to archive/restore proof |
| DM-CVD / DPCC | `parked_controller_stop` plus operator-confirmed parked active/null-run for DM002/DM003 | restore-proof accounted migrated quests: ~851,285 files before; post-follow-up current migrated quest `.ds`: 450 files | restore-proof bucket compaction for DM001 reentry, DM001 legacy, DM002, DM003 and DM004; 2026-05-06 follow-up compacted DM002/DM003 post-closeout payload after state-machine auto-relaunch was fixed | cross-workspace AS/NF quests and no-`quest.yaml` idle duplicates skipped; existing dirty unrelated workspace changes left untouched | migrated quest delta about `-850,835` files; DM002 `496,470 -> 58`; DM003 `201,744 -> 52`; DM004 post-drift now 292; DM001 legacy `5,815 -> 14` | verified; original closeout plus follow-up proofs: DM002 new `22,949/22,949`, DM003 new `16,920/16,920`, DM004 repeat `24,403/24,403`, errors `0` | `artifacts/runtime/lifecycle_migration/compat_exports/workspace_storage_audit.latest.json` exists; SQLite sidecar ignored/untracked | latest file authority remains file-shaped; migration ledger records active/null-run operator gate |
| AS biologics | `stopped_cold` / parked controller stop | restore-proof accounted AS001: ~62,383 files before; current AS001 `.ds`: 56 files | restore-proof bucket compaction for AS001 | none for current AS workspace; repo is largely untracked as a workspace, but SQLite sidecar is ignored | migrated quest delta about `-62,327` files | verified; AS001 `62,330/62,330`, errors `0` | `artifacts/runtime/lifecycle_migration/compat_exports/workspace_storage_audit.latest.json` exists; SQLite sidecar ignored/untracked | latest file authority remains file-shaped |
| HeRR | `pinned_or_unknown_owner` / startup blocked | no quest-local `.ds`; runtime/quests empty in current inventory | none | startup contract blocked; no MDS quest `.ds` exists yet | not applicable | not applicable | workspace SQLite sidecar exists | JACS profile readable on MAS main; managed quest launch remains startup-contract work |

只有矩阵里每一行都有 `applied` 或明确 `skipped reason`，且 old readers verified 不是空值时，才允许把“当前所有项目已完成迁移/兼容”写入 closeout。

### 2026-05-05 当前真实 workspace 状态

本节记录 2026-05-05 的真实迁移事实，避免后续 Agent 把 repo capability、migration ledger 或 sidecar index 写成“所有项目已经完成文件压降”。

`/Users/gaofeng/workspace/Yang/NF-PitNET` 是无功能垂体瘤 / nonfunctioning pituitary neuroendocrine tumor 的 canonical workspace。`/Users/gaofeng/workspace/Yang/无功能垂体瘤` 是本机轻量中文 stale alias/scaffold，约 392 KiB、74 个文件、没有 `.ds` quest root；它不进入独立 runtime lifecycle migration accounting，也不得和 NF-PitNET 重复统计。repo-tracked profile、fixture 与 path-normalization 测试不得再把这个中文 alias 当作真实 NF-PitNET workspace；`nfpitnet` profile 指向该路径时应 fail closed，并要求改用 canonical `NF-PitNET` 路径或临时测试 fixture。

| workspace | current ledger | classification | current `.ds` files/bytes snapshot | applied actions | skipped reason | files delta | restore proof | compat/export/old-reader status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NF-PitNET | `runtime-lifecycle-20260505-current-workspace-restore-proof-closeout` | `parked_controller_stop` / stopped-cold mix | managed 001: 18 files / 56 KB; managed 002: 24 files / 872 KB; managed 003: 38 files / 2,970,040 KB; managed 004: 20 files / 1,512 KB; legacy 002: 14 files / 176,348 KB; tiny skipped legacy roots: 15 files | restore-proof compaction for managed 001-004 and legacy 002; source entries verified: 3, 29, 93,135, 3, 17,307 | tiny legacy roots with 8 and 7 files left in place; cross-workspace orphan skipped | migrated quest `.ds` files about `110,576 -> 114`; relevant NF quest `.ds` now 129 files | verified, errors `0` | workspace SQLite sidecar ignored/untracked; compatibility export exists; old authority files remain file-shaped and readable |
| DM-CVD / DPCC | `runtime-lifecycle-20260505-current-workspace-restore-proof-closeout` plus 2026-05-06 follow-up compaction | `parked_controller_stop` plus operator-confirmed parked active/null-run for DM002/DM003 | DM001 reentry: 34 files / 725,716 KB; DM001 legacy: 14 files / 31,248 KB; DM002: 58 files / 6.3G; DM003: 52 files / 4.5G; DM004: 292 files / 1.0G | restore-proof compaction for DM001 reentry, DM001 legacy, DM002, DM003, DM004; 2026-05-06 follow-up compacted DM002/DM003 new runtime buckets after auto-relaunch fix | cross-workspace AS/NF quests and no-quest idle duplicates skipped; unrelated dirty study/workspace edits preserved | current DM-CVD migrated quest `.ds` files about `851,285 -> 450`; DM002 `496,470 -> 58`; DM003 `201,744 -> 52`; DM004 post-drift final 292; DM001 legacy `5,815 -> 14` | verified, errors `0`; DM002 follow-up `22,949/22,949`, DM003 follow-up `16,920/16,920`, DM004 repeat `24,403/24,403` | workspace SQLite sidecar ignored/untracked; compatibility export exists; old authority files remain file-shaped and readable |
| AS biologics | `runtime-lifecycle-20260505-current-workspace-restore-proof-closeout` | `stopped_cold` / parked controller stop | AS001: 56 files / 2,331,800 KB | restore-proof compaction for AS001; source entries verified 62,330 | none for current AS workspace | AS001 `.ds` files about `62,383 -> 56` | verified, errors `0` | workspace SQLite sidecar ignored/untracked; compatibility export exists; old authority files remain file-shaped and readable |
| HeRR | `20260505T052743Z-herr-inventory-refresh` | `pinned_or_unknown_owner` / startup blocked | no quest-local `.ds`; runtime/quests currently empty | none | startup contract blocked; no MDS quest `.ds` exists yet | not applicable | not applicable | workspace SQLite sidecar now exists; JACS profile is readable on MAS main, but managed quest launch still needs startup contract repair |

结论：current eligible workspaces 已完成 `SQLite sidecar + ledger + compatibility read/export + restore-proof archive compaction`。2026-05-05 closeout 按 restore-proof accounted 口径把 11 个 migrated quest 的 `.ds` 从约 1,024,244 个文件压到 772 个文件，减少约 1,023,472 个小文件；2026-05-06 follow-up 又完成 DPCC004、DM002 与 DM003 的 post-closeout drift compaction，当前核心 disease workspace 的 migrated quest `.ds` 已保持在几十到数百文件级。剩余体积主要是少量 tar.gz archive、manifest、restore proof、SQLite sidecar 和仍需保留的 latest authority/runtime mirror。后续工作重点转为保持新 runtime 默认进入同一 lifecycle 结构，并把任何新增 live writer 漂移先归类到状态机/owner 问题，再进入同一维护流程。

## 备份、回滚与 checkpoint

迁移必须先能回滚，再允许 apply。

备份规则：

- 对 SQLite 使用 SQLite backup API 或 checkpoint 后复制；不得只复制主 DB 而漏掉 WAL/SHM 中的未 checkpoint 数据。
- 对将要 prune 的 expanded payload，先生成 gzip/tar archive、sha256、byte count、source manifest、restore index。
- 对 latest authority files 只读校验 hash，不做迁移写入；如果 migration CLI 需要导出兼容文件，写入 compatibility export 目录，不覆盖 authority latest。
- 对 workspace Git 状态做只读记录，证明 DB/WAL/SHM 没进入 tracking。

回滚规则：

- `rollback-plan` 必须在 `apply` 前生成，列出 archive ref、restore target、checksum、expected files/bytes、owner。
- apply 后至少抽样一个 cold quest 执行 restore proof；如果首个 cold quest restore proof 失败，本轮不得继续 apply 其他 workspace。
- 回滚恢复只允许还原 runtime payload 与 compatibility export，不得回写 publication/controller/study authority。
- 如果发现 archive checksum mismatch、restore index 缺失、owner unknown、live state drift，迁移立即降级为 audit-only 并记录 blocker。

SQLite checkpoint 规则：

- 写入批次结束必须执行 checkpoint 或通过 backup API 产出一致备份。
- 长事务禁止跨大量文件操作；archive 创建、checksum、DB insert、prune 应拆成可恢复 action record。
- 网络盘或跨 host workspace 不使用同一 SQLite WAL 数据库并发写；需要先转为 host-local maintenance。

## 兼容读写策略

迁移期所有读入口按同一顺序工作：

1. 读取 authority latest 文件，判断 study/publication/runtime truth。
2. 读取 SQLite sidecar，补充 history、cursor、retention、bucket summary。
3. 若 SQLite 缺失，读取旧文件历史并返回 `compatibility_fallback_used=true`。
4. 若 latest 文件缺失但 SQLite 存在，只能返回 `authority_missing`，不得由 SQLite 自行生成 publication/study truth。
5. 只有显式 export 命令可以从 SQLite 重建旧 report 文件；普通 read 不做隐式写入。

迁移期所有写入口按同一顺序工作：

1. 写 owner authority file 或 canonical artifact。
2. 写 latest mirror。
3. 在 SQLite 登记 index/history/provenance。
4. 必要时写 compatibility export。
5. 写 migration/retention proof。

SQLite 写入失败时，不允许静默吞掉错误后宣称迁移成功。对于 authority 写入路径，失败策略必须 fail-closed 或明确返回 `sqlite_index_write_failed`，并保留文件 authority 已写入事实。

### 兼容性验证矩阵

`L3/L4/L5` 必须覆盖下列入口。没有真实 workspace 时可先用 fixture；`L5` closeout 必须使用真实 workspace ledger 证明。

| 入口 | 必须继续读取的 authority | SQLite 可提供的增量 | 失败判定 |
| --- | --- | --- | --- |
| `study_progress` | study runtime status、publication/controller latest、package locator | history summary、migration skipped reason、storage bucket trend | SQLite 存在但 latest authority 缺失时仍报告 `authority_missing`。 |
| `runtime_watch` latest | runtime latest mirror、controller stop/live state | report index、cursor、previous run refs | 不得因 DB 缺失拒绝读取现有 latest 文件。 |
| storage audit/status | `storage_audit/latest.json` 或 existing report mirror | bucket history、retention actions、delta trend | apply 结果缺 restore proof 时不能标记 complete。 |
| CLI/MCP product entry | profile/workspace contract、authority latest | project inventory、migration ledger readout | MCP/CLI 不得隐式触发 destructive compaction。 |
| package locator | current package manifest、DOCX/PDF/ZIP presence | archive/index provenance | SQLite 不得替代 `current_package` truth。 |
| legacy report readers | old JSON/Markdown report path | explicit compatibility export | export 只能显式执行，普通 read 不写历史文件。 |

验证输出必须记录：

- `reader_name`
- `workspace_id`
- `study_id`
- `quest_id`
- `authority_files_checked`
- `sqlite_sidecar_checked`
- `compatibility_fallback_used`
- `export_paths`
- `result`
- `error`

## 文档与测试边界

本 program 是 long-horizon execution contract，后续实现需要测试 schema、CLI/MCP/API、reader behavior、guardrail、JSON/YAML/TOML contracts、generated artifacts 和 runtime behavior。

不得新增或恢复以下测试：

- 读取本文件、README 或普通 Markdown 后断言标题、段落、固定短语、链接顺序、表格措辞。
- 用 pytest 检查“某个计划项文字必须出现”。
- 用脚本把文档表述当作 runtime truth。

如果需要可验证约束，先把约束提升为结构化 schema、contract JSON、CLI output、MCP payload、runtime projection 或 generated artifact，再测试该结构化 surface。

## 验收门槛

Repo 级验收：

- MAS `make test-meta`、`scripts/verify.sh` 通过。
- MDS runtime storage focused tests 与 `scripts/verify.sh` 通过。
- `git diff --check` 通过。
- preflight contract 能识别本 program 文档和对应验证。
- DB schema version、export contract、restore proof、DB-not-tracked guard 有测试覆盖。

真实 workspace 验收：

- 每个 workspace 有 baseline/dry-run/apply/verify 或 skipped reason。
- live quest 默认保持 audit-only；只有 `active_run_id=null` 且用户明确确认 parked active 的 quest 可用 operator-confirmed gate 做 destructive compaction，并必须记录在 ledger。
- stopped/cold quest 的 `files_after < files_before`，并记录 bucket-level delta。
- 至少一个冷 quest 完成 restore proof：archive ref、checksum、latest export、reader compatibility 均可验证。
- 旧入口仍能读取 `study-progress`、`runtime_watch` latest、storage audit latest 和 package locator。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package` 未被迁移过程手工 patch。

完成定义：

- MAS/MDS 代码与 docs 吸收到 `main` 并推送。
- 本轮 worktree/branch 清理完成；外部 active worktree 不触碰。
- 当前项目迁移报告已写入各 workspace 的 runtime migration ledger。
- 文件数量和体积收益按 workspace 汇总，而不是只给单个样本。
- SQLite runtime DB 损坏或缺失时，必须能由 ledger、restore index、archive refs、latest mirror 和 compatibility export 重建 runtime projection；任何不可重建数据必须继续有文件/归档 authority。

“完全能用”的最终定义：

- 新创建的 workspace 默认写 lifecycle SQLite runtime DB、latest file mirror 和 migration-compatible ledger。
- 旧 workspace 缺 DB 时仍可读，且第一次 maintenance 能生成 baseline index。
- live quest 自动受 audit-only gate 保护。
- stopped/cold quest 可通过同一 CLI/API 完成 dry-run、apply、verify、export、rollback-plan。
- operator 能看到全项目 inventory、项目级 closeout matrix、file-count delta、restore proof 和 skipped reason。
- 旧 Agent 继续读文件 authority；新 Agent 优先读 SQLite projection 并能导出旧报告。
- 删除 SQLite runtime DB 不会造成 publication/study/artifact truth 丢失；runtime projection 可由 ledger/export/archive refs 重建。

## Agent 接力规则

后续 Agent 进入这条线时，先读：

- `docs/decisions.md` 中 2026-05-05 SQLite sidecar 决策。
- 本文件。
- `docs/status.md` 的 runtime lifecycle storage 条目。
- `docs/program/mas_mds_unified_enhancement_program.md` 的 L5 governance 边界。
- MDS `runtime_storage.py` 与 runtime storage tests。

执行规则：

- 默认开独立 worktree，分 lane 并行推进。
- 每条 lane 写入范围必须提前声明，不跨 lane 改同一文件。
- 完成后用五项 closeout 汇报：做了什么、改了哪些文件、跑了哪些验证、吸收到哪个 `main`、worktree/branch 是否清理。
- 不把计划项写成完成项；没有真实 workspace migration proof 时，只能说 repo-level capability landed。
- 对 live study 只做 supervisor/audit，不做 destructive migration。
- 遇到 authority surface 冲突，先修 owner contract，再继续实现。

## 下一步可直接执行的工作包

1. `L0_contract_schema`：补 schema contract、DB-not-tracked guard、compatibility export contract、meta test。
2. `L1_mas_store_expansion`：把 MAS feedback/action/runtime history 与 report index 扩到 SQLite，并保留 latest 文件 mirror。
3. `L2_mds_runtime_index_retention`：扩展 MDS runtime index，覆盖 run/bash/codex history metadata 与 archive refs。
4. `L3_compatibility_export`：实现从 SQLite 导出旧 report JSON/Markdown 的显式命令。
5. `L4_migration_cli_inventory`：实现全 workspace dry-run inventory 和 migration ledger。
6. `L5_project_migration`：对当前疾病 workspace 做 baseline、dry-run、eligible stopped/cold apply、restore proof 与 final report。
7. `L6_guardrails_observability`：把 file-count budget、restore proof、live audit-only 和 DB-not-tracked 变成可重复验证。

本 program 的目标是让 MAS/MDS 从“百万级散落运行态文件”收敛为“文件 authority + SQLite lifecycle index + cold archive restore contract”的长期形态，同时保持 Git 兼容和旧入口可读。
