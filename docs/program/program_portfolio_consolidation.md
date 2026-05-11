# Program Portfolio Consolidation

Status: `active portfolio governance`
Date: `2026-05-09`
Owner: `MedAutoScience`

## 结论

`docs/program/program_portfolio_consolidation.md` 是后续 MAS/MDS 收敛工作的唯一总控入口。Agent 接到后续执行任务时，先读本文，再按本文的 next execution queue 选择 lane、worktree、验证、吸收和清理；无需另开规划会。

当前三层关系固定如下：

1. 本文是唯一 portfolio 入口，负责决定 active owner doc、执行顺序和 closeout 口径。
2. `mas_single_project_mds_absorb_program.md` 是 MDS 退场、MAS 单项目吸收、workspace layout 收敛、entry compat retirement 和 no-history physical absorb 的总执行计划。
3. `runtime_lifecycle_sqlite_migration_program.md` 是 MAS single-project absorb 之下的 runtime / Git 子计划，负责 runtime lifecycle SQLite authority、workspace root Git full retirement、quest Git retirement、restore proof 和 lifecycle ledger。
4. 旧方向板、增强 backlog、owner-boundary、parity matrix、completion ledger、preflight / cleanup / gate 文档已经按职责移入 `docs/history/program/`、`docs/policies/` 或 `docs/references/`；它们可作为支撑材料引用，不再作为并行总控入口。

因此，Git 退役和 MAS 吸收 MDS 不作为两条互相竞争的改造线推进。技术实现可以分 lane 并行，但必须在同一个 authority contract、同一个 cutover gate 和同一个 closeout ledger 下吸收。SQLite runtime authority 接管的是 MDS Git-era 的 runtime lifecycle、lineage、workspace allocation、checkpoint metadata、diff / Canvas read model、restore index 和 runtime lifecycle ledger；MAS single-project absorb 接管的是产品入口、owner 边界、代码归属、真实 workspace layout 和 compatibility retirement。

2026-05-07 补充：Runtime Control 和 Progress Projection 已经从待讨论的大 lane 进入主线 contract。`owner_route -> consumer latest -> executor dispatch -> rescan` 是 runtime/control 的固定执行链；`study_macro_state -> user_visible_projection` 是用户可见 progress 的固定读模型。后续 program 不再把这两条作为独立大重构入口反复打开；新功能、MDS 吸收、workspace layout、profile/entry compatibility retirement 或 no-history physical absorb 都必须消费这两条 contract，不能重建第二套用户状态、runtime action 或 publication readiness 判断。

2026-05-08 校准：近期模块化与边界重构没有改变 portfolio 队列。当前事实是：Runtime Control、Progress Projection、quest Git retirement、workspace root Git retirement 和 architecture fitness wave 都已经进入 landed/guard 口径；下一步不再重开 Git 退役或全仓结构治理大计划。首个 `workspace_layout_de_mds_ds` lane 已把静态 profile template、doctor/show-profile 输出、bootstrap/quickstart/agent-runtime 文档与旧 MDS/DS path 的显示边界收口到 MAS-owned layout：`runtime/quests`、`runtime/` 与 `ops/mas` 是默认可见路径，`med_deepscientist_*` 只保留为 historical fixture / explicit archive import reference / backend-audit ref。`profile_entry_compat_retirement` lane 已继续把 MCP 旧 `med_deepscientist_upgrade` mode fail-closed、profile JSON 顶层改为 `source_provenance`、`historical_fixture_ref` 与 `explicit_archive_import_ref`、workspace contract 命名切到 managed runtime / controlled backend、product-entry / progress 的默认 `executor_owner` 切到 backend-neutral `controlled_research_backend`。最终 `no_history_physical_absorb` campaign 已完成 repo-level closeout：source provenance 固定到 `med-deepscientist@35976b7d6e3b99b15b57ec44ff5f5d959b342ecc` 与 archive sha256，author audit guard 禁止上游 contributor footprint，parity harness 与 retained capability absorb 已把 MDS 价值收口为 MAS-owned runtime/artifact/quality surfaces 或 oracle fixtures，external MDS 不再是默认 MAS operation 依赖。

2026-05-08 functional monolith closeout：`functional_monolith_completion=landed` 已把目标从“MAS 是唯一入口”推进到“MAS 默认运行、诊断、进度可视化、artifact/quality/status/progress/cockpit/OPL handoff 都不要求外部 MDS repo、daemon、runtime root 或 WebUI”。这仍不是函数级 1:1 搬迁；完成口径是 capability supersede / rewrite / retire。外部 `med-deepscientist` 现在只保留为 frozen source archive、historical fixture、explicit archive import / provenance reference；所有来自外部 MDS / DeepScientist 的材料只能通过 source provenance、snapshot hash、license refs、capability classification、parity proof 和 MAS maintainer-authored commit 进入，不增加 `med-autoscience` default-branch contributor graph。

2026-05-08 behavior equivalence closeout，2026-05-09 scheduler wording correction：`functional_monolith_completion=landed` 不再允许被解释为旧 MDS daemon 行为完全等价。`mds_behavior_equivalence_matrix` 已落地并固定 `completion_claim=default_independence_not_full_behavior_equivalence`：MAS 默认 scheduler adapter 是 MAS-owned `local` scheduler，macOS backend 已落地为 LaunchAgent，每 300 秒执行一次 MAS-owned supervision tick script；desired script 依序运行 `watch-runtime --max-ticks 1`、`supervisor-scan`、`supervisor-consume`、`supervisor-execute-dispatch`。Hermes gateway cron 只在显式选择时作为 optional adapter。旧 MDS resident HTTP/WebSocket daemon、resident WebSocket terminal attach、connector background delivery、GitOps runtime lifecycle 和 workspace-local launchd/systemd/cron/docker service 都不是当前 MAS default behavior。旧 workspace-local host service 只作为 retired cleanup evidence，被 `runtime-ensure-supervision` 清理后回到 MAS scheduler contract。resident WebSocket terminal attach、terminal input/resize/detach 和 UI-issued runtime control 不是当前 read-only landed scope，但也不是 abandoned / retired requirement；它们归后续 interactive parity lane。

