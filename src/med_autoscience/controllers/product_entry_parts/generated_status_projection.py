from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile

from .program_runtime_surfaces import _build_research_runtime_control_projection
from .shared import (
    TARGET_DOMAIN_ID,
    _build_shared_artifact_inventory,
    _build_shared_checkpoint_summary,
    _build_shared_progress_projection,
    _build_shared_runtime_inventory,
    _build_shared_session_continuity,
    _build_shared_task_lifecycle,
    _collect_family_human_gate_ids,
    _non_empty_text,
)


def _build_runtime_inventory_surface(
    *,
    profile: WorkspaceProfile,
    runtime: Mapping[str, Any],
    managed_runtime_contract: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
) -> dict[str, Any]:
    blocking_check_ids = list(product_entry_preflight.get("blocking_check_ids") or [])
    ready_to_try_now = bool(product_entry_preflight.get("ready_to_try_now")) and not blocking_check_ids
    availability = "ready" if ready_to_try_now else "blocked"
    health_status = "healthy" if ready_to_try_now else "attention_required"
    summary = (
        "MAS runtime inventory 已连接 MAS runtime contract 与 OPL supervision projection，当前可通过 workspace cockpit 持续监管并续跑 study。"
        if ready_to_try_now
        else "MAS runtime inventory 当前存在 blocking preflight，需要先恢复 runtime/监督前置状态。"
    )
    return _build_shared_runtime_inventory(
        summary=summary,
        runtime_owner=str(runtime.get("runtime_owner") or ""),
        domain_owner=str(runtime.get("domain_owner") or ""),
        executor_owner=str(runtime.get("executor_owner") or ""),
        substrate=str(runtime.get("runtime_substrate") or ""),
        availability=availability,
        health_status=health_status,
        status_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/domain_health_diagnostic/latest.json",
            "label": "domain health diagnostic event companion",
        },
        attention_surface={
            "ref_kind": "json_pointer",
            "ref": "/operator_loop_surface",
            "label": "workspace cockpit attention surface",
        },
        recovery_surface={
            "ref_kind": "json_pointer",
            "ref": "/managed_runtime_contract/recovery_contract_surface",
            "label": "managed runtime recovery contract surface",
        },
        workspace_binding={
            "workspace_root": str(profile.workspace_root),
            "profile_name": profile.name,
        },
        domain_projection={
            "managed_runtime_backend_id": runtime.get("managed_runtime_backend_id"),
            "managed_runtime_contract": dict(managed_runtime_contract),
            "recommended_loop_surface": operator_loop_surface.get("surface_kind"),
        },
    )


def _build_task_lifecycle_surface(
    *,
    repo_mainline: Mapping[str, Any],
    product_entry_status: Mapping[str, Any],
    product_entry_readiness: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
) -> dict[str, Any]:
    program_id = _non_empty_text(repo_mainline.get("program_id")) or TARGET_DOMAIN_ID
    stage_id = _non_empty_text(repo_mainline.get("current_stage_id")) or _non_empty_text(
        repo_mainline.get("current_program_phase_id")
    ) or "unknown-stage"
    lifecycle_status = _non_empty_text(repo_mainline.get("current_stage_status")) or _non_empty_text(
        repo_mainline.get("current_program_phase_status")
    ) or "unknown"
    lifecycle_summary = _non_empty_text(product_entry_status.get("summary")) or "MAS product entry lane is active."
    checkpoint_summary = _build_shared_checkpoint_summary(
        status="ready" if bool(product_entry_readiness.get("good_to_use_now")) else "monitoring_required",
        summary=(
            "当前 lane 已进入可执行状态，继续通过 workspace cockpit 和 study progress 维持监督与恢复闭环。"
            if bool(product_entry_readiness.get("usable_now"))
            else "当前 lane 需要先完成 blocking preflight 后再恢复常规执行。"
        ),
        checkpoint_id=f"{program_id}:{stage_id}",
        lineage_ref=dict(family_orchestration.get("checkpoint_lineage_surface") or {}),
        verification_ref=dict(family_orchestration.get("event_envelope_surface") or {}),
    )
    return _build_shared_task_lifecycle(
        task_kind="mas_product_entry_mainline",
        task_id=f"{program_id}:{stage_id}",
        status=lifecycle_status,
        summary=lifecycle_summary,
        progress_surface={
            "surface_kind": "workspace_cockpit",
            "summary": "读取 workspace attention queue、监督在线态与研究入口回路。",
            "command": str(operator_loop_surface.get("command") or ""),
            "step_id": "inspect_workspace_inbox",
            "locator_fields": ["profile_ref"],
        },
        resume_surface={
            "surface_kind": "launch_study",
            "summary": "按 study_id 启动或续跑当前研究。",
            "command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "step_id": "continue_study",
            "locator_fields": ["study_id"],
        },
        checkpoint_summary=checkpoint_summary,
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
        domain_projection={
            "current_program_phase_id": repo_mainline.get("current_program_phase_id"),
            "recommended_loop_surface": operator_loop_surface.get("surface_kind"),
            "recommended_loop_command": operator_loop_surface.get("command"),
        },
    )


