from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .layout import build_workspace_runtime_layout_for_profile

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


@dataclass(frozen=True)
class StudyRuntimeContext:
    runtime_root: Path
    quest_root: Path
    runtime_binding_path: Path
    startup_payload_root: Path
    launch_report_path: Path


@dataclass(frozen=True)
class StudyRuntimeArtifacts:
    runtime_binding_path: Path
    launch_report_path: Path
    startup_payload_path: Path | None


class StartupContractValidationStatus(StrEnum):
    CLEAR = "clear"
    BLOCKED = "blocked"


class StartupHydrationStatus(StrEnum):
    HYDRATED = "hydrated"


class StartupHydrationValidationStatus(StrEnum):
    CLEAR = "clear"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class StartupContractValidation:
    status: StartupContractValidationStatus
    blockers: tuple[str, ...]
    medical_analysis_contract_status: str | None
    medical_reporting_contract_status: str | None
    medical_analysis_reason_code: str | None
    medical_reporting_reason_code: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", self._normalize_status(self.status))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "blockers": list(self.blockers),
            "contract_statuses": {
                "medical_analysis_contract": self.medical_analysis_contract_status,
                "medical_reporting_contract": self.medical_reporting_contract_status,
            },
            "reason_codes": {
                "medical_analysis_contract": self.medical_analysis_reason_code,
                "medical_reporting_contract": self.medical_reporting_reason_code,
            },
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StartupContractValidation":
        if not isinstance(payload, dict):
            raise TypeError("startup contract validation payload must be a mapping")
        if "contract_statuses" not in payload:
            raise ValueError("startup contract validation payload missing contract_statuses")
        if "reason_codes" not in payload:
            raise ValueError("startup contract validation payload missing reason_codes")
        blockers = payload.get("blockers") or []
        if not isinstance(blockers, list):
            raise ValueError("startup contract validation payload blockers must be a list")
        contract_statuses = payload.get("contract_statuses")
        if not isinstance(contract_statuses, dict):
            raise ValueError("startup contract validation payload contract_statuses must be a mapping")
        reason_codes = payload.get("reason_codes")
        if not isinstance(reason_codes, dict):
            raise ValueError("startup contract validation payload reason_codes must be a mapping")
        return cls(
            status=payload.get("status"),
            blockers=tuple(str(item) for item in blockers),
            medical_analysis_contract_status=str(contract_statuses.get("medical_analysis_contract") or "") or None,
            medical_reporting_contract_status=str(contract_statuses.get("medical_reporting_contract") or "") or None,
            medical_analysis_reason_code=str(reason_codes.get("medical_analysis_contract") or "") or None,
            medical_reporting_reason_code=str(reason_codes.get("medical_reporting_contract") or "") or None,
        )

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StartupContractValidation":
        if not isinstance(payload, dict):
            raise TypeError("startup contract validation payload must be a mapping")
        if "status" not in payload:
            raise ValueError("startup contract validation payload missing status")
        blockers = payload.get("blockers") or []
        if not isinstance(blockers, list):
            raise ValueError("startup contract validation payload blockers must be a list")
        if "contract_statuses" not in payload:
            raise ValueError("startup contract validation payload missing contract_statuses")
        contract_statuses = payload.get("contract_statuses") or {}
        if not isinstance(contract_statuses, dict):
            raise ValueError("startup contract validation payload contract_statuses must be a mapping")
        if "reason_codes" not in payload:
            raise ValueError("startup contract validation payload missing reason_codes")
        reason_codes = payload.get("reason_codes") or {}
        if not isinstance(reason_codes, dict):
            raise ValueError("startup contract validation payload reason_codes must be a mapping")
        return cls(
            status=payload.get("status"),
            blockers=tuple(str(item) for item in blockers),
            medical_analysis_contract_status=(
                str(contract_statuses.get("medical_analysis_contract") or "") or None
            ),
            medical_reporting_contract_status=(
                str(contract_statuses.get("medical_reporting_contract") or "") or None
            ),
            medical_analysis_reason_code=(str(reason_codes.get("medical_analysis_contract") or "") or None),
            medical_reporting_reason_code=(str(reason_codes.get("medical_reporting_contract") or "") or None),
        )

    @staticmethod
    def _normalize_status(value: StartupContractValidationStatus | str) -> StartupContractValidationStatus:
        if isinstance(value, StartupContractValidationStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("status must be str")
        try:
            return StartupContractValidationStatus(value)
        except ValueError as exc:
            raise ValueError(f"unknown startup contract validation status: {value}") from exc


@dataclass(frozen=True)
class StartupHydrationReport:
    status: StartupHydrationStatus
    recorded_at: str
    quest_root: str
    entry_state_summary: str
    literature_report: dict[str, Any]
    written_files: tuple[str, ...]
    report_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", self._normalize_status(self.status))
        object.__setattr__(self, "written_files", tuple(str(item) for item in self.written_files))
        if self.report_path is not None:
            object.__setattr__(self, "report_path", str(self.report_path))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "recorded_at": self.recorded_at,
            "quest_root": self.quest_root,
            "entry_state_summary": self.entry_state_summary,
            "literature_report": dict(self.literature_report),
            "written_files": list(self.written_files),
        }
        if self.report_path is not None:
            payload["report_path"] = self.report_path
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StartupHydrationReport":
        if not isinstance(payload, dict):
            raise TypeError("startup hydration payload must be a mapping")
        if "recorded_at" not in payload or not str(payload.get("recorded_at") or "").strip():
            raise ValueError("startup hydration payload missing recorded_at")
        if "quest_root" not in payload or not str(payload.get("quest_root") or "").strip():
            raise ValueError("startup hydration payload missing quest_root")
        if "entry_state_summary" not in payload or not str(payload.get("entry_state_summary") or "").strip():
            raise ValueError("startup hydration payload missing entry_state_summary")
        written_files = payload.get("written_files") or []
        if not isinstance(written_files, list):
            raise ValueError("startup hydration payload written_files must be a list")
        if "literature_report" not in payload:
            raise ValueError("startup hydration payload missing literature_report")
        literature_report = payload.get("literature_report") or {}
        if not isinstance(literature_report, dict):
            raise ValueError("startup hydration payload literature_report must be a mapping")
        return cls(
            status=payload.get("status"),
            recorded_at=str(payload.get("recorded_at") or ""),
            quest_root=str(payload.get("quest_root") or ""),
            entry_state_summary=str(payload.get("entry_state_summary") or ""),
            literature_report=dict(literature_report),
            written_files=tuple(str(item) for item in written_files),
            report_path=str(payload.get("report_path") or "") or None,
        )

    @staticmethod
    def _normalize_status(value: StartupHydrationStatus | str) -> StartupHydrationStatus:
        if isinstance(value, StartupHydrationStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("status must be str")
        try:
            return StartupHydrationStatus(value)
        except ValueError as exc:
            raise ValueError(f"unknown startup hydration status: {value}") from exc


@dataclass(frozen=True)
class StartupHydrationValidationReport:
    status: StartupHydrationValidationStatus
    recorded_at: str
    quest_root: str
    blockers: tuple[str, ...]
    medical_analysis_contract_status: str | None
    medical_reporting_contract_status: str | None
    medical_analysis_contract_path: str
    medical_reporting_contract_path: str
    report_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", self._normalize_status(self.status))
        object.__setattr__(self, "blockers", tuple(str(item) for item in self.blockers))
        if self.medical_analysis_contract_status == "":
            object.__setattr__(self, "medical_analysis_contract_status", None)
        if self.medical_reporting_contract_status == "":
            object.__setattr__(self, "medical_reporting_contract_status", None)
        if self.report_path is not None:
            object.__setattr__(self, "report_path", str(self.report_path))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "recorded_at": self.recorded_at,
            "quest_root": self.quest_root,
            "blockers": list(self.blockers),
            "contract_statuses": {
                "medical_analysis_contract": self.medical_analysis_contract_status,
                "medical_reporting_contract": self.medical_reporting_contract_status,
            },
            "checked_paths": {
                "medical_analysis_contract_path": self.medical_analysis_contract_path,
                "medical_reporting_contract_path": self.medical_reporting_contract_path,
            },
        }
        if self.report_path is not None:
            payload["report_path"] = self.report_path
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StartupHydrationValidationReport":
        if not isinstance(payload, dict):
            raise TypeError("startup hydration validation payload must be a mapping")
        if "recorded_at" not in payload or not str(payload.get("recorded_at") or "").strip():
            raise ValueError("startup hydration validation payload missing recorded_at")
        if "quest_root" not in payload or not str(payload.get("quest_root") or "").strip():
            raise ValueError("startup hydration validation payload missing quest_root")
        blockers = payload.get("blockers") or []
        if not isinstance(blockers, list):
            raise ValueError("startup hydration validation blockers must be a list")
        if "contract_statuses" not in payload:
            raise ValueError("startup hydration validation payload missing contract_statuses")
        contract_statuses = payload.get("contract_statuses") or {}
        if not isinstance(contract_statuses, dict):
            raise ValueError("startup hydration validation contract_statuses must be a mapping")
        if "checked_paths" not in payload:
            raise ValueError("startup hydration validation payload missing checked_paths")
        checked_paths = payload.get("checked_paths") or {}
        if not isinstance(checked_paths, dict):
            raise ValueError("startup hydration validation checked_paths must be a mapping")
        return cls(
            status=payload.get("status"),
            recorded_at=str(payload.get("recorded_at") or ""),
            quest_root=str(payload.get("quest_root") or ""),
            blockers=tuple(str(item) for item in blockers),
            medical_analysis_contract_status=(
                str(contract_statuses.get("medical_analysis_contract") or "") or None
            ),
            medical_reporting_contract_status=(
                str(contract_statuses.get("medical_reporting_contract") or "") or None
            ),
            medical_analysis_contract_path=str(checked_paths.get("medical_analysis_contract_path") or ""),
            medical_reporting_contract_path=str(checked_paths.get("medical_reporting_contract_path") or ""),
            report_path=str(payload.get("report_path") or "") or None,
        )

    @staticmethod
    def _normalize_status(
        value: StartupHydrationValidationStatus | str,
    ) -> StartupHydrationValidationStatus:
        if isinstance(value, StartupHydrationValidationStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("status must be str")
        try:
            return StartupHydrationValidationStatus(value)
        except ValueError as exc:
            raise ValueError(f"unknown startup hydration validation status: {value}") from exc


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def _startup_hydration_report_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / "artifacts" / "reports" / "startup" / "hydration_report.json"


def _startup_hydration_validation_report_path(quest_root: Path) -> Path:
    return (
        Path(quest_root).expanduser().resolve()
        / "artifacts"
        / "reports"
        / "startup"
        / "hydration_validation_report.json"
    )


def write_startup_hydration_report(
    *,
    quest_root: Path,
    report: StartupHydrationReport,
) -> StartupHydrationReport:
    path = _startup_hydration_report_path(quest_root)
    payload = report.to_dict()
    payload["report_path"] = str(path)
    _write_json(path, payload)
    return StartupHydrationReport.from_payload(payload)


def write_startup_hydration_validation_report(
    *,
    quest_root: Path,
    report: StartupHydrationValidationReport,
) -> StartupHydrationValidationReport:
    path = _startup_hydration_validation_report_path(quest_root)
    payload = report.to_dict()
    payload["report_path"] = str(path)
    _write_json(path, payload)
    return StartupHydrationValidationReport.from_payload(payload)


def resolve_study_runtime_context(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    quest_id: str,
) -> StudyRuntimeContext:
    layout = build_workspace_runtime_layout_for_profile(profile)
    resolved_study_root = Path(study_root).expanduser().resolve()
    return StudyRuntimeContext(
        runtime_root=layout.runtime_root,
        quest_root=layout.quest_root(quest_id),
        runtime_binding_path=resolved_study_root / "runtime_binding.yaml",
        startup_payload_root=layout.startup_payload_root(study_id),
        launch_report_path=resolved_study_root / "artifacts" / "runtime" / "last_launch_report.json",
    )


def resolve_study_runtime_paths(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, Path]:
    context = resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    return {
        "runtime_root": context.runtime_root,
        "quest_root": context.quest_root,
        "runtime_binding_path": context.runtime_binding_path,
        "startup_payload_root": context.startup_payload_root,
        "launch_report_path": context.launch_report_path,
    }


def build_hydration_payload(*, create_payload: dict[str, Any]) -> dict[str, object]:
    startup_contract = create_payload.get("startup_contract")
    if not isinstance(startup_contract, dict):
        raise ValueError("create payload missing startup_contract")
    medical_analysis_contract = startup_contract.get("medical_analysis_contract_summary")
    if not isinstance(medical_analysis_contract, dict):
        raise ValueError("startup_contract missing medical_analysis_contract_summary")
    medical_reporting_contract = startup_contract.get("medical_reporting_contract_summary")
    if not isinstance(medical_reporting_contract, dict):
        raise ValueError("startup_contract missing medical_reporting_contract_summary")
    entry_state_summary = startup_contract.get("entry_state_summary")
    if not isinstance(entry_state_summary, str) or not entry_state_summary.strip():
        raise ValueError("startup_contract missing entry_state_summary")
    return {
        "medical_analysis_contract": dict(medical_analysis_contract),
        "medical_reporting_contract": dict(medical_reporting_contract),
        "entry_state_summary": entry_state_summary.strip(),
    }


def validate_startup_contract_resolution(*, startup_contract: dict[str, Any]) -> StartupContractValidation:
    def validate_contract(
        *,
        payload: object,
        missing_blocker: str,
        invalid_blocker: str,
        unsupported_blocker: str,
        unresolved_blocker: str,
    ) -> tuple[str | None, str | None, str | None]:
        if payload is None:
            return None, missing_blocker, None
        if not isinstance(payload, dict):
            return None, invalid_blocker, None
        status = str(payload.get("status") or "").strip()
        reason_code = str(payload.get("reason_code") or "").strip() or None
        if status == "resolved":
            return status, None, reason_code
        if status == "unsupported":
            return status, unsupported_blocker, reason_code
        return status or None, unresolved_blocker, reason_code

    blockers: list[str] = []
    analysis_status, analysis_blocker, analysis_reason = validate_contract(
        payload=startup_contract.get("medical_analysis_contract_summary"),
        missing_blocker="missing_medical_analysis_contract",
        invalid_blocker="invalid_medical_analysis_contract",
        unsupported_blocker="unsupported_medical_analysis_contract",
        unresolved_blocker="unresolved_medical_analysis_contract",
    )
    reporting_status, reporting_blocker, reporting_reason = validate_contract(
        payload=startup_contract.get("medical_reporting_contract_summary"),
        missing_blocker="missing_medical_reporting_contract",
        invalid_blocker="invalid_medical_reporting_contract",
        unsupported_blocker="unsupported_medical_reporting_contract",
        unresolved_blocker="unresolved_medical_reporting_contract",
    )
    if analysis_blocker is not None:
        blockers.append(analysis_blocker)
    if reporting_blocker is not None:
        blockers.append(reporting_blocker)
    return StartupContractValidation(
        status=StartupContractValidationStatus.BLOCKED if blockers else StartupContractValidationStatus.CLEAR,
        blockers=tuple(blockers),
        medical_analysis_contract_status=analysis_status,
        medical_reporting_contract_status=reporting_status,
        medical_analysis_reason_code=analysis_reason,
        medical_reporting_reason_code=reporting_reason,
    )


def should_refresh_startup_hydration_while_blocked(status: dict[str, Any]) -> bool:
    if status.get("decision") != "blocked" or not bool(status.get("quest_exists")):
        return False
    quest_status = str(status.get("quest_status") or "").strip()
    if quest_status not in {"created", "idle", "paused"}:
        return False
    return str(status.get("reason") or "").strip() in {
        "startup_boundary_not_ready_for_resume",
        "runtime_reentry_not_ready_for_resume",
        "quest_paused_but_auto_resume_disabled",
        "quest_initialized_but_auto_resume_disabled",
    }


def write_startup_payload(
    *,
    startup_payload_root: Path,
    create_payload: dict[str, Any],
    slug: str,
) -> Path:
    payload_path = Path(startup_payload_root).expanduser().resolve() / f"{slug}.json"
    _write_json(payload_path, create_payload)
    return payload_path


def write_runtime_binding(
    *,
    runtime_binding_path: Path,
    runtime_root: Path,
    study_id: str,
    study_root: Path,
    quest_id: str,
    last_action: str,
    source: str,
    recorded_at: str,
) -> None:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    resolved_study_root = Path(study_root).expanduser().resolve()
    _write_yaml(
        runtime_binding_path,
        {
            "schema_version": 1,
            "engine": "med-deepscientist",
            "study_id": study_id,
            "study_root": str(resolved_study_root),
            "quest_id": quest_id,
            "runtime_root": str(resolved_runtime_root / "quests"),
            "med_deepscientist_runtime_root": str(resolved_runtime_root),
            "last_action": last_action,
            "last_action_at": recorded_at,
            "last_source": source,
        },
    )


def persist_runtime_artifacts(
    *,
    runtime_binding_path: Path,
    launch_report_path: Path,
    runtime_root: Path,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    last_action: str | None,
    status: dict[str, Any],
    source: str,
    force: bool,
    startup_payload_path: Path | None,
    daemon_result: dict[str, Any] | None,
    recorded_at: str,
) -> StudyRuntimeArtifacts:
    if last_action is not None:
        resolved_quest_id = str(quest_id or "").strip()
        if not resolved_quest_id:
            raise ValueError("quest_id is required when last_action is provided")
        write_runtime_binding(
            runtime_binding_path=runtime_binding_path,
            runtime_root=runtime_root,
            study_id=study_id,
            study_root=study_root,
            quest_id=resolved_quest_id,
            last_action=last_action,
            source=source,
            recorded_at=recorded_at,
        )
    write_launch_report(
        launch_report_path=launch_report_path,
        status=status,
        source=source,
        force=force,
        startup_payload_path=startup_payload_path,
        daemon_result=daemon_result,
        recorded_at=recorded_at,
    )
    return StudyRuntimeArtifacts(
        runtime_binding_path=runtime_binding_path,
        launch_report_path=launch_report_path,
        startup_payload_path=startup_payload_path,
    )


def write_launch_report(
    *,
    launch_report_path: Path,
    status: dict[str, Any],
    source: str,
    force: bool,
    startup_payload_path: Path | None,
    daemon_result: dict[str, Any] | None,
    recorded_at: str,
) -> None:
    report = dict(status)
    report.update(
        {
            "source": source,
            "force": force,
            "recorded_at": recorded_at,
            "startup_payload_path": str(startup_payload_path) if startup_payload_path is not None else None,
            "daemon_result": daemon_result,
        }
    )
    _write_json(launch_report_path, report)


def archive_invalid_partial_quest_root(
    *,
    quest_root: Path,
    runtime_root: Path,
    slug: str,
) -> dict[str, Any] | None:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    quest_yaml_path = resolved_quest_root / "quest.yaml"
    if not resolved_quest_root.exists() or quest_yaml_path.exists():
        return None

    recovery_root = Path(runtime_root).expanduser().resolve() / "recovery" / "invalid_partial_quest_roots"
    archive_root = recovery_root / f"{resolved_quest_root.name}-{slug}"
    recovery_root.mkdir(parents=True, exist_ok=True)
    if archive_root.exists():
        raise FileExistsError(f"invalid partial quest recovery target already exists: {archive_root}")
    resolved_quest_root.rename(archive_root)
    return {
        "status": "archived_invalid_partial_quest_root",
        "quest_root": str(resolved_quest_root),
        "archived_root": str(archive_root),
        "missing_required_files": ["quest.yaml"],
    }
