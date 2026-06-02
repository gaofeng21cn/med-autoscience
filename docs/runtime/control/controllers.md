# Controllers

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime control surfaces and controller responsibilities for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable runtime control support only; runtime control truth remains in controller source, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

这个目录用于说明 `MedAutoScience` 中的 runtime control surfaces、controller responsibility 和 owner boundary。

这些 controller 默认首先服务于 Agent 调用面，而不是人手工操作面。

也就是说：

- controller 是 MAS domain handler / authority refs / diagnostic refs 的稳定入口之一，不是 MAS 长期 generic runtime owner。
- CLI 只是当前 direct path 的薄包装；OPL generated/default caller 接管后，repo-local CLI/MCP/product-entry/sidecar wrapper 只能继续作为 domain target、authority function 或诊断入口，否则按 no-active-caller proof 删除。
- 人类主要审核 controller 产出的 report、summary、delivery、owner receipt、typed blocker 和审计日志。

当前 controller / authority-function surface 包括：

1. publishability gate
2. medical publication surface
3. submission minimal exporter
4. domain health diagnostic controller
5. study delivery sync
6. data assets controller
7. backend audit
8. managed study runtime orchestration
9. runtime storage maintenance
10. MAS domain-handler family bridge export/dispatch
11. delivery inspection / inspection package contract
12. clean paper-authority migration and re-materialization owner routing
13. Agent Lab medical manuscript quality refs-only suite projection
14. publication aftercare / ARIS analysis queue / AI reviewer refresh refs-only progression control

对应的 Python 实现在包内：

- `src/med_autoscience/controllers/publication_gate.py`
- `src/med_autoscience/controllers/medical_publication_surface.py`
- `src/med_autoscience/controllers/submission_minimal.py`
- `src/med_autoscience/controllers/domain_health_diagnostic.py`
- `src/med_autoscience/controllers/study_delivery_sync.py`
- `src/med_autoscience/controllers/data_assets.py`
- `src/med_autoscience/controllers/data_asset_updates.py`
- `src/med_autoscience/controllers/backend_audit.py`
- `src/med_autoscience/controllers/domain_status_projection.py`
- `src/med_autoscience/controllers/progress_projection.py`
- `src/med_autoscience/controllers/progress_projection_parts/`
- `src/med_autoscience/controllers/study_runtime_types.py`
- `src/med_autoscience/controllers/study_runtime_decision.py`
- `src/med_autoscience/controllers/study_runtime_decision_parts/`
- `src/med_autoscience/controllers/study_runtime_startup.py`
- `src/med_autoscience/controllers/study_runtime_completion.py`
- `src/med_autoscience/controllers/study_runtime_resolution.py`
- `src/med_autoscience/controllers/study_runtime_execution_parts/`
- `src/med_autoscience/controllers/runtime_storage_maintenance.py`
- `src/med_autoscience/controllers/owner_route_handoff.py`
- `src/med_autoscience/controllers/delivery_inspector.py`
- `src/med_autoscience/controllers/submission_inspection_export.py`
- `src/med_autoscience/controllers/paper_authority_migration.py`
- `src/med_autoscience/controllers/paper_authority_delivery_guard.py`
- `src/med_autoscience/controllers/owner_route_reconcile_parts/action_projection.py`
- `src/med_autoscience/controllers/agent_lab_medical_manuscript_quality.py`
- `src/med_autoscience/controllers/publication_aftercare.py`

对应测试：

- `tests/test_publication_gate.py`
- `tests/test_medical_publication_surface.py`
- `tests/test_submission_minimal.py`
- `tests/test_domain_health_diagnostic.py`
- `tests/test_study_delivery_sync.py`
- `tests/test_data_assets.py`
- `tests/test_data_asset_updates.py`
- upgrade-check 的专用测试模块
- `tests/test_study_runtime_router.py`
- `tests/test_study_runtime_router_topology.py`
- `tests/test_study_runtime_typed_surface.py`
- `tests/test_progress_projection_evidence_adoption.py`
- `tests/test_study_runtime_execution_control_intent_cases/`
- `tests/test_study_runtime_execution_evidence_adoption_cases/`
- `tests/test_runtime_storage_maintenance.py`
- `tests/test_cli_cases/owner_route_handoff_command.py`
- `tests/test_delivery_inspector.py`
- `tests/test_delivery_visibility.py`
- `tests/test_inspection_package_contract.py`
- `tests/test_ai_reviewer_publication_eval_workflow.py`
- `tests/owner_route_reconcile_cases/test_paper_authority_cutover.py`
- `tests/test_domain_owner_action_dispatch_cases/clean_migration_rematerialization.py`
- `tests/test_paper_authority_migration.py`
- `tests/test_agent_lab_medical_manuscript_quality.py`
- `tests/test_publication_aftercare.py`

当前源码形态是：

- functional / structural gates 已按 standard OPL Agent source shape 关闭，controller 代码按 domain handler target、authority function、owner receipt / typed blocker producer 或 refs-only projection input 读取。
- `study_runtime_execution.py`、`study_runtime_transport.py` 和旧 router transport helper 只能作为 retired provenance / migration input / tombstone 语境出现；当前测试约束它们不得重新变成 importable MAS 私有 runtime 控制面。
- former wrapper / private runtime surface 的物理删除只在 replacement parity、MAS owner receipt 或 stable typed blocker、no-active-caller proof、focused tests 与 tombstone/provenance proof 同时成立时执行，不把未授权删除门写回 active functional / structural gap。

对于数据资产层，当前已经区分两类 controller 能力：

- `data_assets`
  - 负责 layout 初始化、状态汇总、public registry 校验、impact 评估、private release diff
- `data_asset_updates`
  - 负责统一的 Agent mutation 入口、mutation log 写入，以及 mutation 后的 refresh 汇总

对于 `MedDeepScientist` / MDS 相关能力，当前 controller 采取的是“先审计、后吸收或归档”的策略：

- `backend_audit`
  - 不直接执行升级或把外部 MDS 恢复成默认 runtime
  - 统一检查 repo 配置、Git 状态、workspace contract、医学 overlay 状态和 legacy provenance/audit surface
  - 输出机器可读 decision，供 Agent 判断是否进入 explicit archive import、backend audit、parity check、upstream intake 或 MAS-side capability absorption

对于 managed study runtime，当前 controller 已明确分成当前 projection / typed surface / authority helper 三组：

- `domain_status_projection.progress_projection(...)`
  - 当前 diagnostic/status projection 入口，读取 MAS domain refs 并返回 status payload；不 re-export 私有 runtime control-plane binding。
- `progress_projection.py`、`progress_projection_parts/` 与 `study_runtime_types.py`
  - 负责 `ProgressProjectionStatus`、decision/reason/status enum 和 runtime result wrapper 等 typed surface；`study_runtime_types.py` 只是 lazy import shim，不是 router re-export 合同。
- `study_runtime_decision.py`、`study_runtime_startup.py`、`study_runtime_completion.py`、`study_runtime_resolution.py` 与 `study_runtime_execution_parts/`
  - 负责 status decision、startup projection、completion sync、study/root resolution、controller authorization、owner handoff、control-intent lifecycle 和 work-unit evidence adoption。

对应稳定技术说明见：