def _build_session_continuity_surface(
    *,
    runtime: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    task_lifecycle: Mapping[str, Any],
    progress_projection_command: str,
) -> dict[str, Any]:
    blocking_check_ids = list(product_entry_preflight.get("blocking_check_ids") or [])
    ready_to_try_now = bool(product_entry_preflight.get("ready_to_try_now")) and not blocking_check_ids
    checkpoint_summary = dict(task_lifecycle.get("checkpoint_summary") or {})
    return _build_shared_session_continuity(
        summary=(
            "MAS session continuity 指针已就绪；恢复入口与进度/工件真相仍以 study-local durable surfaces 为 authority。"
            if ready_to_try_now
            else "MAS session continuity 当前被 preflight blocking；仍可按指针定位 durable truth，但恢复前先清障。"
        ),
        domain_agent_id="mas",
        runtime_owner=str(runtime.get("runtime_owner") or ""),
        domain_owner=str(runtime.get("domain_owner") or ""),
        executor_owner=str(runtime.get("executor_owner") or ""),
        status="ready" if ready_to_try_now else "blocked",
        progress_surface={
            "surface_kind": "study_progress",
            "summary": "读取 study progress projection（只读投影，不替代 runtime/controller 真相）。",
            "command": str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
            "step_id": "inspect_progress",
            "locator_fields": ["profile_ref", "study_id"],
        },
        artifact_surface={
            "surface_kind": "progress_projection",
            "summary": "读取 progress projection 与运行态恢复合同，必要时决定接管/重启。",
            "command": progress_projection_command,
            "step_id": "inspect_runtime_status",
            "locator_fields": ["profile_ref", "study_id"],
        },
        restore_surface={
            "surface_kind": "launch_study",
            "summary": "按 study_id 启动或续跑当前研究运行（restore 指针）。",
            "command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "step_id": "continue_study",
            "locator_fields": ["profile_ref", "study_id"],
        },
        checkpoint_summary=checkpoint_summary if checkpoint_summary else None,
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
        domain_projection={
            "runtime_supervision_path_template": "studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json",
            "publication_eval_path_template": "studies/<study_id>/artifacts/publication_eval/latest.json",
            "controller_decision_path_template": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        },
    )


