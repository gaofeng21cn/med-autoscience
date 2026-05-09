# Supervision Scheduler Contract

Status: `active scheduler contract / local adapter landed`
Owner: `MedAutoScience Runtime OS`
Date: `2026-05-09`

## 入口结论

`MedAutoScience` 的运行形态应固定为三层：

| layer | owner | responsibility |
| --- | --- | --- |
| Runtime Core | `MAS Runtime OS` / `mas_runtime_core` | 持有 worker、run、turn lifecycle、runner completion 后的下一 turn 调度、runtime health 与 recovery truth。 |
| Supervisor Scheduler | `MAS supervision scheduler contract` | 按 cadence 唤醒 MAS-owned supervision tick，记录 job/run receipt，暴露 freshness / SLO / drift；不持有研究执行或质量判断。 |
| Product Projection | `Progress Portal` / `Live Console` / `study-progress` / cockpit | 只读展示前两层事实，不执行 runtime action，不写 study/publication/artifact truth。 |

`MAS supervision scheduler contract` 现在是默认 owner。`local` 是默认 adapter selection：macOS 本机落到 MAS-owned LaunchAgent，Linux / container 仍 fail-closed 为 no persistent local scheduler 并给出 one-shot reconcile 语义。`Hermes gateway cron` 保留为显式 `--manager hermes` optional adapter，不是架构中心，也不是 MAS runtime / session / research owner。

2026-05-09 落地更新：`runtime-supervision-status`、`runtime-ensure-supervision` 和 `runtime-remove-supervision` 已接到 `supervision_scheduler` façade，默认 `--manager local`。macOS local adapter 会生成 MAS-owned tick script、LaunchAgent plist、install proof 和 scheduler receipt；显式 `--manager hermes` 继续调用 Hermes adapter 并投影到同一 `scheduler_owner=mas_supervision_scheduler` 合同下。旧 `systemd|cron|launchd|docker` manager 仍是 retired fail-closed diagnostic，不作为 active shortcut。

## 当前 Hermes 实际职责

截至 `2026-05-09`，Hermes 在 MAS 显式 optional adapter 路径中承担的职责很单一：

1. 写入或刷新 MAS-owned tick script。
   - 当前 Hermes adapter 将脚本放到 `~/.hermes/scripts/med-autoscience/<workspace-key>/watch_runtime_tick.py`。
   - 脚本本身只调用 MAS workspace entry，不持有研究逻辑。
2. 注册、更新、恢复、触发和删除 cron job。
   - `runtime-ensure-supervision --manager hermes` 调用 external Hermes CLI 的 `cron create` / `cron edit` / `cron resume` / `cron run` / `cron remove`。
3. 提供 job registry 与 latest run projection。
   - `runtime-supervision-status` 读取 `~/.hermes/cron/jobs.json`、`~/.hermes/sessions/session_cron_*.json`、gateway service state、script path 和 latest output。
4. 把调度状态投影为 MAS status。
   - 包括 loaded / not loaded / execution failed / drift / duplicate jobs / stale SLO。

这些都是 scheduler adapter 能力，不是 hosted agent runtime 必需能力。它们可以由 MAS-owned local scheduler adapter 复刻，只要保留同构状态面、幂等语义、失败投影和迁移策略。

当前 desired tick sequence 固定为：

1. `watch-runtime --max-ticks 1`
2. `supervisor-scan`
3. `supervisor-consume`
4. `supervisor-execute-dispatch`

该 sequence 是 MAS contract。adapter 只负责按约定调用。

## 外部工程经验

本合同采用成熟 scheduler / durable control-plane 的共性做法，但不引入这些系统作为 MAS dependency：

