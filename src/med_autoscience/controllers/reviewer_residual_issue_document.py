from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


MAX_AUTOMATED_REVIEW_REPAIR_ROUNDS = 3
SURFACE_KIND = "bounded_reviewer_repair_residual_user_review"
SCHEMA_VERSION = 1

_BLOCKING_GAP_SEVERITIES = frozenset({"must_fix", "important"})
_LEGAL_HARD_REVIEW_GATE_KINDS = frozenset(
    {
        "zero_consumable_artifact",
        "artifact_corrupt_or_unreadable",
        "safety_or_compliance",
        "permission_or_credential_boundary",
        "human_or_expert_gate",
        "artifact_mutation_authority_gate",
        "authority_boundary_violation",
        "forbidden_write_guard",
        "stale_or_mismatched_stage_identity",
    }
)


def build_bounded_review_repair_policy(
    *,
    publication_eval: Mapping[str, Any],
    authority_blockers: list[str],
    accept_blockers: list[str],
    required_calibration_refs: list[str],
    worklog: list[dict[str, Any]],
    round_sources: list[tuple[str, object]] | None = None,
) -> dict[str, Any]:
    round_state = review_repair_round_state(
        publication_eval,
        round_sources=round_sources,
    )
    hard_blockers = hard_review_blockers(
        publication_eval=publication_eval,
        authority_blockers=authority_blockers,
        required_calibration_refs=required_calibration_refs,
    )
    residual_issues = residual_issues_from_worklog(worklog)
    quality_claim_authority_blocked = bool(authority_blockers)
    no_clear_actionable_issues = bool(accept_blockers) and not residual_issues
    repair_round_budget_exhausted = bool(residual_issues) and round_state["current_round"] >= round_state["max_rounds"]
    budget_exhausted = repair_round_budget_exhausted and not hard_blockers
    auto_advance_allowed = not hard_blockers
    if hard_blockers:
        status = "hard_blocked"
        next_action = "resolve_hard_reviewer_blocker"
    elif quality_claim_authority_blocked or required_calibration_refs:
        status = "auto_advance_with_reviewer_authority_or_calibration_debt"
        next_action = "advance_and_route_back_reviewer_debt"
    elif no_clear_actionable_issues:
        status = "auto_advance_no_clear_actionable_reviewer_issue"
        next_action = "advance_to_next_stage"
    elif budget_exhausted:
        status = "auto_advance_with_residual_user_review"
        next_action = "advance_to_next_stage_with_residual_user_review"
    elif accept_blockers:
        status = "auto_advance_with_repair_budget_available"
        next_action = "advance_and_optionally_continue_bounded_repair_recheck"
    else:
        status = "accepted"
        next_action = "advance_to_next_stage"
    return {
        "surface_kind": "bounded_reviewer_repair_policy",
        "schema_version": SCHEMA_VERSION,
        "max_automated_repair_rounds": round_state["max_rounds"],
        "current_round": round_state["current_round"],
        "remaining_rounds": max(round_state["max_rounds"] - round_state["current_round"], 0),
        "round_source": round_state["source"],
        "status": status,
        "next_action": next_action,
        "auto_advance_allowed": auto_advance_allowed,
        "no_clear_actionable_reviewer_issue": no_clear_actionable_issues,
        "budget_exhausted": budget_exhausted,
        "repair_round_budget_exhausted": repair_round_budget_exhausted,
        "strict_authority_blocked": False,
        "quality_claim_authority_blocked": quality_claim_authority_blocked,
        "required_calibration_refs_block_stage_progress": False,
        "residual_user_review_required": status == "auto_advance_with_residual_user_review",
        "residual_issue_count": len(residual_issues),
        "hard_blockers": hard_blockers,
        "hard_blocker_count": len(hard_blockers),
        "strict_accept_blockers": list(accept_blockers),
        "authority_boundary": {
            "can_authorize_publication_quality": False,
            "can_authorize_submission": False,
            "can_mutate_paper_body": False,
            "can_bypass_hard_gate": False,
            "residual_user_review_can_block_auto_advance": False,
            "authority_or_calibration_debt_can_block_auto_advance": False,
        },
    }