2026-05-08 runtime continuity closeout：`runtime_continuity_completion=landed` 已补齐 MDS daemon 退役后的 durable session/worker tracking 与 crash-recovery intent。MAS 现在通过 `runtime_session` read model、`recovery_intent` ledger、`runtime_reconcile_trigger` 和 `runtime_continuity` 投影，让用户入口能回答“有没有 worker、上次看到什么时候、为什么没继续、下一次怎么恢复”。这项 closeout 不新增 resident daemon，不改变 MAS scheduler 300 秒 tick owner，也不允许 read model / safe trigger 授权 quality、publication 或 submission readiness。

2026-05-08 live console closeout：`live-console-parity=landed` 已把旧 MDS WebUI 的观察类价值收口为 MAS-owned read-only surface。默认医生/PI 入口仍是 Progress Portal；维护者/高级用户需要 session/run、terminal tail、log tail、runtime health、supervision freshness 和 artifact/event refs 时，进入 MAS Live Console。该能力不依赖外部 MDS repo / daemon / WebUI，不导入旧 WebUI 代码或 history，也不把 UI 升级成 runtime 或 publication authority。

2026-05-08 WebUI user parity correction，2026-05-10 OPL App workbench 更新：Portal 已落地固定 MAS 进度入口，per-study/per-paper 工作台、Route / Decision Trail read-only helper、visible runtime conversation panel、study-scoped Live Console、authorized pause/resume/stop action apply receipts 与 terminal attach fail-closed gate 已进入 repo contract。旧 MDS WebUI 的 per-project/per-quest 工作台仍是 UX oracle；下一阶段不再让 MAS 独立复制完整 WebUI，而是把 MAS projection / action receipt / terminal attach gate 接到 OPL App 的统一 Runtime Workbench。workspace-local Portal / Live Console 继续作为 fallback、evidence 和 operator debug 入口；OPL App 持有产品 UI、通知、approval transport 和 terminal shell，MAS 继续持有 study truth、publication quality、runtime owner 和 terminal attach audit。

2026-05-08 paper autonomy stability 分层：`functional_monolith_completion=landed` 只说明 repo / 默认入口 / 可视化 / runtime core 依赖已经由 MAS 承接；`paper_autonomy_stability=landed` 是更高一层，必须额外具备真实 profile inventory、supervisor reconcile、workspace migration dry-run、read-only soak 和真实 paper status/progress 可读证据。当前新增的 `real_paper_autonomy_soak_inventory` 只做 dry-run/inventory，枚举 `/Users/gaofeng/workspace/Yang/*/ops/medautoscience/profiles/*.toml` 并报告 migration readiness、status/progress readability、active/parked/completed reason 与 legacy MDS launcher/default runner evidence；它不写真实 workspace、不运行 reconcile apply、不修改 `current_package`、不写 publication gate，也不替代 Lane 1 blocker fix、Lane 2 reconcile CLI、Lane 3 owner_route schema 或 Lane 4 migration apply。

2026-05-08 runtime evidence closeout：后续三件优化已收口为 repo-owned read-model/evidence surface，而不是新的 program board。`outer_supervision_slo=landed` 把 MAS scheduler 300 秒外环监管的新鲜度投影到 `runtime-supervision-status`、`runtime-supervisor-reconcile`、`runtime_reconcile_trigger`、`study_progress`、Product Entry 和 Portal；它只生成 `fresh/due/stale/missing/blocked`、dedupe fingerprint 与 canonical one-shot `supervisor-reconcile --dry-run` 推荐，不恢复 MDS daemon 或旧 workspace-local service。`portal_console_soak=landed` 生成 MAS-owned 只读 Portal + Live Console evidence，允许写 display/read-model artifact，禁止写 paper/package/publication/controller/runtime SQLite authority。`paper_autonomy_stability_evidence=evidence_read_model_landed` 把真实 profile inventory、supervisor reconcile dry-run、workspace migration dry-run 和 real workspace soak monitor 合并成单一 read model；真实 workspace 若因 human gate、publication gate、parked handoff 或 profile unreadable 阻塞，必须写 blocker 和下一步，不能把 `paper_autonomy_stability` 伪造为 landed。

2026-05-09 fresh reassessment，2026-05-10 stage knowledge update 后：当前主线仍是 MAS monolith 收尾，但下一步不再是“继续吸收 MDS repo”或“恢复 MDS daemon”。机器矩阵当前固定为 `17` 个 behavior surface：`2 behavior_equivalent / 6 purpose_equivalent_with_different_timing / 1 purpose_equivalent_with_authority_split / 3 partially_equivalent / 4 not_equivalent_retired / 1 historical_fixture_only`，`fully_equivalent_to_mds_daemon=false`。用户感知和受控交互已有 repo contract：per-study/per-paper Portal 工作台、visible runtime conversation panel、study-scoped Live Console、authorized pause/resume/stop action apply receipts、stage knowledge packet / typed closeout / router receipt visibility、`focused_lanes.portal-route-decision-trail` 和 `focused_lanes.terminal-attach-gate`。下一步是 evidence-gated polish、真实 paper stage injection soak 和 terminal attach owner 实现；已经退役的 connector background delivery、GitOps runtime lifecycle、MDS daemon lifecycle controls 和 workspace-local service manager 不作为默认 backlog 重开。

