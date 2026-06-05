# Progress-First Stage Outcome Runbook

Owner: `MedAutoScience`
Purpose: `operator_runbook`
State: `active_runtime_support`
Machine boundary: 本文是人读 operator / docs runbook。机器真相继续归 MAS controller/read-model output、OPL current-control-state、owner receipts、typed blockers、runtime artifacts、publication eval、controller decisions 和真实 workspace evidence。本文不授权手写 runtime-owned study truth、paper body、publication verdict、controller decision、submission package 或 `current_package`。

## 适用范围

本 runbook 用于 DM002 / DM003 这类 Progress-first / AI-first 论文线停滞判断：系统已经能看到 receipt、currentness、read-model、provider handoff 或 `current_executable_owner_action`，但 operator 需要判断当前 stage 是否真正前进、是否应 admission 到 OPL/provider/scheduler，还是仍卡在 hard gate。

它不用于声明终局 readiness。publication-ready、submission-ready、paper closure、artifact authority、memory authority 和 `current_package` 更新仍只能来自对应 MAS owner surface、AI reviewer / publication gate verdict、owner receipt 和 artifact/package freshness proof。

Stage Operating Layer 是 Progress-first 的第一读面：非终局 stage 首屏必须只读呈现 `stage_kernel_projection` 派生的 current stage、artifact roles、missing outputs、accepted receipts、semantic validation、consumability、lineage、retention / restore、current pointer、blocker、next owner 和 provider liveness。`stage_artifact_index` / Stage Deliverable Index 仍然重要，但它是 derived refs-only locator projection，不是 study truth、artifact truth、quality verdict 或 publication readiness authority。缺 `stage_kernel_projection` 时，Workbench / Progress Portal 必须 fail-closed 为 pending lane；不得从 `stage_artifact_index`、controller/read-model/currentness、telemetry、evidence-tail 或 repair 诊断推断 primary progress。

SQLite / State Index Kernel 的读法同样只属于 operating index：`contracts/stage_artifact_kernel_adoption.json#/state_index_kernel_adoption` 声明 MAS 是 OPL SQLite sidecar 小文件治理的首要 candidate，但 SQLite 只能承载 refs、locator、cursor、checksum、source fingerprint、receipt/blocker/restore refs 和 bounded preview hash。`domain_authority_refs.sqlite`、paper work-unit outbox 或任何 legacy runtime lifecycle SQLite 不能作为 stage completion、paper progress、publication quality、artifact authority 或 owner receipt authority；它们只能加速查找、去重、恢复和 operator read-model rebuild。

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

当 OPL / provider 在 study 的 `paper/review` 或等价 MAS owner-authorized review surface 写出 stage closeout，并且 closeout 证明 canonical story-surface delta 已 materialized，Progress-first controller 必须优先把它作为 consumed owner receipt 处理。即使 closeout 自身缺少 `truth_epoch`、`work_unit_id` 或 `work_unit_fingerprint`，只要能从 `stage_packet_ref` 恢复 current owner route，并且 action 是当前质量修复 work unit、owner result 已执行、story-surface hygiene clear，就应退役对应 writer handoff，把 projection 推进到下一 owner，例如 AI reviewer re-eval 或 gate replay。缺 story-surface delta、typed blocker、manuscript digest mismatch 或 stale closeout 仍按 nonconsumable redrive 处理。

同一条 consumed writer handoff 判断必须同时约束 materializer 和 dispatch selector。即使 persisted consumer dispatch 仍留在 `artifacts/supervision/consumer/default_executor_dispatches/` 或 consumer latest read-model 中，只要对应 `run_quality_repair_batch` 已被 owner-authorized closeout 消费，默认 dispatch 不得再选择、执行或用它覆盖当前 AI reviewer / gate / downstream owner action。若 materializer 已投影下一 owner，而 dispatch 仍选择旧 repair handoff，这是 dispatch arbitration currentness bug，应回 MAS controller/read-model 修复，不得手删 study-local dispatch 文件。

