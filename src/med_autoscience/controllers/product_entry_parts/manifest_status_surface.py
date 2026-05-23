from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .boundary_surfaces import (
    _capability_owner_boundary_payload,
    _single_project_boundary_payload,
    _validate_capability_owner_boundary,
    _validate_single_project_boundary,
)
from .manifest_projection_compaction import (
    _manifest_open_auto_research_projection,
    _manifest_opl_current_control_state_handoff_dashboard,
)
from .shared_base import _gate_clearing_followthrough_summary
from .shared_labels import _non_empty_text
from .workspace_attention import (
    _autonomy_soak_focus,
    _gate_clearing_followthrough_focus,
    _operator_status_summary,
    _quality_execution_focus,
    _quality_repair_followthrough_focus,
    _quality_review_followthrough_focus,
    _same_line_route_focus,
)


def _workspace_medical_paper_research_loop_manifest(workspace_cockpit: Mapping[str, Any]) -> dict[str, Any]:
    return dict(workspace_cockpit.get("medical_paper_research_loop_state") or {})


def _workspace_delivery_inspection_manifest(workspace_cockpit: Mapping[str, Any]) -> dict[str, Any]:
    return dict(workspace_cockpit.get("delivery_inspection_state") or {})


def _build_product_entry_status_operator_brief(
    *,
    manifest: Mapping[str, Any],
    workspace_cockpit: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    product_entry_quickstart: Mapping[str, Any],
) -> dict[str, Any]:
    workspace_operator_brief = dict(workspace_cockpit.get("operator_brief") or {})
    workspace_attention_queue = list(workspace_cockpit.get("attention_queue") or [])
    top_attention = dict(workspace_attention_queue[0] or {}) if workspace_attention_queue else {}
    top_attention_status_card = dict(top_attention.get("operator_status_card") or {})

    if not bool(product_entry_preflight.get("ready_to_try_now")):
        return {
            "surface_kind": "product_entry_status_operator_brief",
            "verdict": "preflight_blocked",
            "summary": _non_empty_text(product_entry_preflight.get("summary"))
            or "当前还没有通过前置检查，先不要直接进入研究主线。",
            "should_intervene_now": True,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "preflight_check",
            "recommended_command": _non_empty_text(product_entry_preflight.get("recommended_check_command")),
        }

    if _non_empty_text(workspace_operator_brief.get("verdict")) == "attention_required":
        operator_brief = {
            "surface_kind": "product_entry_status_operator_brief",
            "verdict": "attention_required",
            "summary": _operator_status_summary(top_attention_status_card)
            or _non_empty_text((top_attention.get("quality_repair_followthrough") or {}).get("summary"))
            or _gate_clearing_followthrough_summary(top_attention.get("gate_clearing_followthrough"))
            or _non_empty_text(workspace_operator_brief.get("summary"))
            or "当前 workspace 已有需要优先处理的 attention item。",
            "should_intervene_now": True,
            "focus_scope": _non_empty_text(workspace_operator_brief.get("focus_scope")) or "workspace",
            "focus_study_id": _non_empty_text(workspace_operator_brief.get("focus_study_id")),
            "recommended_step_id": _non_empty_text(top_attention.get("recommended_step_id"))
            or _non_empty_text(workspace_operator_brief.get("recommended_step_id"))
            or "open_workspace_cockpit",
            "recommended_command": _non_empty_text(top_attention.get("recommended_command"))
            or _non_empty_text(workspace_operator_brief.get("recommended_command"))
            or _non_empty_text((manifest.get("summary") or {}).get("recommended_command")),
        }
        current_focus = _non_empty_text(top_attention_status_card.get("current_focus")) or _non_empty_text(
            workspace_operator_brief.get("current_focus")
        ) or _quality_repair_followthrough_focus(top_attention) or _gate_clearing_followthrough_focus(top_attention) or _same_line_route_focus(top_attention) or _quality_execution_focus(top_attention) or _quality_review_followthrough_focus(top_attention) or _autonomy_soak_focus(top_attention)
        if current_focus is not None:
            operator_brief["current_focus"] = current_focus
        next_confirmation_signal = _non_empty_text(top_attention_status_card.get("next_confirmation_signal")) or _non_empty_text(
            workspace_operator_brief.get("next_confirmation_signal")
        )
        if next_confirmation_signal is not None:
            operator_brief["next_confirmation_signal"] = next_confirmation_signal
        return operator_brief

    if _non_empty_text(workspace_operator_brief.get("verdict")) == "ready_for_task":
        return {
            "surface_kind": "product_entry_status_operator_brief",
            "verdict": "ready_for_task",
            "summary": "当前 workspace 已 ready，下一步先给目标 study 下任务，再启动研究。",
            "should_intervene_now": False,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "submit_task",
            "recommended_command": _non_empty_text(workspace_operator_brief.get("recommended_command"))
            or _non_empty_text(
                ((product_entry_quickstart.get("steps") or [None, {}])[1] or {}).get("command")
            ),
        }

    operator_brief = {
        "surface_kind": "product_entry_status_operator_brief",
        "verdict": "monitor_only",
        "summary": _non_empty_text(workspace_operator_brief.get("summary"))
        or "当前先进入 workspace cockpit，持续看进度、告警和恢复建议。",
        "should_intervene_now": bool(workspace_operator_brief.get("should_intervene_now")),
        "focus_scope": _non_empty_text(workspace_operator_brief.get("focus_scope")) or "workspace",
        "focus_study_id": _non_empty_text(workspace_operator_brief.get("focus_study_id")),
        "recommended_step_id": "open_workspace_cockpit",
        "recommended_command": _non_empty_text((manifest.get("summary") or {}).get("recommended_command")),
    }
    current_focus = _non_empty_text(workspace_operator_brief.get("current_focus")) or _quality_review_followthrough_focus(
        workspace_operator_brief
    ) or _quality_repair_followthrough_focus(workspace_operator_brief) or _gate_clearing_followthrough_focus(workspace_operator_brief) or _same_line_route_focus(workspace_operator_brief) or _autonomy_soak_focus(workspace_operator_brief)
    if current_focus is not None:
        operator_brief["current_focus"] = current_focus
    return operator_brief


