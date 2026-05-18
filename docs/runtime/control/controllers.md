# Controllers

这个目录用于说明 `MedAutoScience` 中的外层治理控制器迁移状态。

这些 controller 默认首先服务于 Agent 调用面，而不是人手工操作面。

也就是说：

- controller 是平台级稳定机器接口
- CLI 只是 controller 的薄包装
- 人类主要审核 controller 产出的 report、summary、delivery 和审计日志

当前已经完成最小代码迁移的能力有：

1. publishability gate
2. medical publication surface
3. submission minimal exporter
4. runtime watch controller
5. study delivery sync
6. data assets controller
7. backend audit
8. managed study runtime orchestration
9. runtime storage maintenance
10. MAS sidecar family bridge export/dispatch
11. generic sidecar provider recommendation/provision/import
12. delivery inspection / inspection package contract
13. clean paper-authority migration and re-materialization owner routing

对应的 Python 实现在包内：

- `src/med_autoscience/controllers/publication_gate.py`
- `src/med_autoscience/controllers/medical_publication_surface.py`
- `src/med_autoscience/controllers/submission_minimal.py`
- `src/med_autoscience/controllers/runtime_watch.py`
- `src/med_autoscience/controllers/study_delivery_sync.py`
- `src/med_autoscience/controllers/data_assets.py`
- `src/med_autoscience/controllers/data_asset_updates.py`
- `src/med_autoscience/controllers/backend_audit.py`
- `src/med_autoscience/controllers/study_runtime_router.py`
- `src/med_autoscience/controllers/study_runtime_types.py`
- `src/med_autoscience/controllers/runtime_storage_maintenance.py`
- `src/med_autoscience/controllers/sidecar_family_adapter.py`
- `src/med_autoscience/controllers/sidecar_provider.py`
- `src/med_autoscience/controllers/delivery_inspector.py`
- `src/med_autoscience/controllers/submission_inspection_export.py`
- `src/med_autoscience/controllers/paper_authority_migration.py`
- `src/med_autoscience/controllers/paper_authority_delivery_guard.py`
- `src/med_autoscience/controllers/runtime_supervisor_scan_parts/action_projection.py`

对应测试：

- `tests/test_publication_gate.py`
- `tests/test_medical_publication_surface.py`
- `tests/test_submission_minimal.py`
- `tests/test_runtime_watch.py`
- `tests/test_study_delivery_sync.py`
- `tests/test_data_assets.py`
- `tests/test_data_asset_updates.py`
- upgrade-check 的专用测试模块
- `tests/test_study_runtime_router.py`
- `tests/test_runtime_storage_maintenance.py`
- `tests/test_cli_cases/sidecar_family_adapter_command.py`
- `tests/test_sidecar_provider_aris.py`
- `tests/test_sidecar_provider_adapter.py`
- `tests/test_sidecar_provider_registry.py`
- `tests/test_delivery_inspector.py`
- `tests/test_delivery_visibility.py`
- `tests/test_inspection_package_contract.py`
- `tests/test_ai_reviewer_publication_eval_workflow.py`
- `tests/runtime_supervisor_scan_cases/test_paper_authority_cutover.py`
- `tests/test_runtime_supervisor_dispatch_executor_cases/clean_migration_rematerialization.py`

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
  - 统一检查 repo 配置、Git 状态、workspace contract、医学 overlay 状态和 legacy compatibility surface
  - 输出机器可读 decision，供 Agent 判断是否进入 explicit archive import、backend audit、parity check、upstream intake 或 MAS-side capability absorption

对于 managed study runtime，当前 controller 已明确分成两层：

- `study_runtime_router`
  - 负责 orchestration、preflight、transport 调用和 artifact 落盘
- `study_runtime_types`
  - 负责 `study_runtime_router` 的稳定 typed surface，并由 router 对外 re-export

对应稳定技术说明见：

- `docs/runtime/control/study_runtime_orchestration.md`