这条消费规则不只适用于 `quality_repair_batch_writer_handoff`。任何 default executor dispatch 只要带当前 owner route，且 `artifacts/supervision/consumer/default_executor_execution/latest.json` 或 execution ledger 已有同 action、同 owner-route currentness 的可消费 receipt，例如 `run_quality_repair_batch` 已产生 `progress_delta_candidate`、changed artifact refs、AI reviewer recheck request 或 gate replay refs，selector 就必须把该 dispatch 从 current selection 中移除。后续推进应来自 receipt 触发的下一 owner projection、AI reviewer / gate request、typed blocker 或 stop-loss，而不是重复执行同一个 repair action。

当 progress projection 已证明当前 study 存在 fresh meaningful paper/artifact delta，且同一 scan 仍有可执行 owner action 时，旧 `progress_first_owner_redrive_budget_exhausted` 只能作为 no-loop residue 标注为 stale superseded。Progress-first 优先推进当前 owner action、next-owner handoff 或 provider admission；只有缺 fresh delta、缺可执行 owner action、缺 typed blocker 或缺 hard-source 的重复 nonconsumable closeout 才保持 `terminal_stop_loss`。

当 OPL current-control 的 study-level `owner_route` 只是 truth snapshot / reconcile placeholder，且 `next_owner` 为空、`allowed_actions` 为空，或对当前 dispatch 不满足 owner-route match / route-allows-action 时，它只能作为 fail-closed 诊断背景，不能压住同一 study `action_queue` 中可 dispatch 的当前 owner route。dispatch selector 和 execution owner-route lookup 必须优先使用能匹配当前 dispatch、允许当前 action、带 required output surface 的 action-queue route；只有 action-queue route 缺席或不 dispatchable 时，才把 study-level route 返回给执行层生成明确 blocker。若 AI reviewer / gate / write owner action 已在 `action_queue` 中 ready，而默认 dispatch 因非 dispatchable study-level route 返回 `execution_count=0`，这是 read-model arbitration bug，不是论文目录需要手工迁移或论文 surface 可直接修改的许可。

当 `domain_transition` 已消费上一个 receipt 并明确 `controller_action` 指向下一 owner action，例如 `return_to_ai_reviewer_workflow`，但 OPL current-control 还没有把该 action 放入 `action_queue` 时，已 materialized 的 ready consumer dispatch 仍可作为当前 owner action authority。selector 必须用 consumed-transition route 的 action type、next owner、work unit id / fingerprint 校验 dispatch route；校验通过后按 dispatch 自带 owner route 执行，并在 execution payload 中标记 `owner_route_basis=consumed_transition_owner_action`。这条规则不适用于 publication gate replay 的 stale 防线；gate replay 仍要求严格 source-fingerprint / work-unit currentness，不能用宽松 bridge 执行旧 gate dispatch。

当 `return_to_ai_reviewer_workflow` 的第一次执行已经把 stale `publication_eval/latest.json` 路径转化为 `ai_reviewer_record_production_handoff`，并将 persisted dispatch 的 `required_output_surface` 改为 `artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json` 时，后续默认 dispatch selector 必须优先选择这个 persisted record-only handoff。workspace-level `artifacts/supervision/consumer/latest.json` 中仍残留的旧 inline dispatch 只是 stale read-model，不得覆盖 persisted handoff、不得再次生成同义 handoff，也不得把 handoff-ready 误记为论文内容进展。若 selector 仍显示 `dispatch_authority=consumer_default_executor_dispatch` 且 required output 回到 `artifacts/publication_eval/latest.json`，这是 dispatch arbitration currentness bug，应回 MAS controller 修复。

每个 Progress-first owner action 必须带可机器校验的 target surface。若 AI reviewer 或 domain transition 的推荐动作使用 publication decision 语义，例如 `route_back_same_line`，但实际 executor action 在 `controller_action_type=run_quality_repair_batch`，owner route 仍必须从 executor action policy 推导 `target_surface` / `target_surface_source`，并在 `next_forced_delta` 中显示 `target_surface_specificity=explicit_owner_route_target`。缺 explicit target surface 时 study-state-matrix 应 fail-close 为 `owner_route_target_surface_required`，不得把它当作 queued/running 或继续重复 receipt reconcile。

