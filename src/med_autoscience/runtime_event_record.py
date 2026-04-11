from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _require_text(field_name: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"runtime event record {field_name} must be non-empty")
    return text


def _payload_text(payload: dict[str, Any], field_name: str) -> str:
    value = str(payload.get(field_name) or "").strip()
    if not value:
        raise ValueError(f"runtime event record payload missing {field_name}")
    return value


def _normalize_optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise TypeError("runtime event record optional boolean field must be bool or None")


_STATUS_SNAPSHOT_REQUIRED_KEYS = (
    "quest_status",
    "decision",
    "reason",
    "active_run_id",
    "runtime_liveness_status",
    "worker_running",
    "continuation_policy",
    "continuation_reason",
    "supervisor_tick_status",
    "controller_owned_finalize_parking",
    "runtime_escalation_ref",
)
_OUTER_LOOP_INPUT_REQUIRED_KEYS = (
    "quest_status",
    "decision",
    "reason",
    "active_run_id",
    "runtime_liveness_status",
    "worker_running",
    "supervisor_tick_status",
    "controller_owned_finalize_parking",
    "interaction_action",
    "interaction_requires_user_input",
    "runtime_escalation_ref",
)


def _normalize_runtime_snapshot(
    payload: Any,
    *,
    field_name: str,
    required_keys: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"runtime event record {field_name} must be a mapping")
    normalized = dict(payload)
    missing = [key for key in required_keys if key not in normalized]
    if missing:
        raise ValueError(f"runtime event record {field_name} missing {', '.join(missing)}")
    normalized["quest_status"] = _normalize_optional_text(normalized.get("quest_status"))
    normalized["decision"] = _normalize_optional_text(normalized.get("decision"))
    normalized["reason"] = _normalize_optional_text(normalized.get("reason"))
    normalized["active_run_id"] = _normalize_optional_text(normalized.get("active_run_id"))
    normalized["runtime_liveness_status"] = _normalize_optional_text(normalized.get("runtime_liveness_status"))
    normalized["worker_running"] = _normalize_optional_bool(normalized.get("worker_running"))
    normalized["controller_owned_finalize_parking"] = bool(normalized.get("controller_owned_finalize_parking"))
    if "continuation_policy" in normalized:
        normalized["continuation_policy"] = _normalize_optional_text(normalized.get("continuation_policy"))
    if "continuation_reason" in normalized:
        normalized["continuation_reason"] = _normalize_optional_text(normalized.get("continuation_reason"))
    normalized["supervisor_tick_status"] = _normalize_optional_text(normalized.get("supervisor_tick_status"))
    if "interaction_action" in normalized:
        normalized["interaction_action"] = _normalize_optional_text(normalized.get("interaction_action"))
    if "interaction_requires_user_input" in normalized:
        normalized["interaction_requires_user_input"] = bool(normalized.get("interaction_requires_user_input"))
    runtime_escalation_ref = normalized.get("runtime_escalation_ref")
    if runtime_escalation_ref is not None and not isinstance(runtime_escalation_ref, dict):
        raise TypeError(f"runtime event record {field_name} runtime_escalation_ref must be mapping or None")
    return normalized


