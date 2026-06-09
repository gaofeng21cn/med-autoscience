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
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    current_control_provider_admission_candidates,
    handoff_dispatch_path,
    handoff_work_unit_id,
    materialized_record_only_provider_handoff,
    materialized_record_only_provider_handoffs,
    persisted_provider_admission_candidates,
    provider_admission_pending_dispatch_result,
    provider_probe_has_matching_attempt,
    provider_probe_has_non_running_actions,
    study_has_running_provider_attempt,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control import (
    materialize_provider_admission_current_control_state as _materialize_provider_admission_current_control_state,
)
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
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


PROGRESS_FIRST_SAME_TICK_MAX_PASSES = 3
PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS = 2.0
PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS = 1.0
PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT = 1


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
    return payload


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
    provider_admission_candidates = persisted_provider_admission_candidates(
        study_root=Path(study_root),
        status_payload=status_payload,
    )
    if not provider_admission_candidates:
        candidate_status_payload = _status_payload_with_fresh_progress_currentness(
            profile=profile,
            study_root=study_root,
            status_payload=status_payload,
        )
        provider_admission_candidates = persisted_provider_admission_candidates(
            study_root=Path(study_root),
            status_payload=candidate_status_payload,
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
) -> dict[str, Any]:
    return _run_domain_health_diagnostic_for_quest_impl(
        quest_root=quest_root,
        controller_runners=controller_runners,
        apply=apply,
        publication_gate_refresh_mask=_publication_gate_ai_reviewer_eval_masks_return_to_gate,
    )


def run_domain_health_diagnostic_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    profile: WorkspaceProfile | None = None,
    study_ids: tuple[str, ...] = (),
    request_opl_stage_attempts: bool = False,
    request_opl_owner_route_reconcile: bool = False,
) -> dict[str, Any]:
    report = _run_domain_health_diagnostic_for_runtime_impl(
        runtime_root=runtime_root,
        controller_runners=controller_runners or build_default_controller_runners(),
        apply=apply,
        run_domain_health_diagnostic_for_quest_fn=run_domain_health_diagnostic_for_quest,
        runtime_control_ports=_build_runtime_control_ports(),
        profile=profile,
        study_ids=study_ids,
        request_opl_stage_attempts=request_opl_stage_attempts,
    )
    if apply and request_opl_stage_attempts and request_opl_owner_route_reconcile and profile is not None:
        supervisor_tick = _run_developer_supervisor_same_tick(profile=profile, study_ids=study_ids)
        first_iteration = (supervisor_tick.get("iterations") or [{}])[0]
        report["opl_owner_route_reconcile_request"] = (
            _mapping(first_iteration).get("owner_route_reconcile") or {}
        )
        report["developer_supervisor_same_tick"] = supervisor_tick
    if request_opl_stage_attempts and profile is not None:
        current_control_state = _materialize_report_provider_admission_current_control_state(
            profile=profile,
            report=report,
            apply=apply,
        )
        if current_control_state is not None:
            report["provider_admission_current_control_state"] = current_control_state
    return report


