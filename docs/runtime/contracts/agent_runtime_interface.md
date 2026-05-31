# Agent Runtime Interface

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime contract and stage-surface boundaries for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable runtime contract support only; enforceable runtime truth remains in machine-readable contracts, source, tests, CLI/read-model output, runtime ledgers, and owner receipts.

这份文档写给 `Codex` 等 Agent、内部技术合作者，以及需要审阅 Agent 行为的人。

它属于仓库跟踪的运行面文档层，因此收口在 `docs/runtime/`，但不属于默认公开入口。
与之相对，`docs/history/superpowers/` 只保留历史内部设计稿、plan、spec 和 agent 工作过程产物，不作为公开主入口。
如果未来要把这份文档提升为公开入口，先更新 `docs/public/` / `docs/product/` 的 owner 文档与核心五件套；不恢复 docs 层双语镜像。

`MedAutoScience` 对外可以继续称为医学自动科研平台，但更准确的理解是：它是独立 medical research domain agent，对内由一个 `Agent-first, human-auditable` 的医学自动科研 harness 驱动：

- 人类负责提出研究任务、提供数据、审阅结果和做关键决策
- Agent 负责调用稳定接口，推进数据治理、研究执行和论文交付组织
- 平台负责提供可验证、可审计、可重复调用的 domain entry 与 owner surface，而不是要求医学用户手工维护底层状态

当前 repo-tracked 运行拓扑固定为：

- `MedAutoScience` = 唯一研究 domain entry 与 research owner surface
- `OPL scheduler replacement` = outer supervision scheduler owner；默认 adapter 是 `opl_family_runtime_provider`
  - `MAS supervision scheduler contract` = paper-progress SLO/read-model、domain tick payload、owner receipt、typed blocker、safe action refs 和 legacy tombstone/provenance projection owner；MAS-owned `local` scheduler / LaunchAgent install path 已物理退役，公开 CLI 不再暴露 `--manager local`；`Hermes gateway cron` 是 explicit legacy diagnostic adapter
- `OPL provider-backed stage runtime` = 默认 generic runtime owner / substrate，负责 durable attempt、queue、wakeup、retry/dead-letter、worker residency、generic transition runner 和 provider transport
- MAS domain authority refs = DomainIntent / owner route、owner receipt、typed blocker、artifact/source/quality refs、paper-progress SLO 解释和 standalone diagnostic explanation；不保留 MAS-owned runtime lifecycle、worker lease、attempt ledger 或 recovery-intent 控制面
- `MedDeepScientist` = frozen source archive、historical fixture、explicit archive import / backend-audit / provenance reference
- 旧 `Codex-default host-agent runtime` = 只保留为迁移期对照面与 regression oracle，不再是长期产品方向
- display / paper-facing asset packaging 独立线 = 明确排除在本 runtime / gateway / architecture tranche 之外

Current reading note：本文件里的 `Hermes` 指显式 `--manager hermes` 的 `Hermes gateway cron` diagnostic adapter、显式 `hermes_agent` executor/proof lane 或历史 provenance；它不是 MAS study truth owner、runtime truth owner、session owner、provider truth 或默认 executor owner。study truth 继续由 `MedAutoScience` 的 study-owned surfaces、controller decisions 与 publication gate 持有。

当前 formal-entry matrix 继续固定为：

- `default_formal_entry`：`CLI`
- `supported_protocol_layer`：`MCP`
- `internal_controller_surface`：`controller`

其中：

- `CLI-first` 指的是 Agent runtime 的默认正式入口
- `MCP` 是兼容的协议层，不改写 `CLI-first` 的默认入口语义
- `controller` 属于内部控制面，不与 `CLI`、`MCP` 并列作为对外 formal entry
- 当前 repo-tracked 产品主线按 `Auto-only` 理解；未来若做 `Human-in-the-loop` 产品，应作为兼容 sibling 或 upper-layer product 复用同一 substrate

## 执行真相（product-entry contract 对齐）

以下口径以 `src/med_autoscience/controllers/product_entry.py::build_product_entry_manifest` 及 `tests/test_product_entry.py` 的断言为准：

- `MedAutoScience` 自己不直接打模型。
- 当前默认 generic runtime owner 固定为 OPL provider-backed stage runtime；MAS 只输出 DomainIntent、owner receipt、typed blocker 和 domain authority refs，外部 `med-deepscientist` repo、daemon、runtime root 或 WebUI 不参与默认 operation。
- family 默认执行器正式名称：`Codex CLI`。
- family 默认执行模式：`autonomous`。
- 默认 model / reasoning：继承本机 Codex 默认（`inherit_local_codex_default`）。
- `chat-only executor` 明确 forbidden（`chat_completion_only_executor_forbidden = true`）。
- `Hermes-Agent` 备选执行路线只有在显式 hosted/runtime target 接入时才可用，且必须满足 full agent loop guardrail（`hermes_agent_requires_full_agent_loop = true`）。
- 当前 manifest 的默认执行路径不得把 `MedDeepScientist` 重新暴露为 public executor backend；显式 MDS 相关入口只能是 source provenance、historical fixture、explicit archive import 或 backend-audit reference。

## 当前主线与 monorepo 长线的关系

当前这条 repo-tracked 主线，优先级应按下面顺序理解：

- 保持 OPL provider-backed stage runtime 为默认 generic runtime owner
- 保持 MAS 只作为 domain authority refs、owner receipt、typed blocker、artifact/source/quality refs 与 diagnostic explanation owner
- 保持 execution handle、durable surface 与 fail-closed gate semantics 不漂移
- 继续把 `runtime backend interface` 收紧到 controller / outer-loop / transport / durable surface 全链只认 backend contract
- 把 `MedDeepScientist` 明确收口为 frozen archive、historical fixture、source provenance 和 explicit archive import reference，而不是 hidden authority truth
- 不用“functional monolith landed”覆盖真实行为差异；MDS resident daemon、WebSocket terminal streaming、connector background threads 等差异必须通过 behavior equivalence matrix 公开

monolith 的 honest 读法是：默认 operation、默认诊断、进度可视化和 artifact/quality/status/progress/cockpit 入口已经不依赖外部 MDS repo；这不等于 MDS daemon/WebUI/connector 行为被函数级或 resident-process 级 1:1 复刻。

