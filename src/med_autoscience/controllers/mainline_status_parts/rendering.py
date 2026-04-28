from __future__ import annotations

from typing import Any

from med_autoscience.controllers.mainline_status_parts.labels import (
    _bool_label,
    _entry_point_label,
    _monorepo_status_label,
    _phase_status_label,
    _sequence_scope_label,
)


def render_mainline_phase_markdown(payload: dict[str, Any]) -> str:
    phase = dict(payload.get("phase") or {})
    active_tranche_owner_truth = dict(phase.get("active_tranche_owner_truth") or {})
    single_project_boundary = dict(phase.get("single_project_boundary") or {})
    capability_owner_boundary = dict(phase.get("capability_owner_boundary") or {})
    lines = [
        "# Mainline Phase",
        "",
        f"- 当前 program: `{payload.get('program_id')}`",
        f"- 当前阶段: `{phase.get('id')}`",
        f"- 当前状态: {_phase_status_label(phase.get('status'))}",
        f"- 当前可用性: {_bool_label(phase.get('usable_now'))}",
        f"- 当前摘要: {phase.get('summary') or 'none'}",
    ]
    if active_tranche_owner_truth:
        lines.extend(
            [
                "",
                "## Owner Truth Lanes",
                "",
                f"- 当前摘要: {active_tranche_owner_truth.get('summary') or 'none'}",
                f"- owner: {active_tranche_owner_truth.get('owner') or 'none'}",
            ]
        )
        for item in active_tranche_owner_truth.get("lanes") or []:
            if not isinstance(item, dict):
                continue
            lines.append(f"- owner lane `{item.get('lane_id')}`: {item.get('summary') or 'none'}")
        for item in active_tranche_owner_truth.get("mds_retained_roles") or []:
            if not isinstance(item, dict):
                continue
            lines.append(f"- MDS migration role `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    if capability_owner_boundary:
        lines.extend(
            [
                "",
                "## Capability Owner Boundary",
                "",
                f"- 当前摘要: {capability_owner_boundary.get('summary') or 'none'}",
                f"- owner: {capability_owner_boundary.get('owner') or 'none'}",
            ]
        )
        for item in capability_owner_boundary.get("mas_owned_capabilities") or []:
            if not isinstance(item, dict):
                continue
            lines.append(f"- MAS capability `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
        for item in capability_owner_boundary.get("mds_migration_only_roles") or []:
            if not isinstance(item, dict):
                continue
            lines.append(f"- MDS migration-only `{item.get('role_id')}`: {item.get('summary') or 'none'}")
        proof_boundary = dict(capability_owner_boundary.get("proof_and_absorb_boundary") or {})
        lines.append(f"- parity proof: {proof_boundary.get('parity_status') or 'none'}")
        lines.append(f"- physical absorb: {proof_boundary.get('physical_absorb_status') or 'none'}")
    if single_project_boundary:
        lines.extend(
            [
                "",
                "## 当前 tranche 边界",
                "",
                f"- 当前摘要: {single_project_boundary.get('summary') or 'none'}",
                f"- MAS owner modules: `{', '.join(single_project_boundary.get('mas_owner_modules') or []) or 'none'}`",
            ]
        )
        for item in single_project_boundary.get("land_now") or []:
            lines.append(f"- 当前 tranche 收口: {item}")
        for item in single_project_boundary.get("mds_retained_roles") or []:
            if not isinstance(item, dict):
                continue
            lines.append(f"- MDS 保留 `{item.get('role_id')}`: {item.get('summary') or 'none'}")
        for item in single_project_boundary.get("post_gate_only") or []:
            lines.append(f"- post-gate only: {item}")
        for item in single_project_boundary.get("not_now") or []:
            lines.append(f"- 当前不允许: {item}")
    lines.extend(["", "## 可用入口", ""])
    entry_points = list(phase.get("entry_points") or [])
    if entry_points:
        for item in entry_points:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {_entry_point_label(item.get('name'))}: `{item.get('command') or 'none'}`")
            purpose = str(item.get("purpose") or "").strip()
            if purpose:
                lines.append(f"  入口说明: {purpose}")
    else:
        lines.append("- none")
    lines.extend(["", "## 退出条件", ""])
    exit_criteria = list(phase.get("exit_criteria") or [])
    if exit_criteria:
        for item in exit_criteria:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## 相关文档", ""])
    phase_docs = list(phase.get("phase_docs") or [])
    if phase_docs:
        for item in phase_docs:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def render_mainline_status_markdown(payload: dict[str, Any]) -> str:
    current_stage = dict(payload.get("current_stage") or {})
    current_program_phase = dict(payload.get("current_program_phase") or {})
    runtime_topology = dict((payload.get("ideal_state") or {}).get("runtime_topology") or {})
    active_tranche_owner_truth = dict(payload.get("active_tranche_owner_truth") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    capability_owner_boundary = dict(payload.get("capability_owner_boundary") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    platform_target = dict(payload.get("platform_target") or {})
    lines = [
        "# Mainline Status",
        "",
        f"- 当前 program: `{payload.get('program_id')}`",
        f"- 当前主线阶段: `{current_stage.get('id')}`",
        f"- 当前状态: {_phase_status_label(current_stage.get('status'))}",
        f"- 当前判断: {current_stage.get('summary') or 'none'}",
        f"- 当前 program phase: `{current_program_phase.get('id')}`",
        f"- program phase 状态: {_phase_status_label(current_program_phase.get('status'))}",
        "",
        "## 理想目标",
        "",
        f"- 域入口归属: {runtime_topology.get('domain_gateway') or 'none'}",
        f"- 外环运行基座: {runtime_topology.get('outer_runtime_substrate_owner') or 'none'}",
        f"- 研究后端: {runtime_topology.get('research_backend') or 'none'}",
        f"- 入口形态: {runtime_topology.get('entry_shape') or 'none'}",
        "",
        "## Active Tranche Owner Truth",
        "",
        f"- 当前摘要: {active_tranche_owner_truth.get('summary') or 'none'}",
        f"- owner: {active_tranche_owner_truth.get('owner') or 'none'}",
        f"- stage: `{active_tranche_owner_truth.get('stage_id') or 'none'}`",
    ]
    for item in active_tranche_owner_truth.get("lanes") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- owner lane `{item.get('lane_id')}`: {item.get('summary') or 'none'}")
    for item in active_tranche_owner_truth.get("mds_retained_roles") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- MDS migration role `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    lines.extend(
        [
            "",
            "## Capability Owner Boundary",
            "",
            f"- 当前摘要: {capability_owner_boundary.get('summary') or 'none'}",
            f"- owner: {capability_owner_boundary.get('owner') or 'none'}",
        ]
    )
    for item in capability_owner_boundary.get("mas_owned_capabilities") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- MAS capability `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    for item in capability_owner_boundary.get("mds_migration_only_roles") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- MDS migration-only `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    proof_boundary = dict(capability_owner_boundary.get("proof_and_absorb_boundary") or {})
    lines.append(f"- parity proof: {proof_boundary.get('parity_status') or 'none'}")
    lines.append(f"- physical absorb: {proof_boundary.get('physical_absorb_status') or 'none'}")
    lines.extend(
        [
            "",
            "## Single-Project Boundary",
            "",
            f"- 当前摘要: {single_project_boundary.get('summary') or 'none'}",
            f"- MAS owner modules: `{', '.join(single_project_boundary.get('mas_owner_modules') or []) or 'none'}`",
            "",
            "## Phase 2 User Loop",
            "",
            f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}",
            f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`",
            f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`",
            "",
            "## Phase 3 Clearance",
            "",
            f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}",
            f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`",
            f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`",
        ]
    )
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    for item in phase3_clearance_lane.get("clearance_loop") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    for item in single_project_boundary.get("mds_retained_roles") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- MDS retained `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    for item in single_project_boundary.get("land_now") or []:
        lines.append(f"- 当前 tranche 落点: {item}")
    for item in single_project_boundary.get("post_gate_only") or []:
        lines.append(f"- post-gate only: {item}")
    for item in single_project_boundary.get("not_now") or []:
        lines.append(f"- 当前不允许: {item}")
    lines.extend(
        [
            "",
            "## Phase 4 Deconstruction",
            "",
            f"- 当前摘要: {phase4_backend_deconstruction.get('summary') or 'none'}",
        ]
    )
    for item in phase4_backend_deconstruction.get("substrate_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend(
        [
            "",
            "## Platform Target",
            "",
            f"- 当前平台目标: `{platform_target.get('surface_kind') or 'none'}`",
            f"- 当前摘要: {platform_target.get('summary') or 'none'}",
            f"- 当前序列范围: {_sequence_scope_label(platform_target.get('sequence_scope'))}",
            f"- 当前步骤: `{platform_target.get('current_step_id') or 'none'}`",
            f"- 当前就绪判断: {platform_target.get('current_readiness_summary') or 'none'}",
            f"- monorepo 目标状态: {_monorepo_status_label((platform_target.get('north_star_topology') or {}).get('monorepo_status'))}",
            f"- 推荐 phase 命令: `{platform_target.get('recommended_phase_command') or 'none'}`",
            "",
            "## Monorepo Sequence",
            "",
        ]
    )
    landing_sequence = list(platform_target.get("landing_sequence") or [])
    if landing_sequence:
        for item in landing_sequence:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('step_id')}` [{_phase_status_label(item.get('status'))}] / `{item.get('phase_id')}`: {item.get('summary') or 'none'}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Program Phases", ""])
    for item in payload.get("phase_ladder") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('id')}` [{_phase_status_label(item.get('status'))}]: {item.get('summary')}")
    lines.extend([
        "",
        "## Completed Tranches",
        "",
    ])
    for item in payload.get("completed_tranches") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('id')}`: {item.get('summary')}")
    lines.extend(["", "## Remaining Gaps", ""])
    for item in payload.get("remaining_gaps") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Focus", ""])
    for item in payload.get("next_focus") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Not Now", ""])
    for item in payload.get("explicitly_not_now") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Key Docs", ""])
    for item in payload.get("source_docs") or []:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"
