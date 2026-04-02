from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .layout import build_workspace_runtime_layout_for_profile

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def resolve_study_runtime_paths(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, Path]:
    layout = build_workspace_runtime_layout_for_profile(profile)
    resolved_study_root = Path(study_root).expanduser().resolve()
    return {
        "quest_root": layout.quest_root(quest_id),
        "runtime_binding_path": resolved_study_root / "runtime_binding.yaml",
        "startup_payload_root": layout.startup_payload_root(study_id),
        "launch_report_path": resolved_study_root / "artifacts" / "runtime" / "last_launch_report.json",
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


def validate_startup_contract_resolution(*, startup_contract: dict[str, Any]) -> dict[str, Any]:
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
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "contract_statuses": {
            "medical_analysis_contract": analysis_status,
            "medical_reporting_contract": reporting_status,
        },
        "reason_codes": {
            "medical_analysis_contract": analysis_reason,
            "medical_reporting_contract": reporting_reason,
        },
    }


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