当前 `stabilize_user_product_loop` 这一步里，已经落地一条 controller-owned same-line continuation step：

- 起点是 `publication_eval/latest.json` 给出的 blocked `bounded_analysis` route truth，再叠加 `publication_gate` 已能识别的 repairable blockers。
- 当 scientific-anchor 冻结、paper live path repair、display/export refresh、submission-minimal replay 或 stale delivery replay 属于当前可确定修复项时，`study_outer_loop` 会把泛化 route-back 收口成 `run_gate_clearing_batch`。
- 这一步先批量执行当前 study line 上的确定性修复，再重放 `publication_gate`；它服务的是当前质量/自治/single-project 主线里的 continuation，不是新的 owner-facing lane。
- 因此它属于现有 `quality route truth -> controller decision -> gate replay -> same-line continuation` 链路：质量面负责回答为什么先修这一批，runtime/controller 面负责执行并留下 durable record，read-model 继续消费既有 controller dispatch 信号。

## Execution Handle 与 Durable Surface

当前主线下，Agent 不应把所有运行身份混写成一个“run id”。

必须至少区分：

- `program_id`
  - 当前 `research-foundry-medical-mainline` 的 control-plane / report-routing 指针
  - 以 `README*`、`docs/status.md` 与当前 blocker / activation package 共同锚定
- `study_id`
  - study 聚合根身份
  - 对应 `studies/<study_id>/`
- `quest_id`
  - OPL/MAS handoff 下的研究运行身份；runtime attempt lifecycle 归 OPL，MAS 只持 domain authority refs
  - 新 workspace 对应 `runtime/quests/<quest_id>/` 普通目录；旧 `ops/med-deepscientist/runtime/quests/<quest_id>/` 只作为 historical fixture / archive import reference
- `active_run_id`
  - 当前 live execution 的细粒度执行句柄
  - 只在 live execution / runtime audit 场景里出现

当前 canonical durable surface 至少包括：

- `runtime_binding.yaml`
- `progress_projection`
- `domain_health_diagnostic`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
- `studies/<study_id>/artifacts/controller/gate_clearing_batch/latest.json`
- `studies/<study_id>/artifacts/runtime/last_launch_report.json`
- `studies/<study_id>/artifacts/runtime/health/latest.json`
- `artifacts/runtime/domain_authority_refs.sqlite`
- `artifacts/runtime/lifecycle_migration/*`
- `runtime/quests/<quest_id>/` materialization manifest
- `runtime/restore_index/*`

这意味着：

- `runtime_binding.yaml` 必须同时写出 `runtime_substrate`、`opl_runtime_ref`、`runtime_ref`、`runtime_engine_id`、`research_backend_id`、`research_engine_id`
- `publication_eval` 必须继续落在 study-owned latest surface，而不是回写到 runtime 临时目录
- `runtime_escalation_record` 与 `domain_health_diagnostic` 继续是 quest-owned runtime artifact / diagnostic projection；旧 `ops/med-deepscientist/...` 只作为 historical fixture / explicit archive import reference
- `controller_decisions/latest.json` 是 study-owned outer-loop / controller decision surface
- `artifacts/controller/gate_clearing_batch/latest.json` 是 study-owned same-line continuation execution record：它只记录一次 controller-owned batch repair 与 gate replay，不替代 `controller_decisions/latest.json` 作为 authority decision surface
- `artifacts/runtime/health/latest.json` 是 study-owned domain health / diagnostic snapshot：它只解释 blocker、owner refs 和 escalation context；worker liveness、retry budget 与 attempt lifecycle 归 OPL current control state，不替代 `StudyTruthKernel.canonical_next_action`
- 本地未跟踪 handoff scratch 不替代 repo-tracked runtime truth
- Git history、Git diff/log、workspace root Git、quest `.git`、worktree list、retired runtime lifecycle SQLite 或 recovery-intent snapshots 不作为默认 runtime status surface；Agent 查状态和做 lifecycle 操作时优先读 OPL current control state、MAS file authority、macro state / owner route、domain authority refs index、migration ledger、quest manifest 和 restore index

如果你是医学用户，希望先理解这个项目是什么、适合什么课题、能产出什么，请先看仓库首页 [README.md](../../../README.md)。

## 技术入口路径

根据任务类型，从这里继续进入：

- 工作区接入与部署：[`bootstrap/README.md`](../../../bootstrap/README.md)
- workspace 标准架构与 legacy 迁移：[`workspace_architecture.md`](../../references/workspace/workspace_architecture.md)
- `main` 合并门与现网切换门：[`merge_and_cutover_gates.md`](../../policies/repo-ops/merge_and_cutover_gates.md)
- `Hermes` repo-side continuation：[`../../history/program/hermes_backend_continuation_board.md`](../../history/program/hermes_backend_continuation_board.md)
- `Hermes` repo-side activation package：[`../../history/program/hermes_backend_activation_package.md`](../../history/program/hermes_backend_activation_package.md)
- external `Hermes-Agent` runtime proof / readiness：只在显式 hosted target 接入时先跑 `doctor`，再跑 `hermes-runtime-check`
- `MedDeepScientist` 解构地图：[`../../references/med-deepscientist/med_deepscientist_deconstruction_map.md`](../../references/med-deepscientist/med_deepscientist_deconstruction_map.md)
- external runtime blocker package：[`../../policies/runtime-governance/external_runtime_dependency_gate.md`](../../policies/runtime-governance/external_runtime_dependency_gate.md)
- external gate 未清除前的手工测试与 repo-side 稳定化清单：[`manual_runtime_stabilization_checklist.md`](../../policies/runtime-governance/manual_runtime_stabilization_checklist.md)
- `Phase 6` 当前 repo-tracked activation baseline：[`integration_harness_activation_package.md`](../../history/program/integration_harness_activation_package.md)
- `MedAutoScience` / `MedDeepScientist` 边界：[`runtime_boundary.md`](./runtime_boundary.md)
- 运行句柄与持久表面合同：[`runtime_handle_and_durable_surface_contract.md`](./runtime_handle_and_durable_surface_contract.md)
- managed study runtime 状态机与执行 contract：[`study_runtime_orchestration.md`](../control/study_runtime_orchestration.md)
- 上游 intake 与 fork 升级流程：[`upstream_intake.md`](../../references/med-deepscientist/upstream_intake.md)
- 控制器与内部能力：[`controllers.md`](../control/controllers.md)
- 数据资产策略：[`policies/study-workflow/data_asset_management.md`](../../policies/study-workflow/data_asset_management.md)
- 默认研究场景：[`policies/study-workflow/study_archetypes.md`](../../policies/study-workflow/study_archetypes.md)
- 研究路线偏置：[`policies/study-workflow/research_route_bias_policy.md`](../../policies/study-workflow/research_route_bias_policy.md)
- domain-handler provider 与 figure routes 指南：[`domain_handler_figure_routes.md`](../../delivery/medical-display/contracts/domain_handler_figure_routes.md)
- MAS stage route contract：[`stage_route_contract.md`](./stage_route_contract.md)