- `docs/runtime/control/study_runtime_orchestration.md`

## Progress-First current contract

Progress-First 当前合同采用 closeout-first 口径：每个非终局 controller / owner-route / domain-handler attempt 必须先形成可消费的 typed closeout refs，再由 MAS owner surface 判断它是论文进度、单一下一个 owner blocker、human gate、stop-loss，还是 stable typed blocker。typed blocker 必须保留 blocker lineage，包括 current owner、work unit、source/runtime/truth currentness refs、forbidden-write proof 或 no-progress reason；它可以关闭本轮不可执行状态，但不能被写成 paper ready、publication ready、submission ready 或 artifact/package authority。

currentness resolver、owner-route read-model、`study_progress` / `progress_projection` 只能消费 MAS owner surface：controller decision、owner receipt、AI reviewer / publication eval currentness、repair / gate / delivery controller evidence、typed closeout refs、stable typed blocker refs、human gate refs 和 OPL provider refs 的 MAS-owned projection。OPL provider completion、queue 状态、retry/dead-letter、platform liveness 修复、manifest refresh、read-model refresh 或 currentness resolver 修复只属于 transport / platform repair evidence；除非同一 MAS owner chain 还产出 canonical paper / evidence / review / gate follow-through delta 或 stable owner blocker，否则不得记为论文推进。

Progress-First paper-facing delta 必须携带 durable refs。`gate_clearing_batch` 和 runtime turn closeout 这类 controller/owner surface 只要报告了 paper-facing artifact delta，就必须把对应 paper refs 透传进 `progress_freshness.meaningful_artifact_delta_freshness.changed_refs`，供 `paper_progress_state.paper_facing_progress_slo` 判定 delta class。`status=fresh` 且带有 paper-facing `changed_refs` / `evidence_refs` 的 delta 本身就是用户可见论文进展证据；read-model 不得因为缺少额外 `latest_progress_at` 而让 `user_visible_projection.meaningful_artifact_delta=false`。read-model 不扫描 paper 文件 mtime，也不从 provider heartbeat 推断论文进展；但当 OPL live provider attempt 与 fresh paper refs 同时存在时，即使 publication supervisor 仍处于 downstream-only bundle 阶段，前台也应先显示当前 stage 正在推进，再把 gate / reviewer follow-through 作为下一 owner。

当 publication / manuscript 质量问题被识别为 route-back 时，`study_progress` 与 `paper_progress_state` 必须投影 `publication_route_back_checklist`。该 checklist 至少包含 blockers、route_target、owner、next_work_units、evidence_refs、expected_repair_result，以及最近 terminal stage log 的 `progress_delta_classification`、`deliverable_progress_delta`、`paper_progress_delta`、`platform_repair_delta`、changed paper/stage surfaces。OPL/App/agent consumer 应消费这个结构化 surface 来决定下一 owner work unit；不得从旧 AI reviewer 文案、stale queue 状态或 provider closeout summary 猜测 route-back。

publication-gate replay 的 owner 身份由 registered work-unit family 决定，而不是由 AI reviewer `route_target` 文案决定。`publication_gate_replay`、`owner_authorized_publication_gate_replay` 与 `dpcc_publication_gate_replay_after_current_ai_reviewer_record` 都必须走 `gate_clearing_batch/run_gate_clearing_batch`，并且 authority-route gate 要按同一 family 授权 submission/package/delivery follow-through。Progress-First tick 中，重复 reviewer receipt、重复 read-model reconcile、或把该 family 错派给 writer 都不是有效推进；正确结果只能是 gate-clearing batch 执行、后续 writer/package owner work unit、human gate 或 stable typed blocker。

`paper_progress_state.stage_closeout_progress` 是 read-model 对最近 terminal closeout 的分账投影。`runtime_closeout_only=true` 或 `progress_delta_classification=platform_repair` 只说明 controller/read-model/currentness/OPL provider 层完成了运行态 closeout；除非同一 surface 同时有 deliverable/paper delta、changed paper refs 或 stable typed blocker，它不能被记为 paper-facing manuscript progress。

Research evidence pack 的 paper-line evidence tail 必须在 read-model 层投影为 body-free `evidence_tail_closure_summary`。该 summary 只记录 real paper-line provider apply、publication-route memory writeback、artifact lifecycle、human gate/resume 和 family transition live receipt 的 refs 状态、stable typed blocker 关闭状态、not-triggered 状态与 evidence gap 计数；它可以帮助 operator 判断 owner-chain tail 是否还缺 refs，但不得作为 route authority、domain-ready、publication-ready、artifact mutation、memory accept/reject 或 `current_package` authority。

MAS domain-handler bridge 是 `OPL` provider-backed family runtime 进入 MAS owner surface 的受控入口，不是新的 controller truth owner。`domain-handler export` 只把 MAS-owned domain/status/source refs、owner receipt refs 和 typed blocker refs 投影给 typed family queue；`domain-handler dispatch` 只接受 allowlisted task，回到 MAS controller/domain authority owner chain 产出 dispatch receipt、owner receipt 或 typed blocker。OPL provider 承载 stage attempt、queue/wakeup、retry/dead-letter、human-gate signal、attempt receipt 和 projection，但不得写 study truth、publication quality verdict、artifact gate、paper package、`progress_projection` 或 `domain_health_diagnostic`。这条边界的机器合同由 `contracts/test-lane-manifest.json` 的 `focused_lanes.mas-entry-boundary` 持有；本文件只做人读导航。

`owner-route-reconcile` 读取 OPL provider liveness 时采用 queue-first、attempt-ledger fallback 的只读 projection：先消费 `family-runtime queue list/inspect` 中的 current-control-state；若 queue list 对当前 study 没有可用 live projection，再读取 `family-runtime attempt list/inspect` 中同 workspace、同 study、同 `domain_owner/default-executor-dispatch` 的 running stage attempt。fallback 只用于避免 stale queue projection 把 live OPL attempt 误报为 `opl_stage_attempt_admission_required`；它不写 OPL/MAS truth，不关闭 owner receipt，不宣布 AI reviewer 或 publication gate ready。

`progress_projection` 必须把 fresh OPL live provider attempt 当作执行权 dominance evidence，即使 quest-local `.ds/runtime_state.json` 仍残留 `waiting_for_user`、空 `active_run_id` 或旧 turn closeout continuation。此时 read-model 应输出 `runtime_liveness_audit.source=opl_current_control_state_provider_attempt`、`execution_owner_guard.supervisor_only=true` 和 OPL active run ref；该 projection 只约束前台 supervisor-only，不授权跳过 MAS controller decision、owner receipt、AI reviewer 或 publication gate。

`active_run_id` 不是执行权 dominance evidence。只有 `running_provider_attempt=true` 的 OPL current-control / runtime liveness projection 才能让 domain transition 进入 `active_domain_health_diagnostic` 或 live delivered-package shortcut；当 read-model 明确 `running_provider_attempt=false` 时，旧 `active_run_id` 只能作为 observability lineage 保留，不能抢占当前 AI reviewer、write、gate-clearing、package follow-through、human gate 或 typed blocker。Progress-First operator 面可以继续显示该 run id，但下一步 owner action 必须按 current MAS owner truth 推进。