def _materialize_report_provider_admission_current_control_state(
    *,
    profile: WorkspaceProfile,
    report: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any] | None:
    candidates = [
        dict(item)
        for item in report.get("managed_study_opl_provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ]
    progress_currentness = _mapping(
        _mapping(report.get("current_execution_evidence")).get("progress_currentness")
    )
    supervisor_tick = _mapping(report.get("developer_supervisor_same_tick"))
    if supervisor_tick.get("stop_reason") == "provider_handoff_written_admission_pending":
        terminal_materialize = _mapping(supervisor_tick.get("materialize"))
        if terminal_materialize:
            candidates = _provider_admission_candidates_from_same_tick_materialize(
                materialize_result=terminal_materialize,
                fallback_candidates=candidates,
                progress_currentness=progress_currentness,
            )
    return _materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=candidates,
        generated_at=_non_empty_text(report.get("scanned_at")) or utc_now(),
        apply=apply,
        scanned_studies=_provider_admission_scanned_currentness_studies(progress_currentness),
    )


def _provider_admission_scanned_currentness_studies(
    progress_currentness: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    studies: list[dict[str, Any]] = []
    for study_id, payload in _mapping(progress_currentness).items():
        normalized_study_id = _non_empty_text(study_id)
        if normalized_study_id is None:
            continue
        current_action = _mapping(_mapping(payload).get("current_executable_owner_action"))
        if not current_action:
            continue
        next_owner = _non_empty_text(current_action.get("next_owner"))
        work_unit_id = _non_empty_text(current_action.get("work_unit_id"))
        studies.append(
            {
                "study_id": normalized_study_id,
                "quest_id": _non_empty_text(current_action.get("quest_id")) or normalized_study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "provider_admission_pending_count": 0,
                "action_queue": [],
                "current_executable_owner_action": dict(current_action),
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": next_owner,
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "progress_currentness.current_executable_owner_action",
                },
            }
        )
    return studies


def _provider_admission_candidates_from_same_tick_materialize(
    *,
    materialize_result: Mapping[str, Any],
    fallback_candidates: list[dict[str, Any]],
    progress_currentness: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    fallback_by_identity = {
        (_non_empty_text(candidate.get("study_id")), _non_empty_text(candidate.get("action_type"))): candidate
        for candidate in fallback_candidates
    }
    current_action_by_study = _same_tick_progress_current_actions(progress_currentness)
    candidates: list[dict[str, Any]] = []
    for dispatch in materialize_result.get("default_executor_dispatches") or []:
        if not isinstance(dispatch, Mapping):
            continue
        if _non_empty_text(dispatch.get("dispatch_status")) != "ready":
            continue
        study_id = _non_empty_text(dispatch.get("study_id"))
        action_type = _non_empty_text(dispatch.get("action_type"))
        base = dict(fallback_by_identity.get((study_id, action_type), {}))
        candidate = {
            **base,
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "provider_admission_pending",
            "source": _non_empty_text(base.get("source")) or "same_tick_materialized_dispatch",
            "study_id": study_id,
            "quest_id": _non_empty_text(dispatch.get("quest_id")) or _non_empty_text(base.get("quest_id")),
            "action_type": action_type,
            "work_unit_id": _non_empty_text(dispatch.get("work_unit_id"))
            or _non_empty_text(base.get("work_unit_id"))
            or handoff_work_unit_id(dispatch),
            "work_unit_fingerprint": _non_empty_text(dispatch.get("work_unit_fingerprint"))
            or _non_empty_text(dispatch.get("action_fingerprint"))
            or _non_empty_text(base.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(dispatch.get("action_fingerprint"))
            or _non_empty_text(dispatch.get("work_unit_fingerprint"))
            or _non_empty_text(base.get("action_fingerprint")),
            "dispatch_path": _non_empty_text(dispatch.get("dispatch_path"))
            or _non_empty_text(base.get("dispatch_path"))
            or handoff_dispatch_path(dispatch),
            "dispatch_authority": _non_empty_text(dispatch.get("dispatch_authority"))
            or _non_empty_text(base.get("dispatch_authority")),
            "blocked_reason": OPL_EXECUTION_AUTHORIZATION_BLOCKER,
            "next_executable_owner": _non_empty_text(dispatch.get("next_executable_owner"))
            or _non_empty_text(base.get("next_executable_owner")),
            "required_output_surface": _non_empty_text(dispatch.get("required_output_surface"))
            or _non_empty_text(base.get("required_output_surface")),
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
        }
        if candidate["study_id"] is not None and candidate["action_type"] is not None:
            current_action_identity = current_action_by_study.get(candidate["study_id"])
            if current_action_identity is not None and not _same_tick_candidate_matches_current_action(
                candidate,
                current_action_identity=current_action_identity,
            ):
                continue
            candidates.append({key: value for key, value in candidate.items() if value is not None})
    return candidates


def _same_tick_progress_current_actions(
    progress_currentness: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    current_actions: dict[str, dict[str, Any]] = {}
    for study_id, payload in _mapping(progress_currentness).items():
        normalized_study_id = _non_empty_text(study_id)
        if normalized_study_id is None:
            continue
        current = _mapping(_mapping(payload).get("current_executable_owner_action"))
        if not current:
            continue
        next_action = _mapping(current.get("next_action"))
        repair_precedence = _mapping(current.get("repair_progress_precedence"))
        allowed_actions = _same_tick_text_items(current.get("allowed_actions"))
        explicit_fingerprints = _same_tick_text_items(
            [
                current.get("work_unit_fingerprint"),
                current.get("action_fingerprint"),
                current.get("source_fingerprint"),
                repair_precedence.get("source_fingerprint"),
            ]
        )
        current_actions[normalized_study_id] = {
            "action_type": _non_empty_text(current.get("action_type")),
            "action_ids": list(
                dict.fromkeys(
                    [
                        *allowed_actions,
                        *_same_tick_text_items([current.get("action_type"), next_action.get("action_id")]),
                    ]
                )
            ),
            "work_unit_id": _non_empty_text(current.get("work_unit_id"))
            or _non_empty_text(next_action.get("action_id")),
            "explicit_fingerprints": explicit_fingerprints,
            "source_ref": _non_empty_text(current.get("source_ref"))
            or _non_empty_text(current.get("latest_owner_answer_ref")),
        }
    return current_actions


def _same_tick_candidate_matches_current_action(
    candidate: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    action_type = _non_empty_text(candidate.get("action_type"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id"))
    work_unit_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if action_type is None:
        return False
    expected_action_type = _non_empty_text(current_action_identity.get("action_type"))
    if expected_action_type is not None and action_type != expected_action_type:
        return False
    action_ids = {
        item
        for item in _same_tick_text_items(current_action_identity.get("action_ids"))
    }
    if action_ids and action_type not in action_ids:
        return False
    expected_work_unit_id = _non_empty_text(current_action_identity.get("work_unit_id"))
    if expected_work_unit_id is not None and work_unit_id != expected_work_unit_id:
        return False
    expected_fingerprints = set(_same_tick_text_items(current_action_identity.get("explicit_fingerprints")))
    if expected_fingerprints:
        return work_unit_fingerprint in expected_fingerprints
    expected_source_ref = _non_empty_text(current_action_identity.get("source_ref"))
    if expected_source_ref is not None:
        return work_unit_fingerprint is not None and expected_source_ref in work_unit_fingerprint
    return True


def _same_tick_text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _run_developer_supervisor_same_tick(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...] = (),
    max_passes: int = PROGRESS_FIRST_SAME_TICK_MAX_PASSES,
) -> dict[str, Any]:
    resolved_study_ids = tuple(study_ids) or owner_route_reconcile.resolve_owner_route_reconcile_study_ids(profile)
    retain_unscanned_studies = not bool(study_ids)
    iterations: list[dict[str, Any]] = []
    stop_reason = "max_passes_exhausted"
    carried_scan_result: dict[str, Any] | None = None
    carried_materialize_result: dict[str, Any] | None = None
    for pass_index in range(1, max(1, max_passes) + 1):
        if carried_scan_result is None:
            scan_result = owner_route_reconcile.scan_domain_routes(
                profile=profile,
                study_ids=resolved_study_ids,
                apply_safe_actions=True,
                developer_supervisor_mode="developer_apply_safe",
                live_attempt_timeout_seconds=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
                live_attempt_max_inspect_count=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
                provider_readiness_timeout_seconds=PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
                retain_unscanned_studies=retain_unscanned_studies,
            )
        else:
            scan_result = carried_scan_result
            carried_scan_result = None
        if carried_materialize_result is None:
            materialize_result = domain_action_request_materializer.materialize_domain_action_requests(
                profile=profile,
                study_ids=resolved_study_ids,
                mode="developer_apply_safe",
                apply=True,
            )
        else:
            materialize_result = carried_materialize_result
            carried_materialize_result = None
        if materialized_record_only_provider_handoff(materialize_result):
            dispatch_result = provider_admission_pending_dispatch_result(
                materialize_result=materialize_result,
            )
        else:
            dispatch_result = domain_owner_action_dispatch.dispatch_domain_owner_actions(
                profile=profile,
                study_ids=resolved_study_ids,
                action_types=(),
                mode="developer_apply_safe",
                apply=True,
                consumer_payload=materialize_result,
            )
        iteration = {
            "pass_index": pass_index,
            "owner_route_reconcile": scan_result,
            "materialize": materialize_result,
            "dispatch": dispatch_result,
            "progress_first_delta": _same_tick_delta(
                scan_result=scan_result,
                materialize_result=materialize_result,
                dispatch_result=dispatch_result,
            ),
        }
        if _same_tick_handoff_written(iteration):
            iteration["provider_admission_probe"] = owner_route_reconcile.scan_domain_routes(
                profile=profile,
                study_ids=resolved_study_ids,
                apply_safe_actions=True,
                developer_supervisor_mode="developer_apply_safe",
                persist_surfaces=True,
                live_attempt_timeout_seconds=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
                live_attempt_max_inspect_count=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
                provider_readiness_timeout_seconds=PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
                retain_unscanned_studies=retain_unscanned_studies,
            )
            provider_attempt_started = _provider_attempt_started_for_iteration(iteration)
            if (
                provider_attempt_started
                or materialized_record_only_provider_handoff(_mapping(iteration.get("materialize")))
            ):
                iteration["post_admission_materialize"] = domain_action_request_materializer.materialize_domain_action_requests(
                    profile=profile,
                    study_ids=resolved_study_ids,
                    mode="developer_apply_safe",
                    apply=True,
                )
                if provider_attempt_started and provider_probe_has_non_running_actions(_mapping(iteration["provider_admission_probe"])):
                    carried_scan_result = _mapping(iteration["provider_admission_probe"])
                    carried_materialize_result = _mapping(iteration["post_admission_materialize"])
        iterations.append(iteration)
        stop_reason = _same_tick_stop_reason(iteration)
        if stop_reason not in {
            "continue_same_tick_after_sync_owner_delta",
            "continue_same_tick_after_provider_admission_delta",
        }:
            break
    if stop_reason in {
        "continue_same_tick_after_sync_owner_delta",
        "continue_same_tick_after_provider_admission_delta",
    }:
        stop_reason = "max_passes_exhausted_owner_delta_required"
    terminal_diagnostic = _same_tick_terminal_diagnostic(
        stop_reason=stop_reason,
        iterations=iterations,
    )
    return {
        "surface": "developer_supervisor_same_tick",
        "schema_version": 1,
        "mode": "developer_apply_safe",
        "study_ids": list(resolved_study_ids),
        "max_passes": max(1, max_passes),
        "pass_count": len(iterations),
        "stop_reason": stop_reason,
        "actions": [
            "owner-route-reconcile",
            "domain-action-request-materialize",
            "domain-owner-action-dispatch",
        ],
        "provider_probe_budget": {
            "live_attempt_timeout_seconds": PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
            "provider_readiness_timeout_seconds": PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
            "live_attempt_max_inspect_count": PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
            "scope": "focused_same_tick_owner_route_scan",
        },
        "iterations": iterations,
        "owner_route_reconcile": _mapping(iterations[-1].get("owner_route_reconcile")) if iterations else {},
        "materialize": _same_tick_terminal_materialize(iterations),
        "dispatch": _mapping(iterations[-1].get("dispatch")) if iterations else {},
        "progress_first_terminal_diagnostic": terminal_diagnostic,
        "owner_boundaries": {
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
        },
    }


def _same_tick_delta(
    *,
    scan_result: Mapping[str, Any],
    materialize_result: Mapping[str, Any],
    dispatch_result: Mapping[str, Any],
) -> dict[str, Any]:
    total_default_executor_dispatch_count = _int_value(materialize_result.get("default_executor_dispatch_count"))
    ready_default_executor_dispatch_count = (
        _int_value(materialize_result.get("ready_default_executor_dispatch_count"))
        if "ready_default_executor_dispatch_count" in materialize_result
        else total_default_executor_dispatch_count
    )
    blocked_default_executor_dispatch_count = (
        _int_value(materialize_result.get("blocked_default_executor_dispatch_count"))
        if "blocked_default_executor_dispatch_count" in materialize_result
        else _materialized_dispatch_status_count(materialize_result, "blocked")
    )
    return {
        "scan_action_count": _count(scan_result, "action_queue"),
        "materialized_request_count": _int_value(materialize_result.get("request_task_count")),
        "default_executor_dispatch_count": ready_default_executor_dispatch_count,
        "default_executor_dispatch_total_count": total_default_executor_dispatch_count,
        "ready_default_executor_dispatch_count": ready_default_executor_dispatch_count,
        "blocked_default_executor_dispatch_count": blocked_default_executor_dispatch_count,
        "dispatch_execution_count": _int_value(dispatch_result.get("execution_count")),
        "dispatch_executed_count": _int_value(dispatch_result.get("executed_count")),
        "dispatch_blocked_count": _int_value(dispatch_result.get("blocked_count")),
        "dispatch_repeat_suppressed_count": _int_value(dispatch_result.get("repeat_suppressed_count")),
        "codex_dispatch_count": _int_value(dispatch_result.get("codex_dispatch_count")),
        "handoff_ready_count": _execution_status_count(dispatch_result, "handoff_ready"),
    }


def _same_tick_stop_reason(iteration: Mapping[str, Any]) -> str:
    delta = _mapping(iteration.get("progress_first_delta"))
    if _same_tick_handoff_written(iteration):
        provider_admission_probe = _mapping(iteration.get("provider_admission_probe"))
        if _provider_attempt_started_for_iteration(iteration):
            if provider_probe_has_non_running_actions(provider_admission_probe):
                return "continue_same_tick_after_provider_admission_delta"
            return "provider_attempt_started"
        return "provider_handoff_written_admission_pending"
    if _int_value(delta.get("blocked_default_executor_dispatch_count")) > 0:
        return "typed_blocker_or_dispatch_blocker_observed"
    if _same_tick_provider_admission_blocker_written(iteration):
        return "provider_handoff_written_admission_pending"
    if _int_value(delta.get("dispatch_blocked_count")) > 0:
        return "typed_blocker_or_dispatch_blocker_observed"
    if _int_value(delta.get("dispatch_repeat_suppressed_count")) > 0:
        return "repeat_suppressed_owner_delta_required"
    if _int_value(delta.get("dispatch_executed_count")) > 0:
        return "continue_same_tick_after_sync_owner_delta"
    if _int_value(delta.get("default_executor_dispatch_count")) > 0:
        return "dispatch_materialized_but_not_selected"
    if _int_value(delta.get("scan_action_count")) > 0:
        return "owner_action_projected_but_not_materialized"
    return "no_owner_action_remaining"


def _same_tick_handoff_written(iteration: Mapping[str, Any]) -> bool:
    delta = _mapping(iteration.get("progress_first_delta"))
    return (
        _int_value(delta.get("codex_dispatch_count")) > 0
        or _int_value(delta.get("handoff_ready_count")) > 0
        or materialized_record_only_provider_handoff(_mapping(iteration.get("materialize")))
        or _same_tick_provider_admission_blocker_written(iteration)
    )


def _same_tick_provider_admission_blocker_written(iteration: Mapping[str, Any]) -> bool:
    return bool(_same_tick_provider_admission_blocker_executions(iteration))


def _same_tick_provider_admission_blocker_executions(iteration: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    dispatch = _mapping(iteration.get("dispatch"))
    current_identities = _same_tick_current_dispatch_identities(iteration)
    return [
        execution
        for execution in dispatch.get("executions") or []
        if isinstance(execution, Mapping)
        and _same_tick_provider_admission_blocker_execution(
            execution,
            current_identities=current_identities,
        )
    ]


def _same_tick_provider_admission_blocker_execution(
    execution: Mapping[str, Any],
    *,
    current_identities: list[Mapping[str, str]] | None = None,
) -> bool:
    if not (
        _non_empty_text(execution.get("execution_status")) == "blocked"
        and _non_empty_text(execution.get("blocked_reason")) == OPL_EXECUTION_AUTHORIZATION_BLOCKER
        and execution.get("provider_attempt_or_lease_required") is True
        and _non_empty_text(execution.get("dispatch_path")) is not None
        and _non_empty_text(execution.get("dispatch_authority")) is not None
    ):
        return False
    if current_identities is None:
        return True
    return any(
        _same_tick_identity_matches_execution(identity, execution=execution)
        for identity in current_identities
    )


def _same_tick_current_dispatch_identities(iteration: Mapping[str, Any]) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    identities.extend(
        _same_tick_action_identities(
            _mapping(iteration.get("owner_route_reconcile")).get("action_queue"),
        )
    )
    identities.extend(
        identity
        for identity in _same_tick_action_identities(
            _mapping(iteration.get("materialize")).get("default_executor_dispatches"),
        )
        if _same_tick_identity_has_currentness_anchor(identity)
    )
    return _dedupe_same_tick_identities(identities)


def _same_tick_action_identities(items: object) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    for item in items or []:
        if not isinstance(item, Mapping):
            continue
        identity = {
            key: value
            for key, value in {
                "study_id": _non_empty_text(item.get("study_id")),
                "action_type": _non_empty_text(item.get("action_type")),
                "work_unit_id": (
                    _non_empty_text(item.get("work_unit_id"))
                    or _non_empty_text(item.get("next_work_unit"))
                    or _non_empty_text(item.get("controller_work_unit_id"))
                    or _non_empty_text(_mapping(item.get("controller_next_work_unit")).get("unit_id"))
                    or handoff_work_unit_id(item)
                ),
                "action_fingerprint": _non_empty_text(item.get("action_fingerprint")),
                "work_unit_fingerprint": _non_empty_text(item.get("work_unit_fingerprint")),
                "dispatch_path": handoff_dispatch_path(item),
            }.items()
            if value is not None
        }
        if len(identity) > 1:
            identities.append(identity)
    return identities


def _same_tick_identity_matches_execution(
    identity: Mapping[str, str],
    *,
    execution: Mapping[str, Any],
) -> bool:
    for key in ("study_id", "action_type", "work_unit_id"):
        expected = _non_empty_text(identity.get(key))
        if expected is None:
            continue
        observed = _non_empty_text(execution.get(key))
        if observed is None:
            return False
        if observed != expected:
            return False
    expected_fingerprints = {
        value
        for key in ("action_fingerprint", "work_unit_fingerprint")
        if (value := _non_empty_text(identity.get(key))) is not None
    }
    if expected_fingerprints:
        observed_fingerprints = {
            value
            for key in ("action_fingerprint", "work_unit_fingerprint")
            if (value := _non_empty_text(execution.get(key))) is not None
        }
        if not observed_fingerprints or observed_fingerprints.isdisjoint(expected_fingerprints):
            return False
    expected_dispatch = _non_empty_text(identity.get("dispatch_path"))
    if expected_dispatch is None:
        return True
    observed_dispatch = _non_empty_text(execution.get("dispatch_path"))
    if observed_dispatch is None:
        return False
    return _same_tick_dispatch_ref_matches(expected_dispatch, observed_dispatch)


def _same_tick_identity_has_currentness_anchor(identity: Mapping[str, str]) -> bool:
    return any(
        _non_empty_text(identity.get(key)) is not None
        for key in ("work_unit_id", "action_fingerprint", "work_unit_fingerprint", "dispatch_path")
    )


def _same_tick_dispatch_ref_matches(expected: str, observed: str) -> bool:
    normalized_expected = expected.replace("\\", "/")
    normalized_observed = observed.replace("\\", "/")
    return (
        normalized_expected == normalized_observed
        or normalized_expected.endswith(f"/{normalized_observed}")
        or normalized_observed.endswith(f"/{normalized_expected}")
    )


def _dedupe_same_tick_identities(identities: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    result: list[dict[str, str]] = []
    for identity in identities:
        key = tuple(sorted(identity.items()))
        if key in seen:
            continue
        seen.add(key)
        result.append(identity)
    return result


def _provider_attempt_started(scan_result: Mapping[str, Any]) -> bool:
    for study in scan_result.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        if study.get("running_provider_attempt") is True and (
            _non_empty_text(study.get("active_stage_attempt_id"))
            or _non_empty_text(study.get("active_run_id"))
            or _non_empty_text(study.get("active_workflow_id"))
        ):
            return True
    return False


def _provider_attempt_started_for_iteration(iteration: Mapping[str, Any]) -> bool:
    provider_admission_probe = _mapping(iteration.get("provider_admission_probe"))
    identities = _same_tick_handoff_identities(iteration)
    if not identities:
        return _provider_attempt_started(provider_admission_probe)
    return all(
        provider_probe_has_matching_attempt(provider_admission_probe, identity=identity)
        for identity in identities
    )


def _same_tick_handoff_identities(iteration: Mapping[str, Any]) -> list[dict[str, str]]:
    dispatch = _mapping(iteration.get("dispatch"))
    identities: list[dict[str, str]] = []
    for handoff in materialized_record_only_provider_handoffs(
        _mapping(iteration.get("materialize"))
    ):
        identity = {
            key: value
            for key, value in {
                "study_id": _non_empty_text(handoff.get("study_id")),
                "action_type": _non_empty_text(handoff.get("action_type")),
                "work_unit_id": handoff_work_unit_id(handoff),
                "dispatch_path": handoff_dispatch_path(handoff),
            }.items()
            if value is not None
        }
        if len(identity) > 1:
            identities.append(identity)
    for execution in dispatch.get("executions") or []:
        if not isinstance(execution, Mapping):
            continue
        if not (
            execution.get("will_start_llm") is True
            or _non_empty_text(execution.get("execution_status")) == "handoff_ready"
            or execution in _same_tick_provider_admission_blocker_executions(iteration)
        ):
            continue
        identity = {
            key: value
            for key in ("study_id", "action_type", "work_unit_id", "dispatch_path")
            if (value := _non_empty_text(execution.get(key))) is not None
        }
        if len(identity) > 1:
            identities.append(identity)
    return identities


def _same_tick_terminal_materialize(iterations: list[dict[str, Any]]) -> dict[str, Any]:
    if not iterations:
        return {}
    last_iteration = iterations[-1]
    post_admission_materialize = last_iteration.get("post_admission_materialize")
    if isinstance(post_admission_materialize, Mapping):
        return dict(post_admission_materialize)
    return _mapping(last_iteration.get("materialize"))


def _same_tick_terminal_diagnostic(
    *,
    stop_reason: str,
    iterations: list[dict[str, Any]],
) -> dict[str, Any]:
    last_iteration = iterations[-1] if iterations else {}
    last_delta = _mapping(last_iteration.get("progress_first_delta"))
    provider_admission_probe = _mapping(last_iteration.get("provider_admission_probe"))
    requires_next_owner_delta = stop_reason in {
        "repeat_suppressed_owner_delta_required",
        "max_passes_exhausted_owner_delta_required",
    }
    requires_provider_admission = stop_reason == "provider_handoff_written_admission_pending"
    requires_dispatch_blocker_resolution = (
        stop_reason == "typed_blocker_or_dispatch_blocker_observed"
        and (
            _int_value(last_delta.get("blocked_default_executor_dispatch_count")) > 0
            or _int_value(last_delta.get("dispatch_blocked_count")) > 0
        )
    )
    return {
        "surface": "progress_first_developer_supervisor_terminal_diagnostic",
        "schema_version": 1,
        "stop_reason": stop_reason,
        "same_tick_terminal_projection": _same_tick_terminal_projection(
            stop_reason=stop_reason,
            last_iteration=last_iteration,
            last_delta=last_delta,
            provider_admission_probe=provider_admission_probe,
        ),
        "requires_next_owner_delta": requires_next_owner_delta,
        "requires_provider_admission": requires_provider_admission,
        "requires_dispatch_blocker_resolution": requires_dispatch_blocker_resolution,
        "dispatch_blocker_summary": (
            _dispatch_blocker_summary(last_iteration)
            if requires_dispatch_blocker_resolution
            else None
        ),
        "provider_admission_probe": (
            {
                "observed": False,
                "running_provider_attempt_count": 0,
                "study_ids": [
                    study.get("study_id")
                    for study in provider_admission_probe.get("studies") or []
                    if isinstance(study, Mapping) and _non_empty_text(study.get("study_id"))
                ],
            }
            if requires_provider_admission
            else (
                {
                    "observed": True,
                    "running_provider_attempt_count": sum(
                        1
                        for study in provider_admission_probe.get("studies") or []
                        if isinstance(study, Mapping) and study.get("running_provider_attempt") is True
                    ),
                }
                if stop_reason == "provider_attempt_started"
                else None
            )
        ),
        "post_admission_materialize": (
            {
                "observed": isinstance(last_iteration.get("post_admission_materialize"), Mapping),
                "default_executor_dispatch_count": _int_value(
                    _mapping(last_iteration.get("post_admission_materialize")).get("default_executor_dispatch_count")
                ),
                "ready_default_executor_dispatch_count": _int_value(
                    _mapping(last_iteration.get("post_admission_materialize")).get(
                        "ready_default_executor_dispatch_count"
                    )
                ),
            }
            if isinstance(last_iteration.get("post_admission_materialize"), Mapping)
            else None
        ),
        "last_iteration_delta": dict(last_delta),
        "next_forced_delta": (
            {
                "required_delta_kind": (
                    "deliverable_progress_delta_or_domain_owner_receipt_or_typed_blocker"
                ),
                "reason": stop_reason,
                "target_surface": {
                    "surface_ref": "MAS owner receipt, domain typed blocker, or paper-facing deliverable delta",
                    "owner": "med-autoscience",
                },
                "acceptance_refs": [
                    "deliverable_progress_delta",
                    "domain_owner_receipt_ref",
                    "domain_typed_blocker_ref",
                    "human_gate_or_stop_loss_ref",
                ],
            }
            if requires_next_owner_delta
            else (
                {
                    "required_delta_kind": "opl_provider_attempt_admission",
                    "reason": stop_reason,
                    "target_surface": {
                        "surface_ref": "OPL provider attempt receipt with active stage attempt id",
                        "owner": "one-person-lab",
                    },
                    "acceptance_refs": [
                        "running_provider_attempt",
                        "active_stage_attempt_id",
                        "active_run_id",
                    ],
                    "recommended_owner_commands": [
                        "opl family-runtime worker status --provider temporal",
                        "opl family-runtime scheduler tick --provider temporal",
                    ],
                }
                if requires_provider_admission
                else (
                    {
                        "required_delta_kind": "dispatch_blocker_resolution_or_owner_route_currentness_delta",
                        "reason": stop_reason,
                        "target_surface": {
                            "surface_ref": "owner-route currentness basis, dispatch typed blocker, or domain owner receipt",
                            "owner": "med-autoscience",
                        },
                        "acceptance_refs": [
                            "currentness_contract.missing_required_fields == []",
                            "default_executor_dispatch.blocked_reason",
                            "domain_typed_blocker_ref",
                            "domain_owner_receipt_ref",
                        ],
                    }
                    if requires_dispatch_blocker_resolution
                    else None
                )
            )
        ),
        "forbidden_next_actions": (
            [
                "repeat_receipt_reconcile_without_owner_delta",
                "repeat_read_model_reconcile_without_owner_delta",
                "start_new_provider_attempt_for_same_source_without_owner_delta",
            ]
            if requires_next_owner_delta or requires_provider_admission or requires_dispatch_blocker_resolution
            else []
        ),
    }


def _same_tick_terminal_projection(
    *,
    stop_reason: str,
    last_iteration: Mapping[str, Any],
    last_delta: Mapping[str, Any],
    provider_admission_probe: Mapping[str, Any],
) -> dict[str, Any]:
    provider_attempt_running = _provider_attempt_started_for_iteration(last_iteration)
    stable_typed_blocker_observed = stop_reason == "typed_blocker_or_dispatch_blocker_observed" and (
        _int_value(last_delta.get("blocked_default_executor_dispatch_count")) > 0
        or _int_value(last_delta.get("dispatch_blocked_count")) > 0
    )
    owner_delta_produced = stop_reason in {
        "repeat_suppressed_owner_delta_required",
        "max_passes_exhausted_owner_delta_required",
    }
    terminal_state = _same_tick_terminal_state(
        stop_reason=stop_reason,
        owner_delta_produced=owner_delta_produced,
        provider_attempt_running=provider_attempt_running,
        stable_typed_blocker_observed=stable_typed_blocker_observed,
    )
    return {
        "terminal_state": terminal_state,
        "owner_delta_produced": owner_delta_produced,
        "provider_attempt_running": provider_attempt_running,
        "stable_typed_blocker_observed": stable_typed_blocker_observed,
        "provider_handoff_written": _same_tick_handoff_written(last_iteration),
    }


def _same_tick_terminal_state(
    *,
    stop_reason: str,
    owner_delta_produced: bool,
    provider_attempt_running: bool,
    stable_typed_blocker_observed: bool,
) -> str:
    if provider_attempt_running:
        return "provider_attempt_running"
    if stable_typed_blocker_observed:
        return "stable_typed_blocker_observed"
    if owner_delta_produced:
        if stop_reason == "max_passes_exhausted_owner_delta_required":
            return "owner_delta_produced"
        return "owner_delta_required"
    return stop_reason


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _count(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, list):
        return len(value)
    return _int_value(value)


def _execution_status_count(payload: Mapping[str, Any], status: str) -> int:
    return sum(
        1
        for item in payload.get("executions") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("execution_status")) == status
    )


def _materialized_dispatch_status_count(payload: Mapping[str, Any], status: str) -> int:
    return sum(
        1
        for item in payload.get("default_executor_dispatches") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("dispatch_status")) == status
    )


def _dispatch_blocker_summary(iteration: Mapping[str, Any]) -> dict[str, Any]:
    delta = _mapping(iteration.get("progress_first_delta"))
    materialize = _mapping(iteration.get("materialize"))
    dispatch = _mapping(iteration.get("dispatch"))
    blocked_reasons: list[str] = []
    blocked_actions: list[str] = []
    for item in materialize.get("default_executor_dispatches") or []:
        if not isinstance(item, Mapping):
            continue
        if _non_empty_text(item.get("dispatch_status")) != "blocked":
            continue
        if (reason := _non_empty_text(item.get("blocked_reason"))) is not None and reason not in blocked_reasons:
            blocked_reasons.append(reason)
        if (action_type := _non_empty_text(item.get("action_type"))) is not None and action_type not in blocked_actions:
            blocked_actions.append(action_type)
    for item in dispatch.get("executions") or []:
        if not isinstance(item, Mapping):
            continue
        if _non_empty_text(item.get("execution_status")) != "blocked":
            continue
        if (reason := _non_empty_text(item.get("blocked_reason"))) is not None and reason not in blocked_reasons:
            blocked_reasons.append(reason)
        if (action_type := _non_empty_text(item.get("action_type"))) is not None and action_type not in blocked_actions:
            blocked_actions.append(action_type)
    return {
        "blocked_default_executor_dispatch_count": _int_value(
            delta.get("blocked_default_executor_dispatch_count")
        ),
        "dispatch_blocked_count": _int_value(delta.get("dispatch_blocked_count")),
        "blocked_reasons": blocked_reasons,
        "blocked_actions": blocked_actions,
    }


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.quest_root) == bool(args.runtime_root):
        raise SystemExit("Specify exactly one of --quest-root or --runtime-root")
    if args.quest_root:
        result = run_domain_health_diagnostic_for_quest(quest_root=args.quest_root, apply=args.apply)
    else:
        result = run_domain_health_diagnostic_for_runtime(runtime_root=args.runtime_root, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