## 第三方 Agent 入口资产

当前对外按兼容消费来表达的 Agent 包括：`Codex`、`Claude Code`、`OpenClaw`。

如果你需要把 `MedAutoScience` 的入口契约直接交给受控 Agent 或内部技术协作者，而不是只让它阅读 README，可优先使用这些仓库跟踪资产：

- stage route contract：[`stage_route_contract.md`](./stage_route_contract.md)
- 机器可读镜像：[`../../../templates/stage_route_contract.yaml`](../../../templates/stage_route_contract.yaml)
- `Codex` 入口模板：[`../../../templates/codex/medautoscience-entry.SKILL.md`](../../../templates/codex/medautoscience-entry.SKILL.md)
- `OpenClaw` 入口模板：[`../../../templates/openclaw/medautoscience-entry.prompt.md`](../../../templates/openclaw/medautoscience-entry.prompt.md)

`Claude Code` 不单独维护专有入口模板，默认复用 `Codex` 这一套入口契约。

这些资产只负责声明：

- 哪些模式默认走 `managed`
- 哪些模式默认走 `lightweight`
- 何时需要从轻量专项模式升级为正式纳管模式
- 每个模式可调用的 entry actions、研究 routes、governance routes 和 auxiliary routes

“先定目标期刊，再反推选题和数据要求”的前置规划任务，不单独拆成第六类正式入口。
这类任务默认仍属于轻量专项模式，通常组合使用 `literature_scout`、`idea_exploration`、`decision`，并在需要把目标期刊要求解析为正式约束时调用 `journal-resolution`；其交付应停在数据建议要求清单，而不是从这个场景直接升级到正式 managed 研究。

如果你只是做一次性的文献调研、思路启发、补实验判断或稿件整理，Agent 可以直接按轻量专项模式调用相应 route。
如果任务已经进入需要正式纳管的自动科研推进，则应按契约先走 `doctor -> workspace bootstrap -> runtime overlay-status`，再由 MAS 输出 DomainIntent / owner route refs，并交给 OPL hydrate stage attempt。

## 唯一研究入口

在当前架构里，`MedAutoScience` 是唯一研究入口和独立 medical research domain agent，默认 outer supervision scheduler owner 是 OPL `opl_provider_runtime_manager`，默认 adapter 是 `opl_family_runtime_provider`；MAS 保留 paper-progress SLO/read-model、domain tick payload refs、owner receipt、typed blocker、safe action refs 和 legacy diagnostic projection；默认 generic runtime owner 是 OPL provider-backed stage runtime，MAS 只承担 domain authority refs、owner receipt、typed blocker、artifact/source/quality refs 与 diagnostic explanation；`MedDeepScientist`（仓库名 `med-deepscientist`）只在 frozen source archive、historical fixture、显式 archive import / provenance reference 和上游 intake 里出现。`DeepScientist` 只在上游比较、兼容审计和历史命名里单独出现。

这里的默认 owner 口径只冻结 repo-side substrate contract 与可选 hosted target 方向，不授权 Agent 把 external `Hermes` repo / daemon / workspace surface 当作研究入口或 study truth。

因此：

- Agent 不应直接调用 external `Hermes` daemon / repo / workspace surface 发起研究流程，除非当前 profile 显式进入 hosted target 诊断
- Agent 不应直接调用 `MedDeepScientist` daemon HTTP API 发起 quest
- Agent 不应把 `MedDeepScientist` UI / CLI 当成研究入口
- `ops/med-deepscientist/bin/*` 只可作为 historical fixture / explicit archive import reference，不用于研究治理
- 所有正式研究推进都应经由 `doctor`、`workspace bootstrap`、`runtime overlay-status`、`launch-study` / `domain-health-diagnostic` 产生 MAS refs，并由 OPL `current_control_state` hydrate stage attempt；MAS 不再提供 `study ensure-runtime` 入口

## 当前用户可见的启动与进度入口

对当前 agent-operated 形态，用户真正会碰到的启动与监督入口已经先收成一层轻量 product-entry shell，再往下落到低层 controller 面：

- repo 主线阶段/缺口入口：`mainline-status`
- repo 阶段详情入口：`mainline-phase --phase <current|next|phase_id>`
- workspace cockpit：`workspace-cockpit --profile <profile>`
- 写入 durable study task intake：`submit-study-task --profile <profile> --study-id <study_id> --task-intent "<intent>"`
- 正式启动或续跑：`launch-study --profile <profile> --study-id <study_id>`
- 人话进度投影：`study progress --profile <profile> --study-id <study_id>`
- OPL stage/runtime owner：OPL `current_control_state` / provider attempt ledger 持有 scheduler lifecycle、provider liveness、attempt、retry/dead-letter 与 operator runtime projection；MAS 不再提供 `runtime-supervision-*` compatibility CLI
- MAS refs 刷新入口：`runtime domain-health-diagnostic --runtime-root <runtime_root> --profile <profile> --request-opl-stage-attempts --request-opl-owner-route-reconcile --apply` 只写 refs-only handoff、owner receipt 或 typed blocker，不启动 MAS 私有 runtime
- entry_status / manifest companion：`product-entry-status --profile <profile>`、`product-entry-manifest --profile <profile>`，它们是单一 MAS app skill 下的内部 command contract，并在 integration layer 暴露机器可读 companion；当前会显式导出 `product_entry_guardrails`、`phase3_clearance_lane`、`phase4_backend_deconstruction` 与 `phase5_platform_target`

