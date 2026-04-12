from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml


class StudyManualFinishStatus(StrEnum):
    ACTIVE = "active"


@dataclass(frozen=True)
class StudyManualFinishContract:
    study_root: Path
    status: StudyManualFinishStatus
    summary: str
    next_action_summary: str | None
    compatibility_guard_only: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", self._normalize_status(self.status))

    @staticmethod
    def _normalize_status(value: StudyManualFinishStatus | str) -> StudyManualFinishStatus:
        if isinstance(value, StudyManualFinishStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("manual_finish.status must be str")
        try:
            return StudyManualFinishStatus(value)
        except ValueError as exc:
            raise ValueError(f"unknown manual_finish.status: {value}") from exc


def _load_yaml_dict(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _non_empty_string(raw_value: object, *, field_name: str) -> str:
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return raw_value.strip()


def _optional_string(raw_value: object) -> str | None:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None
    return raw_value.strip()


def resolve_study_manual_finish_contract(*, study_root: Path | None) -> StudyManualFinishContract | None:
    if study_root is None:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload = _load_yaml_dict(resolved_study_root / "study.yaml")
    raw_manual_finish = payload.get("manual_finish")
    if raw_manual_finish is None:
        return None
    if not isinstance(raw_manual_finish, dict):
        raise ValueError("manual_finish must be a mapping")
    return StudyManualFinishContract(
        study_root=resolved_study_root,
        status=_non_empty_string(raw_manual_finish.get("status"), field_name="manual_finish.status"),
        summary=_non_empty_string(raw_manual_finish.get("summary"), field_name="manual_finish.summary"),
        next_action_summary=_optional_string(raw_manual_finish.get("next_action_summary")),
        compatibility_guard_only=bool(raw_manual_finish.get("compatibility_guard_only", True)),
    )
