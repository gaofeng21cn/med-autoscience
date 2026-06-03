# Progress-First Stage Outcome Runbook

Owner: `MedAutoScience`
Purpose: `operator_runbook`
State: `active_runtime_support`
Machine boundary: 本文是人读 operator / docs runbook。机器真相继续归 MAS controller/read-model output、OPL current-control-state、owner receipts、typed blockers、runtime artifacts、publication eval、controller decisions 和真实 workspace evidence。本文不授权手写 runtime-owned study truth、paper body、publication verdict、controller decision、submission package 或 `current_package`。

## 适用范围

本 runbook 用于 DM002 / DM003 这类 Progress-first / AI-first 论文线停滞判断：系统已经能看到 receipt、currentness、read-model、provider handoff 或 `current_executable_owner_action`，但 operator 需要判断当前 stage 是否真正前进、是否应 admission 到 OPL/provider/scheduler，还是仍卡在 hard gate。

它不用于声明终局 readiness。publication-ready、submission-ready、paper closure、artifact authority、memory authority 和 `current_package` 更新仍只能来自对应 MAS owner surface、AI reviewer / publication gate verdict、owner receipt 和 artifact/package freshness proof。

## 非终局 stage outcome

非终局 stage 只能落到以下六类 outcome；不得用 `done`、`complete`、`healthy`、`all clear`、`ready` 这类泛化词关闭 stage。

| outcome | 含义 | operator 下一步 |
| --- | --- | --- |
| `running` | OPL current-control / runtime liveness 明确 `running_provider_attempt=true`，且存在 active stage attempt、run 或 workflow ref。 | 监督 active attempt；不要重复 materialize、dispatch 或 owner-route reconcile 同一 work unit。 |
| `ready_for_owner_action` | `current_executable_owner_action` 完整，hard gate 缺席，但尚未观察到 provider running proof。 | admission 到 OPL/provider/scheduler 或 MAS owner callable；若只写出 handoff，下一 owner 是 provider admission。 |
| `waiting_human` | 当前 owner surface 明确 human gate、approval、pause/resume 或不可由 AI/provider 继续的人工决策。 | 等人工决定；不得用 provider redrive 绕过。 |
| `blocked_with_typed_owner` | MAS-owned typed blocker 明确 current owner、work unit、source/runtime/truth currentness refs、forbidden-write proof 或 no-progress reason。 | 交给 blocker owner、mechanism repair、human gate 或 stop-loss candidate；不得重跑同义 receipt/reconcile。 |
| `terminal_success` | 当前非终局 work unit 已产出可消费 owner receipt、paper/artifact delta、reviewer/gate delta、stable typed blocker 或 next owner handoff，并且后续 owner 已可被投影。 | 消费 receipt 并进入下一 owner；不能把它升级成 publication/submission ready。 |
| `terminal_stop_loss` | same owner/work unit/source currentness 已耗尽 redrive budget，或 hard blocker 无法在当前 lane 内解除。 | 记录 stop-loss owner、原因和允许重开条件；不得继续 ordinary dispatch loop。 |

`receipt_consumed` 是观测状态，不是 `ready_for_owner_action`。它必须立刻让位给下一 owner projection、typed blocker、human gate、running proof 或 stop-loss；若没有下一项，问题归入 read-model/currentness 修复，而不是继续消费同一 receipt。

## 分账规则

paper / deliverable progress 只承认五类 owner delta：

- MAS owner receipt。
- canonical paper / artifact delta。
- independent AI reviewer、auditor 或 publication-gate delta。
- stable typed blocker，且 blocker 明确 owner、work unit 和缺失 evidence。
- next owner handoff，且 handoff 带 current owner、work unit、required output surface、source refs 与 write boundary。

以下内容只能记为 platform repair / observability：telemetry、duration/token/cost 补齐、stage-log accounting、dispatcher hydration、receipt reconciliation、read-model currentness hygiene、OPL refs-only ledger record/verify、provider liveness/projection refresh、Portal wording/card 修复、bounded product-entry refresh。

同一轮同时出现 paper delta 和 platform repair 时，token / time 分账优先归 platform repair；paper / deliverable delta 只记录真实 owner delta 的 surface refs，不把平台修复耗时混报成论文推进。

## AI-first admission

AI-first 的 admission 锚点是 `current_executable_owner_action`，不是 `next_system_action` 文案。

当 `current_executable_owner_action` 已同时具备以下字段，且 hard gate 缺席时，Progress-first operator 必须把下一步交给 OPL/provider/scheduler 或 MAS owner callable：

- current owner。
- controller action / allowed action。
- work unit id 或 work-unit fingerprint。
- required output surface。
- source refs，包括 truth/runtime/source/eval currentness basis。
- allowed write boundary 与 forbidden write boundary。
- dispatchable owner-route attempt envelope。

`provider_attempt_start_requested` / `admission_requested` 表示可交给 provider 或 owner callable；它不是 running proof。只有 OPL current-control 明确 `running_provider_attempt=true` 且存在 active stage attempt、run 或 workflow ref 时，才能写成 `provider_attempt_running_proven=true` 或 `running`。

如果 admission request 已写出但缺 running proof，下一 owner 是 OPL worker / scheduler / provider attempt admission。不要把控制权退回 MAS receipt reconcile、read-model hydration、telemetry completeness、doctor explanation 或 operator wording review。

