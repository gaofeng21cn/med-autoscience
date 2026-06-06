# Medical paper readiness surface currentness SSOT closeout 2026-06-06

Owner: `MedAutoScience`
Purpose: `medical_paper_readiness_surface_currentness_ssot_closeout`
State: `history_provenance`
Machine boundary: 本文是人读文档治理 closeout。当前 readiness surface、owner dispatch、source identity、study truth、owner receipt、typed blocker 和 live paper-line truth 继续归 `contracts/`、源码、测试、runtime/controller durable surfaces、真实 workspace artifact、owner receipts 和 typed blockers。

## Scope

本轮治理 `complete_medical_paper_readiness_surface` 的 currentness：先确定当前 readiness surface 的 Single Source of Truth，再把 active plan 内旧的历史增量值对齐到当前状态，并修正已有 request / dispatch packet 对 readiness `surface_key` identity 的传播。

本轮改变 MAS source / focused tests / docs。它不写真实 runtime state、study workspace、owner receipt、typed blocker、paper/package artifact、publication eval、`current_package` 或 OPL provider state。

## SSOT

当前 readiness surface 的机器真相由以下面共同持有：

- `src/med_autoscience/controllers/owner_route_handoff_parts/export_study_projection.py`：从 `controller_decisions.readiness_next_action` 投影 `current_owner_action.surface_key`。
- `src/med_autoscience/controllers/owner_route_handoff_parts/default_executor_dispatch_tasks.py`：把 readiness `surface_key` 纳入 default-executor `readiness_surface_identity`、`source_fingerprint` 与 `dedupe_key`。
- `src/med_autoscience/controllers/domain_action_request_materializer.py` 与 `src/med_autoscience/controllers/domain_action_request_materializer_parts/supervisor_request_packets.py`：把 readiness `readiness_surface_identity` 写入 supervisor request task / handoff packet。
- `src/med_autoscience/controllers/domain_owner_action_dispatch_parts/action_execution/medical_paper_readiness.py`：owner dispatch 优先使用 `readiness_surface_identity.surface_key`，避免 stale top-level `surface_key` 回写旧 surface。
- `tests/test_cli_cases/owner_route_handoff_command_cases/default_executor_dispatch_currentness_cases.py`：回归证明 surface 从 `bounded_analysis_candidate_board` 变成 `stop_loss_memo` 时，default-executor source identity 和 dedupe key 必须变化。
- `tests/domain_action_request_materializer_cases/test_stage_artifact_publication_handoff.py` 与 `tests/test_domain_owner_action_dispatch_cases/medical_paper_readiness_dispatch.py`：回归证明 request packet、dispatch packet、immutable dispatch packet 和 owner execution 都使用同一 readiness identity。
- `docs/status.md`：当前人读摘要，记录 DM002 当前 `ready_count=5/13`、下一 surface 为 `stop_loss_memo`，DM003 当前 `ready_count=0/13`、下一 surface 为 `literature_provider_runtime`。

`docs/active/mas-ideal-state-gap-plan.md` 是 MAS single Active Truth plan，但它不直接胜过上述机器面和当前状态摘要中的 live readiness 值；它必须把旧增量值折回当前 owner surface 口径。

## Classification

| Section | Classification | Outcome |
| --- | --- | --- |
| `docs/status.md` readiness summary | `covered_by_ssot` | 保留为 current-state 摘要；它不声明 DM002/DM003 live owner closeout、publication-ready、submission-ready、quality verdict 或 package freshness。 |
| `docs/active/mas-ideal-state-gap-plan.md` DM002 `ready_count=4/13` / `bounded_analysis_candidate_board` wording | `conflicts_with_ssot` | 更新为 `ready_count=5/13` / `stop_loss_memo`，并记录 readiness `surface_key` 已进入 source identity。 |
| readiness request / dispatch packet identity | `more_specific_detail` | 修正已有 request task、handoff packet、latest dispatch 和 immutable dispatch packet 的 identity propagation；不新增兼容 alias、wrapper 或第二入口。 |
| stale top-level dispatch `surface_key` replay | `stale_or_superseded` | owner dispatch 以 `readiness_surface_identity.surface_key` 为准，旧 top-level `surface_key` 不能覆盖当前 readiness next action。 |
| `docs/decisions.md` owner-delta result decision | `more_specific_detail` | 保留。它定义 `owner_delta_result`、stable typed blocker 与 closeout binding 语义，不负责当前 live surface 数值。 |
| Prior progress-projection / helper-shim closeouts | `history_or_provenance` | 保留为相邻历史 lane，不作为本主题的当前 truth owner。 |
| DM002/DM003 live owner run、paper-line execution、publication/package readiness | `out_of_scope` | 仍需真实 owner run 产出 StageRun/source/idempotency 匹配的 owner receipt、quality gate receipt、typed blocker、human gate 或 route-back evidence。 |

