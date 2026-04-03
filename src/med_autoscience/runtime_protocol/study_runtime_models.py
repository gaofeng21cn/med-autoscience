from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


__all__ = [
    "StartupContractValidation",
    "StartupContractValidationStatus",
    "StartupHydrationReport",
    "StartupHydrationStatus",
    "StartupHydrationValidationReport",
    "StartupHydrationValidationStatus",
    "StudyRuntimeArtifacts",
    "StudyRuntimeContext",
]


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

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime_binding_path": str(self.runtime_binding_path),
            "launch_report_path": str(self.launch_report_path),
            "startup_payload_path": str(self.startup_payload_path) if self.startup_payload_path is not None else None,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeArtifacts":
        if not isinstance(payload, dict):
            raise TypeError("study runtime artifacts payload must be a mapping")
        runtime_binding_path = str(payload.get("runtime_binding_path") or "").strip()
        if not runtime_binding_path:
            raise ValueError("study runtime artifacts payload missing runtime_binding_path")
        launch_report_path = str(payload.get("launch_report_path") or "").strip()
        if not launch_report_path:
            raise ValueError("study runtime artifacts payload missing launch_report_path")
        startup_payload_raw = payload.get("startup_payload_path")
        startup_payload_path: Path | None
        if startup_payload_raw is None or str(startup_payload_raw).strip() == "":
            startup_payload_path = None
        else:
            startup_payload_path = Path(str(startup_payload_raw))
        return cls(
            runtime_binding_path=Path(runtime_binding_path),
            launch_report_path=Path(launch_report_path),
            startup_payload_path=startup_payload_path,
        )


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
