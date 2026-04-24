from __future__ import annotations

from datetime import datetime, timezone
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
    runtime_supervision as runtime_supervision_controller,
    study_runtime_interaction_arbitration as interaction_arbitration_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    study_runtime_family_orchestration as family_orchestration,
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
    PublicationEvalQualityAssessment,
    PublicationEvalQualityDimension,
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
    resolve_bundle_only_submission_ready_manual_finish_contract,
    resolve_delivered_submission_package_manual_finish_contract,
    resolve_study_manual_finish_contract,
    resolve_submission_metadata_only_manual_finish_contract,
)
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
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
                "summary": "Hermes-hosted 托管监管心跳缺失，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要恢复或补齐 Hermes-hosted supervision tick 调度，再继续托管监管与自动恢复。",
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
                "summary": "最近一次 Hermes-hosted 监管记录缺少可解析时间戳，当前不能确认监管心跳是否仍然新鲜。",
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
                "summary": "Hermes-hosted 托管监管心跳已陈旧，当前不能保证及时发现掉线并自动恢复。",
                "next_action_summary": "需要先恢复 Hermes-hosted supervision tick 调度，再继续托管监管与自动恢复。",
            }
        )
        status.record_supervisor_tick_audit(payload)
        return

    payload.update(
        {
            "status": "fresh",
            "reason": "supervisor_tick_report_fresh",
            "summary": "Hermes-hosted 托管监管心跳新鲜，当前仍在按合同持续监管。",
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
    contract = resolve_study_manual_finish_contract(study_root=study_root)
    return contract is not None and contract.compatibility_guard_only


def _task_intake_overrides_auto_manual_finish_active(*, study_root: Path) -> bool:
    return task_intake_overrides_auto_manual_finish(read_latest_task_intake(study_root=study_root))


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


def _publication_eval_gap_type(blocker: str) -> str:
    normalized = blocker.lower()
    if normalized in {
        "medical_publication_surface_blocked",
        "missing_current_medical_publication_surface_report",
    }:
        return "reporting"
    if any(
        token in normalized
        for token in ("submission", "deliverable", "bundle", "surface", "package", "delivery", "mirror", "current_package")
    ):
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


def _charter_text_sequence(payload: dict[str, object], key: str) -> tuple[str, ...]:
    raw_value = payload.get(key)
    if not isinstance(raw_value, list):
        return ()
    items: list[str] = []
    for item in raw_value:
        text = str(item or "").strip()
        if text:
            items.append(text)
    return tuple(items)


def _publication_eval_has_only_delivery_blockers(report: dict[str, object]) -> bool:
    blockers = [
        str(item).strip()
        for item in (report.get("blockers") or [])
        if str(item).strip()
    ]
    return bool(blockers) and all(_publication_eval_gap_type(item) == "delivery" for item in blockers)


def _publication_eval_quality_assessment(
    *,
    report: dict[str, object],
    charter_payload: dict[str, object],
    evidence_refs: tuple[str, ...],
) -> PublicationEvalQualityAssessment:
    publication_objective = str(charter_payload.get("publication_objective") or "").strip()
    paper_framing_summary = str(charter_payload.get("paper_framing_summary") or "").strip()
    minimum_sci_ready_evidence_package = set(_charter_text_sequence(charter_payload, "minimum_sci_ready_evidence_package"))
    scientific_followup_questions = _charter_text_sequence(charter_payload, "scientific_followup_questions")
    explanation_targets = _charter_text_sequence(charter_payload, "explanation_targets")
    manuscript_conclusion_redlines = _charter_text_sequence(charter_payload, "manuscript_conclusion_redlines")
    results_summary = str(report.get("results_summary") or "").strip()
    conclusion = str(report.get("conclusion") or "").strip()
    medical_surface_status = str(report.get("medical_publication_surface_status") or "").strip()
    report_status = str(report.get("status") or "").strip()
    study_delivery_status = str(report.get("study_delivery_status") or "").strip()
    blockers = {
        str(item).strip()
        for item in (report.get("blockers") or [])
        if str(item).strip()
    }
    delivery_only_blockers = _publication_eval_has_only_delivery_blockers(report)
    submission_minimal_ready = (
        bool(report.get("submission_minimal_present"))
        and bool(report.get("submission_minimal_docx_present"))
        and bool(report.get("submission_minimal_pdf_present"))
    )
    clinical_framing_present = bool(publication_objective or paper_framing_summary)
    clinician_facing_target_declared = (
        bool(explanation_targets)
        or "clinician_facing_interpretation_block" in minimum_sci_ready_evidence_package
    )

    def _quality_dimension(
        *,
        status: str,
        summary: str,
        reviewer_reason: str,
        reviewer_revision_advice: str,
        reviewer_next_round_focus: str,
    ) -> PublicationEvalQualityDimension:
        return PublicationEvalQualityDimension(
            status=status,
            summary=summary,
            evidence_refs=evidence_refs,
            reviewer_reason=reviewer_reason,
            reviewer_revision_advice=reviewer_revision_advice,
            reviewer_next_round_focus=reviewer_next_round_focus,
        )

    if not clinical_framing_present:
        clinical_significance = _quality_dimension(
            status="underdefined",
            summary="Study charter 还没有冻结明确的临床论文 framing，临床意义表述仍不够稳。",
            reviewer_reason="当前 charter 还没冻结临床论文 framing，临床意义判读依据不足。",
            reviewer_revision_advice="先在 charter 固定 publication_objective 或 paper_framing_summary，再回到结果叙事。",
            reviewer_next_round_focus="确认临床问题定义、目标人群与预期结论边界是否写入 charter。",
        )
    elif not (results_summary or conclusion):
        clinical_significance = _quality_dimension(
            status="partial",
            summary="临床问题已经被冻结，但当前 gate 还没有稳定的结果/结论表面来支撑给人阅读的临床叙事。",
            reviewer_reason="临床问题已定义，但当前缺少稳定结果/结论表面支撑临床叙事。",
            reviewer_revision_advice="先补齐可引用的结果摘要或结论段，再组织临床意义叙事。",
            reviewer_next_round_focus="核对结果摘要是否能直接回答临床问题并支撑结论措辞。",
        )
    elif clinician_facing_target_declared:
        clinical_significance = _quality_dimension(
            status="ready",
            summary="临床问题、解释目标与结果表面都已经具备，临床意义叙事已进入可审状态。",
            reviewer_reason="临床问题、解释目标与结果表面已对齐，当前维度达到可审状态。",
            reviewer_revision_advice="保持当前叙事结构，优先做事实一致性与术语统一检查。",
            reviewer_next_round_focus="下一轮重点核对临床解释段与关键结果引用是否逐条一致。",
        )
    else:
        clinical_significance = _quality_dimension(
            status="partial",
            summary="主临床问题与结果表面已具备，但 charter 里还缺更显式的 clinician-facing interpretation target。",
            reviewer_reason="主临床问题与结果表面已具备，但 clinician-facing interpretation target 仍未显式冻结。",
            reviewer_revision_advice="在 charter 补齐 clinician-facing interpretation target，再做临床叙事定稿。",
            reviewer_next_round_focus="下一轮重点确认解释目标是否能覆盖主临床结论的每一条关键陈述。",
        )

    if "missing_publication_anchor" in blockers:
        evidence_strength = _quality_dimension(
            status="blocked",
            summary="主科学锚点还没建立，证据链还不能作为论文主叙事放行。",
            reviewer_reason="缺少可发布主锚点，证据链当前不完整。",
            reviewer_revision_advice="先补齐 main result/publishability anchor，再回到 claim-to-evidence 审阅。",
            reviewer_next_round_focus="下一轮优先验证主锚点、关键指标与结论引用的可追溯性。",
        )
    elif medical_surface_status != "clear" or {
        "medical_publication_surface_blocked",
        "missing_current_medical_publication_surface_report",
    } & blockers:
        evidence_strength = _quality_dimension(
            status="blocked",
            summary="论文稿面的证据链还没有清关，claim-to-evidence 或 paper-facing reporting 仍需修复。",
            reviewer_reason="稿面证据链仍未清关，claim-to-evidence 或 paper-facing reporting 存在阻塞。",
            reviewer_revision_advice="按 blocker 顺序修复稿面证据链与 reporting 缺口，再提交审阅。",
            reviewer_next_round_focus="下一轮重点检查 medical publication surface 报告是否 clear 且 blockers 清零。",
        )
    elif report_status == "clear" or delivery_only_blockers:
        evidence_strength = _quality_dimension(
            status="ready",
            summary="科学证据面已经清楚，剩余问题只在交付/刷新层，不在核心证据层。",
            reviewer_reason="核心科学证据链已经清楚，当前剩余问题位于交付/刷新层。",
            reviewer_revision_advice="核心证据链已达标，下一轮优先清理交付与刷新层阻塞，避免再次影响审阅入口。",
            reviewer_next_round_focus="下一轮重点确认 current package 与 submission surfaces 的刷新时序。",
        )
    else:
        evidence_strength = _quality_dimension(
            status="partial",
            summary="主结果和稿面证据已存在，但 publication gate 仍有非纯交付类缺口没有清完。",
            reviewer_reason="主结果和稿面证据已存在，但 publication gate 仍有非交付类缺口未闭合。",
            reviewer_revision_advice="继续消除非交付类 blocker 并补证据引用链，再申请放行。",
            reviewer_next_round_focus="下一轮重点复核非交付 blockers 的证据闭环。",
        )

    if scientific_followup_questions and explanation_targets:
        novelty_positioning = _quality_dimension(
            status="ready",
            summary="Charter 已显式冻结 follow-up questions 和 explanation targets，创新点/贡献边界有正式审计锚点。",
            reviewer_reason="follow-up questions 与 explanation targets 已冻结，贡献边界具备审计锚点。",
            reviewer_revision_advice="保持当前创新叙事结构，避免超出已冻结边界的扩展表述。",
            reviewer_next_round_focus="下一轮重点校对创新点描述与 follow-up questions 的对应关系。",
        )
    elif scientific_followup_questions or explanation_targets or manuscript_conclusion_redlines:
        novelty_positioning = _quality_dimension(
            status="partial",
            summary="贡献边界已经开始结构化，但 novelty/解释目标还没有完全收成一套显式质量合同。",
            reviewer_reason="贡献边界已开始结构化，但 novelty 与解释目标合同尚未完整闭合。",
            reviewer_revision_advice="补齐缺失的 follow-up questions/explanation targets，使贡献边界可审计。",
            reviewer_next_round_focus="下一轮重点检查创新性叙事是否能被 charter 字段逐条追溯。",
        )
    else:
        novelty_positioning = _quality_dimension(
            status="underdefined",
            summary="当前 charter 还缺显式的 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
            reviewer_reason="当前 charter 缺少显式 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
            reviewer_revision_advice="先在 charter 增补可审计的 scientific follow-up questions 或 explanation targets。",
            reviewer_next_round_focus="补齐 scientific follow-up questions 或 explanation targets，再复核创新叙事与主结论边界。",
        )

    if report_status == "clear" and study_delivery_status == "current" and submission_minimal_ready:
        human_review_readiness = _quality_dimension(
            status="ready",
            summary="给人看的 current_package 和 submission_minimal 已同步到最新真相，可以进入人工审阅。",
            reviewer_reason="current_package 与 submission_minimal 已同步到最新真相，人工审阅入口已就绪。",
            reviewer_revision_advice="保持当前交付状态并仅做事实一致性修订。",
            reviewer_next_round_focus="下一轮重点复核审阅包中的引用路径与提交清单一致性。",
        )
    elif report_status == "clear":
        human_review_readiness = _quality_dimension(
            status="partial",
            summary="科学 gate 已清，但给人看的 current_package 或 submission surface 还需要再同步一轮。",
            reviewer_reason="科学 gate 已清，但 current_package 或 submission surface 仍需同步。",
            reviewer_revision_advice="补齐交付面同步后再提交人工审阅，避免审阅基线漂移。",
            reviewer_next_round_focus="下一轮重点确认 submission_minimal 三件套与 current_package 时间戳一致。",
        )
    else:
        human_review_readiness = _quality_dimension(
            status="blocked",
            summary="publication gate 还没清，当前还不能把稿件当作正式人工审阅包放行。",
            reviewer_reason="publication gate 尚未清关，当前稿件还不能作为正式人工审阅包放行。",
            reviewer_revision_advice="先关闭 publication gate blockers，再准备人工审阅包。",
            reviewer_next_round_focus="下一轮重点核对 gate 状态是否 clear 且关键 blocker 全部移除。",
        )

    return PublicationEvalQualityAssessment(
        clinical_significance=clinical_significance,
        evidence_strength=evidence_strength,
        novelty_positioning=novelty_positioning,
        human_review_readiness=human_review_readiness,
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
    def _route_contract_for_action(action_type: str) -> dict[str, str] | None:
        current_required_action = str(report.get("current_required_action") or "").strip()
        controller_stage_note = str(report.get("controller_stage_note") or "").strip()
        if action_type == "bounded_analysis":
            return {
                "route_target": "analysis-campaign",
                "route_key_question": "What is the narrowest supplementary analysis still required before the paper line can continue?",
                "route_rationale": (
                    controller_stage_note
                    or "The current line is clear enough to continue after one bounded supplementary analysis pass."
                ),
            }
        if action_type not in {"continue_same_line", "route_back_same_line"}:
            return None
        if current_required_action in {"continue_bundle_stage", "complete_bundle_stage"}:
            return {
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "route_rationale": (
                    controller_stage_note
                    or "The publication gate is clear and the current paper line can continue into finalize-stage work."
                ),
            }
        return {
            "route_target": "write",
            "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
            "route_rationale": (
                controller_stage_note
                or "The publication gate is clear and the current paper line can continue through same-line manuscript work."
            ),
        }

    def _blocked_route_action() -> tuple[str, dict[str, str]] | None:
        route_back_recommendation = str(report.get("medical_publication_surface_route_back_recommendation") or "").strip()
        controller_stage_note = str(report.get("controller_stage_note") or "").strip()
        if route_back_recommendation == "return_to_analysis_campaign":
            return (
                "bounded_analysis",
                {
                    "route_target": "analysis-campaign",
                    "route_key_question": "What is the narrowest supplementary analysis still required before the paper line can continue?",
                    "route_rationale": (
                        controller_stage_note
                        or "The current blocked publication surface is best repaired through one bounded supplementary analysis pass."
                    ),
                },
            )
        if route_back_recommendation == "return_to_finalize":
            return (
                "route_back_same_line",
                {
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": (
                        controller_stage_note
                        or "The current blocked publication surface should route back to finalize on the same paper line."
                    ),
                },
            )
        if route_back_recommendation == "return_to_write":
            return (
                "route_back_same_line",
                {
                    "route_target": "write",
                    "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                    "route_rationale": (
                        controller_stage_note
                        or "The current blocked publication surface should route back to manuscript repair on the same paper line."
                    ),
                },
            )
        return None

    status = str(report.get("status") or "").strip()
    if status == "clear":
        current_required_action = str(report.get("current_required_action") or "").strip()
        if current_required_action == "prepare_promotion_review":
            action_type = "prepare_promotion_review"
        elif current_required_action == "continue_write_stage":
            action_type = "bounded_analysis"
        else:
            action_type = "continue_same_line"
        reason = (
            str(report.get("controller_stage_note") or "").strip()
            or "Publication gate is clear and the current line can continue."
        )
        route_contract = _route_contract_for_action(action_type) or {}
    else:
        blocked_route_action = _blocked_route_action()
        if blocked_route_action is not None:
            action_type, route_contract = blocked_route_action
        else:
            current_required_action = str(report.get("current_required_action") or "").strip()
            if current_required_action in {"continue_bundle_stage", "complete_bundle_stage"}:
                action_type = "route_back_same_line"
                route_contract = _route_contract_for_action(action_type) or {}
            else:
                action_type = "return_to_controller"
                route_contract = {}
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
        route_target=route_contract.get("route_target"),
        route_key_question=route_contract.get("route_key_question"),
        route_rationale=route_contract.get("route_rationale"),
        requires_controller_decision=True,
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
        quality_assessment=_publication_eval_quality_assessment(
            report=publication_gate_report,
            charter_payload=charter_payload,
            evidence_refs=evidence_refs,
        ),
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


def _publication_gate_allows_live_runtime_write_stage_resume(
    *,
    status: StudyRuntimeStatus,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report):
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return (
        continuation_state.active_run_id is not None
        and continuation_state.continuation_policy == "auto"
        and continuation_state.continuation_anchor == "decision"
        and continuation_state.continuation_reason is not None
        and continuation_state.continuation_reason.startswith("decision:")
    )


def _publication_gate_allows_post_clear_runtime_continuation(
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not isinstance(publication_gate_report, dict):
        return False
    if _publication_gate_requires_live_runtime_reroute(publication_gate_report):
        return False
    if bool(publication_gate_report.get("bundle_tasks_downstream_only")):
        return False
    if _publication_supervisor_current_required_action(publication_gate_report) not in {
        "continue_write_stage",
        "continue_bundle_stage",
    }:
        return False
    if str(publication_gate_report.get("status") or "").strip() not in {"", "clear"}:
        return False
    return _publication_supervisor_requests_automated_continuation(
        publication_gate_report,
        require_blocked_status=False,
    )


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
    if not runtime_backend_contract.is_managed_research_execution(execution):
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
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    try:
        if decision_path.exists():
            materialize_controller_confirmation_summary(
                study_root=study_root,
                decision_ref=decision_path,
            )
        if summary_path.exists():
            summary = read_controller_confirmation_summary(
                study_root=study_root,
                ref=summary_path,
            )
            return str(summary.get("status") or "").strip() == "pending"
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    payload = _load_json_dict(study_root / "artifacts" / "controller_decisions" / "latest.json")
    return bool(payload.get("requires_human_confirmation"))


def _publication_supervisor_requires_human_confirmation(status: StudyRuntimeStatus) -> bool:
    payload = status.extras.get("publication_supervisor_state")
    return _publication_supervisor_current_required_action(payload) == _HUMAN_CONFIRMATION_REQUIRED_ACTION


def _runtime_liveness_audit_payload(status: StudyRuntimeStatus) -> dict[str, object]:
    payload = status.extras.get("runtime_liveness_audit")
    return dict(payload) if isinstance(payload, dict) else {}


def _stale_progress_without_live_bash_sessions(status: StudyRuntimeStatus) -> bool:
    runtime_liveness_audit = _runtime_liveness_audit_payload(status)
    if not bool(runtime_liveness_audit.get("stale_progress")):
        return False
    if str(runtime_liveness_audit.get("liveness_guard_reason") or "").strip() != "stale_progress_watchdog":
        return False
    bash_session_audit = status.extras.get("bash_session_audit")
    if not isinstance(bash_session_audit, dict):
        return False
    if str(bash_session_audit.get("status") or "").strip() != "none":
        return False
    live_session_count = bash_session_audit.get("live_session_count")
    if live_session_count is None:
        return True
    try:
        return int(live_session_count) == 0
    except (TypeError, ValueError):
        return False


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
        "continuation_anchor": (
            str(continuation_state.get("continuation_anchor") or "").strip() or None
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


def _status_family_human_gates(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    event_time: str,
) -> list[dict[str, object]]:
    gates: list[dict[str, object]] = []
    pending_interaction = status.extras.get("pending_user_interaction")
    interaction_arbitration = status.extras.get("interaction_arbitration")
    pending_interaction_id = (
        str(pending_interaction.get("interaction_id") or "").strip()
        if isinstance(pending_interaction, dict)
        else ""
    )
    pending_interaction_ref = (
        str(pending_interaction.get("source_artifact_path") or "").strip()
        if isinstance(pending_interaction, dict)
        else ""
    )
    pending_interaction_requires_human_gate = True
    if isinstance(interaction_arbitration, dict):
        pending_interaction_requires_human_gate = bool(interaction_arbitration.get("requires_user_input"))
    if pending_interaction_id and pending_interaction_requires_human_gate:
        pending_decisions = (
            [
                str(item).strip()
                for item in (pending_interaction.get("pending_decisions") or [])
                if str(item).strip()
            ]
            if isinstance(pending_interaction, dict)
            else []
        )
        gates.append(
            family_orchestration.build_family_human_gate(
                gate_id=f"status-waiting-{status.study_id}-{pending_interaction_id}",
                gate_kind="runtime_pending_user_interaction",
                requested_at=event_time,
                request_surface_kind="study_runtime_status",
                request_surface_id="study_runtime_status",
                evidence_refs=[
                    {
                        "ref_kind": "repo_path",
                        "ref": pending_interaction_ref,
                        "label": "pending_user_interaction",
                    }
                ]
                if pending_interaction_ref
                else [],
                decision_options=pending_decisions or ["reply"],
            )
        )

    controller_requires_human_confirmation = _controller_decision_requires_human_confirmation(study_root=study_root)
    publication_requires_human_confirmation = _publication_supervisor_requires_human_confirmation(status)
    if controller_requires_human_confirmation or publication_requires_human_confirmation:
        gates.append(
            family_orchestration.build_family_human_gate(
                gate_id=f"status-human-confirmation-{status.study_id}",
                gate_kind="controller_human_confirmation",
                requested_at=event_time,
                request_surface_kind="study_runtime_status",
                request_surface_id="study_runtime_status",
                evidence_refs=[
                    {
                        "ref_kind": "repo_path",
                        "ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                        "label": "controller_decision_latest",
                    }
                ],
                decision_options=["approve", "request_changes", "reject"],
            )
        )
    return gates


def _record_family_orchestration_companion(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
) -> None:
    event_time = _router_module()._utc_now()
    snapshot = _runtime_event_status_snapshot(status)
    runtime_decision = status.decision.value if status.decision is not None else None
    runtime_reason = status.reason.value if status.reason is not None else None
    active_run_id = family_orchestration.resolve_active_run_id(
        snapshot.get("active_run_id"),
        ((status.extras.get("autonomous_runtime_notice") or {}) if isinstance(status.extras.get("autonomous_runtime_notice"), dict) else {}).get("active_run_id"),
        ((status.extras.get("execution_owner_guard") or {}) if isinstance(status.extras.get("execution_owner_guard"), dict) else {}).get("active_run_id"),
    )
    quest_root = Path(status.quest_root).expanduser().resolve()
    runtime_event_ref = status.extras.get("runtime_event_ref")
    runtime_event_artifact_path = (
        str(runtime_event_ref.get("artifact_path") or "").strip()
        if isinstance(runtime_event_ref, dict)
        else ""
    )
    runtime_escalation_ref = status.extras.get("runtime_escalation_ref")
    runtime_escalation_path = (
        str(runtime_escalation_ref.get("artifact_path") or "").strip()
        if isinstance(runtime_escalation_ref, dict)
        else ""
    )
    human_gates = _status_family_human_gates(
        status=status,
        study_root=study_root,
        event_time=event_time,
    )
    family_payload = family_orchestration.build_family_orchestration_companion(
        surface_kind="study_runtime_status",
        surface_id="study_runtime_status",
        event_name=f"study_runtime_status.{runtime_decision or 'observed'}",
        source_surface=str(
            status.execution.get("executor_kind")
            or status.execution.get("executor")
            or "codex_cli_autonomous"
        ),
        session_id=f"study-runtime:{status.study_id}",
        program_id=family_orchestration.resolve_program_id(status.execution),
        study_id=status.study_id,
        quest_id=status.quest_id,
        active_run_id=active_run_id,
        runtime_decision=runtime_decision,
        runtime_reason=runtime_reason,
        payload={
            "entry_mode": status.entry_mode,
            "quest_status": status.quest_status.value if status.quest_status is not None else None,
            "runtime_liveness_status": snapshot.get("runtime_liveness_status"),
            "supervisor_tick_status": snapshot.get("supervisor_tick_status"),
            "controller_owned_finalize_parking": snapshot.get("controller_owned_finalize_parking"),
        },
        event_time=event_time,
        checkpoint_id=f"study-runtime-status:{status.study_id}:{runtime_decision or 'unknown'}",
        checkpoint_label="study_runtime_status snapshot",
        audit_refs=[
            {
                "ref_kind": "repo_path",
                "ref": runtime_event_artifact_path,
                "label": "runtime_event_latest",
            }
            if runtime_event_artifact_path
            else {},
            {
                "ref_kind": "repo_path",
                "ref": runtime_escalation_path,
                "label": "runtime_escalation_record",
            }
            if runtime_escalation_path
            else {},
            {
                "ref_kind": "repo_path",
                "ref": str(quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"),
                "label": "runtime_watch_latest",
            },
        ],
        state_refs=[
            {
                "role": "status",
                "ref_kind": "repo_path",
                "ref": str(runtime_context.launch_report_path),
                "label": "last_launch_report",
            },
            {
                "role": "audit",
                "ref_kind": "repo_path",
                "ref": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "label": "runtime_supervision_latest",
            },
            {
                "role": "controller",
                "ref_kind": "repo_path",
                "ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                "label": "controller_decisions_latest",
            },
        ],
        restoration_evidence=[
            {
                "role": "artifact",
                "ref_kind": "repo_path",
                "ref": runtime_event_artifact_path,
                "label": "runtime_event",
            }
        ]
        if runtime_event_artifact_path
        else [],
        action_graph_id="mas_runtime_orchestration",
        node_id="study_runtime_status",
        gate_id=(human_gates[0].get("gate_id") if human_gates else None),
        resume_mode="reenter_human_gate" if human_gates else "resume_from_checkpoint",
        resume_handle=f"study_runtime_status:{status.study_id}:{runtime_decision or 'unknown'}",
        human_gate_required=bool(human_gates),
        human_gates=human_gates,
    )
    status.extras["family_event_envelope"] = family_payload["family_event_envelope"]
    status.extras["family_checkpoint_lineage"] = family_payload["family_checkpoint_lineage"]
    status.extras["family_human_gates"] = family_payload["family_human_gates"]


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
    runtime_backend=None,
) -> None:
    execution = status.execution
    if (
        runtime_backend is None
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
            runtime_backend=runtime_backend,
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
    current_publication_supervisor_state = (
        dict(status.extras.get("publication_supervisor_state") or {})
        if isinstance(status.extras.get("publication_supervisor_state"), dict)
        else {}
    )
    launch_report_path = runtime_context.launch_report_path
    launch_report_payload = _load_json_dict(launch_report_path) if launch_report_path.exists() else {}
    launch_report_exists = launch_report_path.exists()
    launch_report_quest_status = str(launch_report_payload.get("quest_status") or "").strip() or None
    launch_report_active_run_id = str(launch_report_payload.get("active_run_id") or "").strip() or None
    launch_report_runtime_liveness_status = _launch_report_runtime_liveness_status(launch_report_payload)
    launch_report_supervisor_tick_status = _launch_report_supervisor_tick_status(launch_report_payload)
    launch_report_publication_supervisor_state = (
        dict(launch_report_payload.get("publication_supervisor_state") or {})
        if isinstance(launch_report_payload.get("publication_supervisor_state"), dict)
        else {}
    )
    aligned = launch_report_exists and (
        launch_report_quest_status == current_quest_status
        and launch_report_active_run_id == current_active_run_id
        and launch_report_runtime_liveness_status == current_runtime_liveness_status
        and launch_report_supervisor_tick_status == current_supervisor_tick_status
        and launch_report_publication_supervisor_state == current_publication_supervisor_state
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
    elif launch_report_publication_supervisor_state != current_publication_supervisor_state:
        mismatch_reason = "launch_report_publication_supervisor_state_mismatch"
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


def _should_refresh_runtime_supervision_from_status(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
) -> bool:
    latest_report_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    latest_report = _read_json_mapping(latest_report_path)
    if latest_report is None:
        return False
    status_payload = status.to_dict()
    facts = runtime_supervision_controller._runtime_facts(status_payload)
    strict_live = bool(facts["strict_live"])
    decision = str(status_payload.get("decision") or "").strip() or None
    reason = str(status_payload.get("reason") or "").strip() or None
    quest_status = str(status_payload.get("quest_status") or "").strip() or None
    if strict_live:
        target_health_status = "live"
    elif runtime_supervision_controller._needs_drop_detection(status_payload, strict_live=strict_live):
        target_health_status = "degraded"
    else:
        return False
    return any(
        (
            (str(latest_report.get("health_status") or "").strip() or None) != target_health_status,
            (str(latest_report.get("active_run_id") or "").strip() or None) != facts["active_run_id"],
            (str(latest_report.get("runtime_liveness_status") or "").strip() or None)
            != facts["runtime_liveness_status"],
            (str(latest_report.get("runtime_decision") or "").strip() or None) != decision,
            (str(latest_report.get("runtime_reason") or "").strip() or None) != reason,
            (str(latest_report.get("quest_status") or "").strip() or None) != quest_status,
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


def _controller_stop_source(stop_reason: str | None) -> str | None:
    normalized = str(stop_reason or "").strip()
    if not normalized.startswith("controller_stop:"):
        return None
    source = normalized.split(":", 1)[1].strip()
    return source or None


def _controller_stop_is_auto_recoverable(
    *,
    stop_reason: str | None,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    stop_source = _controller_stop_source(stop_reason)
    if stop_source not in _AUTO_RECOVERY_CONTROLLER_STOP_SOURCES:
        return False
    return _publication_supervisor_requests_automated_continuation(
        publication_gate_report,
        require_blocked_status=True,
    ) or _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report)


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _stopped_controller_owned_auto_recovery_context(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
    publication_gate_report: dict[str, object] | None,
) -> dict[str, str | None] | None:
    if status.quest_status is not StudyRuntimeQuestStatus.STOPPED:
        return None
    publication_gate_status = str((publication_gate_report or {}).get("status") or "").strip() or None
    if publication_gate_status is None or _publication_supervisor_requires_human_confirmation(status):
        return None
    runtime_state = _load_json_dict(_runtime_state_path(quest_root))
    continuation_policy = str(runtime_state.get("continuation_policy") or "").strip() or None
    continuation_anchor = str(runtime_state.get("continuation_anchor") or "").strip() or None
    continuation_reason = str(runtime_state.get("continuation_reason") or "").strip() or None
    stop_reason = str(runtime_state.get("stop_reason") or "").strip() or None
    if continuation_policy != "auto":
        return None
    recovery_mode: str | None = None
    pending_user_message_count = _int_or_none(runtime_state.get("pending_user_message_count"))
    if stop_reason == "user_stop":
        if (
            continuation_reason is not None
            and continuation_reason.startswith("decision:")
            and pending_user_message_count is not None
            and pending_user_message_count > 0
        ):
            recovery_mode = "managed_auto_continuation"
        else:
            return None
    elif stop_reason and not stop_reason.startswith("controller_stop:"):
        return None
    elif continuation_anchor == "decision" and continuation_reason is not None and continuation_reason.startswith("decision:"):
        recovery_mode = "decision"
    if recovery_mode is None and _controller_stop_is_auto_recoverable(
        stop_reason=stop_reason,
        publication_gate_report=publication_gate_report,
    ):
        recovery_mode = "controller_guard"
    if recovery_mode is None:
        return None
    return {
        "active_interaction_id": str(runtime_state.get("active_interaction_id") or "").strip() or None,
        "stop_reason": stop_reason,
        "continuation_reason": continuation_reason,
        "recovery_mode": recovery_mode,
    }


def _task_intake_override_allows_stopped_auto_resume(*, quest_root: Path) -> bool:
    runtime_state = _load_json_dict(_runtime_state_path(quest_root))
    stop_reason = str(runtime_state.get("stop_reason") or "").strip() or None
    return stop_reason is None


def _stopped_invalid_blocking_auto_resume_allowed(
    *, stopped_recovery_context: dict[str, str | None] | None
) -> bool:
    if not isinstance(stopped_recovery_context, dict):
        return False
    stop_reason = str(stopped_recovery_context.get("stop_reason") or "").strip() or None
    return stop_reason is None


def _pending_user_interaction_payload(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    runtime_backend=None,
    fallback_interaction_id: str | None = None,
) -> dict[str, object] | None:
    session_payload: dict[str, object] = {}
    if runtime_backend is not None:
        try:
            raw_session_payload = runtime_backend.get_quest_session(
                runtime_root=runtime_root,
                quest_id=quest_id,
            )
        except (RuntimeError, OSError, ValueError):
            raw_session_payload = {}
        if isinstance(raw_session_payload, dict):
            session_payload = raw_session_payload
    snapshot = session_payload.get("snapshot")
    if not isinstance(snapshot, dict):
        snapshot = {}
    waiting_interaction_id = str(snapshot.get("waiting_interaction_id") or "").strip() or None
    default_reply_interaction_id = str(snapshot.get("default_reply_interaction_id") or "").strip() or None
    active_interaction_id = str(snapshot.get("active_interaction_id") or "").strip() or None
    raw_pending_decisions = snapshot.get("pending_decisions")
    pending_decisions = (
        [str(item).strip() for item in raw_pending_decisions if str(item).strip()]
        if isinstance(raw_pending_decisions, list)
        else []
    )
    interaction_id = (
        waiting_interaction_id
        or default_reply_interaction_id
        or (pending_decisions[0] if pending_decisions else None)
        or active_interaction_id
        or (str(fallback_interaction_id or "").strip() or None)
    )
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
    submission_metadata_only = _waiting_submission_metadata_only(quest_root)
    guidance_requires_user_decision = (
        artifact_payload.get("guidance_vm", {}).get("requires_user_decision")
        if isinstance(artifact_payload.get("guidance_vm"), dict)
        else None
    )
    if submission_metadata_only and guidance_requires_user_decision is not True:
        guidance_requires_user_decision = True
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
        "guidance_requires_user_decision": guidance_requires_user_decision,
        "source_artifact_path": str(interaction_artifact_path) if interaction_artifact_path is not None else None,
        "relay_required": True,
    }


def _record_pending_user_interaction_if_required(
    *,
    status: StudyRuntimeStatus,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    publication_gate_report: dict[str, object] | None,
    runtime_backend=None,
) -> None:
    stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
        status=status,
        quest_root=quest_root,
        publication_gate_report=publication_gate_report,
    )
    if (
        status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not _is_controller_owned_finalize_parking(status)
        and stopped_recovery_context is None
    ):
        return
    payload = _pending_user_interaction_payload(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        runtime_backend=runtime_backend,
        fallback_interaction_id=(
            str(stopped_recovery_context.get("active_interaction_id") or "").strip()
            if isinstance(stopped_recovery_context, dict)
            else None
        ),
    )
    if payload is None:
        return
    status.record_pending_user_interaction(payload)


def _record_interaction_arbitration_if_required(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
    execution: dict[str, object],
    submission_metadata_only: bool,
    publication_gate_report: dict[str, object] | None,
) -> None:
    stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
        status=status,
        quest_root=quest_root,
        publication_gate_report=publication_gate_report,
    )
    if (
        status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not _is_controller_owned_finalize_parking(status)
        and stopped_recovery_context is None
    ):
        return
    payload = status.extras.get("pending_user_interaction")
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
    execution = router._execution_payload(study_payload, profile=profile)
    explicit_runtime_backend_id = runtime_backend_contract.explicit_runtime_backend_id(execution)
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
    managed_runtime_backend = router._managed_runtime_backend_for_execution(
        execution,
        profile=profile,
        runtime_root=runtime_root,
    )
    if managed_runtime_backend is not None:
        execution = dict(execution)
        execution.setdefault("runtime_backend_id", getattr(managed_runtime_backend, "BACKEND_ID", ""))
        execution.setdefault("runtime_backend", getattr(managed_runtime_backend, "BACKEND_ID", ""))
        execution.setdefault("runtime_engine_id", getattr(managed_runtime_backend, "ENGINE_ID", ""))
    quest_runtime = quest_state.inspect_quest_runtime(quest_root)
    quest_exists = quest_runtime.quest_exists
    quest_status = StudyRuntimeStatus._normalize_quest_status_field(quest_runtime.quest_status)
    if quest_status in _LIVE_QUEST_STATUSES and managed_runtime_backend is not None:
        runtime_liveness_audit = router._inspect_quest_live_execution(
            runtime_root=runtime_root,
            quest_id=quest_id,
            runtime_backend=managed_runtime_backend,
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
    task_intake_overrides_auto_manual_finish = _task_intake_overrides_auto_manual_finish_active(
        study_root=study_root,
    )
    submission_metadata_only_manual_finish = (
        quest_exists
        and not task_intake_overrides_auto_manual_finish
        and _submission_metadata_only_manual_finish_active(
            study_root=study_root,
            quest_root=quest_root,
        )
    )
    task_intake_yields_to_submission_closeout = False
    bundle_only_manual_finish = (
        quest_exists
        and (
            _bundle_only_submission_ready_manual_finish_active(
                study_root=study_root,
                quest_root=quest_root,
            )
            or _delivered_submission_package_manual_finish_active(study_root=study_root)
        )
    )
    if task_intake_overrides_auto_manual_finish and bundle_only_manual_finish:
        summary_payload = _load_json_dict(
            study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
        )
        task_intake_yields_to_submission_closeout = task_intake_yields_to_deterministic_submission_closeout(
            read_latest_task_intake(study_root=study_root),
            publishability_gate_report=None,
            evaluation_summary=summary_payload,
        )
        if not task_intake_yields_to_submission_closeout:
            bundle_only_manual_finish = False
    explicit_manual_finish_compatibility_guard = _explicit_manual_finish_compatibility_guard_active(
        study_root=study_root,
    )
    manual_finish_compatibility_guard = (
        explicit_manual_finish_compatibility_guard
        or submission_metadata_only_manual_finish
        or bundle_only_manual_finish
    )
    submission_metadata_only_wait = (
        quest_exists
        and quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not task_intake_overrides_auto_manual_finish
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
    task_intake_yields_to_submission_closeout = task_intake_yields_to_submission_closeout or _task_intake_yields_to_submission_closeout_active(
        study_root=study_root,
        publication_gate_report=publication_gate_report,
    )
    _record_continuation_state_if_present(status=result, quest_root=quest_root)
    _record_pending_user_interaction_if_required(
        status=result,
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        publication_gate_report=publication_gate_report,
        runtime_backend=managed_runtime_backend,
    )
    _record_interaction_arbitration_if_required(
        status=result,
        quest_root=quest_root,
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
        if _should_refresh_runtime_supervision_from_status(status=result, study_root=study_root):
            runtime_supervision_controller.materialize_runtime_supervision(
                study_root=study_root,
                status_payload=result.to_dict(),
                recorded_at=router._utc_now(),
                apply=False,
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
            runtime_backend=managed_runtime_backend,
        )
        _record_family_orchestration_companion(
            status=result,
            study_root=study_root,
            runtime_context=runtime_context,
        )
        return result

    if explicit_runtime_backend_id is not None and managed_runtime_backend is None:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_EXECUTION_RUNTIME_BACKEND_UNBOUND,
        )
        return _finalize_result()

    if managed_runtime_backend is None:
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED_RUNTIME_BACKEND,
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
    study_charter_gate_reason = _study_charter_gate_reason(publication_gate_report)
    if study_charter_gate_reason is not None:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            study_charter_gate_reason,
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
            if manual_finish_compatibility_guard:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
                return _finalize_result()
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

    if manual_finish_compatibility_guard and quest_status not in _LIVE_QUEST_STATUSES:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
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
            if manual_finish_compatibility_guard:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
            elif _stale_progress_without_live_bash_sessions(result):
                if not result.startup_boundary_allows_compute_stage:
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
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED,
                )
        elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
            if manual_finish_compatibility_guard:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
            elif _publication_gate_requires_live_runtime_reroute(
                publication_gate_report,
                status=result,
            ):
                if execution.get("auto_resume") is True:
                    result.set_decision(
                        StudyRuntimeDecision.RESUME,
                        StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL,
                    )
                else:
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                    )
            elif _publication_gate_allows_live_runtime_write_stage_resume(
                status=result,
                publication_gate_report=publication_gate_report,
            ):
                if execution.get("auto_resume") is True:
                    result.set_decision(
                        StudyRuntimeDecision.RESUME,
                        StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY,
                    )
                else:
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                    )
            elif not result.startup_boundary_allows_compute_stage:
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
            if submission_metadata_only_manual_finish:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
                return _finalize_result()
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
        if submission_metadata_only_manual_finish or bundle_only_manual_finish:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
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
        if submission_metadata_only_manual_finish or bundle_only_manual_finish:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
        stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
            status=result,
            quest_root=quest_root,
            publication_gate_report=publication_gate_report,
        )
        interaction_arbitration = result.extras.get("interaction_arbitration")
        if (
            isinstance(stopped_recovery_context, dict)
            and str(stopped_recovery_context.get("recovery_mode") or "").strip() == "controller_guard"
        ):
            post_clear_continuation = _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report)
            if not result.startup_boundary_allows_compute_stage:
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
                    (
                        StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY
                        if post_clear_continuation
                        else StudyRuntimeReason.QUEST_STOPPED_BY_CONTROLLER_GUARD
                    ),
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
                )
            return _finalize_result()
        if stopped_recovery_context is not None and isinstance(interaction_arbitration, dict):
            classification = str(interaction_arbitration.get("classification") or "").strip()
            action = str(interaction_arbitration.get("action") or "").strip()
            if action == "resume" and (
                classification != "invalid_blocking"
                or _stopped_invalid_blocking_auto_resume_allowed(stopped_recovery_context=stopped_recovery_context)
            ):
                if not result.startup_boundary_allows_compute_stage:
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
                else:
                    blocked_reason = (
                        StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA_BUT_AUTO_RESUME_DISABLED
                        if classification == "submission_metadata_only"
                        else StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED
                    )
                    result.set_decision(
                        StudyRuntimeDecision.BLOCKED,
                        blocked_reason,
                    )
                return _finalize_result()
            if classification == "external_input_required":
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
                )
                return _finalize_result()
        if (
            isinstance(stopped_recovery_context, dict)
            and str(stopped_recovery_context.get("recovery_mode") or "").strip() == "managed_auto_continuation"
        ):
            if not result.startup_boundary_allows_compute_stage:
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
                    StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
                )
            return _finalize_result()
        if (
            task_intake_overrides_auto_manual_finish
            and not task_intake_yields_to_submission_closeout
            and _task_intake_override_allows_stopped_auto_resume(
            quest_root=quest_root
        )
        ):
            if not result.startup_boundary_allows_compute_stage:
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
                    StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
                )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
        )
        return _finalize_result()

    if quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER:
        if submission_metadata_only_wait and submission_metadata_only_manual_finish:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return _finalize_result()
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