低层当前入口仍然保留：

- `study progress-projection`
- `runtime domain-health-diagnostic`

Workspace-local Progress-first 监控薄入口固定为：

- `ops/medautoscience/bin/progress-projection <study_id> --format json`
- `ops/medautoscience/bin/study-state-matrix --format json`

`progress-projection <study_id> --json` 只作为旧 JSON alias 兼容；新文档、脚本和自动化应使用 `--format json`。

如果 workspace 来自较早的骨架版本，应先重跑一次 `init-workspace`。当前 controller 会在不加 `--force` 的前提下，自动升级 `_shared.sh` 和当前 domain refs helper，并删除已退役的 `watch-runtime`、`study-runtime-status` 与 workspace-local service wrapper；scheduler 安装、状态和移除不再由 MAS CLI 提供，统一读取 OPL `current_control_state` / provider attempt ledger。新 workspace 默认 no root Git / no quest Git；current workspaces 的 root Git 已完成 restore-proof full retirement。未来接入外部或旧 workspace 时若发现 root `.git`，只走显式 inventory / archive / remove / verify diagnostic，不属于普通 bootstrap 成功条件，也不得重新成为 Agent 状态面。
对于 legacy workspace，`init-workspace` 现在还会优先跟随 `ops/medautoscience/config.env` 中真实生效的 `MED_AUTOSCIENCE_PROFILE`；如果需要把 active profile 原位补齐到 Hermes-era contract，可显式传入 `--hermes-agent-repo-root` 与 `--hermes-home-root`，避免只在旁边生成一个不被当前 workspace 实际消费的 `.local.toml`。
同一条升级路径会把旧 workspace-local host-service 漂移识别为 retired tombstone/provenance evidence。旧 launchd/systemd/cron/docker service 不再作为 active runtime option 保留；`local`、`opl` 和 `hermes` scheduler manager 都不作为 MAS active CLI manager 暴露；显式 Hermes 只作为旧 proof/provenance refs，不刷新 cron job 或 tick script。

前台 contract 要求：

- `mainline-status` 应直接回答 repo 的理想形态、当前主线阶段、5 阶段完善梯子、已完成 tranche、剩余缺口与 next focus，避免用户自己拼多份 program 文档
- `mainline-status` 还应带出 `phase3_clearance_lane` 与 `phase4_backend_deconstruction`，把 host/workspace clearance 与 backend deconstruction 的当前可执行面显式结构化
- `mainline-status` 还应带出 `phase5_platform_target`，把 monorepo / runtime core ingest / hosted frontend 收成结构化 post-gate target，并显式暴露 `sequence_scope / current_step_id / completed_step_ids / remaining_step_ids / landing_sequence`
- `mainline-phase` 应直接回答某一阶段当前如何使用：至少包括当前可用入口、退出条件与关键文档；如果当前阶段仍在 single-project boundary tranche，还要直接投影“当前 tranche 收什么、MDS 保留什么、哪些是 post-gate only”，避免“五阶段”只停留在静态规划说明里
- 只要 `autonomous_runtime_notice.required = true`，就必须把 `browser_url`、`quest_session_api_url`、`active_run_id` 当成当前用户可见的监督入口
- 只要 `execution_owner_guard.supervisor_only = true`，前台就必须切到 supervisor-only，不再继续直接写 runtime-owned surface
- `workspace-cockpit` 应直接投影 repo 主线快照、workspace 级 readiness、latest task intake、OPL scheduler replacement status、MAS supervision SLO/read-model refs、stale / missing progress signal 聚合，以及按优先级排好的 workspace attention refs
- `workspace-cockpit` 还应直接给出当前真实 user loop：至少包括 mainline-status、submit-study-task、launch-study、study-progress、watch 这组命令模板，避免用户再自己拼“怎么启动 / 怎么下任务 / 怎么持续看进度”
- `product-entry-status` / `product-entry-manifest` 应显式带出 `product_entry_guardrails`：至少覆盖 `workspace supervision gap`、`study progress gap`、`human decision gate`、`publication / quality blocker` 四类 guardrail，并把 `inspect_workspace_inbox -> refresh_supervision -> inspect_study_progress -> continue_or_relaunch` 收成标准恢复回路
- `product-entry-status` / `product-entry-manifest` 还应显式带出 `single_project_boundary`：至少回答 `MAS owner modules`、`MDS retained roles`、`post_gate_only` 与 `not_now`，避免调用方只读前台时丢失单项目 owner boundary
- `product-entry-status` / `workspace-cockpit` 还应显式带出 `autonomy_soak_status`、`same_line_route_truth` 与 `quality_review_followthrough` 的人话投影；当同一论文线已经收窄到写作、有限补充分析或 finalize 收口时，前台要直接回答“当前仍在同一条线做什么”“当前关键问题是什么”“下一次确认看什么”
- `product-entry-status` / `product-entry-manifest` 还应显式带出 `phase3_clearance_lane`：至少覆盖 `external_runtime_contract`、`supervisor_service`、`study_recovery_proof` 三类 clearance target，并把 doctor / hermes-runtime-check / watch / launch-study / study-progress 的组合回路收成标准模板
- `product-entry-status` / `product-entry-manifest` 也应显式带出 `phase4_backend_deconstruction`：至少回答 substrate target、backend retained now、current backend chain、optional executor proof lane 与 promotion rule，避免在 Phase 4/5 讨论里重新把 truth 写散
- `product-entry-status` / `product-entry-manifest` 也应显式带出 `phase5_platform_target` 的 monorepo readiness sequence，让用户和顶层 caller 都能直接看到“当前做到哪一步、还差哪几步”，而不是把 monorepo 只当成口头终局
- `launch-study` 应在返回监督入口的同时，把当前 latest task intake 与 progress freshness 一并投影给用户
- `progress-projection` 负责结构化真相；`study-progress` 负责用户可直接读的阶段摘要、当前任务摘要、progress freshness、当前阻塞和下一步，并继续把 `domain_health_diagnostic` 已发现的 figure-loop / 质量守卫 blocker 投影到用户面
- `study-progress` 现在还应显式导出 `intervention_lane`：至少要把 `workspace_supervision_gap`、`runtime_recovery_required`、`human_decision_gate`、`study_progress_gap`、`quality_floor_blocker` 这几类前台干预语义稳定结构化，避免 `workspace-cockpit` 继续靠松散启发式猜当前问题属于哪一类
- `study-progress` 还必须把这类前台干预语义继续收口成 `recommended_command`、`recommended_commands` 与 `recovery_contract`：
  - `recommended_command` = 当前最该执行的一条命令
  - `recommended_commands` = 当前恢复/监管合同里的有序命令列表
  - `recovery_contract` = `lane_id / action_mode / recommended_step_id / steps` 这组结构化恢复合同
