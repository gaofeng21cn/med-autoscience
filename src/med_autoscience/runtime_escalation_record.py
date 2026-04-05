from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _require_text(field_name: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"runtime escalation record {field_name} must be non-empty")
    return text


def _payload_text(payload: dict[str, Any], field_name: str) -> str:
    value = str(payload.get(field_name) or "").strip()
    if not value:
        raise ValueError(f"runtime escalation record payload missing {field_name}")
    return value


def _payload_text_sequence(payload: dict[str, Any], field_name: str) -> tuple[str, ...]:
    if field_name not in payload:
        raise ValueError(f"runtime escalation record payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, list):
        raise ValueError(f"runtime escalation record {field_name} must be a list")
    normalized = tuple(str(item).strip() for item in raw_value if str(item).strip())
    if not normalized:
        raise ValueError(f"runtime escalation record {field_name} must not be empty")
    return normalized


def _payload_optional_text_sequence(payload: dict[str, Any], field_name: str) -> tuple[str, ...]:
    raw_value = payload.get(field_name) or []
    if not isinstance(raw_value, list):
        raise ValueError(f"runtime escalation record {field_name} must be a list")
    return tuple(str(item).strip() for item in raw_value if str(item).strip())


def _payload_text_mapping(payload: dict[str, Any], field_name: str) -> dict[str, str]:
    if field_name not in payload:
        raise ValueError(f"runtime escalation record payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, dict):
        raise ValueError(f"runtime escalation record {field_name} must be a mapping")
    normalized = {str(key).strip(): str(value).strip() for key, value in raw_value.items() if str(key).strip() and str(value).strip()}
    if not normalized:
        raise ValueError(f"runtime escalation record {field_name} must not be empty")
    return normalized


@dataclass(frozen=True)
class RuntimeEscalationTrigger:
    trigger_id: str
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "trigger_id", _require_text("trigger_id", self.trigger_id))
        object.__setattr__(self, "source", _require_text("source", self.source))

    def to_dict(self) -> dict[str, str]:
        return {
            "trigger_id": self.trigger_id,
            "source": self.source,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuntimeEscalationTrigger":
        if not isinstance(payload, dict):
            raise TypeError("runtime escalation trigger payload must be a mapping")
        return cls(
            trigger_id=_payload_text(payload, "trigger_id"),
            source=_payload_text(payload, "source"),
        )


@dataclass(frozen=True)
class RuntimeEscalationRecordRef:
    record_id: str
    artifact_path: str
    summary_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _require_text("record_id", self.record_id))
        object.__setattr__(self, "artifact_path", _require_text("artifact_path", self.artifact_path))
        object.__setattr__(self, "summary_ref", _require_text("summary_ref", self.summary_ref))

    def to_dict(self) -> dict[str, str]:
        return {
            "record_id": self.record_id,
            "artifact_path": self.artifact_path,
            "summary_ref": self.summary_ref,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuntimeEscalationRecordRef":
        if not isinstance(payload, dict):
            raise TypeError("runtime escalation record ref payload must be a mapping")
        return cls(
            record_id=_payload_text(payload, "record_id"),
            artifact_path=_payload_text(payload, "artifact_path"),
            summary_ref=_payload_text(payload, "summary_ref"),
        )


@dataclass(frozen=True)
class RuntimeEscalationRecord:
    schema_version: int
    record_id: str
    study_id: str
    quest_id: str
    emitted_at: str
    trigger: RuntimeEscalationTrigger
    scope: str
    severity: str
    reason: str
    recommended_actions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    runtime_context_refs: dict[str, str]
    summary_ref: str
    artifact_path: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool):
            raise TypeError("runtime escalation record schema_version must be int")
        object.__setattr__(self, "record_id", _require_text("record_id", self.record_id))
        object.__setattr__(self, "study_id", _require_text("study_id", self.study_id))
        object.__setattr__(self, "quest_id", _require_text("quest_id", self.quest_id))
        object.__setattr__(self, "emitted_at", _require_text("emitted_at", self.emitted_at))
        object.__setattr__(
            self,
            "trigger",
            self.trigger if isinstance(self.trigger, RuntimeEscalationTrigger) else RuntimeEscalationTrigger.from_payload(self.trigger),
        )
        object.__setattr__(self, "scope", _require_text("scope", self.scope))
        object.__setattr__(self, "severity", _require_text("severity", self.severity))
        object.__setattr__(self, "reason", _require_text("reason", self.reason))
        normalized_actions = tuple(_require_text("recommended_action", item) for item in self.recommended_actions)
        if not normalized_actions:
            raise ValueError("runtime escalation record recommended_actions must not be empty")
        object.__setattr__(self, "recommended_actions", normalized_actions)
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(_require_text("evidence_ref", item) for item in self.evidence_refs),
        )
        normalized_runtime_context_refs = {
            _require_text("runtime_context_ref_key", key): _require_text("runtime_context_ref_value", value)
            for key, value in dict(self.runtime_context_refs).items()
        }
        if not normalized_runtime_context_refs:
            raise ValueError("runtime escalation record runtime_context_refs must not be empty")
        object.__setattr__(self, "runtime_context_refs", normalized_runtime_context_refs)
        object.__setattr__(self, "summary_ref", _require_text("summary_ref", self.summary_ref))
        if self.artifact_path is not None:
            object.__setattr__(self, "artifact_path", _require_text("artifact_path", self.artifact_path))

    def with_artifact_path(self, artifact_path: str) -> "RuntimeEscalationRecord":
        return RuntimeEscalationRecord(
            schema_version=self.schema_version,
            record_id=self.record_id,
            study_id=self.study_id,
            quest_id=self.quest_id,
            emitted_at=self.emitted_at,
            trigger=self.trigger,
            scope=self.scope,
            severity=self.severity,
            reason=self.reason,
            recommended_actions=self.recommended_actions,
            evidence_refs=self.evidence_refs,
            runtime_context_refs=self.runtime_context_refs,
            summary_ref=self.summary_ref,
            artifact_path=artifact_path,
        )

    def ref(self) -> RuntimeEscalationRecordRef:
        if self.artifact_path is None:
            raise ValueError("runtime escalation record artifact_path must be set before building ref")
        return RuntimeEscalationRecordRef(
            record_id=self.record_id,
            artifact_path=self.artifact_path,
            summary_ref=self.summary_ref,
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "emitted_at": self.emitted_at,
            "trigger": self.trigger.to_dict(),
            "scope": self.scope,
            "severity": self.severity,
            "reason": self.reason,
            "recommended_actions": list(self.recommended_actions),
            "evidence_refs": list(self.evidence_refs),
            "runtime_context_refs": dict(self.runtime_context_refs),
            "summary_ref": self.summary_ref,
        }
        if self.artifact_path is not None:
            payload["artifact_path"] = self.artifact_path
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuntimeEscalationRecord":
        if not isinstance(payload, dict):
            raise TypeError("runtime escalation record payload must be a mapping")
        if "schema_version" not in payload:
            raise ValueError("runtime escalation record payload missing schema_version")
        schema_version = payload.get("schema_version")
        if not isinstance(schema_version, int) or isinstance(schema_version, bool):
            raise TypeError("runtime escalation record schema_version must be int")
        trigger_payload = payload.get("trigger")
        if not isinstance(trigger_payload, dict):
            raise ValueError("runtime escalation record payload missing trigger")
        artifact_path = str(payload.get("artifact_path") or "").strip() or None
        return cls(
            schema_version=schema_version,
            record_id=_payload_text(payload, "record_id"),
            study_id=_payload_text(payload, "study_id"),
            quest_id=_payload_text(payload, "quest_id"),
            emitted_at=_payload_text(payload, "emitted_at"),
            trigger=RuntimeEscalationTrigger.from_payload(trigger_payload),
            scope=_payload_text(payload, "scope"),
            severity=_payload_text(payload, "severity"),
            reason=_payload_text(payload, "reason"),
            recommended_actions=_payload_text_sequence(payload, "recommended_actions"),
            evidence_refs=_payload_optional_text_sequence(payload, "evidence_refs"),
            summary_ref=_payload_text(payload, "summary_ref"),
            runtime_context_refs=_payload_text_mapping(payload, "runtime_context_refs"),
            artifact_path=artifact_path,
        )
