from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.controllers import study_runtime_family_orchestration as family_orchestration
from med_autoscience.native_runtime_event import NativeRuntimeEventRecord
from med_autoscience.runtime_event_record import RuntimeEventRecord, RuntimeEventRecordRef
from med_autoscience.runtime_escalation_record import (
    RuntimeEscalationRecord,
    RuntimeEscalationRecordRef,
    RuntimeEscalationTrigger,
)
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol


def _runtime_status_summary(
    status: dict[str, Any],
    *,
    managed_runtime_event: tuple[RuntimeEventRecordRef, RuntimeEventRecord | NativeRuntimeEventRecord, dict[str, Any] | None]
    | None = None,
) -> dict[str, str]:
    if managed_runtime_event is not None:
        runtime_event_ref, runtime_event_record, _runtime_escalation_payload = managed_runtime_event
        return _runtime_status_summary_from_runtime_event(
            status=status,
            runtime_event_ref=runtime_event_ref,
            runtime_event_record=runtime_event_record,
        )
    runtime_event_payload = status.get("runtime_event_ref")
    if isinstance(runtime_event_payload, dict):
        runtime_event_ref, runtime_event_record = _load_runtime_event_record(
            runtime_event_payload=runtime_event_payload
        )
        return _runtime_status_summary_from_runtime_event(
            status=status,
            runtime_event_ref=runtime_event_ref,
            runtime_event_record=runtime_event_record,
        )
    return {
        "decision": str(status.get("decision") or "").strip(),
        "reason": str(status.get("reason") or "").strip(),
    }


def _runtime_status_summary_from_runtime_event(
    *,
    status: dict[str, Any],
    runtime_event_ref: RuntimeEventRecordRef,
    runtime_event_record: RuntimeEventRecord | NativeRuntimeEventRecord,
) -> dict[str, str]:
    outer_loop_input = runtime_event_record.outer_loop_input
    if isinstance(runtime_event_record, RuntimeEventRecord):
        decision = str(outer_loop_input.get("decision") or "").strip()
        reason = str(outer_loop_input.get("reason") or "").strip()
        supervisor_tick_status = str(outer_loop_input.get("supervisor_tick_status") or "").strip()
    else:
        decision = str(status.get("decision") or "").strip()
        reason = str(status.get("reason") or "").strip()
        supervisor_tick_payload = status.get("supervisor_tick_audit")
        supervisor_tick_status = (
            str(supervisor_tick_payload.get("status") or "").strip()
            if isinstance(supervisor_tick_payload, dict)
            else ""
        )
    return {
        "decision": decision,
        "reason": reason,
        "quest_status": str(outer_loop_input.get("quest_status") or "").strip(),
        "active_run_id": str(outer_loop_input.get("active_run_id") or "").strip(),
        "runtime_liveness_status": str(outer_loop_input.get("runtime_liveness_status") or "").strip(),
        "supervisor_tick_status": supervisor_tick_status,
        "runtime_event_id": runtime_event_ref.event_id,
    }


def _runtime_status_active_run_id(status: dict[str, Any], runtime_status: dict[str, str]) -> str | None:
    return family_orchestration.resolve_active_run_id(
        runtime_status.get("active_run_id"),
        status.get("active_run_id"),
        ((status.get("execution_owner_guard") or {}) if isinstance(status.get("execution_owner_guard"), dict) else {}).get(
            "active_run_id"
        ),
        ((status.get("autonomous_runtime_notice") or {}) if isinstance(status.get("autonomous_runtime_notice"), dict) else {}).get(
            "active_run_id"
        ),
    )