所有非终局 controller / domain-handler / owner-route 路径必须按 `always resolve to next owner` 规则收敛：若当前 study 没有 live provider attempt，就必须生成唯一 current owner action、owner receipt、MAS-owned typed blocker、human gate 或 stop-loss。`owner-route-reconcile` 不得输出空 action queue 后让 study 静默停住；`domain-action-request-materialize` 只能接受同一 study/quest/truth/runtime/source/work-unit currentness 的 owner request；`domain-owner-action-dispatch` 遇到 OPL retry/dead-letter、authority refusal、stale dispatch、forbidden write 或 missing owner callable 时，必须把结果稳定为 MAS owner receipt 或 typed blocker。该规则不授权论文 ready、publication gate clear、submission package 或 `current_package` 写入。

`domain-action-request-materialize` 的 action selection 必须以 per-study current execution truth 为准。若 `studies[].action_queue` 显式为空，或 `current_execution_envelope.state_kind` 已是 `typed_blocker` / `blocked_typed_owner` / `parked` / `running_provider_attempt`，materializer 不得回退消费 workspace top-level `action_queue` 中同 study 的旧 action；只有当前 `domain_transition` 能生成同一 truth/runtime/source/work-unit currentness 的新 owner action 时才可替代该空队列。所有 materialized default-executor dispatch 必须先通过 `owner_route_attempt_envelope.dispatchable=true`，缺 `work_unit_id`、`work_unit_fingerprint`、truth epoch、runtime-health-or-source-eval currentness 时只能返回 blocked/typed blocker，不能写成 ready。`domain-owner-action-dispatch` 执行前应用同一硬门；non-dispatchable owner route 不能靠 stale consumer dispatch、read-model reconcile 或 OPL retry 继续启动 provider attempt。

`domain-owner-action-dispatch` 的默认无 `--action-types` 模式必须按 Progress-First same-tick 语义消费所有 current ready dispatch：先接受 `consumer/latest.json` 中匹配当前 owner route 的 inline dispatch；若 inline surface 缺失或落后，也必须读取同一 study 的 `default_executor_dispatches/*.json` persisted dispatch，并只在该 dispatch 同时通过 current owner route / owner request / currentness score 校验时执行。显式 `--action-types` 只用于诊断、限流或人工指定 owner action；不能成为避免空转的必要条件，也不能绕过 currentness 仲裁。当 scan/latest、consumed transition 或 live provider attempt 已经给出 runtime-current owner route / work unit 时，无论是否传入显式 action list，dispatcher 都必须只执行该 runtime-current dispatch；consumer/latest 或 persisted dispatch 中仍处于 active owner request lifecycle 的旧 tail 只能在没有更高优先级 current route 时作为恢复入口。stale consumed transition、non-dispatchable route、缺 owner request 或不匹配 currentness basis 的 persisted dispatch 继续 fail closed，不得因为默认选择扩大或显式 action list 而被执行。

`domain-health-diagnostic` 的 developer supervisor safe-apply 路径必须按 same-tick pump 语义执行 `owner-route-reconcile -> domain-action-request-materialize -> domain-owner-action-dispatch`，最多连续 3 轮。第一轮若只产生 receipt/read-model follow-through 但没有 provider handoff、typed blocker 或 terminal no-action，controller 必须在同一 tick 继续追下一 owner action，不能把下一 heartbeat 继续耗在相同 reconcile 上。停止原因必须显式落到 `provider_handoff_started`、`typed_blocker_or_dispatch_blocker_observed`、`no_owner_action_remaining`、`repeat_suppressed_owner_delta_required` 或 `max_passes_exhausted_owner_delta_required`。same-tick initial scan 与 handoff 后 provider-admission probe 必须使用短 OPL provider readiness / live attempt inspect 预算，并在 `developer_supervisor_same_tick.provider_probe_budget` 投影；focused `--studies` tick 必须关闭 previous unscanned study handoff retention，让 `owner_route_reconcile`、`provider_admission_probe` 与 top-level reconcile request 只包含目标 study。超预算、未观察到 active attempt 或 OPL inspect 暂不可用时，返回 `provider_handoff_written_admission_pending` / terminal diagnostic，让下一 owner 明确落到 OPL worker / scheduler / attempt admission，而不是阻塞在重复 receipt、read-model reconcile 或长时间 queue/attempt inspect。后两者必须携带 `progress_first_terminal_diagnostic.next_forced_delta`，要求下一步必须产生 deliverable delta、domain owner receipt、typed blocker、human gate 或 stop-loss；重复 receipt、重复 read-model reconcile 和同 source 新 provider attempt 都列为 forbidden next actions。该 surface 只做 MAS controller refs-only 监督，不写 study truth、paper、publication eval、controller decision 或 package。

Progress-First throughput read-model 的排序必须优先呈现推进入口：current executable owner action、running provider attempt、MAS-owned typed owner blocker、human gate 或 stop-loss。receipt consumption、scan/read-model currentness、closeout semantic completeness 和 duration/token/cost telemetry 缺口只能进入 observability / governance diagnostic，除非它们本身已经被 MAS owner surface 稳定为 typed blocker；这些缺口不能抢占 `ready_for_dispatch`、`running` 或 `blocked_typed_owner`，也不能把已具备同一 study/work-unit currentness 的 owner action 吞成空等待。当 monitoring summary 的 typed execution envelope 已声明 `execution_state_kind=typed_blocker` / `blocked_typed_owner` 且携带 typed blocker 时，`study-state-matrix` 必须把它计为 `blocked_typed_owner`；next owner、controller action 或 next work unit 只作为机制修复 / route-back provenance，不能重新打开普通 dispatch loop。当 latest scan 缺少 study-level owner route，但 immutable dispatch 自带 owner_route 且通过 source/work-unit/truth/runtime-or-eval basis 与 allowed action 校验时，dispatch owner_route 可以作为 currentness basis；scan 缺 route 只作为治理缺口记录。

同一 study / owner / work unit / source currentness 的 default-executor redrive 必须执行 no-loop budget。第一次 non-consumable closeout 可以携带 `redrive_context` 重驱一次；第二次同义 closeout 仍没有 canonical paper/evidence/review/gate delta 或可消费 typed closeout refs 时，MAS 必须消费为 `progress_first_owner_redrive_budget_exhausted` typed blocker，并指向机制修复、human gate 或 stop-loss candidate。`domain-handler export`、`owner-route-reconcile` 和 `domain-action-request-materialize` 不得通过 receipt currentness、read-model refresh、`execution_id` 或 dedupe key 变化继续生成普通 default-executor task；这些信息只能作为 refs-only lineage / observability evidence。

`owner_route_attempt_protocol` 的 currentness authority 只来自 source/work-unit/truth/runtime-or-eval basis、source fingerprint 与显式 `allowed_actions`。`owner_reason_contract` 只保留 diagnostic、forbidden-surfaces 与 regression refs；上游 read-model 或 legacy projection 丢失 `allowed_actions` 时，decorator 不再从 reason registry 恢复默认 action，避免 diagnostic reason 变成隐式执行授权。未知 reason、无显式 allowed action 或缺 currentness basis 都 fail closed。

