from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.medical_paper_ops_health import (
    build_medical_paper_ops_health,
    workspace_medical_paper_ops_health,
)
from med_autoscience.controllers.medical_paper_research_loop import (
    build_medical_paper_research_loop,
    workspace_medical_paper_research_loop,
)
from med_autoscience.controllers.medical_paper_v4_operations import (
    build_v4_operations_dashboard,
    workspace_v4_operations_state,
)
from med_autoscience.controllers.pi_action_projection import (
    build_pi_action_projection,
    compact_pi_action_projection,
)
from med_autoscience.controllers.production_blocker_impact_projection import (
    build_production_blocker_impact_projection,
)
from med_autoscience.controllers.runtime_continuity_projection import runtime_continuity_projection
from med_autoscience.controllers.study_progress_parts.macro_state_projection import (
    compact_study_macro_state_from_payload,
)
from med_autoscience.controllers.delivery_visibility_projection import (
    compact_delivery_inspection_projection,
)

from med_autoscience.controllers.product_entry_parts import shared as _shared
from med_autoscience.controllers.product_entry_parts.workspace_cockpit import (
    state_and_study_items as _state_and_study_items,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.command_assembly import (
    study_commands,
    user_loop_commands,
    workspace_commands,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.attention_hub import (
    attention_queue as build_attention_queue,
    operator_brief as build_operator_brief,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.health_cards import (
    workspace_health_cards,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.progress_projection import (
    study_progress_user_visible_projection,
    user_visible_field,
    user_visible_list,
)


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)
_module_reexport(_state_and_study_items)


def _study_item(
    *,
    progress_payload: dict[str, Any],
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    study_id = str(progress_payload.get("study_id") or "").strip()
    commands = study_commands(profile_ref=profile_ref, study_id=study_id)
    supervision = dict(progress_payload.get("supervision") or {})
    monitoring = {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")),
        "supervisor_tick_status": _non_empty_text(supervision.get("supervisor_tick_status")),
    }
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    intervention_lane = dict(progress_payload.get("intervention_lane") or {})
    study_macro_state = compact_study_macro_state_from_payload(progress_payload)
    user_visible_projection = study_progress_user_visible_projection(progress_payload)
    operator_verdict = dict(progress_payload.get("operator_verdict") or {})
    operator_status_card = dict(progress_payload.get("operator_status_card") or {})
    auto_runtime_parked = dict(progress_payload.get("auto_runtime_parked") or {})
    recommended_command = _non_empty_text(progress_payload.get("recommended_command"))
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    autonomy_contract = dict(progress_payload.get("autonomy_contract") or {})
    autonomy_soak_status = dict(progress_payload.get("autonomy_soak_status") or {})
    quality_closure_truth = dict(progress_payload.get("quality_closure_truth") or {})
    quality_execution_lane = dict(progress_payload.get("quality_execution_lane") or {})
    same_line_route_truth = _same_line_route_truth_payload(progress_payload)
    same_line_route_surface = dict(progress_payload.get("same_line_route_surface") or {})
    quality_review_loop = dict(progress_payload.get("quality_review_loop") or {})
    quality_repair_followthrough = dict(progress_payload.get("quality_repair_batch_followthrough") or {})
    quality_review_followthrough = dict(progress_payload.get("quality_review_followthrough") or {})
    gate_clearing_followthrough = _normalized_gate_clearing_followthrough(
        progress_payload,
        fallback_command=commands["progress"],
    )
    ai_first_default_entry_state = dict(progress_payload.get("ai_first_default_entry_state") or {})
    ai_first_operations_dashboard = dict(progress_payload.get("ai_first_operations_dashboard") or {})
    ai_first_feedback_state = dict(progress_payload.get("ai_first_feedback_state") or {})
    ai_first_action_dispatch_lifecycle = dict(
        progress_payload.get("ai_first_action_dispatch_lifecycle") or {}
    )
    dispatch_ledger = dict(progress_payload.get("dispatch_ledger") or {})
    publication_eval = dict(progress_payload.get("publication_eval") or {})
    artifact_runtime_proof_surface = dict(progress_payload.get("artifact_runtime_proof") or {})
    submission_hygiene_truth = dict(progress_payload.get("submission_hygiene_truth") or {})
    delivery_inspection = compact_delivery_inspection_projection(progress_payload.get("delivery_inspection"))
    product_recommended_flow = dict(progress_payload.get("product_recommended_flow") or {})
    paper_orchestra_operator_projection = dict(progress_payload.get("paper_orchestra_operator_projection") or {})
    open_auto_research_state = dict(progress_payload.get("open_auto_research_projection") or {})
    portable_supervisor_dashboard = dict(progress_payload.get("portable_supervisor_dashboard") or {})
    pi_action_projection = _normalized_pi_action_projection(progress_payload)
    medical_paper_readiness_surface = _normalized_medical_paper_readiness_projection(
        progress_payload.get("medical_paper_readiness")
    )
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    runtime_continuity = runtime_continuity_projection(progress_payload)
    study_truth_snapshot = _truth_snapshot_summary(progress_payload.get("study_truth_snapshot"))
    runtime_health_snapshot = _runtime_health_snapshot_summary(progress_payload.get("runtime_health_snapshot"))
    control_plane_snapshot = _control_plane_snapshot_summary(progress_payload.get("control_plane_snapshot"))
    research_runtime_control_projection = dict(progress_payload.get("research_runtime_control_projection") or {})
    runtime_reconcile_trigger = dict(progress_payload.get("runtime_reconcile_trigger") or {})
    outer_supervision_slo = dict(progress_payload.get("outer_supervision_slo") or {})
    production_blocker_impact = build_production_blocker_impact_projection(
        progress_payload,
        study_id=study_id,
    )
    gate_surface = dict(research_runtime_control_projection.get("research_gate_surface") or {})
    if gate_surface.get("approval_gate_field") == "needs_user_decision":
        gate_surface.setdefault("legacy_approval_gate_field", "needs_physician_decision")
        research_runtime_control_projection["research_gate_surface"] = gate_surface
    return {
        "study_id": study_id,
        "truth_epoch": _non_empty_text(progress_payload.get("truth_epoch"))
        or _non_empty_text((study_truth_snapshot or {}).get("truth_epoch")),
        "study_truth_snapshot": study_truth_snapshot,
        "study_macro_state": study_macro_state,
        "runtime_health_epoch": _non_empty_text(progress_payload.get("runtime_health_epoch"))
        or _non_empty_text((runtime_health_snapshot or {}).get("runtime_health_epoch")),
        "runtime_health_snapshot": runtime_health_snapshot,
        "control_plane_snapshot": control_plane_snapshot,
        "status_narration_contract": progress_payload.get("status_narration_contract"),
        "user_visible_projection": user_visible_projection or None,
        "state": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="state",
        ),
        "writer_state": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="writer_state",
        ),
        "user_next": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="user_next",
        ),
        "reason": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="reason",
        ),
        "package_delivered": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="package_delivered",
        ),
        "actual_write_active": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="actual_write_active",
        ),
        "user_action_required": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="user_action_required",
        ),
        "state_label": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="state_label",
        ),
        "state_summary": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="state_summary",
        ),
        "current_stage": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="current_stage",
        ),
        "current_stage_summary": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="current_stage_summary",
        ),
        "current_blockers": user_visible_list(
            user_visible_projection=user_visible_projection,
            key="current_blockers",
        ),
        "next_system_action": user_visible_field(
            user_visible_projection=user_visible_projection,
            key="next_system_action",
        ),
        "intervention_lane": intervention_lane or None,
        "operator_verdict": operator_verdict or None,
        "operator_status_card": operator_status_card or None,
        "auto_runtime_parked": auto_runtime_parked or None,
        "parked_state": progress_payload.get("parked_state"),
        "parked_owner": progress_payload.get("parked_owner"),
        "external_owner": progress_payload.get("external_owner"),
        "external_runtime_owner": progress_payload.get("external_runtime_owner"),
        "resource_release_expected": progress_payload.get("resource_release_expected"),
        "awaiting_explicit_wakeup": progress_payload.get("awaiting_explicit_wakeup"),
        "auto_execution_complete": progress_payload.get("auto_execution_complete"),
        "reopen_policy": progress_payload.get("reopen_policy"),
        "legacy_current_stage": progress_payload.get("legacy_current_stage"),
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract or None,
        "autonomy_soak_status": autonomy_soak_status or None,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_review_loop": quality_review_loop or None,
        "quality_repair_followthrough": quality_repair_followthrough or None,
        "quality_review_followthrough": quality_review_followthrough or None,
        "gate_clearing_followthrough": gate_clearing_followthrough or None,
        "ai_first_default_entry_state": ai_first_default_entry_state or None,
        "ai_first_operations_dashboard": ai_first_operations_dashboard or None,
        "ai_first_feedback_state": ai_first_feedback_state or None,
        "ai_first_action_dispatch_lifecycle": ai_first_action_dispatch_lifecycle or None,
        "dispatch_ledger": dispatch_ledger or None,
        "publication_eval": publication_eval or None,
        "artifact_runtime_proof": artifact_runtime_proof_surface or None,
        "submission_hygiene_truth": submission_hygiene_truth or None,
        "delivery_inspection": delivery_inspection,
        "product_recommended_flow": product_recommended_flow or None,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection or None,
        "open_auto_research_projection": open_auto_research_state or None,
        "portable_supervisor_dashboard": portable_supervisor_dashboard or None,
        "pi_action_projection": pi_action_projection,
        "medical_paper_readiness": medical_paper_readiness_surface or None,
        "research_runtime_control_projection": research_runtime_control_projection or None,
        "runtime_reconcile_trigger": runtime_reconcile_trigger or None,
        "outer_supervision_slo": outer_supervision_slo or None,
        "runtime_continuity": runtime_continuity,
        "production_blocker_impact": production_blocker_impact,
        "recovery_contract": recovery_contract or None,
        "needs_physician_decision": bool(progress_payload.get("needs_physician_decision")),
        "needs_user_decision": bool(progress_payload.get("needs_user_decision")),
        "monitoring": monitoring,
        "task_intake": task_intake or None,
        "progress_freshness": progress_freshness or None,
        "commands": commands,
    }


