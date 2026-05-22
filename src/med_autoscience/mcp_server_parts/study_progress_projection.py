from __future__ import annotations

from typing import Any

from med_autoscience.controllers.delivery_visibility_projection import (
    compact_delivery_inspection_projection,
    render_delivery_inspection_markdown_lines,
)
from med_autoscience.controllers.medical_paper_v3_action_truth import (
    ACTION_BY_SURFACE as READINESS_ACTION_BY_SURFACE,
    LITERATURE_SURFACE_KEYS,
    action_truths_for_readiness,
    compact_missing_surface_with_action_truth,
)
from med_autoscience.controllers.medical_paper_ops_health import build_medical_paper_ops_health
from med_autoscience.controllers.medical_paper_research_loop import (
    build_medical_paper_research_loop,
    compact_medical_paper_research_loop,
    research_loop_markdown_lines,
)
from med_autoscience.controllers.medical_paper_v4_operations import build_v4_operations_dashboard
from med_autoscience.controllers.pi_action_projection import compact_pi_action_projection
from med_autoscience.controllers.study_progress_parts.macro_state_projection import (
    compact_study_macro_state_from_payload,
)
from med_autoscience.controllers.study_progress_parts.user_visible_projection import (
    build_user_visible_projection,
)
from med_autoscience.controllers.runtime_continuity_projection import runtime_continuity_projection
from med_autoscience.mcp_server_parts.open_auto_research_projection import (
    compact_open_auto_research_projection,
    compact_open_auto_research_soak_for_mcp,
    render_mcp_open_auto_research_soak_markdown,
)
from med_autoscience.mcp_server_parts.portable_supervisor_projection import (
    compact_portable_supervisor_dashboard,
    render_mcp_progress_portable_supervisor_dashboard,
)
from med_autoscience.mcp_server_parts.study_progress_markdown_sections import render_mcp_progress_stage