@dataclass(frozen=True)
class RuntimeEventRecordRef:
    event_id: str
    artifact_path: str
    summary_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_text("event_id", self.event_id))
        object.__setattr__(self, "artifact_path", _require_text("artifact_path", self.artifact_path))
        object.__setattr__(self, "summary_ref", _require_text("summary_ref", self.summary_ref))

    def to_dict(self) -> dict[str, str]:
        return {
            "event_id": self.event_id,
            "artifact_path": self.artifact_path,
            "summary_ref": self.summary_ref,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuntimeEventRecordRef":
        if not isinstance(payload, dict):
            raise TypeError("runtime event record ref payload must be a mapping")
        return cls(
            event_id=_payload_text(payload, "event_id"),
            artifact_path=_payload_text(payload, "artifact_path"),
            summary_ref=_payload_text(payload, "summary_ref"),
        )


@dataclass(frozen=True)
class RuntimeEventRecord:
    schema_version: int
    event_id: str
    study_id: str
    quest_id: str
    emitted_at: str
    event_source: str
    event_kind: str
    summary_ref: str
    status_snapshot: dict[str, Any]
    outer_loop_input: dict[str, Any]
    artifact_path: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool):
            raise TypeError("runtime event record schema_version must be int")
        object.__setattr__(self, "event_id", _require_text("event_id", self.event_id))
        object.__setattr__(self, "study_id", _require_text("study_id", self.study_id))
        object.__setattr__(self, "quest_id", _require_text("quest_id", self.quest_id))
        object.__setattr__(self, "emitted_at", _require_text("emitted_at", self.emitted_at))
        object.__setattr__(self, "event_source", _require_text("event_source", self.event_source))
        object.__setattr__(self, "event_kind", _require_text("event_kind", self.event_kind))
        object.__setattr__(self, "summary_ref", _require_text("summary_ref", self.summary_ref))
        object.__setattr__(
            self,
            "status_snapshot",
            _normalize_runtime_snapshot(
                self.status_snapshot,
                field_name="status_snapshot",
                required_keys=_STATUS_SNAPSHOT_REQUIRED_KEYS,
            ),
        )
        object.__setattr__(
            self,
            "outer_loop_input",
            _normalize_runtime_snapshot(
                self.outer_loop_input,
                field_name="outer_loop_input",
                required_keys=_OUTER_LOOP_INPUT_REQUIRED_KEYS,
            ),
        )
        if self.artifact_path is not None:
            object.__setattr__(self, "artifact_path", _require_text("artifact_path", self.artifact_path))

    def with_artifact_path(self, artifact_path: str) -> "RuntimeEventRecord":
        return RuntimeEventRecord(
            schema_version=self.schema_version,
            event_id=self.event_id,
            study_id=self.study_id,
            quest_id=self.quest_id,
            emitted_at=self.emitted_at,
            event_source=self.event_source,
            event_kind=self.event_kind,
            summary_ref=self.summary_ref,
            status_snapshot=self.status_snapshot,
            outer_loop_input=self.outer_loop_input,
            artifact_path=artifact_path,
        )

    def ref(self) -> RuntimeEventRecordRef:
        if self.artifact_path is None:
            raise ValueError("runtime event record artifact_path must be set before building ref")
        return RuntimeEventRecordRef(
            event_id=self.event_id,
            artifact_path=self.artifact_path,
            summary_ref=self.summary_ref,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "emitted_at": self.emitted_at,
            "event_source": self.event_source,
            "event_kind": self.event_kind,
            "summary_ref": self.summary_ref,
            "status_snapshot": dict(self.status_snapshot),
            "outer_loop_input": dict(self.outer_loop_input),
        }
        if self.artifact_path is not None:
            payload["artifact_path"] = self.artifact_path
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuntimeEventRecord":
        if not isinstance(payload, dict):
            raise TypeError("runtime event record payload must be a mapping")
        if "schema_version" not in payload:
            raise ValueError("runtime event record payload missing schema_version")
        schema_version = payload.get("schema_version")
        if not isinstance(schema_version, int) or isinstance(schema_version, bool):
            raise TypeError("runtime event record schema_version must be int")
        return cls(
            schema_version=schema_version,
            event_id=_payload_text(payload, "event_id"),
            study_id=_payload_text(payload, "study_id"),
            quest_id=_payload_text(payload, "quest_id"),
            emitted_at=_payload_text(payload, "emitted_at"),
            event_source=_payload_text(payload, "event_source"),
            event_kind=_payload_text(payload, "event_kind"),
            summary_ref=_payload_text(payload, "summary_ref"),
            status_snapshot=payload.get("status_snapshot"),
            outer_loop_input=payload.get("outer_loop_input"),
            artifact_path=_normalize_optional_text(payload.get("artifact_path")),
        )
