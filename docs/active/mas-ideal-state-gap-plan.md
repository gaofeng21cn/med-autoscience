# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-23`

## 文档读法

- 本文是 MAS 当前唯一 single Active Truth plan：只维护当前完成进度、功能/结构差距、测试/证据差距、下一轮 `/goal` prompt 和 active/history 折回规则。
- dated 过程证据、阶段 follow-through、closeout 记录、具体 attempt / receipt id 和命令流水归档到 [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md)，不回流为 active backlog。
- MAS 的 north-star 目标态回到 [MAS 理想目标态](../references/positioning/mas_ideal_state.md)。本文不重复目标态长叙述，也不维护 OPL、MAG、RCA、MDS/DeepScientist 或 OPL App 的执行计划。
- [MAS 当前开发线路](./current-development-lines.md) 只作为内容线索引；若它与本文冲突，以本文为准，并把仍有效内容折回本文、核心 canonical docs 或对应 history/tombstone。
- 差距按目标态判断，不按当前 MAS 代码是否仍可运行判断。通用 runtime、runner、queue、session、lifecycle refs SQLite、workspace/source intake、memory/artifact transport、workbench、observability、CLI/MCP/Skill/product-entry/sidecar/status wrapper 必须进入 OPL 上收、generated surface 替换、refs-only 收薄或退役分类。
- `minimal authority` 只表示 MAS 持有医学 stage 质控、publication quality、artifact mutation authorization、publication-route memory accept/reject、source readiness、owner receipt 和 typed blocker 等领域裁决边界；它不表示 MAS 应继续维护通用运行平台。
- 过时模块、接口、测试、fixture、CLI alias、wrapper、facade 和 docs 入口不做兼容保留。MDS/DeepScientist、local scheduler、LaunchAgent、supervisor 默认面、旧 runtime_transport / lifecycle refs SQLite generic owner 读法等，一律按 OPL replacement / MAS receipt parity / no-resurrection proof 直接删除、archive 或 tombstone；测试同步改成禁止复活旧面，而不是维护旧调用路径。
- T2E reporting / display legacy alias 已按 direct retirement 执行：`kaplan_meier_grouped -> time_to_event_risk_group_summary` requirement key rewrite 和 `cumulative_incidence_grouped` payload 在 risk-group summary binding 下的 materialization fallback 都已删除；当前路径必须由 `time_to_event_direct_migration` 重新物化 canonical input，旧 payload 进入 fail-closed / typed blocker。
- submission-target `publication_profile` 输入 alias 已退役：workspace profile / study / quest / resolved target 输入必须使用 `exporter_profile`，不再把 `publication_profile` fallback 成 exporter profile；`publication_profile` 只保留为已解析 package/export profile 输出字段与 submission manifest 领域字段。
- 当前 physical-retirement lane 的 source 口径已改为：`runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、`lifecycle_refs_adapter.py`、runtime lifecycle CLI 和旧 SQLite lifecycle read model 属于已退役旧 runtime 控制面，不保留 compatibility alias、facade 或 shim。仍在 active source 中出现的 sidecar、owner-route、workbench/status、storage、artifact、memory 或 terminal 面只能输出 MAS domain authority refs、owner receipt、typed blocker、no-forbidden-write proof 或 diagnostic refs；发现 generic queue、attempt ledger、scheduler、retry/dead-letter、worker residency、runtime lifecycle owner 或 read-model owner 语义时，按复活旧控制面处理并直接清理。

## Active Owner Discovery

| 项 | 当前结论 |
| --- | --- |
| Existing active truth owner | 本文是 MAS current progress、功能/结构差距、测试/证据差距和下一轮 `/goal` prompt 的唯一 owner。 |
| Ideal-state reference | [MAS 理想目标态](../references/positioning/mas_ideal_state.md)；OPL family 级目标与通用 runtime/workbench/App owner 回 OPL 仓维护。 |
| Duplicate / competing active docs | [MAS 当前开发线路](./current-development-lines.md) 只保留内容线索引；P1/P2/P0 owner 文档只维护各自边界与 contract，不维护第二总 backlog。已完成过程语义折回 [history/program](../history/program/README.md)。 |
| Foldback rule | 关闭的差距从本文移除或改写为当前完成进度；只在防止旧语义复活时留下 compact tombstone pointer。 |

## 当前完成进度

| Area | Current status | Live evidence | Notes |
| --- | --- | --- | --- |
| MAS standard semantic pack / generated surface handoff | `done_with_evidence_tail` | `agent/`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、product-entry stage descriptor | `agent/` 是 canonical medical research semantic pack；OPL 可生成/托管 descriptors。真实 stage attempt、独立 reviewer/auditor receipt 仍是 evidence tail。 |
| Functional privatization / generic-owner boundary | `done_with_delete_gates` | `contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`、`docs/status.md` | 未分类 generic owner 回流关闭；retained runtime/workbench/lifecycle shells 只能按 refs-only adapter、diagnostic、direct handler target 或 tombstone 读取。 |
| Legacy alias / retired surface cleanup | `done_for_current_aliases` | `docs/status.md`、`contracts/runtime/legacy-active-path-tombstones.json`、focused fail-closed tests | T2E legacy display alias 和 submission-target `publication_profile` 输入 alias 已 direct-retired；旧输入 fail closed。 |
| Owner-route / dispatch currentness | `active_current_truth` | `docs/decisions.md` 2026-05-22/23 decisions、owner-route protocol contracts、sidecar export/dispatch behavior | 当前多项 DM002/DM003 修复只授权 MAS owner-route transport/currentness，不写 paper truth、publication eval、controller decision 或 package truth。 |
| Physical source morphology | `open_functional_structure_tail` | current source paths: `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、`lifecycle_refs_adapter.py`、workbench/status/owner-route handoff shells | 默认 owner 已归 OPL/Temporal，但 active domain/diagnostic callers 尚未全部清零；删除必须等 OPL parity、MAS receipt parity、focused tests、no-forbidden-write proof 和 tombstone refs。 |
| Real paper-line / workspace evidence | `open_evidence_tail` | `paper_line_guarded_apply_evidence`、`body_free_evidence_packets`、production acceptance contract | Ref packet shape 与 OPL refs-only ledger consumption 已落地；仍缺多条真实 paper-line owner receipt / stable typed blocker、artifact/memory/human-gate receipt 和 provider long-soak。 |

## 当前定位

MAS 是医学研究 domain agent，也是 OPL-compatible package。它保留 direct MAS app skill path，并可被 OPL stage-led runtime 发现、托管和投影。两条入口必须回到同一套 MAS-owned study truth、stage semantics、AI reviewer / quality gate、publication route、artifact authority、memory writeback decision、owner receipt 和 typed blocker。

OPL Framework / shared family layer 持有通用 scheduler、queue、attempt ledger、state-machine runner、provider workflow、human gate transport、memory/artifact locator、lifecycle/index、observability、repair projection、generated entry/status/workbench shell 和 App drilldown。MAS 不把这些通用能力继续写成长期私有平台。

MDS / DeepScientist 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference，不回到 MAS 默认 backend。

## 当前边界

MAS 必须持有：