2026-05-09 runtime watchdog / cost closeout：outer supervision latency 的推荐解法已从“缩短 Hermes cron”改为“MAS-owned per-run watchdog + action cost guard”。`CodexExecTurnRunner` 默认启动 per-run wrapper，由 wrapper 托管 `codex exec` 子进程、刷新 `worker_lease` heartbeat / cursor / exit / monitor state，并在 child exit 后立即调用 `complete_turn_and_normalize`。MAS scheduler 继续保持 300 秒 fail-safe 外环，默认 adapter 是 local，Hermes 是 explicit optional adapter；Portal、Live Console、study-progress、runtime watch 和 supervisor reconcile 只显示 `observe_only` / `reconcile_dry_run` / `controller_apply` / `codex_worker_dispatch` 分类、`will_start_llm` 与 dispatch counters。重复 tick / duplicate fingerprint 只能 no-op suppression，不得重复启动 Codex worker。该 closeout 仍不恢复 MDS daemon、不恢复 workspace-local service、不引入外部 MDS repo 或 WebUI。

2026-05-09 paper progress degradation closeout：本轮把“MAS monolith 上线后论文自动推进变慢”的真实降级风险收敛为机器可读 gate，而不是重开 MDS 吸收或恢复 daemon。`paper_progress_degradation_classifier=landed` 已把 17 个 MDS behavior surface 和 `owner_handoff_dispatch` / `repeat_suppression` / `work_unit_redrive` 三个 P0 overlay 映射为 `production_degrading`、`production_risk`、`diagnostic_degrading`、`acceptable_design_difference` 或 `retired_non_goal`。`owner_handoff_repeat_suppression_closeout=landed` 保证 controller work-unit evidence adoption 后进入 `owner_handoff` / `publication_gate_recheck`，repeat suppression 不得压掉下一 owner，也不得重复启动同一 analysis lane。`paper_progress_stall_safe_reconcile=landed` 把 same-fingerprint loop、read churn、stale truth surface 和 retry budget exhausted 投影为 `paper_progress_stall`；`runtime-supervisor-reconcile --dry-run` 必须零 Codex dispatch，`--apply` 只能在 fresh owner_route、未 parked/completed、无 human gate、无 publication gate missing、retry budget 未耗尽且 action fingerprint 新鲜时派单。`paper_progress_degradation_evidence=landed_read_model` 与 `production_blocker_impact_projection=landed` 已把真实 workspace evidence、next owner、why not running、same fingerprint / handoff、`will_start_llm`、safe reconcile command 和 source refs 投到 study-progress、Portal、Live Console、workspace cockpit、Product Entry 与 OPL handoff。该 closeout 只关闭 repo-level 自动推进降级 guard；真实 human gate、publication gate、parked handoff 或 profile unreadable 仍必须作为 evidence blocker 记录，不能被写成论文自治已完全 landed。

2026-05-10 AI-first paper autonomy closure 校准：`paper_progress_degradation_closeout` 关闭的是 repo-level 自动推进降级 guard，不等于“初稿 -> AI reviewer/gate -> 自动分析或改稿 -> 复评 -> 继续循环直到通过或转向/止损”已经端到端闭合。新的最高优先级 program 是 [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md)：它把 AI reviewer finding 到 repair work unit、负结果到 route decision、canonical manuscript rewrite、stage knowledge/memory consumption and writeback、mechanical route cleanup、gate replay、AI reviewer re-eval、OPL/Hermes queue soak 和真实 DM002/DM003/Obesity 验收收成同一条可执行目标。该 program 不重开 MDS daemon，也不让 OPL/Hermes 持有 MAS truth；gateway 只负责 24h queue/wakeup/notification/retry，医学质量与论文推进闭环仍由 MAS owner surface 持有。

2026-05-11 OPL stage-led family framework 校准：本文仍是 MAS 仓内部 program portfolio 入口；但涉及 OPL 作为 Codex-first、stage-led 完整智能体运行框架、Temporal provider、执行语言、OPL-hosted path、domain-agent skeleton 和跨仓旧面退役的总入口，统一回到 `/Users/gaofeng/workspace/one-person-lab/docs/references/runtime-substrate/opl-stage-led-agent-framework-roadmap.zh-CN.md`。MAS 的 [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) 是 domain-side 子计划：只有 OPL master P1/P2 证明 Temporal provider skeleton、Codex stage activity runner、human-gate signal/query 和 provider receipt 可运行后，MAS 才进入真实 paper-line guarded soak 与物理退役。它不替代 `ai_first_paper_autonomy_closure` 的医学论文主循环，也不得把 OPL attempt completion 当成 MAS paper progress 或 publication quality verdict。`Stage` 是大型任务步骤，`Codex CLI` 是 stage 内默认 concrete executor 和最小执行单元；OPL provider 只能承载 attempt，MAS 继续持有 domain truth。

2026-05-11 skeleton/lifecycle 上收校准：OPL 不应只做入口聚合，而应上收所有智能体运行外围能力。MAS 已验证的 SQLite lifecycle、file lifecycle、artifact index、retention、restore proof、migration ledger 和 workspace lifecycle 经验，需要拆成 `framework_generic` 与 `mas_domain_specific` 两张清单：前者进入 OPL framework primitive，后者留在 MAS truth surface。MAS/MAG/RCA 的目标形态是统一 `domain-agent skeleton`，即按同一 `agent/`、`contracts/`、`runtime/`、`docs/` repo-source 边界向 OPL 暴露 stage、prompt、Skill、knowledge、quality gate、sidecar、receipt schema、projection builder 和 artifact locator contract；真实论文、运行日志、receipt 实例、中间产物和最终交付物必须在 workspace / runtime artifact root，不落在开发仓源码目录。业务内部实现不要求完全同构。MAS 物理目录重组必须等 direct skill path、OPL-hosted path、restore/provenance proof、focused tests 和真实 paper soak 都稳定后再执行。

2026-05-08 hub role hardening closeout：中心 hub 风险已从“建议”转为 architecture fitness guard。Runtime Supervisor、Product Cockpit、MCP Adapter 与 Display Validation 的本轮收口只改变内部角色边界，不改变 CLI/MCP/controller payload 或 live study artifact。`module_boundary_audit` / `architecture_owner_boundary` 现在要求 hub 声明 `authority`、`read_model`、`adapter` 或 `materializer`；read-model / adapter hub 如果声明 authority、控制 runtime/publication 或写 runtime/study truth，会被 blocking。该 hardening 是横向 guard，不改变 next execution queue。