当 `domain-action-request-materialize` 把当前 AI reviewer record 或 gate result 桥接成新的 owner route，并在 dispatch 本体写入完整 `owner_route.currentness_contract`、`allowed_actions`、`required_output_surface` 和 bridge authority 时，dispatch 执行层可以把该 dispatch 自带 owner route 作为 current route 使用。条件是同一 dispatch 通过 owner-route match、route-allows-action 和 owner-route attempt protocol；通过后应标记 `owner_route_basis=dispatch_owner_route_bridge` 并立即执行 owner callable 或生成 typed blocker。不得因 OPL scan read-model 尚未同步同一个 bridge route 而返回 `current_owner_route_missing`，也不得回到下一轮 read-model reconcile。

## 分账规则

paper / deliverable progress 只承认五类 owner delta：

- MAS owner receipt。
- canonical paper / artifact delta。
- independent AI reviewer、auditor 或 publication-gate delta。
- stable typed blocker，且 blocker 明确 owner、work unit 和缺失 evidence。
- next owner handoff，且 handoff 带 current owner、work unit、required output surface、source refs 与 write boundary。

以下内容只能记为 platform repair / observability：telemetry、duration/token/cost 补齐、stage-log accounting、dispatcher hydration、receipt reconciliation、read-model currentness hygiene、OPL refs-only ledger record/verify、provider liveness/projection refresh、Portal wording/card 修复、bounded product-entry refresh。

同一轮同时出现 paper delta 和 platform repair 时，token / time 分账优先归 platform repair；paper / deliverable delta 只记录真实 owner delta 的 surface refs，不把平台修复耗时混报成论文推进。

Stage Operating Layer 分账进一步约束 stage MVP：`stage_kernel_projection` 是 Workbench primary progress 的当前 truth source；`stage_artifact_index` / Stage Deliverable Index 更新本身只算 derived locator/projection，除非它引用了新的 canonical paper / artifact delta、owner receipt、reviewer/gate delta、stable typed blocker、human gate、route-back 或 stop-loss。physical stage folder 只有通过 current pointer promotion、semantic receipt validation、consumability gate、lineage 和 retention / restore 检查后，才可被写成 current artifact progress；仅刷新 currentness、telemetry、read-model、receipt reconcile、provider liveness 或 evidence-tail 分类时，记为 platform repair / observability；不能写成 Stage Operating Layer landed，也不能显示成 primary progress。

## Co-Scientist 增益层分账

Progress-first 的 Co-Scientist 增益层只优化“下一步更快、更准、更少重复”，不创造独立 progress 类别。Operator 读取这层 signal 时按以下规则分账：

| signal | 可计入 | 不可计入 |
| --- | --- | --- |
| `next-delta tournament` | next owner selection evidence、route advisory、no-loop suppression hint。 | paper progress、route blocker、admission gate、publication readiness。 |
| `bounded micro-candidate generation` | 当前 work unit 的候选 repair / analysis / display / review target refs。 | 独立 stage completion、质量闭环、后台 paper-line progress。 |
| `critique-as-repair-hint` | reviewer gap list、repair target surface、route-back briefing。 | AI reviewer verdict、quality closure、publication gate closeout。 |
| `budgeted memory` | failed-path recall、negative result reuse、rejected candidate context、memory routing hint。 | memory accept/reject verdict、artifact authority、paper progress。 |
| `triggered meta-review` | route arbitration brief、stop-loss candidate、human-gate suggestion。 | 每轮必经 admission gate、route blocking layer、publication readiness。 |
| `opportunistic knowledge prefetch` | context hydration、literature/source/journal refs availability、reviewer briefing support。 | paper progress、quality score、readiness proof、hard blocker。 |

