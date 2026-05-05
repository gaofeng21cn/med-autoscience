# Runtime Lifecycle SQLite Migration Program

Status: `active execution program`
Date: `2026-05-05`
Owner: `MedAutoScience Runtime OS + MedDeepScientist backend`

## 结论

引入 SQLite 可行，也有必要，但目标是不替代 Git。目标形态是 `SQLite sidecar + file authority + Git source control`：Git 继续管理源码、合同、文档和可审阅配置；MAS/MDS 的 authority surface、restore metadata、paper/manuscript/package/dataset 交付物继续保持文件形态；SQLite 负责 runtime lifecycle 的索引、历史、游标、摘要、retention ledger 和 compact projection。

这条线应直接按长线目标推进，不按一次只做一个小阶段推进。实现上可以并行展开多个 worktree，但所有 lane 必须共享同一 schema/authority contract，并在吸收回 `main` 前完成兼容导出、真实 workspace dry-run、验证和清理。

## 一步到位目标

本 program 的目标不是只补一个索引文件，也不是只清理某个异常 workspace。完成后的可用状态必须同时满足：

- MAS/MDS repo 已有统一 lifecycle schema、读写 contract、compatibility export、migration CLI / MCP surface、guardrail 和验证入口。
- 所有当前项目先进入 registry-backed inventory，再按 `live_active`、`parked_controller_stop`、`stopped_cold`、`pinned_or_unknown_owner`、`archived_workspace` 分类。
- 所有 eligible stopped/cold quest 完成 baseline、dry-run、apply、compatibility export、restore proof 和 final ledger；所有 live / pinned / unknown owner quest 有明确 skipped reason。
- 旧入口仍能读取 latest authority files、runtime status、storage audit、package locator 和 study progress；新入口能从 SQLite 读取 history、cursor、retention ledger、bucket summary 和 archive refs。
- SQLite sidecar 可删除后由文件 authority / archive / export 流程解释，或明确标记为可重建 index；任何不可重建 truth 仍保留在文件 authority 或归档 authority 中。
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

当前已落地的第一层能力是索引层：

- MAS：`artifacts/runtime/runtime_lifecycle.sqlite` 记录 runtime watch state、runtime report、workspace storage audit。
- MDS：`.ds/runtime_index.sqlite` 记录 maintenance run、bucket snapshot、archive ref 与 metadata。

这层能力降低了枚举和追溯成本，但尚未完成全量小文件减少。真正降低文件数量需要后续把 event/run/bash/codex history 的历史 metadata 与 cursor 查询迁入 SQLite，同时把原始大 payload 合并成 gzip/tar/cold archive，并由 SQLite 记录 archive ref、checksum、byte count 与 restore contract。

## 工程依据

SQLite 官方把带 schema 的数据库文件定位为适合持久化应用状态的单文件应用格式，核心能力包括单文件文档、事务更新、增量更新、并发读取和跨语言访问；这与 MAS/MDS 的 runtime lifecycle 索引需求一致。

SQLite 官方小对象基准显示，把大量小 blob 放入数据库可减少 open/close 和 filesystem block padding 成本；这个结论不能直接等价为所有 MAS/MDS payload 都应该进 SQLite，但它支持把大量小元数据、摘要、游标和 compact projection 从散落文件迁入 SQLite。

SQLite WAL 支持读写并发和顺序写入，但同一 WAL 数据库要求在同一 host 上使用，不适合网络文件系统上的跨主机共享写入。因此 MAS/MDS 的 SQLite sidecar 必须是 workspace-local / quest-local，不作为跨主机中心服务。

SQLite Archive / SQLAR 证明 SQLite 可作为小文件容器，但本 program 不把 SQLite 提升为默认 blob archive。MAS/MDS 默认仍用 gzip/tar/cold archive 保存原始大 payload；SQLite 记录索引与恢复引用。

