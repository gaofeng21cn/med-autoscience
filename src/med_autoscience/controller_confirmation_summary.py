from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.study_decision_record import StudyDecisionRecord

__all__ = [
    "STABLE_CONTROLLER_CONFIRMATION_SUMMARY_RELATIVE_PATH",
    "materialize_controller_confirmation_summary",
    "read_controller_confirmation_summary",
    "resolve_controller_confirmation_summary_ref",
    "stable_controller_confirmation_summary_path",
]


STABLE_CONTROLLER_CONFIRMATION_SUMMARY_RELATIVE_PATH = Path("artifacts/controller/controller_confirmation_summary.json")
_STABLE_CONTROLLER_DECISION_RELATIVE_PATH = Path("artifacts/controller_decisions/latest.json")
_ALLOWED_STATUSES = frozenset({"pending", "approved", "request_changes", "rejected", "resolved", "consumed"})
_ALLOWED_RESPONSES = ("approve", "request_changes", "reject")
_ACTION_LABELS = {
    "ensure_study_runtime": "继续托管推进当前研究运行",
    "ensure_study_runtime_relaunch_stopped": "重新拉起当前已停止的研究运行",
    "pause_runtime": "暂停当前研究运行",
    "stop_runtime": "停止当前研究运行",
}
_ACTION_QUESTIONS = {
    "ensure_study_runtime": "请确认是否允许 MAS 继续托管推进当前研究。",
    "ensure_study_runtime_relaunch_stopped": "请确认是否允许 MAS 重新拉起当前已停止的研究运行。",
    "pause_runtime": "请确认是否允许 MAS 暂停当前研究运行。",
    "stop_runtime": "请确认是否允许 MAS 停止当前研究运行。",
}


def stable_controller_confirmation_summary_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_CONTROLLER_CONFIRMATION_SUMMARY_RELATIVE_PATH).resolve()


def resolve_controller_confirmation_summary_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_controller_confirmation_summary_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("controller confirmation summary reader only accepts the stable controller artifact")
    return stable_path


