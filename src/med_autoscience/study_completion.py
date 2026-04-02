from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_STUDY_COMPLETION_STATUSES = ("completed",)


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
