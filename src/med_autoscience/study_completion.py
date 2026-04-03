from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_STUDY_COMPLETION_STATUSES = ("completed",)


class StudyCompletionStateStatus(StrEnum):
    ABSENT = "absent"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class StudyCompletionContract:
    study_root: Path
    status: str
    summary: str
    user_approval_text: str
    completed_at: str | None
    evidence_paths: tuple[str, ...]
    missing_evidence_paths: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return bool(self.evidence_paths) and not self.missing_evidence_paths


@dataclass(frozen=True)
class StudyCompletionState:
    status: StudyCompletionStateStatus
    contract: StudyCompletionContract | None
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", self._normalize_status(self.status))

    @property
    def ready(self) -> bool:
        return self.contract.ready if self.contract is not None else False

    def to_dict(self) -> dict[str, Any]:
        contract = self.contract
        return {
            "ready": self.ready,
            "status": self.status.value,
            "completion_status": contract.status if contract is not None else None,
            "summary": contract.summary if contract is not None else "",
            "user_approval_text": contract.user_approval_text if contract is not None else "",
            "completed_at": contract.completed_at if contract is not None else None,
            "evidence_paths": list(contract.evidence_paths) if contract is not None else [],
            "missing_evidence_paths": list(contract.missing_evidence_paths) if contract is not None else [],
            "errors": list(self.errors),
        }

    @staticmethod
    def _normalize_status(value: StudyCompletionStateStatus | str) -> StudyCompletionStateStatus:
        if isinstance(value, StudyCompletionStateStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("status must be str")
        try:
            return StudyCompletionStateStatus(value)
        except ValueError as exc:
            raise ValueError(f"unknown study completion state status: {value}") from exc


def _load_yaml_dict(path: Path) -> dict[str, Any]:
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


def _string_list(raw_value: object, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(raw_value, list) or not raw_value:
        raise ValueError(f"{field_name} must be a non-empty list of strings")
    items: list[str] = []
    for item in raw_value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must be a non-empty list of strings")
        items.append(item.strip())
    return tuple(items)


def resolve_study_completion_contract(*, study_root: Path | None) -> StudyCompletionContract | None:
    if study_root is None:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload = _load_yaml_dict(resolved_study_root / "study.yaml")
    raw_completion = payload.get("study_completion")
    if raw_completion is None:
        return None
    if not isinstance(raw_completion, dict):
        raise ValueError("study_completion must be a mapping")

    status = _non_empty_string(raw_completion.get("status"), field_name="study_completion.status")
    if status not in SUPPORTED_STUDY_COMPLETION_STATUSES:
        supported = ", ".join(SUPPORTED_STUDY_COMPLETION_STATUSES)
        raise ValueError(f"study_completion.status must be one of: {supported}")
    evidence_paths = _string_list(raw_completion.get("evidence_paths"), field_name="study_completion.evidence_paths")
    missing_evidence_paths = tuple(
        relative
        for relative in evidence_paths
        if not (resolved_study_root / relative).resolve().exists()
    )
    return StudyCompletionContract(
        study_root=resolved_study_root,
        status=status,
        summary=_non_empty_string(raw_completion.get("summary"), field_name="study_completion.summary"),
        user_approval_text=_non_empty_string(
            raw_completion.get("user_approval_text"),
            field_name="study_completion.user_approval_text",
        ),
        completed_at=_optional_string(raw_completion.get("completed_at")),
        evidence_paths=evidence_paths,
        missing_evidence_paths=missing_evidence_paths,
    )


def resolve_study_completion_state(*, study_root: Path | None) -> StudyCompletionState:
    try:
        contract = resolve_study_completion_contract(study_root=study_root)
    except ValueError as exc:
        return StudyCompletionState(
            status=StudyCompletionStateStatus.INVALID,
            contract=None,
            errors=(str(exc),),
        )
    if contract is None:
        return StudyCompletionState(
            status=StudyCompletionStateStatus.ABSENT,
            contract=None,
            errors=(),
        )
    return StudyCompletionState(
        status=StudyCompletionStateStatus.RESOLVED if contract.ready else StudyCompletionStateStatus.INCOMPLETE,
        contract=contract,
        errors=(),
    )
