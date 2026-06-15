from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import (
    autonomy_ai_doctor,
    control_intent,
    data_asset_gate,
    domain_action_request_materializer,
    domain_owner_action_dispatch,
    figure_loop_guard,
    medical_literature_audit,
    medical_publication_surface,
    medical_reporting_audit,
    publication_gate,
    runtime_health_kernel,
    owner_route_handoff,
    owner_route_reconcile,
    domain_health_diagnostic_outer_loop_dispatch,
    domain_health_diagnostic_recovery_policy,
    domain_health_diagnostic_work_units,
    study_cycle_profiler,
    study_outer_loop,
    study_runtime_family_orchestration as family_orchestration,
    domain_status_projection,
    domain_transition_currentness,
)
from med_autoscience.controllers.domain_health_diagnostic_outer_loop_policy import (
    outer_loop_request_requires_fresh_controller_execution,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.autonomy_repair import (
    apply_ready_ai_doctor_repair,
    reconcile_ai_repair_lifecycle,
    read_ai_repair_lifecycle,
    read_ready_ai_doctor_repair,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.control_plane_gate import (
    CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
    apply_control_plane_dispatch_block,
    runtime_recovery_blocked_by_control_plane,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.fingerprints import build_fingerprint
from med_autoscience.controllers.domain_health_diagnostic_parts.gate_specificity import (
    _compact_work_unit_payload,
    _gate_specificity_non_executable_contract,
    _materialize_specificity_controller_state,
    _specificity_control_intent_identity,
    _specificity_terminal_status_payload,
    _study_requests_gate_specificity_terminal,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import (
    _build_outer_loop_wakeup_audit,
    _candidate_path,
    _controller_decision_latest_matches_outer_loop_request,
    _managed_study_status_payload,
    _non_empty_text,
    _outer_loop_dispatch_blocked_by_explicit_wakeup_contract,
    _quest_report_requests_managed_study_reroute,
    _serialize_managed_study_action,
    _serialize_managed_study_auto_recovery,
    _should_hard_auto_recover_managed_study,
    _should_refresh_managed_study_status_after_stage_request,
    _write_outer_loop_wakeup_audit,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.developer_supervisor_same_tick import (
    PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
    PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
    PROGRESS_FIRST_SAME_TICK_MAX_PASSES,
    PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
    _run_developer_supervisor_same_tick as _run_developer_supervisor_same_tick_impl,
    _same_tick_terminal_diagnostic,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    current_control_provider_admission_candidates,
    persisted_provider_admission_candidates,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report import (
    materialize_report_provider_admission_current_control_state as _materialize_report_provider_admission_current_control_state_impl,
    sync_report_provider_admission_current_control_state as _sync_report_provider_admission_current_control_state,
)
from med_autoscience.controllers.owner_route_reconcile_parts import supervision_surfaces
from med_autoscience.controllers.domain_health_diagnostic_parts.quest_scan import (
    DEFAULT_CONTROLLER_ORDER,
    ControllerRunner,
    _invoke_controller_runner,
    _publication_gate_ai_reviewer_eval_masks_return_to_gate,
    build_default_controller_runners,
    iter_ordered_controller_runners,
    run_domain_health_diagnostic_for_quest as _run_domain_health_diagnostic_for_quest_impl,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.reporting import (
    _attach_family_companion_to_quest_report,
    _attach_family_companion_to_runtime_report,
    _write_latest_domain_health_diagnostic_alias,
    render_domain_health_diagnostic_markdown,
    write_domain_health_diagnostic_report,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan import (
    _MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
    _MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE,
    _MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
    _NO_OP_SUPPRESSION_SUMMARY,
    _WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY,
    _attach_no_op_suppression_to_quest_report,
    _managed_study_recovery_failure_payload,
    _materialize_placeholder_quest_diagnostic_report,
    _serialize_no_op_suppression,
    run_domain_health_diagnostic_for_runtime as _run_domain_health_diagnostic_for_runtime_impl,
    utc_now,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.runtime_dry_run_previews import (
    attach_domain_action_request_materialization_preview,
    attach_domain_handler_owner_resolution_preview,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan_support import (
    PROGRESS_CURRENTNESS_KEYS,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator import (
    apply_managed_study_obligation_actuator,
)
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)
from med_autoscience.controllers.study_runtime_types import ProgressProjectionStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import domain_health_diagnostic as domain_health_diagnostic_protocol
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context
from med_autoscience.runtime_control.ports import RuntimeControlPorts

def _materialize_managed_study_autonomy_slo(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
) -> dict[str, Any]:
    profile_payload = study_cycle_profiler.profile_study_cycle(
        profile=profile,
        study_id=None,
        study_root=study_root,
    )
    slo_status = dict(profile_payload.get("autonomy_progress_slo_status") or {})
    return {
        "study_id": _non_empty_text(slo_status.get("study_id")) or Path(study_root).name,
        "quest_id": _non_empty_text(slo_status.get("quest_id")),
        "state": _non_empty_text(slo_status.get("state")) or "unknown",
        "breach_types": list(slo_status.get("breach_types") or []),
        "ai_doctor_request_required": bool(slo_status.get("ai_doctor_request_required")),
        "ai_doctor_state": _non_empty_text(slo_status.get("ai_doctor_state")) or "not_observed",
        "quality_gate_relaxation_allowed": False,
        "status_path": str(autonomy_ai_doctor.stable_slo_status_path(study_root=study_root)),
    }


def _materialize_domain_health_diagnostic_non_dispatching_decision(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
    tick_request: dict[str, Any],
    wakeup_audit: dict[str, Any],
) -> dict[str, Any]:
    if domain_health_diagnostic_work_units.needs_specificity_request(tick_request):
        return _materialize_specificity_controller_state(
            profile=profile,
            study_root=study_root,
            status_payload=status_payload,
            tick_request=tick_request,
            wakeup_audit=wakeup_audit,
            materialize_decision=study_outer_loop.materialize_non_dispatching_outer_loop_decision,
        )
    decision_payload = domain_health_diagnostic_work_units.strip_context(tick_request)
    decision_payload.pop("study_root", None)
    return study_outer_loop.materialize_non_dispatching_outer_loop_decision(
        profile=profile,
        study_root=study_root,
        status_payload=status_payload,
        source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
        recorded_at=_non_empty_text(wakeup_audit.get("recorded_at")),
        **decision_payload,
    )


def _refresh_managed_study_status_after_stage_request(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    if not _should_refresh_managed_study_status_after_stage_request(status_payload):
        return status_payload
    return _managed_study_status_payload(
        _progress_projection_for_diagnostic(profile=profile, study_root=study_root)
    )


def _status_payload_with_fresh_progress_currentness(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(status_payload)
    study_id = _non_empty_text(payload.get("study_id")) or Path(study_root).name
    if study_id is None:
        return payload
    try:
        from med_autoscience.controllers import study_progress

        progress = study_progress.read_study_progress(
            profile=profile,
            study_id=study_id,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    except Exception:
        return payload
    if not isinstance(progress, Mapping):
        return payload
    refreshed = False
    for key in (
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "current_owner_ticket",
    ):
        if key not in progress:
            continue
        value = progress.get(key)
        if isinstance(value, Mapping) and value:
            payload[key] = dict(value)
            refreshed = True
    if refreshed and (generated_at := _non_empty_text(progress.get("generated_at"))) is not None:
        payload["study_progress_generated_at"] = generated_at
    return payload


def _mapping_payload(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _status_payload_has_actionable_provider_currentness(status_payload: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping_payload(status_payload.get("current_work_unit"))
    envelope = _mapping_payload(status_payload.get("current_execution_envelope"))
    state_kind = _non_empty_text(envelope.get("state_kind")) or _non_empty_text(
        envelope.get("execution_state_kind")
    )
    if (
        _non_empty_text(current_work_unit.get("status")) != "executable_owner_action"
        and state_kind != "executable_owner_action"
    ):
        return False
    current = _mapping_payload(status_payload.get("current_executable_owner_action"))
    action_type = _non_empty_text(current_work_unit.get("action_type")) or _non_empty_text(
        current.get("action_type")
    )
    work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id")) or _non_empty_text(
        current.get("work_unit_id")
    )
    return action_type is not None and work_unit_id is not None


def _current_control_provider_admission_candidates(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    current_control_path = supervision_surfaces.latest_path(profile)
    current_control_payload = supervision_surfaces.read_json_object(current_control_path)
    return current_control_provider_admission_candidates(
        current_control_payload,
        study_root=Path(study_root),
        status_payload=status_payload,
        current_control_ref=str(current_control_path),
    )


def _progress_projection_for_diagnostic(**kwargs: Any) -> dict[str, Any]:
    payload_kwargs = dict(kwargs)
    payload_kwargs["sync_runtime_summary"] = False
    return domain_status_projection.progress_projection(**payload_kwargs)


def _request_opl_stage_attempt(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    status_payload = _managed_study_status_payload(
        _progress_projection_for_diagnostic(profile=profile, study_root=study_root)
    )
    study_id = _non_empty_text(status_payload.get("study_id")) or Path(study_root).name
    quest_id = _non_empty_text(status_payload.get("quest_id"))
    candidate_status_payload = _status_payload_with_fresh_progress_currentness(
        profile=profile,
        study_root=study_root,
        status_payload=status_payload,
    )
    provider_admission_candidates = []
    fresh_progress_has_actionable_currentness = (
        _non_empty_text(candidate_status_payload.get("study_progress_generated_at")) is not None
        and _status_payload_has_actionable_provider_currentness(candidate_status_payload)
    )
    if fresh_progress_has_actionable_currentness:
        provider_admission_candidates = _current_control_provider_admission_candidates(
            profile=profile,
            study_root=study_root,
            status_payload=candidate_status_payload,
        )
        if not provider_admission_candidates:
            provider_admission_candidates = persisted_provider_admission_candidates(
                study_root=Path(study_root),
                status_payload=candidate_status_payload,
            )
    else:
        provider_admission_candidates = persisted_provider_admission_candidates(
            study_root=Path(study_root),
            status_payload=status_payload,
        )
        if not provider_admission_candidates:
            provider_admission_candidates = _current_control_provider_admission_candidates(
                profile=profile,
                study_root=study_root,
                status_payload=candidate_status_payload,
            )
    if provider_admission_candidates:
        status_payload = candidate_status_payload
    provider_admission_identity = provider_admission_candidates[0] if provider_admission_candidates else None
    return {
        **status_payload,
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "status": "opl_stage_attempt_admission_required",
        "source": source,
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_executes_runtime_attempt": False,
        "provider_completion_is_domain_completion": False,
        "opl_stage_attempt_request": {
            "surface_kind": "mas_opl_stage_attempt_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "study_root": str(Path(study_root).expanduser().resolve()),
            "source": source,
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "hydration_owner": "one-person-lab",
            "stage_attempt_state_owner": "one-person-lab",
            "mas_runtime_recovery_retired": True,
            "provider_admission_identity": provider_admission_identity,
            "provider_admission_candidates": provider_admission_candidates,
        },
        "provider_admission_identity": provider_admission_identity,
        "provider_admission_candidates": provider_admission_candidates,
        "resume_postcondition": {
            "effective": False,
            "status": "opl_stage_attempt_admission_required",
            "typed_blocker": {
                "blocker_type": "opl_stage_attempt_admission_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "reason": "mas_runtime_attempt_execution_retired",
                "required_handoff": "Hydrate MAS DomainIntent/owner-route refs through OPL current_control_state.",
            },
        },
    }


def _materialize_opl_runtime_owner_handoff(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
    recorded_at: str,
    apply: bool,
    domain_health_diagnostic_report_path: Path | None = None,
) -> dict[str, Any] | None:
    if status_payload.get("domain_health_diagnostic_error_isolated") is True:
        return None
    study_id = _non_empty_text(status_payload.get("study_id")) or Path(study_root).name
    quest_id = _non_empty_text(status_payload.get("quest_id"))
    quest_root = _candidate_path(status_payload.get("quest_root"))
    provider_admission_candidates = persisted_provider_admission_candidates(
        study_root=Path(study_root),
        status_payload=status_payload,
    )
    provider_admission_identity = (
        provider_admission_candidates[0] if provider_admission_candidates else None
    )
    payload = {
        "surface_kind": "mas_opl_runtime_owner_handoff",
        "schema_version": 1,
        "recorded_at": recorded_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "quest_root": str(quest_root) if quest_root is not None else None,
        "status": "handoff_required",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "provider_completion_is_domain_completion": False,
        "queue_succeeded_is_domain_completion": False,
        "mas_materializes_runtime_supervision": False,
        "mas_runtime_read_model_retired": True,
        "provider_admission_identity": provider_admission_identity,
        "provider_admission_candidates": provider_admission_candidates,
        "reason": _non_empty_text(status_payload.get("reason")) or "opl_current_control_state_required",
        "next_action_summary": (
            _non_empty_text(status_payload.get("next_action_summary"))
            or "Hydrate MAS owner-route refs through OPL current_control_state; OPL owns runtime retry/resume while MAS stays refs-only."
        ),
        "opl_current_control_state_ref": {
            "owner": "one-person-lab",
            "required": True,
            "hydrate_from": "MAS DomainIntent / owner-route refs",
        },
        "refs": {
            "domain_health_diagnostic_report_path": (
                str(domain_health_diagnostic_report_path.expanduser().resolve())
                if domain_health_diagnostic_report_path is not None
                else None
            ),
        },
        "typed_blocker": {
            "blocker_type": "opl_runtime_owner_handoff_required",
            "owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "reason": "mas_runtime_supervision_retired",
            "required_handoff": "Hydrate MAS owner-route refs through OPL current_control_state.",
        },
    }
    if apply:
        handoff_path = Path(study_root).expanduser().resolve() / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["artifact_path"] = str(handoff_path)
    return payload


def _build_runtime_control_ports() -> RuntimeControlPorts:
    return RuntimeControlPorts(
        get_status=lambda **kwargs: _managed_study_status_payload(
            _progress_projection_for_diagnostic(**kwargs)
        ),
        request_opl_stage_attempt=_request_opl_stage_attempt,
        build_outer_loop_request=_build_current_domain_transition_outer_loop_request,
        dispatch_outer_loop=domain_status_projection.study_outer_loop_tick,
        materialize_non_dispatching_decision=_materialize_domain_health_diagnostic_non_dispatching_decision,
        refresh_status_after_stage_request=_refresh_managed_study_status_after_stage_request,
        materialize_opl_runtime_owner_handoff=_materialize_opl_runtime_owner_handoff,
        reconcile_health=runtime_health_kernel.reconcile_runtime_health_snapshot_from_status_payload,
        materialize_autonomy_slo=_materialize_managed_study_autonomy_slo,
        read_ready_ai_repair=read_ready_ai_doctor_repair,
        apply_ai_repair=apply_ready_ai_doctor_repair,
        read_ai_repair_lifecycle=read_ai_repair_lifecycle,
        reconcile_ai_repair_lifecycle=reconcile_ai_repair_lifecycle,
    )


def _build_current_domain_transition_outer_loop_request(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any] | None:
    tick_request = study_outer_loop.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )
    if _tick_request_is_submission_milestone_autopark(tick_request):
        return tick_request
    fallback_tick_request = domain_transition_currentness.status_domain_transition_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )
    if isinstance(fallback_tick_request, dict) and not _tick_request_matches_status_transition(
        tick_request=tick_request,
        status_payload=status_payload,
    ):
        return fallback_tick_request
    return tick_request


def _tick_request_is_submission_milestone_autopark(tick_request: object) -> bool:
    if not isinstance(tick_request, dict):
        return False
    if str(tick_request.get("decision_type") or "").strip() != "continue_same_line":
        return False
    controller_actions = tick_request.get("controller_actions")
    first_action = (
        controller_actions[0]
        if isinstance(controller_actions, list) and controller_actions and isinstance(controller_actions[0], dict)
        else {}
    )
    return (
        str(first_action.get("action_type") or "").strip() == "stop_runtime"
        and str(tick_request.get("reason") or "").strip()
        == "Human-review milestone reached; stop the live runtime and wait for explicit resume."
    )

def _tick_request_matches_status_transition(
    *,
    tick_request: object,
    status_payload: dict[str, Any],
) -> bool:
    domain_transition = status_payload.get("domain_transition")
    if not isinstance(domain_transition, dict):
        return True
    transition_unit = domain_transition.get("next_work_unit")
    if not isinstance(transition_unit, dict):
        return True
    return domain_transition_currentness.tick_request_matches_domain_transition(
        tick_request=tick_request if isinstance(tick_request, dict) else {},
        transition_action=str(domain_transition.get("controller_action") or "").strip(),
        transition_type=str(domain_transition.get("decision_type") or "").strip(),
        transition_unit_id=str(transition_unit.get("unit_id") or "").strip(),
        transition_route_target=str(domain_transition.get("route_target") or "").strip() or None,
    )


def run_domain_health_diagnostic_for_quest(
    *,
    quest_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    persist_diagnostic_reports: bool | None = None,
) -> dict[str, Any]:
    return _run_domain_health_diagnostic_for_quest_impl(
        quest_root=quest_root,
        controller_runners=controller_runners,
        apply=apply,
        persist_diagnostic_reports=persist_diagnostic_reports,
        publication_gate_refresh_mask=_publication_gate_ai_reviewer_eval_masks_return_to_gate,
    )


def run_domain_health_diagnostic_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    persist_diagnostic_reports: bool | None = None,
    profile: WorkspaceProfile | None = None,
    study_ids: tuple[str, ...] = (),
    request_opl_stage_attempts: bool = False,
    request_opl_owner_route_reconcile: bool = False,
) -> dict[str, Any]:
    report = _run_domain_health_diagnostic_for_runtime_impl(
        runtime_root=runtime_root,
        controller_runners=controller_runners or build_default_controller_runners(),
        apply=apply,
        persist_diagnostic_reports=persist_diagnostic_reports,
        run_domain_health_diagnostic_for_quest_fn=run_domain_health_diagnostic_for_quest,
        runtime_control_ports=_build_runtime_control_ports(),
        profile=profile,
        study_ids=study_ids,
        request_opl_stage_attempts=request_opl_stage_attempts,
    )
    if apply and request_opl_stage_attempts and profile is not None:
        apply_managed_study_obligation_actuator(
            report=report,
            profile=profile,
            study_ids=study_ids,
            fail_closed=False,
            phase="initial_apply",
            refresh_owner_callable_actions=lambda actions: _refresh_report_progress_currentness_after_owner_callable_actions(
                report=report,
                profile=profile,
                study_ids=study_ids,
                owner_callable_actions=actions,
            ),
        )
    if apply and request_opl_stage_attempts and request_opl_owner_route_reconcile and profile is not None:
        supervisor_tick = _run_developer_supervisor_same_tick(profile=profile, study_ids=study_ids)
        first_iteration = (supervisor_tick.get("iterations") or [{}])[0]
        report["opl_owner_route_reconcile_request"] = (
            _mapping(first_iteration).get("owner_route_reconcile") or {}
        )
        report["developer_supervisor_same_tick"] = supervisor_tick
        _refresh_report_progress_currentness_after_same_tick(
            report=report,
            profile=profile,
            study_ids=study_ids,
            supervisor_tick=supervisor_tick,
        )
        apply_managed_study_obligation_actuator(
            report=report,
            profile=profile,
            study_ids=study_ids,
            fail_closed=False,
            phase="post_owner_route_reconcile",
            refresh_owner_callable_actions=lambda actions: _refresh_report_progress_currentness_after_owner_callable_actions(
                report=report,
                profile=profile,
                study_ids=study_ids,
                owner_callable_actions=actions,
            ),
        )
    if request_opl_stage_attempts and profile is not None and not apply:
        attach_domain_action_request_materialization_preview(
            report=report,
            profile=profile,
            study_ids=study_ids,
            materialize_domain_action_requests=domain_action_request_materializer.materialize_domain_action_requests,
        )
        attach_domain_handler_owner_resolution_preview(
            report=report,
            profile=profile,
            study_ids=study_ids,
            export_family_domain_handler=owner_route_handoff.export_family_domain_handler,
        )
    if request_opl_stage_attempts and profile is not None:
        current_control_state = _materialize_report_provider_admission_current_control_state(
            profile=profile,
            report=report,
            apply=apply,
        )
        if current_control_state is not None:
            report["provider_admission_current_control_state"] = current_control_state
            _sync_report_provider_admission_current_control_state(
                report,
                current_control_state=current_control_state,
            )
    if apply and request_opl_stage_attempts and profile is not None:
        apply_managed_study_obligation_actuator(
            report=report,
            profile=profile,
            study_ids=study_ids,
            current_control_state=_mapping(report.get("provider_admission_current_control_state")),
            fail_closed=True,
            phase="final_apply_postcondition",
            refresh_owner_callable_actions=lambda actions: _refresh_report_progress_currentness_after_owner_callable_actions(
                report=report,
                profile=profile,
                study_ids=study_ids,
                owner_callable_actions=actions,
            ),
        )
    return report


def _materialize_report_provider_admission_current_control_state(
    *,
    profile: WorkspaceProfile,
    report: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any] | None:
    return _materialize_report_provider_admission_current_control_state_impl(
        profile=profile,
        report=report,
        apply=apply,
        generated_at=_non_empty_text(report.get("scanned_at")) or utc_now(),
    )


def _refresh_report_progress_currentness_after_same_tick(
    *,
    report: dict[str, Any],
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    supervisor_tick: Mapping[str, Any],
) -> None:
    if _non_empty_text(supervisor_tick.get("stop_reason")) not in {
        "provider_handoff_written_admission_pending",
        "provider_attempt_started",
        "typed_blocker_or_dispatch_blocker_observed",
        "repeat_suppressed_owner_delta_required",
        "max_passes_exhausted_owner_delta_required",
        "owner_action_projected_but_not_materialized",
    }:
        return
    refreshed = _fresh_progress_currentness_for_report(
        profile=profile,
        study_ids=_same_tick_refresh_study_ids(
            report=report,
            explicit_study_ids=study_ids,
            supervisor_tick=supervisor_tick,
        ),
    )
    if not refreshed:
        return
    current_execution_evidence = _mapping(report.get("current_execution_evidence"))
    progress_currentness = {
        key: dict(value) if isinstance(value, Mapping) else value
        for key, value in _mapping(current_execution_evidence.get("progress_currentness")).items()
    }
    progress_currentness.update(refreshed)
    current_execution_evidence["progress_currentness"] = progress_currentness
    report["current_execution_evidence"] = current_execution_evidence
    report["managed_study_actions"] = _report_managed_actions_with_progress_currentness(
        actions=[
            dict(action)
            for action in report.get("managed_study_actions") or []
            if isinstance(action, Mapping)
        ],
        progress_currentness=refreshed,
    )


def _refresh_report_progress_currentness_after_owner_callable_actions(
    *,
    report: dict[str, Any],
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    owner_callable_actions: list[dict[str, Any]],
) -> None:
    refreshed_study_ids = tuple(
        dict.fromkeys(
            item
            for item in (
                *_text_items(study_ids),
                *(
                    _non_empty_text(action.get("study_id"))
                    for action in owner_callable_actions
                    if isinstance(action, Mapping)
                ),
            )
            if item is not None
        )
    )
    refreshed = _fresh_progress_currentness_for_report(
        profile=profile,
        study_ids=refreshed_study_ids,
    )
    if not refreshed:
        return
    current_execution_evidence = _mapping(report.get("current_execution_evidence"))
    progress_currentness = {
        key: dict(value) if isinstance(value, Mapping) else value
        for key, value in _mapping(current_execution_evidence.get("progress_currentness")).items()
    }
    progress_currentness.update(refreshed)
    current_execution_evidence["progress_currentness"] = progress_currentness
    report["current_execution_evidence"] = current_execution_evidence
    report["managed_study_actions"] = _report_managed_actions_with_progress_currentness(
        actions=[
            dict(action)
            for action in report.get("managed_study_actions") or []
            if isinstance(action, Mapping)
        ],
        progress_currentness=refreshed,
    )


def _same_tick_refresh_study_ids(
    *,
    report: Mapping[str, Any],
    explicit_study_ids: tuple[str, ...],
    supervisor_tick: Mapping[str, Any],
) -> tuple[str, ...]:
    candidates: list[str] = []
    candidates.extend(_text_items(explicit_study_ids))
    candidates.extend(_text_items(supervisor_tick.get("study_ids")))
    candidates.extend(
        _non_empty_text(action.get("study_id"))
        for action in report.get("managed_study_actions") or []
        if isinstance(action, Mapping)
    )
    materialize = _mapping(supervisor_tick.get("materialize"))
    candidates.extend(
        _non_empty_text(dispatch.get("study_id"))
        for dispatch in materialize.get("default_executor_dispatches") or []
        if isinstance(dispatch, Mapping)
    )
    return tuple(dict.fromkeys(study_id for study_id in candidates if study_id is not None))


def _fresh_progress_currentness_for_report(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    if not study_ids:
        return {}
    try:
        from med_autoscience.controllers import study_progress
    except Exception:
        return {}
    refreshed: dict[str, dict[str, Any]] = {}
    for study_id in study_ids:
        try:
            progress = study_progress.read_study_progress(
                profile=profile,
                study_id=study_id,
                sync_runtime_summary=False,
                materialize_read_model_artifacts=False,
            )
        except Exception:
            continue
        if not isinstance(progress, Mapping):
            continue
        progress_currentness = {
            key: _copy_progress_currentness_value(progress.get(key))
            for key in PROGRESS_CURRENTNESS_KEYS
            if key in progress
        }
        if (generated_at := _non_empty_text(progress.get("generated_at"))) is not None:
            progress_currentness["study_progress_generated_at"] = generated_at
        if progress_currentness:
            progress_currentness["quest_id"] = _non_empty_text(progress.get("quest_id")) or study_id
            refreshed[study_id] = progress_currentness
    return refreshed


def _copy_progress_currentness_value(value: object) -> object:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, list):
        return [
            dict(item) if isinstance(item, Mapping) else item
            for item in value
        ]
    return value


def _report_managed_actions_with_progress_currentness(
    *,
    actions: list[dict[str, Any]],
    progress_currentness: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not actions:
        return []
    refreshed_actions: list[dict[str, Any]] = []
    for action in actions:
        study_id = _non_empty_text(action.get("study_id"))
        currentness = _mapping(progress_currentness.get(study_id)) if study_id is not None else {}
        if currentness:
            refreshed_actions.append({**action, **currentness})
        else:
            refreshed_actions.append(dict(action))
    return refreshed_actions


def _text_items(values: object) -> list[str]:
    return [
        text
        for value in values or []
        if (text := _non_empty_text(value)) is not None
    ]


def _run_developer_supervisor_same_tick(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...] = (),
    max_passes: int = PROGRESS_FIRST_SAME_TICK_MAX_PASSES,
) -> dict[str, Any]:
    return _run_developer_supervisor_same_tick_impl(
        profile=profile,
        study_ids=study_ids,
        max_passes=max_passes,
        owner_route_reconcile_module=owner_route_reconcile,
        domain_action_request_materializer_module=domain_action_request_materializer,
        domain_owner_action_dispatch_module=domain_owner_action_dispatch,
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--refresh-diagnostic-reports", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.quest_root) == bool(args.runtime_root):
        raise SystemExit("Specify exactly one of --quest-root or --runtime-root")
    if args.quest_root:
        result = run_domain_health_diagnostic_for_quest(
            quest_root=args.quest_root,
            apply=args.apply,
            persist_diagnostic_reports=args.apply or args.refresh_diagnostic_reports,
        )
    else:
        result = run_domain_health_diagnostic_for_runtime(
            runtime_root=args.runtime_root,
            apply=args.apply,
            persist_diagnostic_reports=args.apply or args.refresh_diagnostic_reports,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