- study charter、research question、claim boundary、analysis plan、source asset refs 和 study-level owner route。
- 医学 stage pack、prompt/skill、knowledge packet、quality rubric、AI reviewer / auditor record 要求和 stage closeout 义务。
- domain transition table / transition matrix、publication gate、stop-loss、human gate resume 语义和 controller route。
- publication-route memory body、accept/reject/blocker decision 和 body-free writeback receipt。
- canonical manuscript、figures/tables、submission/current package authority、artifact mutation permission 和 rebuild proof。
- owner receipt、typed blocker、safe action refs、no-forbidden-write guard 和 MAS domain projection refs。

OPL 必须持有：

- provider-backed workflow、worker residency、attempt start/query/signal、retry/dead-letter、queue 和 human gate transport。
- generic transition runner、attempt ledger、lifecycle/index、memory/artifact locator、restore/retention shell、operator projection 和 App/workbench shell。
- CLI/MCP/Skill/product-entry/sidecar/status/workbench/projection wrapper 的 generated/hosted surface，除非某个入口仍作为 MAS direct domain handler 或迁移桥明确保留。

AI-first 质量门要求 executor agent 与 reviewer/auditor agent 独立 invocation、独立 context/task record 和独立 receipt。同一 agent 的自审、同一上下文内的执行后复核、或把 executor summary 改名为 reviewer output，不能关闭 MAS quality gate。

## 当前功能/结构状态

当前功能/结构状态不再把 “runtime transport / SQLite / sidecar / workspace cockpit 还能被 direct path 使用”解释为 MAS 合理长期结构。它们的唯一当前价值是承接过渡 caller、输出 MAS owner receipt / typed blocker / refs-only diagnostic，或保留必要 tombstone / no-resurrection proof。若后续发现它们继续扩写 generic queue、attempt ledger、scheduler、session store、workbench 或 lifecycle owner 语义，应重开 physical morphology gap 并优先清理，而不是继续拆 helper。

MAS `family_stage_control_plane` 现在按 runtime-event obligation 读取 `runtime_guard_required=true` 的 stage。`trust_boundary.runtime_event_refs` 与 `stage_contract.runtime_event_refs` 必须覆盖：

- `direction_and_route_selection`：`runtime_event:domain_route_owner_route.direction_route_selected`、`runtime_event:controller_decisions.direction_route_selected`。
- `baseline_and_evidence_setup`：`runtime_event:controller_decisions.baseline_evidence_ready`、`runtime_event:evidence_ledger.baseline_evidence_ready`。
- `bounded_analysis_campaign`：`runtime_event:domain_health_diagnostic.bounded_analysis_evidence_ready`、`runtime_event:evidence_ledger.bounded_analysis_evidence_ready`。
- `manuscript_authoring`：`runtime_event:controller_decisions.manuscript_draft_reviewable`、`runtime_event:canonical_manuscript.manuscript_draft_reviewable`。
- `review_and_quality_gate`：`runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded`、`runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded`。
- `finalize_and_publication_handoff`：`runtime_event:controller_decisions.publication_handoff_ready_or_route_back_recorded`、`runtime_event:artifact_authority.publication_handoff_ready_or_route_back_recorded`。

OPL proof bundle / admission 只有在所有 runtime-guard stage 返回 `admission_status=admitted`、`blockers_count=0`、`warnings_count=0` 后，才能继续把 MAS 当前结构口径写成 `functional_structure_gap_count=0`。若 admission 未跑或返回 blocked，本节必须降级为“存在 stage admission 结构 gap”，不得只把它归入 evidence gate。

在上述 admission gate 通过的前提下，当前机器面已关闭未分类 generic owner 回流、runtime-guard stage admission 和 5 个 structural follow-through gate：`classification_gap_count=0`、`active_private_generic_residue_count=0`、`functional_structure_gap_count=0`。`functional_structure_gap_count` 由 closure evidence 计算，只有同时具备 closed 状态、非结构 gap 标记和 closure proof refs 的 gate 才计入 closed。真实 provider、paper-line、memory/artifact receipt 与 long-soak 仍是后置 evidence gate，不能被结构 closure、repo tests、descriptor ready 或 OPL admission 替代。

每个 stage 的 `stage_contract` 都必须提供 source scope、auditable cohort query、OPL queue trigger、stage/runtime monitor 和 operator dashboard freshness metric refs。该面关闭的是声明式 launch/readiness 闭环结构 gap；真实 paper-line provider launch、consumed refs、owner receipt、memory/artifact apply、human gate/resume 和 long-soak 仍归测试/证据差距。

Stage production expected receipt / monitor freshness 缺口现在通过 `stage_production_evidence_receipt_record|verify` safe action route、payload workorder 与 record preflight 表达。该能力属于 OPL App/operator evidence transport 和 refs-only ledger，不属于 MAS 私有功能面；MAS 的关闭责任是为真实 paper-line stage attempt 提供 owner receipt instance、typed blocker、no-regression evidence、memory/artifact/human gate receipt 或 long-soak refs，并把真实 refs 填入 OPL workorder。空 template、声明型占位 owner receipt ref、OPL ledger receipt ref、artifact/memory/domain truth body 都不能作为 MAS 成功证据。

`stage_owned_typed_blocker_handoff` 位于 `contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence/opl_stage_evidence_receipt_handoff`，为 MAS stage 提供 `real_paper_line_owner_receipt_or_live_monitor_freshness_pending` 语义的 MAS-owned typed blocker refs。它只关闭 OPL refs-only workorder accounting；真实 paper-line owner receipt、publication quality gate、artifact mutation receipt、memory/human-gate scaleout 和 long-soak 仍需 MAS owner chain 证据关闭。

Owner-route / dispatch 当前边界是：MAS 输出 controller authorization、domain route、publication/AI reviewer refs、owner receipt、typed blocker 与 OPL 可消费 owner-route refs；OPL runtime manager 承担 liveness、queue hydration、attempt retry、dead-letter、provider resume/relaunch 和 operator status projection。MAS focused proof 锁定“只产出 refs / receipt / blocker，不写 generic runtime queue，不调用 generic runtime chat”。真实 paper-line canary 仍需由 OPL 消费 refs 后 dispatch 回 MAS owner callable，最终留下 owner receipt、progress delta、gate replay、human gate、stop-loss 或 stable typed blocker。

`domain_dispatch_evidence_record_payload` 已进入 domain route、guarded-apply、publication aftercare、default-executor dispatch pending task 和 stage-level owner handoff。该 payload 是 body-free refs-only handoff，只允许携带 MAS-owned typed blocker refs、evidence refs、no-regression refs、`domain_id`、`task_kind`、`study_id` 或 `stage_id`、source fingerprint、`domain_source_fingerprint`、`stage_attempt_source_fingerprint` 与 `profile_name`，用于让 OPL preflight 和 `domain_dispatch_evidence_receipt_record|verify` 判断 payload 是否属于当前 target。study-level target 绑定 `study_id`；stage-level target 绑定 `stage_id`，不得伪造 `unknown-study`。payload 现在显式暴露 `opl_runtime_action_execute_payload`、dry-run / record command usage 和 `identity_binding`：`stage_id`、`domain_source_fingerprint` 与 `stage_attempt_source_fingerprint` 参与 target identity 绑定，`domain_source_fingerprint` 绑定 MAS owner-route currentness，`stage_attempt_source_fingerprint` 绑定具体 OPL provider attempt，stale / mismatched attempt 不得记录。profile 文件路径、OPL ledger receipt ref、artifact body、memory body、paper body 或 domain truth body 都不能作为成功 payload。