## Next Execution Queue

后续 Agent 默认按下面队列自动取下一项；只有遇到真实 blocker、外部 active owner 冲突或用户改口时才暂停说明。

| order | execution lane | owner doc | required closeout |
| --- | --- | --- | --- |
| `1` | `workspace_layout_de_mds_ds` | `mas_single_project_mds_absorb_program.md` | `landed`: 用户/医生可见 workspace layout、static profile template、doctor/show-profile 输出、bootstrap/quickstart/agent-runtime 文档和 quest 管理命名已去 MDS/DS 化；旧路径仅保留为 migration ledger、restore proof 或 maintainer diagnostic。 |
| `2` | `profile_entry_compat_retirement` | `mas_single_project_mds_absorb_program.md` | `landed`: profile JSON、MCP doctor audit mode、workspace contracts、product-entry/progress executor owner 和 docs 已从默认 MDS entry/compat 退到 explicit backend audit / controlled backend audit；旧 `med_deepscientist_*` 输入字段保留为只读诊断和 backend/oracle 审计。 |
| `3` | `no_history_physical_absorb` | `mas_single_project_mds_absorb_program.md` | `landed`: no-history source provenance、author audit guard、capability parity harness、MAS-owned retained capability absorb、external runtime dependency retirement 和 docs closeout 已完成；没有把上游 DeepScientist / med-deepscientist git history 或 contributor footprint 带入 `med-autoscience main`。 |
| `4` | `functional_monolith_completion` | `mas_single_project_mds_absorb_program.md`、`../runtime/contracts/runtime_core_convergence_and_controlled_cutover.md` | `landed`: MDS remaining surface inventory、runtime core ingest、MAS-native progress/status replacement、legacy MDS WebUI default retirement、OPL App family-level handoff、compat/oracle shrink-to-diagnostic 和 local contributor audit guard 已落地；外部 MDS checkout 不再是默认 operation 或默认 diagnostic dependency，OPL App 只消费 MAS refs/deep links，不重解释 study truth。 |
| `4b` | `mds_behavior_equivalence_audit` | `../references/mds-parity/mds_behavior_equivalence_gap_matrix.md`、`../references/mds-parity/mds_capability_parity_matrix.md` | `landed`: default independence 与 full daemon equivalence 分离；turn completion continuation 已行为等价，Live Console 已提供旧 WebUI 观察类能力的 read-only purpose equivalence；resident daemon / connector threads / GitOps lifecycle / workspace-local host service 的剩余差异已进入机器可读矩阵和 active docs。resident WebSocket terminal attach / UI control 作为 future interactive parity candidate 记录，不写成已放弃。 |
| `4c` | `runtime_continuity_completion` | `../runtime/control/runtime_supervision_loop.md`、`../runtime/projections/runtime_health_kernel.md`、`../runtime/projections/study_progress_projection.md`、`../runtime/display/progress_portal.md`、`../references/mds-parity/mds_behavior_equivalence_gap_matrix.md` | `landed`: `runtime_session`、`recovery_intent`、safe reconcile trigger 和 runtime continuity projection 已覆盖用户可见 worker tracking / last seen / recovery intent；仍按 scheduler-bound MAS Runtime OS 口径，不重引入 MDS daemon 或旧 workspace-local service。 |
| `5` | `runtime_evidence_closeout` | `mas_single_project_mds_absorb_program.md`、`../runtime/control/runtime_supervision_loop.md`、`../runtime/display/progress_portal.md`、`../runtime/display/live_console_ui_contract.md` | `landed/evidence-gated`: outer supervision latency SLA、Portal/Live Console real workspace soak runner 和 paper autonomy stability evidence read model 已落地；`paper_autonomy_stability` 仍只能在真实 evidence 无 blocker 时写成 landed，否则保持 `evidence_landed_with_blockers`。 |
| `5a` | `runtime_watchdog_cost_closeout` | `../runtime/control/runtime_supervision_loop.md`、`../runtime/control/supervision_scheduler_contract.md`、`../references/mds-parity/mds_behavior_equivalence_gap_matrix.md` | `landed`: MAS per-run worker wrapper / watchdog 已承接低延迟 child exit 感知，runtime_session / Live Console / Portal 投影显示 watchdog state 与 `will_start_llm`；supervisor / runtime_watch 记录 dispatch counters 与 duplicate guard；默认 local scheduler 的 300 秒 tick 仍是 fail-safe，Hermes cron 只是 explicit optional adapter，不作为高频 LLM scheduler。 |
| `5b` | `portal_webui_user_parity` | `../references/mds-parity/mds_webui_user_parity_gap_review.md`、`../runtime/display/progress_portal.md`、`../runtime/display/mas_live_console_mds_webui_parity_plan.md` | `landed_read_only_contract / soak-polish`: Portal 已进化到 per-study/per-paper 工作台，含 study-scoped deep links、Route/Decision Trail、Path/Stage、Runtime/Run、Conversation、Terminal/Logs、Artifacts 和 source refs；`focused_lanes.portal-route-decision-trail` 固定只读路线图合同。后续只做真实 workspace soak/source-ref/route-input polish。 |
| `5c` | `runtime_interactive_parity_guarded` | `../references/mds-parity/mds_webui_user_parity_gap_review.md`、`../runtime/display/live_console_ui_contract.md` | `landed_fail_closed_gate / partial_apply_landed`: study-scoped Live Console、authorized pause/resume/stop action apply receipts 与 terminal attach gate 已落地；terminal attach/input/resize/detach 只能在 threat model、owner gate、idempotency、audit 和 token/lease contract 完整后进入实现。 |
| `5d` | `opl_app_mas_runtime_workbench` | `opl_app_mas_runtime_workbench_program.md`、`../references/integration/progress_portal_opl_app_integration.md` | `active plan`: OPL App 成为 MAS 人类运行工作台主入口；MAS 暴露 `mas_opl_runtime_workbench_projection`、action receipt 和 terminal attach owner gate；OPL App 渲染 App-native study workbench、terminal/log 面板、conversation、artifacts 和安全 actions。workspace-local Portal / Live Console 保留为 fallback/evidence。 |
| `6` | `paper_progress_degradation_closeout` | `../references/mds-parity/mds_behavior_equivalence_gap_matrix.md`、`../runtime/control/runtime_supervision_loop.md`、`../runtime/display/progress_portal.md`、`../runtime/display/live_console_ui_contract.md`、`../references/verification/plan_completion_ledger.md` | `landed`: 论文自动推进降级分类、P0 owner handoff / repeat suppression、stalled work-unit safe reconcile、真实 workspace degradation evidence read model 与 production blocker projection 已落地；dry-run reconcile 零 dispatch，apply 受 owner_route / gate / retry / fingerprint guard 约束；read model / UI 不授权 quality、publication 或 submission ready。 |
| `7` | `ai_first_paper_autonomy_closure` | `ai_first_paper_autonomy_closure_program.md` | `active`: AI reviewer finding 必须进入可执行 repair work unit；analysis weak/negative/unexpected result 必须进入 claim downgrade、bounded repair、switch line、return_to_scout、stop_loss 或 human_gate；canonical manuscript / table / figure / package source 必须产生 artifact delta 后 replay gate 并触发 AI reviewer re-eval；DM002、DM003、Obesity 真实 paper soak 必须证明 queue -> dispatch -> repair/review/gate -> receipt -> notification -> progress delta 或 blocker。 |
| `8` | `opl_temporal_mas_runtime_retirement` | `opl_temporal_mas_runtime_retirement_program.md` plus OPL master `/Users/gaofeng/workspace/one-person-lab/docs/references/runtime-substrate/opl-stage-led-agent-framework-roadmap.zh-CN.md` | `active / gated_by_opl_master`: MAS 只做 provider-ready contract、sidecar export/dispatch receipt、forbidden-write guard、paper-line guarded soak 和 retirement evidence；Temporal provider skeleton、Codex stage activity runner、human gate signal/query、OPL App attempt visibility 和 provider cutover 属 OPL master P1-P5。真实 soak 通过前，本地 scheduler / Portal / Live Console 只降级为 diagnostics/fallback，不物理删除。 |
| `9` | `standard_domain_agent_skeleton_mapping` | OPL master plus `opl_temporal_mas_runtime_retirement_program.md` | `active / framework_alignment`: MAS 先完成 skeleton mapping，把现有 stage、prompt/skill、knowledge、quality gate、contract、sidecar、receipt schema / refs、projection builder / refs 和 artifact locator / authority refs 映射到 OPL standard skeleton；同时输出 `framework_generic` / `mas_domain_specific` lifecycle 清单。物理目录重组只在 parity、restore/provenance 和真实 paper soak 稳定后执行。 |

