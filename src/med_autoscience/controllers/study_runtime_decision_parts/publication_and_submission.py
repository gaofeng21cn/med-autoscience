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