def build_residual_user_review_payload(
    *,
    study_id: str | None,
    quest_id: str | None,
    publication_eval: Mapping[str, Any],
    publication_eval_path: Path | str | None,
    worklog: list[dict[str, Any]],
    bounded_policy: Mapping[str, Any],
) -> dict[str, Any]:
    issues = residual_issues_from_worklog(worklog)
    required = (
        _text(bounded_policy.get("status")) == "auto_advance_with_residual_user_review"
        and bool(issues)
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "language": "zh-CN",
        "required": required,
        "status": "pending_user_review" if required else "not_required",
        "study_id": study_id,
        "quest_id": quest_id,
        "source_eval_id": _text(publication_eval.get("eval_id")),
        "source_eval_artifact_path": str(publication_eval_path) if publication_eval_path is not None else None,
        "max_automated_repair_rounds": bounded_policy.get("max_automated_repair_rounds"),
        "current_round": bounded_policy.get("current_round"),
        "policy_status": bounded_policy.get("status"),
        "auto_advance_allowed": bool(bounded_policy.get("auto_advance_allowed")),
        "issue_count": len(issues),
        "issues": issues,
        "user_decision_prompt": (
            "以下是自动 review/修订预算耗尽后仍保留的非硬阻塞意见。"
            "它们不应继续卡住论文进入下一阶段，但投稿前请人工判断哪些必须再修。"
        ),
        "authority_boundary": {
            "human_inspection_only": True,
            "can_authorize_publication_quality": False,
            "can_authorize_submission": False,
            "can_mutate_paper_body": False,
            "does_not_create_owner_receipt": True,
        },
    }


def render_residual_user_review_markdown(payload: Mapping[str, Any]) -> str:
    study_id = _text(payload.get("study_id")) or "unknown-study"
    source_eval_id = _text(payload.get("source_eval_id")) or "unknown-eval"
    issues = _list_of_mappings(payload.get("issues"))
    lines = [
        "# 残留 reviewer 意见人工审阅表",
        "",
        f"- Study: `{study_id}`",
        f"- Source eval: `{source_eval_id}`",
        f"- 自动修订轮次: `{payload.get('current_round')}` / `{payload.get('max_automated_repair_rounds')}`",
        "- 用途: 仅供人工判断残留意见，不是投稿授权、质量门关闭或 owner receipt。",
        "",
        "## 审阅说明",
        "",
        str(payload.get("user_decision_prompt") or "").strip(),
        "",
    ]
    if not issues:
        lines.extend(["## 残留意见", "", "无需要人工复核的残留 reviewer 意见。", ""])
        return "\n".join(lines)
    lines.extend(["## 残留意见", ""])
    for index, issue in enumerate(issues, start=1):
        evidence_refs = _text_list(issue.get("evidence_refs"))
        lines.extend(
            [
                f"### {index}. {_text(issue.get('summary')) or _text(issue.get('issue_id')) or '未命名意见'}",
                "",
                f"- 类型: `{_text(issue.get('kind')) or 'reviewer_issue'}`",
                f"- 严重程度: `{_text(issue.get('severity')) or '未标注'}`",
                f"- 目标位置: `{_text(issue.get('target_section')) or '未标注'}`",
                f"- 建议处理: {_text(issue.get('recommended_user_decision')) or '请判断是否必须修复。'}",
                "- 证据 refs:",
            ]
        )
        if evidence_refs:
            lines.extend(f"  - `{ref}`" for ref in evidence_refs)
        else:
            lines.append("  - 未提供")
        lines.append("")
    return "\n".join(lines)


def write_residual_user_review_artifacts(
    *,
    payload: Mapping[str, Any],
    markdown_path: Path,
    json_path: Path,
) -> dict[str, str]:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_residual_user_review_markdown(payload), encoding="utf-8")
    json_path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "residual_user_review_markdown": str(markdown_path.resolve()),
        "residual_user_review_json": str(json_path.resolve()),
    }


