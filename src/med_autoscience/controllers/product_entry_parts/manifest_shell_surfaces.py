from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .program_surfaces import _build_product_entry_start
from .shared import (
    PRODUCT_ENTRY_STATUS_KIND,
    TARGET_DOMAIN_ID,
    _build_shared_handoff,
    _build_shared_operator_loop_action_catalog,
    _build_shared_product_entry_overview,
    _build_shared_product_entry_quickstart,
    _build_shared_product_entry_readiness,
    _build_shared_product_entry_resume_surface,
    _build_shared_product_entry_shell_catalog,
    _build_shared_product_entry_shell_linked_surface,
    _collect_family_human_gate_ids,
    _json_surface_command,
    _product_entry_shell_from_action_catalog,
)


def _inspection_package_operator_authority() -> dict[str, Any]:
    return {
        "authority": "human_inspection_only",
        "can_write_current_package": False,
        "can_write_submission_minimal": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
    }


def _opl_generated_product_entry_status_surface(*, profile_arg: str) -> dict[str, Any]:
    command = f"opl app product-entry-status --agent med-autoscience --profile {profile_arg}"
    return {
        "command": _json_surface_command(command),
        "purpose": "通过 OPL generated product-entry status 打开 MAS domain refs 投影。",
        "surface_kind": PRODUCT_ENTRY_STATUS_KIND,
        "authority_boundary": {
            "host_owner": "one-person-lab",
            "domain_truth_owner": "MedAutoScience",
            "helper_write_policy": "no_domain_truth_writes",
            "mas_repo_local_default_caller": False,
        },
    }


def _opl_hosted_workspace_workbench_surface(*, profile_arg: str) -> dict[str, Any]:
    command = f"opl app workbench --agent med-autoscience --profile {profile_arg}"
    return {
        "command": _json_surface_command(command),
        "purpose": "通过 OPL hosted workbench 打开 MAS workspace refs 投影。",
        "surface_kind": "workspace_cockpit",
        "authority_boundary": {
            "host_owner": "one-person-lab",
            "domain_truth_owner": "MedAutoScience",
            "helper_write_policy": "no_domain_truth_writes",
            "mas_repo_local_default_caller": False,
        },
    }