当前 owner-route quality control 已收敛为 `Owner-Route Attempt Protocol`：owner route 统一投影 reason registry、priority lattice、currentness contract 和 `owner_route_currentness_basis`，default-executor dispatch 与 sidecar export 消费同一 envelope，缺 registered reason 或 work-unit/truth/runtime/source fingerprint 时 fail closed。

`mas_real_paper_line_provider_canary_closeout` 与 provider-hosted guarded-apply dispatch receipt 已透出统一 `body_free_evidence_packets`，只包含 owner receipt、stable typed blocker、progress delta、AI reviewer/gate、artifact movement、human gate/resume 和 no-forbidden-write refs。guarded-apply、owner-route、aftercare 和 default-executor dispatch 的多批 owner-chain refs / stable typed blocker refs 可被 OPL refs-only external evidence ledger 记录/验证为 `typed_blocker_observed` 或 refs-only receipt，identity mismatch fail closed。当前 active plan 不保存具体 attempt、worklist 数字或命令流水；过程证据归提交历史、OPL ledger 和 [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md)。

这组 evidence 只关闭 dispatch accounting、identity/preflight 与 refs-only ledger consumption 缺口。它不执行 writer / guarded apply / reviewer refresh / runtime redrive，不生成新的 MAS owner receipt，不写 `.ds` runtime truth、`publication_eval/latest.json`、paper/package/`current_package`、memory body 或 artifact body，也不授权 writer closeout、publication-ready、artifact mutation、memory writeback、domain-ready、production-ready、App user path 或 long-soak。

`mas_real_paper_line_provider_canary_closeout` 和 `body_free_evidence_packets` 的当前角色是统一 evidence shape：progress delta、AI reviewer/gate、artifact movement、human gate/resume、stable typed blocker 和 no-forbidden-write proof 只能以 refs 进入 OPL/App/Agent Lab。真实 closeout 仍必须由 MAS owner chain 在真实 workspace 中产出 owner receipt、typed closeout、progress delta、gate replay、human gate、stop-loss、artifact/memory/lifecycle receipt 或 stable typed blocker。