Git 的 untracked-cache、fsmonitor、sparse-checkout / sparse-index 可以降低 Git working tree 和 index 扫描成本。它们不能解决 MAS/MDS 自己在 `.ds` 内生成的 runtime 小文件生命周期，所以只能作为 Git 兼容优化，而不是本问题的核心解法。

参考：

- SQLite Application File Format: `https://www.sqlite.org/appfileformat.html`
- SQLite Faster Than The Filesystem: `https://www.sqlite.org/fasterthanfs.html`
- SQLite WAL: `https://www.sqlite.org/wal.html`
- SQLite Archive Files: `https://www.sqlite.org/sqlar.html`
- Git update-index: `https://git-scm.com/docs/git-update-index`
- Git sparse-index: `https://git-scm.com/docs/sparse-index`

## 权威边界

SQLite sidecar 只能持有 `index/history/retention/cursor sidecar` 内容：

- append-heavy runtime telemetry 与 historical report index。
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
- SQLite sidecar、WAL、SHM、临时 checkpoint 文件必须在 workspace/runtime `.gitignore` 中排除。
- 旧脚本和旧 Agent 继续读取 latest 文件 mirror；新 reader 优先读 SQLite，没有 SQLite 时只允许进入明确的 compatibility fallback，不得产生第二套 truth。
- 导出命令必须能从 SQLite 重建旧 JSON/Markdown report 形态，用于人工审阅、debug 和历史工具兼容。
- Git 优化项只作为辅助：大型 tracked 源码仓可继续使用 sparse-checkout / sparse-index；runtime `.ds` 文件数量问题必须由 SQLite index + archive/retention policy 解决。

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
| NF-PitNET | 待 inventory 填充 | 待实测 | 待执行 | 待分类 | 待实测 | 待验证 | 待导出 | 待验证 |
| DM-CVD | 待 inventory 填充 | 待实测 | 待执行 | 待分类 | 待实测 | 待验证 | 待导出 | 待验证 |
| DPCC | 待 inventory 填充 | 待实测 | 待执行 | 待分类 | 待实测 | 待验证 | 待导出 | 待验证 |
| registry-discovered others | 待 inventory 填充 | 待实测 | 待执行 | 待分类 | 待实测 | 待验证 | 待导出 | 待验证 |

只有矩阵里每一行都有 `applied` 或明确 `skipped reason`，且 old readers verified 不是空值时，才允许把“当前所有项目已完成迁移/兼容”写入 closeout。

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
- 所有 live quest 均保持 audit-only，没有 destructive compaction。
- stopped/cold quest 的 `files_after < files_before`，并记录 bucket-level delta。
- 至少一个冷 quest 完成 restore proof：archive ref、checksum、latest export、reader compatibility 均可验证。
- 旧入口仍能读取 `study-progress`、`runtime_watch` latest、storage audit latest 和 package locator。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package` 未被迁移过程手工 patch。

完成定义：

- MAS/MDS 代码与 docs 吸收到 `main` 并推送。
- 本轮 worktree/branch 清理完成；外部 active worktree 不触碰。
- 当前项目迁移报告已写入各 workspace 的 runtime migration ledger。
- 文件数量和体积收益按 workspace 汇总，而不是只给单个样本。
- SQLite sidecar 可删可重建，或可由明确 export/restore 流程解释；任何不可重建数据必须继续有文件/归档 authority。

“完全能用”的最终定义：

- 新创建的 workspace 默认写 lifecycle SQLite sidecar、latest file mirror 和 migration-compatible ledger。
- 旧 workspace 缺 DB 时仍可读，且第一次 maintenance 能生成 baseline index。
- live quest 自动受 audit-only gate 保护。
- stopped/cold quest 可通过同一 CLI/API 完成 dry-run、apply、verify、export、rollback-plan。
- operator 能看到全项目 inventory、项目级 closeout matrix、file-count delta、restore proof 和 skipped reason。
- 旧 Agent 继续读文件 authority；新 Agent 优先读 SQLite projection 并能导出旧报告。
- 删除 SQLite sidecar 不会造成 publication/study/artifact truth 丢失。

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