def _build_manifest_shell_surfaces(
    *,
    prefix: str,
    profile_arg: str,
    action_catalog: Mapping[str, Any],
    mainline_payload: Mapping[str, Any],
    mainline_snapshot: Mapping[str, Any],
    build_family_product_entry_orchestration: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    progress_projection_command = _json_surface_command(
        f"{prefix} study progress --profile {profile_arg} --study-id <study_id>"
    )
    product_entry_shell = _build_shared_product_entry_shell_catalog(
        _product_entry_shell_from_action_catalog(action_catalog)
    )
    product_entry_shell["product_entry_status"] = _opl_generated_product_entry_status_surface(
        profile_arg=profile_arg
    )
    product_entry_shell["workspace_cockpit"] = _opl_hosted_workspace_workbench_surface(
        profile_arg=profile_arg
    )
    shared_handoff = _build_shared_handoff(
        direct_entry_builder_command=(
            f"{prefix} build-product-entry --profile {profile_arg} "
            "--study-id <study_id> --entry-mode direct"
        ),
        opl_handoff_builder_command=(
            f"{prefix} build-product-entry --profile {profile_arg} "
            "--study-id <study_id> --entry-mode opl-handoff"
        ),
    )
    operator_loop_actions = _build_shared_operator_loop_action_catalog({
        "open_loop": {
            "command": product_entry_shell["workspace_cockpit"]["command"],
            "surface_kind": "workspace_cockpit",
            "summary": "先进入 OPL hosted workbench 中的 MAS workspace refs 投影。",
            "requires": [],
        },
        "submit_task": {
            "command": product_entry_shell["submit_study_task"]["command"],
            "surface_kind": "study_task_intake",
            "summary": "先把新的研究任务写成 durable study task intake。",
            "requires": ["study_id", "task_intent"],
        },
        "continue_study": {
            "command": product_entry_shell["launch_study"]["command"],
            "surface_kind": "launch_study",
            "summary": "创建或恢复某个 study runtime，并回到当前研究主线。",
            "requires": ["study_id"],
        },
        "inspect_progress": {
            "command": product_entry_shell["study_progress"]["command"],
            "surface_kind": "study_progress",
            "summary": "读取某个 study 的当前阶段、阻塞和监督 freshness。",
            "requires": ["study_id"],
        },
        "export_inspection_package": {
            "command": product_entry_shell["export_inspection_package"]["command"],
            "surface_kind": "publication_inspection_package_export",
            "summary": product_entry_shell["export_inspection_package"]["purpose"],
            "requires": ["study_id"],
            **_inspection_package_operator_authority(),
        },
    })
    family_orchestration = build_family_product_entry_orchestration(
        graph_id="mas_workspace_product_entry_study_runtime_graph",
        target_domain_id=TARGET_DOMAIN_ID,
        graph_kind="study_runtime_orchestration",
        graph_version="2026-04-13",
        nodes=[
            {
                "node_id": "step:open_product_entry",
                "node_kind": "operator_step",
                "title": "Open research product entry",
                "surface_kind": PRODUCT_ENTRY_STATUS_KIND,
            },
            {
                "node_id": "step:submit_task",
                "node_kind": "operator_step",
                "title": "Write durable study task",
                "surface_kind": "study_task_intake",
                "produces_checkpoint": True,
            },
            {
                "node_id": "step:continue_study",
                "node_kind": "operator_step",
                "title": "Continue or relaunch a study",
                "surface_kind": "launch_study",
                "produces_checkpoint": True,
            },
            {
                "node_id": "step:inspect_progress",
                "node_kind": "operator_step",
                "title": "Inspect current study progress",
                "surface_kind": "study_progress",
                "produces_checkpoint": True,
            },
            {
                "node_id": "step:export_inspection_package",
                "node_kind": "operator_step",
                "title": "Export human inspection package",
                "surface_kind": "publication_inspection_package_export",
                "produces_checkpoint": False,
            },
        ],
        edges=[
            {
                "from": "step:open_product_entry",
                "to": "step:submit_task",
                "on": "new_task",
            },
            {
                "from": "step:open_product_entry",
                "to": "step:continue_study",
                "on": "resume_study",
            },
            {
                "from": "step:open_product_entry",
                "to": "step:inspect_progress",
                "on": "inspect_status",
            },
            {
                "from": "step:submit_task",
                "to": "step:continue_study",
                "on": "task_written",
            },
            {
                "from": "step:continue_study",
                "to": "step:inspect_progress",
                "on": "progress_refresh",
            },
            {
                "from": "step:inspect_progress",
                "to": "step:export_inspection_package",
                "on": "human_style_review_requested",
            },
        ],
        entry_nodes=["step:open_product_entry"],
        exit_nodes=["step:continue_study", "step:inspect_progress", "step:export_inspection_package"],
        human_gates=[
            {
                "gate_id": "study_user_decision_gate",
                "trigger_nodes": ["step:continue_study"],
                "blocking": True,
            },
            {
                "gate_id": "publication_release_gate",
                "trigger_nodes": ["step:inspect_progress"],
                "blocking": True,
            },
        ],
        checkpoint_nodes=[
            "step:submit_task",
            "step:continue_study",
            "step:inspect_progress",
        ],
        human_gate_previews=[
            {
                "gate_id": "study_user_decision_gate",
                "title": "Study user decision gate",
            },
            {
                "gate_id": "publication_release_gate",
                "title": "Publication release gate",
            },
        ],
        resume_surface_kind="launch_study",
        session_locator_field="study_id",
        checkpoint_locator_field="controller_decision_path",
        action_graph_ref={
            "ref_kind": "json_pointer",
            "ref": "/family_orchestration/action_graph",
            "label": "mas family action graph",
        },
        event_envelope_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/domain_health_diagnostic/latest.json",
            "label": "domain health diagnostic event companion",
        },
        checkpoint_lineage_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "label": "controller checkpoint lineage companion",
        },
    )
    product_entry_quickstart = _build_shared_product_entry_quickstart(
        summary=(
            "先从 product entry status 进入当前 research product entry，"
            "需要新任务时先写 durable study task intake，再继续某个 study 或读取进度。"
        ),
        recommended_step_id="open_product_entry",
        steps=[
            {
                "step_id": "open_product_entry",
                "title": "打开 MAS 入口状态",
                "command": product_entry_shell["product_entry_status"]["command"],
                "surface_kind": PRODUCT_ENTRY_STATUS_KIND,
                "summary": product_entry_shell["product_entry_status"]["purpose"],
                "requires": [],
            },
            {
                "step_id": "submit_task",
                "title": "给 study 下 durable 任务",
                "command": product_entry_shell["submit_study_task"]["command"],
                "surface_kind": "study_task_intake",
                "summary": operator_loop_actions["submit_task"]["summary"],
                "requires": list(operator_loop_actions["submit_task"]["requires"]),
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑 study",
                "command": product_entry_shell["launch_study"]["command"],
                "surface_kind": "launch_study",
                "summary": operator_loop_actions["continue_study"]["summary"],
                "requires": list(operator_loop_actions["continue_study"]["requires"]),
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看研究进度",
                "command": product_entry_shell["study_progress"]["command"],
                "surface_kind": "study_progress",
                "summary": operator_loop_actions["inspect_progress"]["summary"],
                "requires": list(operator_loop_actions["inspect_progress"]["requires"]),
            },
            {
                "step_id": "export_inspection_package",
                "title": "导出人工检查包",
                "command": product_entry_shell["export_inspection_package"]["command"],
                "surface_kind": "publication_inspection_package_export",
                "summary": operator_loop_actions["export_inspection_package"]["summary"],
                "requires": list(operator_loop_actions["export_inspection_package"]["requires"]),
            },
        ],
        resume_contract=dict(family_orchestration["resume_contract"]),
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
    )
    product_entry_quickstart["steps"][-1].update(_inspection_package_operator_authority())
    product_entry_start = _build_product_entry_start(
        product_entry_shell=product_entry_shell,
        operator_loop_actions=operator_loop_actions,
        family_orchestration=family_orchestration,
    )
    product_entry_status_command = product_entry_shell["product_entry_status"]["command"]
    product_entry_overview = {
        "surface_kind": "product_entry_overview",
        "summary": (
            mainline_snapshot.get("current_stage_summary")
            or mainline_snapshot.get("current_program_phase_summary")
        ),
        "product_entry_command": product_entry_status_command,
        "entry_status_command": product_entry_status_command,
        "recommended_command": product_entry_shell["workspace_cockpit"]["command"],
        "operator_loop_command": product_entry_shell["workspace_cockpit"]["command"],
        "progress_surface": {
            "surface_kind": "study_progress",
            "command": product_entry_shell["study_progress"]["command"],
            "step_id": "inspect_progress",
        },
        "resume_surface": _build_shared_product_entry_resume_surface(
            command=product_entry_shell["launch_study"]["command"],
            resume_contract=family_orchestration["resume_contract"],
        ),
        "recommended_step_id": product_entry_quickstart["recommended_step_id"],
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
        "remaining_gaps_count": len(list(mainline_payload.get("remaining_gaps") or [])),
        "human_gate_ids": list(product_entry_quickstart["human_gate_ids"]),
    }
    product_entry_readiness = _build_shared_product_entry_readiness(
        verdict="runtime_ready_not_standalone_product",
        usable_now=True,
        good_to_use_now=False,
        fully_automatic=False,
        summary=(
            "当前可以作为 research entry_status / CLI 主线使用，并通过稳定的 runtime 回路持续推进研究；"
            "但还不是成熟的独立医学产品入口。"
        ),
        recommended_start_surface=PRODUCT_ENTRY_STATUS_KIND,
        recommended_start_command=product_entry_shell["product_entry_status"]["command"],
        recommended_loop_surface="workspace_cockpit",
        recommended_loop_command=product_entry_shell["workspace_cockpit"]["command"],
        blocking_gaps=[
            "独立医学产品入口 / hosted product entry 仍未 landed。",
            "更多 workspace / host 的真实 clearance 与 study-local blocker 收口仍在继续。",
        ],
    )
    product_entry_surface = _build_shared_product_entry_shell_linked_surface(
        shell_key="product_entry_status",
        shell_surface=product_entry_shell["product_entry_status"],
        summary=product_entry_shell["product_entry_status"]["purpose"],
    )
    operator_loop_surface = _build_shared_product_entry_shell_linked_surface(
        shell_key="workspace_cockpit",
        shell_surface=product_entry_shell["workspace_cockpit"],
        summary=product_entry_shell["workspace_cockpit"]["purpose"],
    )
    product_entry_status = {
        "summary": mainline_snapshot.get("current_stage_summary")
        or mainline_snapshot.get("current_program_phase_summary"),
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
        "remaining_gaps_count": len(list(mainline_payload.get("remaining_gaps") or [])),
    }
    return {
        "progress_projection_command": progress_projection_command,
        "product_entry_shell": product_entry_shell,
        "shared_handoff": shared_handoff,
        "operator_loop_actions": operator_loop_actions,
        "family_orchestration": family_orchestration,
        "product_entry_quickstart": product_entry_quickstart,
        "product_entry_start": product_entry_start,
        "product_entry_overview": product_entry_overview,
        "product_entry_readiness": product_entry_readiness,
        "product_entry_surface": product_entry_surface,
        "operator_loop_surface": operator_loop_surface,
        "product_entry_status": product_entry_status,
    }


__all__ = [
    "_build_manifest_shell_surfaces",
    "_inspection_package_operator_authority",
]
