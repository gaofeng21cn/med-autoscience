from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from med_autoscience import publication_display_contract
from med_autoscience.controllers._medical_display_surface_support import resolve_required_display_surface_stub
from med_autoscience.controllers import paper_artifacts


class StartupHydrationValidationStatus(StrEnum):
    CLEAR = "clear"
    BLOCKED = "blocked"


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
            medical_analysis_contract_status=(str(contract_statuses.get("medical_analysis_contract") or "") or None),
            medical_reporting_contract_status=(str(contract_statuses.get("medical_reporting_contract") or "") or None),
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
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def write_startup_hydration_validation_report(
    *,
    quest_root: Path,
    report: StartupHydrationValidationReport,
) -> StartupHydrationValidationReport:
    path = (
        Path(quest_root).expanduser().resolve()
        / "artifacts"
        / "reports"
        / "startup"
        / "hydration_validation_report.json"
    )
    payload = report.to_dict()
    payload["report_path"] = str(path)
    _write_json(path, payload)
    return StartupHydrationValidationReport.from_payload(payload)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_dict(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _validate_contract_status(
    *,
    contract_path: Path,
    missing_blocker: str,
    invalid_blocker: str,
    unsupported_blocker: str,
    unresolved_blocker: str,
) -> tuple[str | None, str | None]:
    if not contract_path.exists():
        return None, missing_blocker
    try:
        payload = _read_json_dict(contract_path)
    except (json.JSONDecodeError, OSError, ValueError):
        return None, invalid_blocker
    status = str(payload.get("status") or "").strip()
    if status == "resolved":
        return status, None
    if status == "unsupported":
        return status, unsupported_blocker
    return status or None, unresolved_blocker


def _is_legacy_display_id(*, display_id: str, display_kind: str) -> bool:
    item = display_id.strip()
    kind = display_kind.strip()
    if kind == "figure":
        return bool(item) and item.lower().startswith("figure") and item[6:].isdigit()
    if kind == "table":
        return bool(item) and item.lower().startswith("table") and item[5:].isdigit()
    return False


def _normalize_display_shell_plan(reporting_contract: dict[str, Any]) -> list[dict[str, str]]:
    plan = reporting_contract.get("display_shell_plan")
    normalized: list[dict[str, str]] = []
    if isinstance(plan, list):
        for item in plan:
            if not isinstance(item, dict):
                raise ValueError("medical_reporting_contract.display_shell_plan must contain mappings")
            display_id_value = item.get("display_id")
            display_kind_value = item.get("display_kind")
            requirement_key_value = item.get("requirement_key")
            if not isinstance(display_id_value, str) or not display_id_value.strip():
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include non-empty string display_id"
                )
            if not isinstance(display_kind_value, str) or not display_kind_value.strip():
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include non-empty string display_kind"
                )
            if not isinstance(requirement_key_value, str) or not requirement_key_value.strip():
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include non-empty string requirement_key"
                )
            if "catalog_id" in item:
                catalog_id_value = item.get("catalog_id")
                if catalog_id_value is not None and not isinstance(catalog_id_value, str):
                    raise ValueError(
                        "medical_reporting_contract.display_shell_plan items must include string catalog_id when provided"
                    )
                if isinstance(catalog_id_value, str):
                    catalog_id = catalog_id_value.strip()
                else:
                    catalog_id = ""
            else:
                catalog_id = ""
            display_id = display_id_value.strip()
            display_kind = display_kind_value.strip()
            requirement_key = requirement_key_value.strip()
            if resolve_required_display_surface_stub(requirement_key) is None:
                raise ValueError(
                    f"medical_reporting_contract.display_shell_plan contains unsupported requirement_key: {requirement_key}"
                )
            if not catalog_id and not _is_legacy_display_id(display_id=display_id, display_kind=display_kind):
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan semantic display_id items must include catalog_id"
                )
            if not display_id or not display_kind or not requirement_key:
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include display_id, display_kind, requirement_key"
                )
            normalized.append(
                {
                    "display_id": display_id,
                    "display_kind": display_kind,
                    "requirement_key": requirement_key,
                }
            )
        return normalized

    legacy_keys = (
        "cohort_flow_required",
        "baseline_characteristics_required",
        "figure_shell_requirements",
        "table_shell_requirements",
    )
    if not any(key in reporting_contract for key in legacy_keys):
        return normalized

    figure_shell_requirements = list(reporting_contract.get("figure_shell_requirements") or [])
    table_shell_requirements = list(reporting_contract.get("table_shell_requirements") or [])
    cohort_flow_required = reporting_contract.get("cohort_flow_required")
    baseline_required = reporting_contract.get("baseline_characteristics_required")
    if cohort_flow_required is False:
        cohort_flow_enabled = False
    elif figure_shell_requirements:
        cohort_flow_enabled = "cohort_flow_figure" in figure_shell_requirements
    else:
        cohort_flow_enabled = True
    if baseline_required is False:
        baseline_enabled = False
    elif table_shell_requirements:
        baseline_enabled = "table1_baseline_characteristics" in table_shell_requirements
    else:
        baseline_enabled = True

    if cohort_flow_enabled:
        normalized.append(
            {
                "display_id": "cohort_flow",
                "display_kind": "figure",
                "requirement_key": "cohort_flow_figure",
            }
        )
    if baseline_enabled:
        normalized.append(
            {
                "display_id": "baseline_characteristics",
                "display_kind": "table",
                "requirement_key": "table1_baseline_characteristics",
            }
        )
    return normalized


