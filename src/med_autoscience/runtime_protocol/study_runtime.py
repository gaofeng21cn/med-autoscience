from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from med_autoscience import opl_runtime_contract
from med_autoscience.runtime_event_record import RuntimeEventRecord, RuntimeEventRecordRef
from med_autoscience.workspace_contracts import build_workspace_runtime_layout_for_profile
from .study_runtime_models import (
    StudyRuntimeArtifacts,
    StudyRuntimeContext,
)

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


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
    opl_control = (
        dict(status.get("opl_current_control_state"))
        if isinstance(status.get("opl_current_control_state"), dict)
        else (
            dict(status.get("current_control_state"))
            if isinstance(status.get("current_control_state"), dict)
            else {}
        )
    )
    runtime_liveness_status = (
        str(
            opl_control.get("status")
            or opl_control.get("state")
            or status.get("runtime_liveness_status")
            or (runtime_liveness_audit.get("status") if isinstance(runtime_liveness_audit, dict) else None)
            or ""
        ).strip()
        or None
    )
    observed_active_run_id = (
        str(
            opl_control.get("active_run_id")
            or status.get("active_run_id")
            or (runtime_liveness_audit.get("active_run_id") if isinstance(runtime_liveness_audit, dict) else None)
            or runtime_audit.get("active_run_id")
            or ""
        ).strip()
        or None
    )
    last_known_run_id = str(status.get("last_known_run_id") or "").strip() or None
    worker_running = (
        runtime_audit.get("worker_running")
        if isinstance(runtime_audit.get("worker_running"), bool)
        else (runtime_liveness_audit.get("worker_running") if isinstance(runtime_liveness_audit, dict) else None)
    )
    strict_live_active_run_id = (
        observed_active_run_id
        if (
            (
                bool(opl_control)
                and runtime_liveness_status
                in {"attempt_running", "provider_admitted", "running", "live"}
                and observed_active_run_id is not None
            )
            or (
                not opl_control
                and runtime_liveness_status == "live"
                and observed_active_run_id is not None
                and worker_running is True
            )
        )
        else None
    )
    return {
        "active_run_id": strict_live_active_run_id,
        "last_known_run_id": (observed_active_run_id or last_known_run_id) if strict_live_active_run_id is None else None,
        "runtime_liveness_status": runtime_liveness_status,
        "supervisor_tick_status": (
            str(
                status.get("supervisor_tick_status")
                or (supervisor_tick_audit.get("status") if isinstance(supervisor_tick_audit, dict) else None)
                or ""
            ).strip()
            or None
        ),
    }


def _runtime_binding_opl_metadata(status: dict[str, Any]) -> tuple[str, str]:
    execution = status.get("execution")
    execution_mapping = execution if isinstance(execution, dict) else None
    runtime_ref = (
        opl_runtime_contract.explicit_opl_runtime_ref(execution_mapping)
        or opl_runtime_contract.OPL_HOSTED_STAGE_RUNTIME_ID
    )
    expected_runtime_engine_id = opl_runtime_contract.engine_id_for_runtime_ref(runtime_ref)
    runtime_engine_id = str(
        (execution_mapping or {}).get("runtime_engine_id")
        or (execution_mapping or {}).get("engine")
        or expected_runtime_engine_id
    ).strip()
    if not runtime_engine_id:
        raise ValueError(f"OPL runtime ref `{runtime_ref}` is missing runtime_engine_id")
    return runtime_ref, runtime_engine_id


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


def _runtime_event_record_path(*, quest_root: Path, record: RuntimeEventRecord) -> Path:
    return _runtime_event_report_root(quest_root) / f"{_artifact_timestamp_slug(record.emitted_at)}_{_safe_artifact_id(record.event_kind)}.json"


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
    opl_runtime_ref: str = opl_runtime_contract.OPL_HOSTED_STAGE_RUNTIME_ID,
    runtime_engine_id: str | None = None,
    research_backend_id: str | None = None,
    research_engine_id: str | None = None,
) -> None:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_runtime_engine_id = runtime_engine_id or opl_runtime_contract.engine_id_for_runtime_ref(
        opl_runtime_ref
    )
    resolved_research_backend_id, resolved_research_engine_id = opl_runtime_contract.controlled_research_backend_metadata_for_runtime_ref(
        opl_runtime_ref
    )
    _write_yaml(
        runtime_binding_path,
        {
            "schema_version": 1,
            "engine": resolved_runtime_engine_id,
            "runtime_owner": opl_runtime_contract.OPL_RUNTIME_OWNER,
            "domain_owner": opl_runtime_contract.MAS_DOMAIN_OWNER,
            "runtime_substrate": opl_runtime_contract.OPL_HOSTED_STAGE_RUNTIME_ID,
            "opl_runtime_ref": opl_runtime_ref,
            "runtime_ref": opl_runtime_ref,
            "runtime_engine_id": resolved_runtime_engine_id,
            "research_backend_id": research_backend_id or resolved_research_backend_id,
            "research_backend": research_backend_id or resolved_research_backend_id,
            "research_engine_id": research_engine_id or resolved_research_engine_id,
            "runtime_home": str(resolved_runtime_root),
            "study_id": study_id,
            "study_root": str(resolved_study_root),
            "quest_id": quest_id,
            "runtime_root": str(resolved_runtime_root / "quests"),
            "runtime_quests_root": str(resolved_runtime_root / "quests"),
            "historical_fixture_ref": {
                "surface_kind": "historical_fixture_ref",
                "runtime_root": str(resolved_runtime_root),
                "read_only": True,
            },
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
        opl_runtime_ref, runtime_engine_id = _runtime_binding_opl_metadata(status)
        research_backend_id = str(status.get("execution", {}).get("research_backend_id") or "").strip() or None
        research_engine_id = str(status.get("execution", {}).get("research_engine_id") or "").strip() or None
        write_runtime_binding(
            runtime_binding_path=runtime_binding_path,
            runtime_root=runtime_root,
            study_id=study_id,
            study_root=study_root,
            quest_id=resolved_quest_id,
            last_action=last_action,
            source=source,
            recorded_at=recorded_at,
            opl_runtime_ref=opl_runtime_ref,
            runtime_engine_id=runtime_engine_id,
            research_backend_id=research_backend_id,
            research_engine_id=research_engine_id,
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