AI reviewer record-only surface 与 `publication_eval/latest.json` 使用同一 fail-closed reviewer OS currentness 合同。`artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json` 只有在 assessment provenance、quality dimensions、future-facing limitations、current manuscript binding 和完整 `reviewer_operating_system` trace 全部满足当前 `medical_publication_ai_reviewer_os_v1` 时，才可作为 owner-route read model 的 current publication eval projection；否则继续使用已 materialized 的 `publication_eval/latest.json` 或路由回 AI reviewer typed blocker。`domain-owner-action-dispatch` 同样不得把缺失、无效 reviewer OS 或 item-only future-facing limitations 的 request record 交给 publication workflow 后置失败。record-only handoff 的 canonical materializer 是 `medautosci publication materialize-ai-reviewer-record --profile <profile.toml> --study-id <study-id> --payload-file <ai_reviewer_record_payload.json> --build-production-trace`：AI reviewer executor 只被授权先写 `artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json` 中的 `record_payload`，再由 MAS owner callable 写 response archive；该路径不写 `publication_eval/latest.json`，并由 MAS production trace builder 从当前 request/input refs 生成 `reviewer_operating_system`，避免 executor 产出 diagnostic/request 形态的 trace。top-level `future_facing_limitations_plan` 必须显式提供 limitation、claim impact、future analysis/data/design 和 current wording restraint 四个字段；`{"item": "..."}` 只能作为 reviewer 笔记，不能进入 publication eval record。

AI reviewer request refresh 的 currentness 判断采用两层证据。第一层是 `reviewer_operating_system.currentness_checks` 对 required ref 的显式 ref + digest 匹配；digest 匹配即证明 record 消费了当前文件内容，不再用文件 mtime 把同内容的投影刷新误判为 stale。第二层只在没有针对该 ref 的显式 currentness check 时启用：request-bound record 的 assessment/source/evidence refs 覆盖 required ref，且 record timestamp 不早于 ref payload timestamp 或 mtime，才可清除 stale current-input blocker。若 record 的 currentness check 提到了 required ref 但 digest 不匹配，必须继续 fail closed；若 request 已带具体 `ai_reviewer_record_stale_after_current_manuscript` / `current_inputs` / `unit_harmonized_rerun` blocker，刷新失败时必须保留原 blocker taxonomy，不得把 current manuscript mirror 或 current input 缺口降级成泛型 unit-harmonized rerun。