本文是队列 authority。实现 lane 可以并行拆分，但吸收顺序仍按上表 gate；不能绕过 portfolio 直接新建另一套 program board。

## Architecture Fitness Budget

模块化治理现在是横向 fitness budget，不是新的 active program board。当前评估与落地记录见 [MAS Modularity Assessment 2026-05-07](../references/mainline/mas_modularity_assessment_2026_05_07.md)：MAS 依赖方向已经干净，Sentrux `above_diagonal=0`，本轮 architecture fitness wave 已把 boundary fitness 清到 `0 blocking / 0 advisory`；但 `product_entry`、`study_progress`、`runtime/control`、MCP/display 这些高扇入 projection/entry/read-model 仍是维护热点。

因此，后续队列执行时统一遵守：

- 不新增机械编号 `part_*` / `chunk_*` / `split_*` 文件。
- 不新增 `exec(compile(...))` 拼接加载。
- 不让 `study-progress`、workspace cockpit、product-entry、MCP 或 OPL handoff 自行解释用户状态、runtime next action 或 publication readiness。
- OPL App 的最优集成方式固定为 App-native Runtime Workbench：消费 MAS progress/conversation/live-console/terminal projection、freshness、source refs、artifact locators、action receipts 和 terminal attach gate。它可以做 family-level dashboard、attention queue、running-recent 聚合和 MAS study drilldown，但不得生成或重算 MAS study truth、publication verdict、quality verdict、runtime owner decision 或 controller next action。
- 新增或修改中心 hub 时必须声明角色：authority 持有裁决，read-model 只投影，adapter 只验证/调用/渲染，materializer 只执行受控写入；非 authority hub 的 authority drift 是 blocking。
- 触碰 near-limit part、高 churn hub 或 nested `_parts` 时，优先按自然 owner 子域拆 importable module，并补 focused public-surface / subdomain tests。
- `scripts/verify.sh structure` 的 Sentrux `quality_signal` 不需要每次提高，但不得无解释退化；DSM `above_diagonal` 必须保持 `0`。

这条 budget 只约束 repo-tracked source/test/docs 维护，不修改 live study artifact，也不抢占下面的 `A1-A4` 主序列。

## 推进模型

后续推进采用一条主序列、多个可并行 implementation lane：

