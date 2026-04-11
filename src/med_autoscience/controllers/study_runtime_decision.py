from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
import json
from pathlib import Path

from med_autoscience.controllers import (
    publication_gate as publication_gate_controller,
    study_runtime_interaction_arbitration as interaction_arbitration_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    startup_data_readiness as startup_data_readiness_controller,
    startup_boundary_gate as startup_boundary_gate_controller,
)
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeAuditRecord,
    StudyRuntimeAuditStatus,
    StudyRuntimeContinuationState,
    StudyRuntimeDecision,
    StudyRuntimeExecutionOwnerGuard,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeSummaryAlignment,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
    _RESUMABLE_QUEST_STATUSES,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import materialize_publication_eval_latest
from med_autoscience.publication_eval_record import (
    PublicationEvalCharterContextRef,
    PublicationEvalGap,
    PublicationEvalRecommendedAction,
    PublicationEvalRecord,
    PublicationEvalVerdict,
)
from med_autoscience.runtime_protocol import paper_artifacts
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.controllers.study_runtime_transport import _get_quest_session
from med_autoscience.study_charter import read_study_charter
from med_autoscience.study_completion import StudyCompletionStateStatus


_SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_KEYS = paper_artifacts.SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_KEYS

_SUPERVISOR_ONLY_ALLOWED_ACTIONS = (
    "read_runtime_status",
    "notify_user_runtime_is_live",
    "open_monitoring_entry",
    "pause_runtime",
    "resume_runtime",
    "stop_runtime",
    "record_user_decision",
)
_SUPERVISOR_ONLY_FORBIDDEN_ACTIONS = (
    "direct_study_execution",
    "direct_runtime_owned_write",
    "direct_paper_line_write",
    "direct_bundle_build",
    "direct_compiled_bundle_proofing",
)
_FINALIZE_PARKING_CONTINUATION_POLICY = "wait_for_user_or_resume"
_FINALIZE_PARKING_CONTINUATION_REASON = "unchanged_finalize_state"
_HUMAN_CONFIRMATION_REQUIRED_ACTION = "human_confirmation_required"
_SUPERVISOR_TICK_EXPECTED_INTERVAL_SECONDS = 5 * 60
_SUPERVISOR_TICK_STALE_AFTER_SECONDS = 2 * _SUPERVISOR_TICK_EXPECTED_INTERVAL_SECONDS


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _supervisor_tick_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _normalize_timestamp(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_json_mapping(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def _supervisor_tick_required(status: StudyRuntimeStatus) -> bool:
    execution = status.execution
    return (
        str(execution.get("engine") or "").strip() == "med-deepscientist"
        and str(execution.get("auto_entry") or "").strip() == "on_managed_research_intent"
        and status.quest_exists
    )


def _record_supervisor_tick_audit(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
) -> None:
    latest_report_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    required = _supervisor_tick_required(status)
    payload: dict[str, object] = {
        "required": required,
        "expected_interval_seconds": _SUPERVISOR_TICK_EXPECTED_INTERVAL_SECONDS,
        "stale_after_seconds": _SUPERVISOR_TICK_STALE_AFTER_SECONDS,
        "latest_report_path": str(latest_report_path),
    }
    if not required:
        payload.update(
            {
                "status": "not_required",
                "reason": "supervisor_tick_not_required",
                "summary": "当前 study 还不要求周期 supervisor tick 监管。",
                "next_action_summary": "继续按需读取研究状态即可。",
            }
        )
        status.record_supervisor_tick_audit(payload)
        return

    latest_report = _read_json_mapping(latest_report_path)
    if latest_report is None:
        payload.update(
            {
                "status": "missing",
                "reason": "supervisor_tick_report_missing",
                "summary": "MedAutoScience 外环监管心跳缺失，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要恢复或补齐 MedAutoScience supervisor tick / heartbeat 调度，再继续托管监管与自动恢复。",
                "latest_recorded_at": None,
                "seconds_since_latest_recorded_at": None,
                "last_known_health_status": None,
            }
        )
        status.record_supervisor_tick_audit(payload)
        return

    payload["last_known_health_status"] = str(latest_report.get("health_status") or "").strip() or None
    recorded_at = _normalize_timestamp(latest_report.get("recorded_at"))
    if recorded_at is None:
        payload.update(
            {
                "status": "invalid",
                "reason": "supervisor_tick_report_timestamp_invalid",
                "summary": "MedAutoScience 最近一次监管记录缺少可解析时间戳，当前不能确认监管心跳是否仍然新鲜。",
                "next_action_summary": "需要刷新 supervisor tick durable surface，然后重新确认托管监管状态。",
                "latest_recorded_at": str(latest_report.get("recorded_at") or "").strip() or None,
                "seconds_since_latest_recorded_at": None,
            }
        )
        status.record_supervisor_tick_audit(payload)
        return

    now = _supervisor_tick_now()
    age_seconds = max(0, int((now - recorded_at).total_seconds()))
    payload["latest_recorded_at"] = recorded_at.isoformat()
    payload["seconds_since_latest_recorded_at"] = age_seconds
    if age_seconds > _SUPERVISOR_TICK_STALE_AFTER_SECONDS:
        payload.update(
            {
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
                "summary": "MedAutoScience 外环监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要先恢复 MedAutoScience supervisor tick / heartbeat 调度，再继续托管监管与自动恢复。",
            }
        )
        status.record_supervisor_tick_audit(payload)
        return

    payload.update(
        {
            "status": "fresh",
            "reason": "supervisor_tick_report_fresh",
            "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
            "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
        }
    )
    status.record_supervisor_tick_audit(payload)


def _normalize_submission_blocking_item_ids(payload: dict[str, object]) -> tuple[str, ...]:
    return paper_artifacts.normalize_submission_checklist_blocking_item_keys(payload)


def _waiting_submission_metadata_only(quest_root: Path) -> bool:
    paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(quest_root)
    if paper_bundle_manifest_path is None:
        return False
    checklist_path = paper_bundle_manifest_path.parent / "review" / "submission_checklist.json"
    if not checklist_path.exists():
        return False
    try:
        payload = json.loads(checklist_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    blocking_item_ids = _normalize_submission_blocking_item_ids(payload)
    if not blocking_item_ids:
        return False
    return all(item_id in _SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_KEYS for item_id in blocking_item_ids)


def _publication_eval_evidence_refs(*values: object) -> tuple[str, ...]:
    refs: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            refs.append(text)
    return tuple(refs)


def _publication_eval_gap_type(blocker: str) -> str:
    normalized = blocker.lower()
    if normalized in {
        "medical_publication_surface_blocked",
        "missing_current_medical_publication_surface_report",
    }:
        return "reporting"
    if any(token in normalized for token in ("submission", "deliverable", "bundle", "surface", "package")):
        return "delivery"
    if any(token in normalized for token in ("terminology", "report", "qc")):
        return "reporting"
    if any(token in normalized for token in ("anchor", "main", "result", "publishability")):
        return "evidence"
    return "claim"


def _publication_eval_verdict(report: dict[str, object]) -> PublicationEvalVerdict:
    status = str(report.get("status") or "").strip()
    anchor_kind = str(report.get("anchor_kind") or "").strip()
    summary = (
        str(report.get("controller_stage_note") or "").strip()
        or str(report.get("conclusion") or "").strip()
        or str(report.get("results_summary") or "").strip()
    )
    if status == "clear":
        return PublicationEvalVerdict(
            overall_verdict="promising",
            primary_claim_status="supported",
            summary=summary or "Publication gate is clear and the current line can continue.",
            stop_loss_pressure="none",
        )
    return PublicationEvalVerdict(
        overall_verdict="blocked",
        primary_claim_status="blocked" if anchor_kind == "missing" else "partial",
        summary=summary or "Publication gate is blocked and requires controller review.",
        stop_loss_pressure="high" if anchor_kind == "missing" else "watch",
    )


def _publication_eval_gaps(
    *,
    report: dict[str, object],
    evidence_refs: tuple[str, ...],
) -> tuple[PublicationEvalGap, ...]:
    blockers = report.get("blockers")
    if isinstance(blockers, list) and blockers:
        return tuple(
            PublicationEvalGap(
                gap_id=f"gap-{index:03d}",
                gap_type=_publication_eval_gap_type(str(blocker)),
                severity="must_fix",
                summary=str(blocker).strip(),
                evidence_refs=evidence_refs,
            )
            for index, blocker in enumerate(blockers, start=1)
            if str(blocker).strip()
        )
    return (
        PublicationEvalGap(
            gap_id="gap-001",
            gap_type="reporting",
            severity="optional",
            summary=(
                str(report.get("controller_stage_note") or "").strip()
                or str(report.get("conclusion") or "").strip()
                or "No blocking publication gate gap is active."
            ),
            evidence_refs=evidence_refs,
        ),
    )


def _publication_eval_action(
    *,
    report: dict[str, object],
    generated_at: str,
    evidence_refs: tuple[str, ...],
) -> PublicationEvalRecommendedAction:
    status = str(report.get("status") or "").strip()
    anchor_kind = str(report.get("anchor_kind") or "").strip()
    if status == "clear":
        action_type = "prepare_promotion_review" if anchor_kind == "paper_bundle" else "continue_same_line"
        reason = (
            str(report.get("controller_stage_note") or "").strip()
            or "Publication gate is clear and the current line can continue."
        )
    else:
        action_type = "return_to_controller"
        reason = (
            str(report.get("controller_stage_note") or "").strip()
            or "Publication gate is blocked and requires controller review."
        )
    return PublicationEvalRecommendedAction(
        action_id=f"publication-eval-action::{action_type}::{generated_at}",
        action_type=action_type,
        priority="now",
        reason=reason,
        evidence_refs=evidence_refs,
        requires_controller_decision=True,
    )


def _materialize_publication_eval_from_gate_report(
    *,
    study_root: Path,
    study_id: str,
    quest_root: Path,
    quest_id: str | None,
    publication_gate_report: dict[str, object],
) -> dict[str, str] | None:
    if str(publication_gate_report.get("gate_kind") or "").strip() != "publishability_control":
        return None
    stable_charter_path = (study_root / "artifacts" / "controller" / "study_charter.json").resolve()
    if not stable_charter_path.exists():
        return None
    generated_at = str(publication_gate_report.get("generated_at") or "").strip()
    if not generated_at:
        raise ValueError("publication gate report missing generated_at for publication eval materialization")
    charter_payload = read_study_charter(study_root=study_root)
    resolved_quest_id = (
        str(publication_gate_report.get("quest_id") or "").strip()
        or str(quest_id or "").strip()
        or quest_root.name
    )
    latest_gate_path = (
        str(publication_gate_report.get("latest_gate_path") or "").strip()
        or str((quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json").resolve())
    )
    main_result_ref = (
        str(publication_gate_report.get("main_result_path") or "").strip()
        or str((quest_root / "artifacts" / "results" / "main_result.json").resolve())
    )
    paper_root_ref = (
        str(publication_gate_report.get("paper_root") or "").strip()
        or str((study_root / "paper").resolve())
    )
    submission_minimal_ref = (
        str(publication_gate_report.get("submission_minimal_manifest_path") or "").strip()
        or str((Path(paper_root_ref).resolve() / "submission_minimal" / "submission_manifest.json"))
    )
    runtime_escalation_ref = str(
        (quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json").resolve()
    )
    evidence_refs = _publication_eval_evidence_refs(
        latest_gate_path,
        main_result_ref,
        paper_root_ref,
        str(quest_root.resolve()),
    )
    record = PublicationEvalRecord(
        schema_version=1,
        eval_id=f"publication-eval::{study_id}::{resolved_quest_id}::{generated_at}",
        study_id=study_id,
        quest_id=resolved_quest_id,
        emitted_at=generated_at,
        evaluation_scope="publication",
        charter_context_ref=PublicationEvalCharterContextRef(
            ref=str(stable_charter_path),
            charter_id=str(charter_payload.get("charter_id") or "").strip(),
            publication_objective=str(charter_payload.get("publication_objective") or "").strip(),
        ),
        runtime_context_refs={
            "runtime_escalation_ref": runtime_escalation_ref,
            "main_result_ref": main_result_ref,
        },
        delivery_context_refs={
            "paper_root_ref": paper_root_ref,
            "submission_minimal_ref": submission_minimal_ref,
        },
        verdict=_publication_eval_verdict(publication_gate_report),
        gaps=_publication_eval_gaps(report=publication_gate_report, evidence_refs=evidence_refs),
        recommended_actions=(
            _publication_eval_action(
                report=publication_gate_report,
                generated_at=generated_at,
                evidence_refs=evidence_refs,
            ),
        ),
    )
    return materialize_publication_eval_latest(study_root=study_root, record=record)


def _record_quest_runtime_audits(
    *,
    status: StudyRuntimeStatus,
    quest_runtime: quest_state.QuestRuntimeSnapshot,
) -> quest_state.QuestRuntimeLivenessStatus:
    runtime_liveness_audit = StudyRuntimeAuditRecord.from_payload(dict(quest_runtime.runtime_liveness_audit or {}))
    bash_session_audit = StudyRuntimeAuditRecord.from_payload(dict(quest_runtime.bash_session_audit or {}))
    status.record_runtime_liveness_audit(runtime_liveness_audit)
    status.record_bash_session_audit(bash_session_audit)
    return quest_runtime.runtime_liveness_status


def _publication_gate_allows_direct_write(status: StudyRuntimeStatus) -> bool:
    try:
        return not status.publication_supervisor_state.bundle_tasks_downstream_only
    except KeyError:
        return True


def _runtime_owned_roots(quest_root: Path) -> tuple[str, ...]:
    return (
        str(quest_root),
        str(quest_root / ".ds"),
        str(quest_root / "paper"),
        str(quest_root / "release"),
        str(quest_root / "artifacts"),
    )


def _record_execution_owner_guard(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
) -> None:
    execution = status.execution
    if str(execution.get("engine") or "").strip() != "med-deepscientist":
        return
    if str(execution.get("auto_entry") or "").strip() != "on_managed_research_intent":
        return
    if not status.quest_exists or status.quest_status not in _LIVE_QUEST_STATUSES:
        return
    try:
        runtime_liveness = status.runtime_liveness_audit_record
    except KeyError:
        return
    if runtime_liveness.status is StudyRuntimeAuditStatus.NONE:
        return
    try:
        active_run_id = status.autonomous_runtime_notice.active_run_id
    except KeyError:
        active_run_id = str(runtime_liveness.payload.get("active_run_id") or "").strip() or None
    publication_gate_allows_direct_write = _publication_gate_allows_direct_write(status)
    guard_reason = "live_managed_runtime"
    current_required_action = "supervise_managed_runtime"
    controller_stage_note = (
        "live managed runtime owns study-local execution; the foreground agent must stay supervisor-only "
        "until explicit takeover"
    )
    if runtime_liveness.status is not StudyRuntimeAuditStatus.LIVE:
        guard_reason = "managed_runtime_audit_unhealthy"
        current_required_action = "inspect_runtime_health_and_decide_intervention"
        controller_stage_note = (
            "managed runtime still owns study-local execution, but the liveness audit is unhealthy; "
            "stay supervisor-only until the runtime is inspected and explicitly paused or resumed"
        )
    payload = {
        "owner": "managed_runtime",
        "supervisor_only": True,
        "guard_reason": guard_reason,
        "active_run_id": active_run_id,
        "current_required_action": current_required_action,
        "allowed_actions": list(_SUPERVISOR_ONLY_ALLOWED_ACTIONS),
        "forbidden_actions": list(_SUPERVISOR_ONLY_FORBIDDEN_ACTIONS),
        "runtime_owned_roots": list(_runtime_owned_roots(quest_root)),
        "takeover_required": True,
        "takeover_action": "pause_runtime_then_explicit_human_takeover",
        "publication_gate_allows_direct_write": publication_gate_allows_direct_write,
        "controller_stage_note": controller_stage_note,
    }
    status.record_execution_owner_guard(StudyRuntimeExecutionOwnerGuard.from_payload(payload))


def _load_json_dict(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _runtime_state_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"


def _continuation_state_payload(*, quest_root: Path, quest_status: StudyRuntimeQuestStatus | None) -> dict[str, object] | None:
    runtime_state_path = _runtime_state_path(quest_root)
    runtime_state = _load_json_dict(runtime_state_path)
    continuation_policy = str(runtime_state.get("continuation_policy") or "").strip() or None
    continuation_anchor = str(runtime_state.get("continuation_anchor") or "").strip() or None
    continuation_reason = str(runtime_state.get("continuation_reason") or "").strip() or None
    if continuation_policy is None and continuation_anchor is None and continuation_reason is None:
        return None
    return {
        "quest_status": str(runtime_state.get("status") or "").strip() or (quest_status.value if quest_status is not None else None),
        "active_run_id": str(runtime_state.get("active_run_id") or "").strip() or None,
        "continuation_policy": continuation_policy,
        "continuation_anchor": continuation_anchor,
        "continuation_reason": continuation_reason,
        "runtime_state_path": str(runtime_state_path),
    }


def _record_continuation_state_if_present(*, status: StudyRuntimeStatus, quest_root: Path) -> None:
    payload = _continuation_state_payload(quest_root=quest_root, quest_status=status.quest_status)
    if payload is None:
        return
    status.record_continuation_state(StudyRuntimeContinuationState.from_payload(payload))


def _is_controller_owned_finalize_parking(status: StudyRuntimeStatus) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return (
        continuation_state.active_run_id is None
        and continuation_state.continuation_policy == _FINALIZE_PARKING_CONTINUATION_POLICY
        and continuation_state.continuation_reason == _FINALIZE_PARKING_CONTINUATION_REASON
    )


def _controller_decision_requires_human_confirmation(*, study_root: Path) -> bool:
    payload = _load_json_dict(study_root / "artifacts" / "controller_decisions" / "latest.json")
    return bool(payload.get("requires_human_confirmation"))


def _publication_supervisor_requires_human_confirmation(status: StudyRuntimeStatus) -> bool:
    payload = status.extras.get("publication_supervisor_state")
    if not isinstance(payload, dict):
        return False
    return str(payload.get("current_required_action") or "").strip() == _HUMAN_CONFIRMATION_REQUIRED_ACTION


def _runtime_liveness_audit_payload(status: StudyRuntimeStatus) -> dict[str, object]:
    payload = status.extras.get("runtime_liveness_audit")
    return dict(payload) if isinstance(payload, dict) else {}


def _runtime_event_status_snapshot(status: StudyRuntimeStatus) -> dict[str, object]:
    runtime_liveness_audit = _runtime_liveness_audit_payload(status)
    runtime_audit = (
        dict(runtime_liveness_audit.get("runtime_audit") or {})
        if isinstance(runtime_liveness_audit.get("runtime_audit"), dict)
        else {}
    )
    continuation_state = status.extras.get("continuation_state")
    supervisor_tick_audit = status.extras.get("supervisor_tick_audit")
    return {
        "quest_status": status.quest_status.value if status.quest_status is not None else None,
        "decision": status.decision.value if status.decision is not None else None,
        "reason": status.reason.value if status.reason is not None else None,
        "active_run_id": str(runtime_liveness_audit.get("active_run_id") or runtime_audit.get("active_run_id") or "").strip() or None,
        "runtime_liveness_status": str(runtime_liveness_audit.get("status") or "").strip() or None,
        "worker_running": runtime_audit.get("worker_running") if isinstance(runtime_audit.get("worker_running"), bool) else None,
        "continuation_policy": (
            str(continuation_state.get("continuation_policy") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "continuation_reason": (
            str(continuation_state.get("continuation_reason") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "supervisor_tick_status": (
            str(supervisor_tick_audit.get("status") or "").strip() or None
            if isinstance(supervisor_tick_audit, dict)
            else None
        ),
        "controller_owned_finalize_parking": _is_controller_owned_finalize_parking(status),
        "runtime_escalation_ref": (
            dict(status.extras.get("runtime_escalation_ref"))
            if isinstance(status.extras.get("runtime_escalation_ref"), dict)
            else None
        ),
    }


def _runtime_event_outer_loop_input(status: StudyRuntimeStatus) -> dict[str, object]:
    snapshot = _runtime_event_status_snapshot(status)
    interaction_arbitration = status.extras.get("interaction_arbitration")
    return {
        "quest_status": snapshot["quest_status"],
        "decision": snapshot["decision"],
        "reason": snapshot["reason"],
        "active_run_id": snapshot["active_run_id"],
        "runtime_liveness_status": snapshot["runtime_liveness_status"],
        "worker_running": snapshot["worker_running"],
        "supervisor_tick_status": snapshot["supervisor_tick_status"],
        "controller_owned_finalize_parking": snapshot["controller_owned_finalize_parking"],
        "interaction_action": (
            str(interaction_arbitration.get("action") or "").strip() or None
            if isinstance(interaction_arbitration, dict)
            else None
        ),
        "interaction_requires_user_input": (
            bool(interaction_arbitration.get("requires_user_input"))
            if isinstance(interaction_arbitration, dict)
            else False
        ),
        "runtime_escalation_ref": snapshot["runtime_escalation_ref"],
    }


def _launch_report_runtime_liveness_status(payload: dict[str, object]) -> str | None:
    runtime_liveness_audit = payload.get("runtime_liveness_audit")
    if isinstance(runtime_liveness_audit, dict):
        status = str(runtime_liveness_audit.get("status") or "").strip()
        if status:
            return status
    status = str(payload.get("runtime_liveness_status") or "").strip()
    return status or None


def _launch_report_supervisor_tick_status(payload: dict[str, object]) -> str | None:
    supervisor_tick_audit = payload.get("supervisor_tick_audit")
    if isinstance(supervisor_tick_audit, dict):
        status = str(supervisor_tick_audit.get("status") or "").strip()
        if status:
            return status
    status = str(payload.get("supervisor_tick_status") or "").strip()
    return status or None


def _record_runtime_event(
    *,
    status: StudyRuntimeStatus,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
) -> None:
    execution = status.execution
    if (
        str(execution.get("engine") or "").strip() != "med-deepscientist"
        or str(execution.get("auto_entry") or "").strip() != "on_managed_research_intent"
        or not status.quest_exists
    ):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    try:
        session_payload = _get_quest_session(
            runtime_root=runtime_context.runtime_root,
            quest_id=status.quest_id,
        )
    except (RuntimeError, OSError, ValueError):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    runtime_event_ref = session_payload.get("runtime_event_ref")
    if isinstance(runtime_event_ref, dict):
        status.record_runtime_event_ref(runtime_event_ref)
    else:
        status.extras.pop("runtime_event_ref", None)
    runtime_event = session_payload.get("runtime_event")
    if isinstance(runtime_event, dict):
        status["runtime_event"] = dict(runtime_event)
    else:
        status.extras.pop("runtime_event", None)


def _sync_runtime_summary_if_needed(
    *,
    status: StudyRuntimeStatus,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
) -> None:
    current_snapshot = _runtime_event_status_snapshot(status)
    current_quest_status = (
        str(current_snapshot.get("quest_status") or "").strip() or (status.quest_status.value if status.quest_status is not None else None)
    )
    current_active_run_id = str(current_snapshot.get("active_run_id") or "").strip() or None
    current_runtime_liveness_status = str(current_snapshot.get("runtime_liveness_status") or "").strip() or None
    current_supervisor_tick_status = str(current_snapshot.get("supervisor_tick_status") or "").strip() or None
    launch_report_path = runtime_context.launch_report_path
    launch_report_payload = _load_json_dict(launch_report_path) if launch_report_path.exists() else {}
    launch_report_exists = launch_report_path.exists()
    launch_report_quest_status = str(launch_report_payload.get("quest_status") or "").strip() or None
    launch_report_active_run_id = str(launch_report_payload.get("active_run_id") or "").strip() or None
    launch_report_runtime_liveness_status = _launch_report_runtime_liveness_status(launch_report_payload)
    launch_report_supervisor_tick_status = _launch_report_supervisor_tick_status(launch_report_payload)
    aligned = launch_report_exists and (
        launch_report_quest_status == current_quest_status
        and launch_report_active_run_id == current_active_run_id
        and launch_report_runtime_liveness_status == current_runtime_liveness_status
        and launch_report_supervisor_tick_status == current_supervisor_tick_status
    )
    mismatch_reason: str | None = None
    if not launch_report_exists:
        mismatch_reason = "launch_report_missing"
    elif launch_report_quest_status != current_quest_status:
        mismatch_reason = "launch_report_quest_status_mismatch"
    elif launch_report_active_run_id != current_active_run_id:
        mismatch_reason = "launch_report_active_run_id_mismatch"
    elif launch_report_runtime_liveness_status != current_runtime_liveness_status:
        mismatch_reason = "launch_report_runtime_liveness_status_mismatch"
    elif launch_report_supervisor_tick_status != current_supervisor_tick_status:
        mismatch_reason = "launch_report_supervisor_tick_status_mismatch"
    status_sync_applied = False
    if not aligned:
        study_runtime_protocol.persist_runtime_artifacts(
            runtime_binding_path=runtime_context.runtime_binding_path,
            launch_report_path=launch_report_path,
            runtime_root=runtime_context.runtime_root,
            study_id=status.study_id,
            study_root=Path(status.study_root),
            quest_id=status.quest_id if status.quest_exists else None,
            last_action=None,
            status=status.to_dict(),
            source="study_runtime_status",
            force=False,
            startup_payload_path=None,
            daemon_result=None,
            recorded_at=_router_module()._utc_now(),
        )
        status_sync_applied = True
    status.record_runtime_summary_alignment(
        StudyRuntimeSummaryAlignment(
            source_of_truth="study_runtime_status",
            runtime_state_path=str(_runtime_state_path(runtime_context.quest_root)),
            runtime_state_status=current_quest_status,
            source_active_run_id=current_active_run_id,
            source_runtime_liveness_status=current_runtime_liveness_status,
            source_supervisor_tick_status=current_supervisor_tick_status,
            launch_report_path=str(launch_report_path),
            launch_report_exists=launch_report_exists,
            launch_report_quest_status=launch_report_quest_status,
            launch_report_active_run_id=launch_report_active_run_id,
            launch_report_runtime_liveness_status=launch_report_runtime_liveness_status,
            launch_report_supervisor_tick_status=launch_report_supervisor_tick_status,
            aligned=aligned,
            mismatch_reason=mismatch_reason,
            status_sync_applied=status_sync_applied,
        )
    )


def _find_pending_interaction_artifact_path(*, quest_root: Path, interaction_id: str) -> Path | None:
    resolved_interaction_id = str(interaction_id or "").strip()
    if not resolved_interaction_id:
        return None
    candidates: list[Path] = []
    patterns = (
        f".ds/worktrees/*/artifacts/*/{resolved_interaction_id}.json",
        f"artifacts/*/{resolved_interaction_id}.json",
    )
    for pattern in patterns:
        candidates.extend(quest_root.glob(pattern))
    return quest_state.find_latest(candidates)


def _pending_user_interaction_payload(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
) -> dict[str, object] | None:
    router = _router_module()
    try:
        session_payload = router.med_deepscientist_transport.get_quest_session(
            runtime_root=runtime_root,
            quest_id=quest_id,
        )
    except (RuntimeError, OSError, ValueError):
        return None
    snapshot = session_payload.get("snapshot")
    if not isinstance(snapshot, dict):
        return None
    waiting_interaction_id = str(snapshot.get("waiting_interaction_id") or "").strip() or None
    default_reply_interaction_id = str(snapshot.get("default_reply_interaction_id") or "").strip() or None
    raw_pending_decisions = snapshot.get("pending_decisions")
    pending_decisions = (
        [str(item).strip() for item in raw_pending_decisions if str(item).strip()]
        if isinstance(raw_pending_decisions, list)
        else []
    )
    interaction_id = waiting_interaction_id or default_reply_interaction_id or (pending_decisions[0] if pending_decisions else None)
    if interaction_id is None:
        return None
    interaction_artifact_path = _find_pending_interaction_artifact_path(
        quest_root=quest_root,
        interaction_id=interaction_id,
    )
    artifact_payload = _load_json_dict(interaction_artifact_path) if interaction_artifact_path is not None else {}
    reply_schema = artifact_payload.get("reply_schema")
    if not isinstance(reply_schema, dict):
        reply_schema = {}
    reply_mode = str(artifact_payload.get("reply_mode") or "").strip() or None
    return {
        "interaction_id": interaction_id,
        "kind": str(artifact_payload.get("kind") or "").strip() or None,
        "waiting_interaction_id": waiting_interaction_id,
        "default_reply_interaction_id": default_reply_interaction_id,
        "pending_decisions": pending_decisions,
        "blocking": reply_mode == "blocking" or waiting_interaction_id == interaction_id,
        "reply_mode": reply_mode,
        "expects_reply": bool(artifact_payload.get("expects_reply", waiting_interaction_id == interaction_id)),
        "allow_free_text": bool(artifact_payload.get("allow_free_text", True)),
        "message": str(artifact_payload.get("message") or "").strip() or None,
        "summary": str(artifact_payload.get("summary") or "").strip() or None,
        "reply_schema": reply_schema,
        "decision_type": str(reply_schema.get("decision_type") or "").strip() or None,
        "options_count": (
            len(artifact_payload.get("options") or [])
            if isinstance(artifact_payload.get("options"), list)
            else 0
        ),
        "guidance_requires_user_decision": (
            artifact_payload.get("guidance_vm", {}).get("requires_user_decision")
            if isinstance(artifact_payload.get("guidance_vm"), dict)
            else None
        ),
        "source_artifact_path": str(interaction_artifact_path) if interaction_artifact_path is not None else None,
        "relay_required": True,
    }


def _record_pending_user_interaction_if_required(
    *,
    status: StudyRuntimeStatus,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
) -> None:
    if status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER and not _is_controller_owned_finalize_parking(status):
        return
    payload = _pending_user_interaction_payload(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    if payload is None:
        return
    status.record_pending_user_interaction(payload)


def _record_interaction_arbitration_if_required(
    *,
    status: StudyRuntimeStatus,
    execution: dict[str, object],
    submission_metadata_only: bool,
    publication_gate_report: dict[str, object] | None,
) -> None:
    if status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER and not _is_controller_owned_finalize_parking(status):
        return
    payload = status.extras.get("pending_user_interaction")
    if status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER and not isinstance(payload, dict):
        return
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=payload if isinstance(payload, dict) else None,
        decision_policy=str(execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=submission_metadata_only,
        publication_gate_report=publication_gate_report if isinstance(publication_gate_report, dict) else None,
    )
    status.record_interaction_arbitration(arbitration)


def _status_state(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
) -> StudyRuntimeStatus:
    router = _router_module()
    execution = router._execution_payload(study_payload)
    selected_entry_mode = str(entry_mode or execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    runtime_root = runtime_context.runtime_root
    quest_root = runtime_context.quest_root
    runtime_binding_path = runtime_context.runtime_binding_path
    launch_report_path = runtime_context.launch_report_path
    quest_runtime = quest_state.inspect_quest_runtime(quest_root)
    quest_exists = quest_runtime.quest_exists
    quest_status = StudyRuntimeStatus._normalize_quest_status_field(quest_runtime.quest_status)
    if quest_status in _LIVE_QUEST_STATUSES:
        runtime_liveness_audit = router._inspect_quest_live_execution(
            runtime_root=runtime_root,
            quest_id=quest_id,
        )
        quest_runtime = quest_runtime.with_runtime_liveness_audit(runtime_liveness_audit).with_bash_session_audit(
            dict(runtime_liveness_audit.get("bash_session_audit") or {})
        )
    contracts = router.inspect_workspace_contracts(profile)
    readiness = startup_data_readiness_controller.startup_data_readiness(workspace_root=profile.workspace_root)
    startup_boundary_gate = startup_boundary_gate_controller.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    runtime_reentry_gate = runtime_reentry_gate_controller.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_root=quest_root if quest_exists else None,
        enforce_startup_hydration=quest_status in _LIVE_QUEST_STATUSES,
    )
    completion_state = router._study_completion_state(study_root=study_root)
    submission_metadata_only_wait = (
        quest_exists
        and quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER
        and _waiting_submission_metadata_only(quest_root)
    )

    result = StudyRuntimeStatus(
        schema_version=1,
        study_id=study_id,
        study_root=str(study_root),
        entry_mode=selected_entry_mode,
        execution=execution,
        quest_id=quest_id,
        quest_root=str(quest_root),
        quest_exists=quest_exists,
        quest_status=quest_status,
        runtime_binding_path=str(runtime_binding_path),
        runtime_binding_exists=runtime_binding_path.exists(),
        workspace_contracts=contracts,
        startup_data_readiness=readiness,
        startup_boundary_gate=startup_boundary_gate,
        runtime_reentry_gate=runtime_reentry_gate,
        study_completion_state=completion_state,
        controller_first_policy_summary=router.render_controller_first_summary(),
        automation_ready_summary=router.render_automation_ready_summary(),
    )

    if quest_exists:
        publication_gate_report = publication_gate_controller.build_gate_report(
            publication_gate_controller.build_gate_state(quest_root)
        )
        result.record_publication_supervisor_state(
            publication_gate_controller.extract_publication_supervisor_state(publication_gate_report)
        )
        _materialize_publication_eval_from_gate_report(
            study_root=study_root,
            study_id=study_id,
            quest_root=quest_root,
            quest_id=quest_id,
            publication_gate_report=publication_gate_report,
        )
    else:
        publication_gate_report = None
    _record_continuation_state_if_present(status=result, quest_root=quest_root)
    _record_pending_user_interaction_if_required(
        status=result,
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
    )
    _record_interaction_arbitration_if_required(
        status=result,
        execution=execution,
        submission_metadata_only=submission_metadata_only_wait,
        publication_gate_report=publication_gate_report,
    )

    def _finalize_result() -> StudyRuntimeStatus:
        router._record_autonomous_runtime_notice_if_required(
            status=result,
            runtime_root=runtime_root,
            launch_report_path=launch_report_path,
        )
        _record_execution_owner_guard(status=result, quest_root=quest_root)
        _record_supervisor_tick_audit(status=result, study_root=study_root)
        if not result.should_refresh_startup_hydration_while_blocked():
            result.extras.pop("runtime_escalation_ref", None)
        else:
            runtime_escalation_ref = study_runtime_protocol.read_runtime_escalation_record_ref(quest_root=quest_root)
            if runtime_escalation_ref is not None:
                result.record_runtime_escalation_ref(runtime_escalation_ref)
        if sync_runtime_summary:
            _sync_runtime_summary_if_needed(
                status=result,
                runtime_context=runtime_context,
            )
        if include_progress_projection:
            from med_autoscience.controllers import study_progress as study_progress_controller

            result.record_progress_projection(
                study_progress_controller.build_study_progress_projection(
                    profile=profile,
                    study_id=study_id,
                    study_root=study_root,
                    status_payload=result,
                    entry_mode=entry_mode,
                )
            )
        _record_runtime_event(
            status=result,
            runtime_context=runtime_context,
        )
        return result

    if str(execution.get("engine") or "").strip() != "med-deepscientist":
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MED_DEEPSCIENTIST,
        )
        return _finalize_result()

    auto_entry = str(execution.get("auto_entry") or "").strip()
    default_entry_mode = str(execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    if auto_entry != "on_managed_research_intent":
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED,
        )
        return _finalize_result()
    if selected_entry_mode != default_entry_mode:
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.ENTRY_MODE_NOT_MANAGED,
        )
        return _finalize_result()

    completion_contract_status = completion_state.status
    if completion_contract_status in {
        StudyCompletionStateStatus.INVALID,
        StudyCompletionStateStatus.INCOMPLETE,
    }:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_COMPLETION_CONTRACT_NOT_READY,
        )
        return _finalize_result()
    if completion_state.ready:
        contract = completion_state.contract
        if contract is not None and contract.requires_program_human_confirmation:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STUDY_COMPLETION_REQUIRES_PROGRAM_HUMAN_CONFIRMATION,
            )
            return _finalize_result()
        if publication_gate_report is not None and str(publication_gate_report.get("status") or "").strip() != "clear":
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STUDY_COMPLETION_PUBLISHABILITY_GATE_BLOCKED,
            )
            return _finalize_result()
        if not quest_exists:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.STUDY_COMPLETION_DECLARED_WITHOUT_MANAGED_QUEST,
            )
            return _finalize_result()
        if quest_status == StudyRuntimeQuestStatus.COMPLETED:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.QUEST_ALREADY_COMPLETED,
            )
            return _finalize_result()
        if quest_status in _LIVE_QUEST_STATUSES:
            audit_status = router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
            if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STUDY_COMPLETION_LIVE_RUNTIME_AUDIT_FAILED,
                )
            elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE_AND_COMPLETE,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.SYNC_COMPLETION,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.SYNC_COMPLETION,
            StudyRuntimeReason.STUDY_COMPLETION_READY,
        )
        return _finalize_result()

    if not result.workspace_overall_ready:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.WORKSPACE_CONTRACT_NOT_READY,
        )
        return _finalize_result()

    if result.has_unresolved_contract_for(study_id):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_DATA_READINESS_BLOCKED,
        )
        return _finalize_result()

    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=router._build_startup_contract(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            study_payload=study_payload,
            execution=execution,
        )
    )
    result.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return _finalize_result()

    if not quest_exists:
        if result.startup_boundary_allows_compute_stage:
            if result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.CREATE_AND_START,
                    StudyRuntimeReason.QUEST_MISSING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_AUTO_START,
                )
        else:
            result.set_decision(
                StudyRuntimeDecision.CREATE_ONLY,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_AUTO_START,
            )
        return _finalize_result()

    if quest_status in _LIVE_QUEST_STATUSES:
        audit_status = router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
        controller_owned_finalize_parking = _is_controller_owned_finalize_parking(result)
        if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED,
            )
        elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
            if not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RUNNING_QUEST,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RUNNING_QUEST,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.NOOP,
                    StudyRuntimeReason.QUEST_ALREADY_RUNNING,
                )
        elif controller_owned_finalize_parking:
            interaction_arbitration = result.extras.get("interaction_arbitration")
            if isinstance(interaction_arbitration, dict):
                classification = str(interaction_arbitration.get("classification") or "").strip()
                action = str(interaction_arbitration.get("action") or "").strip()
                if classification == "external_input_required" and action == "block":
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
                    )
                    return _finalize_result()
            if _controller_decision_requires_human_confirmation(study_root=study_root) or _publication_supervisor_requires_human_confirmation(result):
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
                )
            elif not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
                )
            elif execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                )
        elif not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
        elif not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
        elif execution.get("auto_resume") is True:
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION,
            )
        else:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
            )
        return _finalize_result()

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        if not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
            return _finalize_result()
        if not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
            return _finalize_result()
        if execution.get("auto_resume") is True:
            resumable_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_WAITING_TO_START)
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                resumable_reason,
            )
        else:
            blocked_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED)
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                blocked_reason,
            )
        return _finalize_result()

    if quest_status == StudyRuntimeQuestStatus.STOPPED:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
        )
        return _finalize_result()

    if quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER:
        interaction_arbitration = result.extras.get("interaction_arbitration")
        if isinstance(interaction_arbitration, dict):
            classification = str(interaction_arbitration.get("classification") or "").strip()
            action = str(interaction_arbitration.get("action") or "").strip()
            if action == "resume":
                resume_reason = {
                    "submission_metadata_only": StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                    "premature_completion_request": (
                        StudyRuntimeReason.QUEST_COMPLETION_REQUESTED_BEFORE_PUBLICATION_GATE_CLEAR
                    ),
                    "invalid_blocking": StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                }.get(classification, StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING)
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    resume_reason,
                )
                return _finalize_result()
            if classification == "external_input_required":
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
                )
                return _finalize_result()
        if submission_metadata_only_wait:
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_USER,
        )
        return _finalize_result()

    result.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.QUEST_EXISTS_WITH_NON_RESUMABLE_STATE,
    )
    return _finalize_result()


def _status_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
) -> dict[str, object]:
    router = _router_module()
    return router._status_state(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
        sync_runtime_summary=sync_runtime_summary,
        include_progress_projection=include_progress_projection,
    ).to_dict()