def _load_runtime_escalation_record(
    *,
    runtime_escalation_payload: dict[str, Any],
) -> tuple[RuntimeEscalationRecordRef, RuntimeEscalationRecord]:
    runtime_escalation_ref = RuntimeEscalationRecordRef.from_payload(runtime_escalation_payload)
    artifact_path = Path(runtime_escalation_ref.artifact_path).expanduser().resolve()
    payload = json.loads(artifact_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("runtime escalation record artifact must contain a mapping payload")
    record = RuntimeEscalationRecord.from_payload(payload)
    written_ref = record.ref()
    if written_ref.record_id != runtime_escalation_ref.record_id:
        raise ValueError("study_outer_loop_tick runtime escalation record_id mismatch against status ref")
    if Path(written_ref.artifact_path).expanduser().resolve() != artifact_path:
        raise ValueError("study_outer_loop_tick runtime escalation artifact_path mismatch against status ref")
    if written_ref.summary_ref != runtime_escalation_ref.summary_ref:
        raise ValueError("study_outer_loop_tick runtime escalation summary_ref mismatch against status ref")
    return written_ref, record


def _load_runtime_event_record(
    *,
    runtime_event_payload: dict[str, Any],
) -> tuple[RuntimeEventRecordRef, RuntimeEventRecord | NativeRuntimeEventRecord]:
    runtime_event_ref = RuntimeEventRecordRef.from_payload(runtime_event_payload)
    artifact_path = Path(runtime_event_ref.artifact_path).expanduser().resolve()
    payload = json.loads(artifact_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("runtime event record artifact must contain a mapping payload")
    try:
        record = RuntimeEventRecord.from_payload(payload)
    except (TypeError, ValueError):
        record = NativeRuntimeEventRecord.from_payload(payload)
    written_ref = record.ref()
    if written_ref.event_id != runtime_event_ref.event_id:
        raise ValueError("study_outer_loop_tick runtime event event_id mismatch against status ref")
    if Path(written_ref.artifact_path).expanduser().resolve() != artifact_path:
        raise ValueError("study_outer_loop_tick runtime event artifact_path mismatch against status ref")
    if written_ref.summary_ref != runtime_event_ref.summary_ref:
        raise ValueError("study_outer_loop_tick runtime event summary_ref mismatch against status ref")
    return written_ref, record


def _managed_runtime_requires_event_ref(status: dict[str, Any]) -> bool:
    execution = status.get("execution")
    if not runtime_backend_contract.is_managed_research_execution(execution if isinstance(execution, dict) else None):
        return False
    return isinstance(status.get("runtime_event_ref"), dict)


def _hydrate_managed_runtime_refs(status: dict[str, Any]) -> dict[str, Any]:
    hydrated = dict(status)
    quest_root_text = str(hydrated.get("quest_root") or "").strip()
    if not quest_root_text:
        return hydrated
    quest_root = Path(quest_root_text).expanduser().resolve()
    if not isinstance(hydrated.get("runtime_event_ref"), dict):
        runtime_event_ref = None
        try:
            runtime_event_ref = study_runtime_protocol.read_runtime_event_record_ref(quest_root=quest_root)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            runtime_event_path = quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json"
            if runtime_event_path.exists():
                raw_payload = json.loads(runtime_event_path.read_text(encoding="utf-8")) or {}
                if isinstance(raw_payload, dict):
                    raw_payload = dict(raw_payload)
                    raw_payload.setdefault("artifact_path", str(runtime_event_path))
                    try:
                        runtime_event_ref = RuntimeEventRecord.from_payload(raw_payload).ref()
                    except (TypeError, ValueError):
                        try:
                            runtime_event_ref = NativeRuntimeEventRecord.from_payload(raw_payload).ref()
                        except (TypeError, ValueError):
                            runtime_event_ref = None
        if runtime_event_ref is not None:
            hydrated["runtime_event_ref"] = runtime_event_ref.to_dict()
    if not isinstance(hydrated.get("runtime_escalation_ref"), dict):
        runtime_escalation_ref = study_runtime_protocol.read_runtime_escalation_record_ref(quest_root=quest_root)
        if runtime_escalation_ref is not None:
            hydrated["runtime_escalation_ref"] = runtime_escalation_ref.to_dict()
    return hydrated


def _resolve_managed_runtime_event_contract(
    *,
    status: dict[str, Any],
) -> tuple[RuntimeEventRecordRef, RuntimeEventRecord | NativeRuntimeEventRecord, dict[str, Any] | None]:
    runtime_event_payload = status.get("runtime_event_ref")
    if not isinstance(runtime_event_payload, dict):
        raise ValueError("study_outer_loop_tick requires runtime_event_ref from managed runtime status")
    runtime_event_ref, runtime_event_record = _load_runtime_event_record(
        runtime_event_payload=runtime_event_payload
    )
    status_study_id = str(status.get("study_id") or "").strip()
    status_quest_id = str(status.get("quest_id") or "").strip()
    if isinstance(runtime_event_record, RuntimeEventRecord) and status_study_id and runtime_event_record.study_id != status_study_id:
        raise ValueError("study_outer_loop_tick runtime event study_id mismatch against status")
    if status_quest_id and runtime_event_record.quest_id != status_quest_id:
        raise ValueError("study_outer_loop_tick runtime event quest_id mismatch against status")
    if isinstance(runtime_event_record, RuntimeEventRecord):
        supervisor_tick_status = str(runtime_event_record.outer_loop_input.get("supervisor_tick_status") or "").strip()
        runtime_escalation_payload = runtime_event_record.outer_loop_input.get("runtime_escalation_ref")
        if runtime_escalation_payload is not None and not isinstance(runtime_escalation_payload, dict):
            raise ValueError("study_outer_loop_tick runtime_event runtime_escalation_ref must be a mapping")
    else:
        supervisor_tick_payload = status.get("supervisor_tick_audit")
        supervisor_tick_status = (
            str(supervisor_tick_payload.get("status") or "").strip()
            if isinstance(supervisor_tick_payload, dict)
            else ""
        )
        runtime_escalation_payload = status.get("runtime_escalation_ref")
    if supervisor_tick_status != "fresh":
        raise ValueError("study_outer_loop_tick requires supervisor_tick_status=fresh in managed runtime event input")
    status_runtime_escalation_payload = status.get("runtime_escalation_ref")
    if isinstance(runtime_event_record, RuntimeEventRecord) and isinstance(status_runtime_escalation_payload, dict):
        if runtime_escalation_payload is None:
            raise ValueError("study_outer_loop_tick requires runtime_escalation_ref in managed runtime event input")
        if status_runtime_escalation_payload != runtime_escalation_payload:
            raise ValueError("study_outer_loop_tick runtime escalation ref mismatch against runtime_event")
    return runtime_event_ref, runtime_event_record, runtime_escalation_payload


def _resolve_runtime_escalation_record(
    *,
    runtime_escalation_payload: dict[str, Any] | None,
    status: dict[str, Any] | None = None,
    study_root: Path | None = None,
    study_id: str | None = None,
    quest_id: str | None = None,
    emitted_at: str | None = None,
    source: str | None = None,
    runtime_status: dict[str, str] | None = None,
) -> tuple[RuntimeEscalationRecordRef, RuntimeEscalationRecord]:
    if isinstance(runtime_escalation_payload, dict):
        return _load_runtime_escalation_record(runtime_escalation_payload=runtime_escalation_payload)
    if (
        isinstance(status, dict)
        and study_root is not None
        and study_id is not None
        and quest_id is not None
        and emitted_at is not None
    ):
        quest_root_text = str(status.get("quest_root") or "").strip()
        if not quest_root_text:
            raise ValueError("study_outer_loop_tick requires quest_root to materialize runtime_escalation_ref")
        quest_root = Path(quest_root_text).expanduser().resolve()
        summary_path = (study_root / "artifacts" / "runtime" / "last_launch_report.json").resolve()
        runtime_event_payload = status.get("runtime_event_ref")
        runtime_event_path = (
            str(runtime_event_payload.get("artifact_path") or "").strip()
            if isinstance(runtime_event_payload, dict)
            else ""
        )
        supervisor_tick_payload = status.get("supervisor_tick_audit")
        runtime_supervision_path = (
            str(supervisor_tick_payload.get("latest_report_path") or "").strip()
            if isinstance(supervisor_tick_payload, dict)
            else ""
        )
        evidence_refs = tuple(
            path
            for path in (
                runtime_event_path,
                runtime_supervision_path,
                str(summary_path),
            )
            if path
        )
        escalation_reason = (
            str((runtime_status or {}).get("reason") or "").strip()
            or str(status.get("reason") or "").strip()
            or "managed_runtime_outer_loop_wakeup"
        )
        record = RuntimeEscalationRecord(
            schema_version=1,
            record_id=f"runtime-escalation::{study_id}::{quest_id}::{escalation_reason}::{emitted_at}",
            study_id=study_id,
            quest_id=quest_id,
            emitted_at=emitted_at,
            trigger=RuntimeEscalationTrigger(
                trigger_id=escalation_reason,
                source=str(source or "study_outer_loop_tick").strip() or "study_outer_loop_tick",
            ),
            scope="quest",
            severity="quest",
            reason=escalation_reason,
            recommended_actions=("controller_review_required",),
            evidence_refs=evidence_refs,
            runtime_context_refs={
                "launch_report_path": str(summary_path),
            },
            summary_ref=str(summary_path),
            artifact_path=None,
        )
        written_record = study_runtime_protocol.write_runtime_escalation_record(
            quest_root=quest_root,
            record=record,
        )
        return written_record.ref(), written_record
    raise ValueError("study_outer_loop_tick requires runtime_escalation_ref from managed runtime input")

