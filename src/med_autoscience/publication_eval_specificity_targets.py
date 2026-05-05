from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS = (
    "claim",
    "figure",
    "table",
    "metric",
    "source_path",
)

_ALLOWED_TARGET_KINDS = frozenset(REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS)
_ALLOWED_FIELDS = frozenset({"target_kind", "target_id", "source_path", "blocking_reason"})


def _require_text(label: str, field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _require_choice(label: str, field_name: str, value: Any, allowed_values: frozenset[str]) -> str:
    normalized = _require_text(label, field_name, value)
    if normalized not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(f"{label} {field_name} must be one of: {allowed}")
    return normalized


def _reject_unknown_fields(label: str, payload: dict[str, Any]) -> None:
    unknown_fields = sorted(set(payload) - _ALLOWED_FIELDS)
    if unknown_fields:
        raise ValueError(f"{label} payload contains unknown fields: {', '.join(unknown_fields)}")


@dataclass(frozen=True)
class PublicationEvalSpecificityTarget:
    target_kind: str
    target_id: str
    source_path: str
    blocking_reason: str

    def __post_init__(self) -> None:
        label = "publication eval specificity target"
        object.__setattr__(
            self,
            "target_kind",
            _require_choice(label, "target_kind", self.target_kind, _ALLOWED_TARGET_KINDS),
        )
        object.__setattr__(self, "target_id", _require_text(label, "target_id", self.target_id))
        object.__setattr__(self, "source_path", _require_text(label, "source_path", self.source_path))
        object.__setattr__(self, "blocking_reason", _require_text(label, "blocking_reason", self.blocking_reason))

    def to_dict(self) -> dict[str, str]:
        return {
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "source_path": self.source_path,
            "blocking_reason": self.blocking_reason,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalSpecificityTarget":
        if not isinstance(payload, dict):
            raise TypeError("publication eval specificity target payload must be a mapping")
        _reject_unknown_fields("publication eval specificity target", payload)
        return cls(
            target_kind=_require_text("publication eval specificity target", "target_kind", payload.get("target_kind")),
            target_id=_require_text("publication eval specificity target", "target_id", payload.get("target_id")),
            source_path=_require_text("publication eval specificity target", "source_path", payload.get("source_path")),
            blocking_reason=_require_text(
                "publication eval specificity target",
                "blocking_reason",
                payload.get("blocking_reason"),
            ),
        )


def normalize_publication_eval_specificity_targets(value: Any) -> tuple[PublicationEvalSpecificityTarget, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("publication eval recommended action specificity_targets must be a list")
    return tuple(
        item if isinstance(item, PublicationEvalSpecificityTarget) else PublicationEvalSpecificityTarget.from_payload(item)
        for item in value
    )


def to_payload_list(value: tuple[PublicationEvalSpecificityTarget, ...]) -> list[dict[str, str]]:
    return [target.to_dict() for target in value]


def specificity_target_status(value: Any) -> dict[str, Any]:
    try:
        targets = normalize_publication_eval_specificity_targets(value)
    except (TypeError, ValueError) as exc:
        return {
            "valid": False,
            "targets": [],
            "covered_target_kinds": [],
            "missing_target_kinds": list(REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS),
            "error": str(exc),
        }
    covered = {target.target_kind for target in targets}
    missing = [kind for kind in REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS if kind not in covered]
    return {
        "valid": True,
        "targets": [target.to_dict() for target in targets],
        "covered_target_kinds": [kind for kind in REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS if kind in covered],
        "missing_target_kinds": missing,
        "complete": not missing,
    }


__all__ = [
    "PublicationEvalSpecificityTarget",
    "REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS",
    "normalize_publication_eval_specificity_targets",
    "specificity_target_status",
]