- `workspace-cockpit` / `launch-study` / `product-entry-status` 对齐消费 `study-progress.recovery_contract` 与 `recommended_command`，而不是各自再猜一遍当前应该 refresh supervision、launch study 还是仅保持人工判断
- `workspace-cockpit` / `product-entry-status` 对齐消费 `study-progress.intervention_lane`：恢复异常应比普通 blocker 更靠前，质量硬阻塞不能继续被压平到泛化的 `study_blocked`
- `build-product-entry` 的 `return_surface_contract` 还应显式带出 `single_project_boundary` 与 `study_progress_projection_contract`，至少告诉外部 caller：当前 owner boundary 是什么，以及 `study-progress` 里哪几个字段分别对应 `autonomy_soak_status`、`quality_execution_lane`、`same_line_route_truth`、`quality_review_followthrough`
- 默认 OPL scheduler replacement、显式 legacy `local` diagnostic adapter、显式 `hermes` diagnostic adapter，或显式 `owner-route-reconcile --apply-safe-actions --developer-supervisor-mode developer_apply_safe` 负责刷新 MAS owner-route/domain-authority handoff refs；没有新鲜 OPL tick / current-control-state evidence，`study-progress` 必须诚实降回 `managed_opl_runtime_owner_handoff_gap`
- 如果 `study.yaml` 显式声明 `manual_finish` 且 `manual_finish_guard_only = true`，`study-progress` 应把该 study 投影成 `manual_finishing`，表达“当前以人工收尾 + 显式 guard 为主”，而不是继续误报成默认应自动续跑的活跃 runtime blocker；旧 `compatibility_guard_only` 字段已经退役，active runtime 入口必须 fail-closed

历史上真实 workspace 曾使用 workspace-local launchd service 验证监管刷新；该路径现在只作为历史/debug 事实保留。当前 active contract 以 OPL scheduler replacement + MAS supervision SLO/read-model contract 为准，local one-shot tick 只作为显式 legacy diagnostic / cleanup adapter；旧 launchd/systemd/cron/docker service 出现时应被清理，不再作为“产品态常驻路径”或替代 scheduler 推荐给 Agent。

## 运行层分工

在这个运行层里，不建议把人类和 Agent 的职责混在一起：

- 人类定义研究目标、确认课题边界、提供或授权数据、审阅研究输出、决定是否继续推进
- Agent 负责调用 CLI 和稳定接口，组织数据资产、推进研究阶段、收敛论文交付
- 技术同事负责接入 workspace、核对 profile、维护实现层与 controller 行为

当前外层 scheduler adapter 收敛之后，runtime 的概念主链应按下面这条来读：

- `study charter / startup boundary / publication gate / completion sync`

它的含义不是把判断继续藏在 inner runtime 里，而是：

- `MedAutoScience` outer-loop 负责研究治理、journal / reporting / publication judgment
- OPL scheduler replacement 负责默认周期唤醒、provider SLO 与 runtime manager projection；`MAS supervision scheduler contract` 负责 MAS one-shot tick 的 domain payload、SLO/read-model、owner receipt 和 legacy diagnostic projection；`local` 是显式 legacy diagnostic / cleanup adapter，Hermes gateway cron 只作 explicit legacy diagnostic adapter
- OPL current control state 负责默认 runtime state、attempt event、recovery 与 quest/stage lifecycle；MAS 负责 domain authority refs、owner receipt、typed blocker 和 publication/artifact/source authority
- `MedDeepScientist` 仅提供 frozen source / historical fixture / explicit archive import reference

这条分工不改变 domain truth owner：study framing、数据准备度、publication gate 与 completion sync 仍由 `MedAutoScience` 持有；`Hermes` 只承接当前 scheduler adapter 或显式 hosted target，不把 repo-side seam 升格成独立 study authority。

因此当前更好的地方，不是“多了一个名字”，而是 outer-loop / inner-loop coordination 被显式拆开：

- 是否继续进入 managed runtime，不由 inner runtime 自己偷做决定
- 是否 pause / stop / relaunch / complete，不再只是 backend 内部状态转换
- 是否已经够资格朝论文交付继续推进，要经过 publication gate 与 completion sync，而不是只看 quest 是否还活着

因此，README 首页不再承担“教人逐条执行命令”的职责；命令、payload 和运行约束统一收在这份文档里，供 Agent 调用和人类审计。

## 接口使用原则

Agent 调用接口时，优先遵守以下顺序：

1. 先读状态，再做变更
2. 优先使用平台提供的稳定入口，不直接改底层状态文件
3. 不直接调用 `MedDeepScientist` daemon API，也不绕过 `MedAutoScience` controller
4. 把可审计结果落到 workspace 中，而不是只停留在会话上下文
5. 变更数据资产时，优先使用统一 mutation 入口，而不是散落地手工更新多个文件

对数据资产相关任务，通常先读这些状态：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli data-assets-status --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli assess-data-asset-impact --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli validate-public-registry --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli startup-data-readiness --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli tooluniverse-status --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli data-asset-gate --quest-root /path/to/runtime/quests/<study-id>
```

如果需要初始化数据资产层，可用：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli init-data-assets --workspace-root /path/to/workspace
```

如果需要比较私有数据版本差异，可用：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli diff-private-release --workspace-root /path/to/workspace --family-id master --from-version v2026-03-28 --to-version v2026-04-10
```

## 统一 mutation 入口

当 Agent 需要对数据资产注册表施加可审计变更时，优先使用统一 mutation 入口：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli apply-data-asset-update --workspace-root /path/to/workspace --payload-file /tmp/data_update.json
```

