from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeEscalationRecord:
    recorded_at: str
    quest_root: str
    reason: str
    summary_ref: str
    record_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "recorded_at", self._require_text("recorded_at", self.recorded_at))
        object.__setattr__(self, "quest_root", self._require_text("quest_root", self.quest_root))
        object.__setattr__(self, "reason", self._require_text("reason", self.reason))
        object.__setattr__(self, "summary_ref", self._require_text("summary_ref", self.summary_ref))
        if self.record_path is not None:
            object.__setattr__(self, "record_path", self._require_text("record_path", self.record_path))

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "recorded_at": self.recorded_at,
            "quest_root": self.quest_root,
            "reason": self.reason,
            "summary_ref": self.summary_ref,
        }
        if self.record_path is not None:
            payload["record_path"] = self.record_path
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RuntimeEscalationRecord":
        if not isinstance(payload, dict):
            raise TypeError("runtime escalation record payload must be a mapping")
        return cls(
            recorded_at=cls._payload_text(payload, "recorded_at"),
            quest_root=cls._payload_text(payload, "quest_root"),
            reason=cls._payload_text(payload, "reason"),
            summary_ref=cls._payload_text(payload, "summary_ref"),
            record_path=(str(payload.get("record_path") or "").strip() or None),
        )

    @staticmethod
    def _payload_text(payload: dict[str, Any], field_name: str) -> str:
        value = str(payload.get(field_name) or "").strip()
        if not value:
            raise ValueError(f"runtime escalation record payload missing {field_name}")
        return value

    @staticmethod
    def _require_text(field_name: str, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"runtime escalation record {field_name} must be non-empty")
        return text