def _build_progress_projection_surface(
    *,
    profile: WorkspaceProfile,
    repo_mainline: Mapping[str, Any],
    product_entry_status: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    product_entry_readiness: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    progress_projection_command: str,
) -> dict[str, Any]:
    headline = _non_empty_text(product_entry_status.get("summary")) or "MAS 当前保持 repo-owned product entry continuity。"
    next_step = _non_empty_text(operator_loop_surface.get("command")) or "none"
    latest_update = _non_empty_text(repo_mainline.get("current_stage_summary")) or _non_empty_text(
        repo_mainline.get("current_program_phase_summary")
    ) or headline
    blocking_check_ids = list(product_entry_preflight.get("blocking_check_ids") or [])
    attention_items = list(product_entry_status.get("next_focus") or [])
    if blocking_check_ids:
        attention_items.extend(f"preflight_blocking::{item}" for item in blocking_check_ids)
    return _build_shared_progress_projection(
        headline=headline,
        latest_update=latest_update,
        next_step=next_step,
        status_summary=_non_empty_text(product_entry_readiness.get("summary")) or "none",
        current_status=_non_empty_text(product_entry_readiness.get("verdict")) or "runtime_ready_not_standalone_product",
        runtime_status="ready" if bool(product_entry_preflight.get("ready_to_try_now")) and not blocking_check_ids else "blocked",
        progress_surface={
            "surface_kind": "workspace_cockpit",
            "summary": "读取 workspace attention queue 与监督在线态（progress 指针）。",
            "command": next_step,
            "step_id": "open_loop",
            "locator_fields": ["profile_ref"],
        },
        artifact_surface={
            "surface_kind": "progress_projection",
            "summary": "按 study_id 读取 runtime 恢复合同与运行态（artifact/restore 辅助指针）。",
            "command": progress_projection_command,
            "step_id": "inspect_runtime_status",
            "locator_fields": ["profile_ref", "study_id"],
        },
        inspect_paths=[str(profile.workspace_root), str(profile.runtime_root), "studies/<study_id>/artifacts"],
        attention_items=attention_items,
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
        domain_projection={
            "recommended_restore_command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "recommended_progress_command": str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
            "research_runtime_control_projection": _build_research_runtime_control_projection(
                resume_command=str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
                check_progress_command=str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
                check_runtime_status_command=progress_projection_command,
                surface_kind="research_runtime_control_projection",
            ),
        },
    )


def _build_artifact_inventory_surface(
    *,
    profile: WorkspaceProfile,
    progress_projection: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    progress_projection_command: str,
) -> dict[str, Any]:
    supporting_files = [
        {
            "file_id": "artifact_runtime_proof",
            "label": "Artifact runtime proof",
            "path": "studies/<study_id>/manuscript/delivery_manifest.json",
            "summary": "canonical-source rebuild proof consumed by study_progress artifact_runtime_proof.",
        },
        {
            "file_id": "submission_hygiene_truth",
            "label": "Submission hygiene truth",
            "path": "study_progress.submission_hygiene_truth",
            "summary": "aggregates submission minimal, publication surface QC, internal language leakage, citation/numeric/display gates, and artifact proof.",
        },
        {
            "file_id": "task_intake_latest",
            "label": "Study task intake (latest)",
            "path": "studies/<study_id>/artifacts/controller/task_intake/latest.json",
            "summary": "durable task intake truth (task_id/intent/entry_mode/return_surface_contract).",
        },
        {
            "file_id": "domain_health_diagnostic_latest",
            "label": "Domain health diagnostic (latest)",
            "path": "studies/<study_id>/artifacts/domain_health_diagnostic/latest.json",
            "summary": "domain health diagnostic event companion for supervision freshness.",
        },
        {
            "file_id": "runtime_supervision_latest",
            "label": "Runtime supervision (latest)",
            "path": "studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json",
            "summary": "MAS domain runtime projection refs; generic scheduler and lifecycle ownership stay in OPL.",
        },
        {
            "file_id": "publication_eval_latest",
            "label": "Publication eval (latest)",
            "path": "studies/<study_id>/artifacts/publication_eval/latest.json",
            "summary": "publication eval truth (publishability/quality closure state).",
        },
        {
            "file_id": "medical_manuscript_blueprint",
            "label": "Medical manuscript blueprint",
            "path": "studies/<study_id>/paper/medical_manuscript_blueprint.json",
            "summary": "pre-draft clinical argument blueprint for medical-journal prose generation.",
        },
        {
            "file_id": "medical_journal_style_corpus",
            "label": "Medical journal style corpus",
            "path": "studies/<study_id>/paper/medical_journal_style_corpus.json",
            "summary": "reusable style principles and short paraphrased exemplars for medical original-research voice.",
        },
        {
            "file_id": "medical_prose_review_request",
            "label": "AI medical prose review request",
            "path": "studies/<study_id>/artifacts/publication_eval/medical_prose_review_request.json",
            "summary": "AI reviewer input bundle; mechanical flags are evidence snippets only.",
        },
        {
            "file_id": "medical_prose_review",
            "label": "AI medical prose review",
            "path": "studies/<study_id>/artifacts/publication_eval/medical_prose_review.json",
            "summary": "AI-owned subjective manuscript prose verdict and representative rewrites.",
        },
        {
            "file_id": "retrospective_medical_prose_audit",
            "label": "Retrospective medical prose audit",
            "path": "studies/<study_id>/artifacts/publication_eval/retrospective_medical_prose_audit.json",
            "summary": "NF-PitNET 003 / DPCC 003 / DPCC 004 replay audit fixture for prose-quality regression.",
        },
        {
            "file_id": "controller_decisions_latest",
            "label": "Controller decisions (latest)",
            "path": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "summary": "controller decision truth (gate decisions / interventions / followthrough).",
        },
    ]
    return _build_shared_artifact_inventory(
        deliverable_files=[],
        supporting_files=supporting_files,
        workspace_path=str(profile.workspace_root),
        progress_headline=_non_empty_text(progress_projection.get("headline")) or None,
        artifact_surface={
            "surface_kind": "progress_projection",
            "summary": "按 study_id 读取 progress projection 与运行态恢复合同。",
            "command": progress_projection_command,
            "step_id": "inspect_runtime_status",
            "locator_fields": ["profile_ref", "study_id"],
        },
        inspect_paths=[str(profile.workspace_root), "studies/<study_id>/artifacts", str(profile.runtime_root)],
        domain_projection={
            "recommended_restore_command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "recommended_progress_command": str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
        },
    )