def build_product_entry_status_payload(
    *,
    manifest: Mapping[str, Any],
    workspace_cockpit: Mapping[str, Any],
    schema_version: int,
    product_entry_status_kind: str,
    product_entry_status_schema_ref: str,
) -> dict[str, Any]:
    product_entry_shell = dict(manifest.get("product_entry_shell") or {})
    shared_handoff = dict(manifest.get("shared_handoff") or {})
    product_entry_preflight = dict(manifest.get("product_entry_preflight") or {})
    product_entry_quickstart = dict(manifest.get("product_entry_quickstart") or {})
    workspace_operator_brief = dict(workspace_cockpit.get("operator_brief") or {})
    single_project_boundary = _validate_single_project_boundary(
        _single_project_boundary_payload(manifest.get("single_project_boundary")),
        context="product_entry_status.source.single_project_boundary",
    )
    capability_owner_boundary = _validate_capability_owner_boundary(
        _capability_owner_boundary_payload(manifest.get("capability_owner_boundary")),
        context="product_entry_status.source.capability_owner_boundary",
    )
    operator_brief = _build_product_entry_status_operator_brief(
        manifest=manifest,
        workspace_cockpit=workspace_cockpit,
        product_entry_preflight=product_entry_preflight,
        product_entry_quickstart=product_entry_quickstart,
    )

    return {
        "schema_version": schema_version,
        "surface_kind": product_entry_status_kind,
        "recommended_action": "inspect_or_prepare_research_loop",
        "target_domain_id": manifest.get("target_domain_id"),
        "workspace_locator": dict(manifest.get("workspace_locator") or {}),
        "runtime": dict(manifest.get("runtime") or {}),
        "product_entry_status": dict(manifest.get("product_entry_status") or {}),
        "product_entry_surface": dict(manifest.get("product_entry_surface") or {}),
        "operator_loop_surface": dict(manifest.get("operator_loop_surface") or {}),
        "operator_loop_actions": dict(manifest.get("operator_loop_actions") or {}),
        "product_entry_start": dict(manifest.get("product_entry_start") or {}),
        "product_entry_overview": dict(manifest.get("product_entry_overview") or {}),
        "product_entry_preflight": product_entry_preflight,
        "product_entry_readiness": dict(manifest.get("product_entry_readiness") or {}),
        "product_entry_quickstart": product_entry_quickstart,
        "family_orchestration": dict(manifest.get("family_orchestration") or {}),
        "product_entry_manifest": manifest,
        "entry_surfaces": {
            "entry_status": dict(product_entry_shell.get("product_entry_status") or {}),
            "cockpit": dict(product_entry_shell.get("workspace_cockpit") or {}),
            "submit_task": dict(product_entry_shell.get("submit_study_task") or {}),
            "launch_study": dict(product_entry_shell.get("launch_study") or {}),
            "study_progress": dict(product_entry_shell.get("study_progress") or {}),
            "export_inspection_package": dict(product_entry_shell.get("export_inspection_package") or {}),
            "mainline_status": dict(product_entry_shell.get("mainline_status") or {}),
            "mainline_phase": dict(product_entry_shell.get("mainline_phase") or {}),
            "direct_entry_builder": dict(shared_handoff.get("direct_entry_builder") or {}),
            "opl_handoff_builder": dict(shared_handoff.get("opl_handoff_builder") or {}),
        },
        "summary": {
            "product_entry_command": _non_empty_text(
                (manifest.get("product_entry_overview") or {}).get("product_entry_command")
            )
            or _non_empty_text((manifest.get("product_entry_overview") or {}).get("entry_status_command"))
            or _non_empty_text((product_entry_shell.get("product_entry_status") or {}).get("command")),
            "entry_status_command": _non_empty_text(
                (manifest.get("product_entry_overview") or {}).get("entry_status_command")
            )
            or _non_empty_text((product_entry_shell.get("product_entry_status") or {}).get("command")),
            "recommended_command": _non_empty_text((manifest.get("summary") or {}).get("recommended_command"))
            or _non_empty_text(manifest.get("recommended_command")),
            "operator_loop_command": _non_empty_text(
                (manifest.get("product_entry_overview") or {}).get("operator_loop_command")
            )
            or _non_empty_text((product_entry_shell.get("workspace_cockpit") or {}).get("command")),
        },
        "schema_ref": product_entry_status_schema_ref,
        "domain_entry_contract": dict(manifest.get("domain_entry_contract") or {}),
        "user_interaction_contract": dict(manifest.get("user_interaction_contract") or {}),
        "notes": [
            "This entry_status surface is a controller-owned product entry over the current research product-entry shell.",
            "It does not claim that a mature standalone medical frontend is already landed.",
            "It does not include the display / paper-figure asset line.",
        ],
        "single_project_boundary": single_project_boundary,
        "capability_owner_boundary": capability_owner_boundary,
        "executor_defaults": dict(manifest.get("executor_defaults") or {}),
        "functional_consumer_boundary": dict(manifest.get("functional_consumer_boundary") or {}),
        "runtime_inventory": dict(manifest.get("runtime_inventory") or {}),
        "task_lifecycle": dict(manifest.get("task_lifecycle") or {}),
        "skill_catalog": dict(manifest.get("skill_catalog") or {}),
        "family_action_catalog": dict(manifest.get("family_action_catalog") or {}),
        "automation": dict(manifest.get("automation") or {}),
        "phase2_user_product_loop": dict(manifest.get("phase2_user_product_loop") or {}),
        "product_entry_guardrails": dict(manifest.get("product_entry_guardrails") or {}),
        "phase3_clearance_lane": dict(manifest.get("phase3_clearance_lane") or {}),
        "phase4_backend_deconstruction": dict(manifest.get("phase4_backend_deconstruction") or {}),
        "operator_brief": operator_brief,
        "workspace_operator_brief": workspace_operator_brief,
        "workspace_ai_first_operations_state": dict(
            workspace_cockpit.get("ai_first_operations_state") or {}
        ),
        "workspace_paper_orchestra_operator_projection": dict(
            workspace_cockpit.get("paper_orchestra_operator_projection") or {}
        ),
        "workspace_open_auto_research_projection": _manifest_open_auto_research_projection(
            workspace_cockpit.get("open_auto_research_projection")
        ),
        "workspace_medical_paper_ops_health": dict(
            workspace_cockpit.get("medical_paper_ops_health_state") or {}
        ),
        "workspace_medical_paper_readiness": dict(
            workspace_cockpit.get("medical_paper_readiness_state") or {}
        ),
        "workspace_medical_paper_research_loop": _workspace_medical_paper_research_loop_manifest(
            workspace_cockpit
        ),
        "workspace_delivery_inspection": _workspace_delivery_inspection_manifest(workspace_cockpit),
        "workspace_opl_current_control_state_handoff_dashboard": _manifest_opl_current_control_state_handoff_dashboard(
            workspace_cockpit.get("opl_current_control_state_handoff_dashboard")
        ),
        "workspace_ai_first_feedback_state": {
            "surface_kind": "workspace_ai_first_feedback_state",
            "authority": "observability_only",
            "counts": dict((workspace_cockpit.get("ai_first_operations_state") or {}).get("counts") or {}),
            "study_feedback": [
                {
                    "study_id": item.get("study_id"),
                    "feedback_state": dict(item.get("ai_first_feedback_state") or {}),
                }
                for item in (workspace_cockpit.get("studies") or [])
                if isinstance(item, Mapping) and item.get("ai_first_feedback_state")
            ],
        },
        "workspace_attention_queue_preview": list((workspace_cockpit.get("attention_queue") or []))[:3],
        "workspace_truth_snapshots": [
            dict(item["study_truth_snapshot"])
            for item in (workspace_cockpit.get("studies") or [])
            if isinstance(item, Mapping) and isinstance(item.get("study_truth_snapshot"), Mapping)
        ],
        "workspace_runtime_health_snapshots": [
            dict(item["runtime_health_snapshot"])
            for item in (workspace_cockpit.get("studies") or [])
            if isinstance(item, Mapping) and isinstance(item.get("runtime_health_snapshot"), Mapping)
        ],
        "phase5_platform_target": dict(manifest.get("phase5_platform_target") or {}),
    }