def review_repair_round_state(
    publication_eval: Mapping[str, Any],
    *,
    round_sources: list[tuple[str, object]] | None = None,
) -> dict[str, Any]:
    parsed_candidates: list[tuple[int, str]] = []
    for source, value in [*(round_sources or []), *_round_candidates(publication_eval)]:
        parsed = _positive_int(value)
        if parsed is not None:
            parsed_candidates.append((parsed, source))
    if parsed_candidates:
        current_round, source = max(parsed_candidates, key=lambda item: item[0])
        return {
            "current_round": current_round,
            "max_rounds": MAX_AUTOMATED_REVIEW_REPAIR_ROUNDS,
            "source": source,
        }
    return {
        "current_round": 1,
        "max_rounds": MAX_AUTOMATED_REVIEW_REPAIR_ROUNDS,
        "source": "default_first_round",
    }


def hard_review_blockers(
    *,
    publication_eval: Mapping[str, Any],
    authority_blockers: list[str],
    required_calibration_refs: list[str],
) -> list[str]:
    _ = required_calibration_refs
    blockers: list[str] = []
    blockers.extend(
        blocker
        for blocker in authority_blockers
        if "currentness_checks" in blocker
        or "source_fingerprint" in blocker
        or "stage_identity" in blocker
    )
    for gap in _list_of_mappings(publication_eval.get("gaps")):
        if _has_hard_gate_marker(gap):
            blockers.append(f"hard_reviewer_gap:{_text(gap.get('gap_id')) or _text(gap.get('summary')) or 'unnamed'}")
    for dimension, value in _mapping(publication_eval.get("quality_assessment")).items():
        item = _mapping(value)
        if _has_hard_gate_marker(item):
            blockers.append(f"hard_quality_dimension:{dimension}")
    return _dedupe_text(blockers)


def residual_issues_from_worklog(worklog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in worklog:
        if not _is_actionable_residual(item):
            continue
        issue_id = _text(item.get("concern_id")) or f"reviewer_issue:{len(issues) + 1}"
        evidence_refs = _dedupe_text(_text_list(item.get("evidence_refs")) + _text_list(item.get("artifact_refs")))
        issues.append(
            {
                "issue_id": issue_id,
                "kind": _text(item.get("kind")) or "reviewer_issue",
                "severity": _text(item.get("severity")) or _text(item.get("status")) or "unclassified",
                "target_section": _text(item.get("section")),
                "summary": _text(item.get("reviewer_concern")) or _text(item.get("summary")),
                "reviewer_revision_advice": _text(item.get("reviewer_revision_advice")),
                "evidence_refs": evidence_refs,
                "recommended_user_decision": "请判断该意见是否必须在投稿前继续修复；若不是硬阻塞，不应继续阻止进入下一阶段。",
                "auto_repair_budget_exhausted": True,
            }
        )
    return issues


def _round_candidates(publication_eval: Mapping[str, Any]) -> list[tuple[str, object]]:
    _ = publication_eval
    return []


def _is_actionable_residual(item: Mapping[str, Any]) -> bool:
    kind = _text(item.get("kind"))
    if kind == "quality_dimension":
        return _text(item.get("status")) not in {"", "ready"}
    if kind == "publication_gap":
        return _text(item.get("severity")) in _BLOCKING_GAP_SEVERITIES
    return False


def _has_hard_gate_marker(item: Mapping[str, Any]) -> bool:
    if item.get("requires_human_gate") is True:
        return True
    gate_kind = (
        _text(item.get("gate_kind"))
        or _text(item.get("gate"))
        or _text(item.get("blocker_type"))
    )
    return gate_kind in _LEGAL_HARD_REVIEW_GATE_KINDS


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        try:
            parsed = int(value.strip())
        except ValueError:
            return None
        return parsed if parsed > 0 else None
    return None


def _calibration_case_id(ref: str) -> str:
    return ref.rsplit("#", 1)[-1].strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _dedupe_text(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


__all__ = [
    "MAX_AUTOMATED_REVIEW_REPAIR_ROUNDS",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_bounded_review_repair_policy",
    "build_residual_user_review_payload",
    "hard_review_blockers",
    "render_residual_user_review_markdown",
    "residual_issues_from_worklog",
    "review_repair_round_state",
    "write_residual_user_review_artifacts",
]