## Hard gates

preflight 只保留以下 hard gates：

- `human_gate`：需要用户、PI、医生、外部编辑或显式 approval/resume。
- `forbidden_authority_write`：当前 action 会写 MAS 禁止 surface，例如未授权的 study truth、runtime-owned state、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission/current package 或非当前 owner 的 paper surface。
- `missing_owner_callable`：当前 owner/action 没有可调用 MAS owner callable、domain-handler dispatch 或 OPL provider entry。
- `missing_source_or_data`：当前 work unit 的必需 source/data/evidence ref 缺失，无法形成 owner output 或 typed blocker。
- `irreversible_mutation`：会执行不可逆数据、artifact、submission、cleanup、external side effect 或权限变更，需要显式授权。

不属于 hard gate 的缺口必须单独列为 observability/platform repair：telemetry 缺失、token/cost 缺失、read-model 字段不完整、Portal 文案漂移、diagnostic completeness、低信息 scheduler tombstone、当前性解释缺口。只有这些缺口影响 owner-route identity、required source/data 或 forbidden write boundary 时，才按对应 hard gate 归类。

## DM002 / DM003 stable verification commands

以下命令只读或 MAS controller-authorized；运行前先确认 profile 指向 DM-CVD workspace，不要手写 DM-CVD workspace truth。若 workspace root 下没有已持久化 profile，先用临时 profile 运行只读 smoke；临时 profile 只描述 workspace 路径，不写 study truth、runtime-owned state、paper、`publication_eval/latest.json`、`controller_decisions/latest.json` 或 package。

```bash
rtk git status --short --branch
```

```bash
DM_CVD_ROOT=/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk
DM_CVD_PROFILE="$(mktemp "${TMPDIR:-/tmp}/dm-cvd-mas-profile.XXXXXX.toml")"
cat >"${DM_CVD_PROFILE}" <<'EOF'
name = "dm-cvd-mortality-risk-workspace"
workspace_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk"
runtime_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/runtime/quests"
studies_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies"
portfolio_root = "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/portfolio"
default_publication_profile = "general_medical_journal"
default_citation_style = "AMA"
enable_medical_overlay = true
EOF
```

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile "${DM_CVD_PROFILE}" \
  --study-id 002-dm-china-us-mortality-attribution \
  --format json
```

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli study progress \
  --profile "${DM_CVD_PROFILE}" \
  --study-id 003-dpcc-primary-care-phenotype-treatment-gap \
  --format json
```

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli runtime domain-health-diagnostic \
  --profile "${DM_CVD_PROFILE}" \
  --studies 002-dm-china-us-mortality-attribution 003-dpcc-primary-care-phenotype-treatment-gap \
  --request-opl-stage-attempts \
  --dry-run
```

上述 dry-run 是只读 admission/status smoke。`--request-opl-owner-route-reconcile` 是安全推进 tick，CLI 要求显式 `--apply`，避免 operator 把会写 refs-only reconcile/materialize/dispatch surface 的动作误当成纯只读检查。

```bash
rtk scripts/run-python-clean.sh -m med_autoscience.cli runtime domain-health-diagnostic \
  --profile "${DM_CVD_PROFILE}" \
  --studies 002-dm-china-us-mortality-attribution 003-dpcc-primary-care-phenotype-treatment-gap \
  --request-opl-stage-attempts \
  --request-opl-owner-route-reconcile \
  --apply
```

Use `--apply` only when the lane is explicitly allowed to drive MAS controller refs-only owner-route reconcile/materialize/dispatch. It must not write runtime-owned study truth, canonical paper body, `publication_eval/latest.json`, `controller_decisions/latest.json`, submission/current package, memory body or artifact body outside MAS owner-authorized surfaces.

When validating a docs-only change in this repo, use documentation review plus git diff/status. Do not run live `--apply` only to prove this runbook.

## 错误路径

不要再走以下路径：

- 把 `active_run_id` 当作 running proof。running proof 只来自 OPL current-control / runtime liveness 的 `running_provider_attempt=true` 和 active attempt/run/workflow ref。
- 把 `next_system_action` 文案当作 admission authority。authority 必须来自 `current_executable_owner_action` 与 owner-route attempt envelope。
- 把 `receipt_consumed` 显示成 `ready_owner_action` 或等待 owner pickup。它应触发下一 owner projection 或暴露 currentness 缺口。
- 把 provider handoff 写出当作 provider attempt 已启动。缺 running proof 时只能写 `provider_handoff_written_admission_pending`。
- 把 telemetry、duration/token/cost、Portal card wording、read-model hygiene、refs-only ledger record/verify 当成 paper progress。
- 用显式 `--action-types` 作为正常 Progress-first 必需步骤；它只用于诊断、限流或人工指定，默认 dispatch 必须消费 current ready dispatch。
- 用 broad recursive scan、mtime、旧 request lifecycle、旧 generated_at、stale consumer dispatch 或旧 package freshness proof 覆盖当前 owner/work-unit currentness。
- 手工写 DM-CVD study truth、runtime-owned state、canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal/`、`manuscript/current_package/` 或 submission package 来关闭 currentness 问题。
- 把 repo-side docs/code fix landed 推断成 live study 已恢复。每次状态判断都必须重新读取 live study/runtime surfaces。