def _normalized_pi_action_projection(progress_payload: Mapping[str, Any]) -> dict[str, Any]:
    compact = compact_pi_action_projection(progress_payload.get("pi_action_projection"))
    if compact is not None:
        return compact
    return compact_pi_action_projection(build_pi_action_projection(progress_payload)) or {}


from .readiness_and_delivery import (
    _normalized_medical_paper_readiness_projection,
    _read_medical_paper_readiness_projection,
    _workspace_delivery_inspection_state,
    _workspace_medical_paper_readiness_state,
    _workspace_portable_supervisor_queue_dashboard,
)


def _truth_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "truth_epoch",
        "authority_epoch",
        "canonical_next_action",
        "blocking_reasons",
        "dominant_authority_refs",
        "allowed_controller_actions",
        "package_state",
        "writer_epoch",
        "source_signature",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _runtime_health_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
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
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _control_plane_snapshot_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    keys = (
        "control_state",
        "canonical_next_action",
        "canonical_runtime_action",
        "dispatch_gate",
        "route_authorization",
        "blocking_reasons",
        "allowed_controller_actions",
        "authority_refs",
        "quality_gate_relaxation_allowed",
    )
    summary = {key: value[key] for key in keys if key in value}
    return summary or None


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.exists():
        return []
    return [
        study_root
        for study_root in sorted(path for path in profile.studies_root.iterdir() if path.is_dir())
        if (study_root / "study.yaml").exists()
    ]