## Changes

- `docs/active/mas-ideal-state-gap-plan.md` 对齐 DM002 当前 readiness 值：`ready_count=5/13`，下一 surface 为 `stop_loss_memo`。
- 同一 active plan 把 `bounded_analysis_candidate_board` 归入已证明的 owner surface follow-through，并把 readiness `surface_key` source identity 作为当前 owner-dispatch currentness 边界。
- `docs/history/program/README.md` 增加本 closeout 索引。
- `domain_action_request_materializer` / `supervisor_request_packets` 让 readiness request task、handoff packet 和 persisted request packet 携带 `readiness_surface_identity`。
- `default_executor_dispatch_tasks` 在生成 OPL default-executor task 前把当前 `readiness_surface_identity` 写入已有 latest / immutable dispatch packet，使 `dispatch_ref` 指向的实体 packet 与 task identity 一致。
- `medical_paper_readiness` owner dispatch 优先按 identity surface 执行，防止旧 dispatch 的 stale `surface_key` 重放。

## Verification

本轮验证入口：

```bash
rtk git diff --check -- docs/active/mas-ideal-state-gap-plan.md docs/history/program/README.md docs/history/program/medical_paper_readiness_surface_currentness_ssot_closeout_2026_06_06.md src/med_autoscience/controllers/domain_action_request_materializer.py src/med_autoscience/controllers/domain_action_request_materializer_parts/supervisor_request_packets.py src/med_autoscience/controllers/domain_owner_action_dispatch_parts/action_execution/medical_paper_readiness.py src/med_autoscience/controllers/owner_route_handoff_parts/default_executor_dispatch_tasks.py tests/domain_action_request_materializer_cases/test_stage_artifact_publication_handoff.py tests/test_cli_cases/owner_route_handoff_command_cases/default_executor_dispatch_currentness_cases.py tests/test_domain_owner_action_dispatch_cases/medical_paper_readiness_dispatch.py
rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs/active/mas-ideal-state-gap-plan.md docs/history/program/README.md docs/history/program/medical_paper_readiness_surface_currentness_ssot_closeout_2026_06_06.md src/med_autoscience/controllers/domain_action_request_materializer.py src/med_autoscience/controllers/domain_action_request_materializer_parts/supervisor_request_packets.py src/med_autoscience/controllers/domain_owner_action_dispatch_parts/action_execution/medical_paper_readiness.py src/med_autoscience/controllers/owner_route_handoff_parts/default_executor_dispatch_tasks.py tests/domain_action_request_materializer_cases/test_stage_artifact_publication_handoff.py tests/test_cli_cases/owner_route_handoff_command_cases/default_executor_dispatch_currentness_cases.py tests/test_domain_owner_action_dispatch_cases/medical_paper_readiness_dispatch.py
rtk rg -n "ready_count=4/13|DM002 当前 .*bounded_analysis_candidate_board|下一 surface 为 `bounded_analysis_candidate_board`" docs/status.md docs/active/mas-ideal-state-gap-plan.md
rtk scripts/run-pytest-clean.sh tests/test_cli_cases/owner_route_handoff_command.py -q -k readiness_surface_key_changes_default_executor_source_identity
rtk scripts/run-pytest-clean.sh tests/domain_action_request_materializer_cases/test_stage_artifact_publication_handoff.py -q -k medical_paper_readiness
rtk scripts/run-pytest-clean.sh tests/test_domain_owner_action_dispatch_cases/medical_paper_readiness_dispatch.py -q -k "prefers_readiness_identity_over_stale_surface_key or materializes_provider_payload"
rtk /Users/gaofeng/.local/bin/opl-doc-doctor doctor . --format json
```

Expected active-doc stale-currentness scan: no matches in `docs/status.md` or `docs/active/mas-ideal-state-gap-plan.md`.

## Remaining Risk

本轮只关闭文档当前性冲突和 SSOT foldback。DM002 / DM003 live owner closeout 仍开放：需要 owner run 继续补当前 readiness surface，并产出可验证 owner receipt、quality gate receipt、typed blocker、human gate 或 route-back evidence。该 evidence tail 不能由文档、doctor、dry-run blocker、source identity、provider completion 或 refs-only projection 代签。