def _compact_string_list(value: Any, *, limit: int = 12) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _compact_record(value: Any, keys: tuple[str, ...]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact: dict[str, Any] = {}
    for key in keys:
        if key in value:
            compact[key] = value[key]
    return compact or None


def _compact_events(value: Any, *, limit: int = 5) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    events: list[dict[str, Any]] = []
    keys = ("timestamp", "time_label", "category", "title", "summary", "source", "artifact_path")
    for item in value:
        event = _compact_record(item, keys)
        if event is not None:
            events.append(event)
        if len(events) >= limit:
            break
    return events


def _compact_task_intake(value: Any) -> dict[str, Any] | None:
    task_intake = _compact_record(
        value,
        (
            "task_id",
            "study_id",
            "emitted_at",
            "entry_mode",
            "task_intent",
            "journal_target",
            "first_cycle_outputs",
        ),
    )
    if task_intake is None:
        return None
    if isinstance(task_intake.get("first_cycle_outputs"), list):
        task_intake["first_cycle_outputs"] = _compact_string_list(task_intake["first_cycle_outputs"], limit=8)
    source = value if isinstance(value, dict) else {}
    constraints = _compact_string_list(source.get("constraints"), limit=8)
    if constraints:
        task_intake["constraints"] = constraints
    revision_intake = _compact_record(
        source.get("revision_intake"),
        ("kind", "status", "handoff_required", "reactivation_required", "checklist"),
    )
    if revision_intake is not None:
        if isinstance(revision_intake.get("checklist"), list):
            revision_intake["checklist"] = _compact_string_list(revision_intake["checklist"], limit=12)
        task_intake["revision_intake"] = revision_intake
    return task_intake


def _compact_runtime_efficiency(value: Any) -> dict[str, Any] | None:
    runtime_efficiency = _compact_record(
        value,
        (
            "run_id",
            "telemetry_path",
            "prompt_bytes",
            "stdout_bytes",
            "tool_result_bytes_total",
            "tool_result_bytes_after_compaction_total",
            "tool_result_bytes_saved_total",
            "compacted_tool_result_count",
            "full_detail_tool_call_count",
            "mcp_tool_call_count",
            "tool_call_budget",
            "tool_call_count",
            "tool_call_budget_remaining",
            "tool_call_budget_exceeded",
            "unique_command_count",
            "read_tool_call_count",
            "repeated_read_result_count",
            "repeated_read_ratio",
            "full_detail_count",
            "evidence_packet_index_path",
            "evidence_packet_count",
            "gate_replay_hit_count",
            "latest_gate_replay_at",
            "gate_replay_status",
            "gate_replay_ref",
            "gate_cache",
            "summary",
        ),
    )
    if runtime_efficiency is None:
        return None
    gate_cache_surfaces = []
    if isinstance(value, dict):
        gate_cache_surfaces = [
            item
            for item in value.get("gate_cache_surfaces", [])
            if isinstance(item, dict)
        ][:5]
    if gate_cache_surfaces:
        runtime_efficiency["gate_cache_surfaces"] = gate_cache_surfaces
    return runtime_efficiency


def _compact_module_surfaces(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    module_surfaces: dict[str, Any] = {}
    keys = (
        "module",
        "surface_kind",
        "summary_id",
        "summary_ref",
        "status_summary",
        "next_action_summary",
        "health_status",
        "runtime_decision",
        "runtime_reason",
        "overall_verdict",
        "primary_claim_status",
        "requires_controller_decision",
    )
    for module_name, module_payload in value.items():
        module_surface = _compact_record(module_payload, keys)
        if module_surface is not None:
            module_surfaces[module_name] = module_surface
    return module_surfaces or None


def _compact_medical_paper_readiness(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        (
            "surface",
            "overall_status",
            "ready_count",
            "required_count",
            "quality_claim_authorized",
            "mechanical_projection_can_authorize_quality",
            "next_action",
        ),
    )
    if compact is None:
        return None
    raw_missing_surfaces: list[dict[str, Any]] = []
    for item in value.get("capability_surfaces") or []:
        if not isinstance(item, dict):
            continue
        if not bool(item.get("required_for_ready")) or item.get("status") == "present":
            continue
        missing = _compact_readiness_missing_surface(item)
        if missing is not None:
            raw_missing_surfaces.append(missing)
    literature_missing_surfaces = [
        item
        for item in raw_missing_surfaces
        if str(item.get("surface_key") or "").strip() in LITERATURE_SURFACE_KEYS
    ]
    missing_surfaces = literature_missing_surfaces[:1] or raw_missing_surfaces
    compact["missing_surfaces"] = missing_surfaces[:8]
    compact["v3_action_truth"] = action_truths_for_readiness(value)
    compact["v4_operations"] = _compact_medical_paper_v4_operations(
        build_v4_operations_dashboard(value)
    )
    compact["ops_health"] = _compact_medical_paper_ops_health(
        build_medical_paper_ops_health(value)
    )
    compact["research_loop"] = compact_medical_paper_research_loop(
        build_medical_paper_research_loop(value, ops_health=compact["ops_health"])
    )
    return compact


def _compact_medical_paper_ops_health(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        (
            "surface",
            "overall_status",
            "summary",
            "counts",
            "last_green_at",
            "next_operator_action",
            "authority_contract",
            "quality_claim_authorized",
            "mechanical_projection_can_authorize_quality",
        ),
    )
    if compact is None:
        return None
    health = value.get("health")
    if isinstance(health, dict):
        compact["health"] = {
            key: _compact_record(
                item,
                ("component", "status", "missing_reason", "next_action", "durable_refs"),
            )
            for key, item in health.items()
            if isinstance(item, dict)
        }
    return compact


def _compact_medical_paper_v4_operations(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        (
            "surface",
            "overall_status",
            "summary",
            "next_action",
            "authority_contract",
            "quality_claim_authorized",
            "mechanical_projection_can_authorize_quality",
        ),
    )
    if compact is None:
        return None
    health = value.get("health")
    if isinstance(health, dict):
        compact["health"] = {
            key: _compact_record(
                item,
                ("surface_key", "status", "missing_reason", "next_action", "pending_action_count", "action_ids"),
            )
            for key, item in health.items()
            if isinstance(item, dict)
        }
    return compact


def _compact_readiness_missing_surface(item: dict[str, Any]) -> dict[str, Any] | None:
    return compact_missing_surface_with_action_truth(item)


def _compact_user_visible_projection(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        (
            "surface",
            "read_model",
            "schema_version",
            "authority",
            "projection_only",
            "answer_focus",
            "study_id",
            "quest_id",
            "state",
            "writer_state",
            "user_next",
            "reason",
            "conflict_reason",
            "package_delivered",
            "actual_write_active",
            "meaningful_artifact_delta",
            "next_owner",
            "why_not_progressing",
            "user_action_required",
            "state_label",
            "state_summary",
            "current_stage",
            "current_stage_label",
            "current_stage_summary",
            "status_summary",
            "paper_stage",
            "paper_stage_summary",
            "next_system_action",
            "next_step",
            "needs_user_decision",
            "needs_physician_decision",
            "study_macro_state",
            "conditions",
        ),
    )
    if compact is None:
        return None
    compact["current_blockers"] = _compact_string_list(value.get("current_blockers"), limit=12)
    supervision = _compact_record(
        value.get("supervision"),
        (
            "browser_url",
            "quest_session_api_url",
            "active_run_id",
            "health_status",
            "supervisor_tick_status",
        ),
    )
    if supervision is not None:
        compact["supervision"] = supervision
    evidence = value.get("evidence") if isinstance(value.get("evidence"), dict) else {}
    compact["evidence"] = {
        "latest_events": _compact_events(evidence.get("latest_events")),
        "refs": dict(evidence.get("refs") or {}) if isinstance(evidence.get("refs"), dict) else {},
    }
    evidence_refs = value.get("evidence_refs")
    if isinstance(evidence_refs, dict):
        compact["evidence_refs"] = dict(evidence_refs)
    return compact


def _current_user_visible_projection(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if value.get("schema_version") != 2:
        return None
    for key in ("writer_state", "user_next", "reason", "state_label", "state_summary"):
        if key not in value:
            return None
    return value


def _apply_user_visible_projection(compact: dict[str, Any], user_visible: dict[str, Any]) -> None:
    for key in (
        "study_id",
        "quest_id",
        "state",
        "writer_state",
        "user_next",
        "reason",
        "conflict_reason",
        "package_delivered",
        "actual_write_active",
        "meaningful_artifact_delta",
        "next_owner",
        "why_not_progressing",
        "user_action_required",
        "state_label",
        "state_summary",
        "current_stage",
        "current_stage_label",
        "current_stage_summary",
        "status_summary",
        "paper_stage",
        "paper_stage_summary",
        "next_system_action",
        "next_step",
        "needs_user_decision",
        "needs_physician_decision",
    ):
        if key in user_visible:
            compact[key] = user_visible[key]
    compact["current_blockers"] = _compact_string_list(user_visible.get("current_blockers"), limit=12)
    evidence = user_visible.get("evidence") if isinstance(user_visible.get("evidence"), dict) else {}
    latest_events = _compact_events(evidence.get("latest_events"))
    if latest_events:
        compact["latest_events"] = latest_events


def compact_study_progress_projection(payload: dict[str, Any]) -> dict[str, Any]:
    compact_keys = (
        "schema_version",
        "generated_at",
        "truth_epoch",
        "runtime_health_epoch",
        "study_id",
        "study_root",
        "quest_id",
        "quest_root",
        "current_stage",
        "current_stage_summary",
        "paper_stage",
        "paper_stage_summary",
        "next_system_action",
        "auto_runtime_parked",
        "parked_state",
        "parked_owner",
        "resource_release_expected",
        "awaiting_explicit_wakeup",
        "auto_execution_complete",
        "reopen_policy",
        "needs_physician_decision",
        "needs_user_decision",
        "physician_decision_summary",
        "user_decision_summary",
        "runtime_decision",
        "runtime_reason",
        "progress_freshness",
        "recommended_command",
    )
    source_payload = dict(payload)
    study_macro_state = compact_study_macro_state_from_payload(source_payload)
    if study_macro_state is not None:
        source_payload["study_macro_state"] = study_macro_state
    user_visible_source = _current_user_visible_projection(source_payload.get("user_visible_projection"))
    if user_visible_source is None:
        user_visible_source = build_user_visible_projection(source_payload)
        source_payload["user_visible_projection"] = user_visible_source

    compact = {key: source_payload[key] for key in compact_keys if key in source_payload}
    compact["current_blockers"] = _compact_string_list(payload.get("current_blockers"), limit=12)
    compact["latest_events"] = _compact_events(payload.get("latest_events"))
    user_visible_projection = _compact_user_visible_projection(user_visible_source)

    for key, keys in {
        "intervention_lane": (
            "lane_id",
            "title",
            "severity",
            "summary",
            "recommended_action_id",
            "repair_mode",
            "route_target",
            "route_target_label",
            "route_key_question",
            "route_summary",
        ),
        "operator_verdict": (
            "surface_kind",
            "study_id",
            "lane_id",
            "severity",
            "decision_mode",
            "needs_intervention",
            "focus_scope",
            "summary",
            "reason_summary",
            "primary_step_id",
            "primary_surface_kind",
            "primary_command",
        ),
        "operator_status_card": (
            "surface_kind",
            "study_id",
            "handling_state",
            "handling_state_label",
            "owner_summary",
            "current_focus",
            "latest_truth_time",
            "latest_truth_source",
            "human_surface_freshness",
            "human_surface_summary",
            "next_confirmation_signal",
            "user_visible_verdict",
            "runtime_efficiency_summary",
            "runtime_efficiency_refs",
            "runtime_efficiency_metrics",
        ),
        "autonomy_soak_status": (
            "surface_kind",
            "status",
            "summary",
            "autonomy_state",
            "dispatch_status",
            "route_target",
            "route_target_label",
            "route_key_question",
            "progress_freshness_status",
            "next_confirmation_signal",
        ),
        "quality_closure_truth": ("state", "summary", "current_required_action", "route_target"),
        "quality_execution_lane": (
            "lane_id",
            "lane_label",
            "repair_mode",
            "route_target",
            "route_key_question",
            "summary",
            "why_now",
        ),
        "quality_review_loop": (
            "policy_id",
            "loop_id",
            "closure_state",
            "lane_id",
            "current_phase",
            "current_phase_label",
            "recommended_next_phase",
            "blocking_issue_count",
            "summary",
            "recommended_next_action",
            "re_review_ready",
        ),
        "supervision": (
            "browser_url",
            "quest_session_api_url",
            "active_run_id",
            "health_status",
            "supervisor_tick_status",
            "supervisor_tick_required",
            "supervisor_tick_summary",
            "supervisor_tick_latest_recorded_at",
            "launch_report_path",
        ),
        "continuation_state": (
            "quest_status",
            "active_run_id",
            "continuation_policy",
            "continuation_anchor",
            "continuation_reason",
            "runtime_state_path",
        ),
    }.items():
        item = _compact_record(source_payload.get(key), keys)
        if item is not None:
            compact[key] = item

    for key in ("recommended_commands", "refs"):
        value = source_payload.get(key)
        if isinstance(value, list):
            compact[key] = value[:5]
        elif isinstance(value, dict):
            compact[key] = dict(value)

    for key, builder in {
        "task_intake": _compact_task_intake,
        "runtime_efficiency": _compact_runtime_efficiency,
        "module_surfaces": _compact_module_surfaces,
        "medical_paper_readiness": _compact_medical_paper_readiness,
        "pi_action_projection": compact_pi_action_projection,
        "delivery_inspection": compact_delivery_inspection_projection,
        "open_auto_research_projection": compact_open_auto_research_projection,
        "portable_supervisor_dashboard": compact_portable_supervisor_dashboard,
        "study_truth_snapshot": _compact_study_truth_snapshot,
        "runtime_health_snapshot": _compact_runtime_health_snapshot,
        "control_plane_snapshot": _compact_control_plane_snapshot,
    }.items():
        item = builder(source_payload.get(key))
        if item is not None:
            compact[key] = item
    runtime_continuity = runtime_continuity_projection(source_payload)
    if runtime_continuity.get("runtime_session") or runtime_continuity.get("recovery_intent"):
        compact["runtime_continuity"] = runtime_continuity
    if study_macro_state is not None:
        compact["study_macro_state"] = study_macro_state
    ai_repair_lifecycle = _compact_record(
        payload.get("ai_repair_lifecycle"),
        (
            "surface",
            "state",
            "top_action",
            "auto_apply_allowed",
            "last_apply_attempt_at",
            "applied_at",
            "blocked_reason",
            "next_owner",
            "external_supervisor_required",
        ),
    )
    if ai_repair_lifecycle is not None:
        compact["ai_repair_lifecycle"] = ai_repair_lifecycle

    if user_visible_projection is not None:
        compact["user_visible_projection"] = user_visible_projection
        _apply_user_visible_projection(compact, user_visible_projection)

    compact["mcp_projection"] = {
        "surface_kind": "mcp_compacted_study_progress_projection",
        "source_surface_kind": "study_progress",
        "compacted": True,
        "full_detail_surface": "CLI study-progress --format json",
    }
    return compact


def _compact_study_truth_snapshot(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _compact_record(
        value,
        (
            "truth_epoch",
            "authority_epoch",
            "canonical_next_action",
            "blocking_reasons",
            "dominant_authority_refs",
            "allowed_controller_actions",
            "package_state",
            "writer_epoch",
            "source_signature",
        ),
    )


def _compact_runtime_health_snapshot(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _compact_record(
        value,
        (
            "runtime_health_epoch",
            "canonical_runtime_action",
            "attempt_state",
            "retry_budget_remaining",
            "worker_liveness_state",
            "supervisor_state",
            "dominant_runtime_refs",
            "blocking_reasons",
            "allowed_controller_actions",
            "source_signature",
        ),
    )


def _compact_control_plane_snapshot(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _compact_record(
        value,
        (
            "control_state",
            "canonical_next_action",
            "canonical_runtime_action",
            "dispatch_gate",
            "route_authorization",
            "blocking_reasons",
            "allowed_controller_actions",
            "authority_refs",
            "quality_gate_relaxation_allowed",
        ),
    )


def compact_study_runtime_result_for_mcp(payload: dict[str, Any]) -> dict[str, Any]:
    compact = dict(payload)
    progress_projection = payload.get("progress_projection")
    if isinstance(progress_projection, dict):
        compact["progress_projection"] = compact_study_progress_projection(progress_projection)
        compact["mcp_projection"] = {
            "surface_kind": "mcp_compacted_progress_projection",
            "compacted_progress_projection": True,
        }
    return compact


from med_autoscience.mcp_server_parts.study_progress_markdown_renderer import (
    _render_mcp_progress_identity,
    _render_mcp_progress_supervision,
    _render_mcp_progress_runtime_state,
    _render_mcp_progress_operator_and_action,
    _render_mcp_progress_blockers,
    _render_mcp_progress_medical_paper_readiness,
    _render_mcp_progress_open_auto_research,
    _render_mcp_progress_refs,
)


def render_mcp_study_progress_markdown(payload: dict[str, Any]) -> str:
    compact = compact_study_progress_projection(payload)
    lines: list[str] = []
    lines.extend(_render_mcp_progress_identity(compact))
    lines.extend(render_mcp_progress_stage(compact))
    lines.extend(_render_mcp_progress_supervision(compact))
    lines.extend(_render_mcp_progress_runtime_state(compact))
    lines.extend(_render_mcp_progress_operator_and_action(compact))
    lines.extend(_render_mcp_progress_blockers(compact))
    lines.extend(_render_mcp_progress_medical_paper_readiness(compact))
    lines.extend(
        render_delivery_inspection_markdown_lines(
            compact.get("delivery_inspection"),
            heading="## Delivery Inspection",
        )
    )
    lines.extend(_render_mcp_progress_open_auto_research(compact))
    lines.extend(render_mcp_progress_portable_supervisor_dashboard(compact))
    lines.extend(_render_mcp_progress_refs(compact))
    return "\n".join(lines) + "\n"