`quality_repair_batch` 与其内部调用的 `gate_clearing_batch` 必须消费同一 effective current publication eval：优先读取已通过上述 currentness 合同的 current AI reviewer record-only eval；没有 current record 时才读取 stable `artifacts/publication_eval/latest.json`。repair evidence、batch `source_eval_id`、controller route context 和 nested gate-clearing eval id 必须绑定同一个 current eval id；否则旧 `publication_eval/latest.json` 会关闭旧 reviewer record，却让 owner-route read model 继续按更新的 AI reviewer record 排同一个 work unit，形成反复 redrive。该 effective reader 不改变 `publication_eval/latest.json` 的物化 owner，也不授权 `publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 current package 写入。

当 current eval 来源是 `ai_reviewer_responses/*_publication_eval_record.json` 时，domain transition 的 `completion_receipt_consumption`、`source_refs` 和 owner-route publication eval ref 必须指向该实际 record path，不能回写成 stable `artifacts/publication_eval/latest.json`。若 `quality_repair_batch` 已针对该 current eval 产出 canonical artifact delta 并写出 `artifacts/supervision/requests/ai_reviewer/latest.json` recheck request，`owner-route-reconcile` 必须先投给 `return_to_ai_reviewer_workflow`，等待 AI reviewer owner 产出新的 publication eval / record；不得继续重复派发同一个 `run_quality_repair_batch` write work unit。该规则只消费 owner receipt 与 request currentness，不授权机械 projection 宣布质量 ready。

当 current eval 是已通过 record-only 合同的 AI reviewer archive projection，且 `project_ai_reviewer_request_lifecycle` 对同一 stable `artifacts/supervision/requests/ai_reviewer/latest.json` 投影出 `assessment_written=true`、`blocked_reason` 为空时，旧 request 中的 `ai_reviewer_record_stale_after_current_inputs`、`ai_reviewer_record_stale_after_current_manuscript` 或 unit-harmonized stale blocker 已被 current record 消费。domain transition table 必须在同一 tick honor 该 current record 的 `recommended_actions[]` / route-back owner，不得继续把 next work unit 投回 `produce_ai_reviewer_publication_eval_record_against_current_inputs`、`produce_ai_reviewer_publication_eval_record_against_current_manuscript` 或 unit-harmonized reviewer production。旧 request path 只保留为 receipt/currentness lineage；Progress-First 的下一步必须进入 write、gate-clearing、package follow-through、human gate 或 typed blocker，而不是重复 reviewer/read-model reconcile。

`domain-handler export` 选择 `domain_owner/default-executor-dispatch` 时必须先剔除已经被 MAS owner receipt 消费的 dispatch，再在剩余候选之间做 blocked-action / currentness / newest 选择。较新的 `return_to_ai_reviewer_workflow` dispatch 若已有 current AI reviewer receipt，只能作为已完成 owner step 进入 receipt ledger；它不得继续遮蔽后续未消费的 `run_quality_repair_batch`、gate 或 delivery work unit。若未消费候选存在，export 必须把它投影为 OPL 可调度 family task，而不是只输出 refs-only reconcile task 或让 scheduler tick idempotent-noop。该规则保持 MAS 不写 OPL runtime state、不直接 resume provider，也不放宽 publication gate；它只保证 Progress-First 的下一 owner work unit 不被已完成 receipt 吞掉。

Publication-gate replay 的 owner 选择以 work-unit family 为准。`publication_gate_replay`、`owner_authorized_publication_gate_replay` 和 `dpcc_publication_gate_replay_after_current_ai_reviewer_record` 必须进入 `gate_clearing_batch/run_gate_clearing_batch`，即便 reviewer action 的 `route_target` 写成 `write`。`route_target` 只表达后续修复语义；已注册的 replay work unit、lane 和 required output surface 才是当前 executable owner truth。这个规则用于防止已消费 AI reviewer receipt 后再次落入 writer receipt / read-model reconcile 循环。

Generic provider lifecycle CLI 已退役，不再作为 MAS 活跃 controller surface。外部 research/analysis progression 通过 publication aftercare 的 refs-only owner-route task 投影或 OPL provider-backed family runtime 进入 MAS domain-handler family bridge；MAS 仓不再保留 `recommend-domain-handler` / `provision-domain-handler` / `import-domain-handler` 这类 provider registry、workspace provisioning 或 import control-plane 壳。任何可执行任务仍必须回到 MAS owner chain，并由 `domain-handler export` / `domain-handler dispatch` 产出 owner receipt、typed blocker 或 refs-only dispatch receipt。

后续优先顺序：

1. MAS domain authority refs / owner receipt / typed blocker 与 OPL runtime handoff 的 owner-path 收敛
2. OPL framework migration：stage descriptor、domain-handler receipt、artifact locator、authority refs 与 direct / hosted path 等价
3. policy/config 外置化和 publication profile 驱动的细粒度规则
4. legacy MDS / Hermes / workspace-local manager surface 的显式降级、归档或 parity-only 保留

## 完整交付契约

`study_delivery_sync` 已经是 `MedAutoScience` 的一等 controller，它负责把 `submission_minimal` 和 `finalize` 阶段产出搬到 `studies/<study-id>/{manuscript,artifacts}/final` 下。对于已经形成 `submission_minimal` 的 finalized paper bundle，下游的 `finalize` skill 由 overlay 注入后会自动调用 `study_delivery_sync(stage="finalize")`，因此新的医学课题在进入正式论文交付收口时，会自动完成浅路径正式交付同步，而不再依赖 workspace 里 legacy 的手工路径。

新生成的 submission package 使用 `submission-package.v2`：`paper/submission_minimal/` 是 controller-authorized source package，`manuscript/current_package/` 是 human-facing mirror。两边根目录放 `manuscript.docx`、`paper.pdf`、figures/tables 等常用投稿文件；`audit/` 放 manifest、evidence/review ledger、study charter；`reproducibility/` 放 source signature 和来源路径索引。新包不再平铺 root-level audit JSON，读取端只保留 legacy root-file import diagnostic 用于旧工作区识别。

`publication gate` 的 `allow_write=false` 只约束下游投稿包、bundle、submission proofing 和 `current_package` 写面。MAS managed runtime worker 在当前 controller work unit 明确授权时，仍可修改 canonical `paper/` 下的 manuscript、evidence ledger、review ledger、revision log 或分析修订材料；这些写入属于上游 analysis-campaign/write stage，不属于前台人工接管。`execution_owner_guard.supervisor_only=true` 继续阻止 Codex App 前台绕开 MAS 直接改论文，但不能关掉 MAS 自己派发给 managed worker 的 canonical paper 修订权限。

AI reviewer 把医学写作质量问题回退到方法学或 source-documentation owner 时，`medical_prose_quality_analysis_source_documentation_repair` 属于 upstream analysis/paper repair work unit。`run_quality_repair_batch` 必须在 control-plane 中使用 `paper_write` 授权执行该 work unit，并产出 canonical repair evidence、AI reviewer recheck request 或 typed blocker；它不能因为 publication gate 仍处于 downstream bundle block 而退回 `bundle_build` 或抢跑 submission/current package。

AI reviewer 把当前医学写作质量问题回退到 write owner 时，`medical_prose_write_repair` 同样属于 upstream publishability repair work unit。即使调用方携带了旧的 `submission_minimal_refresh` 或其他 bundle route context，`quality_repair_batch` 也必须以当前 AI reviewer-backed `publication_eval/latest.json` 中的 upstream `route_back_same_line` work unit 为准，改走 `paper_write`。当 record-only reviewer verdict 的 `recommended_actions[]` 只给出 `blocking_work_units[]`、未给出 `next_work_unit` 时，`owner-route-reconcile` 必须从 `blocking_work_units[]` 选择已注册的 write/story-surface work unit，仍投递到 `write/run_quality_repair_batch`；缺 `next_work_unit` 不能使 current write route-back 回落到旧 `return_to_ai_reviewer_workflow`。若 AI reviewer callable、owner request 或 repeat-suppression 没有完成，`paper_repair_executor` 和 domain-handler dispatch receipt 必须保留真实 typed blocker，例如 `ai_reviewer_request_missing` 或 `repeat_suppressed`，而不是把它降成泛型 callable 缺失。该路径仍不得写 publication eval、controller decision、submission package 或 current package；它只让 canonical paper repair owner 有机会完成修稿或给出精确 blocker。

`medical_prose_write_repair` 与 `manuscript_story_repair` 共用 story-surface delta 合同。若 `quality_repair_batch/latest.json` 对当前 `publication_eval/latest.json` 返回 `blocked_reason=manuscript_story_surface_delta_missing`、`next_owner=write`，controller projection、owner route、runtime prompt 和 `owner-route-reconcile` 必须保留原始 write work unit，并把 `run_quality_repair_batch` 交给 write owner继续处理。该 redrive 只授权 canonical `paper/draft.md` 或 `paper/build/review_manuscript.md` 的正文修订或 typed blocker，不授权抢跑 package/current_package、修改 AI reviewer verdict，或把内部运行态语言写进论文正文。

`run_quality_repair_batch` writer handoff 和通用 default-executor dispatch 必须携带 `default_executor_search_discipline.v1`。executor 只能按 stage packet / owner refs 做 bounded search；不得用 `grep -R`、`find .` 或 repository-wide `rglob` 扫 `runtime/.ds/**`、Codex homes、plugin cache 或资产目录。缺少证据时返回 typed blocker，而不是扩大到 runtime/cache 全盘搜索。

若同一 eval id 的 `quality_repair_batch/latest.json` 已形成 `writer_worker_handoff`，且其 owner route 允许 `run_quality_repair_batch`，该 writer handoff 是当前 owner truth。`owner-route-reconcile` 必须用它阻止 pending `ai_reviewer_assessment_required` 或旧 `domain_transition_ai_reviewer_re_eval` 抢占，直到 write owner 产出 story-surface delta、typed blocker 或新的 AI reviewer recheck request。

`current_manuscript_claim_evidence_alignment_repair` 是 `claim_evidence_alignment_repair` 的 current-manuscript alias。它属于 upstream publishability repair，由 `quality_repair_batch` 以 `paper_write` 授权执行 claim/evidence map 与 evidence ledger 对齐；不得被 generic `manuscript_story_repair` 或 story-surface digest currentness gate 覆盖。若 controller / dispatch / publication eval 已显式给出这个 work unit，route merge、authority gate、gate clearing 和 upstream repair 都必须保留该 work unit，并返回 claim-evidence alignment evidence、AI reviewer recheck request 或 typed blocker。

当 AI reviewer-owned current manuscript eval 已明确给出 `route_back_same_line`、`route_target=write` 或 `next_work_unit.lane=write` 时，该 write route-back 是当前论文质量 owner truth，优先级高于 publication gate blocker 的重复 replay。`current_manuscript_claim_evidence_alignment_repair`、`claim_evidence_alignment_repair` 和注册的 story-surface write work unit 都必须被投到 `write` owner / `run_quality_repair_batch`；只有 write repair 产出 evidence、AI reviewer recheck request 或 typed blocker 后，才允许重新进入 `publication_gate_replay`。这防止 gate-clearing 已刷新 package freshness 但 gate replay 仍 blocked 时，owner-route 反复排同一个 `run_gate_clearing_batch` 而不回到真正的 manuscript / claim-evidence owner。

当 claim map 已引用某个 claim，但 `evidence_ledger.claims[]` 缺少同一 `claim_id` 时，repair owner 可以只在所有 claim evidence item 都能精确命中同 ID `evidence_ledger.items[].item_id`、且 item 具备 source paths 与 summary 时，把这些 ledger items 物化为正式 claim-level `claims[].evidence[]`。`claim_evidence_alignment` gate 本身仍不把 top-level `items[]` 当作对齐成功证据；无法精确物化时必须保留 typed blocker，而不是使用 source-path overlap 或其他启发式补齐。

当 AI reviewer-owned eval 已证明 claim-evidence alignment ready，且 `publication_quality_readiness` 唯一剩余缺口是 `owner_authorized_publication_gate_recheck` 时，controller transition 必须把下一步交给 `publication_gate_replay` / `run_gate_clearing_batch`。该 gate-recheck-only 状态不得继续执行旧 `route_back_same_line` write repair；只有 alignment 未 ready、缺少 digest、存在 blocker 或 missing 字段超出 gate recheck 时，才保留原 AI reviewer route-back 或 fail-closed owner route。

`domain_transition_publication_gate_blocker` 是 owner-route attempt protocol 的已注册 reason。它归属 `gate_clearing_batch` owner，允许 `run_gate_clearing_batch`，并要求写出 `artifacts/controller/gate_clearing_batch/latest.json` 或相应 typed blocker；owner-route registry 不得把它降成 `external_supervisor` 空队列。

`publication_gate_blocker` domain transition 生成的 action type 必须是 `run_gate_clearing_batch`，并由 `gate_clearing_batch` owner 执行。`publication_gate_specificity_required` 只表示需要把 blocker target 具体化到 claim / figure / table / metric / source refs，不能替代已经明确的 publication gate replay。

当 `publication_gate_blocker` 的 transition payload 仍带历史 `owner=publication_gate` 或 stale `external_supervisor_required` lifecycle 时，owner-route reconciliation 必须以可执行 action owner 为准，把 `run_gate_clearing_batch` 投到 `gate_clearing_batch`，并保留 `allowed_actions=["run_gate_clearing_batch"]`。这条规则防止 registered owner reason 正确但 action owner 不匹配时再次形成空队列。

`domain-owner-action-dispatch` 对 `run_gate_clearing_batch` 必须直接分派到 MAS-owned `gate_clearing_batch.run_gate_clearing_batch`，并把 current owner route / prompt contract 的 `work_unit_id=publication_gate_replay` 作为 controller route context 传入。这个执行路径不得写 `publication_eval/latest.json`、`controller_decisions/latest.json`、paper package 或 manuscript surface；它只能通过 gate-clearing batch owner 产出 `artifacts/controller/gate_clearing_batch/latest.json`、freshness proof、lifecycle receipt 或 typed blocker。

所有从 domain transition、owner-route scan、request materializer 或 default-executor dispatch 派生的 `run_gate_clearing_batch`，其 `required_output_surface` 都必须统一为 `artifacts/controller/gate_clearing_batch/latest.json`。`publication_eval/latest.json` 是 AI reviewer / publication eval authority surface，不能作为 gate-clearing batch 的 required output，也不能在 prompt contract 中误导 executor 写入。

closed `publication_work_unit_lifecycle/latest.json` 只有在 `source_eval_id` 明确等于当前 `publication_eval/latest.json.eval_id` 时，才可以触发 `publication_gate_recheck`。缺少 `source_eval_id` 或指向旧 eval 的 lifecycle 只能作为历史/残留，不得抢占当前 AI reviewer-backed `route_back_same_line`。当当前 route-back 指向 write owner 时，outer-loop、runtime resume preflight、runtime-core turn authorization 与 owner-route reconciliation 必须物化 `run_quality_repair_batch` controller decision，而不是把旧 `request_opl_stage_attempt` 或 `run_gate_clearing_batch` 授权继续传给 runtime。

story-surface delta 的 currentness 必须基于上一轮同一 `source_eval_id`、同一 `manuscript_story_surface_delta_missing` blocked batch 记录的 canonical manuscript surface 指纹。若当前 `paper/draft.md` 或 `paper/build/review_manuscript.md` 只是早已晚于 stale `publication_eval/latest.json`，但内容指纹没有相对上一轮 blocked batch 改变，`repair_execution_evidence` 必须继续 fail closed 到 `manuscript_story_surface_delta_missing`。缺少上一轮 surface fingerprint 时也不能用 publication eval mtime、gate replay mtime、ledger mtime 或文件新旧启发式推断正文修订完成。

`medical_prose_write_repair` 可以由 MAS writer-owner materializer 从 canonical `paper/` evidence surfaces 生成正文 story-surface delta。该 materializer 的输入只能是 `methods_implementation_manifest`、cohort/display/treatment-gap/transition support surfaces、table markdown 和 canonical evidence/review refs；不得读取 `manuscript/current_package`、delivery mirror、旧 artifact archive 或人工 inspection package 作为正文 authority。它必须把 phenotype derivation transparency、recorded medication-coverage 或 potential treatment-review gap terminology、BP/data-quality assessment、baseline characteristics、numeric results 和 restrained discussion 写入 `paper/draft.md` 并同步 `paper/build/review_manuscript.md`，同时继续禁止 `paper/submission_minimal/`、`manuscript/current_package/`、`publication_eval/latest.json`、`controller_decisions/latest.json` 和 submission readiness verdict。该正文 delta 只是 AI reviewer recheck 的输入，不等于 `medical_journal_prose_quality=ready`。若同一 `source_eval_id` 的上一轮 blocked batch 已记录 story-surface 指纹，writer-owned 当前正文只要同步变化、无运行态语言、具备医学论文基本章节和上述领域概念，就必须被保留；preservation guard 不得用旧模板术语覆盖更稳妥的 medication-coverage 表达。

注册到 `STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS` 的其他 write-owner story-surface work unit 使用同一 preservation guard。DM002 external-validation hardening work unit 的当前 writer-owned 正文只要相对上一轮同一 `source_eval_id` 的 blocked surface 指纹同步变化、无运行态术语、具备 Abstract / Introduction / Methods / Results / Discussion / Limitations / Conclusion，并覆盖 external validation、validation cohort、discrimination、calibration、95% CI 或 bootstrap/Wilson uncertainty、Cox 或 prediction score、NHANES 与 development-validation source 语义，就必须保留并作为 AI reviewer recheck 输入。`eval_bound_currentness` 的 current reviewer-bound manuscript 保护仍只用于避免 `medical_prose_write_repair` 覆盖当前 AI reviewer 绑定稿；它不得被扩展成其他 story-surface work unit 的完成证据。

当该 work unit 的 specificity target 明确命中 HDL/unit harmonization、unit-standardized model application、`harmonization_route_back`、`unit_harmonized_external_validation_rerun` 或 `unit_harmonized_validation_uncertainty_and_grouped_calibration` 时，它升级为 hard methodology route。`quality_repair_batch` 必须在普通 gate-clearing、display materialization、paper owner surface 初始化、package freshness 和 AI reviewer recheck 前写入 `blocked_reason=unit_harmonized_rerun_required`，并交给 `analysis_harmonization_owner` 的 `unit_harmonized_external_validation_rerun`。普通 prose/source-documentation closeout、generic completed receipt 或 package refresh 不能关闭该阻塞；只有 unit-harmonized rerun evidence 或同一 owner 的 typed blocker 可以被 runtime evidence adoption 消费。

Supervisor scan 必须消费这个 hard methodology handoff。只要 `artifacts/controller/quality_repair_batch/latest.json` 明确写出 `status=blocked`、`blocked_reason=unit_harmonized_rerun_required`、`next_owner=analysis_harmonization_owner`、`next_work_unit=unit_harmonized_external_validation_rerun`、`quality_gate_relaxation_allowed=false` 和 `current_package_write_allowed=false`，owner route 就必须投到 `analysis_harmonization_owner` 的 `unit_harmonized_external_validation_rerun`，且不得被旧 `domain_transition_ai_reviewer_re_eval`、`auto_runtime_parked` 或 generic external supervisor lifecycle 覆盖。

`analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker` 是该路线的可执行 owner callable。它不能只写 `artifacts/supervision/requests/analysis_harmonization/latest.json`；执行后必须写出 `artifacts/controller/analysis_harmonization/latest.json`，并在其中给出 unit-harmonized rerun evidence，或给出 `blocked_reason=unit_harmonized_rerun_required`、`typed_blocker_owner=analysis_harmonization_owner` 的 typed blocker。clean reproducible-model rebuild route 被 human gate 授权后，该 owner 可以在 controller-owned analysis surface 下重建 unit-harmonized Cox external-validation evidence，并把 raw-scale HDL run 与 unit-harmonized HDL run 并列记录到 `artifacts/controller/analysis_harmonization/unit_harmonized_external_validation_rerun.json`；该 evidence 只供后续 AI reviewer / writing owner 重写医学结论，不等于 submission readiness verdict。该 owner callable 不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、submission package 或 current package，也不能授权 submission readiness。若输入、编码、分析依赖或 evidence materialization 不足，必须 fail closed 到 typed blocker，而不是把 raw-scale transport metrics 继续包装为医学结论。

AI reviewer 或 controller decision 可能把同一 hard methodology request 表达为 `unit_harmonized_validation_uncertainty_and_grouped_calibration`，其语义是补齐 unit-harmonized external validation 的不确定性、分组校准和复现细节。该 work unit 不应落回 generic `request_opl_stage_attempt`、`quality_repair_batch` 或 OPL generic runner；MAS current controller authorization refs 必须把它映射到 `domain-owner-action-dispatch --action-types unit_harmonized_external_validation_rerun`，由 `analysis_harmonization_owner` 产出 evidence 或 typed blocker。这是 MAS domain owner callable 映射，不是 MAS 私有 control-plane 扩张；OPL 仍只承载 provider、queue、attempt、projection 和 App/workbench shell。

Display materialization 是 quality-repair-batch 的 gate replay 依赖面。它重建 `paper/tables/table_catalog.json` 时必须保留或从 `paper/claim_evidence_map.json` 派生表格 `claim_ids`，例如 T1 基线表绑定 case-mix claim，T2 performance 表绑定 validation/calibration/transportability claims。Materializer 不能把表格 claim binding 重写为空；否则 display-to-claim closure 会被 replay 自身重新打开。

`stale_study_delivery_mirror` 归属下游 package/delivery lane。若 canonical paper 与 submission authority 已 current，但缺少 current package freshness proof，controller 必须产出 `submission_delivery_terminal_blocker` 这类 controller-owned blocker，说明 delivery lane 自身不闭合的原因；它不得长期把 analysis-campaign/write stage 路由回 `gate_needs_specificity`，也不得让 Codex CLI 重放同一个不可执行的 package replay loop。

AI reviewer-backed `return_to_ai_reviewer_workflow` 属于医学质量 owner redrive；它不能被 mechanical projection、旧 reviewer artifact 或 package freshness proof 替代。若当前包尚未形成 delivery-manifest-current 的用户可见里程碑，`publication_eval/latest.json` 与 `controller_decisions/latest.json` 当前一致指向 `ai_reviewer_re_eval` / `domain_transition_ai_reviewer_re_eval` 时，managed study runtime 应保持或恢复到 AI reviewer workflow，由 AI reviewer 关闭写作质量判断。若 `manuscript/delivery_manifest.json` 已证明 `manuscript/current_package/` 是当前 human-facing milestone package，controller 必须优先投影 `delivered_package_handoff` 并 `stop_runtime`，等待新的显式 reviewer_revision、用户修改意见或 resume/relaunch；这个停驻只说明交付包已交给用户审阅，不说明 `medical_journal_prose_quality` 或 submission readiness 已经 clear。

显式 `reviewer_revision` intake 晚于当前 AI reviewer-owned `publication_eval/latest.json` 时，旧 eval 不再是 current 医学质量判断。domain transition candidate、domain transition table 与 supervisor route scan 都必须优先生成 `return_to_ai_reviewer_workflow`，不得被 closed `publication_gate_recheck` lifecycle、package freshness proof 或旧 route-back artifact 抢占。该规则属于 MAS domain agent 的 AI reviewer currentness 语义；OPL 只可承载 attempt/queue/projection，不持有或关闭 `medical_journal_prose_quality` verdict。

OPL provider attempt 启动前必须把上述 current domain transition 物化为当前 controller decision。若 `progress_projection` 已经给出 `domain_transition.ai_reviewer_re_eval` / `return_to_ai_reviewer_workflow`，但 `artifacts/controller_decisions/latest.json` 仍是旧的 `run_gate_clearing_batch` 或其他 stale work unit，MAS owner-route preflight 必须先通过 `study_outer_loop.materialize_non_dispatching_outer_loop_decision` 写出匹配的 AI reviewer controller decision，再把 controller authorization refs 交给 OPL provider-backed runtime 创建新 attempt。若当前 `domain_transition.route_back_same_line` 指向 write owner，preflight 必须同样写出匹配的 `run_quality_repair_batch` controller decision，并把当前 work unit fingerprint 绑定到 runtime owner-route refs。OPL provider auto-continue 只能消费这组 MAS currentness refs，并把 fresh controller decision 绑定为本次 attempt 的 `current_controller_authorization`。executor prompt 和 `current_controller_authorization` 只能从这个 MAS controller decision 读取授权，不得直接把 status read-model、旧 runtime state 或 OPL queue 投影当作质量真相。

`manuscript_story_repair` 的 repair execution evidence 必须证明正文面已清除 invalid-analysis-history residue。stage packet、claim/evidence guardrail、review ledger 或 gate replay 本身不能把 raw-scale sensitivity、unit-harmonization lesson、contaminated analysis history、data-processing error 等错误分析轨迹包装成有效论文增量。若 `paper/draft.md` 或 `paper/build/review_manuscript.md` 仍含这类残留，`repair_execution_evidence/latest.json` 必须写出 `status=blocked`、`canonical_artifact_delta.status=blocked`、`progress_delta_candidate=false` 和 `invalid_analysis_history_residue_present`，继续交给 write / quality repair owner 清理正文，而不是推进 AI reviewer re-eval 或 package refresh。错误轨迹只能留在 provenance、handoff 或 typed blocker；正式论文主线必须基于 cleaned valid evidence 组织。

Clean paper-authority migration 是旧论文项目进入新 MAS 的正式切换路径。旧 active paper authority surfaces 先由 `paper_authority_migration` 归档为 provenance，并写 cutover receipt；此后新 MAS 只能从当前 canonical study / paper / evidence / review / blueprint surface 重新物化 quality authority。读旧 token、旧 `gap_type`、旧 prose review 或旧 package metadata 的 normalizer 不属于 controller 能力。旧 artifact 不合新 contract 时，controller 必须 fail closed，并把 owner route 交给 AI reviewer、publication gate、write 或 delivery owner 重新生成当前 surface。

Clean paper-authority migration 的 discovery 只认 canonical study root。`studies/*` 下只有旧 `manuscript/current_package`、旧 paper authority archive 或 worktree residue 的目录，会进入 `noncanonical_paper_authority_residue_dirs` 诊断报告，不进入 study migration、quality、publication gate 或 delivery owner 队列。

当 clean cutover 后缺 `paper/medical_manuscript_blueprint.json` 等 canonical manuscript inputs，`return_to_ai_reviewer_workflow` 或 `run_quality_repair_batch` 的执行结果必须落到 `canonical_paper_inputs_rehydrate_required`，`next_owner=write`。Supervisor scan、consumer 和 dispatch executor 负责把这个 typed blocker 交给 `write` owner，且投影中必须保持 `legacy_artifact_reader_allowed=false`、`mechanical_blueprint_as_canonical_allowed=false`、`paper_package_mutation_allowed=false`。`domain_health_diagnostic` 只能记录 `controller_work_unit_blocked` audit/ledger，不能把 blocked work unit 误报为 executed，也不能因此重建 submission/current package。

Agent Lab medical manuscript quality suite 是 MAS 到 OPL Agent Lab 的 refs-only 投影。它把 AI reviewer-backed `medical_journal_prose_quality`、current reviewer feedback refs 和稿件质量 gap refs 暴露为 self-evolution task / scorecard / improvement candidate / promotion gate refs，并把 hard methodology/unit-harmonization route 作为可回归的 mechanism edit refs 暴露给 `opl-meta-agent`。OPL 可以用这些 refs 改进 stage attempt 和 agent 行为，但不能写 MAS study truth、publication quality verdict、artifact authority 或 submission readiness；最终质量关闭仍必须回到 MAS AI reviewer 与 publication owner。

该 suite 的 developer work order 必须按 study 质量 family 暴露目标，不能把某一篇论文的 reviewer target 当成通用目标。`prediction_model_external_validation` 可投影 HDL harmonization、model reproducibility、Table 1 / Table 2、uncertainty、NHANES framing 和 calibration / risk-collapse display 目标；`observational_phenotype_treatment_gap` 必须投影 phenotype derivation transparency、recorded treatment-gap terminology、BP/data-quality assessment、baseline characteristics table、formal figures/tables、numeric abstract、restrained discussion、reference style、claim-evidence alignment 和 method/data-error route-back 目标。suite 还必须投影 `first_draft_quality_route_back_checklist`，把 Methods 可复现、Results 数字化/CI、正式 Figure/Table、Abstract 硬指标与不确定性、结果驱动 Discussion、运行态术语清除和 claim-evidence 对齐转成带 blocker、route_target、owner、next_work_units、evidence_refs 与 expected_repair_result 的可执行 route-back 项，而不是只给 Agent Lab 一个 blocked 结论。`contracts/agent_lab_handoff.json` 的 `external_suite_improvement_policy.medical_manuscript_quality` 是 OMA 读取这些 family-specific change refs、patch hints 与 runtime required refs 的 contract；该 contract 只能指导 MAS repo patch 和 regression，不授权 `medical_journal_prose_quality=ready`。

DM002 暴露的 owner-chain / currentness / story-surface delta 问题必须在同一个 suite 中作为 regression family 暴露，而不是停留在单篇论文故障记录。该 family 覆盖 authority monotonicity、quality-repair writer handoff currentness、publication work-unit registry consistency、story-surface delta or typed blocker、runtime language purge、Methods/Results numeric reproducibility floor。它只给 OPL Agent Lab、OMA 和 MAS repo patch 指明 regression/test/documentation surface；它不推进 DM002 runtime，也不把 Agent Lab pass 解释成论文 ready、AI reviewer pass、publication gate close 或 submission readiness。

该 regression family 现在还覆盖 stale AI reviewer/current eval drift、OPL retry/dead-letter stabilization 和 macro-state no-stale-live。目标是让 Agent Lab 与 OMA 把 “旧 eval 抢当前 route”、“provider dead-letter 后无人接” 和 “旧 active_run_id 被投影为 live” 视为同一 owner-chain 控制面缺陷族，而不是 paper-local 文稿缺陷。

`publication-aftercare-plan` 是 publication aftercare 的 refs-only controller surface。它把 resubmission、talk package、Overleaf sync、ARIS research-pipeline / auto-review-loop / experiment queue、analysis queue 与 reviewer refresh 统一投影为可审计 refs、blocker 和 MAS owner-route task template。该 surface 不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal/`、`manuscript/current_package/` 或投稿包；domain-handler export 只能把 ready 的 aftercare 项投影为 `publication_aftercare/analysis-queue-progress` 或 `publication_aftercare/reviewer-refresh` typed task。domain-handler dispatch 收到这些 task 后必须回到 OPL-dispatched MAS domain owner chain：analysis queue 走 owner-route domain-authority handoff，reviewer refresh 走独立 AI reviewer workflow dispatch，质量 verdict、publishability 和 submission readiness 仍由 AI reviewer-backed publication eval 与 publication gate 决定。旧 `domain-route-reconcile` 只作为历史入口名或 provenance，不是当前 active control plane。

## Inspection package 契约

`delivery_inspector` 与 `inspection_package` 都服务人工检查，不是投稿授权面。`delivery_inspector` 当前是 read-only controller：它读取 `submission_minimal`、`current_package`、journal mirrors、zip 与 delivery manifest，输出 freshness、layout migration 和 source/mirror 标签；它的 `mutation_policy.read_only=true` 且 `writes_package=false`，不得派生 submission authorization 或 publication quality verdict。

`inspection_package` 是 human-inspection-only delivery surface。它允许在 `publishability_gate` 或 bundle gate blocked 时，把当前 draft / canonical paper surfaces 导出到 `manuscript/inspection_package/` 与 `artifacts/inspection_package/`，供人工审阅当前稿件、证据、图表、review ledger 和 blocked context。若 `delivery_inspector` 已证明现有 `current_package.zip` 是 current controller-authorized package，它只写 `authorized_current_package_available` review pointer / receipt，不重新物化 inspection zip。它不属于 `study_delivery_sync` 的正式 handoff，不写 `paper/submission_minimal/`，不写 `manuscript/current_package/`，不写 `current_package.zip`，也不更新 `publication_eval/latest.json` 或 `controller_decisions/latest.json`。

该 surface 的实现契约应包含：

- `surface_kind = inspection_package`
- `authority = human_inspection_only`
- `can_authorize_submission = false`
- `can_authorize_publication_quality = false`
- `can_clear_publishability_gate = false`
- `can_dispatch_delivery_sync = false`
- `forbidden_writes` 必须覆盖 `paper/submission_minimal/`、`manuscript/current_package/`、`manuscript/current_package.zip`、`artifacts/publication_eval/latest.json` 与 `artifacts/controller_decisions/latest.json`

任何需要投稿、正式 bundle handoff 或质量放行的后续动作，必须回到 MAS owner chain：AI reviewer / publication gate / controller decision / `submission_minimal` / `study_delivery_sync`。人工在 inspection package 中发现的问题只能形成 reviewer feedback、durable task intake 或 canonical paper repair input，不能直接 patch inspection package 后声明 gate cleared。
