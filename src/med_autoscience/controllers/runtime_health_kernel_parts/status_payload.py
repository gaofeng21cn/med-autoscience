from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_runtime_refs import resolve_opl_runtime_refs

from . import event_log, provider_readiness


JsonReader = Callable[[Path | None], dict[str, Any] | None]
MappingReader = Callable[[object], dict[str, Any]]
TextReader = Callable[[object], str | None]
EventSourceSignature = Callable[[str, Mapping[str, Any]], str]
StableAudit = Callable[[Mapping[str, Any]], dict[str, Any]]


def transient_event(
    *,
    schema_version: int,
    study_id: str,
    quest_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
    event_source_signature: EventSourceSignature,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "event_id": event_log.build_event_id(
            study_id=study_id,
            quest_id=quest_id,
            event_type=event_type,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
        "quest_id": quest_id,
        "event_type": event_type,
        "recorded_at": recorded_at,
        "payload": dict(payload),
        "source_signature": event_source_signature(event_type, payload),
        "transient": True,
    }


def status_payload_runtime_health_events(
    *,
    schema_version: int,
    recovery_decisions: Iterable[str],
    volatile_supervisor_keys: frozenset[str],
    study_id: str,
    quest_id: str,
    status_payload: Mapping[str, Any],
    recorded_at: str,
    first_sequence: int,
    read_json: JsonReader,
    mapping: MappingReader,
    text: TextReader,
    event_source_signature: EventSourceSignature,
    stable_runtime_audit: StableAudit,
    stable_runtime_liveness_audit: StableAudit,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sequence = first_sequence
    facts = resolve_opl_runtime_refs(status_payload)
    lifecycle_proof_ref = _opl_lifecycle_proof_ref(status_payload, mapping=mapping, text=text)
    runtime_liveness_audit = mapping(status_payload.get("runtime_liveness_audit"))
    runtime_audit = mapping(runtime_liveness_audit.get("runtime_audit"))
    runtime_payload = {
        "quest_status": text(status_payload.get("quest_status")),
        "decision": text(status_payload.get("decision")),
        "reason": text(status_payload.get("reason")),
        "runtime_liveness_status": facts.runtime_liveness_status,
        "worker_running": facts.worker_running,
        "worker_pending": facts.worker_pending,
        "stop_requested": facts.stop_requested,
        "active_run_id": facts.active_run_id if facts.strict_live else None,
        "observed_at": recorded_at,
        "runtime_audit": stable_runtime_audit(runtime_audit) or None,
        "runtime_liveness_audit": stable_runtime_liveness_audit(runtime_liveness_audit) or None,
        "liveness_guard_reason": text(runtime_liveness_audit.get("liveness_guard_reason")),
        "autonomy_slo": mapping(status_payload.get("autonomy_slo")) or None,
        "progress_freshness": mapping(status_payload.get("progress_freshness")) or None,
    }
    runtime_payload = {key: value for key, value in runtime_payload.items() if value is not None}
    if runtime_payload:
        sequence += 1
        events.append(
            transient_event(
                schema_version=schema_version,
                study_id=study_id,
                quest_id=quest_id,
                event_type="runtime_state_observed",
                payload=runtime_payload,
                recorded_at=recorded_at,
                sequence=sequence,
                event_source_signature=event_source_signature,
            )
        )

    supervisor_tick_audit = mapping(status_payload.get("supervisor_tick_audit"))
    if supervisor_tick_audit:
        supervisor_payload = {
            key: value
            for key, value in supervisor_tick_audit.items()
            if key not in volatile_supervisor_keys
        }
        if "provider_readiness" not in supervisor_payload:
            readiness_payload = provider_readiness.provider_readiness_from_status_payload(
                status_payload,
                mapping=mapping,
            )
            if readiness_payload:
                supervisor_payload["provider_readiness"] = readiness_payload
        supervisor_payload["supervisor_tick_status"] = text(supervisor_tick_audit.get("status"))
        sequence += 1
        events.append(
            transient_event(
                schema_version=schema_version,
                study_id=study_id,
                quest_id=quest_id,
                event_type="supervisor_tick",
                payload=supervisor_payload,
                recorded_at=recorded_at,
                sequence=sequence,
                event_source_signature=event_source_signature,
            )
        )
        if lifecycle_proof_ref is not None and provider_readiness.recovered_supervisor_tick(
            supervisor_payload,
            mapping=mapping,
            text=text,
            bool_value=_bool,
        ):
            sequence += 1
            events.append(
                transient_event(
                    schema_version=schema_version,
                    study_id=study_id,
                    quest_id=quest_id,
                    event_type="attempt_released",
                    payload={
                        "release_reason": "provider_recovered_after_runtime_retry_exhaustion",
                        "decision": text(status_payload.get("decision")),
                        "reason": text(status_payload.get("reason")),
                        "previous_budget_scope": "terminal_runtime_recovery",
                        "provider_ready": True,
                        "worker_ready": True,
                        "managed_worker_source_current": True,
                        "opl_lifecycle_proof_ref": lifecycle_proof_ref,
                        "lifecycle_authority_owner": "one-person-lab",
                        "mas_runtime_health_event_role": "diagnostic_observation",
                        "attempt_lifecycle_authority": False,
                        "retry_or_dead_letter_authority": False,
                    },
                    recorded_at=recorded_at,
                    sequence=sequence,
                    event_source_signature=event_source_signature,
                )
            )

    launch_payload = launch_report_event_payload(status_payload, read_json=read_json, mapping=mapping, text=text)
    if launch_payload and lifecycle_proof_ref is not None:
        launch_payload = _with_lifecycle_boundary(launch_payload, lifecycle_proof_ref=lifecycle_proof_ref)
        sequence += 1
        events.append(
            transient_event(
                schema_version=schema_version,
                study_id=study_id,
                quest_id=quest_id,
                event_type="launch_attempt",
                payload=launch_payload,
                recorded_at=recorded_at,
                sequence=sequence,
                event_source_signature=event_source_signature,
            )
        )

    decision = text(status_payload.get("decision"))
    if decision in recovery_decisions and lifecycle_proof_ref is not None:
        event_type = "relaunch_attempt" if decision == "relaunch_stopped" else "recover_attempt"
        if event_type == "relaunch_attempt":
            sequence += 1
            events.append(
                transient_event(
                    schema_version=schema_version,
                    study_id=study_id,
                    quest_id=quest_id,
                    event_type="attempt_released",
                    payload={
                        "release_reason": "explicit_relaunch_stopped",
                        "decision": decision,
                        "reason": text(status_payload.get("reason")),
                        "previous_budget_scope": "terminal_runtime_recovery",
                        "opl_lifecycle_proof_ref": lifecycle_proof_ref,
                        "lifecycle_authority_owner": "one-person-lab",
                        "mas_runtime_health_event_role": "diagnostic_observation",
                        "attempt_lifecycle_authority": False,
                        "retry_or_dead_letter_authority": False,
                    },
                    recorded_at=recorded_at,
                    sequence=sequence,
                    event_source_signature=event_source_signature,
                )
            )
        sequence += 1
        events.append(
            transient_event(
                schema_version=schema_version,
                study_id=study_id,
                quest_id=quest_id,
                event_type=event_type,
                payload={
                    "attempt_state": "requested",
                    "decision": decision,
                    "reason": text(status_payload.get("reason")),
                    "active_run_id": facts.active_run_id if facts.strict_live else None,
                    "opl_lifecycle_proof_ref": lifecycle_proof_ref,
                    "lifecycle_authority_owner": "one-person-lab",
                    "mas_runtime_health_event_role": "diagnostic_observation",
                    "attempt_lifecycle_authority": False,
                    "retry_or_dead_letter_authority": False,
                },
                recorded_at=recorded_at,
                sequence=sequence,
                event_source_signature=event_source_signature,
            )
        )
    return events


def _with_lifecycle_boundary(
    payload: Mapping[str, Any],
    *,
    lifecycle_proof_ref: str,
) -> dict[str, Any]:
    return {
        **dict(payload),
        "opl_lifecycle_proof_ref": lifecycle_proof_ref,
        "lifecycle_authority_owner": "one-person-lab",
        "mas_runtime_health_event_role": "diagnostic_observation",
        "attempt_lifecycle_authority": False,
        "retry_or_dead_letter_authority": False,
    }


def _opl_lifecycle_proof_ref(
    status_payload: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str | None:
    for source in (
        status_payload,
        mapping(status_payload.get("opl_current_control_state_handoff")),
        mapping(status_payload.get("runtime_liveness_audit")),
        mapping(status_payload.get("runtime_audit")),
    ):
        for key in (
            "opl_lifecycle_proof_ref",
            "opl_lifecycle_ref",
            "opl_command_ref",
            "opl_event_ref",
            "opl_outbox_ref",
            "opl_stage_run_ref",
            "opl_stage_attempt_id",
            "stage_attempt_id",
            "active_stage_attempt_id",
            "active_workflow_id",
        ):
            if value := text(source.get(key)):
                return value
    facts = resolve_opl_runtime_refs(status_payload)
    if facts.strict_live and facts.active_run_id:
        return facts.active_run_id
    return None


def launch_report_event_payload(
    status_payload: Mapping[str, Any],
    *,
    read_json: JsonReader,
    mapping: MappingReader,
    text: TextReader,
) -> dict[str, Any]:
    direct_report = mapping(status_payload.get("last_launch_report"))
    launch_report_path = _candidate_path(status_payload.get("launch_report_path"), text=text)
    file_report = read_json(launch_report_path) if launch_report_path is not None else None
    report = direct_report or mapping(file_report)
    if not report:
        return {}
    active_run_id = _first_text(
        report.get("active_run_id"),
        mapping(report.get("autonomous_runtime_notice")).get("active_run_id"),
        mapping(report.get("runtime_liveness_audit")).get("active_run_id"),
        text=text,
    )
    if active_run_id is None and text(report.get("last_action")) is None:
        return {}
    return {
        "attempt_state": text(report.get("dispatch_status")) or text(report.get("status")) or "observed",
        "active_run_id": active_run_id,
        "last_action": text(report.get("last_action")),
        "summary_ref": str(launch_report_path) if launch_report_path is not None else None,
    }


def _candidate_path(value: object, *, text: TextReader) -> Path | None:
    text_value = text(value)
    if text_value is None:
        return None
    return Path(text_value).expanduser().resolve()


def _first_text(*values: object, text: TextReader) -> str | None:
    for value in values:
        text_value = text(value)
        if text_value is not None:
            return text_value
    return None


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None
