# 手工测试与运行面稳定化清单

## 文档目的

这份清单只服务当前 **论文配图资产线以外的主线**。
它把当前仓库里已经稳定、适合人工手工测试或验收的 repo-side surface 收口成一个可执行清单，同时把 explicit executor/proof diagnostic、historical backend / explicit archive import 诊断和 MAS 默认运行面分开。

当前 monolith 结论是：MAS 默认运行、默认诊断、默认进度和默认质量入口不再依赖外部 MDS。这里整理的是 **repo-side baseline 与显式外部/历史诊断面**，不是把旧 external runtime cutover 重新提升为 active 主线。

## 使用边界

- 正式研究入口仍是 `MedAutoScience`，不是直接调用 `MedDeepScientist` daemon / UI / CLI。
- `MedDeepScientist` 是 historical fixture / explicit archive import / backend audit / parity oracle，不是默认 execution surface 或系统本体。
- OPL 是 stage-led runtime framework；它可以托管 wakeup、queue、attempt、approval 和 projection，但不能替 MAS 写 study truth、publication quality 或 artifact authority。
- `program_id`、`study_id`、`quest_id`、`active_run_id` 不得混写。
- gate semantics 继续按 fail-closed 链理解：`progress_projection -> runtime_escalation_record -> publication_eval/latest.json -> controller_decisions/latest.json -> controller action`。
- `display / paper figure asset packaging` 独立工作线不在本文范围内；本文只覆盖非 display 主线。

## 当前可手工测试的稳定功能面

| 功能面 | 正式入口 / 命令 | 人工应核对的稳定信号 | repo-side 证据 / 落盘表面 | 当前阻断边界 |
| --- | --- | --- | --- | --- |
| workspace / profile 预检 | `doctor --profile <profile>` | profile、runtime contract、launcher contract、overlay readiness、blocking verdict 是否结构化输出 | `external_runtime_dependency_gate.md`、`src/med_autoscience/doctor.py` | 通过 `doctor` 不等于 external runtime gate 已解除 |
| explicit Hermes executor/proof 证据预检 | `doctor hermes-runtime --profile <profile>` 或 `doctor hermes-runtime --hermes-agent-repo-root <repo_root> --hermes-home-root <home_root>` | 显式 `hermes_agent` executor/proof 证据和旧 Hermes provenance 是否结构化收口；当前缺的是 repo、profile、proof 还是历史 gateway 语境必须可区分 | `external_runtime_dependency_gate.md`、`src/med_autoscience/hermes_runtime_contract.py`、`src/med_autoscience/controllers/hermes_runtime_check.py` | 该检查只证明显式 executor/proof 诊断状态，不能声明 MAS Full online 或 study truth ready |
| MDS / historical backend audit | `doctor backend-audit --profile <profile> --refresh` | controlled fork、`MEDICAL_FORK_MANIFEST.json`、`behavior_equivalence_gate.yaml`、workspace contract 检查是否 fail-closed | `external_runtime_dependency_gate.md`、`src/med_autoscience/controllers/backend_audit.py` | 只服务 provenance / archive import / parity；不恢复默认 MDS runtime |
| managed study runtime 只读总表面 | `study progress-projection --profile <profile> --study-id <study_id>` | `study_id` / `quest_id` / `active_run_id` 分离；`decision` / `reason`；`autonomous_runtime_notice`；`execution_owner_guard`；`publication_supervisor_state` | `progress_projection`；`studies/<study_id>/artifacts/runtime/last_launch_report.json` | `startup_boundary_gate`、`runtime_reentry_gate`、`waiting_for_user` 会 fail-closed |
| managed study runtime 受控推进 | `study ensure-runtime --profile <profile> --study-id <study_id>` | 只通过 controller action 进入 `create / resume / pause`；live managed runtime 时必须切 supervisor-only；不得旁路写 runtime-owned surface | `progress_projection`；`studies/<study_id>/artifacts/runtime/last_launch_report.json` | external runtime 未健康、human confirmation、startup boundary 未过时不得冒进 |
| 前台 progress 投影 | `study progress --profile <profile> --study-id <study_id>` | 是否把 `publication_supervisor_state`、`autonomous_runtime_notice`、`execution_owner_guard` 汇总成 controller-owned projection，而不是第二个 authority daemon | `../../runtime/projections/study_progress_projection.md`；`studies/<study_id>/artifacts/controller_decisions/latest.json` | 只读投影不能替代 runtime / controller 真相 |
| quest / runtime health diagnostic 与监管外环 | `runtime domain-health-diagnostic --quest-root <quest_root> --apply` 或 `runtime domain-health-diagnostic --runtime-root <runtime_root> --apply --request-opl-stage-attempts --profile <profile>` | 只有 `runtime_liveness_audit.status=live` 且 `worker_running=true` 且 `active_run_id!=null` 才能视为 live；否则必须进入 recovering / degraded / escalated | `domain_health_diagnostic`；quest 侧 legacy namespace `artifacts/reports/domain_health_diagnostic/`；`runtime_escalation_record.json` | 监管面可以升级但不能伪装成 cutover 已完成 |
| publication gate / publication eval latest | `publication gate --quest-root <quest_root> --apply` | `publication_supervisor_state.bundle_tasks_downstream_only=true` 时必须把 bundle/build/proofing 当作硬阻断；`publication_eval/latest.json` 必须落在 study-owned latest surface | `studies/<study_id>/artifacts/publication_eval/latest.json` | `Methods` 缺口、`endpoint_provenance_note.md` 缺失、`waiting_for_user` 等 external workspace paper truth gap 仍阻断 |
| outer-loop 决策闭环 | 通过 `progress_projection(...)` / `study_outer_loop_tick(...)` 读写 | `runtime_escalation_record.json`、`publication_eval/latest.json`、`controller_decisions/latest.json` 是否按 study-owned / quest-owned 边界分离；controller action 是否仍经受控 surface | `runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`；`studies/<study_id>/artifacts/controller_decisions/latest.json` | 当前闭环仍服务 repo-side consistency audit，不等于 external runtime gate 已放行 |
| study delivery projection | `study delivery-sync --paper-root <study_root>/paper --stage submission_minimal` | 只做 controller-authorized `paper -> manuscript` 投影，不把 external workspace 的论文真相缺口伪装成 repo-side 已解决 | `docs/runtime/control/controllers.md`；study delivery artifacts | 不负责自动清除 human-required metadata / paper truth gap |

