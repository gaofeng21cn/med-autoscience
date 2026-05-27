from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any



SCHEMA_VERSION = 1
WRITER_STATES = ("live", "queued", "parked", "conflict")
USER_NEXT_STATES = ("watch", "submit_info", "repair", "revise", "runtime_handoff", "none", "inspect")
REASONS = (
    "runtime",
    "external_info",
    "stop_loss",
    "user_stop",
    "quality",
    "truth_conflict",
    "unknown",
)

SNAPSHOT_RELATIVE_PATH = Path("artifacts/runtime/study_macro_state/latest.json")

_EXTERNAL_INFO_REASONS = frozenset(
    {
        "quest_waiting_for_submission_metadata",
        "quest_waiting_for_submission_metadata_but_auto_resume_disabled",
        "external_metadata_pending",
        "external_metadata_gap",
    }
)

_PACKAGE_READY_PARKED_STATES = frozenset(
    {
        "package_ready_handoff",
        "external_metadata_pending",
    }
)

_STOP_LOSS_STATES = frozenset(
    {
        "stop_loss_recommended",
        "publishability_stop_loss",
    }
)

_USER_STOP_STATES = frozenset(
    {
        "user_stopped",
        "manual_stop",
        "manual_hold",
    }
)


def derive_study_macro_state(
    *,
    study_id: str,
    status: Mapping[str, Any],
    progress: Mapping[str, Any] | None = None,
    publication_eval: Mapping[str, Any] | None = None,
    controller_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    progress_payload = _mapping(progress)
    truth = _mapping(status.get("study_truth_snapshot")) or _mapping(progress_payload.get("study_truth_snapshot"))
    route = _mapping(progress_payload.get("owner_route")) or _mapping(status.get("owner_route"))
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress_payload.get("runtime_health_snapshot"))
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress_payload.get("auto_runtime_parked"))
    details = _base_details(
        truth=truth,
        status=status,
        progress=progress_payload,
        route=route,
        publication_eval=_mapping(publication_eval),
        controller_decision=_mapping(controller_decision),
    )

    if _truth_conflict(status=status, progress=progress_payload, truth=truth):
        return _state(
            study_id=study_id,
            writer_state="conflict",
            user_next="inspect",
            reason="truth_conflict",
            details=details,
            conditions=[_condition("TruthConflict", "true", "status surfaces disagree on writer ownership")],
        )

    redrive_route = _runtime_redrive_route(status=status)
    if redrive_route is not None and not _live_status_active_run_id(status=status, truth=truth):
        return _state(
            study_id=study_id,
            writer_state="queued",
            user_next="repair",
            reason="quality",
            details={
                **details,
                "decision_type": _text(redrive_route.get("decision_type")),
                "route_target": _text(redrive_route.get("route_target")),
                "next_work_unit": _text(_mapping(redrive_route.get("next_work_unit")).get("unit_id")),
                "route_owner": _text(redrive_route.get("owner")),
            },
            conditions=[_condition("DomainTransitionRedrive", "true", "current domain transition names an owner work unit")],
        )

    if active_run_id := _active_run_id(status=status, progress=progress_payload, truth=truth):
        return _state(
            study_id=study_id,
            writer_state="live",
            user_next="watch",
            reason="runtime",
            details={**details, "active_run_id": active_run_id},
            conditions=[_condition("LiveWriter", "true", "managed runtime has an active run")],
        )

    if _is_submit_info_state(status=status, progress=progress_payload, auto_parked=auto_parked):
        return _state(
            study_id=study_id,
            writer_state="parked",
            user_next="submit_info",
            reason="external_info",
            details={
                **details,
                "missing_external_info": _missing_external_info(status=status, progress=progress_payload),
                "reopen_allowed": True,
                "reopen_mode": "external_info_or_revision_intake",
                "package_delivered": True,
            },
            conditions=[_condition("ExternalInfoPending", "true", "submission package waits for external metadata")],
        )

    stop_kind = _stop_kind(status=status, progress=progress_payload, truth=truth)
    if stop_kind is not None:
        package_delivered = _package_delivered(truth=truth, status=status, progress=progress_payload)
        final_line_decision = _final_line_decision(status=status, progress=progress_payload, truth=truth)
        terminal_abandon = _is_terminal_abandon(final_line_decision)
        return _state(
            study_id=study_id,
            writer_state="parked",
            user_next="none",
            reason=stop_kind,
            details={
                **details,
                "stop_origin": _text(progress_payload.get("stop_origin")) or _text(status.get("stop_origin")),
                "package_delivered": package_delivered,
                "reopen_allowed": False if terminal_abandon else True,
                "reopen_mode": "closed" if terminal_abandon else "new_plan_required",
                "final_line_decision": final_line_decision if terminal_abandon else None,
            },
            conditions=[
                _condition(
                    "TerminalAbandon" if terminal_abandon else "StoppedForPublishability",
                    "true",
                    (
                        "study line is explicitly closed and not eligible for automatic reopen"
                        if terminal_abandon
                        else "study is parked until a new plan is supplied"
                    ),
                )
            ],
        )

    if _is_opl_runtime_handoff_queued(status=status, progress=progress_payload, route=route, runtime_health=runtime_health):
        return _state(
            study_id=study_id,
            writer_state="queued",
            user_next="runtime_handoff",
            reason="runtime",
            details=details,
            conditions=[_condition("OplRuntimeHandoffQueued", "true", "runtime owner route requires OPL handoff")],
        )

    return _state(
        study_id=study_id,
        writer_state="parked",
        user_next="inspect",
        reason="unknown",
        details=details,
        conditions=[_condition("StateObserved", "unknown", "no macro state dominance rule matched")],
    )


