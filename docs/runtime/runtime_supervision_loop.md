# Runtime Supervision Loop

这份文档冻结 `MedAutoScience` 侧针对 `MedDeepScientist` managed runtime 的外环监管合同，也就是当前的 outer `supervisor loop` contract。

一句话结论：

- `MedAutoScience` 不是第二个 authority daemon
- 但它必须拥有稳定的 `supervision tick`
- 这个 tick 的长期托管 owner 可以是 `Hermes-Agent gateway cron`、Linux `systemd --user`、宿主 `cron`、Docker/Kubernetes one-shot scheduler 或 macOS `launchd`
- 这个 loop 的职责是持续发现掉线、执行 reconciliation、写出 durable supervision surface，并把结果翻译成前台可见的人话

## 1. 总目标

我们要解决的不是“把日志看起来拼热闹”，而是下面这三个正式目标：

- worker 掉线后，外层必须能在有限时间内发现
- 发现后必须按固定规则自动恢复或升级
- 前台必须能持续看到几点几分发生了什么、研究推进到哪一步、现在是否需要人工介入

这三个目标必须同时成立，才算 managed runtime 真正可托管。

除此之外还有一条 fail-closed 边界：

- 如果 outer supervisor tick 自己已经缺失或陈旧，系统也不能继续假装“MAS 仍在稳定监管”
- 这种情况必须作为正式监管异常直接暴露到 status / progress surface

## 2. authority 边界

这里的外环应按三层分工理解：

- `Hermes-Agent`
  - 长期运行与托管能力 owner
- `MedAutoScience`
  - 医学研究治理、supervision judgment、projection 与 reconciliation owner
- `MedDeepScientist`
  - quest executor / research backend

对应的监管外环是：

- `Hermes-hosted`
- `controller-judged`
- `tick-driven`
- `fail-closed`

它不是：

- 第二个 authority daemon
- 第二份 runtime truth
- 直接接管 `MedDeepScientist` 生命周期的替代物

所以权责边界保持不变：

- `MedDeepScientist` 持有 inner runtime execution truth
- `MedAutoScience` 持有 outer supervision / projection / reconciliation truth

## 3. 正式执行形态

当前正式 outer-loop tick 入口是：

- `medautosci runtime watch --runtime-root <runtime_root> --apply --ensure-study-runtimes --profile <profile>`

```bash
medautosci runtime watch \
  --runtime-root <runtime_root> \
  --apply \
  --ensure-study-runtimes \
  --profile <profile>
```

这个 tick 每次至少做四件事：

1. 读取 managed study 的 `study_runtime_status` 或 `ensure_study_runtime`
2. 扫描 live quest 的 `runtime_watch`
3. 生成 study-owned `runtime_supervision/latest.json`
4. 必要时写出或刷新 `runtime_escalation_record.json`

也就是说，外环的核心不是“循环本身”，而是单次 tick 的 controller contract。

跨 study 的小时级巡检入口是 portable supervisor scan：

```bash
medautosci runtime supervisor-scan \
  --profile <profile> \
  --studies <study_id> <study_id> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe
```