## 人工手工测试时必须保持的 freeze truth

1. 当前 repo-side 已 absorbed；不要再伪造新的 repo 内 architecture tranche。
2. 正式研究入口仍是 `MedAutoScience`；不得直接把 `MedDeepScientist` UI / CLI / daemon HTTP API 当作研究入口。
3. `publication_eval/latest.json` 是 study-owned latest surface，不得回写到 runtime 临时目录。
4. `runtime_escalation_record.json` 与 `domain_health_diagnostic` 是 quest-owned runtime artifact / diagnostic projection，不得与 study-owned artifact 混写；`artifacts/reports/domain_health_diagnostic/` 只作为 legacy path namespace。
5. 本地未跟踪 handoff scratch 只承载机器私有 continuation，不替代 repo-tracked runtime truth。

## 当前明确不属于 repo-side 放行面的事项

下列事项仍必须保持诚实阻断，不得因为仓内文档或测试存在就宣称已经通过：

- external controlled fork 的真实 `MEDICAL_FORK_MANIFEST.json` 证据
- `ops/med-deepscientist/behavior_equivalence_gate.yaml` 放行（尤其是 `phase_25_ready=true` 与 `critical_overrides` 清理）
- external workspace contract 全绿
- 至少一个真实项目的受控热身稳定通过
- external workspace 上的 `waiting_for_user`
- `Methods` 结构缺口、`endpoint_provenance_note.md` 缺失及其他 paper truth gap
- `runtime cutover`、`end-to-end harness`、cross-repo write、physical migration、scaffold cutover

## 相关回归面

当前这份清单对应的 repo-native regression surface 至少包括：

- `tests/test_hermes_runtime_contract.py`
- `tests/test_hermes_runtime_check.py`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_study_runtime_router.py`
- `tests/test_publication_eval_latest.py`
- `tests/test_publication_eval_record.py`
- `tests/test_study_decision_record.py`
- `tests/test_publication_gate.py`

## 当前结论

如果这些 repo-side surface 通过验证，而真实继续推进仍卡在 explicit executor/proof diagnostic、historical backend audit、workspace truth 或 human-required interaction，结论必须具体写成对应 blocker。不能把它泛化成 MAS 默认运行依赖未完成，也不能用外部 runtime 证据缺失否定 MAS monolith closeout。
