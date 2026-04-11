from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from med_autoscience.controllers import workspace_literature as workspace_literature_controller
from med_autoscience import startup_literature
from med_autoscience import study_reference_context
from med_autoscience.runtime_event_record import RuntimeEventRecord, RuntimeEventRecordRef
from med_autoscience.runtime_escalation_record import (
    RuntimeEscalationRecord,
    RuntimeEscalationRecordRef,
    RuntimeEscalationTrigger,
)
from med_autoscience.study_decision_record import StudyDecisionRecord

from .layout import build_workspace_runtime_layout_for_profile
from .study_runtime_models import (
    StartupContractValidation,
    StartupContractValidationStatus,
    StartupHydrationReport,
    StartupHydrationStatus,
    StartupHydrationValidationReport,
    StartupHydrationValidationStatus,
    StudyRuntimeArtifacts,
    StudyRuntimeContext,
)

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def _launch_report_runtime_projection(status: dict[str, Any]) -> dict[str, Any]:
    runtime_liveness_audit = status.get("runtime_liveness_audit")
    runtime_audit = (
        dict(runtime_liveness_audit.get("runtime_audit"))
        if isinstance(runtime_liveness_audit, dict) and isinstance(runtime_liveness_audit.get("runtime_audit"), dict)
        else {}
    )
    supervisor_tick_audit = status.get("supervisor_tick_audit")
    return {
        "active_run_id": (
            str(
                status.get("active_run_id")
                or (runtime_liveness_audit.get("active_run_id") if isinstance(runtime_liveness_audit, dict) else None)
                or runtime_audit.get("active_run_id")
                or ""
            ).strip()
            or None
        ),
        "runtime_liveness_status": (
            str(
                status.get("runtime_liveness_status")
                or (runtime_liveness_audit.get("status") if isinstance(runtime_liveness_audit, dict) else None)
                or ""
            ).strip()
            or None
        ),
        "supervisor_tick_status": (
            str(
                status.get("supervisor_tick_status")
                or (supervisor_tick_audit.get("status") if isinstance(supervisor_tick_audit, dict) else None)
                or ""
            ).strip()
            or None
        ),
    }


def _runtime_escalation_record_path(quest_root: Path) -> Path:
    return (
        Path(quest_root).expanduser().resolve()
        / "artifacts"
        / "reports"
        / "escalation"
        / "runtime_escalation_record.json"
    )


def _runtime_event_report_root(quest_root: Path) -> Path:
    return (
        Path(quest_root).expanduser().resolve()
        / "artifacts"
        / "reports"
        / "runtime_events"
    )


def _artifact_timestamp_slug(recorded_at: str) -> str:
    normalized = recorded_at.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe_artifact_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    if not normalized:
        raise ValueError("study decision record decision_id must produce a non-empty artifact filename")
    return normalized


def _study_decision_record_path(*, study_root: Path, record: StudyDecisionRecord) -> Path:
    resolved_study_root = Path(study_root).expanduser().resolve()
    return (
        resolved_study_root
        / "artifacts"
        / "controller_decisions"
        / f"{_artifact_timestamp_slug(record.emitted_at)}_{_safe_artifact_id(record.decision_id)}.json"
    )


def _runtime_event_record_path(*, quest_root: Path, record: RuntimeEventRecord) -> Path:
    return _runtime_event_report_root(quest_root) / f"{_artifact_timestamp_slug(record.emitted_at)}_{_safe_artifact_id(record.event_kind)}.json"


def write_runtime_escalation_record(
    *,
    quest_root: Path,
    record: RuntimeEscalationRecord,
) -> RuntimeEscalationRecord:
    path = _runtime_escalation_record_path(quest_root)
    persisted_record = record.with_artifact_path(str(path))
    payload = persisted_record.to_dict()
    _write_json(path, payload)
    return RuntimeEscalationRecord.from_payload(payload)


def read_runtime_escalation_record_ref(
    *,
    quest_root: Path,
) -> RuntimeEscalationRecordRef | None:
    path = _runtime_escalation_record_path(quest_root)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("runtime escalation record artifact must contain a mapping payload")
    return RuntimeEscalationRecord.from_payload(payload).ref()


def write_runtime_event_record(
    *,
    quest_root: Path,
    record: RuntimeEventRecord,
) -> RuntimeEventRecord:
    path = _runtime_event_record_path(quest_root=quest_root, record=record)
    persisted_record = record.with_artifact_path(str(path))
    payload = persisted_record.to_dict()
    _write_json(path, payload)
    _write_json(path.parent / "latest.json", payload)
    return RuntimeEventRecord.from_payload(payload)


def read_runtime_event_record_ref(
    *,
    quest_root: Path,
) -> RuntimeEventRecordRef | None:
    path = _runtime_event_report_root(quest_root) / "latest.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("runtime event record artifact must contain a mapping payload")
    return RuntimeEventRecord.from_payload(payload).ref()


def write_study_decision_record(
    *,
    study_root: Path,
    record: StudyDecisionRecord,
) -> StudyDecisionRecord:
    path = _study_decision_record_path(study_root=study_root, record=record)
    persisted_record = record.with_artifact_path(str(path))
    payload = persisted_record.to_dict()
    _write_json(path, payload)
    _write_json(path.parent / "latest.json", payload)
    return StudyDecisionRecord.from_payload(payload)


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


def build_hydration_payload(
    *,
    create_payload: dict[str, Any],
    study_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, object]:
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
    payload: dict[str, object] = {
        "medical_analysis_contract": dict(medical_analysis_contract),
        "medical_reporting_contract": dict(medical_reporting_contract),
        "entry_state_summary": entry_state_summary.strip(),
        "literature_records": startup_literature.resolve_startup_literature_records(startup_contract=startup_contract),
    }
    if (study_root is None) != (workspace_root is None):
        raise ValueError("study_root and workspace_root must be provided together")
    if study_root is None or workspace_root is None:
        return payload

    reference_context = study_reference_context.build_study_reference_context(
        study_root=study_root,
        workspace_root=workspace_root,
        startup_contract=startup_contract,
    )
    payload["workspace_literature"] = workspace_literature_controller.workspace_literature_status(
        workspace_root=workspace_root
    )
    payload["study_reference_context"] = reference_context
    payload["literature_records"] = list(reference_context.get("records") or [])
    return payload


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
    report.update(_launch_report_runtime_projection(report))
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