| order | portfolio gate | owner doc | 并行性 |
| --- | --- | --- | --- |
| `A0_program_portfolio_freeze` | 固定 active / support / historical 分类，停止新建重复 program board。 | 本文 | 可单独落地。 |
| `A1_authority_contract` | 固定 MAS owner matrix、SQLite runtime authority schema、MDS oracle-only 规则。 | `../policies/runtime-governance/mas_mds_owner_boundary_contract.md`、`runtime_lifecycle_sqlite_migration_program.md` | `Q0` 必须先完成，其他 lane 只能读合同。 |
| `A2_repo_capability_absorb` | 把 MDS Git-era branch/worktree/checkpoint/diff/canvas 语义迁入 SQLite lineage/materializer/projection。 | `mas_single_project_mds_absorb_program.md`、`runtime_lifecycle_sqlite_migration_program.md` | `Q1/Q2/Q3` 可按 disjoint write set 并行。 |
| `A3_workspace_cutover` | 当前 NF-PitNET、DM-CVD / DPCC、AS biologics、HeRR 等 workspace 进入 SQLite-backed runtime layout，quest `.git` 和 workspace root Git 退为 restore diagnostic archive；new workspace no root Git / no quest Git。 | `runtime_lifecycle_sqlite_migration_program.md` | current-project active-path quest Git、workspace root Git、用户可见 layout、profile template 和入口文档已进入 verified/landed 口径。 |
| `A4_entry_and_compat_retirement` | MDS product entry、默认 Git writer、Git worktree writer、隐式 Git diff/log reader 退役；root Git 不再是可选 workspace 维护模式，只允许作为外部/旧 workspace 的显式 restore diagnostic 被处理。 | `mas_single_project_mds_absorb_program.md` | `landed`: quest/root Git、MDS product-entry default path、profile/entry compat 和 no-history absorb repo-level gates 已关闭；外部 MDS 仅是显式 oracle/intake/audit 支持面。 |
| `A5_archive_cleanup` | 已落地 closeout、intake 和 activation package 移入 history/reference 或保持只读参考。 | 本文 | 只做链接保全后的文档移动，不改变 runtime。 |
| `A6_functional_monolith_completion` | 不再满足于“MAS 是唯一入口”；把仍有长期价值的 MDS runtime core、status/visualization、orchestration、diagnostic 和 learning capabilities 以 MAS-owned/no-history 方式收进同一 repo，并退役旧 MDS WebUI default path。OPL App 集成只作为 family-level projection/deep-link layer，不成为 MAS progress authority。 | `mas_single_project_mds_absorb_program.md`、`../runtime/contracts/runtime_core_convergence_and_controlled_cutover.md` | `landed`: inventory、runtime core、visual surface、OPL handoff contract、compat shrink、contributor audit guard 已收口；后续只允许 future upstream source intake review 和 optional hosted frontend packaging。 |

关键顺序是 `A1 -> A2 -> A3 -> A4 -> A6`。当前 quest Git、workspace root Git、workspace 用户可见 layout、profile/entry compatibility retirement 和 no-history physical absorb repo-level closeout 已对 repo contract / new scaffold 完成到 verified / default-retired / landed。`A6` 是新的 functional monolith completion，不是重开 Git 清理或 profile 兼容清理；如果把 SQLite 当成 paper truth，或把 legacy backend diagnostic 当成默认研究入口，会破坏 MAS publication authority。

## Active Portfolio

这些文件继续作为 `docs/program/` 的 active development-plan 面维护。

| file | portfolio role | current handling |
| --- | --- | --- |
| `README.md` / `README.zh-CN.md` | directory index | 说明 `docs/program/` 只承载 active development-plan 层。 |
| `program_portfolio_consolidation.md` | active portfolio entry | 唯一规划入口、执行队列和 closeout 归口。 |
| `opl_app_mas_runtime_workbench_program.md` | active integration/product program | 把 MAS Progress Portal / Live Console / terminal attach / conversation read model 接到 OPL App 的统一 Runtime Workbench，同时保留 MAS domain authority。 |
| `opl_temporal_mas_runtime_retirement_program.md` | active runtime-retirement program | OPL/Temporal 成为完整 family runtime 后，MAS scheduler/watchdog/legacy runtime surface 的迁移、降级和退役总计划；退役必须以 Temporal provider soak、MAS direct parity 和 sidecar receipt 证据为门槛。 |
| `ai_first_paper_autonomy_closure_program.md` | active execution program | 全自动高质量医学论文主闭环 program：AI reviewer、repair work units、analysis direction autonomy、stage knowledge/memory loop、mechanical route cleanup、manuscript rewrite、gate replay、real paper soak。 |
| `mas_single_project_mds_absorb_program.md` | active execution program | MAS 吸收 MDS、no-history import、真实 workspace layout cutover 和 MDS entry retirement 的总计划。 |
| `runtime_lifecycle_sqlite_migration_program.md` | active subprogram | runtime lifecycle SQLite authority、文件数量压降、quest Git retirement、current workspace cutover 的执行子计划。 |

## Support Docs

这些文件不是独立 program owner，继续作为 active program 的支撑材料；更新时应在对应目录维护，不再放回 `docs/program/`。

| file | support role | target owner |
| --- | --- | --- |
| `../policies/runtime-governance/mas_mds_owner_boundary_contract.md` | owner-boundary contract | owner matrix、projection/oracle/observability 越权防护，所有 bridge / adapter / projection 必须引用。 |
| `../references/mds-parity/mds_capability_parity_matrix.md` | MDS capability parity / oracle matrix | 由 `mas_single_project_mds_absorb_program.md` 引用，作为 absorb gate 的 appendix。 |
| `../references/verification/plan_completion_ledger.md` | landed evidence ledger | 记录 planned vs landed vs verified；不得把计划写成完成。 |
| `../policies/repo-ops/mainline_integration_and_cleanup.md` | operational policy | worktree absorb、cleanup、push、主线卫生纪律。 |
| `../policies/repo-ops/repository_ci_preflight.md` | operational policy | repo 验证与 preflight 纪律；叙述性 docs-only 走 documentation review。 |
| `../policies/repo-ops/merge_and_cutover_gates.md` | gate policy | repo merge gate 与 runtime cutover gate 的老入口，后续只作为 gate policy。 |
| `../policies/runtime-governance/external_runtime_dependency_gate.md` | external blocker policy | external runtime / workspace / human gate 未清除前的 blocker package。 |
| `../references/mainline/mas_single_project_quality_and_autonomy_mainline.md` | mainline narrative | 医学论文质量和长时间自治优化收口到 MAS 单项目主线的解释入口。 |
| `../references/mainline/project_repair_priority_map.md` | repair triage reference | 维护优先级参考，不作为独立 program board。 |
| `../policies/runtime-governance/manual_runtime_stabilization_checklist.md` | manual ops checklist | 外部/runtime 稳定化清单。 |
| `../references/verification/real_study_relaunch_verification.md` | real workspace verification reference | 真实 study relaunch 验证参考。 |
| `../references/med-deepscientist/` | MDS learning and upstream intake references | MDS 被吸收后仍保留的 recurring upstream learning、deconstruction、method、provenance 与 intake 支撑材料。 |