MAS sidecar bridge 是 `OPL` provider-backed family runtime 进入 MAS owner surface 的受控入口，不是新的 controller truth owner。`sidecar export` 只把 MAS-owned runtime/status/source refs 投影给 typed family queue；`sidecar dispatch` 只接受 allowlisted task，回到 MAS controller/runtime owner chain 产出 dispatch receipt。OPL provider 可以承载 stage attempt、queue/wakeup、retry/dead-letter、human-gate signal、attempt receipt 和 projection，但不得写 study truth、publication quality verdict、artifact gate、paper package、`study_runtime_status` 或 `runtime_watch`。这条边界的机器合同由 `contracts/test-lane-manifest.json` 的 `focused_lanes.mas-entry-boundary` 持有；本文件只做人读导航。

Generic sidecar provider 是 bounded extension 的统一 controller surface。Provider-specific CLI / controller / adapter wrapper 不再作为活跃入口；`aris` 这类 provider 通过 `recommend-sidecar --provider aris`、`provision-sidecar --provider aris`、`import-sidecar --provider aris` 和 `sidecars.registry` 暴露。Provider 行为归 `sidecar_provider` controller、generic adapter 与 provider registry，而不是独立的 provider 命令或 thin wrapper。

后续优先顺序：

1. MAS Runtime OS / managed runtime transport 的 owner-path 收敛和 compatibility guard
2. OPL framework migration：stage descriptor、sidecar receipt、artifact locator、authority refs 与 direct / hosted path 等价
3. policy/config 外置化和 publication profile 驱动的细粒度规则
4. legacy MDS / Hermes / workspace-local manager surface 的显式降级、归档或 parity-only 保留

## 完整交付契约

`study_delivery_sync` 已经是 `MedAutoScience` 的一等 controller，它负责把 `submission_minimal` 和 `finalize` 阶段产出搬到 `studies/<study-id>/{manuscript,artifacts}/final` 下。对于已经形成 `submission_minimal` 的 finalized paper bundle，下游的 `finalize` skill 由 overlay 注入后会自动调用 `study_delivery_sync(stage="finalize")`，因此新的医学课题在进入正式论文交付收口时，会自动完成浅路径正式交付同步，而不再依赖 workspace 里 legacy 的手工路径。

新生成的 submission package 使用 `submission-package.v2`：`paper/submission_minimal/` 是 controller-authorized source package，`manuscript/current_package/` 是 human-facing mirror。两边根目录放 `manuscript.docx`、`paper.pdf`、figures/tables 等常用投稿文件；`audit/` 放 manifest、evidence/review ledger、study charter；`reproducibility/` 放 source signature 和来源路径索引。新包不再平铺 root-level audit JSON，读取端只保留 legacy root-file fallback 用于旧工作区识别。

`publication gate` 的 `allow_write=false` 只约束下游投稿包、bundle、submission proofing 和 `current_package` 写面。MAS managed runtime worker 在当前 controller work unit 明确授权时，仍可修改 canonical `paper/` 下的 manuscript、evidence ledger、review ledger、revision log 或分析修订材料；这些写入属于上游 analysis-campaign/write stage，不属于前台人工接管。`execution_owner_guard.supervisor_only=true` 继续阻止 Codex App 前台绕开 MAS 直接改论文，但不能关掉 MAS 自己派发给 managed worker 的 canonical paper 修订权限。

`stale_study_delivery_mirror` 归属下游 package/delivery lane。若 canonical paper 与 submission authority 已 current，但缺少 current package freshness proof，controller 必须产出 `submission_delivery_terminal_blocker` 这类 controller-owned blocker，说明 delivery lane 自身不闭合的原因；它不得长期把 analysis-campaign/write stage 路由回 `gate_needs_specificity`，也不得让 Codex CLI 重放同一个不可执行的 package replay loop。

