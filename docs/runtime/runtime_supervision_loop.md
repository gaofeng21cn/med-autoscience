# Runtime Supervision Loop

这份文档冻结 `MedAutoScience` 侧针对 `MedDeepScientist` managed runtime 的外环监管合同，也就是当前的 outer `supervisor loop` contract。

一句话结论：

- `MedAutoScience` 不是第二个 authority daemon
- 但它必须拥有稳定的 `supervision tick`
- 这个 tick 的长期托管 owner 可以是 `Hermes-Agent gateway cron`、Linux `systemd --user`、宿主 `cron`、macOS `launchd`，或由 OPL、Hermes、部署平台持有的外部容器环境调用 MAS CLI
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

该入口写出 workspace-level `artifacts/supervision/hourly/latest.json`，只消费 MAS durable truth surfaces：`study_runtime_status`、`study_progress`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json` 与 AI repair lifecycle。它的职责是形成 `action_queue`、`why_not_applied`、owner-visible request packet 与 `external_supervisor_required`，而不是直接修改 paper/current_package。

MAS 的内置 AI repair 是第一层修复机制。它使用默认执行器 policy：

- `executor_kind = codex_cli_default`
- `executor_name = Codex CLI`
- model、reasoning effort 与本机 Codex 配置保持继承
- chat-completion-only executor 禁止作为 repair executor

第一层的时间策略固定为：

- 内置 MAS AI 监测 tick：每 `300` 秒一次
- 无 meaningful artifact/progress 后 `1800` 秒进入 AI repair 判断
- AI doctor request 写出后 `900` 秒仍未被处理，升级为 timeout/platform repair
- 触发信号包括 `no_meaningful_progress`、`same_fingerprint_loop`、`read_churn_without_artifact_delta`、`stale_truth_surface` 与 `runtime_recovery_retry_budget_exhausted`

这些策略同时投影到 `two_layer_ai_repair_policy`，由 `runtime supervisor-scan` 和 `runtime supervisor-consume` 输出。这样前台看到“AI reviewer 队列积压”时，能同时看到内置 AI repair 是否已接上、是否超时，以及下一层开发者 supervisor 是否已到接手阈值。

当 `action_queue` 包含 `publication_gate_specificity_required` 或 `return_to_ai_reviewer_workflow` 时，supervisor scan 只能物化 request packet：

- `publication_gate_specificity_required` 的 owner 是 `publication_gate`
- `return_to_ai_reviewer_workflow` 的 owner 是 `ai_reviewer`
- request packet 的 authority 是 `request_only`
- 预期输出仍回到对应 owner 的 durable surface，例如 `publication_eval/latest.json`
- supervisor 本身不得写 `publication_eval/latest.json`、不得放宽 quality/publication gate、不得改 `paper/current_package` 或 `manuscript/current_package`

每个 study scan 还必须生成同一个 `owner_route`，并把它复制进 action、handoff packet、consumer dispatch 与 executor prompt contract。`owner_route` 是 `scan -> consume -> execute-dispatch -> rescan` 的路由票据，字段至少包括：

- `route_epoch`：来自 `StudyTruthKernel` 的 truth/authority epoch；缺失时用当前 status source 派生。
- `source_fingerprint`：当前 truth/status/progress/action 的稳定指纹。
- `current_owner` 与 `next_owner`：当前写入 owner 与下一可执行 owner。
- `owner_reason`：本轮路由原因，例如 `ai_reviewer_assessment_required`、`publication_gate_specificity_required` 或 runtime repair reason。
- `allowed_actions` / `blocked_actions`：本轮允许执行和明确禁止执行的 supervisor action。
- `idempotency_key`：由 study、epoch、fingerprint、owner、reason 和 action 集合派生；用于拒绝旧 dispatch。

consumer 只能传播该 route，不能重新解释 owner。request handoff 和 default executor dispatch 都必须通过同一 `owner_route.allowed_actions` gate；route 缺失、next owner 不匹配或 action 不在 allowed set 内时，只能写 blocked task，不能写 owner request packet。executor 执行前必须把 dispatch 中的 route 与最新 `hourly/latest.json` 的 route 对齐；如果 epoch、fingerprint、owner 或 reason 已变化，执行器必须写 `blocked_reason=owner_route_stale`，等待下一轮 consume 生成新 dispatch。

`allowed_actions` 只表达当前 `next_owner` 可以执行的动作，不是 action queue 的全集。scan 可以同时暴露后续 owner 的观测动作，例如 AI reviewer request；但本轮 dispatch executor 只能执行 owner_route 允许的动作。这样 runtime liveness 的 retry/exhausted 噪声、publication gate 的 blocker、AI reviewer 的质量判断和 artifact freshness 的修复任务不会在同一个 tick 互相抢 owner。

当 no-live / retry-exhausted 与当前 controller decision 同时存在时，scan 必须先做 current truth 对齐：

- `controller_decisions/latest.json` 的 action 必须是 runtime redrive 类 action；
- `controller_decisions/latest.json` 的 work-unit fingerprint 必须出现在当前 `publication_eval/latest.json`；
- next work unit 不能只是 `gate_needs_specificity` / `needs_specificity` terminal；
- 满足以上条件时，`runtime_platform_repair` 的 owner 是 `mas_controller`，authority 是 `observability_only`，reason 是 `runtime_controller_redrive_required`；
- relaunch 前必须把当前 controller decision 与 publication eval 中同 fingerprint 的具体 `specificity_targets` / actionable target 写入 runtime state 的 controller authorization；没有可执行 target 时不能把 no-live 状态误判成可恢复 runtime；
- 只有没有当前 controller route 或当前 route 已不对齐时，retry budget exhausted 才能升级为 external supervisor handoff。

完成态与停驻态也属于 current truth。若 `study_runtime_status` / `study_progress` 已经给出 `quest_status=completed` 且 completion contract resolved，或 `auto_runtime_parked.parked=true` / `canonical_runtime_action=await_explicit_resume` 且没有 live worker，scan 必须清空 stale lifecycle、不给 AI reviewer 或 external supervisor 排队，并把 `owner_route.current_owner` 投为 `controller_stop` 或 completed truth。manual hold、publishability stop-loss、package-ready handoff 和 external metadata pending 都只能等待显式 resume / revision intake，不能被 no-live 噪声、旧 publication gate 或旧 AI reviewer required 重新打开 writer。

同一轮 owner action 必须满足幂等合同。`route_epoch` 和 `source_fingerprint` 决定本轮 owner routing，具体 repo-side owner 还必须给自己的 work unit 写稳定 fingerprint：

- fingerprint 只表达语义输入，不表达普通观测时间；内容相同的 JSON/资产被同一 owner 重写后，不能因为 `mtime` 变化制造新 work unit。
- 对 package/submission authoring 类 repair，失败可在同 fingerprint 下重跑，因为缺失输出可能由同一 owner 重新生成。
- 对 non-authoring artifact input failure，例如 display input payload 缺必要字段，重复执行不会产生新信息；同 fingerprint、同 blocking artifact 的失败必须复用为稳定 blocked truth，并继续把具体 `blocking_artifact_refs` 暴露给 scan / progress / owner route。
- 因此 `scan -> consume -> execute-dispatch -> rescan` 的收敛结果应是“owner 前进或具体 blocker 稳定”，不能是同一 action 无限重放。

外层工程消费入口是：

```bash
medautosci runtime-supervisor-consume \
  --profile <profile> \
  --studies <study_id> <study_id> \
  --developer-supervisor-mode developer_apply_safe \
  --apply