## Recurring Support Lanes

这些 lane 不是 `docs/program/` 的并行总控入口，也不是已退役事项。它们属于按触发执行的长期支持能力：入口、policy 或 protocol 留在 `docs/status.md` / `docs/references/`，每次执行后的 dated record 留在 `docs/history/program/`。

| recurring lane | active owner | dated records | handling rule |
| --- | --- | --- | --- |
| DeepScientist latest-update learning | `docs/status.md`、`../references/med-deepscientist/deepscientist_continuous_learning_policy.md`、`../references/med-deepscientist/deepscientist_latest_update_learning_protocol.md` | `../history/program/deepscientist_learning_intake_YYYY_MM_DD.md` | 用户触发“学习 DeepScientist 最新更新”时继续执行 fresh upstream audit、decision matrix、落地、验证、吸收和清理；dated intake 只是单轮快照。 |
| external agent orchestration learning | `docs/status.md`、`../history/program/external_agent_orchestration_learning_intake_2026_04_30.md` 的 `Continued Learning Saturation Protocol` | 后续同族 intake snapshot | 继续只吸收可加强 MAS 自治、handoff、observability、retry/reconciliation 与 reviewer gate 的 contract/template；外部 owner、generic persona、marketing/product lifecycle 维持 watch/reject。 |
| PaperOrchestra / adjacent writing-system learning | `docs/status.md`、`../history/program/paper_orchestra_learning_intake_2026_05_02.md` 的 `Continued Learning Saturation Protocol` | 后续同族 intake snapshot | 作为写作/评审/论文工作流相邻学习面保留；不能替代 MAS publication authority 或 medical quality gate。 |
| open auto research learning | `docs/status.md`、`../history/program/open_auto_research_learning_intake_2026_05_04.md` 的 `Continued Learning Saturation Protocol` | 后续同族 intake snapshot | 继续按 adopt/watch/reject 选择性吸收 read-model、rubric、trajectory、candidate-path 等方法；外部框架和自动论文生成器不升格为 MAS truth。 |
| research-harness learning | `docs/status.md`、`../history/program/research_harness_learning_intake_2026_05_11.md` 的 `Continued Learning Saturation Protocol` | 后续同族 intake snapshot | 继续按 clean-room adopt/watch/reject 吸收 numeric trace、claim-evidence coverage、adversarial resolution 和 source-readiness 模板；RH 代码、`pool.db`、dashboard、MCP server 和 auto-runner 不得成为 MAS 依赖、truth 或 runtime owner。 |

因此，`history/program` 里的 `*_learning_intake_YYYY_MM_DD.md` 应理解为 recurring lane 的 dated snapshot。它们不作为 active backlog 重复追踪，但对应 support lane 仍可被用户或维护者触发。

## Landed Or Historical Reference

这些文件已经完成主要吸收，或被更新的 active board 覆盖。已完成链接审计且没有 active contract 职责的文件移入 `docs/history/program/`。如果业务代码或行为测试还依赖叙述性 docs 路径，优先退役这条机器依赖，改用稳定 id 或 durable surface，再执行归档。

| file | recommended state | reason |
| --- | --- | --- |
| `../references/mainline/ai_first_research_os_architecture.md` | reference | AI-first OS 架构已进入 architecture/status/mainline 口径，保留为目标架构参考。 |
| `../history/program/ai_first_operationalization_closeout.md` | landed closeout | AI-first repo-level closeout 记录，后续只读。 |
| `../history/program/ai_first_usable_closeout_projection.md` | landed closeout | usable closeout projection 已落地，后续由 ledger 与 active surfaces 接续。 |
| `../history/program/ai_first_closeout_handoff_governance.md` | landed closeout / support | handoff governance 已落地，可作为 closeout policy 参考。 |
| `../history/program/external_agent_orchestration_learning_intake_2026_04_30.md` | dated recurring-lane snapshot | 外部 orchestration 学习快照；support lane 仍可按 saturation protocol 继续触发。 |
| `../history/program/open_auto_research_learning_intake_2026_05_04.md` | dated recurring-lane snapshot | OAR lesson 已吸收为 repo-level read model；同族 open auto research 学习仍可按触发继续执行。 |
| `../history/program/paper_orchestra_learning_intake_2026_05_02.md` | dated recurring-lane snapshot | PaperOrchestra lesson intake；相邻写作系统学习仍可作为 support lane 继续触发。 |
| `../history/program/research_harness_learning_intake_2026_05_11.md` | dated recurring-lane snapshot | research-harness lesson intake；research-domain harness 学习仍可作为 support lane 继续触发，但只能 clean-room 吸收 MAS-owned contract/template。 |
| `../history/program/deepscientist_learning_intake_2026_04_25.md` | dated recurring-lane snapshot | DeepScientist 单轮 intake 快照；长期 learning lane 仍由 policy/protocol 触发。 |
| `../history/program/deepscientist_learning_intake_2026_04_28.md` | dated recurring-lane snapshot | DeepScientist 单轮 intake 快照；长期 learning lane 仍由 policy/protocol 触发。 |
| `../history/program/deepscientist_learning_intake_2026_04_30.md` | dated recurring-lane snapshot | DeepScientist 单轮 intake 快照；长期 learning lane 仍由 policy/protocol 触发。 |
| `../history/program/deepscientist_learning_intake_2026_05_05.md` | latest dated recurring-lane snapshot | 当前最新 DeepScientist intake 记录，仍由 learning protocol 引用，但不是独立 program board。 |
| `../history/program/research_foundry_medical_mainline.md` | superseded narrative / reference | Research Foundry / Harness OS 叙述已被当前 MAS/MDS autonomy 与 single-project docs 收口；保留为历史架构脉络。 |
| `../history/program/research_foundry_medical_execution_map.md` | superseded execution map / reference | 同上，作为旧 phase ladder 入口保留。 |
| `../history/program/open_harness_os_freeze_plan.md` | historical architecture freeze | Harness OS freeze 计划不再作为当前 MAS/MDS 执行板。 |
| `../history/program/integration_harness_activation_package.md` | landed activation package | activation baseline 历史包。 |
| `../history/program/hermes_backend_activation_package.md` | landed activation package | activation baseline 历史包。 |
| `../history/program/hermes_backend_continuation_board.md` | historical continuation board | 外部 Hermes 目标 wording / seam 历史板，当前不应超过 MAS/MDS absorb 与 Runtime OS owner。 |
| `../history/program/upstream_hermes_agent_fast_cutover_board.md` | historical cutover board | upstream Hermes cutover 历史板；当前只作为 legacy provider / historical cutover 参考，不作为 MAS 默认运行 blocker。 |
| `../history/program/journal_package_builtins_upgrade_plan.md` | landed/specific implementation plan | journal package builtins 计划不再作为 portfolio board。 |
| `../history/program/mas_mds_autonomy_operating_system_program.md` | retired master board | 已被本文的 single-entry portfolio 和 execution queue 覆盖。 |
| `../history/program/mas_mds_unified_enhancement_program.md` | retired enhancement board | L1-L5 增强 backlog 已被当前 MAS absorb / runtime lifecycle 队列和对应 policy/reference surface 收口。 |
| `../runtime/projections/study_progress_projection.md` | landed projection reference | study-progress projection 已是稳定 surface 参考。 |