def materialize_study_macro_state_snapshot(
    *,
    study_root: Path,
    snapshot: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    snapshot_path = resolved_study_root / SNAPSHOT_RELATIVE_PATH
    payload = _snapshot_payload(snapshot)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result: dict[str, Any] = {
        "surface": "study_macro_state_materialization",
        "snapshot_path": str(snapshot_path.resolve()),
        "index": None,
        "index_status": "file_authority_only",
    }
    if db_path is not None:
        result["ignored_db_path"] = str(Path(db_path).expanduser().resolve())
    return result


def _state(
    *,
    study_id: str,
    writer_state: str,
    user_next: str,
    reason: str,
    details: Mapping[str, Any],
    conditions: list[dict[str, Any]],
) -> dict[str, Any]:
    if writer_state not in WRITER_STATES:
        raise ValueError(f"unknown writer_state: {writer_state}")
    if user_next not in USER_NEXT_STATES:
        raise ValueError(f"unknown user_next: {user_next}")
    if reason not in REASONS:
        raise ValueError(f"unknown macro state reason: {reason}")
    normalized_details = {key: value for key, value in dict(details).items() if value not in (None, "", [], {})}
    source = {
        "study_id": study_id,
        "writer_state": writer_state,
        "user_next": user_next,
        "reason": reason,
        "details": normalized_details,
        "conditions": conditions,
    }
    return {
        "surface": "study_macro_state",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "writer_state": writer_state,
        "user_next": user_next,
        "reason": reason,
        "details": normalized_details,
        "conditions": conditions,
        "source_fingerprint": _fingerprint(source),
    }


def _snapshot_payload(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(snapshot)
    payload.setdefault("snapshot_id", _text(snapshot.get("source_fingerprint")) or _fingerprint(snapshot))
    return payload


def _base_details(
    *,
    truth: Mapping[str, Any],
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    route: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "truth_epoch": _text(truth.get("truth_epoch")) or _text(truth.get("authority_epoch")),
        "source_signature": _text(truth.get("source_signature")),
        "quest_status": _text(status.get("quest_status")),
        "paper_stage": _text(progress.get("paper_stage")),
        "journal_target": _text(progress.get("journal_target")) or _text(status.get("journal_target")),
        "format_profile": _text(progress.get("format_profile")) or _text(status.get("format_profile")),
        "decision_owner": _text(route.get("next_owner")) or _text(_mapping(controller_decision.get("owner_route")).get("next_owner")),
        "publication_owner": _text(_mapping(publication_eval.get("assessment_provenance")).get("owner")),
    }


def _is_submit_info_state(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    auto_parked: Mapping[str, Any],
) -> bool:
    reason = _text(status.get("reason")) or _text(progress.get("reason"))
    parked_state = _text(auto_parked.get("parked_state")) or _text(progress.get("parked_state"))
    if reason in _EXTERNAL_INFO_REASONS:
        return True
    if parked_state in _PACKAGE_READY_PARKED_STATES:
        return True
    if _is_completed_delivery_state(status=status, progress=progress):
        return True
    missing = _missing_external_info(status=status, progress=progress)
    return bool(missing) and _text(status.get("quest_status")) in {"completed", "paused", "stopped"}


def _stop_kind(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    truth: Mapping[str, Any],
) -> str | None:
    quality = _mapping(truth.get("quality_state"))
    quality_state = _text(quality.get("state"))
    if quality_state in _USER_STOP_STATES:
        return "user_stop"
    if quality_state in _STOP_LOSS_STATES:
        return "stop_loss"
    candidates = {
        _text(status.get("reason")),
        _text(progress.get("reason")),
        _text(progress.get("parked_state")),
        _text(_mapping(status.get("auto_runtime_parked")).get("parked_state")),
        _text(progress.get("paper_stage")),
        _text(_mapping(status.get("publication_supervisor_state")).get("supervisor_phase")),
    }
    if any(item in _STOP_LOSS_STATES or item == "publishability_stop_loss_recommended" for item in candidates):
        return "stop_loss"
    if any(item in _USER_STOP_STATES for item in candidates):
        return "user_stop"
    if "quest_waiting_for_explicit_wakeup_after_manual_hold" in candidates:
        return "user_stop"
    return None


def _final_line_decision(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    truth: Mapping[str, Any],
) -> dict[str, Any]:
    for candidate in (
        truth.get("final_line_decision"),
        status.get("final_line_decision"),
        progress.get("final_line_decision"),
        _mapping(truth.get("quality_state")).get("final_line_decision"),
        _mapping(status.get("quality_state")).get("final_line_decision"),
        _mapping(progress.get("quality_state")).get("final_line_decision"),
    ):
        mapping = _mapping(candidate)
        if mapping:
            return dict(mapping)
    return {}


def _is_terminal_abandon(final_line_decision: Mapping[str, Any]) -> bool:
    return (
        _text(final_line_decision.get("decision")) in {"abandon", "final_abandon", "close"}
        and final_line_decision.get("reopen_allowed") is False
    )


def _is_opl_runtime_handoff_queued(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    route: Mapping[str, Any],
    runtime_health: Mapping[str, Any],
) -> bool:
    allowed = {_text(item) for item in route.get("allowed_actions") or []}
    allowed.discard(None)
    if _text(route.get("next_owner")) == "one-person-lab" and _text(route.get("owner_reason")) in {
        "runtime_controller_redrive_required",
        "abnormal_stopped_runtime_resume_required",
    }:
        return True
    if _text(runtime_health.get("canonical_runtime_action")) == "recover_runtime":
        reason = _text(status.get("reason")) or _text(progress.get("reason"))
        return reason not in _EXTERNAL_INFO_REASONS
    return False


def _truth_conflict(*, status: Mapping[str, Any], progress: Mapping[str, Any], truth: Mapping[str, Any]) -> bool:
    active_run_id = _active_run_id(status=status, progress=progress, truth=truth)
    if active_run_id and _text(_mapping(truth.get("execution_owner")).get("owner")) == "controller_stop":
        return True
    if _text(status.get("quest_status")) == "running" and _text(progress.get("current_stage")) == "auto_runtime_parked":
        return True
    return False


def _active_run_id(*, status: Mapping[str, Any], progress: Mapping[str, Any], truth: Mapping[str, Any]) -> str | None:
    if _text(status.get("quest_status")) in {"paused", "stopped", "completed"}:
        return None
    if _runtime_redrive_route(status=status) is not None and not _live_status_active_run_id(status=status, truth=truth):
        return None
    runtime_audit = _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit"))
    liveness = _mapping(status.get("runtime_liveness_audit"))
    if runtime_audit.get("worker_running") is False or liveness.get("worker_running") is False:
        return None
    if _text(status.get("runtime_liveness_status")) in {"none", "not_live", "stale"}:
        return None
    health = _mapping(status.get("runtime_health_snapshot"))
    if (
        _text(health.get("canonical_runtime_action")) == "external_supervisor_required"
        and health.get("retry_budget_remaining") == 0
    ):
        return None
    return (
        _text(status.get("active_run_id"))
        or _text(truth.get("active_run_id"))
        or _text(_mapping(truth.get("execution_owner")).get("active_run_id"))
        or _text(progress.get("active_run_id"))
        or _text(_mapping(progress.get("supervision")).get("active_run_id"))
    )


def _runtime_redrive_route(*, status: Mapping[str, Any]) -> dict[str, Any] | None:
    transition = _mapping(status.get("domain_transition"))
    if _text(transition.get("decision_type")) in {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
        "route_back_same_line",
    }:
        return transition
    return None


def _live_status_active_run_id(*, status: Mapping[str, Any], truth: Mapping[str, Any]) -> str | None:
    del truth
    if _text(status.get("quest_status")) in {"paused", "stopped", "completed", "waiting_for_user"}:
        return None
    runtime_audit = _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit"))
    liveness = _mapping(status.get("runtime_liveness_audit"))
    if runtime_audit.get("worker_running") is False or liveness.get("worker_running") is False:
        return None
    if _text(status.get("runtime_liveness_status")) in {"none", "not_live", "stale", "parked"}:
        return None
    health = _mapping(status.get("runtime_health_snapshot"))
    worker_liveness = _mapping(health.get("worker_liveness_state"))
    if _text(worker_liveness.get("state")) in {"not_live", "parked", "stale"}:
        return None
    return (
        _text(status.get("active_run_id"))
        or _text(liveness.get("active_run_id"))
        or _text(runtime_audit.get("active_run_id"))
    )


def _missing_external_info(*, status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    candidates = (
        _mapping(status.get("submission_metadata")).get("missing_external_info"),
        _mapping(progress.get("submission_metadata")).get("missing_external_info"),
        status.get("missing_external_info"),
        progress.get("missing_external_info"),
    )
    for candidate in candidates:
        if isinstance(candidate, list):
            return [_text(item) for item in candidate if _text(item) is not None]
    return []


def _package_delivered(*, truth: Mapping[str, Any], status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    package = _mapping(truth.get("package_state"))
    authority_state = _text(package.get("authority_state"))
    if authority_state in {"current", "fresh", "provisionally_current_for_epoch"}:
        return True
    if _mapping(status.get("delivered_package")).get("observed") is True:
        return True
    if _mapping(progress.get("delivered_package")).get("observed") is True:
        return True
    if status.get("package_delivered") is True or progress.get("package_delivered") is True:
        return True
    if _is_completed_delivery_state(status=status, progress=progress):
        return True
    return _text(progress.get("paper_stage")) in {"bundle_stage_ready", "bundle_stage_blocked"}


def _is_completed_delivery_state(*, status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    completion = _mapping(status.get("study_completion_contract"))
    if (
        _text(status.get("quest_status")) == "completed"
        and _text(status.get("decision")) == "completed"
        and _text(status.get("reason")) == "quest_already_completed"
    ):
        return True
    if completion.get("ready") is True and _text(completion.get("completion_status")) == "completed":
        return True
    return _text(progress.get("current_stage")) == "study_completed"


def _condition(condition_type: str, status: str, reason: str) -> dict[str, Any]:
    return {
        "type": condition_type,
        "status": status,
        "reason": reason,
    }


def _fingerprint(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"study-macro-state::{digest}"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "REASONS",
    "SCHEMA_VERSION",
    "SNAPSHOT_RELATIVE_PATH",
    "USER_NEXT_STATES",
    "WRITER_STATES",
    "derive_study_macro_state",
    "materialize_study_macro_state_snapshot",
]