这个入口适合：

- 新增或更新 public dataset 登记
- 新增或更新 private release manifest
- 需要把变更操作作为正式审计记录落盘

这个入口不适合：

- 用来替代所有只读查询
- 把随意的自由文本状态塞进 registry
- 绕过既有 policy 或 release contract，直接做无边界写入

简单说，先判断是不是“要改 registry 状态”；如果不是，先用只读命令。只有当 Agent 需要提交一笔可审计的数据资产变更时，才进入 mutation 流程。

Agent 驱动的数据更新审计会写到：

- `portfolio/data_assets/mutations/`

私有版本差异报告默认写到：

- `portfolio/data_assets/private/diffs/`

startup 阶段的数据准备度摘要默认写到：

- `portfolio/data_assets/startup/latest_startup_data_readiness.json`

quest 级 `data-asset-gate` 采用双层信号：

- 私有数据过期或 release contract 未闭合：`hard block`
- public-data 扩展机会：`advisory`

因此，不要把 public-data 扩展机会误当成必须立刻中断主实验的阻断信号。

大型 public data 资产（例如 MRI archive、GEO raw tar、SRA/FASTQ、影像 zip）默认先保持 remote-only：

- 先登记 accession、license、cohort/modality、保留/拒绝理由与目标 study 作用。
- 只有当 study charter 或 analysis plan 已写明具体用途、预计体积、复用位置与清理/保留策略时，才下载或物化完整数据。
- 如果当前路线停题、止损或一时没有明确用途，应清理本地镜像，保留 registry 与 mutation log 作为可追溯入口。

## mutation payload 示例

### 示例 1：登记 public dataset

```json
{
  "action": "upsert_public_dataset",
  "dataset": {
    "dataset_id": "geo-gse000001",
    "source_type": "GEO",
    "accession": "GSE000001",
    "roles": ["external_validation"],
    "target_families": ["master"],
    "target_study_archetypes": ["clinical_classifier"],
    "status": "candidate",
    "rationale": "Candidate external validation cohort."
  }
}
```

### 示例 2：登记 private release manifest

```json
{
  "action": "upsert_private_release_manifest",
  "family_id": "master",
  "version_id": "v2026-04-10",
  "manifest": {
    "dataset_id": "nfpitnet_master",
    "raw_snapshot": "followup_refresh",
    "generated_by": "pipeline/v2.py",
    "main_outputs": {
      "analysis_csv": "analysis.csv"
    },
    "release_contract": {
      "update_type": ["followup_refresh"],
      "qc_status": "locked"
    }
  }
}
```

这些 payload 是接口示例，不是给医学用户手工填写的表单。Agent 在构造 payload 前，应先确认：

- 当前变更是否确实属于 registry 更新
- 目标 dataset family、study archetype 或 dataset id 是否有明确归属
- 写入后是否能被人类审阅和追踪

## workspace / profile / bootstrap 衔接

Agent 在真正推进研究前，应先确认 workspace 已正确接入。最短路径是：

1. 阅读并准备 [`bootstrap/README.md`](../../../bootstrap/README.md) 中的 profile 和 workspace 要求
2. 用 `doctor` 检查 `workspace_root`、`runtime_quests_root`、`mas_runtime_home`、`studies_root`、`portfolio_root`、`historical_fixture_runtime_root`
3. 用 `bootstrap` 初始化 overlay 和数据资产层

典型命令如下：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli workspace bootstrap --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli runtime overlay-status --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli doctor backend-audit --profile profiles/my-study.local.toml --refresh
```

如果这些环境还没接好，不要急着调用研究阶段接口，因为很多状态落盘路径都依赖 workspace contract。

## Controlled Backend Audit

当 Agent 发现 upstream `DeepScientist` 有新提交，或者准备把本机 frozen source / historical fixture / backend-audit reference 切到新的 intake 版本时，不应直接原地升级。推荐先执行：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli doctor backend-audit --profile profiles/my-study.local.toml --refresh
```

这个检查会统一汇总：

- `repo_check`
  - `explicit_archive_import_ref.controlled_backend_repo_root` 是否已配置
  - 目标目录是否存在、是否是 Git repo
  - 当前 branch、`HEAD`、comparison ref
  - 相对 comparison ref 的 `ahead_count / behind_count`
  - 当前工作树是否干净
  - 如果目标 repo 根目录存在 `MEDICAL_FORK_MANIFEST.json`，则额外暴露受控 fork manifest：
    - `engine_family`
    - `freeze_base_commit`
    - `applied_commits`
    - `is_controlled_fork`
    - `upstream_remote_name`
    - `upstream_ref`
- `workspace_check`
  - 当前 workspace / managed runtime / controlled backend audit contract 是否仍然完整
- `overlay_check`
  - 医学 overlay 是否仍然全部处于 `overlay_applied`

核心目标是把“上游有更新”与“现在适合纳入 backend audit / parity intake”分开判断。

典型 `decision` 含义如下：

- `audit_delta_available`
  - upstream 有新提交，且当前 repo / workspace / overlay 状态允许进入 audit / parity intake 流程
- `needs_branch_review`
  - 当前 checkout 不在稳定主线；如果只是受控 fork 的 `main` 保留了经过审计的领先提交，这一项不应触发
- `blocked_dirty_repo`
  - 本地 `MedDeepScientist` repo 有未提交改动，应先清理
- `overlay_reapply_needed`
  - 当前没有 upstream 更新，但医学 overlay 已不再处于理想状态，应先重覆写
- `up_to_date`
  - 当前既没有检测到 upstream 更新，也没有 overlay 漂移

对于 Agent 来说，推荐流程是：

1. 先跑 `doctor backend-audit`
2. 只在结果明确允许时，才把 `MedDeepScientist` 变化作为 source provenance / parity fixture intake 处理
3. intake 后重新跑 `doctor backend-audit`
4. 必要时执行 `runtime reapply-overlay`
5. 最后再执行一次 `workspace bootstrap` 或至少 `runtime overlay-status`

普通的非 fork 仓库可以继续把 `origin/main` 作为默认的 comparison ref，当前 `backend-audit` 也会以这个 ref 作为比较基础。