## Deprecated Or Merge Candidates

这些文件不建议继续新增实质计划内容；需要更新时应合并到 active docs。

| file | merge target |
| --- | --- |
| `../history/program/research_foundry_medical_mainline.md` | `../references/mainline/mas_single_project_quality_and_autonomy_mainline.md` / 本文 |
| `../history/program/research_foundry_medical_execution_map.md` | 本文 |
| `../history/program/open_harness_os_freeze_plan.md` | `../architecture.md` 或 `../references/` |
| `../history/program/hermes_backend_continuation_board.md` | `../policies/runtime-governance/external_runtime_dependency_gate.md` / `mas_single_project_mds_absorb_program.md` |
| `../history/program/hermes_backend_activation_package.md` | `../references/verification/plan_completion_ledger.md` / `docs/history/program/` |
| `../history/program/integration_harness_activation_package.md` | `../references/verification/plan_completion_ledger.md` / `docs/history/program/` |
| `../history/program/upstream_hermes_agent_fast_cutover_board.md` | `../policies/runtime-governance/external_runtime_dependency_gate.md` / `docs/history/program/` |

## Archive Rule

历史归档必须后置于链接审计，不能在当前 active planning 里直接移动文件。归档时遵守：

1. 先在本文把文件标成 `historical_reference`、`landed_closeout`、`superseded` 或 `dated_recurring_lane_snapshot`.
2. 用 `rg` 查所有 inbound links，更新到新路径或保留 stub。
3. 只移动叙述性历史材料，不移动 active contracts、ledgers、policies 或 runtime docs。
4. 代码和测试不得把 `docs/**` 当成机器 truth、policy truth、runtime truth 或 regression oracle；如需引用 program / policy / runtime 概念，使用稳定 id 或 durable surface。
5. 只允许 docs tooling 识别 `docs/` 路径、生成 docs asset 或输出人读链接；这些工具不得读取 Markdown 措辞作为行为断言。
6. 不写 pytest 固定 Markdown 措辞、标题或链接锚点；归档验收走人工 review、`git diff --check` 和必要的 link spot-check。
7. 任何文档移动都不能作为 repo capability、workspace cutover 或 runtime migration 完成证明。

## Definition Of Done

这个 portfolio 收敛完成时必须满足：

- 后续 Agent 能先读本文决定该更新落在哪个 active owner doc。
- 新的 runtime lifecycle / quest Git / MDS absorb 工作都进入同一个 `A1-A4` 主序列。
- `runtime_lifecycle_sqlite_migration_program.md` 明确作为 `mas_single_project_mds_absorb_program.md` 的 runtime persistence 子计划执行。
- current-project quest Git、workspace root Git retirement、workspace layout 去 MDS/DS 化、profile/entry compatibility retirement 和 no-history physical absorb repo-level closeout 不再作为未完成 active backlog 重复规划。
- functional monolith completion 已进入 landed 口径；后续不得把默认入口/依赖退役、MDS 功能重新组织吸收或旧 WebUI/default daemon 迁移重开成 active backlog，只保留 future upstream source intake review、explicit archive import reference 和 optional hosted frontend packaging。
- paper autonomy stability 不继承 functional monolith 的 landed 结论；它必须由真实 workspace profile inventory、supervisor reconcile、migration dry-run 和 read-only soak 证据单独关闭。
- paper progress degradation closeout 只表示 repo-level 自动推进 guard 已落地；真实论文如果仍被 human gate、publication gate、parked handoff、profile unreadable 或 source evidence 缺失阻塞，必须保留 blocker 与下一 owner，不能把 production blocker projection 写成质量、投稿或交付放行。
- AI-first paper autonomy closure 完成时，必须证明初稿 / AI reviewer / repair / gate replay / reviewer re-eval / route decision 循环在真实 paper soak 中闭合；worker live、queue 有任务或 request packet materialized 都不能单独证明论文可持续自动推进。
- 已落地 closeout、activation package 不再被当作 active backlog；dated learning intake 不再被当作 active backlog，但其 recurring support lane 仍按对应 policy/protocol 可触发。
- `../references/verification/plan_completion_ledger.md` 继续区分 repo capability landed、真实 workspace cutover completed、compatibility retirement completed、no-history absorb landed 与 recurring upstream learning support。
