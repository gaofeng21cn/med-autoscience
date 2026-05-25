# Controllers

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime control surfaces and controller responsibilities for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable runtime control support only; runtime control truth remains in controller source, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

这个目录用于说明 `MedAutoScience` 中的外层治理控制器迁移状态。

这些 controller 默认首先服务于 Agent 调用面，而不是人手工操作面。

也就是说：

- controller 是 MAS domain handler / authority refs / diagnostic refs 的稳定入口之一，不是 MAS 长期 generic runtime owner。
- CLI 只是当前 direct path 的薄包装；OPL generated/default caller 接管后，repo-local CLI/MCP/product-entry/sidecar wrapper 只能继续作为 domain target、authority function 或诊断入口，否则按 no-active-caller proof 删除。
- 人类主要审核 controller 产出的 report、summary、delivery、owner receipt、typed blocker 和审计日志。

当前已经完成最小代码迁移的能力有：

1. publishability gate
2. medical publication surface
3. submission minimal exporter
4. domain health diagnostic controller
5. study delivery sync
6. data assets controller
7. backend audit
8. managed study runtime orchestration
9. runtime storage maintenance
10. MAS sidecar family bridge export/dispatch
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
- `src/med_autoscience/controllers/study_runtime_router.py`
- `src/med_autoscience/controllers/study_runtime_types.py`
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

当前迁移策略是：

- 先把已经在真实医学课题中跑通过的 controller 以最小切片迁入新 repo
- 先保住行为和测试
- 再做第二轮去耦，把 policy、adapter、runtime protocol 从 controller 里拆出去

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

对于 managed study runtime，当前 controller 已明确分成两层：

- `study_runtime_router`
  - 负责 orchestration、preflight、transport 调用和 artifact 落盘
- `study_runtime_types`
  - 负责 `study_runtime_router` 的稳定 typed surface，并由 router 对外 re-export

对应稳定技术说明见：

- `docs/runtime/control/study_runtime_orchestration.md`

MAS sidecar bridge 是 `OPL` provider-backed family runtime 进入 MAS owner surface 的受控入口，不是新的 controller truth owner。`sidecar export` 只把 MAS-owned domain/status/source refs、owner receipt refs 和 typed blocker refs 投影给 typed family queue；`sidecar dispatch` 只接受 allowlisted task，回到 MAS controller/domain authority owner chain 产出 dispatch receipt、owner receipt 或 typed blocker。OPL provider 承载 stage attempt、queue/wakeup、retry/dead-letter、human-gate signal、attempt receipt 和 projection，但不得写 study truth、publication quality verdict、artifact gate、paper package、`progress_projection` 或 `domain_health_diagnostic`。这条边界的机器合同由 `contracts/test-lane-manifest.json` 的 `focused_lanes.mas-entry-boundary` 持有；本文件只做人读导航。

Generic sidecar provider lifecycle CLI 已退役，不再作为 MAS 活跃 controller surface。外部 research/analysis progression 通过 publication aftercare 的 refs-only owner-route task 投影或 OPL provider-backed family runtime 进入 MAS sidecar family bridge；MAS 仓不再保留 `recommend-sidecar` / `provision-sidecar` / `import-sidecar` 这类 provider registry、workspace provisioning 或 import control-plane 壳。任何可执行任务仍必须回到 MAS owner chain，并由 `sidecar export` / `sidecar dispatch` 产出 owner receipt、typed blocker 或 refs-only dispatch receipt。

后续优先顺序：

1. MAS domain authority refs / owner receipt / typed blocker 与 OPL runtime handoff 的 owner-path 收敛
2. OPL framework migration：stage descriptor、sidecar receipt、artifact locator、authority refs 与 direct / hosted path 等价
3. policy/config 外置化和 publication profile 驱动的细粒度规则
4. legacy MDS / Hermes / workspace-local manager surface 的显式降级、归档或 parity-only 保留

## 完整交付契约

`study_delivery_sync` 已经是 `MedAutoScience` 的一等 controller，它负责把 `submission_minimal` 和 `finalize` 阶段产出搬到 `studies/<study-id>/{manuscript,artifacts}/final` 下。对于已经形成 `submission_minimal` 的 finalized paper bundle，下游的 `finalize` skill 由 overlay 注入后会自动调用 `study_delivery_sync(stage="finalize")`，因此新的医学课题在进入正式论文交付收口时，会自动完成浅路径正式交付同步，而不再依赖 workspace 里 legacy 的手工路径。

新生成的 submission package 使用 `submission-package.v2`：`paper/submission_minimal/` 是 controller-authorized source package，`manuscript/current_package/` 是 human-facing mirror。两边根目录放 `manuscript.docx`、`paper.pdf`、figures/tables 等常用投稿文件；`audit/` 放 manifest、evidence/review ledger、study charter；`reproducibility/` 放 source signature 和来源路径索引。新包不再平铺 root-level audit JSON，读取端只保留 legacy root-file import diagnostic 用于旧工作区识别。