AI reviewer-backed `return_to_ai_reviewer_workflow` 属于医学质量 owner redrive。即使当前交付包只剩 submission metadata external gaps，只要 `publication_eval/latest.json` 与 `controller_decisions/latest.json` 当前一致指向 `ai_reviewer_re_eval` / `domain_transition_ai_reviewer_re_eval`，managed study runtime 应优先保持或恢复到 AI reviewer workflow，由 AI reviewer 关闭写作质量判断；普通 metadata-only submission parking 仍保持停靠，live worker 也可被 pause 等待外部信息，不因该路径获得自动放行。resumable / paused 状态下应用这个例外时，必须同时存在当前 `controller_decisions/latest.json` 的 `return_to_ai_reviewer_workflow` 授权和 `domain-transition::ai_reviewer_re_eval::*` work-unit fingerprint；旧 reviewer_revision intake 或旧 AI reviewer blocked assessment 不能单独重开 writer。

Clean paper-authority migration 是旧论文项目进入新 MAS 的正式切换路径。旧 active paper authority surfaces 先由 `paper_authority_migration` 归档为 provenance，并写 cutover receipt；此后新 MAS 只能从当前 canonical study / paper / evidence / review / blueprint surface 重新物化 quality authority。读旧 token、旧 `gap_type`、旧 prose review 或旧 package metadata 的 normalizer 不属于 controller 能力。旧 artifact 不合新 contract 时，controller 必须 fail closed，并把 owner route 交给 AI reviewer、publication gate、write 或 delivery owner 重新生成当前 surface。

当 clean cutover 后缺 `paper/medical_manuscript_blueprint.json` 等 canonical manuscript inputs，`return_to_ai_reviewer_workflow` 或 `run_quality_repair_batch` 的执行结果必须落到 `canonical_paper_inputs_rehydrate_required`，`next_owner=write`。Supervisor scan、consumer 和 dispatch executor 负责把这个 typed blocker 交给 `write` owner，且投影中必须保持 `legacy_artifact_reader_allowed=false`、`mechanical_blueprint_as_canonical_allowed=false`、`paper_package_mutation_allowed=false`。`runtime_watch` 只能记录 `controller_work_unit_blocked` audit/ledger，不能把 blocked work unit 误报为 executed，也不能因此重建 submission/current package。

## Inspection package 契约

`delivery_inspector` 与 `inspection_package` 都服务人工检查，不是投稿授权面。`delivery_inspector` 当前是 read-only controller：它读取 `submission_minimal`、`current_package`、journal mirrors、zip 与 delivery manifest，输出 freshness、layout migration 和 source/mirror 标签；它的 `mutation_policy.read_only=true` 且 `writes_package=false`，不得派生 submission authorization 或 publication quality verdict。

`inspection_package` 是 human-inspection-only delivery surface。它允许在 `publishability_gate` 或 bundle gate blocked 时，把当前 draft / canonical paper surfaces 导出到 `manuscript/inspection_package/` 与 `artifacts/inspection_package/`，供人工审阅当前稿件、证据、图表、review ledger 和 blocked context。它不属于 `study_delivery_sync` 的正式 handoff，不写 `paper/submission_minimal/`，不写 `manuscript/current_package/`，不写 `current_package.zip`，也不更新 `publication_eval/latest.json` 或 `controller_decisions/latest.json`。

该 surface 的实现契约应包含：

- `surface_kind = inspection_package`
- `authority = human_inspection_only`
- `can_authorize_submission = false`
- `can_authorize_publication_quality = false`
- `can_clear_publishability_gate = false`
- `can_dispatch_delivery_sync = false`
- `forbidden_writes` 必须覆盖 `paper/submission_minimal/`、`manuscript/current_package/`、`manuscript/current_package.zip`、`artifacts/publication_eval/latest.json` 与 `artifacts/controller_decisions/latest.json`

任何需要投稿、正式 bundle handoff 或质量放行的后续动作，必须回到 MAS owner chain：AI reviewer / publication gate / controller decision / `submission_minimal` / `study_delivery_sync`。人工在 inspection package 中发现的问题只能形成 reviewer feedback、durable task intake 或 canonical paper repair input，不能直接 patch inspection package 后声明 gate cleared。