```

该入口只把 scan queue 转成 owner handoff task，写入 workspace-level `artifacts/supervision/consumer/latest.json` / `history.jsonl` 以及 study-level consumer packet。它负责说明 `request_owner`、`required_output_surface`、`request_packet_ref`、forbidden surfaces 与 verification commands；它不执行 publication gate 或 AI reviewer 的专业判断，也不修改论文包。

从 2026-05-05 起，developer scheduler 的正式同 tick 行为是 `scan -> consume -> execute-dispatch`：

```bash
medautosci runtime supervisor-scan \
  --profile <profile> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe

medautosci runtime supervisor-consume \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply

medautosci runtime supervisor-execute-dispatch \
  --profile <profile> \
  --mode developer_apply_safe \
  --apply
```

如果未显式传 `--studies`，`supervisor-consume` 从最新 `hourly/latest.json` 的 `action_queue` 推导需要消费的 study 列表。consumer 会额外写出 study-level default executor dispatch request：

- `studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/<action_type>.json`

这个 dispatch request 是“把问题交给默认 Codex CLI 执行器”的机器可读派单面，包含 owner、输入 surface、必需输出 surface、forbidden surfaces 与 prompt contract。它不等同于 owner output；例如 AI reviewer 的 output 仍必须由 AI reviewer workflow 写回 owner-authorized durable surface，consumer 本身不得写 `publication_eval/latest.json`。

`runtime supervisor-execute-dispatch` 是第三步执行/落账面。它读取 `default_executor_dispatches/*`，校验 forbidden surfaces 和 prompt contract 后，只调用 owner 授权的 repo surface，或写出 `blocked_reason`。当前允许行为是：

- `publication_gate_specificity_required`：重放 `publication_gate` owner 的 gate report，并只物化 controller-owned `publication_eval/latest.json`，要求推荐动作带具体 `claim/figure/table/metric/source_path` targets。
- `runtime_platform_repair`：调用已有 runtime supervisor scan 的 safe platform repair path。
- `return_to_ai_reviewer_workflow`：如果没有结构化 AI reviewer record，不生成评审结论，写 `blocked_reason=owner_callable_surface_missing` 与 `required_repo_surface=structured_ai_reviewer_default_executor_workflow`。

执行器的默认读取权威是 workspace-level `artifacts/supervision/consumer/latest.json`。无论调用方是否显式传 action type，`runtime supervisor-execute-dispatch` 都只能从 consumer latest 当前列出的 ready dispatch 中筛选执行；study-level `default_executor_dispatches/*.json` 目录里的旧文件不能单独作为执行票据。这样可以避免旧 `runtime_platform_repair` 或旧 `return_to_ai_reviewer_workflow` dispatch 在下一轮 scan/consume 已经改判 owner 后继续执行。

publication gate 与 AI reviewer 的 currentness 使用 work-unit fingerprint，而不是最近生成时间：

- gate report 每次重放都可能生成新的 `generated_at`，这个时间戳不能单独使 AI reviewer-backed `publication_eval/latest.json` 过期。
- AI reviewer-backed eval 只有在 `study_id`、`quest_id`、`paper_root` 匹配，并且推荐动作携带同一个 publication work-unit fingerprint 时，才能覆盖同语义 gate 重放。
- 对 `bundle_stage_blocked` 的 specificity gate，AI reviewer eval 还必须携带完整 `claim/figure/table/metric/source_path` specificity targets；否则 publication gate 必须刷新 mechanical projection，补齐当前阻断目标，并重新要求 AI reviewer workflow。
- mechanical projection 只能具体化 blocker 和 owner handoff，不能关闭 AI reviewer 质量判断；AI reviewer output 也不能用缺 target 的旧记录阻止 publication gate 更新当前 blocker targets。

controller work-unit evidence adoption 采用同一条 AI-first 边界：

- adoption 只识别客观、受控、可归属的 evidence，例如 owner-authorized output、controller work-unit fingerprint、artifact checksum、restore proof、runtime event、runtime supervision tick、worker liveness 和 freshness/currentness proof。
- adoption 不判断医学叙事质量、科学结论质量、publishability 或 submission readiness；这些判断仍由 AI reviewer workflow、publication gate 与 MAS study truth surface 持有。
- `cold_archive`、`report_history`、runtime report store 和 lifecycle restore proof 只能作为 restore/report evidence source；它们可以证明历史报告、运行事件或 artifact 可恢复，但不能替代 `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_charter`、`evidence_ledger`、`review_ledger` 或当前 paper/package authority。
- 当当前 controller work unit 的受控证据被采纳后，runtime status 使用 `controller_work_unit_evidence_adopted` 表示本轮不再 relaunch 同一个 work unit；下一 owner 是 publication gate / controller recheck，且不得把该状态解释为 write、finalize、submission package 或 publishability 放行。
- 若受控 worker 已经完成同一 work unit，supervisor 必须进入 gate recheck、owner route 前进或下一 owner handoff；不得因为 stale queue、fresh timestamp、archived report 或 report replay 重复派发同一 work unit。
- repo-side fix landed、archive proof verified、report history 可读取，只能说明平台或证据面已有修复证据；它不等同于具体 study 已恢复、live worker 已存在、论文质量已放行或 `current_package` / `submission_minimal` 已成为当前 authority。

runtime repair 与 publication gate 的 owner routing 使用 controller terminal 证据，而不是泛化的 gate blocker：

- `gate_specificity.required=true` 本身不足以阻止 runtime relaunch；异常 stopped、paused/resume 无 live worker、active/running 但无 live worker、retry budget exhausted 仍必须进入 runtime platform repair。
- 已交付人审/投稿包且无 live worker 的 parked handoff 是例外：当 `auto_runtime_parked` 或 delivery/current_package handoff 证据成立时，平台 repair redrive 不能自动重开 writer，只能等待显式 resume / revision intake。
- 若 latest task intake 明确是 reviewer revision 或 submission refresh，用户显式唤醒可以释放 delivered-package parking；`runtime_platform_repair` source 不能借同一个 intake 自动释放该停驻。
- 只有 resume/postcondition 或 runtime status 明确给出 `gate_needs_specificity` / `needs_specificity` / `publication_gate_specificity_required`，并且来源是 controller work-unit authorization 时，supervisor 才把 no-live-worker relaunch 转交给 publication gate。
- 若 stale specificity terminal 已被带完整 targets 的 publication eval 证明满足，platform repair 可以清掉旧 terminal，并把队列推进到下一 owner；已 applied 的 runtime repair 不应继续留在当次 action queue。

前台兼容性核对必须把 project / study / runtime owner 分开：

- NF-PitNET 003 不属于 DM002/DM003 runtime 风险核对的目标，不因 DM lifecycle 或 evidence adoption 文档更新触碰其 paper、current package、submission minimal 或 runtime-owned surface。
- DM002 / DM003 是否 live、是否 no-live-worker、是否 stale、是否需要人工介入，必须 fresh 读取 `study_runtime_status`、`study_progress`、`runtime_supervision/latest.json`、`publication_eval/latest.json` 与 `controller_decisions/latest.json`；不能用 repo commit、lifecycle migration ledger、cold archive 或 report history 代替当前 truth。
- 如果存在 live managed runtime，或 `study_runtime_status.execution_owner_guard.supervisor_only=true`，前台只能进入 supervisor-only 监管态；不得直接写 runtime-owned surface，也不得修改 DM workspace 的论文正文、`current_package` 或 `submission_minimal`。
- 如果当前 truth 是 `quest_status=active` 但 `active_run_id=null` / no live session / retry budget exhausted，前台只能报告 live 兼容风险并等待 controller/runtime owner 决策；不得把 repo 修复完成表述为 study 已恢复。

第二层 Developer Supervisor Mode 的时间策略固定为：

- scheduler/heartbeat：每 `3600` 秒一次
- owner request `2` 小时未被 pickup，标记 `owner_pickup_overdue`
- action queue `6` 小时仍未被消费或仍无进展，标记 `developer_supervisor_attention_required`
- developer heartbeat 必须评估内置 AI monitoring/repair 是否失效，并在 `developer_apply_safe` 与 GitHub gate 通过时消费队列、写 default executor dispatch request、执行 ready dispatch，或明确 blocked reason / next owner

这解释了之前的故障模式：heartbeat 只运行 `supervisor-scan` 时，系统能准确报告 `AI reviewer queue` 或 `publication_gate_specificity_required` 积压，但没有运行 `supervisor-consume`，也没有生成默认 Codex executor dispatch request，所以“AI 监测发现问题”与“AI 修复真正被派单执行”之间断开。后续如果只运行到 `supervisor-consume`，也只能得到 `dispatch_status=ready`；必须同 tick 运行 `supervisor-execute-dispatch`，才能把 ready dispatch 推进为 `executed` 或明确 blocked。

Developer Supervisor Mode 有三个正式模式：

- `internal_only`：只运行 MAS 内部 AI doctor/self-healing；不启用外层工程代理。
- `external_observe`：外层只读巡检，只投影 stale/blocked/why_not_applied，不生成可消费 safe-action request。
- `developer_apply_safe`：开发环境模式，允许 `supervisor-scan --apply-safe-actions --developer-supervisor-mode developer_apply_safe` 写 supervision/control/autonomy request、handoff packet 与 action queue。

`developer_apply_safe` 还受 GitHub 用户门控保护：本机 `gh api user --jq .login` 必须返回 `gaofeng21cn`，否则 effective mode 自动降级到 `external_observe`，并投影 `github_user_not_authorized_for_developer_supervisor_mode`。这个门控用于防止普通用户或生产研究环境意外获得 repo-level developer supervisor authority。

`Codex App heartbeat` 不是这条 contract 的依赖。Codex App 可以作为本机开发环境的一个外部 scheduler 调用该入口，但 MAS 运行环境必须同样支持 Linux `systemd --user`、宿主 `cron`、macOS `launchd` 兼容路径，以及由 OPL、Hermes 或部署平台提供的容器环境。

workspace bootstrap 会渲染 portable scheduler entry 与示例模板：

- `ops/medautoscience/bin/supervisor-scan`
- `ops/medautoscience/bin/supervisor-consume`
- `ops/medautoscience/bin/supervisor-execute-dispatch`
- `ops/medautoscience/bin/watch-runtime-service-runner`
- `ops/medautoscience/supervisor/systemd/medautoscience-supervisor-scan.service`
- `ops/medautoscience/supervisor/systemd/medautoscience-supervisor-scan.timer`
- `ops/medautoscience/supervisor/cron/supervisor-scan.cron`
- `ops/medautoscience/supervisor/launchd/README.md`

`systemd` 与 `cron` 模板调用 `watch-runtime-service-runner`，由 runner 在同一小时级 tick 内依次执行 `supervisor-scan`、`supervisor-consume`、`supervisor-execute-dispatch`。Codex App heartbeat 仍只是本机兼容 scheduler；MAS 架构依赖的是 portable scheduler entry 和这些 durable surfaces。

`medautosci runtime ensure-supervision --manager systemd|cron|launchd` 返回可复制的安装命令和模板路径，并验证当前 workspace 是否已有可执行的 `supervisor-scan` entry。显式追加 `--write-install-proof` 时，它会写出 workspace-level `artifacts/supervision/install_proof/latest.json`，记录 manager、scheduler owner、安装命令、状态检查命令、预期产物、freshness、safe-action mode、GitHub gate 与 host service claim。这个接口只生成 scheduler instruction / install proof，不在没有真实宿主安装 evidence 时声称宿主 service 已安装；安装动作仍归属 host operator 或外部 scheduler。

容器环境不是 MAS-owned runtime。MAS 不维护 `medautoscience:latest` 镜像，也不生成 Kubernetes CronJob manifest。容器、volume、gateway、scheduler 与镜像发布由 OPL、Hermes 或部署平台持有；容器内只需要能调用 MAS CLI，例如：

```bash
medautosci runtime supervisor-scan \
  --profile <profile> \
  --apply-safe-actions \
  --developer-supervisor-mode developer_apply_safe
```

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

### 5.5 stopped submission milestone parking

如果 quest 已经进入 `stopped`，但 MAS 的当前 controller truth 表明它只是 submission/finalize 里程碑停车，外环必须刷新 controller-owned parked decision，并把该状态写成正式停车，而不是把旧 stopped state 解释成可人工 patch 的许可。

在 `developer_apply_safe` 且 GitHub gate 允许的前提下，supervisor scan 可以执行的动作只有：

- 通过 runtime backend `stop_quest` 或 already-stopped 结果确认 runtime 资源已释放
- 写 `artifacts/autonomy/repair_lifecycle/latest.json`
- 标记 `authority = controller_stop`
- 标记 `state = parked`
- 明确 `paper_package_mutation_allowed = false`
- 明确 `manual_study_patch_allowed = false`
- 明确 `quality_gate_relaxation_allowed = false`
- 明确 `medical_claim_authoring_allowed = false`

这条规则只收口 runtime/resource 与 controller decision projection。后续如果用户、导师或审稿意见重新打开同一 paper line，仍必须走 durable revision intake 与 MAS/MDS relaunch/resume，再从 canonical paper authority 重新生成投影包。

## 6. durable surfaces

这条链路当前正式落到下面几个稳定表面：

- quest-level `runtime_watch/latest.json`
- study-level `studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json`
- study-level `studies/<study_id>/artifacts/autonomy/repair_lifecycle/latest.json`
- workspace-level `artifacts/supervision/hourly/latest.json`
- workspace-level `artifacts/supervision/consumer/latest.json`
- workspace-level `artifacts/supervision/consumer/history.jsonl`
- study-level `studies/<study_id>/artifacts/supervision/consumer/<action_type>.json`
- study-level `studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/<action_type>.json`
- study-level `studies/<study_id>/artifacts/supervision/consumer/default_executor_execution/latest.json`
- study-level `studies/<study_id>/artifacts/supervision/requests/publication_gate_specificity/latest.json`
- study-level `studies/<study_id>/artifacts/supervision/requests/ai_reviewer/latest.json`
- quest-level `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- study-level `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- physician-facing projection `study_progress`

其中：

- `runtime_watch/latest.json` 负责 quest controller scan truth
- `artifacts/runtime/health/latest.json` 负责 reducer-owned runtime health truth
- `runtime_supervision/latest.json` 负责 outer-loop supervision read model，并携带 `runtime_health_epoch`
- `repair_lifecycle/latest.json` 负责投影 AI doctor repair 从 request、diagnosis、repair action 到 apply attempt 的生命周期
- `artifacts/supervision/hourly/latest.json` 负责跨 study 巡检 action queue 与 why-not-applied 投影
- `artifacts/supervision/consumer/latest.json` 与 study-level consumer packets 负责把外层 queue 消费成 request-owner handoff task
- `default_executor_dispatches/*` 负责把未被 owner 接手的 queue 转成默认 Codex CLI 执行器派单，不承担 publication/AI reviewer output authority
- `default_executor_execution/latest.json` 负责记录 ready dispatch 的执行尝试、owner callable surface、blocked reason 与 written execution ledger
- `artifacts/supervision/requests/*/latest.json` 负责保存 owner-visible request packet；它们是 request surface，不是 owner output surface
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
- 外部 OPL、Hermes 或部署平台提供的容器环境，周期性调用 MAS CLI
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