def _workspace_cockpit_study_snapshot(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
) -> tuple[dict[str, Any], list[str]]:
    progress_payload = study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )
    item = _study_item(progress_payload=progress_payload, profile_ref=profile_ref)
    if not item.get("medical_paper_readiness"):
        item["medical_paper_readiness"] = _read_medical_paper_readiness_projection(study_root=study_root) or None
    readiness = item.get("medical_paper_readiness") if isinstance(item.get("medical_paper_readiness"), Mapping) else {}
    item["medical_paper_v4_operations"] = build_v4_operations_dashboard(readiness)
    item["medical_paper_ops_health"] = build_medical_paper_ops_health(readiness, progress_payload=item)
    item["medical_paper_research_loop"] = build_medical_paper_research_loop(
        readiness,
        ops_health=item["medical_paper_ops_health"],
    )
    alerts = list(item["current_blockers"])
    progress_freshness = dict(item.get("progress_freshness") or {})
    progress_summary = _non_empty_text(progress_freshness.get("summary"))
    if _non_empty_text(progress_freshness.get("status")) in {"stale", "missing"} and progress_summary is not None:
        alerts.append(progress_summary)
    return item, alerts


def read_workspace_cockpit(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    inspect_workspace_supervision = _controller_override("_inspect_workspace_supervision", _inspect_workspace_supervision)
    doctor_report = build_doctor_report_fn(profile)
    workspace_alerts = _workspace_ready_alerts(doctor_report)
    studies: list[dict[str, Any]] = []
    study_roots = _study_roots(profile)
    if study_roots:
        with ThreadPoolExecutor(max_workers=len(study_roots)) as executor:
            futures = [
                executor.submit(
                    _workspace_cockpit_study_snapshot,
                    profile=profile,
                    profile_ref=profile_ref,
                    study_root=study_root,
                )
                for study_root in study_roots
            ]
            for future in futures:
                item, item_alerts = future.result()
                studies.append(item)
                for alert in item_alerts:
                    if alert not in workspace_alerts:
                        workspace_alerts.append(alert)
    service = inspect_workspace_supervision(profile)
    health_cards = workspace_health_cards(
        profile=profile,
        study_roots=study_roots,
        studies=studies,
        service=service,
    )
    workspace_supervision = health_cards["workspace_supervision"]
    if (
        (not bool(service.get("loaded")) or bool(service.get("drift_reasons")))
        and service.get("summary") not in workspace_alerts
    ):
        workspace_alerts.append(str(service.get("summary")))
    baseline_alerts = _workspace_ready_alerts(doctor_report)
    if workspace_alerts and not baseline_alerts:
        workspace_status = "attention_required"
    elif baseline_alerts:
        workspace_status = "blocked"
    else:
        workspace_status = "ready"
    mainline_snapshot = _mainline_snapshot()
    commands = workspace_commands(profile=profile, profile_ref=profile_ref)
    attention_queue = build_attention_queue(
        workspace_status=workspace_status,
        workspace_supervision=workspace_supervision,
        studies=studies,
        commands=commands,
    )
    user_loop = user_loop_commands(profile=profile, profile_ref=profile_ref)
    operator_brief = build_operator_brief(
        workspace_status=workspace_status,
        workspace_alerts=workspace_alerts,
        attention_queue=attention_queue,
        studies=studies,
        user_loop=user_loop,
        commands=commands,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "workspace_status": workspace_status,
        "mainline_snapshot": mainline_snapshot,
        "workspace_alerts": workspace_alerts,
        "workspace_supervision": workspace_supervision,
        "medical_paper_readiness_state": health_cards["medical_paper_readiness_state"],
        "medical_paper_v4_operations_state": health_cards["medical_paper_v4_operations_state"],
        "medical_paper_ops_health_state": health_cards["medical_paper_ops_health_state"],
        "medical_paper_research_loop_state": health_cards["medical_paper_research_loop_state"],
        "ai_first_operations_state": health_cards["ai_first_operations_state"],
        "ai_first_cross_study_completion_projection": health_cards[
            "ai_first_cross_study_completion_projection"
        ],
        "paper_orchestra_operator_projection": health_cards["paper_orchestra_operator_projection"],
        "open_auto_research_projection": health_cards["open_auto_research_projection"],
        "portable_supervisor_queue_dashboard": health_cards["portable_supervisor_queue_dashboard"],
        "delivery_inspection_state": health_cards["delivery_inspection_state"],
        "attention_queue": attention_queue,
        "operator_brief": operator_brief,
        "user_loop": user_loop,
        "phase2_user_product_loop": phase2_user_product_loop,
        "studies": studies,
        "commands": commands,
    }