2026-05-21 MAS hard-methodology callable routing 已补齐：AI reviewer / controller 可能把 HDL/unit harmonization 问题表达为 `unit_harmonized_validation_uncertainty_and_grouped_calibration`，MAS current controller authorization refs 现在将其映射为 `analysis_harmonization_owner`，并通过 `domain-owner-action-dispatch --action-types unit_harmonized_external_validation_rerun` 调用 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`。该 callable 只能产出 unit-harmonized rerun evidence 或 MAS-owned typed blocker，并把 hard-methodology route 留在 MAS 医学方法学 authority boundary；OPL 仍只提供 provider、queue、attempt、generic transition runner、projection 和 App/workbench shell。该修复不写 paper、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 submission readiness，也不把 MAS owner callable 扩张成通用 runtime/control-plane owner。

标准 pack 合同已把 MAS `pack_compiler_input` 收到 OPL scaffold 的 canonical 形状：`canonical_semantic_pack_root="agent/"`、`canonical_semantic_pack_role="declarative_medical_research_semantics_for_opl_pack_compiler"`，不再暴露旧 `canonical_repo_source_semantic_pack_root`。`required_domain_pack_paths` 必须只指向真实 agent pack 语义文件，不能通过 README 或目录存在性替代 prompts / stages / skills / quality gates / knowledge 文件。

`codex_cli_launch_packet` 位于 `contracts/stage_control_plane.json` 并投影到 product-entry stage descriptor。该 packet 暴露 prompt refs、skill/tool refs、knowledge refs、quality gate refs、expected receipt refs、forbidden authority 与 `executor_requirements=Codex CLI`，用于让 Codex CLI default executor 直接启动 stage。它只定义执行边界、证据义务和禁止写面，不把医学判断、quality verdict、publication readiness 或 source/artifact authority 写成脚本逻辑。

Structural conformance 只确认 MAS scaffold validation、`agent/` semantic pack、pack compiler input、generated surface owner、private generic-owner guard、physical morphology policy 和 active path scan 可被 OPL 接受；它不声明真实 paper-line provider apply、App 用户路径、owner-chain long soak 或 runtime transport / SQLite refs index 的物理删除已经完成。

Production acceptance surface 位于 `contracts/production_acceptance/mas-production-acceptance.json`。该 surface 把 conformance 不能声明 live/domain-ready 的尾部证据收口到 MAS-owned acceptance receipt，并明确 structural / physical conformance、production-like receipt chain 或 OPL/provider completion 都不能授权 domain ready、publication ready 或 medical ready。它不把任何具体 paper-line、artifact mutation、publication gate 或 `current_package` 写成 ready。

Lane 4A evidence scaleout 选择既有 `paper_line_guarded_apply_evidence` 作为真实 paper-line / MAS evidence surface 的 OPL 摄取入口，并把它扩展为 body-free ref packet 合同：progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume 和 stable typed blocker 都只能作为 MAS-owned refs 暴露给 OPL / Agent Lab。该 ref shape 已同步到 `contracts/production_acceptance/mas-production-acceptance.json`、`product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence` 和 Agent Lab handoff。`mas_real_paper_line_provider_canary_closeout` contract 的成功标准固定为 MAS owner chain 返回真实 owner receipt 或 stable typed blocker；provider completion、suite pass 或 work order 只能作为证据输入，不能作为 canary success 或 publication-ready。该合同不迁移 MAS study truth、quality verdict、artifact/memory body 或 artifact mutation authority。真实 closeout 仍需要 MAS owner receipt 或 stable typed blocker。

Memory/artifact/human-gate evidence scaleout 使用 `body_free_evidence_packet` helper，并接入 publication-route memory、artifact lifecycle、human gate/resume 与 provider SLO read model。packet 只能包含 `ref`、`role`、`freshness`、`owner`、`receipt_id` 和 `no_forbidden_write_proof`；accepted/rejected/blocked memory writeback、artifact mutation/restore/retention receipt、human gate resume 和 provider long-soak 都必须以 refs-only packet 进入 OPL / Agent Lab。该 shape 关闭的是可摄取证据格式，不关闭真实 writeback、artifact mutation、human gate 或 long-soak。

默认 managed runtime backend 已切到 `opl_provider_backed_stage_runtime`。`runtime_backend_default_operation_contract` 显式输出 `default_runtime_backend_is_opl_provider_owned=true`，默认自治运行口径固定为 `default_autonomous_runtime.enabled_by_default=true`、`hosted_runtime_owner=one-person-lab`、`hosted_runtime_provider=temporal`、`wakeup_retry_resume_owner=one-person-lab`、`codex_app_outer_driver_required=false`、`mas_daemon_scheduler_attempt_loop_allowed=false`，并同步到 product-entry / sidecar read model 与 runtime handoff policy。该口径现在指向 OPL 唯一 stage/runtime 控制面；已退役的 `mas_runtime_core`、turn runner、worker lease、runtime lifecycle SQLite writer 和 lifecycle refs adapter 不再作为 delegated runtime adapter、diagnostic fallback 或 retained compatibility surface 出现。

物理代码层的 handoff 投影只允许表达 OPL-owned provider/stage runtime 与 MAS domain authority refs 的交界：MAS 产出 DomainIntent、owner route refs、owner receipt、typed blocker、artifact/source/quality refs 和 no-forbidden-write proof；OPL 持有 hydrate、queue、attempt ledger、provider query、retry/dead-letter、human gate 和 operator projection。任何把 `runtime_transport/`、turn runner、worker lease、domain route scan/consume/dispatch/reconcile 或 lifecycle SQLite 写成 MAS generic runtime、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 或 workbench owner 的投影都视为旧控制面复活。

`physical_source_morphology_standardization` 已作为独立结构口径进入 active source 收口。成熟 agent/runtime 框架的共同做法是分开 agent declaration、tools / authority functions、runtime orchestration、state persistence 与 workbench/evidence gate；OPL 吸收这一分层原则，MAS 不能继续用物理源码形态暗示自己持有 generic runtime platform。外部框架分层参考只是工程经验来源，不是 MAS runtime dependency。MAS 理想源码读法应是:

- `agent/` 持有医学 stage、prompt、skill、knowledge、quality gate 和 policy。
- `contracts/` 持有 OPL pack compiler input、stage/action/memory/artifact/receipt contract、runtime handoff、evidence request 和 cleanup gate。
- `runtime/authority_functions/` 或 `src/med_autoscience/**` 中长期保留的代码只承担 medical authority function、domain handler、domain authority refs surface、native helper、diagnostic/provenance probe 或 fixture。
- generic runtime / lifecycle / worker lease 命名如果仍在 active source 中出现，必须指向已退役历史、OPL-owned runtime primitive、MAS domain authority refs、owner receipt 或 typed blocker；不能再写成 MAS-retained bridge、runtime lifecycle adapter 或 diagnostic fallback。

因此，当前 active API 不再包含旧 `domain_route_reconcile.py` 控制面；历史 `domain-route-reconcile` 名称只能作为 provenance / tombstone 或迁移输入读取。当前允许保留的 MAS surface 归位到 `owner_route_reconcile.py`、`domain_action_request_materializer.py`、`domain_owner_action_dispatch.py` 和 `domain_slo_scheduler_projection.py`：它们只能表达 DomainIntent、domain route refs、owner action request、authority dispatch receipt、owner receipt、typed blocker、domain authority refs 和 OPL runtime-manager SLO projection。developer repair/worktree 元数据不进入 owner payload；`runtime_transport`、runtime lifecycle SQLite writer、turn runner、worker lease、domain-route-reconcile 旧入口和 lifecycle refs adapter 不再作为 current executable gate、remaining delete gate 或 retained adapter 记录在当前态。

同一轮收口把 runtime lifecycle refs 从 `lifecycle_refs_adapter` 迁出到 `domain_authority_refs_index`：该索引只保存 owner receipt、domain authority locator、artifact/source/status refs、cleanup receipts 或 typed blocker refs，不承担 generic runtime lifecycle、persistence、restore/retention、terminal transport 或 read-model owner。`runtime_storage_maintenance` 继续只允许输出 refs / receipt / blocker，不得声明 generic cleanup policy、generic runtime owner 或 paper closure verdict；terminal attach/read-model 面在 MAS 当前态中只允许作为 tombstone/provenance 读取。

2026-05-19 的后续退役证明把上一轮 legacy cleanup residue 从 active classification 中移出，改为 `legacy_cleanup_tombstone_provenance` 与 `retired_legacy_residue_tombstones` 机器面：`mas_generic_workbench_shell`、`legacy_scheduler_default_aliases`、`daemonish_terminal_attach_status_as_runtime_owner`、`scheduler_legacy_residue_tombstone_provenance` 均为 `domain_ref_consumer_count=0`、`default_entry_allowed=false`、`current_role=history_tombstone_provenance_only`。这表示它们已经进入 history/tombstone 证明面，不再作为 active cleanup gate 或 MAS 私有 runtime residue 计数。

Physical cleanup 后，current product-entry / sidecar 不再暴露旧 residue audit 程序面。当前机器入口只保留 `legacy_retirement_tombstone_proof`、`functional_consumer_boundary.retired_legacy_residue_tombstones` 和 `contracts/runtime/legacy-active-path-tombstones.json`；旧 residue 不再作为 current manifest audit surface 暴露，也不再作为 product-entry / sidecar 字段被测试保护。

Runtime transport active adapter 口径已关闭：turn state、prompt/authorization、message queue、worker wrapper/isolation、residency/liveness 与 lifecycle refs SQLite 不再是 MAS active source 的当前允许形态。当前允许保留的 domain refs 面限于 domain authority index、paper work-unit outbox、storage/source/artifact/memory locator 或 diagnostic exporter；这些面只能输出 body-free refs、owner receipt、typed blocker 或 no-forbidden-write proof，不得写成 MAS generic runtime 控制面。

仍有 active domain / diagnostic caller 的 body-free refs 面必须声明为 domain authority refs 或 locator refs，而不是 active runtime adapter。`paper_work_unit_outbox_index`、`runtime_storage_maintenance`、`publication_route_memory_locator_transport_shell`、`artifact_lifecycle_storage_audit_shell` 的删除门只用于防止误删 domain refs；它们不能被用作继续保留 MAS runtime lifecycle、scheduler、worker lease、attempt ledger、terminal transport 或 read-model 控制面的理由。

2026-05-20 的 generated/default caller retirement proof 已进入 `functional_consumer_boundary`、`runtime_transport_handoff_projection` 和 legacy tombstone proof。`generated_default_caller_boundary` 与 `physical_retirement_gate_matrix` 现在列出 MAS hand-written surfaces 的允许角色：direct skill target、domain handler、receipt signer、typed blocker、AI-first validator、diagnostic 或 tombstone；任何 runtime_transport、lifecycle refs SQLite、workbench、sidecar 或 status surface 只有在 no-resurrection proof、OPL parity、MAS receipt parity、focused tests 和 tombstone refs 同时成立后才允许物理删除。

OPL legacy cleanup 只消费 MAS replacement parity refs、no-regression evidence refs、history refs 和 tombstone refs，并关闭 OPL cleanup ledger blocker。它不表示 MAS tracked runtime transport 或 SQLite refs index 已物理删除，也不表示真实 paper-line provider apply、App 发布路径或 App/workbench 用户路径已完成。

Family transition materialization 当前通过 read-only `study_state_matrix` action 暴露，并同步到 product-entry shell、CLI/Skill descriptor 和 descriptor-only MCP projection。OPL 可以通过该 action 按 `family_transition_spec_descriptor.locator_refs` 物化 MAS-owned `family_transition_spec` 与 `family_transition_matrix_cases`，再用 OPL generic `family-transition-runner` 执行 matrix。MAS 只持有医学 domain transition table / read model / owner route 语义，不持有 generic state-machine runner；该 action 不写 study truth、不执行 domain action、不授权 publication quality、artifact authority 或 submission readiness。

以下 7 项已作为功能/结构 closure gate 关闭：

1. `generated_surface_default_owner_cutover`
   OPL generated / hosted CLI、MCP、Skill、product-entry、sidecar、status、workbench 和 projection descriptor 已 ready，并以 default-owner target proof 路由到 OPL generated surface 或 MAS domain handler target。MAS hand-written shell 只能继续作为 direct domain entry、domain handler、owner receipt signer、AI-first output validator、diagnostic cleanup 或 fixture/provenance。

2. `domain_authority_refs_thinning`
   domain authority refs index、paper outbox、runtime storage maintenance、workspace/source intake、publication-route memory transport、artifact lifecycle audit 和相关 projection 已收薄为 body-free locator、receipt、blocker、authority refs 或 diagnostic exporter；terminal attach/read-model 已从 MAS 当前态物理退役。这些路径不得承担 MAS generic lifecycle / restore-retention / workbench / terminal transport owner，也不得读取 memory body 或 artifact body。
   `runtime_transport_handoff_projection` 进一步把 runtime transport 与 domain route 代码路径逐项约束为 OPL-owned generic runtime 的 domain bridge / diagnostic，不允许它们重新声明 MAS-owned queue、attempt ledger、worker residency、transition runner 或 persistence engine。

3. `legacy_cleanup_physical_retirement`
   local LaunchAgent/status/remove cleanup、workspace-local watch service wrappers、旧 alias/facade 和 legacy no-resurrection gate 已完成 physical retirement；当前机器清单把 local scheduler install path 与 workspace-local watch wrappers 归为 `legacy_cleanup_physical_retired`，只保留 tombstone/provenance refs 和 forbidden-caller proof。当前 `manager=local` direct call 必须 fail closed，不再返回可用 adapter payload。OPL cleanup dry-run / apply / verify 已能消费 MAS replacement / history / tombstone proof refs；后续任何物理删除、archive 或 tombstone 仍受 domain owner receipt、OPL parity 和 no-resurrection gate 约束。

4. `opl_app_workbench_drilldown`
   OPL App / workbench drilldown 消费 MAS route/source/quality/artifact/memory/blocker/action refs 和 operator grouping。MAS 只输出 domain projection refs，不在本仓复制通用工作台。仍需证明真实用户路径消费 OPL read model，而不是 MAS repo 复制 Portal/workbench shell。

5. `lifecycle_locator_retention_restore_ledger_reconciliation`
   lifecycle locator、retention、restore、cleanup ledger 和 workspace/runtime artifact root locator 已按 OPL primitive 与 MAS artifact/source/memory authority 对账。MAS 不持有 generic restore-retention engine，只持有 artifact authority、receipt refs 和 guarded permission；真实 workspace 中的 accepted/rejected writeback、artifact mutation、cleanup/restore/retention receipt 仍需 scaleout。

6. `family_transition_materialization_handoff`
   `study_state_matrix` 是 MAS-owned domain transition read model materializer，供 OPL 消费 spec/cases 并执行 generic matrix runner。MAS 不复制 OPL state-machine runner、queue、attempt ledger 或 route executor；matrix evaluated 只说明状态转移 spec/cases 可被 OPL runner 消费，不等于 paper-line owner receipt、publication quality、artifact mutation或 submission readiness。

7. `hard_methodology_callable_routing`
   `unit_harmonized_validation_uncertainty_and_grouped_calibration` 已被 mapped 到 `analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker`。MAS 保留的是医学方法学 owner callable、evidence materialization 和 typed blocker authority；generic runtime、runner、queue、attempt ledger 与 App route 仍归 OPL。

## 当前物理源码形态差距

这部分属于结构治理 tail，不能被 `classification_gap_count=0`、`functional_structure_gap_count=0`、OPL admission、legacy cleanup ledger、conformance passed 或 generated interface ready 吞掉。当前真相是：MAS 已经完成 owner/contract/read-model 收薄和 domain route / domain SLO projection active source 命名收口；旧 runtime 相关源码只能作为 OPL handoff refs、domain authority refs、retired provenance、direct domain handler target 或 deletion map 出现，不能再写成 retained runtime adapter。

- domain route 与 domain SLO projection active source 已完成物理命名收口；剩余历史语境只允许作为 tombstone/provenance、diagnostic ref 或医学 publication/control surface 术语存在。
- route/stage 残留边界的机器面已把旧 MAS 私有 runtime/route surface 名从 current active boundary 中退役，并收敛到 `owner_route_reconcile`、`progress_projection`、`domain_health_diagnostic`、`domain_decision_authority`、`domain_authority_refs_index` 和 `owner_route_dispatch_receipt`。`route_stage_residue_boundary.legacy_surface_names_current_active=false`、`all_residual_surfaces_physically_retired=true`；该 physical retirement 指旧 surface 名和旧 owner 读法。当前实体只能表达 domain refs / receipt / blocker / projection，不能因仍被调用就保留旧 runtime 控制面语义。
- `runtime_transport/`、turn runner、worker lease 与 `lifecycle_refs_adapter.py` 不再是 active domain / diagnostic caller 的允许形态；本 lane 中只能留下 OPL provider-backed stage runtime handoff、`domain_authority_refs_index`、owner receipt、typed blocker、guarded apply receipt 和 no-forbidden-write refs。若扫描仍发现旧 runtime 控制面调用，应直接列为 resurrection blocker，而不是重新加 retained gate。
- `product_entry_parts/workspace_cockpit/`、product-entry manifest/status 与 runtime status projection 仍承担 direct MAS path、OPL handoff 输入或 diagnostic read model；generic sidecar provider lifecycle CLI 已退役，owner-route handoff active bridge 只剩 `owner_route_handoff` 的 export/dispatch owner-route。default caller 迁移后，只保留 MAS domain handler target、receipt signer、typed blocker 和 authority refs，其余删除、archive 或 tombstone。
- `owner_route_handoff_adapter` 已迁入 `owner_route_dispatch_receipt` / owner-route handoff 语义面，删除门机器化为 `deletion_readiness_worklist`。当前 sidecar export/dispatch 只能保留为 owner-route refs adapter；删除、archive 或 tombstone 由 OPL generated sidecar default caller parity、真实 paper-line owner receipt 或 stable typed blocker parity、focused sidecar tests、no-forbidden-write proof 和 history/tombstone refs 约束。相关 sidecar export/read-model/pending-task 组装已按 parts/facade 收薄，但这只降低文件耦合，不声明 physical delete、App/workbench closeout、publication-ready 或 artifact mutation authorization。
- OPL generated/default caller readiness 已进入 `functional_consumer_boundary.generated_default_caller_boundary.opl_default_caller_readiness_evidence`：generated/hosted default-caller surface 的 structural replacement / default-owner cutover 只作为删除门输入，不授权物理删除，不声明 domain ready、production ready、publication quality、artifact mutation 或 paper-line closure。
- study-progress / workbench / domain authority refs / runtime storage 等 surfaces 已按 parts/helpers 收薄为 projection、locator、refs-only payload assembly 或 diagnostic input。当前 active plan 不保存具体文件行数和拆分 tranche；这些过程证据归提交历史、machine-readable audit 和 history/provenance。它们不能被写成 MAS runtime lifecycle/read-model owner；删除或迁出按 OPL primitive parity、MAS domain receipt parity、focused tests、no-forbidden-write proof 和 tombstone refs 执行。
- `functional_privatization_audit` / `runtime_transport_handoff_projection.physical_cleanup_gate` 当前还显式列出 `workbench_shell_domain_projection_refs`、`owner_route_dispatch_receipt`、`progress_projection` 三个 current residue cleanup gate。它们分别对应 OPL workbench domain projection refs、MAS owner-route dispatch receipt、MAS domain truth progress projection；现状均不是 MAS generic runtime owner，也不是可复制的新 Agent 模板 surface。旧 surface id 只保留为 retired legacy id 映射，不再是 current active surface id。
- developer repair / worktree / verification 元数据不得长期留在 MAS domain handler；目标是迁入 OPL Agent Lab / developer repair lane 或 explicit contract refs。

这组差距的关闭门槛是：OPL generated/provider parity、MAS domain receipt parity、focused tests、no-forbidden-write proof 和 provenance/tombstone refs 同时成立。未满足前写成 OPL-owned gap、domain authority refs 或 retired provenance；满足后直接物理删除、archive 或 tombstone，不保留 compatibility alias。

当前直接退役优先级：

| surface | 当前实际状态 | 下一步动作 |
| --- | --- | --- |
| `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease | 本 physical-retirement lane 中已按 no-alias 物理退役；不作为 MAS direct/diagnostic runtime caller 保留。 | 扫描旧 import / string / CLI alias / docs current态；发现即改到 OPL provider stage runtime、MAS owner receipt 或 typed blocker。 |
| `lifecycle_refs_adapter.py` 与 lifecycle refs SQLite parts | 本 physical-retirement lane 中已由 `domain_authority_refs_index` 取代；不保留 runtime lifecycle adapter。 | 删除旧 caller 和文案；只允许 domain authority refs / owner receipt locator，不保留 MAS generic persistence engine 或 compatibility alias。 |
| `product_entry_parts/workspace_cockpit/`、status/progress/workbench projections | direct MAS path / OPL handoff 输入仍可见。 | OPL generated product/status/workbench 成为 default caller 后，只保留 MAS truth refs；删除旧 cockpit/workbench shell 和只保护旧字段的测试。 |
| `owner_route_handoff*` | dispatch/export owner-route refs adapter，不承担 queue、attempt、retry/dead-letter 或 runtime liveness。 | OPL generated sidecar default caller parity、真实 owner receipt 或 stable typed blocker parity 成立后，保留 domain action handlers，删除旧 export/dispatch wrapper。 |
| T2E legacy reporting/display aliases | requirement key rewrite 与 legacy grouped payload fallback 已退役；当前只允许 canonical `time_to_event_risk_group_summary` input 或 fail-closed blocker。 | 不恢复 alias / normalizer；旧 workspace 通过 `time_to_event_direct_migration` 重物化 canonical input。 |
| submission-target `publication_profile` 输入 alias | profile/study/quest/resolved-target 输入不再接受 `publication_profile` 作为 exporter fallback；当前 canonical 输入为 `exporter_profile`。 | `publication_profile` 只保留在 package/export output 和 submission manifest 领域字段；旧输入 fail closed，不恢复 conflict normalizer 或兼容测试。 |
| managed / legacy / compatibility tests | 部分仍验证旧 runtime/managed/legacy 行为。 | 改为 no-resurrection、fail-closed、current contract 或 tombstone tests；删除只维护旧调用路径的兼容测试。 |

## 当前测试/证据差距

MAS production acceptance receipt 已把 conformance 不能声明 live/domain-ready 的尾部证据收口到 MAS-owned contract。以下是后续真实 paper-line / workspace scaleout 验证范围，不能替代真实 paper closure、publication-ready 或 artifact mutation authorization，也不再作为结构标准化缺口计数：

- 真实 paper-line provider apply：OPL provider -> MAS sidecar -> MAS owner chain 在真实论文线上留下 attempt query、typed closeout、MAS owner receipt，并通过 Lane 4A ref packet 暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume、stop-loss 或 stable typed blocker。当前已固定可摄取 ref shape，并已证明多批 guarded-apply payload 可被 OPL refs-only ledger 消费；剩余缺口仍是多条真实 paper line 的持续 owner receipt / stable typed blocker、artifact/memory/human-gate receipt 和 long-soak closeout。
- domain dispatch owner-chain ledger scaleout：MAS pending task 和 stage-level owner handoff 现在能提供 OPL 可记录的 `domain_dispatch_evidence_record_payload`，可把缺 owner-chain evidence 的 workorder 关闭为 MAS-owned typed blocker 或 refs-only receipt；当前已证明 reviewer-refresh、default-executor dispatch、domain-route 与 stage-level typed blocker payload 可被 OPL identity preflight 与 refs-only ledger 消费，也能 fail-closed 阻断错绑 payload。payload 还携带可直接提交给 `opl runtime action execute` 的 refs-only body、preflight/identity-binding 使用要求和 stale-attempt policy，降低 operator route-back 到错误 OPL target 的风险。这仍是 ledger/evidence scaleout，不替代真实 paper-line owner receipt、typed closeout、writer direct-fix / closeout、runtime redrive、reviewer refresh 执行、artifact/memory/human-gate receipt 或 long-soak。
- owner-chain refs packet 物化：`paper_line_provider_canary_closeout` 和 provider-hosted guarded-apply receipt 现在能输出标准 `body_free_evidence_packets`，但 packet 只承载既有 MAS owner refs；真实关闭仍需要 paper-line canary 反复产出 owner receipt、stable blocker、artifact/memory/human-gate receipt、monitor freshness 和 no-forbidden-write proof。
- publication-route memory receipt scaleout：更多真实 paper line 产生 accepted/rejected/blocked writeback receipts，并可被后续 stage 小集合检索。
- artifact lifecycle receipt scaleout：真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded apply receipt 和 rebuild/freshness proof。
- human gate / resume：approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。
- provider SLO long soak：长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。
- owner-route / OPL runtime handoff：stopped / waiting / paused / live 等状态与 controller authorization、domain transition、submission metadata handoff、AI reviewer routeback 的组合路径必须由 MAS focused tests 锁定为 refs-only handoff；MAS 不写 generic runtime queue、不做 provider redrive、不把 OPL attempt 状态当 MAS truth。真实 paper-line canary 仍需证明 OPL 消费 MAS owner-route refs 后 dispatch 回 MAS owner chain，并产出 owner receipt、progress delta、gate replay、human gate、stop-loss 或 stable typed blocker。
- family transition materialization：`study_state_matrix` action 与 OPL generic matrix runner 已有 focused proof；真实关闭仍需要 paper-line canary 证明 matrix route/work-unit 进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。

## 一步到位 physical/source morphology closure 路线

后续不再按“先证据、再删一点、再改一层”的阶段漂移推进，而是按以下并行 lane 同时收敛。每条 lane 都只在自己的 gate 成立后关闭；证据 tail 不能替代结构迁移，descriptor ready 也不能替代 production/default caller cutover。

| lane | 关闭对象 | 功能/结构闭合门槛 | 测试/证据 tail |
| --- | --- | --- | --- |
| `codex_pack_canonicalization` | `agent/` Codex pack、stage prompt、tools/knowledge refs、quality gate refs 与 pack compiler input | `agent/` 是唯一 canonical medical research semantic pack；`contracts/pack_compiler_input.json` 和 stage control plane 只引用真实 pack 文件；每个 stage 已投影 `codex_cli_launch_packet`、expected receipt refs、forbidden authority 与 `executor_requirements=Codex CLI`；`src/` 只保留 domain handler、authority function、native helper、fixture 或 domain authority refs surface | `opl agents scaffold --validate <repo> --json` 绿色；真实 stage attempt 消费 launch packet；独立 reviewer/auditor receipt 证明 AI-first quality gate 未被程序 verdict 替代 |
| `opl_generated_default_caller_cutover` | OPL-generated CLI/MCP/Skill/product-entry/status/workbench shell 与 MAS hand-written shell 的默认 caller 边界 | OPL generated / hosted surface 成为 hosted/default caller；MAS hand-written shell 只保留 direct domain entry、domain handler target、owner receipt signer、AI-first validator、typed blocker 或 diagnostic；旧 wrapper/alias/facade 无 default caller | direct MAS path 与 OPL-hosted path receipt equivalence；no-forbidden-write proof；App/workbench 真实用户路径消费 OPL read model |
| `runtime_transport_sqlite_physical_retirement` | `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、`lifecycle_refs_adapter.py` 和 lifecycle refs SQLite writer | `DEFAULT_MANAGED_RUNTIME_BACKEND_ID=opl_provider_backed_stage_runtime` 已关闭默认 backend owner gap；repo-local `runtime domain-health-diagnostic --loop` 长循环 shell已物理退役，`watch-runtime` 只保留 one-shot domain diagnostic tick；旧 runtime transport、worker lease 和 lifecycle refs adapter 在本 lane 中按 no-alias 退役；剩余 active path 只能是 OPL provider stage runtime、MAS domain authority refs、owner receipt、typed blocker、artifact/source/quality refs 或 no-forbidden-write proof | 至少一条真实 paper-line canary 给出 MAS owner receipt、artifact delta、gate replay、route decision、stop-loss 或 stable typed blocker；restart/re-query、retry/dead-letter 与 no-forbidden-write 证明持续成立 |
| `workbench_sidecar_status_retirement` | `product_entry_parts/workspace_cockpit/`、product-entry status、runtime status projection、`owner_route_handoff` 和旧 product/workbench wrapper | generated/default caller retirement proof 已列出允许角色；OPL generated product/status/workbench shell 成为 production/default caller后，MAS 只输出 domain projection refs、receipt signer、typed blocker、authority refs 和 direct skill target；generic sidecar provider lifecycle CLI 已退役，legacy cockpit/workbench shell 无 active caller | App/workbench drilldown 能展示 provider refs、stage review refs、memory refs、artifact refs、safe action receipt refs 和 typed blockers；真实用户路径与发布/截图证据补齐 |
| `real_paper_line_canary` | 从 proof/conformance 进入真实论文线 owner-chain | `mas_real_paper_line_provider_canary_closeout` contract 已落地；选取一条真实 paper line，从 OPL provider attempt 进入 MAS sidecar dispatch，再由 MAS owner surface 产出 owner receipt 或 stable typed blocker；Lane 4A ref packet 只暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume、stop-loss 或 typed blocker refs；整个链路不写 OPL 不该写的 truth/body/package；这些 refs 以标准 `body_free_evidence_packets` 供 OPL/App/Agent Lab 摄取 | `contracts/agent_lab_handoff.json` 已声明通用 `agent_production_evidence_suite` 的 MAS 实例，其中包含 real-paper-line task；`paper_line_guarded_apply_evidence` 已作为 OPL-ingestable refs surface 固化；当前已落地 canary harness / closeout contract / body-free packet 物化，但 live real paper-line owner receipt 或 stable typed blocker 的持续 scaleout 仍待产生；canary 结果只能证明该链路可运行，不能直接写成 publication-ready、medical-ready 或 `current_package` authority |
| `family_transition_route_canary` | `study_state_matrix` / domain transition table 到 OPL generic matrix runner 的真实 owner-chain落地 | MAS 只提供 read-only transition table / spec / cases；OPL 负责 runner、attempt、queue、retry/dead-letter 和 projection；domain route、quality verdict、artifact authority 和 owner receipt 仍由 MAS 授权 | 已有 focused proof 覆盖 action catalog / product-entry / CLI / Skill / descriptor-only MCP projection 与 OPL materialization；仍缺真实 paper-line owner-chain receipt 或 stable typed blocker，不能把 matrix pass 写成 paper ready |
| `memory_artifact_human_gate_long_soak` | production evidence tail | publication-route memory、artifact lifecycle、human gate/resume、expected receipt instance、monitor freshness 和 provider SLO 都以 MAS owner receipt / typed blocker 作为唯一关闭证据；OPL 只持 refs、transport、projection、payload workorder/preflight 和 stage evidence receipt ledger；body-free evidence packet shape 已落地 | `contracts/agent_lab_handoff.json` 已声明 memory/artifact/human gate scaleout 和 provider SLO long-soak tasks；Agent Lab result、`opl-meta-agent` work order 与 OPL stage evidence receipt 只是证据/候选或 refs-only roundtrip，关闭仍需要真实 memory receipt、artifact authority receipt、human gate/resume receipt、provider SLO receipt、MAS owner receipt 或 typed blocker |

## 并行落地顺序

1. 并行启动 `codex_pack_canonicalization`、`opl_generated_default_caller_cutover` 和 `runtime_transport_sqlite_physical_retirement` 的 parity / stale-surface 盘点。前两条优先关闭默认 caller 和 semantic pack 边界，第三条只做 no-resurrection / deletion map，不在 evidence 不足时恢复 active adapter。
2. 同步推进 `workbench_sidecar_status_retirement`，把 production/default caller 迁到 OPL generated product/status/workbench shell；MAS 侧保留 direct skill target、domain handler、receipt signer、typed blocker 和 diagnostic。
3. 用 `real_paper_line_canary` 验证 OPL attempt -> MAS sidecar -> MAS owner chain。canary 必须返回 owner receipt、progress delta、gate replay、route decision、human gate、stop-loss 或 stable typed blocker，不能只返回 provider completion。
4. canary 通过或稳定 typed-block 后，再扩展 `memory_artifact_human_gate_long_soak`。这一步只关闭测试/证据 tail，不回写成结构 closure，也不替 AI reviewer / publication gate / artifact authority 宣布 ready。
5. 每个物理删除动作都必须带 replacement parity、domain receipt parity、focused tests、no-forbidden-write proof 和 provenance/tombstone refs；满足即删除、archive 或 tombstone，不新增兼容 alias。删除旧面时同步删除或改写只保护旧路径的兼容测试，当前测试只锁定 machine-readable contract、CLI/API 行为、generated manifest、owner receipt、typed blocker、fail-closed 或 tombstone semantics。

## 下一轮 Agent Prompt

可直接作为 `/goal` 使用：

```text
使用 MAS / OPL Doc Governance，继续治理 /Users/gaofeng/workspace/med-autoscience 的 Active Truth 与目标态收敛。写入范围仅限 med-autoscience；先读 AGENTS.md、TASTE.md、README*、docs/README.md、docs/project.md、docs/status.md、docs/architecture.md、docs/invariants.md、docs/decisions.md、docs/active/mas-ideal-state-gap-plan.md、docs/active/current-development-lines.md，并按 live contracts/source/tests/CLI/read-model 核实当前事实。

目标：围绕 single Active Truth plan 推进一轮最小可验证收口，优先处理 `runtime_transport_sqlite_physical_retirement` 与 `workbench_sidecar_status_retirement` 的 active caller / parity / tombstone 删除门。不要把真实 evidence tail 误写成功能未落地，也不要把 conformance、descriptor ready、provider completion 或 refs-only ledger 记录写成 publication-ready、domain-ready、artifact mutation authorization 或 paper closure。

必须执行：1. 读取 `contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`、`contracts/stage_control_plane.json`、product-entry manifest、sidecar export/read-model 和相关 tests，确认 retained adapter / diagnostic / direct handler target 的 active caller。2. 对已满足 no-active-caller、OPL parity、MAS receipt parity、focused tests、no-forbidden-write proof 和 tombstone/provenance refs 的旧 wrapper、alias、facade、compat test 或文档入口直接删除、archive 或 tombstone；未满足的只更新删除门，不新增兼容面。3. 把关闭项折回本文件的当前完成进度；把过程证据折回 docs/history/program 或对应 history/tombstone；保持 `docs/active/current-development-lines.md` 只是内容线索引。

非目标：不修改 OPL/MAG/RCA/MDS 仓；不写真实 study workspace artifact、paper body、publication_eval/latest.json、controller_decisions/latest.json、current_package、memory body 或 artifact body；不恢复 MDS/DeepScientist、Hermes/local scheduler、old runtime_transport、publication_profile 输入 alias、T2E legacy display alias 或任何 compatibility shim。

验证命令：至少运行 `python3 /Users/gaofeng/workspace/opl-doc-governance/scripts/opl_doc_doctor.py doctor . --format json`、`git diff --check` 和 `scripts/verify.sh`。若修改 machine-readable contract、action metadata、schema 或 runtime semantics，追加 `make test-meta`；若只是 docs-only，仍运行 repo native 最小验证并说明其结果。

完成门槛：main checkout 干净或只包含本轮目标变更；closed gaps 已从本文件移除或改写为当前完成进度；功能/结构差距与测试/证据差距仍分开；active docs 没有 dated closeout/process diary；历史材料只在 history/tombstone 中保留；最终提交到当前 main。
```

## History / Tombstone Foldback

| 内容 | Foldback target | 当前规则 |
| --- | --- | --- |
| dated closeout、attempt / receipt id、命令流水、旧 phase checklist | `docs/history/program/` 或对应 `docs/history/<area>/` | 只保留 provenance；不得作为 current truth 或 active backlog。 |
| 已被 current owner surface 替代的旧 runtime/workbench/scheduler/alias 文案 | `docs/history/**` tombstone / provenance，或 machine-readable tombstone refs | active docs 只写当前 owner、删除门和 no-resurrection guard。 |
| 已关闭功能/结构 gap | 本文 `当前完成进度`，必要时加 compact tombstone pointer | 不保留旧 checklist chronology。 |
| 仍缺 live evidence 的能力 | 本文 `当前测试/证据差距` | 不回写成结构未完成，也不写成 production/domain ready。 |

## 当前不能写成

- 不能写成 OPL provider proof 等于 MAS paper closure、publication-ready 或 artifact mutation authorization。
- 不能写成 MAS production acceptance receipt 等于具体论文线 publication-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能写成 `mas_owner_receipt_present` / stable blocker 等于 workspace mutation、artifact authority 放行或 paper closure。
- 不能写成 MAS 已经没有任何私有程序面；准确口径是私有面已收敛为声明式 pack / generated surface handoff、domain authority refs、minimal authority function 或 no-resurrection cleanup tombstone/provenance gate。
- 不能把旧 `runtime_transport/`、turn runner、worker lease、runtime lifecycle SQLite 或 `lifecycle_refs_adapter.py` 重新写成 active adapter、diagnostic fallback、compat alias 或 active caller gate；准确口径是旧 private runtime 控制面已进入 no-alias physical retirement，当前 owner-route/receipt/ref-index 实体只能作为 OPL handoff 输入、MAS domain authority refs、owner receipt 或 typed blocker。
- 不能把 `workbench_shell_domain_projection_refs`、`owner_route_dispatch_receipt` 或 `progress_projection` 写成可长期私有化；准确口径是它们已有 active cleanup gate、forbidden owner flags 和删除门，当前只允许作为 domain projection / dispatch receipt / truth progress refs。
- 不能把 `domain_authority_refs_retirement_gates` 写成继续保留 MAS generic runtime；这些 gate 只证明 domain authority refs / diagnostic refs 边界和明确删除门。
- 不能把 `legacy_cleanup_tombstone_provenance` 写成 active cleanup residue；它只保留 no-resurrection proof、history/tombstone refs 和 forbidden output 边界。
- 不能把 `delegated_domain_adapter_id=mas_runtime_core` 或显式 diagnostic `runtime_backend_id=mas_runtime_core` 读成 MAS generic runtime owner；当前 machine contract 已明确默认 `runtime_backend_id=opl_provider_backed_stage_runtime`、`default_runtime_backend_is_opl_provider_owned=true`、`runtime_owner=one-person-lab`、`runtime_substrate=opl_provider_backed_stage_runtime`、`domain_runtime_adapter_role=mas_domain_owner_receipt_adapter`、`runtime_backend_is_generic_owner=false`，且 `default_autonomous_runtime` 明确 hosted autonomy 默认启用、Codex App 不承担外围持续 driver、MAS daemon/scheduler/attempt loop 禁止。
- 不能把 MAS legacy cleanup dry-run / apply / verify ready 写成物理源码已清零；它只证明 OPL cleanup gate 和 refs-only ledger 可消费 MAS replacement / no-regression / history / tombstone refs。
- 不能把 OPL `stage_production_evidence_receipt_record|verify` 写成 MAS production ready；它只证明 expected receipt / monitor freshness 的 refs-only record/verify route、payload workorder 和 preflight 可用，真实关闭仍需要 MAS owner receipt instance、typed blocker、memory/artifact/human gate 或 long-soak evidence。
- 不能把 `study_state_matrix` 或 OPL `family-transition-runner` matrix pass 写成 MAS paper closure、publication quality、artifact authority、submission readiness 或 domain ready；它只证明状态转移 spec/cases 的 read-only materialization 和 generic runner consumption。
- 不能把 generated surface cutover、domain authority refs 收薄、legacy physical retirement、OPL App/workbench drilldown 或 lifecycle ledger 对账的结构 closure 写成真实 paper closure、publication-ready、artifact mutation authorization 或 provider long-soak 已完成。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可以由 repo tests 替代的事项。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出，程序只做校验、持久化、签收和防越权。
- 不能把 `judgment_mode=mechanical_guard` 的 helper、owner receipt signer、schema validator、currentness checker 或 domain authority refs surface 写成医学 verdict owner；这些面只能签收、校验、投影或阻断，不能生成 quality/source/memory/artifact ready/pass。
- 不能把 executor agent 的自审、同一上下文内的“执行后复核”、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 MDS/DeepScientist、Hermes、local scheduler 或旧 workspace wrapper 写成 MAS 默认 active runtime owner。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