如果目标 repo 是受控 fork，`recommended_actions` 可能返回 `run_controlled_fork_intake_workflow`，表示应走 intake 流程，而不是直接对稳定线执行 `pull origin main`。

对于受控 fork，推荐的 remote 语义应固定为：

- `origin` 指向 fork 自己的 GitHub 主仓，其 `main` 维护 fork 的稳定线和 intake 合并点
- `upstream` 指向 `DeepScientist` 上游仓库，所有兼容审计、`backend-audit` 等命令都应以 `upstream/main` 作为 comparison ref

## Phase 1 gate 与真实执行

当前所谓 Phase 1 已经允许把 profile 的 historical backend repo root 指向一个受控的 sibling fork，例如本地 checkout 或 GitHub repo `med-deepscientist`；它对外的产品名是 `MedDeepScientist`。当前主链已经把 `adapters/deepscientist/*` 退出正式运行面，但这仍不等于 external `Hermes` runtime truth 已经到位。`med_deepscientist_repo_root` 仍可作为 TOML 输入配置项；`doctor profile --format json` 只会在 `source_provenance`、`historical_fixture_ref` 与 `explicit_archive_import_ref` 下暴露历史引用面。现阶段它主要服务于 `backend-audit` 这类审计与 provenance/parity intake 流程，不是默认 workspace truth 或 product entry。如果 repo 根目录存在 `MEDICAL_FORK_MANIFEST.json`，系统会把它识别为受控 fork并暴露 manifest 元数据。与此同时，`ops/mas/behavior_equivalence_gate.yaml` 是新 workspace 的关键 gate artifact；旧 `ops/med-deepscientist/behavior_equivalence_gate.yaml` 只作为 historical fixture / archive import reference 读取。`med_autoscience.workspace_contracts.inspect_behavior_equivalence_gate` 依赖其中的 `schema_version`、`phase_25_ready` 与 `critical_overrides`，后者通常指向 site-packages 级别的本地改动。

当前 closeout 已把默认 generic runtime owner 切到 OPL provider-backed stage runtime。MAS 只作为 domain authority refs、owner receipt、typed blocker、artifact/source/quality refs 与 diagnostic explanation owner；默认 scheduler owner 已迁到 OPL replacement；显式 `local` scheduler 的意义只剩 legacy tombstone/provenance 或 cleanup diagnostic，不再按固定间隔调用 MAS-owned supervision tick script；Hermes gateway cron 只在显式 status/remove 时承担 diagnostic cleanup 角色。它们都不把 external Hermes repo、external MDS repo 或旧 MDS daemon 重新变成默认 runtime truth。

### 当前 `Hermes` 名义与宿主安装的关系

`med_autoscience.runtime_transport.hermes` 当前只能按 explicit executor/proof diagnostic target 或 historical compatibility reference 理解。默认 MAS operation 走 OPL provider-backed stage runtime，并只把 MAS domain authority refs、owner receipt 或 typed blocker 作为回执边界，也就是说：

- 本仓默认写出 `opl_runtime_ref = opl_hosted_stage_runtime` / `runtime_ref = opl_hosted_stage_runtime` / `runtime_engine_id = opl-hosted-stage-runtime`
- controlled research metadata 不再需要 `research_backend_id = mas_runtime_core` / `delegated_domain_adapter_id = mas_runtime_core` 作为 runtime owner；若历史 payload 仍出现这些字段，只能按 retired provenance / migration input 读取
- `Hermes gateway cron` 只负责 legacy scheduler diagnostic cleanup 语义：job registry、cadence、latest cron session、gateway liveness projection 和旧 job/script removal；不调用新的 MAS tick script，不持有 study truth、runtime authority、session truth 或 publication authority
- explicit hosted Hermes / `hermes_agent` proof target 必须通过 runtime backend contract、readiness proof 和 fail-closed gate 显式接入；它不得成为 default provider 或 MAS runtime truth
- MDS 只保留 frozen source archive、historical fixture、explicit archive import / provenance reference 和 read-only backend audit；runnable `runtime_transport/med_deepscientist.py` 已退役，不参与默认 watch/status/execute/recovery

当前代码事实也限制了优化方式：`systemd|cron|launchd|docker` workspace-local service manager 已从公开 CLI choices 移除，只能作为内部 cleanup/audit evidence 返回 retired 状态，并不是可用替代 scheduler。本地默认运行已经由 OPL replacement 承担；MAS `local` adapter 只保留 legacy diagnostic / cleanup 和同构 status / SLO，不能让用户或 workspace 重新维护旧 host service。

`behavior_equivalence_gate.yaml` 现在是 workspace 兼容和历史迁移 gate，不是声明 “MDS daemon 行为已经完全等价” 的口径。行为等价事实以 `mds_behavior_equivalence_matrix` 为准：MAS 默认运行不要求 MDS daemon，也不提供旧 MDS WebSocket terminal streaming / connector background delivery；这些差异必须显式展示，不能被 functional-monolith status 覆盖。

## Runtime Protocol Surface

Phase 2 曾把 `MedAutoScience` 的 runtime 布局与 quest 状态解析提升为 repo-local protocol 层，作为迁移输入收束散落在 controller 或 adapter 里的路径规则。当前 active 口径下，这些 protocol 名称不能再读成 MAS generic runtime owner；默认 runtime / attempt / queue / retry / worker residency / status owner 已归 OPL，MAS 只保留 domain authority refs、owner receipt、typed blocker 与 diagnostic/provenance refs。

- `med_autoscience.runtime_protocol.layout`
  - 负责 workspace 内 MAS-owned `runtime/`、`runtime/quests/`、`ops/mas/`、startup brief / payload root、behavior gate 等 project-local runtime 路径契约
  - `study_runtime_router`、`workspace_contracts`、`workspace_init` 等 controller / scaffold 代码应统一经由这层派生路径，而不是散落硬编码 legacy `ops/med-deepscientist/...`