| source | 可借鉴经验 | MAS 落点 |
| --- | --- | --- |
| [Kubernetes CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) | CronJob 只负责按 schedule 创建 Job；Job 应幂等；要显式处理 missed schedule、starting deadline、concurrency policy 和 scheduled timestamp。 | Scheduler adapter 只发起 MAS tick；tick 必须幂等；status 记录 scheduled time、started time、missed/skipped reason 和 overlap policy。 |
| [Temporal Schedule](https://docs.temporal.io/schedule) | Schedule 有独立 identity；Action 与 Spec 分开；支持 pause、backfill、overlap policy、catchup window、pause-on-failure。 | MAS job identity 独立于 study/run；contract 拆成 schedule spec、tick action、policy、receipt；支持 pause/resume/trigger-now 和 catchup/skip 策略。 |
| [APScheduler](https://apscheduler.readthedocs.io/en/stable/userguide.html) | 持久 job store 需要稳定 job id 与 replace-existing；限制并发实例；用 misfire grace time 控制迟到触发。 | Local adapter 必须有 stable job id、upsert 而非重复创建、single active tick lock、misfire grace / stale SLO。 |
| [Celery periodic tasks](https://docs.celeryq.dev/en/3.1/userguide/periodic-tasks.html) | 同一 schedule 只能有一个 scheduler，否则会产生重复任务；集中 schedule state 可避免同步和锁问题。 | 每个 workspace-key 同一时间只能有一个 primary scheduler adapter；迁移时必须先 disable old adapter 或证明不会双调度。 |
| [Apple launchd timed jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html) | macOS 推荐 launchd 管理 timed jobs；cron 仍支持但不建议程序化写共享 crontab；sleep/offline 行为需要明确。 | macOS local adapter 优先 LaunchAgent；cron 只作显式 fallback；status 必须说明 sleep/offline catchup 语义。 |

共同结论：scheduler 的核心不是“谁能定时执行命令”，而是围绕同一个 job identity 提供幂等安装、单实例运行、missed-run 策略、失败 receipt、状态投影和安全迁移。

## Scheduler Contract

MAS-owned scheduler contract 必须提供下列 machine boundary。默认 local adapter、显式 Hermes adapter 与后续 local backend 都要映射到同一字段。

### Scheduler Job

| field | meaning |
| --- | --- |
| `scheduler_owner` | `mas_supervision_scheduler`。表示 contract owner，不等于 adapter。 |
| `adapter_id` | `hermes_gateway_cron`、`local_launchd`、`local_systemd_user`、`local_cron` 或 future hosted adapter。 |
| `workspace_key` | 由 profile/workspace root 派生的稳定 key。 |
| `job_id` | 稳定 job identity；重复 ensure 必须 upsert 同一 job。 |
| `profile_ref` | profile path / profile fingerprint。 |
| `tick_script_ref` | MAS-owned script path、checksum、generated_at。 |
| `schedule_spec` | interval/cadence、timezone、jitter/catchup policy。默认 `interval_seconds=300`。 |
| `overlap_policy` | 默认 `skip_if_running`；禁止同一 workspace 同时跑两个 outer tick。 |
| `misfire_policy` | 默认 `record_missed_and_wait_next`；允许 operator 触发 one-shot reconcile。 |
| `enabled` | scheduler 是否启用。 |

### Tick Receipt

| field | meaning |
| --- | --- |
| `scheduled_for` | 计划触发时间。 |
| `started_at` / `finished_at` | 实际开始和结束时间。 |
| `exit_code` | tick script exit code。 |
| `outcome` | `succeeded` / `failed` / `skipped_overlap` / `missed_deadline` / `blocked`。 |
| `run_id` | adapter-local run receipt id。 |
| `stdout_ref` / `stderr_ref` | 输出引用；不得把大输出塞入 status summary。 |
| `tick_sequence` | 实际执行的 MAS sequence 与各步 outcome。 |
| `slo_state` | `fresh` / `due` / `stale` / `missing` / `blocked`。 |
| `dedupe_fingerprint` | 防重复触发和状态漂移定位。 |

### Adapter Status

| field | meaning |
| --- | --- |
| `adapter_installed` | adapter 所需 OS/service 资产是否存在。 |
| `adapter_loaded` | OS/gateway 是否已加载 job。 |
| `adapter_enabled` | job 是否启用。 |
| `next_due_at` | 下一次预计触发。 |
| `last_receipt_ref` | 最新 receipt path。 |
| `drift_reasons` | schedule/script/profile/checksum/job-state drift。 |
| `duplicate_job_ids` | 同一 workspace-key 下的重复 job。 |
| `migration_state` | `none` / `shadow` / `cutover_ready` / `cutover_complete` / `rollback_ready`。 |

## Adapter 策略

### Optional Adapter: `hermes_gateway_cron`

保留为 explicit optional adapter。它的角色是：

- 继续服务仍显式选择 Hermes 的真实 workspace。
- 提供当前 job registry、session history、latest run 和 gateway liveness。
- 作为 parity oracle，帮助验证 local adapter 输出是否同构。

它不再被文档或 UI 写成 MAS architecture center。

### 默认 Adapter: `mas_local_scheduler`

MAS-owned local adapter 的 CLI 形态为：

```bash
medautosci runtime-ensure-supervision --profile <profile> --manager local
medautosci runtime-supervision-status --profile <profile>
medautosci runtime-remove-supervision --profile <profile> --manager local
```

`local` 是产品语义；内部 OS backend 由 host 探测决定。当前 landed backend 是 macOS LaunchAgent；其他 backend 保持 blocked/fail-closed，不伪装成已安装：

| OS / environment | preferred backend | notes |
| --- | --- | --- |
| macOS user desktop | `launchd` LaunchAgent | landed；不写共享 crontab；生成 MAS tick script、plist、receipt 和 install proof。 |
| Linux with user systemd | `systemd --user` timer | blocked until implemented；不得回退到旧 workspace-local scaffold。 |
| Linux without systemd user | explicit `cron` fallback | blocked until implemented；未来也只能通过 `local` adapter contract，不允许直接恢复旧 `--manager cron`。 |
| container / CI | no persistent scheduler by default | 只支持 one-shot dry-run / reconcile；不得伪装成 installed scheduler。 |

现有 `--manager systemd|cron|launchd|docker` 仍保持 retired/fail-closed，直到被新的 `local` adapter 取代。不要把旧 workspace-local host service scaffold 复活；新 adapter 的所有 state、receipt 和 proof 都归 MAS scheduler contract。

### Optional Adapter: `hermes_hosted`

Hermes 可以继续作为 optional hosted / remote / multi-model executor substrate：

- hosted runtime carrier
- non-GPT / provider-routed executor
- OPL online-management gateway
- cross-workspace registry 或 remote supervision

这类价值必须通过显式 adapter selection 和 readiness proof 进入，不参与默认本地 MAS dependency。

## 一步到位落地计划

### Phase 0: 文档与 contract freeze

本阶段目标是把 owner 口径一次性写清。

- 新增本文件作为 active scheduler contract。
- 更新 `runtime_boundary.md`、`runtime_supervision_loop.md`、`runtime_core_convergence_and_controlled_cutover.md`、`architecture.md`、`status.md`、`decisions.md` 的口径。
- 明确三层：Runtime Core / Supervisor Scheduler / Product Projection。
- 明确 Hermes 当前承担的是单一 scheduler adapter 职责。
- 明确 local adapter 已成为默认；Hermes 只作为 explicit optional adapter 保留。

验收：

- docs 中不再把 Hermes 写成 MAS architecture center。
- active docs 只能说 `Hermes gateway cron = explicit optional scheduler adapter`。
- active docs 不允许说 `Hermes = MAS runtime owner / session owner / research executor owner`。

### Phase 1: Contract surface implementation

Status: `landed`

实现 MAS-owned scheduler data model 和 read/write façade。

受影响模块建议：

- `src/med_autoscience/controllers/hermes_supervision.py`
- 新增 `src/med_autoscience/controllers/supervision_scheduler.py`
- 新增 `src/med_autoscience/controllers/supervision_scheduler_parts/*`
- CLI parser / command dispatch
- tests: scheduler contract, hermes adapter parity, local adapter dry-run

关键要求：

- `runtime-supervision-status` 输出 `scheduler_owner=mas_supervision_scheduler` 和 `adapter_id=<current adapter>`。
- Hermes adapter 先通过新 façade 暴露同一 schema，不改变真实 workspace 行为。
- tick script 生成、checksum、sequence、SLO、duplicate detection 和 latest receipt 进入 backend-neutral shape。
- 现有 Hermes 状态读取继续可用，但被标记为 adapter projection。

验收：

- Hermes adapter behavior 不变。
- 新 schema 与旧 status 保持兼容或提供清晰 migration field。
- focused tests 覆盖 Hermes job upsert/drift/duplicate/latest-run。

### Phase 2: Local adapter dry-run and install proof

Status: `landed for macOS LaunchAgent; blocked/fail-closed for non-macOS persistent backends`

实现 `--manager local --dry-run` 和 install proof，不立即切默认。

关键要求：

- macOS 生成 LaunchAgent plist preview、label、program arguments、stdout/stderr path、state dir、remove plan。
- Linux systemd user 生成 `.service` / `.timer` preview、unit name、enable/start/status/remove plan。
- cron fallback 只在显式允许时生成 marker-block preview。
- 所有 backend 都写同一 install proof 和 status projection。
- container/CI 返回 no persistent scheduler，并给出 one-shot reconcile command。

验收：

- `runtime-ensure-supervision --manager local --dry-run` 不写 OS scheduler，却能给出完整 proof。
- `runtime-supervision-status` 能解释 local adapter missing / ready / blocked。
- 不触碰 legacy workspace-local scaffold。

### Phase 3: Local adapter apply and shadow parity

Status: `macOS apply landed; real workspace shadow/cutover evidence pending`

在真实 profile 上安装 local adapter，但先 shadow 验证。

关键要求：

- 允许 `local` job 安装为 disabled/shadow 或低风险 one-shot。
- 对同一 profile 比较 Hermes adapter 与 local adapter 的 schedule spec、tick script checksum、latest receipt、SLO state。
- 明确防双调度策略：同一 workspace-key 同时只能有一个 primary enabled adapter。
- 提供 `trigger-now` one-shot，用于验证 tick sequence 与 receipt。

验收：

- 真实 workspace 上 local adapter 可以 trigger one-shot 并生成同构 receipt。
- Hermes 仍为 primary；local 为 shadow。
- `runtime-supervision-status` 能显示 primary/secondary adapter 与 drift。

### Phase 4: Default cutover

Status: `CLI default switched to local; real workspace migration receipts pending`

把默认 scheduler adapter 切到 `local`。

关键要求：

- `runtime-ensure-supervision` 默认 manager 从 `hermes` 切到 `local`，或 profile 明确写 `scheduler_adapter=local`。
- Hermes job 被 disable/remove 前，必须记录 migration receipt。
- 已注册 Hermes job 的 workspace 进入 `cutover_ready -> cutover_complete`，不能产生双调度。
- OPL handoff / Portal / Live Console 只消费 MAS scheduler status，不再读 Hermes-specific source 作为默认事实。

验收：

- 新 workspace 默认不需要 Hermes 即可获得 outer supervision。
- 旧 workspace 迁移后仍有 scheduled tick、latest receipt、SLO state 和 repair command。
- `runtime-supervision-status` 在无 Hermes 环境中不报 architecture blocker，只报告 local adapter state。

### Phase 5: OPL simplification and optional Hermes

Status: `in progress across OPL ecosystem`

把 OPL 的依赖口径同步为 optional Hermes provider。

关键要求：

- OPL README / docs / decisions：Codex-default + MAS local scheduler 是默认；Hermes 是 optional online-management / hosted provider。
- Full first-install manifest 不再把 Hermes 作为 mandatory baseline；可以作为 optional advanced bundle。
- runtime tray / observer 改为读取 MAS scheduler projection；Hermes cron projection 只在 adapter_id 为 Hermes 时展示。
- `--executor hermes` / non-GPT provider routing 继续保留为显式路径。

验收：

- OPL core/domain readiness 不依赖 Hermes。
- 安装包和状态页能在未安装 Hermes 时保持 green，只把 hosted/online-management 能力列为 optional missing。

### Phase 6: Cleanup and compatibility retirement

Status: `MAS default wording cleanup landed; old workspace migration receipts pending`

移除默认路径中的 Hermes required assumptions。

关键要求：

- profile template 中 Hermes repo/home 字段降为 optional hosted adapter settings。
- docs 中所有 `Hermes-hosted supervision` 文案改成 adapter-aware wording。
- 保留 Hermes tests 作为 optional adapter tests。
- 删除或迁移只会读取 `~/.hermes/cron/jobs.json` 的默认 projection，改读 MAS scheduler status。

验收：

- active default docs 不再把 Hermes 写成默认 owner，也不再把旧 Hermes-hosted supervision warning 当作默认运行 blocker。
- 无 Hermes host 环境下 MAS default workflow 可完成 status/progress/watch/supervision。
- Hermes adapter 仍可显式安装、检查和移除。

## Done Criteria

Hermes 可以从 required dependency 降为 optional adapter 的条件：

1. `runtime-ensure-supervision --manager local` 能在至少 macOS 本机安装、刷新、触发、状态检查和移除 scheduler。
2. `runtime-supervision-status` 不依赖 Hermes path 也能输出 loaded/missing/stale/blocked、latest receipt、SLO state、repair command。
3. 同一 workspace-key 有 primary adapter lock，迁移不会双调度。
4. tick sequence、receipt、SLO、duplicate detection、drift detection 与 Hermes adapter 同构。
5. Portal、Live Console、study-progress、workspace cockpit 和 OPL handoff 只读取 MAS scheduler projection。
6. 旧 Hermes jobs 有 disable/remove migration receipt。
7. OPL core/domain install 和 MAS default operation 在无 Hermes 环境下不降级。

## 不做的事

- 不新增 MDS 式 resident HTTP/WebSocket daemon。
- 不恢复旧 workspace-local `systemd` / `cron` / `launchd` / `docker` scaffold 作为 active option。
- 不让 scheduler adapter 写 study truth、quality truth、publication truth、paper/current_package 或 artifact authority。
- 不把 Product Projection 页面刷新做成 runtime action。
- 不把 Hermes optional hosted executor 删除；只从 default dependency 里降级。

## 风险

- **双调度风险**：迁移时 Hermes 和 local 同时 enabled 会重复 tick。必须有 primary adapter lock 和 migration receipt。
- **状态投影断层**：如果 local adapter 不提供 latest run/session receipt，Portal/OPL 会丢失当前 Hermes 提供的可见性。必须先同构 status。
- **OS 差异**：launchd、systemd user、cron 的 missed-run / sleep / permission 行为不同。MAS status 必须写清 adapter semantics，不能假装完全一致。
- **OPL 包装联动**：OPL Full package、runtime tray、installer、docs 和 tests 都要一起改口径，否则用户仍会把 Hermes 当 required。
- **Hermes optional value 混淆**：non-GPT executor、hosted runtime、online-management gateway 仍有价值，但必须通过 explicit adapter/provider 进入。
