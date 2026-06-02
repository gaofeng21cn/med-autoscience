from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.progress_first_receipt_identity import (
    canonical_work_unit_identity_from_completion,
    consumed_ai_reviewer_receipt_matches_transition_work_unit,
    gate_clearing_batch_receipt_consumption_for_transition,
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers import study_macro_state
from med_autoscience.controllers.study_state_matrix_parts.current_owner_handoff import (
    effective_transition_for_monitoring,
    monitoring_has_authoritative_owner_action,
)
from med_autoscience.study_manual_finish import _delivered_package_ready


def resolve_study_ids(profile: Any) -> tuple[str, ...]:
    studies_root = Path(profile.studies_root).expanduser().resolve()
    if not studies_root.exists():
        return ()
    study_ids: list[str] = []
    for child in sorted(studies_root.iterdir(), key=lambda item: item.name):
        if child.is_dir() and (child / "study.yaml").is_file():
            study_ids.append(child.name)
    return tuple(study_ids)


def build_study_state_matrix(
    *,
    profile: Any,
    domain_status_projection: Any,
    study_ids: Iterable[str] | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_ids = tuple(study_ids or ()) or resolve_study_ids(profile)
    studies: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    monitoring_summaries: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for study_id in resolved_study_ids:
        try:
            status = _dict(
                domain_status_projection.progress_projection(
                    profile=profile,
                    study_id=study_id,
                    study_root=None,
                    entry_mode=entry_mode,
                )
            )
        except Exception as exc:
            status = _status_projection_error(
                profile=profile,
                study_id=study_id,
                exc=exc,
            )
        delivered_package = _delivered_package_observation(status=status)
        if delivered_package.get("observed") is True:
            status = {**status, "delivered_package": delivered_package}
        study_root = _study_root_from_status(profile=profile, study_id=study_id, status=status)
        macro = _projection_error_macro_state(study_id=study_id, status=status) or _read_materialized_macro_state(
            study_root=study_root
        ) or study_macro_state.derive_study_macro_state(
            study_id=study_id,
            status=status,
            progress={},
        )
        active_run_id = _resolved_active_run_id(status=status, macro_state=macro)
        running_provider_attempt = _resolved_running_provider_attempt(status)
        writer_state = str(macro["writer_state"])
        counts[writer_state] = counts.get(writer_state, 0) + 1
        transition = study_domain_transition_table.project_domain_transition(
            study_id=study_id,
            study_root=study_root,
            status=status,
            macro_state=macro,
            active_run_id=active_run_id,
            running_provider_attempt=running_provider_attempt,
            delivered_package=delivered_package,
        )
        monitoring = _progress_first_monitoring_summary(
            status=status,
            transition=transition,
            active_run_id=active_run_id,
            study_root=study_root,
        )
        effective_transition = effective_transition_for_monitoring(
            transition=transition,
            monitoring=monitoring,
        )
        supervisor_bundle = _supervisor_monitoring_bundle(
            status=status,
            monitoring=monitoring,
            transition=effective_transition,
            study_root=study_root,
        )
        monitoring_summaries.append(monitoring)
        transitions.append(effective_transition)
        studies.append(
            {
                "study_id": study_id,
                "quest_id": _text(status.get("quest_id")),
                "quest_status": _text(status.get("quest_status")),
                "active_run_id": active_run_id,
                "monitoring": monitoring,
                "progress_first_monitoring_summary": monitoring,
                "supervisor_monitoring_bundle": supervisor_bundle,
                "delivered_package": delivered_package or None,
                "study_macro_state": macro,
                "domain_transition": effective_transition,
            }
        )
    return {
        "surface": "study_state_matrix",
        "schema_version": 1,
        "workspace_root": str(Path(profile.workspace_root).expanduser().resolve()),
        "study_count": len(studies),
        "counts": counts,
        "progress_first_tick_accounting": _progress_first_tick_accounting(monitoring_summaries),
        "studies": studies,
        "domain_transition_table": study_domain_transition_table.build_domain_transition_table(transitions),
    }


def render_study_state_matrix_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Study State Matrix",
        "",
        f"- workspace_root: `{payload.get('workspace_root')}`",
        f"- study_count: `{payload.get('study_count')}`",
        "",
        "| study_id | writer | user_next | reason | active_run_id | provider | next_work_unit |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for study in payload.get("studies") or []:
        study_payload = _dict(study)
        macro = _dict(study_payload.get("study_macro_state"))
        bundle = _dict(study_payload.get("supervisor_monitoring_bundle"))
        provider_status = _dict(bundle.get("provider_status"))
        next_work_unit = _dict(bundle.get("next_work_unit"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _text(study_payload.get("study_id")) or "",
                    _text(macro.get("writer_state")) or "",
                    _text(macro.get("user_next")) or "",
                    _text(macro.get("reason")) or "",
                    _text(study_payload.get("active_run_id")) or "",
                    _text(provider_status.get("status")) or "",
                    _text(next_work_unit.get("unit_id")) or _text(bundle.get("next_work_unit")) or "",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Domain Transition Table",
            "",
            "| study_id | decision_type | route_target | next_work_unit | controller_action | owner | blocker |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in _dict(_dict(payload).get("domain_transition_table")).get("rows") or []:
        transition = _dict(row)
        next_work_unit = _dict(transition.get("next_work_unit"))
        typed_blocker = _dict(transition.get("typed_blocker"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _text(transition.get("study_id")) or "",
                    _text(transition.get("decision_type")) or "",
                    _text(transition.get("route_target")) or "",
                    _text(next_work_unit.get("unit_id")) or "",
                    _text(transition.get("controller_action")) or "",
                    _text(transition.get("owner")) or "",
                    _text(typed_blocker.get("blocker_id")) or "",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return {}


def _study_root_from_status(*, profile: Any, study_id: str, status: Mapping[str, Any]) -> Path:
    if text := _text(status.get("study_root")):
        return Path(text).expanduser().resolve()
    return Path(profile.studies_root).expanduser().resolve() / study_id


def _read_materialized_macro_state(*, study_root: Path) -> dict[str, Any] | None:
    path = study_root / study_macro_state.SNAPSHOT_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    macro = dict(payload)
    if _text(macro.get("surface")) != "study_macro_state":
        return None
    if _text(macro.get("writer_state")) not in study_macro_state.WRITER_STATES:
        return None
    return macro


def _delivered_package_observation(*, status: Mapping[str, Any]) -> dict[str, Any]:
    if status.get("status_projection_error"):
        return {"observed": False}
    study_root_text = _text(status.get("study_root"))
    if not study_root_text:
        return {}
    study_root = Path(study_root_text).expanduser().resolve()
    manuscript_root = study_root / "manuscript"
    candidates = (
        (
            "manuscript/current_package",
            manuscript_root / "current_package",
            manuscript_root / "current_package.zip",
            True,
        ),
        (
            "manuscript/submission_package",
            manuscript_root / "submission_package",
            None,
            False,
        ),
    )
    for surface, package_root, zip_path, require_administrative_todo in candidates:
        if _delivered_package_ready(
            study_root=study_root,
            package_root=package_root,
            require_zip_path=zip_path,
            require_administrative_todo=require_administrative_todo,
        ):
            return {
                "surface": surface,
                "observed": True,
                "package_root": str(package_root),
                "zip_path": str(zip_path) if zip_path is not None else None,
                "authority_role": "user_visible_milestone_package_not_quality_authority",
            }
    return {"observed": False}


def _status_projection_error(*, profile: Any, study_id: str, exc: Exception) -> dict[str, Any]:
    message = str(exc) or exc.__class__.__name__
    study_root = Path(profile.studies_root).expanduser().resolve() / study_id
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_status": "projection_error",
        "active_run_id": None,
        "status_projection_error": {
            "error_type": exc.__class__.__name__,
            "message": message,
        },
    }


def _projection_error_macro_state(*, study_id: str, status: Mapping[str, Any]) -> dict[str, Any] | None:
    projection_error = _dict(status.get("status_projection_error")) or _dict(status.get("projection_error"))
    if not projection_error:
        return None
    return {
        "surface": "study_macro_state",
        "schema_version": 1,
        "study_id": study_id,
        "writer_state": "conflict",
        "user_next": "inspect",
        "reason": "truth_conflict",
        "details": {"status_projection_error": projection_error},
        "conditions": [
            {
                "type": "StatusProjectionError",
                "status": "true",
                "reason": "progress projection failed and must be inspected before routing",
            }
        ],
        "source_fingerprint": f"study-macro-state:projection-error:{study_id}",
    }


def _resolved_active_run_id(*, status: Mapping[str, Any], macro_state: Mapping[str, Any]) -> str | None:
    nested_progress = _dict(status.get("progress_projection"))
    if _text(macro_state.get("writer_state")) == "parked":
        return _text(_dict(macro_state.get("details")).get("active_run_id"))
    return (
        _text(_dict(status.get("supervision")).get("active_run_id"))
        or _text(_dict(status.get("progress_first_monitoring_summary")).get("active_run_id"))
        or _text(_dict(nested_progress.get("progress_first_monitoring_summary")).get("active_run_id"))
        or _text(_dict(status.get("opl_current_control_state_handoff")).get("active_run_id"))
        or _text(status.get("active_run_id"))
        or _text(_dict(status.get("study_truth_snapshot")).get("active_run_id"))
        or _text(_dict(_dict(status.get("study_truth_snapshot")).get("execution_owner")).get("active_run_id"))
        or _text(_dict(macro_state.get("details")).get("active_run_id"))
    )


def _resolved_running_provider_attempt(status: Mapping[str, Any]) -> bool | None:
    projection = _dict(status.get("progress_projection"))
    monitoring = _dict(status.get("progress_first_monitoring_summary")) or _dict(
        projection.get("progress_first_monitoring_summary")
    )
    if isinstance(monitoring.get("running_provider_attempt"), bool):
        return monitoring.get("running_provider_attempt")
    runtime_liveness = _dict(status.get("runtime_liveness_audit"))
    if isinstance(runtime_liveness.get("running_provider_attempt"), bool):
        return runtime_liveness.get("running_provider_attempt")
    opl_control = _dict(status.get("opl_current_control_state_handoff")) or _dict(
        status.get("opl_current_control_state")
    )
    if isinstance(opl_control.get("running_provider_attempt"), bool):
        return opl_control.get("running_provider_attempt")
    return None


def _progress_first_monitoring_summary(
    *,
    status: Mapping[str, Any],
    transition: Mapping[str, Any],
    active_run_id: str | None,
    study_root: Path,
) -> dict[str, Any]:
    projection = _dict(status.get("progress_projection"))
    existing = _dict(status.get("progress_first_monitoring_summary")) or _dict(
        projection.get("progress_first_monitoring_summary")
    )
    transition_consumed_owner_action = _transition_consumed_owner_action(transition)
    gate_clearing_dispatch_consumption = _gate_clearing_batch_dispatch_consumption(
        study_root=study_root,
        transition=transition,
    )
    existing_authoritative_owner_action = (
        _existing_authoritative_owner_action(existing) and not gate_clearing_dispatch_consumption
    )
    existing_next_work_unit = _dict(existing.get("next_work_unit")) or _text(existing.get("next_work_unit"))
    next_work_unit = (
        existing_next_work_unit
        if existing_authoritative_owner_action and existing_next_work_unit
        else _dict(existing.get("next_work_unit")) or _dict(transition.get("next_work_unit"))
    )
    use_transition_consumed_owner_action = (
        transition_consumed_owner_action
        and not existing_authoritative_owner_action
        and not gate_clearing_dispatch_consumption
    )
    if use_transition_consumed_owner_action:
        next_work_unit = _dict(transition.get("next_work_unit")) or next_work_unit
    existing_owner_action = (
        _text(existing.get("next_owner")) is not None
        or _text(existing.get("controller_action")) is not None
        or _work_unit_id(existing.get("next_work_unit")) is not None
    )
    existing_dispatch_consumption = _dict(existing.get("dispatch_consumption"))
    transition_dispatch_consumption = _transition_dispatch_consumption(transition)
    dispatch_consumption = (
        gate_clearing_dispatch_consumption or existing_dispatch_consumption or transition_dispatch_consumption
    )
    existing_receipt_consumed = _text(existing_dispatch_consumption.get("consumption_status")) in {
        "consumed",
        "receipt_consumed",
        "completed",
    }
    transition_receipt_consumed = _text(transition_dispatch_consumption.get("consumption_status")) in {
        "consumed",
        "receipt_consumed",
        "completed",
    }
    existing_consumed_same_ai_reviewer_record = _existing_consumed_ai_reviewer_record(
        existing=existing,
        dispatch_consumption=dispatch_consumption,
    )
    existing_consumed_same_gate_clearing_batch = bool(gate_clearing_dispatch_consumption)
    owner_action_current = (
        existing_authoritative_owner_action
        or (
            existing_owner_action
            and not existing_consumed_same_ai_reviewer_record
            and not existing_consumed_same_gate_clearing_batch
        )
        or use_transition_consumed_owner_action
    )
    typed_blocker = ({} if use_transition_consumed_owner_action else _dict(existing.get("typed_blocker"))) or (
        {} if existing_owner_action or existing_receipt_consumed else _dict(transition.get("typed_blocker"))
    )
    current_blockers = [] if use_transition_consumed_owner_action else _string_list(existing.get("current_blockers"))
    if not current_blockers and typed_blocker:
        current_blockers = [
            text
            for item in (
                typed_blocker.get("blocker_id"),
                typed_blocker.get("blocker_type"),
                typed_blocker.get("summary"),
            )
            if (text := _text(item)) is not None
        ]
    return {
        "surface": existing.get("surface") or "study_state_matrix_progress_first_monitoring_summary",
        "schema_version": existing.get("schema_version") or 1,
        "authority": existing.get("authority") or "refs_only_observability",
        "study_id": _text(existing.get("study_id")) or _text(status.get("study_id")),
        "current_stage": _text(existing.get("current_stage")) or _text(status.get("current_stage")),
        "paper_stage": _text(existing.get("paper_stage")) or _text(status.get("paper_stage")),
        "active_run_id": _text(existing.get("active_run_id")) or active_run_id,
        "active_stage_attempt_id": _text(existing.get("active_stage_attempt_id")),
        "active_workflow_id": _text(existing.get("active_workflow_id")),
        "running_provider_attempt": existing.get("running_provider_attempt"),
        "worker_liveness": _dict(existing.get("worker_liveness")),
        "execution_state_kind": (
            "executable_owner_action"
            if use_transition_consumed_owner_action or existing_authoritative_owner_action
            else (
                "blocked_typed_owner"
                if existing_consumed_same_ai_reviewer_record and typed_blocker
                else (
                    "receipt_consumed"
                    if existing_consumed_same_ai_reviewer_record or existing_consumed_same_gate_clearing_batch
                    else _text(existing.get("execution_state_kind"))
                )
            )
        )
        or ("receipt_consumed" if transition_receipt_consumed else None),
        "owner_action_current": owner_action_current,
        "next_owner": (
            _text(transition.get("owner"))
            if use_transition_consumed_owner_action
            else _text(existing.get("next_owner"))
        )
        or _text(transition.get("owner")),
        "route_target": (
            _text(transition.get("route_target"))
            if use_transition_consumed_owner_action
            else _text(existing.get("route_target"))
        )
        or _text(transition.get("route_target")),
        "controller_action": (
            _text(transition.get("controller_action"))
            if use_transition_consumed_owner_action
            else _text(existing.get("controller_action"))
        )
        or _text(transition.get("controller_action")),
        "next_work_unit": next_work_unit or _text(existing.get("next_work_unit")),
        "typed_blocker": typed_blocker or None,
        "current_blockers": current_blockers[:12],
        "progress_delta_classification": _text(existing.get("progress_delta_classification"))
        or _text(status.get("progress_delta_classification")),
        "paper_progress_delta_counted": existing.get("paper_progress_delta_counted"),
        "platform_repair_delta_counted": existing.get("platform_repair_delta_counted"),
        "next_forced_delta": _dict(existing.get("next_forced_delta")),
        "stage_progress_log": _dict(existing.get("stage_progress_log")),
        "latest_terminal_stage": _dict(existing.get("latest_terminal_stage")) or None,
        "dispatch_consumption": dispatch_consumption,
        "foreground_write_policy": _dict(existing.get("foreground_write_policy")),
        "source_refs": _string_list(existing.get("source_refs")),
        "publication_eval": _publication_eval_monitoring_summary(study_root=study_root),
        "source": "progress_projection",
    }


def _supervisor_monitoring_bundle(
    *,
    status: Mapping[str, Any],
    monitoring: Mapping[str, Any],
    transition: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    publication_eval = _dict(monitoring.get("publication_eval")) or _publication_eval_monitoring_summary(
        study_root=study_root
    )
    return {
        "surface": "study_state_matrix_supervisor_monitoring_bundle",
        "schema_version": 1,
        "authority": "refs_only_supervisor_read_model",
        "current_stage": _text(monitoring.get("current_stage")) or _text(status.get("current_stage")),
        "paper_stage": _text(monitoring.get("paper_stage")) or _text(status.get("paper_stage")),
        "active_run_id": _text(monitoring.get("active_run_id")),
        "active_stage_attempt_id": _text(monitoring.get("active_stage_attempt_id")),
        "provider_status": _provider_status(monitoring),
        "worker_liveness": _dict(monitoring.get("worker_liveness")) or None,
        "latest_24h_timeline_refs": _latest_24h_timeline_refs(monitoring),
        "latest_closeout": _latest_closeout_summary(monitoring),
        "publication_eval": publication_eval or None,
        "verdict": _dict(publication_eval.get("verdict")) or _text(publication_eval.get("verdict")),
        "currentness": publication_eval.get("currentness"),
        "typed_blocker": _dict(monitoring.get("typed_blocker")) or _dict(transition.get("typed_blocker")) or None,
        "next_owner": _text(monitoring.get("next_owner")) or _text(transition.get("owner")),
        "controller_action": _text(monitoring.get("controller_action")) or _text(transition.get("controller_action")),
        "next_work_unit": _dict(monitoring.get("next_work_unit"))
        or _dict(transition.get("next_work_unit"))
        or _text(monitoring.get("next_work_unit")),
        "authority_boundary": {
            "refs_only": True,
            "can_write_study_truth": False,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _existing_authoritative_owner_action(existing: Mapping[str, Any]) -> bool:
    if _dict(existing.get("typed_blocker")):
        return False
    if _text(existing.get("execution_state_kind")) != "executable_owner_action":
        return False
    if _existing_consumed_ai_reviewer_record(
        existing=existing,
        dispatch_consumption=_dict(existing.get("dispatch_consumption")),
    ):
        return False
    return (
        _text(existing.get("next_owner")) is not None
        or _text(existing.get("controller_action")) is not None
        or _work_unit_id(existing.get("next_work_unit")) is not None
    )


def _provider_status(monitoring: Mapping[str, Any]) -> dict[str, Any]:
    running = monitoring.get("running_provider_attempt")
    if running is True:
        status = "running_provider_attempt"
    elif running is False:
        status = "provider_not_running"
    else:
        status = "provider_liveness_unknown"
    return {
        "status": status,
        "running_provider_attempt": running if isinstance(running, bool) else None,
        "active_workflow_id": _text(monitoring.get("active_workflow_id")),
        "execution_state_kind": _text(monitoring.get("execution_state_kind")),
    }


def _transition_consumed_owner_action(transition: Mapping[str, Any]) -> bool:
    if _dict(transition.get("typed_blocker")):
        return False
    completion = _dict(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if _consumed_receipt_matches_transition_work_unit(transition=transition, completion=completion):
        return False
    return (
        _text(transition.get("owner")) is not None
        or _text(transition.get("controller_action")) is not None
        or bool(_dict(transition.get("next_work_unit")))
    )


def _transition_dispatch_consumption(transition: Mapping[str, Any]) -> dict[str, Any]:
    completion = _dict(transition.get("completion_receipt_consumption"))
    execution = _dict(transition.get("default_executor_execution_receipt_consumption"))
    if not completion and not execution:
        return {}
    identity = canonical_work_unit_identity_from_completion(completion or execution)
    return {
        "consumption_status": _text(completion.get("consumption_status"))
        or _text(completion.get("status"))
        or _text(execution.get("consumption_status"))
        or _text(execution.get("status"))
        or "receipt_consumed",
        "receipt_ref": _text(completion.get("receipt_ref")) or _text(execution.get("receipt_ref")),
        "receipt_kind": _text(completion.get("receipt_kind")) or _text(execution.get("receipt_kind")),
        "execution_status": _text(execution.get("execution_status")),
        "action_fingerprint": _text(completion.get("action_fingerprint"))
        or _text(execution.get("action_fingerprint")),
        "work_unit_id": _text(identity.get("work_unit_id")),
        "work_unit_fingerprint": _text(identity.get("work_unit_fingerprint")),
        "canonical_work_unit_identity": identity or None,
    }


def _gate_clearing_batch_dispatch_consumption(
    *,
    study_root: Path,
    transition: Mapping[str, Any],
) -> dict[str, Any]:
    path = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, Mapping):
        return {}
    receipt = gate_clearing_batch_receipt_consumption_for_transition(
        transition=transition,
        record=payload,
    )
    return dict(receipt or {})


def _existing_consumed_ai_reviewer_record(
    *,
    existing: Mapping[str, Any],
    dispatch_consumption: Mapping[str, Any],
) -> bool:
    if _text(dispatch_consumption.get("consumption_status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if _text(existing.get("next_owner")) != "ai_reviewer":
        return False
    if _text(existing.get("controller_action")) != "return_to_ai_reviewer_workflow":
        return False
    completion = {
        **dict(dispatch_consumption),
        "status": _text(dispatch_consumption.get("consumption_status")) or _text(dispatch_consumption.get("status")),
        "receipt_kind": _text(dispatch_consumption.get("receipt_kind")) or "ai_reviewer_publication_eval",
    }
    transition = {
        "decision_type": "ai_reviewer_re_eval",
        "controller_action": existing.get("controller_action"),
        "next_work_unit": existing.get("next_work_unit"),
        "source_refs": existing.get("source_refs"),
        "work_unit_fingerprint": existing.get("work_unit_fingerprint"),
    }
    return _consumed_receipt_matches_transition_work_unit(transition=transition, completion=completion)


def _consumed_receipt_matches_transition_work_unit(
    *,
    transition: Mapping[str, Any],
    completion: Mapping[str, Any],
) -> bool:
    return consumed_ai_reviewer_receipt_matches_transition_work_unit(
        transition=transition,
        completion=completion,
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _latest_24h_timeline_refs(monitoring: Mapping[str, Any]) -> dict[str, Any]:
    stage_log = _dict(monitoring.get("stage_progress_log"))
    latest_terminal_stage = _dict(monitoring.get("latest_terminal_stage"))
    refs = _string_list(stage_log.get("attempt_refs"))
    refs.extend(_string_list(monitoring.get("source_refs")))
    if source_path := _text(latest_terminal_stage.get("source_path")):
        refs.append(source_path)
    if closeout_ref := _text(_latest_closeout_summary(monitoring).get("ref")):
        refs.append(closeout_ref)
    return {
        "window_hours": 24,
        "refs": _dedupe(refs)[:20],
        "stage_progress_log": stage_log or None,
        "latest_terminal_stage_ref": _text(latest_terminal_stage.get("source_path")),
    }


def _latest_closeout_summary(monitoring: Mapping[str, Any]) -> dict[str, Any]:
    latest_terminal_stage = _dict(monitoring.get("latest_terminal_stage"))
    closeout_refs = _string_list(latest_terminal_stage.get("closeout_refs")) or [
        ref for ref in _string_list(monitoring.get("source_refs")) if "closeout" in ref
    ]
    return {
        "ref": closeout_refs[0] if closeout_refs else _text(latest_terminal_stage.get("source_path")),
        "stage_attempt_id": _text(latest_terminal_stage.get("stage_attempt_id")),
        "stage_id": _text(latest_terminal_stage.get("stage_id")),
        "status": _text(latest_terminal_stage.get("status")),
        "outcome": _text(latest_terminal_stage.get("outcome")),
        "remaining_blockers": _string_list(latest_terminal_stage.get("remaining_blockers")),
    }


def _publication_eval_monitoring_summary(*, study_root: Path) -> dict[str, Any]:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "ref": str(path),
            "observed": False,
        }
    if not isinstance(payload, Mapping):
        return {
            "ref": str(path),
            "observed": False,
        }
    reviewer_os = _dict(payload.get("reviewer_operating_system"))
    return {
        "ref": str(path),
        "observed": True,
        "status": _text(payload.get("status")),
        "eval_id": _text(payload.get("eval_id")),
        "domain_ready_verdict": _text(payload.get("domain_ready_verdict")),
        "verdict": _dict(payload.get("verdict")) or _text(payload.get("verdict")),
        "currentness": _dict(reviewer_os.get("currentness_checks")) or _dict(payload.get("currentness_checks")) or None,
        "assessment_provenance": _dict(payload.get("assessment_provenance")) or None,
    }


def _progress_first_tick_accounting(monitoring_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    study_items = _ranked_progress_first_study_items(
        [_progress_first_tick_study_item(summary) for summary in monitoring_summaries]
    )
    return {
        "surface": "progress_first_tick_accounting",
        "schema_version": 1,
        "authority": "refs_only_observability",
        "expected_owner_action_count": sum(
            item["monitoring_status"] in {"running", "ready_for_dispatch", "stalled_unconsumed_action"}
            for item in study_items
        ),
        "ready_for_owner_action_count": sum(
            item["monitoring_status"] in {"ready_for_dispatch", "stalled_unconsumed_action"}
            for item in study_items
        ),
        "running_provider_attempt_count": sum(item["running_provider_attempt"] is True for item in study_items),
        "typed_blocker_count": sum(item["monitoring_status"] == "blocked_typed_owner" for item in study_items),
        "human_gate_count": sum(item["monitoring_status"] == "human_gate" for item in study_items),
        "owner_route_contract_blocker_count": sum(
            item["monitoring_status"] == "blocked_owner_route_contract" for item in study_items
        ),
        "unconsumed_owner_action_count": sum(
            item["monitoring_status"] == "stalled_unconsumed_action" for item in study_items
        ),
        "overdue_owner_pickup_count": sum(item["owner_pickup_overdue"] is True for item in study_items),
        "missing_closeout_semantics_count": sum(item["missing_closeout_semantics"] is True for item in study_items),
        "generic_target_surface_count": sum(
            item["target_surface_specificity"] == "generic_route_obligation_fallback" for item in study_items
        ),
        "throughput_bottleneck_counts": _throughput_bottleneck_counts(study_items),
        "throughput_bottlenecks": [dict(item) for item in study_items],
        "studies": study_items,
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _progress_first_tick_study_item(summary: Mapping[str, Any]) -> dict[str, Any]:
    dispatch_consumption = _dict(summary.get("dispatch_consumption"))
    latest_terminal_stage = _dict(summary.get("latest_terminal_stage"))
    semantic = _dict(latest_terminal_stage.get("semantic_completeness"))
    telemetry = _dict(latest_terminal_stage.get("telemetry_completeness"))
    next_forced_delta = _dict(summary.get("next_forced_delta"))
    target_surface_specificity = _target_surface_specificity(next_forced_delta)
    missing_closeout_semantics = bool(latest_terminal_stage) and _text(semantic.get("status")) not in {
        None,
        "complete",
    }
    telemetry_status = _text(telemetry.get("status")) if telemetry else None
    missing_stage_telemetry = bool(latest_terminal_stage) and telemetry_status not in {None, "complete"}
    owner_route_contract_blocker = _owner_route_contract_blocker(
        latest_terminal_stage=latest_terminal_stage,
        missing_closeout_semantics=missing_closeout_semantics,
        next_forced_delta=next_forced_delta,
        target_surface_specificity=target_surface_specificity,
    )
    monitoring_status = _progress_first_monitoring_status(
        summary=summary,
        dispatch_consumption=dispatch_consumption,
        owner_route_contract_blocker=owner_route_contract_blocker,
    )
    return {
        "study_id": _text(summary.get("study_id")),
        "monitoring_status": monitoring_status,
        "active_run_id": _text(summary.get("active_run_id")),
        "running_provider_attempt": summary.get("running_provider_attempt") is True,
        "next_owner": _text(summary.get("next_owner")),
        "controller_action": _text(summary.get("controller_action")),
        "next_work_unit": _dict(summary.get("next_work_unit")) or _text(summary.get("next_work_unit")),
        "typed_blocker": _dict(summary.get("typed_blocker")) or None,
        "dispatch_consumption": dispatch_consumption or None,
        "owner_pickup_overdue": _owner_pickup_overdue(dispatch_consumption),
        "target_surface_specificity": target_surface_specificity,
        "missing_explicit_target_surface": next_forced_delta.get("missing_explicit_target_surface") is True,
        "owner_route_contract_blocker": owner_route_contract_blocker,
        "missing_closeout_semantics": missing_closeout_semantics,
        "missing_closeout_semantic_fields": _string_list(semantic.get("missing_fields")),
        "telemetry_completeness": telemetry_status,
        "missing_telemetry_fields": _string_list(telemetry.get("missing_fields")),
        "missing_stage_telemetry": missing_stage_telemetry,
        "throughput_bottleneck": _throughput_bottleneck(
            monitoring_status=monitoring_status,
            owner_pickup_overdue=_owner_pickup_overdue(dispatch_consumption),
            target_surface_specificity=target_surface_specificity,
            missing_closeout_semantics=missing_closeout_semantics,
            missing_stage_telemetry=missing_stage_telemetry,
        ),
    }


def _ranked_progress_first_study_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(items, key=_throughput_priority_key)
    for index, item in enumerate(ranked, start=1):
        item["priority_rank"] = index
    return ranked


def _throughput_bottleneck_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        bottleneck = _text(item.get("throughput_bottleneck")) or "observability_only"
        counts[bottleneck] = counts.get(bottleneck, 0) + 1
    return counts


def _target_surface_specificity(next_forced_delta: Mapping[str, Any]) -> str | None:
    explicit = _text(next_forced_delta.get("target_surface_specificity"))
    if explicit is not None:
        return explicit
    diagnostic = _dict(next_forced_delta.get("target_surface_diagnostic"))
    specificity = _text(diagnostic.get("specificity"))
    if specificity == "precise":
        return "explicit_owner_route_target"
    if specificity == "generic_fallback":
        return "generic_route_obligation_fallback"
    return None


def _throughput_priority_key(item: Mapping[str, Any]) -> tuple[int, str]:
    status = _text(item.get("monitoring_status"))
    if item.get("owner_pickup_overdue") is True:
        rank = 10
    elif status == "blocked_owner_route_contract":
        rank = 15
    elif status == "stalled_unconsumed_action":
        rank = 20
    elif status == "ready_for_dispatch":
        rank = 30
    elif status == "running":
        rank = 40
    elif status == "blocked_typed_owner":
        rank = 50
    elif status == "human_gate":
        rank = 60
    elif item.get("missing_closeout_semantics") is True:
        rank = 70
    elif item.get("missing_stage_telemetry") is True:
        rank = 75
    elif status == "receipt_consumed":
        rank = 80
    else:
        rank = 90
    return (rank, _text(item.get("study_id")) or "")


def _throughput_bottleneck(
    *,
    monitoring_status: str,
    owner_pickup_overdue: bool,
    target_surface_specificity: str | None,
    missing_closeout_semantics: bool,
    missing_stage_telemetry: bool,
) -> str:
    if owner_pickup_overdue:
        return "owner_pickup_overdue"
    if monitoring_status == "blocked_owner_route_contract":
        if target_surface_specificity == "generic_route_obligation_fallback":
            return "generic_target_surface"
        if missing_closeout_semantics:
            return "missing_closeout_semantics"
        return "owner_route_contract_blocker"
    if monitoring_status == "stalled_unconsumed_action":
        return "ready_owner_action_unconsumed"
    if monitoring_status == "ready_for_dispatch":
        return "ready_owner_action"
    if monitoring_status == "running":
        return "running_provider_attempt"
    if monitoring_status == "blocked_typed_owner":
        return "typed_blocker"
    if monitoring_status == "human_gate":
        return "human_gate"
    if target_surface_specificity == "generic_route_obligation_fallback":
        return "generic_target_surface"
    if missing_closeout_semantics:
        return "missing_closeout_semantics"
    if missing_stage_telemetry:
        return "missing_stage_telemetry"
    return "observability_only"


def _progress_first_monitoring_status(
    *,
    summary: Mapping[str, Any],
    dispatch_consumption: Mapping[str, Any],
    owner_route_contract_blocker: str | None,
) -> str:
    if summary.get("running_provider_attempt") is True:
        return "running"
    if _is_human_gate(summary):
        return "human_gate"
    if _is_typed_owner_blocker(summary):
        return "blocked_typed_owner"
    consumption_status = _text(dispatch_consumption.get("consumption_status"))
    owner_action_current = summary.get("owner_action_current")
    if owner_action_current is True or (
        owner_action_current is None
        and (_text(summary.get("next_owner")) is not None or _text(summary.get("controller_action")) is not None)
    ):
        if owner_route_contract_blocker is not None:
            return "blocked_owner_route_contract"
        if consumption_status in {"unconsumed", "stale", "overdue"} or _owner_pickup_overdue(dispatch_consumption):
            return "stalled_unconsumed_action"
        return "ready_for_dispatch"
    if _dict(summary.get("typed_blocker")):
        return "blocked_typed_owner"
    if consumption_status in {"consumed", "receipt_consumed", "completed"}:
        return "receipt_consumed"
    return "observability_only"


def _owner_route_contract_blocker(
    *,
    latest_terminal_stage: Mapping[str, Any],
    missing_closeout_semantics: bool,
    next_forced_delta: Mapping[str, Any],
    target_surface_specificity: str | None,
) -> str | None:
    if target_surface_specificity == "generic_route_obligation_fallback":
        return "owner_route_target_surface_required"
    if next_forced_delta.get("missing_explicit_target_surface") is True:
        return "owner_route_target_surface_required"
    if missing_closeout_semantics and latest_terminal_stage:
        return "typed_closeout_semantics_required"
    return None


def _is_typed_owner_blocker(summary: Mapping[str, Any]) -> bool:
    if not _dict(summary.get("typed_blocker")):
        return False
    return _text(summary.get("execution_state_kind")) in {"typed_blocker", "blocked_typed_owner"}


def _is_human_gate(summary: Mapping[str, Any]) -> bool:
    if _text(summary.get("progress_delta_classification")) == "human_gate":
        return True
    typed_blocker = _dict(summary.get("typed_blocker"))
    return _text(typed_blocker.get("owner")) in {"user", "physician", "pi"} or _text(
        typed_blocker.get("blocker_id")
    ) in {"human_gate", "study_user_decision_gate"}


def _owner_pickup_overdue(dispatch_consumption: Mapping[str, Any]) -> bool:
    if dispatch_consumption.get("owner_pickup_overdue") is True:
        return True
    hours = dispatch_consumption.get("unconsumed_duration_hours")
    return isinstance(hours, int | float) and not isinstance(hours, bool) and hours > 0


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "build_study_state_matrix",
    "render_study_state_matrix_markdown",
    "resolve_study_ids",
]