缺少、陈旧或失败的 prefetch / tournament / meta-review / memory recall 只算 observability 或 platform repair，不能压住已经可执行的 `current_executable_owner_action`。只有这些 signal 暴露了真实 hard gate，例如 missing source/data、forbidden write、human gate、missing owner callable 或 irreversible mutation，才按 Hard gates 归类；否则下一步仍应推进 owner action、reviewer request、memory writeback receipt、typed blocker、route-back 或 stop-loss。

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

Terminal `stage_artifact_index.next_owner_action=publication_handoff_owner_gate` 已具备完整 current owner action 时，Progress-first admission 的下一步是 OPL provider execution authorization / attempt lease / closeout receipt binding，随后才由 MAS owner callable 产出 `handoff_owner_receipt.json` 或 `receipts/typed_blocker.json`。缺少这组 OPL binding 时，operator outcome 应是 `blocked_with_typed_owner`，typed blocker owner=`one-person-lab`，reason=`opl_execution_authorization_required`；不得退回旧 writer repair、旧 gate replay、generic owner-route hydration 或 repeat receipt reconcile。

## Hard gates

preflight 只保留以下 hard gates：

- `human_gate`：需要用户、PI、医生、外部编辑或显式 approval/resume。
- `opl_execution_authorization_required`：当前 owner action 已可 dispatch，但缺 OPL provider attempt、attempt lease、execution authorization decision 或 closeout receipt binding；owner=`one-person-lab`，解除者是 OPL provider admission / lease / closeout binding。
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

## Durable closeout template

以下模板用于 docs/runbook/closeout lane 交接。它只记录 repo 文档改动、验证证据和后续 owner；不得手写 live study truth、runtime-owned state、canonical paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal/`、`manuscript/current_package/` 或 submission package。

```markdown
### Artifact-first MVP closeout

- Scope:
  - Updated docs:
  - Source-of-truth surfaces read:
  - Explicit non-write surfaces:
- Artifact-first rule landed:
  - Stage artifact refs / `stage_artifact_index` are the MVP progress core:
  - typed closeout / read-model / currentness / evidence-tail / provider liveness are enhancement, audit, or scheduling layers:
  - OPL App workbench displays refs-only and does not write MAS truth:
- Landed commits:
  - <main session fill>
- Verification evidence:
  - documentation review:
  - git diff/status:
  - optional docs/link check:
- Residual risk / next owner:
  - <main session fill>
