from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.controllers import (
    data_asset_gate,
    figure_loop_guard,
    medical_literature_audit,
    medical_publication_surface,
    medical_reporting_audit,
    publication_gate,
    runtime_supervision,
    runtime_watch_alerts,
    runtime_watch_recovery_policy,
    runtime_watch_outer_loop_dispatch,
    runtime_watch_work_units,
    study_outer_loop,
    study_runtime_family_orchestration as family_orchestration,
    study_runtime_router,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_escalation_record import RuntimeEscalationRecordRef
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol
from med_autoscience.controllers.runtime_watch_outer_loop_policy import outer_loop_request_requires_fresh_controller_execution
from med_autoscience.study_decision_record import (
    StudyDecisionCharterRef,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionRecord,
)


ControllerRunner = Callable[..., dict[str, Any]]

DEFAULT_CONTROLLER_ORDER: tuple[str, ...] = (
    "data_asset_gate",
    "medical_publication_surface",
    "publication_gate",
    "medical_literature_audit",
    "medical_reporting_audit",
    "figure_loop_guard",
)

_MANAGED_STUDY_AUTO_RECOVERY_SOURCE = "runtime_watch_auto_recovery"
_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE = "runtime_watch_controller_reroute"
_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE = "runtime_watch_outer_loop_wakeup"
_HARD_AUTO_RECOVERY_QUEST_STATUSES = frozenset({"active", "running", "waiting_for_user", "stopped"})
_HARD_AUTO_RECOVERY_REASONS = frozenset(
    {
        "quest_marked_running_but_no_live_session",
        "quest_parked_on_unchanged_finalize_state",
        "quest_waiting_on_invalid_blocking",
        "quest_completion_requested_before_publication_gate_clear",
        "quest_stopped_by_controller_guard",
    }
)
_RUNTIME_RECOVERY_DECISIONS = frozenset({"create_and_start", "resume", "relaunch_stopped"})

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_default_controller_runners() -> dict[str, ControllerRunner]:
    return {
        "data_asset_gate": data_asset_gate.run_controller,
        "medical_publication_surface": medical_publication_surface.run_controller,
        "publication_gate": publication_gate.run_controller,
        "medical_literature_audit": medical_literature_audit.run_controller,
        "medical_reporting_audit": medical_reporting_audit.run_controller,
        "figure_loop_guard": figure_loop_guard.run_controller,
    }


def iter_ordered_controller_runners(
    controller_runners: dict[str, ControllerRunner],
) -> list[tuple[str, ControllerRunner]]:
    priority = {name: index for index, name in enumerate(DEFAULT_CONTROLLER_ORDER)}
    ordered_known: list[tuple[int, tuple[str, ControllerRunner]]] = []
    ordered_unknown: list[tuple[str, ControllerRunner]] = []
    for name, runner in controller_runners.items():
        entry = (name, runner)
        if name in priority:
            ordered_known.append((priority[name], entry))
        else:
            ordered_unknown.append(entry)
    return [entry for _, entry in sorted(ordered_known, key=lambda item: item[0])] + ordered_unknown


def build_fingerprint(controller_name: str, result: dict[str, Any]) -> str:
    if controller_name == "publication_gate":
        payload = {
            "status": result.get("status"),
            "allow_write": result.get("allow_write"),
            "blockers": result.get("blockers") or [],
            "missing_non_scalar_deliverables": result.get("missing_non_scalar_deliverables") or [],
            "submission_minimal_present": result.get("submission_minimal_present"),
            "draft_handoff_delivery_required": result.get("draft_handoff_delivery_required"),
            "draft_handoff_delivery_status": result.get("draft_handoff_delivery_status"),
            "supervisor_phase": result.get("supervisor_phase"),
            "phase_owner": result.get("phase_owner"),
            "upstream_scientific_anchor_ready": result.get("upstream_scientific_anchor_ready"),
            "bundle_tasks_downstream_only": result.get("bundle_tasks_downstream_only"),
            "current_required_action": result.get("current_required_action"),
            "deferred_downstream_actions": result.get("deferred_downstream_actions") or [],
            "controller_stage_note": result.get("controller_stage_note"),
        }
    elif controller_name == "medical_publication_surface":
        top_hits = result.get("top_hits") or []
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "top_hits": [
                {
                    "path": item.get("path"),
                    "location": item.get("location"),
                    "phrase": item.get("phrase"),
                }
                for item in top_hits[:10]
            ],
        }
    elif controller_name == "data_asset_gate":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "advisories": result.get("advisories") or [],
            "study_id": result.get("study_id"),
            "outdated_dataset_ids": result.get("outdated_dataset_ids") or [],
            "unresolved_dataset_ids": result.get("unresolved_dataset_ids") or [],
            "public_support_dataset_ids": result.get("public_support_dataset_ids") or [],
        }
    elif controller_name == "figure_loop_guard":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "dominant_figure_id": result.get("dominant_figure_id"),
            "dominant_figure_mentions": result.get("dominant_figure_mentions"),
            "reference_count": result.get("reference_count"),
        }
    elif controller_name == "medical_literature_audit":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "action": result.get("action"),
            "missing_pmids": result.get("missing_pmids") or [],
        }
    elif controller_name == "medical_reporting_audit":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "action": result.get("action"),
        }
    else:
        payload = result
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _invoke_controller_runner(
    runner: ControllerRunner,
    *,
    quest_root: Path,
    apply: bool,
) -> dict[str, Any]:
    try:
        return runner(quest_root=quest_root, apply=apply)
    except FileNotFoundError as exc:
        return {
            "status": "awaiting_artifacts",
            "blockers": [],
            "advisories": [f"missing_artifact:{exc}"],
            "report_json": None,
            "report_markdown": None,
            "suppression_reason": "precondition_missing",
        }