def run_validation(*, quest_root: Path) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    try:
        paper_root = paper_artifacts.resolve_latest_paper_root(resolved_quest_root)
    except FileNotFoundError:
        paper_root = resolved_quest_root / "paper"
    analysis_path = paper_root / "medical_analysis_contract.json"
    reporting_path = paper_root / "medical_reporting_contract.json"
    blockers: list[str] = []
    analysis_status, analysis_blocker = _validate_contract_status(
        contract_path=analysis_path,
        missing_blocker="missing_medical_analysis_contract",
        invalid_blocker="invalid_medical_analysis_contract",
        unsupported_blocker="unsupported_medical_analysis_contract",
        unresolved_blocker="unresolved_medical_analysis_contract",
    )
    reporting_status, reporting_blocker = _validate_contract_status(
        contract_path=reporting_path,
        missing_blocker="missing_medical_reporting_contract",
        invalid_blocker="invalid_medical_reporting_contract",
        unsupported_blocker="unsupported_medical_reporting_contract",
        unresolved_blocker="unresolved_medical_reporting_contract",
    )
    if analysis_blocker is not None:
        blockers.append(analysis_blocker)
    if reporting_blocker is not None:
        blockers.append(reporting_blocker)

    if reporting_blocker is None:
        reporting_payload = _read_json_dict(reporting_path)
        raw_display_shell_plan = reporting_payload.get("display_shell_plan")
        try:
            display_shell_plan = _normalize_display_shell_plan(reporting_payload)
        except ValueError:
            blockers.append("invalid_display_shell_plan")
            display_shell_plan = []
        display_surface_default = bool(raw_display_shell_plan) if isinstance(raw_display_shell_plan, list) else bool(
            display_shell_plan
        )
        display_surface_enabled = bool(reporting_payload.get("display_registry_required", display_surface_default))
        if display_surface_enabled:
            publication_style_profile_path = paper_root / "publication_style_profile.json"
            display_overrides_path = paper_root / "display_overrides.json"
            if not publication_style_profile_path.exists():
                blockers.append("missing_publication_style_profile")
            else:
                try:
                    publication_display_contract.load_publication_style_profile(publication_style_profile_path)
                except (OSError, ValueError, json.JSONDecodeError):
                    blockers.append("invalid_publication_style_profile")
            if not display_overrides_path.exists():
                blockers.append("missing_display_overrides")
            else:
                try:
                    publication_display_contract.load_display_overrides(display_overrides_path)
                except (OSError, ValueError, json.JSONDecodeError):
                    blockers.append("invalid_display_overrides")
            display_registry_path = paper_root / "display_registry.json"
            if not display_registry_path.exists():
                blockers.append("missing_display_registry")
            for item in display_shell_plan:
                if item["display_kind"] == "figure":
                    shell_path = paper_root / "figures" / f"{item['display_id']}.shell.json"
                else:
                    shell_path = paper_root / "tables" / f"{item['display_id']}.shell.json"
                if not shell_path.exists():
                    blockers.append(f"missing_{item['display_id'].lower()}_shell")
                stub = resolve_required_display_surface_stub(item["requirement_key"])
                if stub is not None and not (paper_root / stub.filename).exists():
                    blockers.append(stub.blocker_key)

    report = write_startup_hydration_validation_report(
        quest_root=resolved_quest_root,
        report=StartupHydrationValidationReport(
            status=(
                StartupHydrationValidationStatus.BLOCKED
                if blockers
                else StartupHydrationValidationStatus.CLEAR
            ),
            recorded_at=_utc_now(),
            quest_root=str(resolved_quest_root),
            blockers=tuple(blockers),
            medical_analysis_contract_status=analysis_status,
            medical_reporting_contract_status=reporting_status,
            medical_analysis_contract_path=str(analysis_path),
            medical_reporting_contract_path=str(reporting_path),
            report_path=None,
        ),
    )
    return report.to_dict()