该入口写出 workspace-level `artifacts/supervision/hourly/latest.json`，只消费 MAS durable truth surfaces：`study_runtime_status`、`study_progress`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json` 与 AI repair lifecycle。它的职责是形成 `action_queue`、`why_not_applied` 与 `external_supervisor_required`，而不是直接修改 paper/current_package。

Developer Supervisor Mode 有三个正式模式：

- `internal_only`：只运行 MAS 内部 AI doctor/self-healing；不启用外层工程代理。
- `external_observe`：外层只读巡检，只投影 stale/blocked/why_not_applied，不生成可消费 safe-action request。
- `developer_apply_safe`：开发环境模式，允许 `supervisor-scan --apply-safe-actions --developer-supervisor-mode developer_apply_safe` 写 supervision/control/autonomy request、handoff packet 与 action queue。

`developer_apply_safe` 还受 GitHub 用户门控保护：本机 `gh api user --jq .login` 必须返回 `gaofeng21cn`，否则 effective mode 自动降级到 `external_observe`，并投影 `github_user_not_authorized_for_developer_supervisor_mode`。这个门控用于防止普通用户或生产研究环境意外获得 repo-level developer supervisor authority。

`Codex App heartbeat` 不是这条 contract 的依赖。Codex App 可以作为本机开发环境的一个外部 scheduler 调用该入口，但 MAS 运行环境必须同样支持 Linux、cron、systemd、Docker one-shot 与 Kubernetes CronJob。

workspace bootstrap 会渲染 portable scheduler entry 与示例模板：

- `ops/medautoscience/bin/supervisor-scan`
- `ops/medautoscience/supervisor/systemd/medautoscience-supervisor-scan.service`
- `ops/medautoscience/supervisor/systemd/medautoscience-supervisor-scan.timer`
- `ops/medautoscience/supervisor/cron/supervisor-scan.cron`
- `ops/medautoscience/supervisor/docker/supervisor-scan.oneshot.sh`
- `ops/medautoscience/supervisor/kubernetes/supervisor-scan-cronjob.yaml`
- `ops/medautoscience/supervisor/launchd/README.md`

`medautosci runtime ensure-supervision --manager systemd|cron|docker|launchd` 返回可复制的安装命令和模板路径，并验证当前 workspace 是否已有可执行的 `supervisor-scan` entry。显式追加 `--write-install-proof` 时，它会写出 workspace-level `artifacts/supervision/install_proof/latest.json`，记录 manager、scheduler owner、安装命令、状态检查命令、预期产物、freshness、safe-action mode、GitHub gate 与 host service claim。这个接口只生成 scheduler instruction / install proof，不在没有真实宿主安装 evidence 时声称宿主 service 已安装；安装动作仍归属 host operator 或外部 scheduler。

同时，外环还必须对“最近一次 supervisor tick 是否仍然新鲜”给出正式判断：

- `fresh`
- `missing`
- `stale`
- `invalid`

只要不是 `fresh`，前台就必须明确表述为“监管心跳异常”，不能继续把研究描述成被持续托管监管。

## 4. fail-closed live 语义

外层只有在下面条件同时满足时，才允许把运行面声明为 live managed runtime：

- `runtime_liveness_audit.status == live`
- `runtime_audit.worker_running == true`
- `active_run_id != null`

只要缺任一项，就不能再宣称“这是一个正常 live 的 managed runtime”。

这时必须明确落在以下之一：

- `recovering`
- `degraded`
- `external_supervisor_required`

这就是 fail-closed 语义。

## 5. reconciliation 规则

外环针对“表面 active/running、实际没有 live worker”的正式处理规则固定为：

### 5.1 首次发现掉线

- 写 `runtime_supervision/latest.json`
- `health_status = recovering` 或 `degraded`
- 若本次 tick 允许 apply，就调用 `ensure_study_runtime`

### 5.2 恢复成功

- 下一次 tick 确认：
  - `runtime_liveness_audit.status == live`
  - `worker_running == true`
  - `active_run_id != null`
- `runtime_supervision/latest.json` 回到 `live`
- `last_transition = recovered`

### 5.3 恢复连续失败

- `consecutive_failure_count` 增长
- 达到阈值后升级为 `external_supervisor_required`
- 写 `runtime_escalation_record.json`
- 前台和 Gateway/MAS 都必须看到明确的平台级 supervisor 介入信号
- control plane 不得继续把该状态伪装成 recovering dispatch

### 5.4 controller-owned finalize parking

如果 quest 进入下面这类停车态：

- `status = active` 或 `running`
- `active_run_id = null`
- `continuation_policy = wait_for_user_or_resume`
- `continuation_reason = unchanged_finalize_state`

那么 MAS 必须把它视为 `controller-owned parking`，而不是默认等用户。

也就是说：

- `finalize_ready` 只代表 paper-line-local recommendation
- 是否真的进入 `finalize`，仍由 MAS 外环根据 `publication_supervisor_state`、`controller_decisions/latest.json`、`pending_user_interaction`、`interaction_arbitration` 统一仲裁
- 只有当显式 contract 表明确实需要 external secret / credential 或 controller 要求人工确认时，才允许保持 user-blocking
- 否则这类 parking 必须被 MAS 自动吸收并恢复，不得把程序内 routing 判断抛给用户

## 6. durable surfaces

这条链路当前正式落到下面几个稳定表面：

- quest-level `runtime_watch/latest.json`
- study-level `studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json`
- study-level `studies/<study_id>/artifacts/autonomy/repair_lifecycle/latest.json`
- workspace-level `artifacts/supervision/hourly/latest.json`
- quest-level `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- study-level `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- physician-facing projection `study_progress`

其中：

- `runtime_watch/latest.json` 负责 quest controller scan truth
- `artifacts/runtime/health/latest.json` 负责 reducer-owned runtime health truth
- `runtime_supervision/latest.json` 负责 outer-loop supervision read model，并携带 `runtime_health_epoch`
- `repair_lifecycle/latest.json` 负责投影 AI doctor repair 从 request、diagnosis、repair action 到 apply attempt 的生命周期
- `artifacts/supervision/hourly/latest.json` 负责跨 study 巡检 action queue 与 why-not-applied 投影
- `study_progress` 负责把这些 truth 翻译成医生/PI 能看懂的前台进度

不要把 runtime health truth 硬塞进：

- `publication_eval/latest.json`
- `controller_decisions/latest.json`

这两个表面仍然各自承担发表判断与 controller 决策的真相职责。

运行健康的用户可见动作必须来自 `RuntimeHealthKernel.canonical_runtime_action`；`last_launch_report`、`runtime_watch/latest.json` 与 `runtime_supervision/latest.json` 都只能作为 input event 或 read model。

## 7. 前台可见语义

只要 `runtime_supervision/latest.json` 处于：

- `recovering`
- `degraded`
- `external_supervisor_required`

前台就必须优先展示 runtime health，而不是被论文阶段覆盖。

也就是说，即使 paper line 正在 `finalize`，只要 worker 掉线，前台也要先明确告诉医生：

- 什么时候发现掉线
- 是否已经尝试恢复
- 当前是恢复中、恢复失败，还是已升级
- 下一步系统准备做什么
- 是否已经需要人工介入

只要 AI repair 处于 `ready_for_repair` 但未 apply，前台必须展示：

- `blocked_reason`
- `next_owner`
- `external_supervisor_required`
- 最近一次 `last_apply_attempt_at`

禁止只显示 `awaiting_ai_doctor` 或 `ready_for_repair` 而不解释为什么没有执行。

## 8. 与常驻 daemon 的关系

从 contract 角度说，`MedAutoScience` 没有必要因为这个问题变成第二个 authority daemon。

更合理的形态是：

- 先把单次 `supervisor tick` 做严谨
- 再由外部 scheduler 周期调用它

可接受的 scheduler 形态包括：

- `Hermes gateway cron`
- Linux `systemd --user`
- 宿主 `cron`
- Docker one-shot container，由外部 cron 或 Kubernetes CronJob 调度
- macOS `launchd` 兼容路径

MAS 负责“这一跳应该怎么判、怎么恢复、怎么写 durable truth”。scheduler 只负责按周期调用，不持有医学或 runtime authority。

这能保证未来无论宿主变成 Codex、Gateway 还是 managed web runtime，合同都不漂。

## 9. 当前这条外环能恢复到哪里

当前这条外环已经能诚实做到：

- 发现 live worker 掉线、finalize parking 或恢复失败
- 通过 backend contract 请求 `ensure_study_runtime`、resume、relaunch 这类受控恢复
- 把 `clinician_update`、`next_action_summary`、`needs_human_intervention` 写入 `runtime_supervision/latest.json`
- 在连续失败后升级为 `external_supervisor_required`，并把平台级 supervisor 介入信号写到 `runtime_escalation_record.json`、`repair_lifecycle/latest.json`、hourly supervision scan 与 `study_progress`

但它当前还不能诚实宣称：

- 宿主上已经存在一个独立安装的 Hermes host
- 在 external `Hermes` runtime 尚未独立落地时，完全脱离 `MedDeepScientist` engine 自行接管执行

也就是说，当前 outer loop 擅长的是监管、恢复请求、告警升级与人话汇报；它不是在 external gate 未解除前平地再造一个新的 execution engine。