def _serialize_managed_study_action(
    action_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any]:
    action = (
        action_payload
        if isinstance(action_payload, StudyRuntimeStatus)
        else StudyRuntimeStatus.from_payload(action_payload)
    )
    return {
        "study_id": action.study_id,
        "decision": action.decision.value if action.decision is not None else None,
        "reason": action.reason.value if action.reason is not None else None,
    }


def _managed_study_status_payload(
    action_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any]:
    if isinstance(action_payload, StudyRuntimeStatus):
        return action_payload.to_dict()
    return dict(action_payload)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _candidate_path(value: object) -> Path | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return Path(text).expanduser().resolve()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _write_json_object(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mapping_value(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _payload_active_run_id(payload: Mapping[str, Any]) -> str | None:
    continuation_state = _mapping_value(payload, "continuation_state")
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    autonomous_runtime_notice = _mapping_value(payload, "autonomous_runtime_notice")
    execution_owner_guard = _mapping_value(payload, "execution_owner_guard")
    for candidate in (
        payload.get("active_run_id"),
        continuation_state.get("active_run_id"),
        runtime_liveness_audit.get("active_run_id"),
        runtime_audit.get("active_run_id"),
        autonomous_runtime_notice.get("active_run_id"),
        execution_owner_guard.get("active_run_id"),
    ):
        active_run_id = _non_empty_text(candidate)
        if active_run_id is not None:
            return active_run_id
    return None


def _payload_runtime_liveness_status(payload: Mapping[str, Any]) -> str | None:
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    return _non_empty_text(runtime_liveness_audit.get("status")) or _non_empty_text(runtime_audit.get("status"))


def _payload_strict_live(payload: Mapping[str, Any]) -> bool:
    if _payload_runtime_liveness_status(payload) != "live":
        return False
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    if runtime_audit.get("worker_running") is not True:
        return False
    return _payload_active_run_id(payload) is not None


def _should_refresh_managed_study_status_after_ensure(payload: Mapping[str, Any]) -> bool:
    if _non_empty_text(payload.get("decision")) not in _RUNTIME_RECOVERY_DECISIONS:
        return False
    return not _payload_strict_live(payload)


def _refresh_managed_study_status_after_ensure(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    if not _should_refresh_managed_study_status_after_ensure(status_payload):
        return status_payload
    refreshed = study_runtime_router.study_runtime_status(
        profile=profile,
        study_root=study_root,
    )
    return _managed_study_status_payload(refreshed)


def _runtime_watch_wakeup_latest_path(study_root: Path) -> Path:
    return study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"


def _artifact_fingerprint(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False}
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return {
            "path": str(resolved),
            "exists": False,
        }
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "exists": True,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
    }


def _runtime_supervision_artifact_fingerprint(path: Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return {
            "path": str(resolved),
            "exists": False,
        }
    payload = _read_json_object(resolved) or {}
    stable_payload = {
        "study_id": _non_empty_text(payload.get("study_id")),
        "quest_id": _non_empty_text(payload.get("quest_id")),
        "health_status": _non_empty_text(payload.get("health_status")),
        "runtime_reason": _non_empty_text(payload.get("runtime_reason")),
        "next_action": _non_empty_text(payload.get("next_action")),
        "active_run_id": _non_empty_text(payload.get("active_run_id")),
        "needs_human_intervention": bool(payload.get("needs_human_intervention")),
        "supervisor_tick_status": _non_empty_text(payload.get("supervisor_tick_status")),
    }
    canonical = json.dumps(stable_payload, ensure_ascii=False, sort_keys=True)
    return {
        "path": str(resolved),
        "exists": True,
        "stable_payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "stable_payload": stable_payload,
    }


def _managed_outer_loop_wakeup_fingerprint(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    quest_root = _candidate_path(status_payload.get("quest_root"))
    watched_payload = {
        "status": {
            "study_id": _non_empty_text(status_payload.get("study_id")),
            "quest_id": _non_empty_text(status_payload.get("quest_id")),
            "quest_root": str(quest_root) if quest_root is not None else None,
            "quest_status": _non_empty_text(status_payload.get("quest_status")),
            "decision": _non_empty_text(status_payload.get("decision")),
            "reason": _non_empty_text(status_payload.get("reason")),
            "active_run_id": _payload_active_run_id(status_payload),
            "runtime_liveness_status": _payload_runtime_liveness_status(status_payload),
            "runtime_event_ref": dict(status_payload.get("runtime_event_ref") or {})
            if isinstance(status_payload.get("runtime_event_ref"), Mapping)
            else None,
            "runtime_escalation_ref": dict(status_payload.get("runtime_escalation_ref") or {})
            if isinstance(status_payload.get("runtime_escalation_ref"), Mapping)
            else None,
            "publication_supervisor_state": dict(status_payload.get("publication_supervisor_state") or {})
            if isinstance(status_payload.get("publication_supervisor_state"), Mapping)
            else None,
        },
        "artifacts": {
            "publication_eval_latest": _artifact_fingerprint(
                resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
            ),
            "evaluation_summary_latest": _artifact_fingerprint(
                resolved_study_root / "artifacts" / "evaluation_summary" / "latest.json"
            ),
            "controller_decision_latest": _artifact_fingerprint(
                resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
            ),
            "runtime_supervision_latest": _runtime_supervision_artifact_fingerprint(
                resolved_study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
            ),
            "publication_gate_latest": _artifact_fingerprint(
                (quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                if quest_root is not None
                else None
            ),
        },
    }
    canonical = json.dumps(watched_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest(), watched_payload


def _build_outer_loop_wakeup_audit(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any]:
    input_fingerprint, watched_payload = _managed_outer_loop_wakeup_fingerprint(
        study_root=study_root,
        status_payload=status_payload,
    )
    latest_path = _runtime_watch_wakeup_latest_path(Path(study_root).expanduser().resolve())
    previous = _read_json_object(latest_path) or {}
    previous_outcome = _non_empty_text(previous.get("outcome"))
    previous_fingerprint = _non_empty_text(previous.get("input_fingerprint"))
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "study_id": _non_empty_text(status_payload.get("study_id")) or Path(study_root).name,
        "quest_id": _non_empty_text(status_payload.get("quest_id")),
        "input_fingerprint": input_fingerprint,
        "previous_input_fingerprint": previous_fingerprint,
        "previous_outcome": previous_outcome,
        "dispatch_cause": "input_unchanged" if previous_fingerprint == input_fingerprint else "input_changed",
        "watched_inputs": watched_payload,
        "latest_path": str(latest_path),
    }


def _write_outer_loop_wakeup_audit(*, study_root: Path, audit: Mapping[str, Any]) -> None:
    _write_json_object(_runtime_watch_wakeup_latest_path(Path(study_root).expanduser().resolve()), audit)


def _should_hard_auto_recover_managed_study(action_payload: dict[str, Any] | StudyRuntimeStatus) -> bool:
    payload = _managed_study_status_payload(action_payload)
    decision = _non_empty_text(payload.get("decision"))
    if decision == "resume":
        if _non_empty_text(payload.get("quest_status")) not in _HARD_AUTO_RECOVERY_QUEST_STATUSES:
            return False
        if _non_empty_text(payload.get("reason")) not in _HARD_AUTO_RECOVERY_REASONS:
            return False
        if _payload_active_run_id(payload) is not None:
            return False
        return _payload_runtime_liveness_status(payload) != "live"
    return runtime_supervision.is_auto_continuation_recovery_pending(payload)


def _serialize_managed_study_auto_recovery(
    *,
    preflight_payload: dict[str, Any] | StudyRuntimeStatus,
    applied_payload: dict[str, Any] | StudyRuntimeStatus,
    source: str,
) -> dict[str, Any]:
    preflight = _serialize_managed_study_action(preflight_payload)
    applied = _serialize_managed_study_action(applied_payload)
    return {
        "study_id": applied.get("study_id") or preflight.get("study_id"),
        "preflight_decision": preflight.get("decision"),
        "preflight_reason": preflight.get("reason"),
        "applied_decision": applied.get("decision"),
        "applied_reason": applied.get("reason"),
        "source": source,
    }


def _controller_decision_latest_matches_outer_loop_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> bool:
    latest_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    payload = _read_json_object(latest_path)
    if payload is None:
        return False
    record = StudyDecisionRecord.from_payload(payload)
    desired_charter_ref = StudyDecisionCharterRef.from_payload(dict(tick_request.get("charter_ref") or {})).to_dict()
    desired_publication_eval_ref = StudyDecisionPublicationEvalRef.from_payload(
        dict(tick_request.get("publication_eval_ref") or {})
    ).to_dict()
    desired_controller_actions = tuple(
        StudyDecisionControllerAction.from_payload(action).to_dict()
        for action in (tick_request.get("controller_actions") or [])
        if isinstance(action, dict)
    )
    desired_runtime_escalation_payload = status_payload.get("runtime_escalation_ref")
    desired_runtime_escalation_ref = (
        RuntimeEscalationRecordRef.from_payload(dict(desired_runtime_escalation_payload)).to_dict()
        if isinstance(desired_runtime_escalation_payload, dict)
        else None
    )
    if record.decision_type.value != _non_empty_text(tick_request.get("decision_type")):
        return False
    if record.requires_human_confirmation is not bool(tick_request.get("requires_human_confirmation")):
        return False
    if record.reason != (_non_empty_text(tick_request.get("reason")) or ""):
        return False
    if record.charter_ref.to_dict() != desired_charter_ref:
        return False
    if record.publication_eval_ref.to_dict() != desired_publication_eval_ref:
        return False
    if tuple(action.to_dict() for action in record.controller_actions) != desired_controller_actions:
        return False
    if desired_runtime_escalation_ref is None:
        return True
    return record.runtime_escalation_ref.to_dict() == desired_runtime_escalation_ref

def _quest_report_requests_managed_study_reroute(report: Mapping[str, Any] | None) -> bool:
    if not isinstance(report, Mapping):
        return False
    controllers = report.get("controllers")
    if not isinstance(controllers, Mapping):
        return False
    figure_loop_guard_report = controllers.get("figure_loop_guard")
    if not isinstance(figure_loop_guard_report, Mapping):
        return False
    if _non_empty_text(figure_loop_guard_report.get("action")) != "applied":
        return False
    return bool(figure_loop_guard_report.get("quest_stop_applied"))


def _write_latest_watch_alias(*, report_dir: Path, report: Mapping[str, Any], markdown: str) -> tuple[Path, Path]:
    latest_json = report_dir / "latest.json"
    latest_markdown = report_dir / "latest.md"
    report_dir.mkdir(parents=True, exist_ok=True)
    latest_json.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest_markdown.write_text(markdown, encoding="utf-8")
    return latest_json, latest_markdown


def _watch_human_gates_for_quest_report(
    *,
    report: Mapping[str, Any],
    scanned_at: str,
) -> list[dict[str, Any]]:
    publication_gate_payload = report.get("controllers", {}).get("publication_gate")
    if not isinstance(publication_gate_payload, Mapping):
        return []
    if str(publication_gate_payload.get("current_required_action") or "").strip() != "human_confirmation_required":
        return []
    evidence_ref = str(publication_gate_payload.get("report_json") or "").strip()
    return [
        family_orchestration.build_family_human_gate(
            gate_id=f"watch-gate-{_stable_gate_id_seed(report)}",
            gate_kind="publication_gate_human_confirmation",
            requested_at=scanned_at,
            request_surface_kind="runtime_watch",
            request_surface_id="runtime_watch",
            evidence_refs=[
                {
                    "ref_kind": "repo_path",
                    "ref": evidence_ref,
                    "label": "publication_gate_report",
                }
            ]
            if evidence_ref
            else [],
            decision_options=["approve", "request_changes", "reject"],
        )
    ]


def _stable_gate_id_seed(report: Mapping[str, Any]) -> str:
    quest_root = str(report.get("quest_root") or "").strip()
    scanned_at = str(report.get("scanned_at") or "").strip()
    return family_orchestration.resolve_active_run_id(quest_root, scanned_at) or "runtime-watch"


def _attach_family_companion_to_quest_report(report: dict[str, Any], *, quest_root: Path) -> None:
    runtime_state = quest_state.load_runtime_state(quest_root)
    active_run_id = family_orchestration.resolve_active_run_id(runtime_state.get("active_run_id"))
    scanned_at = str(report.get("scanned_at") or "").strip() or utc_now()
    human_gates = _watch_human_gates_for_quest_report(report=report, scanned_at=scanned_at)
    controller_refs = []
    for name, payload in (report.get("controllers") or {}).items():
        if not isinstance(payload, Mapping):
            continue
        report_json = str(payload.get("report_json") or "").strip()
        if not report_json:
            continue
        controller_refs.append(
            {
                "ref_kind": "repo_path",
                "ref": report_json,
                "label": f"{name}_report",
            }
        )
    companion = family_orchestration.build_family_orchestration_companion(
        surface_kind="runtime_watch",
        surface_id="runtime_watch/latest.json",
        event_name="runtime_watch.quest_scanned",
        source_surface="runtime_watch",
        session_id=f"runtime-watch:{quest_root.name}",
        program_id=None,
        study_id=quest_root.name,
        quest_id=quest_root.name,
        active_run_id=active_run_id,
        runtime_decision=None,
        runtime_reason=None,
        payload={
            "quest_status": report.get("quest_status"),
            "controller_count": len(report.get("controllers") or {}),
        },
        event_time=scanned_at,
        checkpoint_id=f"runtime-watch-quest:{quest_root.name}:{report.get('quest_status')}",
        checkpoint_label="runtime watch quest scan",
        audit_refs=controller_refs,
        state_refs=[
            {
                "role": "audit",
                "ref_kind": "repo_path",
                "ref": str(quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"),
                "label": "runtime_watch_latest",
            }
        ],
        restoration_evidence=controller_refs,
        action_graph_id="mas_runtime_orchestration",
        node_id="runtime_watch_quest_scan",
        gate_id=(human_gates[0].get("gate_id") if human_gates else None),
        resume_mode="reenter_human_gate" if human_gates else "resume_from_checkpoint",
        resume_handle=f"runtime_watch:{quest_root.name}",
        human_gate_required=bool(human_gates),
        human_gates=human_gates,
    )
    report["family_event_envelope"] = companion["family_event_envelope"]
    report["family_checkpoint_lineage"] = companion["family_checkpoint_lineage"]
    report["family_human_gates"] = companion["family_human_gates"]


def _attach_family_companion_to_runtime_report(report: dict[str, Any], *, runtime_root: Path) -> None:
    scanned_at = str(report.get("scanned_at") or "").strip() or utc_now()
    human_gates: list[dict[str, Any]] = []
    for quest_report in report.get("reports") or []:
        if not isinstance(quest_report, Mapping):
            continue
        for gate in quest_report.get("family_human_gates") or []:
            if isinstance(gate, Mapping):
                human_gates.append(dict(gate))
    companion = family_orchestration.build_family_orchestration_companion(
        surface_kind="runtime_watch",
        surface_id="runtime_watch/runtime_tick",
        event_name="runtime_watch.runtime_scanned",
        source_surface="runtime_watch",
        session_id=f"runtime-watch:{runtime_root}",
        program_id=None,
        study_id=None,
        quest_id=None,
        active_run_id=None,
        runtime_decision=None,
        runtime_reason=None,
        payload={
            "scanned_quest_count": len(report.get("scanned_quests") or []),
            "managed_study_action_count": len(report.get("managed_study_actions") or []),
            "managed_study_auto_recovery_count": len(report.get("managed_study_auto_recoveries") or []),
        },
        event_time=scanned_at,
        checkpoint_id=f"runtime-watch-runtime:{runtime_root.name}:{len(report.get('scanned_quests') or [])}",
        checkpoint_label="runtime watch runtime scan",
        audit_refs=[
            {
                "ref_kind": "repo_path",
                "ref": str(item.get("latest_report_json") or item.get("report_json") or "").strip(),
                "label": "runtime_watch_quest_report",
            }
            for item in (report.get("reports") or [])
            if isinstance(item, Mapping) and str(item.get("latest_report_json") or item.get("report_json") or "").strip()
        ],
        state_refs=[
            {
                "role": "workspace",
                "ref_kind": "repo_path",
                "ref": str(runtime_root),
                "label": "runtime_root",
            }
        ],
        action_graph_id="mas_runtime_orchestration",
        node_id="runtime_watch_runtime_scan",
        gate_id=(human_gates[0].get("gate_id") if human_gates else None),
        resume_mode="reenter_human_gate" if human_gates else "resume_from_checkpoint",
        resume_handle=f"runtime_watch:{runtime_root}",
        human_gate_required=bool(human_gates),
        human_gates=human_gates,
    )
    report["family_event_envelope"] = companion["family_event_envelope"]
    report["family_checkpoint_lineage"] = companion["family_checkpoint_lineage"]
    report["family_human_gates"] = companion["family_human_gates"]


def render_watch_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Runtime Watch Report",
        "",
        f"- scanned_at: `{report['scanned_at']}`",
        f"- quest_root: `{report['quest_root']}`",
        f"- quest_status: `{report['quest_status']}`",
        "",
        "## Controllers",
        "",
    ]
    for name, item in (report.get("controllers") or {}).items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- status: `{item.get('status')}`",
                f"- action: `{item.get('action')}`",
                f"- blockers: `{', '.join(item.get('blockers') or ['none'])}`",
                f"- advisories: `{', '.join(item.get('advisories') or ['none'])}`",
                f"- report_json: `{item.get('report_json')}`",
                f"- report_markdown: `{item.get('report_markdown')}`",
                f"- suppression_reason: `{item.get('suppression_reason') or 'none'}`",
                "",
            ]
        )
        if name == "publication_gate" and item.get("supervisor_phase"):
            lines.extend(
                [
                    "#### Publication Supervisor",
                    "",
                    f"- supervisor_phase: `{item.get('supervisor_phase')}`",
                    f"- phase_owner: `{item.get('phase_owner')}`",
                    f"- upstream_scientific_anchor_ready: `{str(item.get('upstream_scientific_anchor_ready')).lower()}`",
                    f"- bundle_tasks_downstream_only: `{str(item.get('bundle_tasks_downstream_only')).lower()}`",
                    f"- current_required_action: `{item.get('current_required_action')}`",
                    f"- deferred_downstream_actions: `{', '.join(item.get('deferred_downstream_actions') or ['none'])}`",
                    f"- controller_stage_note: `{item.get('controller_stage_note')}`",
                    "",
                ]
            )
    outer_loop_dispatch = dict(report.get("managed_study_outer_loop_dispatch") or {})
    if outer_loop_dispatch:
        lines.extend(
            [
                "## Managed Study Outer-Loop Dispatch",
                "",
                f"- study_id: `{outer_loop_dispatch.get('study_id') or 'none'}`",
                f"- decision_type: `{outer_loop_dispatch.get('decision_type') or 'none'}`",
                f"- route_target: `{outer_loop_dispatch.get('route_target') or 'none'}`",
                f"- route_key_question: `{outer_loop_dispatch.get('route_key_question') or 'none'}`",
                f"- controller_action_type: `{outer_loop_dispatch.get('controller_action_type') or 'none'}`",
                f"- study_decision_ref: `{outer_loop_dispatch.get('study_decision_ref') or 'none'}`",
                f"- dispatch_status: `{outer_loop_dispatch.get('dispatch_status') or 'none'}`",
                f"- source: `{outer_loop_dispatch.get('source') or 'none'}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_watch_report(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    markdown = render_watch_markdown(report)
    json_path, md_path = runtime_watch_protocol.write_watch_report(
        quest_root=quest_root,
        report=report,
        markdown=markdown,
    )
    latest_json, latest_markdown = _write_latest_watch_alias(
        report_dir=json_path.parent,
        report=report,
        markdown=markdown,
    )
    return json_path, md_path, latest_json, latest_markdown


def _materialize_placeholder_quest_watch_report(status_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    quest_root = _candidate_path(status_payload.get("quest_root"))
    if quest_root is None:
        return None
    report = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "quest_root": str(quest_root),
        "quest_status": _non_empty_text(status_payload.get("quest_status")) or quest_state.quest_status(quest_root),
        "controllers": {},
    }
    _attach_family_companion_to_quest_report(report, quest_root=quest_root)
    json_path, md_path, latest_json, latest_markdown = write_watch_report(quest_root, report)
    report["report_json"] = str(json_path)
    report["report_markdown"] = str(md_path)
    report["latest_report_json"] = str(latest_json)
    report["latest_report_markdown"] = str(latest_markdown)
    return report


def run_watch_for_quest(
    *,
    quest_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
) -> dict[str, Any]:
    controller_runners = controller_runners or build_default_controller_runners()
    current_state = runtime_watch_protocol.load_watch_state(quest_root)
    controller_state = dict(current_state.controllers)
    report: dict[str, Any] = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "quest_root": str(quest_root),
        "quest_status": quest_state.quest_status(quest_root),
        "controllers": {},
    }

    for name, runner in iter_ordered_controller_runners(controller_runners):
        dry_run_result = _invoke_controller_runner(runner, quest_root=quest_root, apply=False)
        fingerprint = build_fingerprint(name, dry_run_result)
        previous = controller_state.get(name) or runtime_watch_protocol.RuntimeWatchControllerState()
        intervention_statuses = {"blocked"}
        if name == "data_asset_gate":
            intervention_statuses.add("advisory")
        if (
            name == "publication_gate"
            and dry_run_result.get("draft_handoff_delivery_required") is True
            and str(dry_run_result.get("draft_handoff_delivery_status") or "").strip() in {"missing", "stale", "invalid"}
            and str(dry_run_result.get("status") or "").strip()
        ):
            intervention_statuses.add(str(dry_run_result.get("status") or "").strip())
        plan = runtime_watch_protocol.plan_controller_intervention(
            previous_controller_state=previous,
            dry_run_result=dry_run_result,
            fingerprint=fingerprint,
            apply=apply,
            scanned_at=report["scanned_at"],
            intervention_statuses=intervention_statuses,
        )
        final_result = dry_run_result
        if plan.should_apply:
            final_result = _invoke_controller_runner(runner, quest_root=quest_root, apply=True)
            final_fingerprint = build_fingerprint(name, final_result)
            controller_state[name] = runtime_watch_protocol.RuntimeWatchControllerState(
                last_seen_fingerprint=final_fingerprint,
                last_applied_fingerprint=final_fingerprint,
                last_applied_at=report["scanned_at"],
                last_status=str(final_result.get("status") or "").strip() or None,
                last_suppression_reason=None,
            )
        else:
            controller_state[name] = plan.controller_state
        report_result = final_result if plan.should_apply else dry_run_result
        status = report_result.get("status")
        suppression_reason = plan.suppression_reason
        report["controllers"][name] = {
            "status": status,
            "action": plan.action.value,
            "blockers": report_result.get("blockers") or [],
            "advisories": report_result.get("advisories") or [],
            "report_json": final_result.get("report_json"),
            "report_markdown": final_result.get("report_markdown"),
            "suppression_reason": suppression_reason,
        }
        if name == "publication_gate":
            report["controllers"][name].update(
                {
                    "supervisor_phase": report_result.get("supervisor_phase"),
                    "phase_owner": report_result.get("phase_owner"),
                    "upstream_scientific_anchor_ready": report_result.get("upstream_scientific_anchor_ready"),
                    "bundle_tasks_downstream_only": report_result.get("bundle_tasks_downstream_only"),
                    "current_required_action": report_result.get("current_required_action"),
                    "deferred_downstream_actions": report_result.get("deferred_downstream_actions") or [],
                    "controller_stage_note": report_result.get("controller_stage_note"),
                    "draft_handoff_delivery_required": report_result.get("draft_handoff_delivery_required"),
                    "draft_handoff_delivery_status": report_result.get("draft_handoff_delivery_status"),
                }
            )
        if name == "figure_loop_guard":
            report["controllers"][name].update(
                {
                    "quest_stop_applied": bool(report_result.get("quest_stop_applied")),
                    "quest_stop_status": report_result.get("quest_stop_status"),
                    "quest_stop_deferred": bool(report_result.get("quest_stop_deferred")),
                    "quest_stop_defer_reason": report_result.get("quest_stop_defer_reason"),
                }
            )

    _attach_family_companion_to_quest_report(report, quest_root=quest_root)
    runtime_watch_protocol.save_watch_state(
        quest_root=quest_root,
        payload=runtime_watch_protocol.RuntimeWatchState(
            schema_version=1,
            updated_at=report["scanned_at"],
            controllers=controller_state,
        ),
    )
    json_path, md_path, latest_json, latest_markdown = write_watch_report(quest_root, report)
    report["report_json"] = str(json_path)
    report["report_markdown"] = str(md_path)
    report["latest_report_json"] = str(latest_json)
    report["latest_report_markdown"] = str(latest_markdown)
    return report


def run_watch_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    profile: WorkspaceProfile | None = None,
    ensure_study_runtimes: bool = False,
) -> dict[str, Any]:
    controller_runners = controller_runners or build_default_controller_runners()
    managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
    managed_study_auto_recoveries: list[dict[str, Any]] = []
    managed_study_recovery_holds: list[dict[str, Any]] = []
    managed_study_outer_loop_dispatches: list[dict[str, Any]] = []
    managed_study_outer_loop_wakeup_audits: list[dict[str, Any]] = []
    managed_study_alert_deliveries: list[dict[str, Any]] = []
    if ensure_study_runtimes:
        if profile is None:
            raise ValueError("profile is required when ensure_study_runtimes is enabled")
        for study_root in sorted(profile.studies_root.iterdir()):
            if not study_root.is_dir():
                continue
            if not (study_root / "study.yaml").exists():
                continue
            if apply:
                action_payload = study_runtime_router.ensure_study_runtime(
                    profile=profile,
                    study_root=study_root,
                    source="runtime_watch",
                )
            else:
                action_payload = study_runtime_router.study_runtime_status(
                    profile=profile,
                    study_root=study_root,
                )
                if _should_hard_auto_recover_managed_study(action_payload):
                    preflight_payload = action_payload
                    recovery_hold = runtime_watch_recovery_policy.hold_for_flapping_circuit_breaker(
                        study_root=study_root,
                        status_payload=preflight_payload,
                    )
                    if recovery_hold is not None:
                        runtime_watch_recovery_policy.write_recovery_probe(
                            study_root=study_root,
                            recovery_hold=recovery_hold,
                        )
                        managed_study_recovery_holds.append(recovery_hold)
                    else:
                        action_payload = study_runtime_router.ensure_study_runtime(
                            profile=profile,
                            study_root=study_root,
                            source=_MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
                        )
                        managed_study_auto_recoveries.append(
                            _serialize_managed_study_auto_recovery(
                                preflight_payload=preflight_payload,
                                applied_payload=action_payload,
                                source=_MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
                            )
                        )
            managed_study_statuses.append((study_root, _managed_study_status_payload(action_payload)))
    scanned: list[str] = []
    reports: list[dict[str, Any]] = []
    for quest_root in quest_state.iter_active_quests(runtime_root):
        scanned.append(quest_root.name)
        reports.append(
            run_watch_for_quest(
                quest_root=quest_root,
                controller_runners=controller_runners,
                apply=apply,
            )
        )
    report_by_quest_root = {
        str(Path(str(report.get("quest_root") or "")).expanduser().resolve()): report
        for report in reports
        if str(report.get("quest_root") or "").strip()
    }
    if apply and ensure_study_runtimes and profile is not None:
        rerouted_managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
        for study_root, status_payload in managed_study_statuses:
            resolved_status_payload = status_payload
            quest_root = status_payload.get("quest_root")
            quest_report = report_by_quest_root.get(str(Path(str(quest_root)).expanduser().resolve())) if quest_root else None
            if _quest_report_requests_managed_study_reroute(quest_report):
                rerouted_payload = study_runtime_router.ensure_study_runtime(
                    profile=profile,
                    study_root=study_root,
                    source=_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE,
                )
                managed_study_auto_recoveries.append(
                    _serialize_managed_study_auto_recovery(
                        preflight_payload=status_payload,
                        applied_payload=rerouted_payload,
                        source=_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE,
                    )
                )
                resolved_status_payload = _managed_study_status_payload(rerouted_payload)
            rerouted_managed_study_statuses.append((study_root, resolved_status_payload))
        managed_study_statuses = rerouted_managed_study_statuses
    managed_study_supervision: list[dict[str, Any]] = []
    for study_root, status_payload in managed_study_statuses:
        if profile is not None:
            status_payload = _refresh_managed_study_status_after_ensure(
                profile=profile,
                study_root=study_root,
                status_payload=status_payload,
            )
        quest_root = _candidate_path(status_payload.get("quest_root"))
        quest_report = report_by_quest_root.get(str(quest_root)) if quest_root is not None else None
        if apply and profile is not None:
            wakeup_audit = _build_outer_loop_wakeup_audit(
                study_root=study_root,
                status_payload=status_payload,
            )
            if runtime_watch_work_units.outer_loop_wakeup_inputs_unchanged(wakeup_audit):
                wakeup_audit = {
                    **wakeup_audit,
                    "outcome": "skipped_unchanged_inputs",
                    "reason": "outer-loop wakeup inputs match a prior terminal no-op state",
                }
                _write_outer_loop_wakeup_audit(study_root=study_root, audit=wakeup_audit)
                managed_study_outer_loop_wakeup_audits.append(wakeup_audit)
            else:
                tick_request = study_outer_loop.build_runtime_watch_outer_loop_tick_request(
                    study_root=study_root,
                    status_payload=status_payload,
                )
                if tick_request is None:
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "no_request",
                        "reason": "outer-loop wakeup did not produce an autonomous request",
                    }
                elif (
                    work_unit_duplicate := runtime_watch_work_units.dispatch_already_executed(
                        study_root=study_root,
                        tick_request=tick_request,
                    )
                )[0]:
                    work_unit_context = runtime_watch_work_units.context_payload(
                        tick_request,
                        work_unit_dispatch_key=work_unit_duplicate[1],
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "skipped_matching_work_unit",
                        "reason": "outer-loop work unit already dispatched for the same blocker fingerprint",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_decision_blocker_authority",
                        **work_unit_context,
                    }
                    runtime_watch_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="skipped_duplicate",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif _controller_decision_latest_matches_outer_loop_request(
                    study_root=study_root,
                    status_payload=status_payload,
                    tick_request=tick_request,
                ) and not outer_loop_request_requires_fresh_controller_execution(tick_request):
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "skipped_matching_decision",
                        "reason": "controller_decisions/latest.json already matches the wakeup request",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_decision",
                    }
                else:
                    work_unit_dispatch_key = runtime_watch_work_units.dispatch_key(tick_request)
                    outer_loop_result = study_runtime_router.study_outer_loop_tick(
                        profile=profile,
                        source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
                        **runtime_watch_work_units.strip_context(tick_request),
                    )
                    if _non_empty_text(outer_loop_result.get("dispatch_status")) != "executed":
                        raise ValueError("runtime watch outer-loop wakeup requires executed autonomous dispatch")
                    dispatch_payload = runtime_watch_outer_loop_dispatch.serialize_outer_loop_dispatch(
                        tick_request=tick_request,
                        outer_loop_result=outer_loop_result,
                    )
                    managed_study_outer_loop_dispatches.append(dispatch_payload)
                    if quest_report is None:
                        quest_report = _materialize_placeholder_quest_watch_report(status_payload)
                        if isinstance(quest_report, dict):
                            reports.append(quest_report)
                            quest_root = _candidate_path(status_payload.get("quest_root"))
                            if quest_root is not None:
                                report_by_quest_root[str(quest_root)] = quest_report
                    if isinstance(quest_report, dict):
                        runtime_watch_outer_loop_dispatch.attach_to_quest_report(
                            quest_report=quest_report,
                            dispatch_payload=dispatch_payload,
                            write_latest_watch_alias=_write_latest_watch_alias,
                            render_watch_markdown=render_watch_markdown,
                        )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "dispatched",
                        "reason": "outer-loop wakeup dispatched an autonomous controller decision",
                        "dispatch": dispatch_payload,
                        **runtime_watch_work_units.context_payload(
                            tick_request,
                            work_unit_dispatch_key=work_unit_dispatch_key,
                        ),
                    }
                    runtime_watch_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="dispatched",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                    status_payload = _managed_study_status_payload(
                        study_runtime_router.study_runtime_status(
                            profile=profile,
                            study_root=study_root,
                        )
                    )
                _write_outer_loop_wakeup_audit(study_root=study_root, audit=wakeup_audit)
                managed_study_outer_loop_wakeup_audits.append(wakeup_audit)
        quest_root = _candidate_path(status_payload.get("quest_root"))
        quest_report = report_by_quest_root.get(str(quest_root)) if quest_root is not None else None
        supervision_report = runtime_supervision.materialize_runtime_supervision(
            study_root=study_root,
            status_payload=status_payload,
            recorded_at=utc_now(),
            apply=apply,
            runtime_watch_report_path=(
                Path(str(quest_report.get("latest_report_json") or quest_report.get("report_json")))
                if isinstance(quest_report, dict)
                and str(quest_report.get("latest_report_json") or quest_report.get("report_json") or "").strip()
                else None
            ),
        )
        if supervision_report is not None:
            managed_study_supervision.append(supervision_report)
            alert_delivery = runtime_watch_alerts.deliver_runtime_alert(
                profile=profile,
                study_root=study_root,
                status_payload=status_payload,
                supervision_report=supervision_report,
                apply=apply,
            )
            if alert_delivery is not None:
                managed_study_alert_deliveries.append(alert_delivery)
    managed_study_actions = [
        _serialize_managed_study_action(status_payload)
        for _, status_payload in managed_study_statuses
    ]
    runtime_report = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "runtime_root": str(runtime_root),
        "scanned_quests": scanned,
        "managed_study_actions": managed_study_actions,
        "managed_study_auto_recoveries": managed_study_auto_recoveries,
        "managed_study_recovery_holds": managed_study_recovery_holds,
        "managed_study_outer_loop_dispatches": managed_study_outer_loop_dispatches,
        "managed_study_outer_loop_wakeup_audits": managed_study_outer_loop_wakeup_audits,
        "managed_study_supervision": managed_study_supervision,
        "managed_study_alert_deliveries": managed_study_alert_deliveries,
        "reports": reports,
    }
    _attach_family_companion_to_runtime_report(runtime_report, runtime_root=Path(runtime_root).expanduser().resolve())
    return runtime_report


