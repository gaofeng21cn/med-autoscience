from __future__ import annotations

from med_autoscience.publication_eval_record import (
    PublicationEvalQualityAssessment,
    PublicationEvalQualityDimension,
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


def _quality_dimension(
    *,
    status: str,
    summary: str,
    evidence_refs: tuple[str, ...],
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


def _clinical_significance_dimension(
    *,
    publication_objective: str,
    paper_framing_summary: str,
    clinician_facing_target_declared: bool,
    results_summary: str,
    conclusion: str,
    evidence_refs: tuple[str, ...],
) -> PublicationEvalQualityDimension:
    if not (publication_objective or paper_framing_summary):
        return _quality_dimension(
            status="underdefined",
            summary="Study charter 还没有冻结明确的临床论文 framing，临床意义表述仍不够稳。",
            evidence_refs=evidence_refs,
            reviewer_reason="当前 charter 还没冻结临床论文 framing，临床意义判读依据不足。",
            reviewer_revision_advice="先在 charter 固定 publication_objective 或 paper_framing_summary，再回到结果叙事。",
            reviewer_next_round_focus="确认临床问题定义、目标人群与预期结论边界是否写入 charter。",
        )
    if not (results_summary or conclusion):
        return _quality_dimension(
            status="partial",
            summary="临床问题已经被冻结，但当前 gate 还没有稳定的结果/结论表面来支撑给人阅读的临床叙事。",
            evidence_refs=evidence_refs,
            reviewer_reason="临床问题已定义，但当前缺少稳定结果/结论表面支撑临床叙事。",
            reviewer_revision_advice="先补齐可引用的结果摘要或结论段，再组织临床意义叙事。",
            reviewer_next_round_focus="核对结果摘要是否能直接回答临床问题并支撑结论措辞。",
        )
    if clinician_facing_target_declared:
        return _quality_dimension(
            status="ready",
            summary="临床问题、解释目标与结果表面都已经具备，临床意义叙事已进入可审状态。",
            evidence_refs=evidence_refs,
            reviewer_reason="临床问题、解释目标与结果表面已对齐，当前维度达到可审状态。",
            reviewer_revision_advice="保持当前叙事结构，优先做事实一致性与术语统一检查。",
            reviewer_next_round_focus="下一轮重点核对临床解释段与关键结果引用是否逐条一致。",
        )
    return _quality_dimension(
        status="partial",
        summary="主临床问题与结果表面已具备，但 charter 里还缺更显式的 clinician-facing interpretation target。",
        evidence_refs=evidence_refs,
        reviewer_reason="主临床问题与结果表面已具备，但 clinician-facing interpretation target 仍未显式冻结。",
        reviewer_revision_advice="在 charter 补齐 clinician-facing interpretation target，再做临床叙事定稿。",
        reviewer_next_round_focus="下一轮重点确认解释目标是否能覆盖主临床结论的每一条关键陈述。",
    )


def _evidence_strength_dimension(
    *,
    blockers: set[str],
    medical_surface_status: str,
    report_status: str,
    delivery_only_blockers: bool,
    evidence_refs: tuple[str, ...],
) -> PublicationEvalQualityDimension:
    if "missing_publication_anchor" in blockers:
        return _quality_dimension(
            status="blocked",
            summary="主科学锚点还没建立，证据链还不能作为论文主叙事放行。",
            evidence_refs=evidence_refs,
            reviewer_reason="缺少可发布主锚点，证据链当前不完整。",
            reviewer_revision_advice="先补齐 main result/publishability anchor，再回到 claim-to-evidence 审阅。",
            reviewer_next_round_focus="下一轮优先验证主锚点、关键指标与结论引用的可追溯性。",
        )
    if medical_surface_status != "clear" or {
        "medical_publication_surface_blocked",
        "missing_current_medical_publication_surface_report",
    } & blockers:
        return _quality_dimension(
            status="blocked",
            summary="论文稿面的证据链还没有清关，claim-to-evidence 或 paper-facing reporting 仍需修复。",
            evidence_refs=evidence_refs,
            reviewer_reason="稿面证据链仍未清关，claim-to-evidence 或 paper-facing reporting 存在阻塞。",
            reviewer_revision_advice="按 blocker 顺序修复稿面证据链与 reporting 缺口，再提交审阅。",
            reviewer_next_round_focus="下一轮重点检查 medical publication surface 报告是否 clear 且 blockers 清零。",
        )
    if report_status == "clear" or delivery_only_blockers:
        return _quality_dimension(
            status="ready",
            summary="科学证据面已经清楚，剩余问题只在交付/刷新层，不在核心证据层。",
            evidence_refs=evidence_refs,
            reviewer_reason="核心科学证据链已经清楚，当前剩余问题位于交付/刷新层。",
            reviewer_revision_advice="核心证据链已达标，下一轮优先清理交付与刷新层阻塞，避免再次影响审阅入口。",
            reviewer_next_round_focus="下一轮重点确认 current package 与 submission surfaces 的刷新时序。",
        )
    return _quality_dimension(
        status="partial",
        summary="主结果和稿面证据已存在，但 publication gate 仍有非纯交付类缺口没有清完。",
        evidence_refs=evidence_refs,
        reviewer_reason="主结果和稿面证据已存在，但 publication gate 仍有非交付类缺口未闭合。",
        reviewer_revision_advice="继续消除非交付类 blocker 并补证据引用链，再申请放行。",
        reviewer_next_round_focus="下一轮重点复核非交付 blockers 的证据闭环。",
    )


def _novelty_positioning_dimension(
    *,
    scientific_followup_questions: tuple[str, ...],
    explanation_targets: tuple[str, ...],
    manuscript_conclusion_redlines: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> PublicationEvalQualityDimension:
    if scientific_followup_questions and explanation_targets:
        return _quality_dimension(
            status="ready",
            summary="Charter 已显式冻结 follow-up questions 和 explanation targets，创新点/贡献边界有正式审计锚点。",
            evidence_refs=evidence_refs,
            reviewer_reason="follow-up questions 与 explanation targets 已冻结，贡献边界具备审计锚点。",
            reviewer_revision_advice="保持当前创新叙事结构，避免超出已冻结边界的扩展表述。",
            reviewer_next_round_focus="下一轮重点校对创新点描述与 follow-up questions 的对应关系。",
        )
    if scientific_followup_questions or explanation_targets or manuscript_conclusion_redlines:
        return _quality_dimension(
            status="partial",
            summary="贡献边界已经开始结构化，但 novelty/解释目标还没有完全收成一套显式质量合同。",
            evidence_refs=evidence_refs,
            reviewer_reason="贡献边界已开始结构化，但 novelty 与解释目标合同尚未完整闭合。",
            reviewer_revision_advice="补齐缺失的 follow-up questions/explanation targets，使贡献边界可审计。",
            reviewer_next_round_focus="下一轮重点检查创新性叙事是否能被 charter 字段逐条追溯。",
        )
    return _quality_dimension(
        status="underdefined",
        summary="当前 charter 还缺显式的 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
        evidence_refs=evidence_refs,
        reviewer_reason="当前 charter 缺少显式 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
        reviewer_revision_advice="先在 charter 增补可审计的 scientific follow-up questions 或 explanation targets。",
        reviewer_next_round_focus="补齐 scientific follow-up questions 或 explanation targets，再复核创新叙事与主结论边界。",
    )


def _human_review_readiness_dimension(
    *,
    report_status: str,
    study_delivery_status: str,
    submission_minimal_ready: bool,
    evidence_refs: tuple[str, ...],
) -> PublicationEvalQualityDimension:
    if report_status == "clear" and study_delivery_status == "current" and submission_minimal_ready:
        return _quality_dimension(
            status="ready",
            summary="给人看的 current_package 和 submission_minimal 已同步到最新真相，可以进入人工审阅。",
            evidence_refs=evidence_refs,
            reviewer_reason="current_package 与 submission_minimal 已同步到最新真相，人工审阅入口已就绪。",
            reviewer_revision_advice="保持当前交付状态并仅做事实一致性修订。",
            reviewer_next_round_focus="下一轮重点复核审阅包中的引用路径与提交清单一致性。",
        )
    if report_status == "clear":
        return _quality_dimension(
            status="partial",
            summary="科学 gate 已清，但给人看的 current_package 或 submission surface 还需要再同步一轮。",
            evidence_refs=evidence_refs,
            reviewer_reason="科学 gate 已清，但 current_package 或 submission surface 仍需同步。",
            reviewer_revision_advice="补齐交付面同步后再提交人工审阅，避免审阅基线漂移。",
            reviewer_next_round_focus="下一轮重点确认 submission_minimal 三件套与 current_package 时间戳一致。",
        )
    return _quality_dimension(
        status="blocked",
        summary="publication gate 还没清，当前还不能把稿件当作正式人工审阅包放行。",
        evidence_refs=evidence_refs,
        reviewer_reason="publication gate 尚未清关，当前稿件还不能作为正式人工审阅包放行。",
        reviewer_revision_advice="先关闭 publication gate blockers，再准备人工审阅包。",
        reviewer_next_round_focus="下一轮重点核对 gate 状态是否 clear 且关键 blocker 全部移除。",
    )


def _medical_journal_prose_dimension(
    *,
    report: dict[str, object],
    evidence_refs: tuple[str, ...],
) -> PublicationEvalQualityDimension:
    medical_prose_review_status = str(report.get("medical_prose_review_status") or "").strip()
    medical_prose_review_summary = str(report.get("medical_prose_review_summary") or "").strip()
    medical_prose_review_ref = str(report.get("medical_prose_review_path") or "").strip()
    if not medical_prose_review_status:
        medical_prose_review_status = "underdefined"
    if not medical_prose_review_summary:
        medical_prose_review_summary = (
            "Gate materialization is mechanical; AI reviewer must judge medical journal prose "
            "from the manuscript, blueprint, style contract, claim-evidence map, results narrative, "
            "figure semantics, and review ledger before quality closure."
        )
    prose_evidence_refs = evidence_refs
    if medical_prose_review_ref and medical_prose_review_ref not in prose_evidence_refs:
        prose_evidence_refs = (*evidence_refs, medical_prose_review_ref)
    return PublicationEvalQualityDimension(
        status=medical_prose_review_status,
        summary=medical_prose_review_summary,
        evidence_refs=prose_evidence_refs,
        reviewer_reason=(
            "Mechanical publication-gate projection cannot authorize subjective manuscript prose quality."
        ),
        reviewer_revision_advice=(
            "Route the manuscript through an AI prose review and consume its representative rewrites "
            "before full-draft quality closure."
        ),
        reviewer_next_round_focus=(
            "Confirm medical journal voice, reader flow, paragraph argumentation, claim restraint, "
            "and absence of work-report residue."
        ),
    )


def publication_eval_quality_assessment(
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
    submission_minimal_ready = (
        bool(report.get("submission_minimal_present"))
        and bool(report.get("submission_minimal_docx_present"))
        and bool(report.get("submission_minimal_pdf_present"))
    )
    clinician_facing_target_declared = (
        bool(explanation_targets)
        or "clinician_facing_interpretation_block" in minimum_sci_ready_evidence_package
    )

    return PublicationEvalQualityAssessment(
        clinical_significance=_clinical_significance_dimension(
            publication_objective=publication_objective,
            paper_framing_summary=paper_framing_summary,
            clinician_facing_target_declared=clinician_facing_target_declared,
            results_summary=results_summary,
            conclusion=conclusion,
            evidence_refs=evidence_refs,
        ),
        evidence_strength=_evidence_strength_dimension(
            blockers=blockers,
            medical_surface_status=medical_surface_status,
            report_status=report_status,
            delivery_only_blockers=_publication_eval_has_only_delivery_blockers(report),
            evidence_refs=evidence_refs,
        ),
        novelty_positioning=_novelty_positioning_dimension(
            scientific_followup_questions=scientific_followup_questions,
            explanation_targets=explanation_targets,
            manuscript_conclusion_redlines=manuscript_conclusion_redlines,
            evidence_refs=evidence_refs,
        ),
        medical_journal_prose_quality=_medical_journal_prose_dimension(
            report=report,
            evidence_refs=evidence_refs,
        ),
        human_review_readiness=_human_review_readiness_dimension(
            report_status=report_status,
            study_delivery_status=study_delivery_status,
            submission_minimal_ready=submission_minimal_ready,
            evidence_refs=evidence_refs,
        ),
    )

