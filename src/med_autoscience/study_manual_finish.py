from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path

import yaml

from med_autoscience.runtime_protocol import paper_artifacts


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


_AUTONOMOUS_CURRENT_PACKAGE_REQUIRED_FILES = (
    "manuscript.docx",
    "paper.pdf",
    "references.bib",
    "submission_checklist.json",
    "SUBMISSION_TODO.md",
)
_BUNDLE_ONLY_CURRENT_PACKAGE_REQUIRED_FILES = (
    "manuscript.docx",
    "paper.pdf",
    "references.bib",
    "submission_manifest.json",
    "SUBMISSION_TODO.md",
)
_AUTONOMOUS_MANUAL_FINISH_SUMMARY = (
    "浅层投稿包已经交付并可供审计，当前只差作者、单位、伦理、基金、利益冲突、数据可用性等人工前置信息；"
    "系统已停车，等待用户显式唤醒。"
)
_AUTONOMOUS_MANUAL_FINISH_NEXT_ACTION = (
    "继续保持 current_package 可审状态；待作者补齐前置信息或明确要求继续后，再显式 resume 或 relaunch。"
)
_BUNDLE_ONLY_MANUAL_FINISH_SUMMARY = (
    "当前论文线已到投稿包里程碑，submission-ready 包已生成并可供审计；"
    "系统已停车，等待用户显式接力或新的有界任务。"
)
_BUNDLE_ONLY_MANUAL_FINISH_NEXT_ACTION = (
    "当前包已经可直接交给用户审阅；如需继续补元数据、外投或新增 bounded 任务，再显式 resume 或 relaunch。"
)


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


def _autonomous_current_package_ready(*, study_root: Path) -> bool:
    manuscript_root = study_root / "manuscript"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    if not current_package_root.exists() or not current_package_zip.exists():
        return False
    return all((current_package_root / relative_path).exists() for relative_path in _AUTONOMOUS_CURRENT_PACKAGE_REQUIRED_FILES)


def _bundle_only_current_package_ready(*, study_root: Path) -> bool:
    manuscript_root = study_root / "manuscript"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    if not current_package_root.exists() or not current_package_zip.exists():
        return False
    return all((current_package_root / relative_path).exists() for relative_path in _BUNDLE_ONLY_CURRENT_PACKAGE_REQUIRED_FILES)


def _read_json_dict(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _bundle_only_submission_ready(*, study_root: Path) -> bool:
    if not _bundle_only_current_package_ready(study_root=study_root):
        return False
    summary_payload = _read_json_dict(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    )
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_review_loop = (
        dict(summary_payload.get("quality_review_loop") or {})
        if isinstance(summary_payload.get("quality_review_loop"), dict)
        else {}
    )
    closure_state = str(
        quality_closure_truth.get("state")
        or quality_review_loop.get("closure_state")
        or ""
    ).strip()
    if closure_state != "bundle_only_remaining":
        return False
    quality_assessment = (
        dict(summary_payload.get("quality_assessment") or {})
        if isinstance(summary_payload.get("quality_assessment"), dict)
        else {}
    )
    human_review = (
        dict(quality_assessment.get("human_review_readiness") or {})
        if isinstance(quality_assessment.get("human_review_readiness"), dict)
        else {}
    )
    human_review_status = str(human_review.get("status") or "").strip()
    return human_review_status in {"ready", ""}


def resolve_submission_metadata_only_manual_finish_contract(
    *,
    study_root: Path | None,
    quest_root: Path | None,
) -> StudyManualFinishContract | None:
    if study_root is None or quest_root is None:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    if not _autonomous_current_package_ready(study_root=resolved_study_root):
        return None
    paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(resolved_quest_root)
    if paper_bundle_manifest_path is None:
        return None
    submission_checklist = paper_artifacts.load_submission_checklist(paper_bundle_manifest_path)
    if not paper_artifacts.submission_checklist_requires_external_metadata(submission_checklist):
        return None
    return StudyManualFinishContract(
        study_root=resolved_study_root,
        status=StudyManualFinishStatus.ACTIVE,
        summary=_AUTONOMOUS_MANUAL_FINISH_SUMMARY,
        next_action_summary=_AUTONOMOUS_MANUAL_FINISH_NEXT_ACTION,
        compatibility_guard_only=True,
    )


def resolve_bundle_only_submission_ready_manual_finish_contract(
    *,
    study_root: Path | None,
) -> StudyManualFinishContract | None:
    if study_root is None:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    if not _bundle_only_submission_ready(study_root=resolved_study_root):
        return None
    return StudyManualFinishContract(
        study_root=resolved_study_root,
        status=StudyManualFinishStatus.ACTIVE,
        summary=_BUNDLE_ONLY_MANUAL_FINISH_SUMMARY,
        next_action_summary=_BUNDLE_ONLY_MANUAL_FINISH_NEXT_ACTION,
        compatibility_guard_only=True,
    )


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


def resolve_effective_study_manual_finish_contract(
    *,
    study_root: Path | None,
    quest_root: Path | None = None,
) -> StudyManualFinishContract | None:
    explicit_contract = resolve_study_manual_finish_contract(study_root=study_root)
    if explicit_contract is not None:
        return explicit_contract
    metadata_only_contract = resolve_submission_metadata_only_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )
    if metadata_only_contract is not None:
        return metadata_only_contract
    return resolve_bundle_only_submission_ready_manual_finish_contract(study_root=study_root)