`publication gate` 的 `allow_write=false` 只约束下游投稿包、bundle、submission proofing 和 `current_package` 写面。MAS managed runtime worker 在当前 controller work unit 明确授权时，仍可修改 canonical `paper/` 下的 manuscript、evidence ledger、review ledger、revision log 或分析修订材料；这些写入属于上游 analysis-campaign/write stage，不属于前台人工接管。`execution_owner_guard.supervisor_only=true` 继续阻止 Codex App 前台绕开 MAS 直接改论文，但不能关掉 MAS 自己派发给 managed worker 的 canonical paper 修订权限。

AI reviewer 把医学写作质量问题回退到方法学或 source-documentation owner 时，`medical_prose_quality_analysis_source_documentation_repair` 属于 upstream analysis/paper repair work unit。`run_quality_repair_batch` 必须在 control-plane 中使用 `paper_write` 授权执行该 work unit，并产出 canonical repair evidence、AI reviewer recheck request 或 typed blocker；它不能因为 publication gate 仍处于 downstream bundle block 而退回 `bundle_build` 或抢跑 submission/current package。

AI reviewer 把当前医学写作质量问题回退到 write owner 时，`medical_prose_write_repair` 同样属于 upstream publishability repair work unit。即使调用方携带了旧的 `submission_minimal_refresh` 或其他 bundle route context，`quality_repair_batch` 也必须以当前 AI reviewer-backed `publication_eval/latest.json` 中的 upstream `route_back_same_line` work unit 为准，改走 `paper_write`。若 AI reviewer callable、owner request 或 repeat-suppression 没有完成，`paper_repair_executor` 和 sidecar dispatch receipt 必须保留真实 typed blocker，例如 `ai_reviewer_request_missing` 或 `repeat_suppressed`，而不是把它降成泛型 callable 缺失。该路径仍不得写 publication eval、controller decision、submission package 或 current package；它只让 canonical paper repair owner 有机会完成修稿或给出精确 blocker。

`medical_prose_write_repair` 与 `manuscript_story_repair` 共用 story-surface delta 合同。若 `quality_repair_batch/latest.json` 对当前 `publication_eval/latest.json` 返回 `blocked_reason=manuscript_story_surface_delta_missing`、`next_owner=write`，controller projection、owner route、runtime prompt 和 `owner-route-reconcile` 必须保留原始 write work unit，并把 `run_quality_repair_batch` 交给 write owner继续处理。该 redrive 只授权 canonical `paper/draft.md` 或 `paper/build/review_manuscript.md` 的正文修订或 typed blocker，不授权抢跑 package/current_package、修改 AI reviewer verdict，或把内部运行态语言写进论文正文。

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

该 suite 的 developer work order 必须按 study 质量 family 暴露目标，不能把某一篇论文的 reviewer target 当成通用目标。`prediction_model_external_validation` 可投影 HDL harmonization、model reproducibility、Table 1 / Table 2、uncertainty、NHANES framing 和 calibration / risk-collapse display 目标；`observational_phenotype_treatment_gap` 必须投影 phenotype derivation transparency、recorded treatment-gap terminology、BP/data-quality assessment、baseline characteristics table、formal figures/tables、numeric abstract、restrained discussion、reference style、claim-evidence alignment 和 method/data-error route-back 目标。`contracts/agent_lab_handoff.json` 的 `external_suite_improvement_policy.medical_manuscript_quality` 是 OMA 读取这些 family-specific change refs、patch hints 与 runtime required refs 的 contract；该 contract 只能指导 MAS repo patch 和 regression，不授权 `medical_journal_prose_quality=ready`。

DM002 暴露的 owner-chain / currentness / story-surface delta 问题必须在同一个 suite 中作为 regression family 暴露，而不是停留在单篇论文故障记录。该 family 覆盖 authority monotonicity、quality-repair writer handoff currentness、publication work-unit registry consistency、story-surface delta or typed blocker、runtime language purge、Methods/Results numeric reproducibility floor。它只给 OPL Agent Lab、OMA 和 MAS repo patch 指明 regression/test/documentation surface；它不推进 DM002 runtime，也不把 Agent Lab pass 解释成论文 ready、AI reviewer pass、publication gate close 或 submission readiness。

`publication-aftercare-plan` 是 publication aftercare 的 refs-only controller surface。它把 resubmission、talk package、Overleaf sync、ARIS research-pipeline / auto-review-loop / experiment queue、analysis queue 与 reviewer refresh 统一投影为可审计 refs、blocker 和 MAS owner-route task template。该 surface 不写 `publication_eval/latest.json`、`controller_decisions/latest.json`、canonical paper、`paper/submission_minimal/`、`manuscript/current_package/` 或投稿包；sidecar export 只能把 ready 的 aftercare 项投影为 `publication_aftercare/analysis-queue-progress` 或 `publication_aftercare/reviewer-refresh` typed task。sidecar dispatch 收到这些 task 后必须回到 OPL-dispatched MAS domain owner chain：analysis queue 走 owner-route domain-authority handoff，reviewer refresh 走独立 AI reviewer workflow dispatch，质量 verdict、publishability 和 submission readiness 仍由 AI reviewer-backed publication eval 与 publication gate 决定。旧 `domain-route-reconcile` 只作为历史入口名或 provenance，不是当前 active control plane。

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
