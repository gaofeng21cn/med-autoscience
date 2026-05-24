from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.autonomy_ai_doctor_parts.breach_explanation import (
    with_breach_explanation,
)


SCHEMA_VERSION = 1
DEFAULT_EXPECTED_MINUTES = 30
GATE_CLOSURE_EXPECTED_MINUTES = 10
QUALITY_REPAIR_EXPECTED_MINUTES = 60

SLO_STATUS_RELATIVE_PATH = Path("artifacts/autonomy/slo_status/latest.json")
AI_DOCTOR_REQUESTS_RELATIVE_ROOT = Path("artifacts/autonomy/ai_doctor_requests")
AI_DOCTOR_ATTEMPTS_RELATIVE_ROOT = Path("artifacts/autonomy/ai_doctor_attempts")
AI_DOCTOR_DIAGNOSES_RELATIVE_ROOT = Path("artifacts/autonomy/ai_doctor_diagnoses")
REPAIR_ACTIONS_RELATIVE_ROOT = Path("artifacts/autonomy/repair_actions")

_TIMESTAMP_KEYS = (
    "created_at",
    "recorded_at",
    "generated_at",
    "emitted_at",
    "updated_at",
    "finished_at",
    "latest_gate_replayed_at",
    "publication_eval_latest_at",
    "publishability_gate_latest_at",
    "meaningful_artifact_delta_at",
    "last_meaningful_progress_at",
)
_QUALITY_GATE_SURFACES = (
    "study_charter",
    "evidence_ledger",
    "review_ledger",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
)
_AI_DOCTOR_TRIGGER_BREACHES = frozenset(
    {
        "no_meaningful_progress",
        "same_fingerprint_loop",
        "stale_truth_surface",
        "late_success_timeout",
        "gate_closure_drift",
        "read_churn_without_artifact_delta",
        "opl_runtime_handoff_required",
    }
)
_NO_ARTIFACT_DELTA_PROGRESS_KINDS = frozenset(
    {
        "parked_no_artifact_delta",
        "read_churn_without_artifact_delta",
    }
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_time(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _payload_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def stable_slo_status_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / SLO_STATUS_RELATIVE_PATH


def ai_doctor_requests_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / AI_DOCTOR_REQUESTS_RELATIVE_ROOT


def ai_doctor_attempts_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / AI_DOCTOR_ATTEMPTS_RELATIVE_ROOT


def ai_doctor_diagnoses_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / AI_DOCTOR_DIAGNOSES_RELATIVE_ROOT


def repair_actions_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / REPAIR_ACTIONS_RELATIVE_ROOT


def read_latest_slo_status(*, study_root: Path) -> dict[str, Any] | None:
    payload = _read_json_object(stable_slo_status_path(study_root=study_root))
    return with_breach_explanation(payload) if payload is not None else None


def _latest_timestamp_from_payload(value: object) -> datetime | None:
    if isinstance(value, Mapping):
        candidates: list[datetime] = []
        for key, item in value.items():
            if key in _TIMESTAMP_KEYS and (parsed := _parse_time(item)) is not None:
                candidates.append(parsed)
            nested = _latest_timestamp_from_payload(item)
            if nested is not None:
                candidates.append(nested)
        return max(candidates) if candidates else None
    if isinstance(value, list):
        candidates = [
            parsed
            for item in value
            if (parsed := _latest_timestamp_from_payload(item)) is not None
        ]
        return max(candidates) if candidates else None
    return None


def _latest_telemetry_path(quest_root: Path | None) -> Path | None:
    if quest_root is None:
        return None
    runs_root = quest_root / ".ds" / "runs"
    if not runs_root.exists():
        return None
    candidates = sorted(
        runs_root.glob("*/telemetry.json"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0,
    )
    return candidates[-1] if candidates else None


def _latest_artifact_delta_path(quest_root: Path | None) -> Path | None:
    if quest_root is None:
        return None
    delta_root = quest_root / ".ds" / "artifact_deltas"
    if not delta_root.exists():
        return None
    candidates = sorted(
        delta_root.glob("*.json"),
        key=lambda item: item.stat().st_mtime if item.exists() else 0,
    )
    return candidates[-1] if candidates else None


def _mds_progress_markers(quest_root: Path | None) -> dict[str, Any]:
    telemetry_path = _latest_telemetry_path(quest_root)
    telemetry = _read_json_object(telemetry_path) if telemetry_path is not None else None
    artifact_delta_path = _latest_artifact_delta_path(quest_root)
    artifact_delta = _read_json_object(artifact_delta_path) if artifact_delta_path is not None else None
    meaningful_at = (
        _text((telemetry or {}).get("meaningful_artifact_delta_at"))
        or _text((artifact_delta or {}).get("created_at"))
    )
    return {
        "telemetry_path": str(telemetry_path) if telemetry_path is not None else None,
        "artifact_delta_path": str(artifact_delta_path) if artifact_delta_path is not None else None,
        "turn_completed_at": (
            _text((telemetry or {}).get("completed_at"))
            or _text((telemetry or {}).get("finished_at"))
            or _text((telemetry or {}).get("updated_at"))
            or _text((telemetry or {}).get("created_at"))
        ),
        "meaningful_artifact_delta_at": meaningful_at,
        "meaningful_artifact_delta_kind": (
            _text((telemetry or {}).get("meaningful_artifact_delta_kind"))
            or _text((artifact_delta or {}).get("artifact_kind"))
        ),
        "meaningful_artifact_delta_source_signature": (
            _text((telemetry or {}).get("meaningful_artifact_delta_source_signature"))
            or _text((artifact_delta or {}).get("source_signature"))
        ),
        "turn_progress_kind": _text((telemetry or {}).get("turn_progress_kind")),
        "stage_intent": _text((telemetry or {}).get("stage_intent")),
        "read_churn_ratio": _float((telemetry or {}).get("read_churn_ratio")),
        "same_result_reinjection_count": _int((telemetry or {}).get("same_result_reinjection_count")),
        "repeated_read_result_count": _int((telemetry or {}).get("repeated_read_result_count")),
        "read_tool_call_count": _int((telemetry or {}).get("read_tool_call_count")),
    }


def _expected_minutes(gate_summary: Mapping[str, Any], sli_summary: Mapping[str, Any]) -> int:
    next_work_unit_id = _text(sli_summary.get("next_work_unit_id"))
    blockers = [
        blocker
        for item in _list(gate_summary.get("current_blockers"))
        if (blocker := _text(item)) is not None
    ]
    unit_text = " ".join([next_work_unit_id or "", *blockers]).lower()
    if any(token in unit_text for token in ("replay", "closure", "stale", "package", "delivery", "submission")):
        return GATE_CLOSURE_EXPECTED_MINUTES
    if any(token in unit_text for token in ("claim", "evidence", "medical_publication_surface", "story")):
        return QUALITY_REPAIR_EXPECTED_MINUTES
    return DEFAULT_EXPECTED_MINUTES


def _last_meaningful_progress(
    *,
    generated_at: str,
    profile_payload: Mapping[str, Any],
    mds_markers: Mapping[str, Any],
) -> dict[str, Any]:
    marker_at = _parse_time(mds_markers.get("meaningful_artifact_delta_at"))
    latest_from_payload = _latest_timestamp_from_payload(
        {
            "publication_eval_replay_lag": profile_payload.get("publication_eval_replay_lag"),
            "work_unit_lifecycle_summary": profile_payload.get("work_unit_lifecycle_summary"),
            "paper_line_delivery_metrics": profile_payload.get("paper_line_delivery_metrics"),
            "gate_blocker_summary": profile_payload.get("gate_blocker_summary"),
        }
    )
    latest = max([candidate for candidate in (marker_at, latest_from_payload) if candidate is not None], default=None)
    now = _parse_time(generated_at)
    age_seconds = max(0, int((now - latest).total_seconds())) if now is not None and latest is not None else None
    if marker_at is not None and latest == marker_at:
        source = "mds_artifact_delta"
        source_ref = mds_markers.get("artifact_delta_path") or mds_markers.get("telemetry_path")
    elif latest_from_payload is not None:
        source = "mas_control_surface"
        source_ref = None
    else:
        source = "not_observed"
        source_ref = None
    return {
        "last_meaningful_progress_at": _iso(latest),
        "seconds_since_last_meaningful_progress": age_seconds,
        "source": source,
        "source_ref": source_ref,
    }


def _breach_types(
    *,
    generated_at: str,
    expected_minutes: int,
    last_progress: Mapping[str, Any],
    profile_payload: Mapping[str, Any],
    mds_markers: Mapping[str, Any],
) -> list[str]:
    autonomy_slo = _mapping(profile_payload.get("autonomy_slo"))
    progress_health = _mapping(autonomy_slo.get("progress_health"))
    sli_summary = _mapping(profile_payload.get("sli_summary"))
    runtime_failure = _mapping(
        profile_payload.get("runtime_failure_classification")
        or autonomy_slo.get("runtime_failure_classification")
    )
    replay_lag = _mapping(profile_payload.get("publication_eval_replay_lag"))
    turn_progress_kind = _text(mds_markers.get("turn_progress_kind"))
    turn_completed_at = _parse_time(mds_markers.get("turn_completed_at"))
    generated_time = _parse_time(generated_at)
    turn_seconds_since_completion = (
        max(0, int((generated_time - turn_completed_at).total_seconds()))
        if generated_time is not None and turn_completed_at is not None
        else None
    )
    no_artifact_delta_turn_overdue = bool(
        turn_progress_kind in _NO_ARTIFACT_DELTA_PROGRESS_KINDS
        and not _text(mds_markers.get("meaningful_artifact_delta_at"))
        and turn_seconds_since_completion is not None
        and turn_seconds_since_completion > expected_minutes * 60
    )
    breach: list[str] = []
    if (
        last_progress.get("seconds_since_last_meaningful_progress") is not None
        and int(last_progress["seconds_since_last_meaningful_progress"]) > expected_minutes * 60
        and progress_health.get("state") in {"no_progress_candidate", "incident_candidate", "blocked_with_actionable_work"}
    ) or (
        no_artifact_delta_turn_overdue
        and progress_health.get("state") in {"no_progress_candidate", "incident_candidate", "blocked_with_actionable_work"}
    ):
        breach.append("no_meaningful_progress")
    if bool(sli_summary.get("duplicate_dispatch_active")):
        breach.append("same_fingerprint_loop")
    if _text(replay_lag.get("status")) in {"publication_eval_missing_after_gate_replay", "stale_after_gate_replay"}:
        breach.append("stale_truth_surface")
        breach.append("gate_closure_drift")
    if no_artifact_delta_turn_overdue and expected_minutes == GATE_CLOSURE_EXPECTED_MINUTES:
        breach.append("gate_closure_drift")
    if _text(runtime_failure.get("diagnosis_code")) in {"resume_late_success_after_timeout", "daemon_late_success"}:
        breach.append("late_success_timeout")
    if _text(runtime_failure.get("action_mode")) == "opl_runtime_handoff_required":
        breach.append("opl_runtime_handoff_required")
    if (
        _float(mds_markers.get("read_churn_ratio")) >= 0.5
        and not _text(mds_markers.get("meaningful_artifact_delta_at"))
    ) or turn_progress_kind == "read_churn_without_artifact_delta":
        breach.append("read_churn_without_artifact_delta")
    return sorted(set(breach))


def _compact_evidence_packet(
    *,
    study_root: Path | None,
    quest_root: Path | None,
    profile_payload: Mapping[str, Any],
    mds_markers: Mapping[str, Any],
) -> dict[str, Any]:
    refs = {
        "study_root": str(study_root) if study_root is not None else None,
        "quest_root": str(quest_root) if quest_root is not None else None,
        "publication_eval": str(study_root / "artifacts" / "publication_eval" / "latest.json")
        if study_root is not None
        else None,
        "controller_decision": str(study_root / "artifacts" / "controller_decisions" / "latest.json")
        if study_root is not None
        else None,
        "slo_status": str(stable_slo_status_path(study_root=study_root)) if study_root is not None else None,
        "mds_telemetry": mds_markers.get("telemetry_path"),
        "mds_artifact_delta": mds_markers.get("artifact_delta_path"),
    }
    compact = {
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "refs": refs,
        "current_blockers": [
            blocker
            for item in _list(_mapping(profile_payload.get("gate_blocker_summary")).get("current_blockers"))
            if (blocker := _text(item)) is not None
        ],
        "sli_summary": dict(_mapping(profile_payload.get("sli_summary"))),
        "publication_eval_replay_lag": dict(_mapping(profile_payload.get("publication_eval_replay_lag"))),
        "mds_progress_markers": dict(mds_markers),
    }
    return {
        **compact,
        "packet_sha256": _payload_hash(compact),
        "content_policy": "compact_facts_only_no_medical_conclusion",
    }


def build_ai_doctor_request(slo_status: Mapping[str, Any]) -> dict[str, Any]:
    stable_identity = {
        "study_id": slo_status.get("study_id"),
        "quest_id": slo_status.get("quest_id"),
        "breach_types": slo_status.get("breach_types"),
        "evidence_hash": _mapping(slo_status.get("compact_evidence_packet")).get("packet_sha256"),
    }
    request_id = f"ai-doctor-request::{_payload_hash(stable_identity)[:20]}"
    return {
        "surface": "ai_doctor_request",
        "schema_version": SCHEMA_VERSION,
        "request_id": request_id,
        "state": "request_ready",
        "study_id": _text(slo_status.get("study_id")),
        "quest_id": _text(slo_status.get("quest_id")),
        "requested_ai_role": "control_plane_doctor",
        "default_model_policy": "inherit_current_codex_configuration",
        "diagnosis_scope": "progress_stall_or_control_plane_failure",
        "breach_types": list(_list(slo_status.get("breach_types"))),
        "compact_evidence_packet": dict(_mapping(slo_status.get("compact_evidence_packet"))),
        "allowed_repair_scopes": ["task_repair", "controller_repair", "opl_runtime_handoff_proposal"],
        "forbidden_actions": [
            "relax_publication_gate",
            "write_medical_conclusion",
            "patch_live_study_artifact_as_platform_fix",
            "change_default_model_or_reasoning",
        ],
        "quality_gate_relaxation_allowed": False,
        "created_at": _text(slo_status.get("generated_at")),
    }


def _primary_root_cause(breach_types: set[str], evidence_packet: Mapping[str, Any]) -> str:
    if "read_churn_without_artifact_delta" in breach_types:
        return "read_churn_without_artifact_delta"
    if "same_fingerprint_loop" in breach_types:
        return "same_fingerprint_loop"
    if "stale_truth_surface" in breach_types or "gate_closure_drift" in breach_types:
        return "stale_truth_surface"
    if "opl_runtime_handoff_required" in breach_types:
        return "opl_runtime_handoff_required"
    markers = _mapping(evidence_packet.get("mds_progress_markers"))
    marker_kind = _text(markers.get("turn_progress_kind"))
    if marker_kind is not None:
        return marker_kind
    return sorted(breach_types)[0] if breach_types else "unknown"


def _attempt_repair_plan(root_cause: str, evidence_packet: Mapping[str, Any]) -> dict[str, Any]:
    sli_summary = _mapping(evidence_packet.get("sli_summary"))
    next_work_unit_id = _text(sli_summary.get("next_work_unit_id")) or "analysis_claim_evidence_repair"
    if root_cause in {"read_churn_without_artifact_delta", "same_fingerprint_loop"}:
        return {
            "repair_scope": "controller_repair",
            "repair_kind": (
                "analysis_claim_evidence_redrive"
                if next_work_unit_id == "analysis_claim_evidence_repair"
                else "bounded_work_unit_redrive"
            ),
            "work_unit_id": next_work_unit_id,
            "max_attempts": 3,
            "backoff_policy": "exponential",
            "quality_gate_relaxation_allowed": False,
        }
    if root_cause == "stale_truth_surface":
        return {
            "repair_scope": "controller_repair",
            "repair_kind": "publication_gate_replay_or_authority_sync",
            "work_unit_id": next_work_unit_id,
            "max_attempts": 1,
            "backoff_policy": "none",
            "quality_gate_relaxation_allowed": False,
        }
    return {
        "repair_scope": "opl_runtime_handoff",
        "repair_kind": "provider_or_runtime_blocker_handoff",
        "work_unit_id": next_work_unit_id,
        "max_attempts": 1,
        "backoff_policy": "none",
        "quality_gate_relaxation_allowed": False,
    }


def _attempt_auto_apply(root_cause: str, repair_plan: Mapping[str, Any]) -> dict[str, Any]:
    eligible = root_cause in {
        "read_churn_without_artifact_delta",
        "same_fingerprint_loop",
        "stale_truth_surface",
    }
    return {
        "eligible": eligible,
        "mode": "controller_work_unit" if eligible else "proposal_only",
        "quality_gate_relaxation_allowed": False,
        "reason": (
            "bounded_controller_redrive_allowed"
            if eligible
            else _text(repair_plan.get("repair_kind")) or "requires_opl_runtime_handoff"
        ),
    }


def build_ai_doctor_attempt(
    *,
    request_payload: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    evidence_packet = _mapping(request_payload.get("compact_evidence_packet"))
    breach_types = {str(item) for item in _list(request_payload.get("breach_types")) if str(item).strip()}
    root_cause = _primary_root_cause(breach_types, evidence_packet)
    repair_plan = _attempt_repair_plan(root_cause, evidence_packet)
    diagnosis_seed = {
        "request_id": _text(request_payload.get("request_id")),
        "root_cause": root_cause,
        "repair_kind": repair_plan.get("repair_kind"),
        "evidence_hash": evidence_packet.get("packet_sha256"),
    }
    diagnosis_id = f"ai-doctor-diagnosis::{_payload_hash(diagnosis_seed)[:20]}"
    attempt_id = f"ai-doctor-attempt::{_payload_hash({**diagnosis_seed, 'recorded_at': recorded_at})[:20]}"
    return {
        "surface": "ai_doctor_attempt",
        "schema_version": SCHEMA_VERSION,
        "attempt_id": attempt_id,
        "diagnosis_id": diagnosis_id,
        "request_id": _text(request_payload.get("request_id")),
        "recorded_at": recorded_at,
        "study_id": _text(request_payload.get("study_id")),
        "quest_id": _text(request_payload.get("quest_id")),
        "input_evidence_packet": dict(evidence_packet),
        "root_cause": root_cause,
        "proposed_repair": repair_plan,
        "repair_owner": "mas_controller",
        "risk": "medium" if repair_plan.get("repair_scope") != "opl_runtime_handoff" else "high",
        "auto_apply": _attempt_auto_apply(root_cause, repair_plan),
        "result": {
            "status": "repair_plan_recorded",
            "medical_conclusion_written": False,
            "quality_gate_relaxation_allowed": False,
        },
        "quality_gate_relaxation_allowed": False,
        "medical_conclusion_written": False,
    }


def _attempt_as_diagnosis_payload(attempt_payload: Mapping[str, Any]) -> dict[str, Any]:
    proposed_repair = _mapping(attempt_payload.get("proposed_repair"))
    auto_apply = _mapping(attempt_payload.get("auto_apply"))
    return {
        "surface": "ai_doctor_diagnosis",
        "schema_version": SCHEMA_VERSION,
        "diagnosis_id": _text(attempt_payload.get("diagnosis_id")),
        "recorded_at": _text(attempt_payload.get("recorded_at")),
        "study_id": _text(attempt_payload.get("study_id")),
        "quest_id": _text(attempt_payload.get("quest_id")),
        "request_id": _text(attempt_payload.get("request_id")),
        "diagnosis_code": _text(attempt_payload.get("root_cause")),
        "repair_scope": _text(proposed_repair.get("repair_scope")) or "controller_repair",
        "recommended_repair_kind": _text(proposed_repair.get("repair_kind")) or "bounded_work_unit_redrive",
        "repair_owner": _text(attempt_payload.get("repair_owner")) or "mas_controller",
        "risk": _text(attempt_payload.get("risk")) or "medium",
        "auto_apply_allowed": bool(auto_apply.get("eligible")),
        "quality_gate_relaxation_allowed": False,
        "medical_conclusion_written": False,
    }


def materialize_ai_doctor_attempt(
    *,
    study_root: Path,
    request_payload: Mapping[str, Any],
    recorded_at: str | None = None,
) -> dict[str, Any]:
    recorded_at = recorded_at or _utc_now()
    attempt_payload = build_ai_doctor_attempt(
        request_payload=request_payload,
        recorded_at=recorded_at,
    )
    attempt_root = ai_doctor_attempts_root(study_root=study_root)
    attempt_path = attempt_root / f"{attempt_payload['attempt_id'].split('::')[-1]}.json"
    _write_json(attempt_path, attempt_payload)
    _write_json(attempt_root / "latest.json", attempt_payload)
    return attempt_payload


def materialize_ai_doctor_timeout_if_stale(
    *,
    study_root: Path,
    slo_status: Mapping[str, Any],
    request_payload: Mapping[str, Any],
    observed_at: str | None = None,
    timeout_seconds: int = 15 * 60,
) -> dict[str, Any] | None:
    observed_at = observed_at or _utc_now()
    created_at = _parse_time(request_payload.get("created_at"))
    observed_time = _parse_time(observed_at)
    if created_at is None or observed_time is None:
        return None
    age_seconds = int((observed_time - created_at).total_seconds())
    if age_seconds <= timeout_seconds:
        return None
    request_id = _text(request_payload.get("request_id"))
    payload = {
        "surface": "ai_doctor_timeout_escalation",
        "schema_version": SCHEMA_VERSION,
        "study_id": _text(slo_status.get("study_id")),
        "quest_id": _text(slo_status.get("quest_id")),
        "request_id": request_id,
        "state": "opl_runtime_handoff_required",
        "observed_at": observed_at,
        "created_at": _iso(created_at),
        "age_seconds": age_seconds,
        "timeout_after_seconds": timeout_seconds,
        "quality_gate_relaxation_allowed": False,
    }
    repair_payload = {
        "surface": "autonomy_repair_orchestration",
        "schema_version": SCHEMA_VERSION,
        "state": "ready_for_repair",
        "study_id": payload["study_id"],
        "quest_id": payload["quest_id"],
        "action_count": 1,
        "actions": [
            {
                "action_type": "opl_runtime_blocker_handoff",
                "repair_kind": "ai_doctor_request_timeout_handoff",
                "owner": "one-person-lab",
                "risk": "high",
                "auto_apply_allowed": False,
                "request_id": request_id,
            }
        ],
        "quality_gate_relaxation_allowed": False,
        "created_at": observed_at,
    }
    repair_root = repair_actions_root(study_root=study_root)
    repair_path = repair_root / f"{_payload_hash({'request_id': request_id, 'timeout': observed_at})[:20]}.json"
    _write_json(repair_path, repair_payload)
    _write_json(repair_root / "latest.json", repair_payload)
    return payload


def build_repair_orchestration(
    *,
    slo_status: Mapping[str, Any],
    ai_doctor_diagnosis: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    breach_types = {str(item) for item in _list(slo_status.get("breach_types"))}
    actions: list[dict[str, Any]] = []
    if ai_doctor_diagnosis is not None:
        actions.append(
            {
                "action_type": _text(ai_doctor_diagnosis.get("repair_scope")) or "controller_repair",
                "repair_kind": _text(ai_doctor_diagnosis.get("recommended_repair_kind"))
                or "ai_doctor_selected_repair",
                "owner": _text(ai_doctor_diagnosis.get("repair_owner")) or "mas_controller",
                "risk": _text(ai_doctor_diagnosis.get("risk")) or "medium",
                "auto_apply_allowed": bool(ai_doctor_diagnosis.get("auto_apply_allowed")),
                "diagnosis_id": _text(ai_doctor_diagnosis.get("diagnosis_id")),
            }
        )
    if "stale_truth_surface" in breach_types or "gate_closure_drift" in breach_types:
        actions.append(
            {
                "action_type": "controller_repair",
                "repair_kind": "publication_gate_replay_or_authority_sync",
                "owner": "mas_controller",
                "risk": "low",
                "auto_apply_allowed": True,
            }
        )
    if "same_fingerprint_loop" in breach_types or "no_meaningful_progress" in breach_types:
        actions.append(
            {
                "action_type": "controller_repair",
                "repair_kind": "suppress_repeated_long_turn_until_artifact_delta_or_specificity",
                "owner": "mas_controller",
                "risk": "medium",
                "auto_apply_allowed": True,
            }
        )
    if "read_churn_without_artifact_delta" in breach_types:
        actions.append(
            {
                "action_type": "task_repair",
                "repair_kind": "require_compact_evidence_and_meaningful_artifact_delta",
                "owner": "runtime_worker",
                "risk": "medium",
                "auto_apply_allowed": True,
            }
        )
    if "opl_runtime_handoff_required" in breach_types:
        actions.append(
            {
                "action_type": "opl_runtime_blocker_handoff",
                "repair_kind": "provider_or_runtime_blocker_handoff",
                "owner": "one-person-lab",
                "risk": "high",
                "auto_apply_allowed": False,
            }
        )
    if ai_doctor_diagnosis is None and bool(slo_status.get("ai_doctor_request_required")):
        actions.insert(
            0,
            {
                "action_type": "ai_doctor_diagnosis",
                "repair_kind": "diagnose_before_next_long_turn",
                "owner": "current_codex_ai",
                "risk": "low",
                "auto_apply_allowed": False,
            },
        )
    state = "awaiting_ai_doctor" if actions and actions[0]["action_type"] == "ai_doctor_diagnosis" else (
        "ready_for_repair" if actions else "monitor_only"
    )
    return {
        "surface": "autonomy_repair_orchestration",
        "schema_version": SCHEMA_VERSION,
        "state": state,
        "study_id": _text(slo_status.get("study_id")),
        "quest_id": _text(slo_status.get("quest_id")),
        "action_count": len(actions),
        "actions": actions,
        "quality_gate_relaxation_allowed": False,
        "user_feedback_priority": "user_feedback_supersedes_package_ready_and_old_gate",
        "runtime_blocker_handoff_policy": "opl_runtime_owner_handoff_required; high_risk_semantics_stop_as_typed_blocker",
        "created_at": _text(slo_status.get("generated_at")),
    }


def materialize_ai_doctor_diagnosis(
    *,
    study_root: Path,
    diagnosis_payload: Mapping[str, Any],
    recorded_at: str | None = None,
) -> dict[str, Any]:
    if bool(diagnosis_payload.get("quality_gate_relaxation_allowed")):
        raise ValueError("AI doctor diagnosis cannot relax publication or quality gates")
    recorded_at = recorded_at or _utc_now()
    compact = {
        "study_id": _text(diagnosis_payload.get("study_id")),
        "quest_id": _text(diagnosis_payload.get("quest_id")),
        "request_id": _text(diagnosis_payload.get("request_id")),
        "diagnosis_code": _text(diagnosis_payload.get("diagnosis_code")),
        "repair_scope": _text(diagnosis_payload.get("repair_scope")),
        "recommended_repair_kind": _text(diagnosis_payload.get("recommended_repair_kind")),
    }
    diagnosis_id = _text(diagnosis_payload.get("diagnosis_id")) or f"ai-doctor-diagnosis::{_payload_hash(compact)[:20]}"
    payload = {
        "surface": "ai_doctor_diagnosis",
        "schema_version": SCHEMA_VERSION,
        "diagnosis_id": diagnosis_id,
        "recorded_at": recorded_at,
        "default_model_policy": "inherit_current_codex_configuration",
        "quality_gate_relaxation_allowed": False,
        "medical_conclusion_written": False,
        **dict(diagnosis_payload),
    }
    payload["diagnosis_id"] = diagnosis_id
    payload["quality_gate_relaxation_allowed"] = False
    payload["medical_conclusion_written"] = False
    diagnosis_root = ai_doctor_diagnoses_root(study_root=study_root)
    diagnosis_path = diagnosis_root / f"{diagnosis_id.split('::')[-1]}.json"
    _write_json(diagnosis_path, payload)
    _write_json(diagnosis_root / "latest.json", payload)
    latest_slo = read_latest_slo_status(study_root=study_root) or {
        "study_id": payload.get("study_id"),
        "quest_id": payload.get("quest_id"),
        "breach_types": [],
        "generated_at": recorded_at,
    }
    repair_payload = build_repair_orchestration(
        slo_status=latest_slo,
        ai_doctor_diagnosis=payload,
    )
    repair_root = repair_actions_root(study_root=study_root)
    repair_path = repair_root / f"{_payload_hash({'diagnosis_id': diagnosis_id})[:20]}.json"
    _write_json(repair_path, repair_payload)
    _write_json(repair_root / "latest.json", repair_payload)
    return payload


def build_autonomy_control_plane_observer(
    profile_payload: Mapping[str, Any],
    *,
    study_root: Path | None = None,
    quest_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or _utc_now()
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    sli_summary = _mapping(profile_payload.get("sli_summary"))
    mds_markers = _mds_progress_markers(quest_root)
    expected_minutes = _expected_minutes(gate_summary, sli_summary)
    last_progress = _last_meaningful_progress(
        generated_at=generated_at,
        profile_payload=profile_payload,
        mds_markers=mds_markers,
    )
    breach_types = _breach_types(
        generated_at=generated_at,
        expected_minutes=expected_minutes,
        last_progress=last_progress,
        profile_payload=profile_payload,
        mds_markers=mds_markers,
    )
    external_blocker = bool(
        _mapping(
            profile_payload.get("runtime_failure_classification")
            or _mapping(profile_payload.get("autonomy_slo")).get("runtime_failure_classification")
        ).get("external_blocker")
    )
    ai_doctor_required = bool(
        not external_blocker
        and any(breach in _AI_DOCTOR_TRIGGER_BREACHES for breach in breach_types)
    )
    compact_evidence = _compact_evidence_packet(
        study_root=study_root,
        quest_root=quest_root,
        profile_payload=profile_payload,
        mds_markers=mds_markers,
    )
    state = "breach" if breach_types else "met"
    if external_blocker and breach_types:
        state = "blocked_external"
    elif not breach_types and last_progress.get("last_meaningful_progress_at") is None:
        state = "unknown"
    payload = {
        "surface": "autonomy_progress_slo_status",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "state": state,
        "expected_minutes": expected_minutes,
        "breach_types": breach_types,
        "breach_count": len(breach_types),
        "ai_doctor_request_required": ai_doctor_required,
        "ai_doctor_state": "request_ready" if ai_doctor_required else "not_required",
        "quality_gate_relaxation_allowed": False,
        "last_meaningful_progress": dict(last_progress),
        "last_meaningful_progress_at": last_progress.get("last_meaningful_progress_at"),
        "mds_progress_markers": mds_markers,
        "compact_evidence_packet": compact_evidence,
        "observer_inputs": {
            "sli_summary": dict(sli_summary),
            "publication_eval_replay_lag": dict(_mapping(profile_payload.get("publication_eval_replay_lag"))),
            "runtime_failure_classification": dict(
                _mapping(
                    profile_payload.get("runtime_failure_classification")
                    or _mapping(profile_payload.get("autonomy_slo")).get("runtime_failure_classification")
                )
            ),
        },
        "incident_learning_closure": {
            "closure_chain": ["incident", "diagnosis", "repair_action", "validation", "regression_hint"],
            "regression_hint": {
                "fixture_family": "autonomy_progress_slo",
                "breach_types": breach_types,
                "expected_test_surface": "autonomy_ai_doctor",
            },
            "quality_gate_relaxation_allowed": False,
        },
    }
    payload = with_breach_explanation(payload) or payload
    request = build_ai_doctor_request(payload) if ai_doctor_required else None
    repair = build_repair_orchestration(slo_status=payload)
    if request is not None:
        payload["ai_doctor_request"] = {
            "request_id": request["request_id"],
            "state": request["state"],
        }
    payload["repair_recommendation"] = {
        "state": repair["state"],
        "action_count": repair["action_count"],
        "top_action": repair["actions"][0] if repair["actions"] else None,
    }
    payload["quality_authority_surfaces"] = list(_QUALITY_GATE_SURFACES)
    return payload


def materialize_autonomy_control_plane_observer(
    *,
    study_root: Path,
    quest_root: Path | None,
    profile_payload: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    payload = build_autonomy_control_plane_observer(
        profile_payload,
        study_root=study_root,
        quest_root=quest_root,
        generated_at=generated_at,
    )
    _write_json(stable_slo_status_path(study_root=study_root), payload)
    request_payload = build_ai_doctor_request(payload) if bool(payload.get("ai_doctor_request_required")) else None
    if request_payload is not None:
        request_root = ai_doctor_requests_root(study_root=study_root)
        request_path = request_root / f"{request_payload['request_id'].split('::')[-1]}.json"
        _write_json(request_path, request_payload)
        _write_json(request_root / "latest.json", request_payload)
        payload["ai_doctor_request"]["path"] = str(request_path)
        attempt_payload = materialize_ai_doctor_attempt(
            study_root=study_root,
            request_payload=request_payload,
            recorded_at=generated_at,
        )
        attempt_path = ai_doctor_attempts_root(study_root=study_root) / f"{attempt_payload['attempt_id'].split('::')[-1]}.json"
        payload["ai_doctor_state"] = "attempt_recorded"
        payload["ai_doctor_attempt"] = {
            "attempt_id": attempt_payload["attempt_id"],
            "diagnosis_id": attempt_payload["diagnosis_id"],
            "state": attempt_payload["result"]["status"],
            "path": str(attempt_path),
        }
        _write_json(stable_slo_status_path(study_root=study_root), payload)
    attempt_diagnosis = (
        _attempt_as_diagnosis_payload(attempt_payload)
        if request_payload is not None and "attempt_payload" in locals()
        else None
    )
    repair_payload = build_repair_orchestration(
        slo_status=payload,
        ai_doctor_diagnosis=attempt_diagnosis,
    )
    repair_root = repair_actions_root(study_root=study_root)
    repair_identity = {
        "study_id": payload.get("study_id"),
        "quest_id": payload.get("quest_id"),
        "breach_types": payload.get("breach_types"),
        "state": repair_payload.get("state"),
    }
    repair_path = repair_root / f"{_payload_hash(repair_identity)[:20]}.json"
    _write_json(repair_path, repair_payload)
    _write_json(repair_root / "latest.json", repair_payload)
    return payload


__all__ = [
    "AI_DOCTOR_ATTEMPTS_RELATIVE_ROOT",
    "AI_DOCTOR_DIAGNOSES_RELATIVE_ROOT",
    "AI_DOCTOR_REQUESTS_RELATIVE_ROOT",
    "REPAIR_ACTIONS_RELATIVE_ROOT",
    "SLO_STATUS_RELATIVE_PATH",
    "ai_doctor_attempts_root",
    "ai_doctor_diagnoses_root",
    "ai_doctor_requests_root",
    "build_ai_doctor_attempt",
    "build_ai_doctor_request",
    "build_autonomy_control_plane_observer",
    "build_repair_orchestration",
    "materialize_ai_doctor_attempt",
    "materialize_ai_doctor_diagnosis",
    "materialize_ai_doctor_timeout_if_stale",
    "materialize_autonomy_control_plane_observer",
    "read_latest_slo_status",
    "repair_actions_root",
    "stable_slo_status_path",
]
