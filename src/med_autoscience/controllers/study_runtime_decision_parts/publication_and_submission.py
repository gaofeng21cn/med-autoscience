from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
import json
from pathlib import Path

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.controller_confirmation_summary import (
    materialize_controller_confirmation_summary,
    read_controller_confirmation_summary,
    stable_controller_confirmation_summary_path,
)
from med_autoscience.controllers import (
    publication_gate as publication_gate_controller,
    runtime_worker_activity,
    runtime_supervision as runtime_supervision_controller,
    study_truth_kernel,
    study_runtime_interaction_arbitration as interaction_arbitration_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    study_runtime_family_orchestration as family_orchestration,
    startup_data_readiness as startup_data_readiness_controller,
    startup_boundary_gate as startup_boundary_gate_controller,
)
from med_autoscience.controllers.submission_package_layout import resolve_submission_manifest_path
from med_autoscience.controllers.study_runtime_decision_parts import publication_stop_loss
from med_autoscience.controllers.study_runtime_execution_parts import runtime_events as _execution_runtime_events
from med_autoscience.controllers.study_runtime_decision_parts.publication_eval_quality import (
    _publication_eval_gap_type,
    publication_eval_quality_assessment,
)
from med_autoscience.controllers.study_runtime_decision_parts.publication_decision import (
    publication_eval_action as _publication_decision_eval_action,
)
from med_autoscience.controllers.study_runtime_decision_parts.publication_owner_currentness import (
    _current_ai_reviewer_publication_eval_ref,
)
from med_autoscience.controllers.study_runtime_execution_parts.controller_authorization import (
    _controller_decision_authorization_identity,
    _load_controller_decision_authorization_context,
)
from med_autoscience.controllers.study_runtime_execution_parts.work_unit_evidence_adoption import (
    existing_controller_work_unit_evidence_adoption,
    record_controller_work_unit_evidence_adoption,
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
from med_autoscience.publication_eval_latest import (
    materialize_publication_eval_latest,
    stable_publication_eval_latest_path,
)
from med_autoscience.publication_eval_specificity_targets import specificity_target_status
from med_autoscience.publication_eval_record import (
    PublicationEvalAssessmentProvenance,
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
from med_autoscience.study_manual_finish import (
    manual_finish_guard_only,
    resolve_bundle_only_submission_ready_manual_finish_contract,
    resolve_delivered_submission_package_manual_finish_contract,
    resolve_runtime_read_study_manual_finish_contract,
    resolve_study_manual_finish_contract,
    resolve_submission_metadata_only_manual_finish_contract,
)
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    reviewer_revision_has_open_reviewer_first_blockers,
    task_intake_requests_manual_hold,
    task_intake_overrides_auto_manual_finish,
    task_intake_yields_to_deterministic_submission_closeout,
)

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
_AUTO_RECOVERY_CONTROLLER_STOP_SOURCES = frozenset(
    {
        "medautosci-figure-loop-guard",
        "codex-medical-publication-surface",
    }
)

def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")

def _record_existing_controller_work_unit_evidence_adoption(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
) -> dict[str, object] | None:
    authorization_context = _load_controller_decision_authorization_context(study_root=study_root)
    if authorization_context is None:
        return None
    identity = _controller_decision_authorization_identity(authorization_context)
    evidence_adoption = existing_controller_work_unit_evidence_adoption(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )
    if evidence_adoption is None:
        return None
    record_controller_work_unit_evidence_adoption(
        status=status,
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
        evidence_adoption=evidence_adoption,
    )
    return evidence_adoption

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


def _surface_emitted_at(payload: dict[str, object] | None) -> datetime | None:
    if not isinstance(payload, dict):
        return None
    return _normalize_timestamp(payload.get("emitted_at") or payload.get("generated_at") or payload.get("created_at"))


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


def _load_json_dict(path: Path) -> dict[str, object]:
    payload = _read_json_mapping(path)
    return payload if payload is not None else {}

def _supervisor_tick_required(status: StudyRuntimeStatus) -> bool:
    execution = status.execution
    return (
        runtime_backend_contract.is_managed_research_execution(execution)
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
                "summary": "MAS scheduler 托管监管心跳缺失，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要恢复或补齐 MAS scheduler supervision tick 调度，再继续托管监管与自动恢复。",
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
                "summary": "最近一次 MAS scheduler 监管记录缺少可解析时间戳，当前不能确认监管心跳是否仍然新鲜。",
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
                "summary": "MAS scheduler 托管监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要先恢复 MAS scheduler supervision tick 调度，再继续托管监管与自动恢复。",
            }
        )
        status.record_supervisor_tick_audit(payload)
        return

    payload.update(
        {
            "status": "fresh",
            "reason": "supervisor_tick_report_fresh",
            "summary": "MAS scheduler 托管监管心跳新鲜，当前仍在按合同持续监管。",
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
    if blocking_item_ids:
        return all(item_id in _SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_KEYS for item_id in blocking_item_ids)
    return paper_artifacts.submission_checklist_requires_external_metadata(payload)


def _submission_metadata_only_manual_finish_active(*, study_root: Path, quest_root: Path) -> bool:
    return (
        resolve_submission_metadata_only_manual_finish_contract(
            study_root=study_root,
            quest_root=quest_root,
        )
        is not None
    )


def _bundle_only_submission_ready_manual_finish_active(*, study_root: Path, quest_root: Path | None = None) -> bool:
    return (
        resolve_bundle_only_submission_ready_manual_finish_contract(
            study_root=study_root,
            quest_root=quest_root,
        )
        is not None
    )


def _delivered_submission_package_manual_finish_active(*, study_root: Path) -> bool:
    return resolve_delivered_submission_package_manual_finish_contract(study_root=study_root) is not None


def _explicit_manual_finish_compatibility_guard_active(*, study_root: Path) -> bool:
    contract = resolve_runtime_read_study_manual_finish_contract(study_root=study_root)
    return manual_finish_guard_only(contract)


def _task_intake_overrides_auto_manual_finish_active(*, study_root: Path) -> bool:
    return task_intake_overrides_auto_manual_finish(read_latest_task_intake(study_root=study_root))


def _task_intake_release_blocked_by_current_closeout(
    *,
    study_root: Path,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    payload = read_latest_task_intake(study_root=study_root)
    if not task_intake_overrides_auto_manual_finish(payload):
        return False
    evaluation_summary_payload = _load_json_dict(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    )
    if task_intake_yields_to_deterministic_submission_closeout(
        payload,
        study_root=study_root,
        publishability_gate_report=dict(publication_gate_report) if isinstance(publication_gate_report, dict) else None,
        evaluation_summary=evaluation_summary_payload,
    ):
        return True
    publication_eval_payload = _load_json_dict(study_root / "artifacts" / "publication_eval" / "latest.json")
    provenance = publication_eval_payload.get("assessment_provenance")
    provenance_payload = provenance if isinstance(provenance, dict) else {}
    owner = str(provenance_payload.get("owner") or "").strip()
    if owner != "ai_reviewer":
        return False
    return _surface_emitted_at(publication_eval_payload) >= _surface_emitted_at(payload)


def _task_intake_yields_to_submission_closeout_active(
    *,
    study_root: Path,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    payload = read_latest_task_intake(study_root=study_root)
    if not task_intake_overrides_auto_manual_finish(payload):
        return False
    evaluation_summary_payload = _load_json_dict(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    )
    return task_intake_yields_to_deterministic_submission_closeout(
        payload,
        study_root=study_root,
        publishability_gate_report=dict(publication_gate_report) if isinstance(publication_gate_report, dict) else None,
        evaluation_summary=evaluation_summary_payload,
    )


def _publication_eval_evidence_refs(*values: object) -> tuple[str, ...]:
    refs: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            refs.append(text)
    return tuple(refs)


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


def _publication_eval_specificity_targets(report: dict[str, object]) -> tuple[dict[str, str], ...]:
    blockers = [str(item).strip() for item in (report.get("blockers") or []) if str(item).strip()]
    if not blockers:
        return ()

    def _text(value: object) -> str | None:
        text = str(value or "").strip()
        return text or None

    def _source_path_from_ref(ref: object) -> str | None:
        if not isinstance(ref, dict):
            return None
        return _text(ref.get("source_path")) or _text(ref.get("artifact_path"))

    def _target_id_from_ref(ref: dict[str, object], default_target_id: str) -> str:
        for key in (
            "target_id",
            "claim_id",
            "figure_id",
            "table_id",
            "metric_id",
            "display_id",
            "artifact_role",
            "blocker",
        ):
            if text := _text(ref.get(key)):
                return text
        return default_target_id

    def _kind_from_ref(ref: dict[str, object]) -> str | None:
        haystack = " ".join(
            str(ref.get(key) or "")
            for key in ("target_kind", "artifact_role", "blocker", "artifact_path", "source_path")
        ).lower()
        if "claim" in haystack or "evidence" in haystack or "story" in haystack or "review_ledger" in haystack:
            return "claim"
        if "figure" in haystack or "display" in haystack:
            return "figure"
        if "table" in haystack or "submission" in haystack:
            return "table"
        if "metric" in haystack or "result" in haystack or "analysis" in haystack:
            return "metric"
        if "source" in haystack or "path" in haystack:
            return "source_path"
        return None

    def _fallback_path(kind: str) -> str | None:
        paper_root = _text(report.get("paper_root"))
        if kind == "claim" and paper_root is not None:
            return str(Path(paper_root) / "claim_evidence_map.json")
        if kind == "figure" and paper_root is not None:
            return str(Path(paper_root) / "figures" / "figure_catalog.json")
        if kind == "table":
            return _text(report.get("submission_minimal_manifest_path")) or (
                str(Path(paper_root) / "tables" / "table_catalog.json") if paper_root is not None else None
            )
        if kind == "metric":
            return _text(report.get("main_result_path"))
        return (
            _text(report.get("medical_publication_surface_report_path"))
            or _text(report.get("latest_gate_path"))
            or _text(report.get("main_result_path"))
            or paper_root
        )

    def _append_target(
        targets: list[dict[str, str]],
        *,
        kind: str,
        target_id: str,
        source_path: str | None,
        blocking_reason: str,
    ) -> None:
        if kind in {item["target_kind"] for item in targets}:
            return
        if source_path is None:
            source_path = _fallback_path(kind)
        if source_path is None:
            return
        targets.append(
            {
                "target_kind": kind,
                "target_id": target_id,
                "source_path": source_path,
                "blocking_reason": blocking_reason,
            }
        )

    targets: list[dict[str, str]] = []
    blocking_refs = report.get("blocking_artifact_refs")
    if isinstance(blocking_refs, list):
        for ref in blocking_refs:
            if not isinstance(ref, dict):
                continue
            kind = _kind_from_ref(ref)
            if kind is None:
                continue
            blocker = _text(ref.get("blocker")) or blockers[0]
            _append_target(
                targets,
                kind=kind,
                target_id=_target_id_from_ref(ref, f"{kind}_publication_gate_target"),
                source_path=_source_path_from_ref(ref),
                blocking_reason=blocker,
            )

    defaults = {
        "claim": "claim_evidence_map",
        "figure": "figure_catalog",
        "table": "submission_table_or_manifest",
        "metric": "main_result_metrics",
        "source_path": "publication_gate_source_path",
    }
    for kind, target_id in defaults.items():
        _append_target(
            targets,
            kind=kind,
            target_id=target_id,
            source_path=_fallback_path(kind),
            blocking_reason=blockers[0],
        )
    return tuple(targets)


def _publication_eval_action(
    *,
    report: dict[str, object],
    generated_at: str,
    evidence_refs: tuple[str, ...],
) -> PublicationEvalRecommendedAction:
    return _publication_decision_eval_action(
        report=report,
        generated_at=generated_at,
        evidence_refs=evidence_refs,
        specificity_targets=_publication_eval_specificity_targets,
    )


def _study_charter_gate_reason(report: dict[str, object] | None) -> StudyRuntimeReason | None:
    if not isinstance(report, dict):
        return None
    blockers = {
        str(item).strip()
        for item in (report.get("blockers") or [])
        if str(item).strip()
    }
    if "study_charter_missing" in blockers:
        return StudyRuntimeReason.STUDY_CHARTER_MISSING
    if "study_charter_invalid" in blockers:
        return StudyRuntimeReason.STUDY_CHARTER_INVALID
    return None


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
    try:
        charter_payload = read_study_charter(study_root=study_root)
    except (json.JSONDecodeError, ValueError):
        return None
    resolved_quest_id = (
        str(publication_gate_report.get("quest_id") or "").strip()
        or str(quest_id or "").strip()
        or quest_root.name
    )
    current_ai_reviewer_ref = _current_ai_reviewer_publication_eval_ref(
        study_root=study_root,
        study_id=study_id,
        resolved_quest_id=resolved_quest_id,
        publication_gate_report=publication_gate_report,
    )
    if current_ai_reviewer_ref is not None:
        return current_ai_reviewer_ref
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
        or str(resolve_submission_manifest_path(Path(paper_root_ref).resolve() / "submission_minimal"))
    )
    publication_gate_report_with_defaults = {
        **publication_gate_report,
        "latest_gate_path": latest_gate_path,
        "main_result_path": main_result_ref,
        "paper_root": paper_root_ref,
        "submission_minimal_manifest_path": submission_minimal_ref,
    }
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
        assessment_provenance=PublicationEvalAssessmentProvenance(
            owner="mechanical_projection",
            source_kind="publication_gate_report",
            policy_id="publication_gate_projection_v1",
            source_refs=evidence_refs,
            ai_reviewer_required=True,
        ),
        verdict=_publication_eval_verdict(publication_gate_report_with_defaults),
        quality_assessment=publication_eval_quality_assessment(
            report=publication_gate_report_with_defaults,
            charter_payload=charter_payload,
            evidence_refs=evidence_refs,
        ),
        gaps=_publication_eval_gaps(report=publication_gate_report_with_defaults, evidence_refs=evidence_refs),
        recommended_actions=(
            _publication_eval_action(
                report=publication_gate_report_with_defaults,
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


def _record_runtime_worker_activity(status: StudyRuntimeStatus) -> None:
    status["runtime_worker_activity"] = runtime_worker_activity.normalize_activity(status.to_dict())


def _record_auto_runtime_parked_projection(status: StudyRuntimeStatus) -> None:
    _execution_runtime_events.record_auto_runtime_parked_projection(status)


def _publication_gate_allows_direct_write(status: StudyRuntimeStatus) -> bool:
    try:
        return not status.publication_supervisor_state.bundle_tasks_downstream_only
    except KeyError:
        return True


def _publication_supervisor_current_required_action(payload: dict[str, object] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = str(payload.get("current_required_action") or "").strip()
    return value or None


def _publication_supervisor_requests_automated_continuation(
    payload: dict[str, object] | None,
    *,
    require_blocked_status: bool,
) -> bool:
    if not isinstance(payload, dict):
        return False
    if str(payload.get("phase_owner") or "").strip() != "publication_gate":
        return False
    current_required_action = _publication_supervisor_current_required_action(payload)
    if current_required_action in {None, _HUMAN_CONFIRMATION_REQUIRED_ACTION}:
        return False
    if not require_blocked_status:
        return True
    status = str(payload.get("status") or "").strip()
    return status not in {"", "clear"}


def _publication_gate_requires_live_runtime_reroute(
    publication_gate_report: dict[str, object] | None,
    *,
    status: StudyRuntimeStatus | None = None,
) -> bool:
    if not isinstance(publication_gate_report, dict):
        return False
    current_required_action = _publication_supervisor_current_required_action(publication_gate_report)
    blockers = {
        str(item).strip()
        for item in (publication_gate_report.get("blockers") or [])
        if str(item).strip()
    }
    if (
        "active_run_drifting_into_write_without_gate_approval" in blockers
        and bool(publication_gate_report.get("bundle_tasks_downstream_only"))
        and _publication_supervisor_requests_automated_continuation(
            publication_gate_report,
            require_blocked_status=True,
        )
    ):
        return True
    if status is None:
        return False
    if current_required_action != "return_to_publishability_gate":
        return False
    if not bool(publication_gate_report.get("bundle_tasks_downstream_only")):
        return False
    if not _publication_supervisor_requests_automated_continuation(
        publication_gate_report,
        require_blocked_status=True,
    ):
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return (
        continuation_state.active_run_id is not None
        and continuation_state.continuation_policy == "auto"
        and continuation_state.continuation_anchor == "write"
    )


__all__ = [name for name in globals() if not name.startswith("__")]
