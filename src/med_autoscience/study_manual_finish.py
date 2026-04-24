from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from importlib import import_module
import json
from pathlib import Path

import yaml

from med_autoscience.controllers import study_delivery_sync
from med_autoscience.runtime_protocol import paper_artifacts
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    task_intake_overrides_auto_manual_finish,
    task_intake_yields_to_deterministic_submission_closeout,
)


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
_ADMINISTRATIVE_TODO_TERMS = frozenset(
    {
        "affiliation",
        "affiliations",
        "author",
        "authors",
        "corresponding author",
        "ethics",
        "ethics approval",
        "ethics approval number",
        "irb",
        "funding",
        "grant",
        "grants",
        "conflict of interest",
        "competing interest",
        "competing interests",
        "data availability",
        "consent",
        "acknowledgement",
        "acknowledgements",
        "cover letter",
        "title page",
        "orcid",
        "copyright",
        "license",
        "clinical trial registration",
    }
)
_SCIENTIFIC_TODO_TERMS = frozenset(
    {
        "analysis",
        "model",
        "revise statistical",
        "sensitivity",
        "subgroup",
        "result",
        "results",
        "figure",
        "table",
        "method",
        "methods",
        "discussion",
        "limitation",
        "claim",
        "evidence",
        "cohort",
        "data cleaning",
        "rerun",
        "re-run",
        "experiment",
    }
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


def _delivery_authority_context(
    *,
    study_root: Path,
    quest_root: Path | None = None,
) -> tuple[Path | None, str]:
    manifest_payload = _read_json_dict(study_root / "manuscript" / "delivery_manifest.json")
    publication_profile = str(manifest_payload.get("publication_profile") or "").strip() or "general_medical_journal"
    surface_roles = (
        dict(manifest_payload.get("surface_roles") or {})
        if isinstance(manifest_payload.get("surface_roles"), dict)
        else {}
    )
    raw_paper_root = str(surface_roles.get("controller_authorized_paper_root") or "").strip()
    if raw_paper_root:
        candidate = Path(raw_paper_root).expanduser().resolve()
        if candidate.exists():
            return candidate, publication_profile
    if quest_root is not None:
        paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(quest_root)
        if paper_bundle_manifest_path is not None:
            return paper_bundle_manifest_path.parent.resolve(), publication_profile
    return None, publication_profile


def _submission_surfaces_current(
    *,
    study_root: Path,
    quest_root: Path | None = None,
) -> bool:
    paper_root, publication_profile = _delivery_authority_context(
        study_root=study_root,
        quest_root=quest_root,
    )
    if paper_root is None or not study_delivery_sync.can_sync_study_delivery(paper_root=paper_root):
        return False
    delivery_status = study_delivery_sync.describe_submission_delivery(
        paper_root=paper_root,
        publication_profile=publication_profile,
    )
    if str(delivery_status.get("status") or "").strip() != "current":
        return False
    authority_status = _submission_minimal_controller().describe_submission_minimal_authority(
        paper_root=paper_root,
        publication_profile=publication_profile,
    )
    return str(authority_status.get("status") or "").strip() == "current"


def _autonomous_current_package_ready(*, study_root: Path, quest_root: Path | None = None) -> bool:
    manuscript_root = study_root / "manuscript"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    if not current_package_root.exists() or not current_package_zip.exists():
        return False
    if not all((current_package_root / relative_path).exists() for relative_path in _AUTONOMOUS_CURRENT_PACKAGE_REQUIRED_FILES):
        return False
    return _submission_surfaces_current(study_root=study_root, quest_root=quest_root)


def _bundle_only_current_package_ready(*, study_root: Path, quest_root: Path | None = None) -> bool:
    manuscript_root = study_root / "manuscript"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    if not current_package_root.exists() or not current_package_zip.exists():
        return False
    if not all((current_package_root / relative_path).exists() for relative_path in _BUNDLE_ONLY_CURRENT_PACKAGE_REQUIRED_FILES):
        return False
    return _submission_surfaces_current(study_root=study_root, quest_root=quest_root)


def _read_json_dict(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _manifest_surface_qc_accepts_delivered_package(manifest_payload: dict[str, object]) -> bool:
    manuscript_payload = manifest_payload.get("manuscript")
    manuscript = manuscript_payload if isinstance(manuscript_payload, dict) else {}
    qc_payload = manuscript.get("surface_qc") or manifest_payload.get("surface_qc")
    if not isinstance(qc_payload, dict):
        return True
    failures = qc_payload.get("failures")
    if isinstance(failures, list) and failures:
        return False
    status = str(qc_payload.get("status") or "").strip().lower()
    return status == "pass"


def _package_manifest_has_nonzero_display_assets(manifest_payload: dict[str, object]) -> bool:
    figures = manifest_payload.get("figures")
    tables = manifest_payload.get("tables")
    return isinstance(figures, list) and len(figures) > 0 and isinstance(tables, list) and len(tables) > 0


def _package_root_has_required_delivery_files(package_root: Path) -> bool:
    if not (package_root / "manuscript.docx").exists() or not (package_root / "paper.pdf").exists():
        return False
    has_figure = any(path.is_file() for path in (package_root / "figures").glob("*"))
    has_table = any(path.is_file() for path in (package_root / "tables").glob("*"))
    return has_figure and has_table


def _submission_todo_is_administrative_only(todo_path: Path) -> bool:
    if not todo_path.exists():
        return False
    todo_text = todo_path.read_text(encoding="utf-8").strip()
    if not todo_text:
        return True
    actionable_lines = []
    for raw_line in todo_text.splitlines():
        line = raw_line.strip().lower()
        if not line or line.startswith("#"):
            continue
        if line in {
            "pending items:",
            "these items are administrative/front-matter handoff tasks. they are listed here so the current package can be reviewed for scientific audit while formal submission details are completed.",
        }:
            continue
        if line.startswith("- ") or line.startswith("* "):
            line = line[2:].strip()
        if line.startswith("[ ]"):
            line = line[3:].strip()
        actionable_lines.append(line)
    if not actionable_lines:
        return True
    for line in actionable_lines:
        if any(term in line for term in _SCIENTIFIC_TODO_TERMS):
            return False
        if not any(term in line for term in _ADMINISTRATIVE_TODO_TERMS):
            return False
    return True


def _delivered_package_ready(
    *,
    study_root: Path,
    package_root: Path,
    require_zip_path: Path | None = None,
    require_administrative_todo: bool = True,
) -> bool:
    if not package_root.exists() or not package_root.is_dir():
        return False
    if require_zip_path is not None and not require_zip_path.exists():
        return False
    manifest_payload = _read_json_dict(package_root / "submission_manifest.json")
    if not manifest_payload:
        manifest_payload = _read_json_dict(study_root / "manuscript" / "submission_manifest.json")
    if not manifest_payload:
        return False
    if not _package_root_has_required_delivery_files(package_root):
        return False
    if not _package_manifest_has_nonzero_display_assets(manifest_payload):
        return False
    if not _manifest_surface_qc_accepts_delivered_package(manifest_payload):
        return False
    todo_path = package_root / "SUBMISSION_TODO.md"
    if require_administrative_todo and not _submission_todo_is_administrative_only(todo_path):
        return False
    if todo_path.exists() and not _submission_todo_is_administrative_only(todo_path):
        return False
    return True


def _delivered_submission_package_ready(*, study_root: Path) -> bool:
    manuscript_root = study_root / "manuscript"
    if _delivered_package_ready(
        study_root=study_root,
        package_root=manuscript_root / "current_package",
        require_zip_path=manuscript_root / "current_package.zip",
        require_administrative_todo=True,
    ):
        return True
    if _delivered_package_ready(
        study_root=study_root,
        package_root=manuscript_root / "submission_package",
        require_administrative_todo=False,
    ):
        return True
    journal_mirror_root = manuscript_root / "journal_package_mirrors"
    if journal_mirror_root.exists():
        for package_root in sorted(path for path in journal_mirror_root.iterdir() if path.is_dir()):
            if _delivered_package_ready(
                study_root=study_root,
                package_root=package_root,
                require_administrative_todo=False,
            ):
                return True
    return False


def _submission_minimal_controller():
    return import_module("med_autoscience.controllers.submission_minimal")


def _bundle_only_submission_ready(*, study_root: Path, quest_root: Path | None = None) -> bool:
    if not _bundle_only_current_package_ready(study_root=study_root, quest_root=quest_root):
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
    if not _autonomous_current_package_ready(study_root=resolved_study_root, quest_root=resolved_quest_root):
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
    quest_root: Path | None = None,
) -> StudyManualFinishContract | None:
    if study_root is None:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_quest_root = Path(quest_root).expanduser().resolve() if quest_root is not None else None
    if not _bundle_only_submission_ready(study_root=resolved_study_root, quest_root=resolved_quest_root):
        return None
    return StudyManualFinishContract(
        study_root=resolved_study_root,
        status=StudyManualFinishStatus.ACTIVE,
        summary=_BUNDLE_ONLY_MANUAL_FINISH_SUMMARY,
        next_action_summary=_BUNDLE_ONLY_MANUAL_FINISH_NEXT_ACTION,
        compatibility_guard_only=True,
    )


def resolve_delivered_submission_package_manual_finish_contract(
    *,
    study_root: Path | None,
) -> StudyManualFinishContract | None:
    if study_root is None:
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    if not _delivered_submission_package_ready(study_root=resolved_study_root):
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
    resolved_study_root = Path(study_root).expanduser().resolve() if study_root is not None else None
    latest_task_intake = (
        read_latest_task_intake(study_root=resolved_study_root) if resolved_study_root is not None else None
    )
    if task_intake_overrides_auto_manual_finish(latest_task_intake):
        evaluation_summary_payload = (
            _read_json_dict(
                resolved_study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
            )
            if resolved_study_root is not None
            else {}
        )
        if not task_intake_yields_to_deterministic_submission_closeout(
            latest_task_intake,
            publishability_gate_report=None,
            evaluation_summary=evaluation_summary_payload,
        ):
            return None
    metadata_only_contract = resolve_submission_metadata_only_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )
    if metadata_only_contract is not None:
        return metadata_only_contract
    bundle_only_contract = resolve_bundle_only_submission_ready_manual_finish_contract(study_root=study_root, quest_root=quest_root)
    if bundle_only_contract is not None:
        return bundle_only_contract
    return resolve_delivered_submission_package_manual_finish_contract(study_root=study_root)