def _required_text(label: str, field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _optional_text(label: str, field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{label} {field_name} must be str or None")
    text = value.strip()
    return text or None


def _required_mapping(label: str, field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    return dict(value)


def _required_string_list(label: str, field_name: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} {field_name} must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _required_text(label, field_name, item)
        if text in seen:
            continue
        normalized.append(text)
        seen.add(text)
    if not normalized:
        raise ValueError(f"{label} {field_name} must not be empty")
    return normalized


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{label} payload must be a JSON object: {path}")
    return payload


def _resolve_decision_path(
    *,
    study_root: Path,
    ref: str | Path | dict[str, Any] | None,
) -> Path:
    if isinstance(ref, dict):
        artifact_path = _required_text("controller confirmation decision_ref", "artifact_path", ref.get("artifact_path"))
        candidate = Path(artifact_path).expanduser()
    elif ref is None:
        candidate = _STABLE_CONTROLLER_DECISION_RELATIVE_PATH
    else:
        candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (Path(study_root).expanduser().resolve() / candidate).resolve()


def _load_decision_record(
    *,
    study_root: Path,
    ref: str | Path | dict[str, Any] | None = None,
) -> StudyDecisionRecord:
    decision_path = _resolve_decision_path(study_root=study_root, ref=ref)
    payload = _read_json_object(decision_path, label="study decision record")
    record = StudyDecisionRecord.from_payload(payload)
    if isinstance(ref, dict):
        provided_decision_id = _required_text("controller confirmation decision_ref", "decision_id", ref.get("decision_id"))
        if provided_decision_id != record.decision_id:
            raise ValueError("controller confirmation decision_ref decision_id mismatch")
    artifact_path = _optional_text("study decision record", "artifact_path", payload.get("artifact_path"))
    return record.with_artifact_path(artifact_path or str(decision_path))


def _question_for_user(record: StudyDecisionRecord) -> str:
    primary_action = record.controller_actions[0].action_type.value
    return _ACTION_QUESTIONS.get(primary_action, "请确认是否允许 MAS 执行当前控制面建议。")


def _next_action_if_approved(record: StudyDecisionRecord) -> str:
    labels: list[str] = []
    seen: set[str] = set()
    for action in record.controller_actions:
        label = _ACTION_LABELS.get(action.action_type.value, action.action_type.value)
        if label in seen:
            continue
        labels.append(label)
        seen.add(label)
    return "；".join(labels) if labels else "按当前控制面建议继续推进。"


def _build_summary_payload(record: StudyDecisionRecord) -> dict[str, Any]:
    decision_action_types = [action.action_type.value for action in record.controller_actions]
    return {
        "schema_version": 1,
        "summary_id": f"controller-confirmation::{record.study_id}::{record.decision_id}",
        "study_id": record.study_id,
        "quest_id": record.quest_id,
        "decision_ref": record.ref().to_dict(),
        "gate_id": f"controller-human-confirmation-{record.study_id}",
        "status": "pending",
        "requested_at": record.emitted_at,
        "decision_type": record.decision_type.value,
        "request_reason": record.reason,
        "question_for_user": _question_for_user(record),
        "allowed_responses": list(_ALLOWED_RESPONSES),
        "controller_action_types": decision_action_types,
        "next_action_if_approved": _next_action_if_approved(record),
    }


def _normalized_decision_ref(*, study_root: Path, value: object) -> dict[str, str]:
    payload = _required_mapping("controller confirmation summary", "decision_ref", value)
    record = _load_decision_record(study_root=study_root, ref=payload)
    if not record.requires_human_confirmation:
        raise ValueError("controller confirmation summary decision_ref must point to a pending human-confirmation decision")
    return record.ref().to_dict()


def _normalized_payload(*, study_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("controller confirmation summary payload must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("controller confirmation summary schema_version must be 1")
    status = _required_text("controller confirmation summary", "status", payload.get("status"))
    if status not in _ALLOWED_STATUSES:
        raise ValueError(f"controller confirmation summary status must be one of: {', '.join(sorted(_ALLOWED_STATUSES))}")
    normalized = {
        "schema_version": 1,
        "summary_id": _required_text("controller confirmation summary", "summary_id", payload.get("summary_id")),
        "study_id": _required_text("controller confirmation summary", "study_id", payload.get("study_id")),
        "quest_id": _required_text("controller confirmation summary", "quest_id", payload.get("quest_id")),
        "decision_ref": _normalized_decision_ref(study_root=study_root, value=payload.get("decision_ref")),
        "gate_id": _required_text("controller confirmation summary", "gate_id", payload.get("gate_id")),
        "status": status,
        "requested_at": _required_text("controller confirmation summary", "requested_at", payload.get("requested_at")),
        "decision_type": _required_text("controller confirmation summary", "decision_type", payload.get("decision_type")),
        "request_reason": _required_text("controller confirmation summary", "request_reason", payload.get("request_reason")),
        "question_for_user": _required_text("controller confirmation summary", "question_for_user", payload.get("question_for_user")),
        "allowed_responses": _required_string_list(
            "controller confirmation summary",
            "allowed_responses",
            payload.get("allowed_responses"),
        ),
        "controller_action_types": _required_string_list(
            "controller confirmation summary",
            "controller_action_types",
            payload.get("controller_action_types"),
        ),
        "next_action_if_approved": _required_text(
            "controller confirmation summary",
            "next_action_if_approved",
            payload.get("next_action_if_approved"),
        ),
        "resolved_at": _optional_text("controller confirmation summary", "resolved_at", payload.get("resolved_at")),
    }
    if normalized["status"] == "pending":
        record = _load_decision_record(study_root=study_root, ref=normalized["decision_ref"])
        if not record.requires_human_confirmation:
            raise ValueError("pending controller confirmation summary must point to a decision that still requires human confirmation")
    return normalized


def read_controller_confirmation_summary(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    summary_path = resolve_controller_confirmation_summary_ref(study_root=study_root, ref=ref)
    payload = _read_json_object(summary_path, label="controller confirmation summary")
    return _normalized_payload(study_root=study_root, payload=payload)


def materialize_controller_confirmation_summary(
    *,
    study_root: Path,
    decision_ref: str | Path | dict[str, Any] | None = None,
) -> dict[str, str] | None:
    record = _load_decision_record(study_root=study_root, ref=decision_ref)
    summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    if not record.requires_human_confirmation:
        if summary_path.exists():
            summary_path.unlink()
        return None
    normalized = _normalized_payload(
        study_root=study_root,
        payload=_build_summary_payload(record),
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "summary_id": str(normalized["summary_id"]),
        "artifact_path": str(summary_path),
    }