def _build_skill_runtime_continuity_envelope(
    *,
    runtime: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    session_continuity: Mapping[str, Any],
    progress_projection: Mapping[str, Any],
    artifact_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    resume_contract = dict(family_orchestration.get("resume_contract") or {})
    restore_surface = dict(session_continuity.get("restore_surface") or {})
    session_progress_surface = dict(session_continuity.get("progress_surface") or {})
    artifact_surface = dict(artifact_inventory.get("artifact_surface") or {})
    progress_domain_projection = dict(progress_projection.get("domain_projection") or {})
    restore_point_surface_ref = "/session_continuity/restore_surface"
    if isinstance(progress_domain_projection.get("research_runtime_control_projection"), Mapping):
        restore_point_surface_ref = (
            "/progress_projection/domain_projection/research_runtime_control_projection/restore_point_surface"
        )
    return {
        "surface_kind": "skill_runtime_continuity",
        "runtime_owner": str(runtime.get("runtime_owner") or ""),
        "domain_owner": str(runtime.get("domain_owner") or ""),
        "executor_owner": str(runtime.get("executor_owner") or ""),
        "session_locator_field": str(resume_contract.get("session_locator_field") or ""),
        "session_surface_ref": "/session_continuity",
        "progress_surface_ref": "/progress_projection/progress_surface",
        "artifact_surface_ref": "/artifact_inventory/artifact_surface",
        "restore_point_surface_ref": restore_point_surface_ref,
        "recommended_resume_command": str(restore_surface.get("command") or ""),
        "recommended_progress_command": str(session_progress_surface.get("command") or ""),
        "recommended_artifact_command": str(artifact_surface.get("command") or ""),
    }




__all__ = [
    "_build_artifact_inventory_surface",
    "_build_progress_projection_surface",
    "_build_runtime_inventory_surface",
    "_build_session_continuity_surface",
    "_build_skill_runtime_continuity_envelope",
    "_build_task_lifecycle_surface",
]