- `med_autoscience.runtime_protocol.topology`
  - 负责 `paper_root`、`worktree_root`、`quest_root`、`study_root` 之间的关系解析
  - 新 workspace 显式承认的受管布局是 `runtime/quests/<quest_id>` 普通目录、study-local paper/manuscript authority 与 `domain_authority_refs.sqlite` refs index；旧 `ops/med-deepscientist/runtime/quests/<quest_id>/.ds/worktrees/<worktree>/paper` 只作为 historical fixture / archive import reference
  - `study_delivery_sync` 这类 controller 应调用 `resolve_paper_root_context()`，而不是自己拼 `.ds/worktrees/...` 或依赖 `parents[4]` 这类脆弱层级
- `med_autoscience.runtime_protocol.quest_state`
  - 负责 `runtime_state.json`、quest status、active quest 枚举、main `RESULT.json`、active `stdout.jsonl` 与最近 stdout 行的统一读取
  - `publication_gate`、`domain_health_diagnostic`、`study_runtime_router` 这类 controller 应直接消费这一层，而不是各自重复遍历 `.ds/...`
- `med_autoscience.runtime_protocol.paper_artifacts`
  - 负责 latest `paper_root`、`paper_bundle_manifest.json`、`artifact_manifest.json`、`submission_minimal` 输出路径的统一解析
  - `publication_gate`、`medical_publication_surface`、`submission_targets` 不再自己猜测 `paper/` 下的交付拓扑
- retired `med_autoscience.runtime_protocol.user_message`
  - 曾负责 `.ds/user_message_queue.json`、`.ds/runtime_state.json` 中 `pending_user_message_count`、以及 `.ds/interaction_journal.jsonl` 的一致落盘
  - 当前不作为 active queue / journal truth；OPL 持有 message queue、delivery retry/dead-letter 与 provider wakeup，MAS controller 只记录 task-intake / owner-route / typed blocker refs
  - `data_asset_gate`、`figure_loop_guard`、`medical_publication_surface` 这类 controller 不再自己维护 queue/journal 真相

Phase 3 开始，transport 面也开始显式收口：

- retired `med_autoscience.runtime_transport.mas_runtime_core`
  - 不再作为 MAS domain adapter backend contract、local runtime state、session/liveness projection、quest lifecycle control 或 artifact handoff owner
  - 当前 replacement 是 OPL provider-backed stage runtime + MAS domain authority refs / owner receipt / typed blocker
- `med_autoscience.runtime_transport.hermes`
  - 只负责 explicit hosted/proof diagnostic target 或 compatibility reference
  - 不作为默认 operation dependency
- MDS retained surfaces
  - 只保留 source provenance、historical fixture、explicit archive import reference、upstream learning、parity oracle reference 与 read-only backend audit
  - 不再提供 runnable MAS transport module，不负责 daemon URL 解析、quest lifecycle control、quest state、artifact topology 或 user message queue 协议真相

production code 只允许依赖 `runtime_protocol` / `runtime_transport` 的 backend contract；不得因为旧 diagnostic transport 存在就恢复 MDS 默认 runtime dependency。

对于单个 study 的 runtime 编排，`study_runtime_router` 的稳定入口、typed surface 归属、decision 执行边界与 side-effect 约束，另见 [`study_runtime_orchestration.md`](../control/study_runtime_orchestration.md)。

## Target Layering

理想形态下，这个系统应收敛成 5 层，而且每层只做一类事情：

1. `policy`
   - 只表达医学治理规则、发表约束、数据资产规则、研究路线偏置
   - 不读写 runtime 文件，不发 daemon 请求
2. `controller`
   - 只负责把政策、study 状态和任务目标编排成明确动作
   - 不自己猜路径，不自己拼 `.ds/...`，不自己维护 queue 文件
3. `runtime_protocol`
   - 只负责 `MedAutoScience` 承认的 runtime 文件契约
   - 包括 topology、quest_state、paper_artifacts、user_message
   - 这是 filesystem-facing truth
4. `runtime_transport`
  - 只负责 substrate / backend transport
  - 默认由 OPL provider-backed stage runtime 持有；MAS 只服务 DomainIntent、owner receipt、typed blocker 和 authority refs 场景，`hermes` 和 `med_deepscientist` 只服务显式 hosted/diagnostic/reference 场景
  - 这是 process/network-facing truth
5. `engine`
  - 当前默认 engine 是 OPL provider-backed stage runtime；MAS 不再承担 delegated runtime engine，只承担 domain authority refs / owner receipt / typed blocker
  - 旧 MDS daemon / UI / connector / team 行为只作为 historical fixture 或 explicit archive import reference

对应关系应是单向的：

- `policy -> controller`
- `controller -> runtime_protocol`
- `controller -> runtime_transport`
- `runtime_transport -> engine/reference`

`controller` 不应反向依赖 adapter，也不应直接触碰 engine 私有实现细节。

## What We Intend To Remove

沿这条主线，后面会继续优化掉这些没必要的部分：

- adapter 中重复存在的一套“第二真相”
  - 例如 `paper_bundle.py`、`mailbox.py`、`daemon_api.py`、`runtime.py` 曾分别重新承载 artifact、queue、transport、quest state 解析
- controller 内部重复的拓扑推导
  - 例如手写 `.ds/worktrees/...`、`parents[4]`、零散 `glob`
- 同一概念混放在一个文件里
  - 例如一个模块同时做本地 queue 落盘和 daemon HTTP control
- 只为兼容历史命名而保留的多层转发
  - `adapters/deepscientist/*` 已经从正式主链删除；后续不要重新引入第二套 protocol / transport 真相
- 没有必要长期保留的 `DeepScientist` 品牌耦合命名
  - 对外 profile 和 workspace 默认显示已经收口到 MAS-owned `runtime/quests`、`runtime/` 与 `ops/mas`
  - 剩余 `med_deepscientist_*` 字段和 `ops/med-deepscientist/*` 路径只允许作为 historical fixture、explicit archive import reference、backend audit 或 parity oracle 兼容名

## 审计与人类复核

`human-auditable` 不等于“人类手工逐条执行命令”，而是：

- Agent 所做的变更有明确接口和落盘位置
- 人类可以审阅数据资产变化、研究阶段输出和最终交付材料
- 关键继续/停止决策仍由人类负责

因此，推荐的工作方式是：

1. 人类定义研究目标和边界
2. Agent 调用运行层接口推进
3. 平台把关键状态和结果落盘
4. 人类基于这些审计痕迹做关键判断