def run_watch_loop(
    *,
    runtime_root: Path,
    apply: bool,
    profile: WorkspaceProfile | None = None,
    ensure_study_runtimes: bool = False,
    interval_seconds: int = 300,
    max_ticks: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if max_ticks is not None and max_ticks <= 0:
        raise ValueError("max_ticks must be positive when provided")

    tick_count = 0
    last_result: dict[str, Any] | None = None
    tick_errors: list[dict[str, Any]] = []
    started_at = utc_now()

    while True:
        tick_count += 1
        try:
            last_result = run_watch_for_runtime(
                runtime_root=resolved_runtime_root,
                controller_runners=None,
                apply=apply,
                profile=profile,
                ensure_study_runtimes=ensure_study_runtimes,
            )
        except Exception as exc:
            tick_errors.append(
                {
                    "tick": tick_count,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
        if max_ticks is not None and tick_count >= max_ticks:
            break
        sleep_fn(float(interval_seconds))

    return {
        "schema_version": 1,
        "mode": "loop",
        "started_at": started_at,
        "completed_at": utc_now(),
        "runtime_root": str(resolved_runtime_root),
        "apply": apply,
        "ensure_study_runtimes": ensure_study_runtimes,
        "interval_seconds": interval_seconds,
        "tick_count": tick_count,
        "tick_errors": tick_errors,
        "last_result": last_result,
    }


def run_managed_supervisor_tick(
    *,
    profile: WorkspaceProfile,
    apply: bool,
) -> dict[str, Any]:
    return run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        apply=apply,
        profile=profile,
        ensure_study_runtimes=True,
    )


def run_managed_supervisor_loop(
    *,
    profile: WorkspaceProfile,
    apply: bool,
    interval_seconds: int = 300,
    max_ticks: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    return run_watch_loop(
        runtime_root=profile.runtime_root,
        apply=apply,
        profile=profile,
        ensure_study_runtimes=True,
        interval_seconds=interval_seconds,
        max_ticks=max_ticks,
        sleep_fn=sleep_fn,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--max-ticks", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.quest_root) == bool(args.runtime_root):
        raise SystemExit("Specify exactly one of --quest-root or --runtime-root")
    if args.loop and args.quest_root:
        raise SystemExit("--loop is only supported with --runtime-root")
    if args.quest_root:
        result = run_watch_for_quest(quest_root=args.quest_root, apply=args.apply)
    elif args.loop:
        result = run_watch_loop(
            runtime_root=args.runtime_root,
            apply=args.apply,
            interval_seconds=args.interval_seconds,
            max_ticks=args.max_ticks,
        )
    else:
        result = run_watch_for_runtime(runtime_root=args.runtime_root, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