```

### Artifact-first MVP closeout - 2026-06-03 repo integration

- Scope:
  - Updated docs: `docs/active/stage_surface_standardization_program.md`, `docs/runtime/control/progress_first_stage_outcome.md`, `docs/active/opl_app_mas_runtime_workbench_program.md`.
  - Source-of-truth surfaces read: `agent/stages/stage_route_contract.yaml`, `contracts/stage_control_plane.json`, progress-first controller/projection tests.
  - Explicit non-write surfaces: no live study truth, runtime-owned state, canonical paper body, `publication_eval/latest.json`, `controller_decisions/latest.json`, `paper/submission_minimal/`, `manuscript/current_package/`, or submission package was edited.
- Artifact-first rule landed:
  - Stage artifact refs / `stage_artifact_index` are the MVP progress core and are projected into study progress, Progress Portal, and OPL domain-pack workbench descriptors.
  - typed closeout / read-model / currentness / evidence-tail / provider liveness are enhancement, audit, or scheduling layers.
  - OPL App / workbench surfaces display refs-only stage artifacts and cannot write MAS truth, publication readiness, quality verdict, paper body, or package outputs.
  - 2026-06-03 stage-native contract follow-through: `stage_artifact_index` now projects stage folder contract, manifest requirements, receipt requirements, and fail-closed artifact classification. 2026-06-03 physical kernel follow-through: MAS now declares and consumes the OPL physical Stage Folder Kernel locator from `contracts/mas-paper-study-stage-pack.json`, reading `current.json`, stage `latest`, attempt `manifest.json`, receipt file, manifest hash refs, lineage refs, and conformance refs from `OPL_STATE_DIR/runtime-state/domains/med-autoscience/deliverables/mas-paper-study/<study_id>/paper-study`. Legacy declared refs can still seed migration / historical projection, but missing OPL physical manifest, receipt, hash, or pointer keeps the artifact out of current progress.
- Landed commits:
  - `1878effb` Add artifact-first stage index kernel.
  - `43e80918` Prioritize artifact-first owner actions in progress monitoring.
  - `792b2230` Project artifact-first stage index to workbench surfaces.
  - `49d43aa3` Document artifact-first MVP runtime rules.
  - Integration cleanup commit keeps line-budget gates green by moving runtime storage maintenance tests to a cases module and extracting artifact-first monitoring helpers.
- Verification evidence:
  - `rtk scripts/run-pytest-clean.sh tests/test_stage_artifact_index.py -q` -> 4 passed.
  - `rtk scripts/run-pytest-clean.sh tests/study_progress_cases/current_executable_owner_action.py -q` -> 18 passed.
  - `rtk scripts/run-pytest-clean.sh tests/study_progress_cases/stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_review_opl_projection_reference.py -q` -> 5 passed.
  - `rtk scripts/run-pytest-clean.sh tests/test_product_entry.py -q -k stage_control_plane_descriptor` -> 1 passed, 105 deselected.
  - `rtk scripts/run-pytest-clean.sh tests/test_runtime_storage_maintenance.py -q` -> 31 passed.
  - `rtk make test-meta` -> 282 passed, 4193 deselected.
  - `rtk scripts/verify.sh` -> repo hygiene audit passed; smoke entrypoints / line budget 4 passed.
- Residual risk / next owner:
  - This closeout does not declare any study publication ready, submission ready, or final paper quality ready.
  - DM002/DM003 live-study smoke remains read-only follow-through evidence, not a prerequisite for the repo-level artifact-first MVP integration.

### Stage-Native Artifact Operating Layer closeout - 2026-06-04 repo integration

- Scope:
  - Updated docs: `docs/active/mas-ideal-state-gap-plan.md`, `docs/active/stage_surface_standardization_program.md`, `docs/runtime/control/progress_first_stage_outcome.md`.
  - Updated contract: `contracts/stage_artifact_kernel_adoption.json`.
  - Updated source/projection: state index kernel, semantic receipt validator, promotion audit helper, lineage / retention drilldown, study progress `stage_kernel_projection`, Progress Portal / Workbench `stage_operating_layer`.
  - Explicit non-write surfaces: no live study truth, runtime-owned state, canonical paper body, `publication_eval/latest.json`, `controller_decisions/latest.json`, `paper/submission_minimal/`, `manuscript/current_package/`, memory body, artifact body, submission package, or OPL `current.json` was edited.
- Operating-layer rule landed:
  - `stage_artifact_index` remains a rebuildable derived locator projection.
  - `stage_kernel_projection` is the primary Workbench progress source and now exposes `state_index`, `promotion`, and `lineage_retention` drilldowns.
  - Semantic receipt validation is body-free and fail-closed; typed blocker is a domain outcome, not runtime failure.
  - Promotion audit is read-only and cannot promote or rewrite current pointer.
  - Lineage / retention drilldown never authorizes cleanup; cleanup / restore still needs owner-authorized receipt.
  - Workbench cross-domain soak is display-only and cannot authorize MAS/MAG/OMA/RCA readiness or artifact mutation.
- Verification evidence:
  - `rtk scripts/run-pytest-clean.sh tests/test_opl_state_index_kernel.py tests/test_opl_stage_promotion_runtime.py tests/test_mas_stage_semantic_receipts.py tests/test_opl_stage_lineage_retention.py tests/study_progress_cases/stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_artifact_index_projection.py tests/progress_portal_cases/test_stage_kernel_cross_domain_soak_projection.py tests/test_stage_artifact_kernel_adoption_contract.py -q` -> 25 passed.
  - Full verification and final commit id are recorded by the main session after absorb / cleanup.
- Residual risk / next owner:
  - This closeout does not declare any study publication ready, submission ready, final paper quality ready, memory writeback success, artifact mutation authorization, or live provider long-soak completion.
  - Remaining evidence tail is real paper-line owner delta, independent reviewer/auditor scaleout, live cross-domain soak, human gate / resume and owner-authorized artifact lifecycle apply.

## 错误路径

不要再走以下路径：

- 把 `active_run_id` 当作 running proof。running proof 只来自 OPL current-control / runtime liveness 的 `running_provider_attempt=true` 和 active attempt/run/workflow ref。
- 把 `next_system_action` 文案当作 admission authority。authority 必须来自 `current_executable_owner_action` 与 owner-route attempt envelope。
- 把 `receipt_consumed` 显示成 `ready_owner_action` 或等待 owner pickup。它应触发下一 owner projection 或暴露 currentness 缺口。
- 在 provider-hosted `paper/review` closeout 已证明 story-surface delta materialized 后，继续导出同一个 `run_quality_repair_batch` writer handoff。应消费 receipt、退役 handoff，并投影下一 owner。
- 在 materializer 已消费旧 writer handoff 后，dispatch selector 仍从 persisted/consumer dispatch fallback 执行同一个 `run_quality_repair_batch`。应过滤已消费 handoff，并执行当前 owner action。
- 在 default executor execution receipt 已证明同一 owner route 的 `run_quality_repair_batch` 产生 paper/artifact delta 后，dispatch selector 仍把同一个普通 consumer dispatch 当作 ready action。应消费 execution receipt 并等待/投影下一 owner，不能重复 repair。
- 在 progress projection 已证明 fresh meaningful paper/artifact delta 且当前 owner action 仍可执行时，继续把旧 `progress_first_owner_redrive_budget_exhausted` 当作当前 typed blocker。应标注 stale superseded 并推进 owner action / handoff / provider admission。
- 当 study-level `owner_route` 是非 dispatchable placeholder，而 `action_queue` 已有当前 owner action route 时，仍让默认 dispatch 返回空 execution。应让 action-queue route 成为当前 dispatch authority，不能继续重复 read-model reconcile。
- 当 consumed `domain_transition.controller_action` 已指向下一 owner action，且 consumer dispatch 已 ready，但 `action_queue` 暂空时，仍因 consumed transition 非空而清空 fallback dispatch。应按 consumed-transition owner action bridge 执行当前 dispatch，不能让论文推进等待下一轮同义 reconcile。
- 在 `ai_reviewer_record_production_handoff` persisted dispatch 已存在后，继续让 stale `consumer/latest.json` inline dispatch 覆盖它，导致重复写 handoff 而不是把 AI reviewer record-production owner action 交给下一 owner。应优先 persisted record-only handoff，并把旧 inline 当作 read-model lag。
- 把 provider handoff 写出当作 provider attempt 已启动。缺 running proof 时只能写 `provider_handoff_written_admission_pending`。
- 把 telemetry、duration/token/cost、Portal card wording、read-model hygiene、refs-only ledger record/verify 当成 paper progress。
- 把 `next-delta tournament`、`bounded micro-candidate generation`、`critique-as-repair-hint`、`budgeted memory`、`triggered meta-review` 或 `opportunistic knowledge prefetch` 当成 admission gate、route blocking layer、quality closure、publication readiness、artifact authority 或 paper progress。它们只能辅助 route selection、reviewer gap finding 和 failed-path memory reuse。
- 用显式 `--action-types` 作为正常 Progress-first 必需步骤；它只用于诊断、限流或人工指定，默认 dispatch 必须消费 current ready dispatch。
- 用 broad recursive scan、mtime、旧 request lifecycle、旧 generated_at、stale consumer dispatch 或旧 package freshness proof 覆盖当前 owner/work-unit currentness。
- 手工写 DM-CVD study truth、runtime-owned state、canonical paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、`paper/submission_minimal/`、`manuscript/current_package/` 或 submission package 来关闭 currentness 问题。
- 把 repo-side docs/code fix landed 推断成 live study 已恢复。每次状态判断都必须重新读取 live study/runtime surfaces。
