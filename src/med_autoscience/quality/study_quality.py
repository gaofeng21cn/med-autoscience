from __future__ import annotations

from pathlib import Path
from typing import Any


_REVIEW_LEDGER_BLOCKING_STATUSES = {"open", "in_progress", "deferred"}
_QUALITY_DIMENSION_ORDER = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "human_review_readiness",
)


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _required_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def _quality_basis_item(
    quality_closure_basis: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    raw_item = quality_closure_basis.get(key)
    return dict(raw_item) if isinstance(raw_item, dict) else {}


def build_reviewer_first_readiness(
    *,
    review_ledger_payload: dict[str, Any] | None,
    review_ledger_path: str | Path | None,
    fallback_basis_item: dict[str, Any],
) -> dict[str, Any]:
    fallback = {
        "required": True,
        "status": str(fallback_basis_item.get("status") or "underdefined").strip() or "underdefined",
        "ready": str(fallback_basis_item.get("status") or "").strip() == "ready",
        "source": "publication_eval",
        "summary": str(fallback_basis_item.get("summary") or "当前还没有稳定的 reviewer-first readiness 判断。").strip(),
        "open_concern_count": 0,
        "resolved_concern_count": 0,
        "evidence_refs": _required_string_list(fallback_basis_item.get("evidence_refs")),
    }
    if not isinstance(review_ledger_payload, dict):
        return fallback

    concerns = review_ledger_payload.get("concerns")
    if not isinstance(concerns, list) or not concerns:
        return fallback

    open_count = 0
    resolved_count = 0
    highest_open_severity = None
    severity_rank = {"critical": 0, "major": 1, "minor": 2, "editorial": 3}
    for concern in concerns:
        if not isinstance(concern, dict):
            continue
        status = str(concern.get("status") or "").strip()
        if status in _REVIEW_LEDGER_BLOCKING_STATUSES:
            open_count += 1
            severity = str(concern.get("severity") or "").strip()
            if highest_open_severity is None or severity_rank.get(severity, 99) < severity_rank.get(highest_open_severity, 99):
                highest_open_severity = severity
        elif status == "resolved":
            resolved_count += 1

    evidence_ref = str(Path(review_ledger_path).expanduser()) if review_ledger_path is not None else None
    evidence_refs = [evidence_ref] if evidence_ref else fallback["evidence_refs"]
    if open_count:
        status = "blocked" if highest_open_severity in {"critical", "major"} else "partial"
        return {
            "required": True,
            "status": status,
            "ready": False,
            "source": "review_ledger",
            "summary": f"review ledger 仍有 {open_count} 个未关闭 concern，reviewer-first readiness 不能视为已闭环。",
            "open_concern_count": open_count,
            "resolved_concern_count": resolved_count,
            "evidence_refs": evidence_refs,
        }
    return {
        "required": True,
        "status": "ready",
        "ready": True,
        "source": "review_ledger",
        "summary": f"review ledger 已把 {resolved_count} 个 concern 全部收口，reviewer-first readiness 已具备常规放行条件。",
        "open_concern_count": 0,
        "resolved_concern_count": resolved_count,
        "evidence_refs": evidence_refs,
    }


def _bounded_analysis_truth(
    *,
    charter_payload: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
    quality_closure_truth: dict[str, Any],
) -> dict[str, Any]:
    raw_contract = (
        dict((dict(charter_payload.get("paper_quality_contract") or {})).get("bounded_analysis") or {})
        if isinstance(charter_payload.get("paper_quality_contract"), dict)
        else {}
    )
    completion_boundary = dict(raw_contract.get("completion_boundary") or {})
    required_now = str((route_repair_plan or {}).get("action_type") or "").strip() == "bounded_analysis"
    closure_state = str(quality_closure_truth.get("state") or "").strip()
    if closure_state in {"write_line_ready", "bundle_only_remaining"}:
        entry_state = "not_required"
        completion_state = "satisfied"
    elif required_now:
        entry_state = "ready_to_enter"
        completion_state = "pending_required_updates"
    else:
        entry_state = "route_not_selected"
        completion_state = "not_required"
    return {
        "contract_defined": bool(raw_contract),
        "required_now": required_now,
        "entry_state": entry_state,
        "completion_state": completion_state,
        "route_target": _optional_text((route_repair_plan or {}).get("route_target")),
        "route_key_question": _optional_text((route_repair_plan or {}).get("route_key_question")),
        "allowed_scenarios": _required_string_list(raw_contract.get("allowed_scenarios")),
        "allowed_targets": _required_string_list(raw_contract.get("allowed_targets")),
        "completion_criteria": _required_string_list(completion_boundary.get("completion_criteria")),
        "required_updates": _required_string_list(completion_boundary.get("required_updates")),
    }


def _narrowest_scientific_gap(
    *,
    publication_eval: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
    quality_closure_truth: dict[str, Any],
    quality_execution_lane: dict[str, Any],
) -> dict[str, Any]:
    closure_state = str(quality_closure_truth.get("state") or "").strip()
    route_target = _optional_text((route_repair_plan or {}).get("route_target")) or _optional_text(
        quality_execution_lane.get("route_target")
    )
    route_key_question = _optional_text((route_repair_plan or {}).get("route_key_question")) or _optional_text(
        quality_execution_lane.get("route_key_question")
    )
    why_now = _optional_text((route_repair_plan or {}).get("route_rationale")) or _optional_text(
        quality_execution_lane.get("why_now")
    )
    if closure_state == "bundle_only_remaining":
        return {
            "state": "closed",
            "gap_id": None,
            "severity": None,
            "summary": "Open scientific gap is already closed; only finalize / submission-bundle stabilization remains.",
            "route_target": route_target,
            "route_key_question": route_key_question,
            "why_now": why_now,
        }

    gaps = publication_eval.get("gaps")
    selected_gap = None
    severity_rank = {"must_fix": 0, "important": 1, "optional": 2}
    if isinstance(gaps, list):
        for index, gap in enumerate(gaps):
            if not isinstance(gap, dict):
                continue
            summary = _optional_text(gap.get("summary"))
            if summary is None:
                continue
            severity = _optional_text(gap.get("severity")) or "important"
            marker = (severity_rank.get(severity, 99), index)
            if selected_gap is None or marker < selected_gap[0]:
                selected_gap = (
                    marker,
                    {
                        "gap_id": _optional_text(gap.get("gap_id")),
                        "severity": severity,
                        "summary": summary,
                    },
                )
    gap_payload = selected_gap[1] if selected_gap is not None else {"gap_id": None, "severity": None, "summary": str(quality_closure_truth.get("summary") or "").strip()}
    gap_state = (
        "bounded_analysis_required"
        if str((route_repair_plan or {}).get("action_type") or "").strip() == "bounded_analysis"
        else "same_line_repair_required"
    )
    return {
        "state": gap_state,
        "gap_id": gap_payload.get("gap_id"),
        "severity": gap_payload.get("severity"),
        "summary": gap_payload.get("summary"),
        "route_target": route_target,
        "route_key_question": route_key_question,
        "why_now": why_now,
    }


def _finalize_bundle_readiness(
    *,
    quality_closure_truth: dict[str, Any],
    quality_closure_basis: dict[str, Any],
    reviewer_first: dict[str, Any],
) -> dict[str, Any]:
    closure_state = str(quality_closure_truth.get("state") or "").strip()
    ready_dimensions = [
        key
        for key in _QUALITY_DIMENSION_ORDER
        if str(_quality_basis_item(quality_closure_basis, key).get("status") or "").strip() == "ready"
    ]
    if bool(reviewer_first.get("ready")) and "human_review_readiness" not in ready_dimensions:
        ready_dimensions.append("human_review_readiness")
    if closure_state != "bundle_only_remaining":
        return {
            "status": closure_state or "quality_repair_required",
            "ready_for_finalize": False,
            "reviewer_first_ready": bool(reviewer_first.get("ready")),
            "summary": "当前还在质量修复阶段，finalize / bundle readiness 不能提前视为稳定。",
            "why_stable": "当前最窄 scientific gap 仍未闭环，先完成同线质量修复再进入 finalize / bundle。",
            "basis_dimensions": [],
        }
    if reviewer_first.get("source") != "review_ledger":
        return {
            "status": "missing_review_ledger",
            "ready_for_finalize": False,
            "reviewer_first_ready": False,
            "summary": "核心科学质量已进入 bundle-only 收口，但 reviewer-first readiness 还没有由 review ledger 证明。",
            "why_stable": "先补齐 review ledger 或关闭 reviewer concern，再把 finalize / bundle readiness 视为稳定。",
            "basis_dimensions": [],
        }
    if not bool(reviewer_first.get("ready")):
        return {
            "status": "reviewer_first_not_ready",
            "ready_for_finalize": False,
            "reviewer_first_ready": False,
            "summary": "核心科学质量已进入 bundle-only 收口，但 reviewer-first concern 仍未关闭。",
            "why_stable": "先关闭 review ledger 中的阻塞 concern，再把 finalize / bundle readiness 视为稳定。",
            "basis_dimensions": [],
        }
    return {
        "status": "bundle_only_remaining",
        "ready_for_finalize": True,
        "reviewer_first_ready": bool(reviewer_first.get("ready")),
        "summary": "核心科学面、reviewer-first readiness 和 publication gate 已经落在同一组 quality truth 上；当前只剩 finalize / bundle 收口。",
        "why_stable": (
            "clinical_significance、evidence_strength、novelty_positioning 已达到 ready，"
            "reviewer-first 也已具备常规放行条件。"
        ),
        "basis_dimensions": ready_dimensions,
    }


def build_study_quality_truth(
    *,
    study_id: str,
    charter_payload: dict[str, Any],
    publication_eval: dict[str, Any],
    promotion_gate_payload: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
    quality_closure_truth: dict[str, Any],
    quality_closure_basis: dict[str, Any],
    quality_execution_lane: dict[str, Any],
    review_ledger_payload: dict[str, Any] | None,
    review_ledger_path: str | Path | None,
) -> dict[str, Any]:
    reviewer_first = build_reviewer_first_readiness(
        review_ledger_payload=review_ledger_payload,
        review_ledger_path=review_ledger_path,
        fallback_basis_item=_quality_basis_item(quality_closure_basis, "human_review_readiness"),
    )
    bounded_analysis = _bounded_analysis_truth(
        charter_payload=charter_payload,
        route_repair_plan=route_repair_plan,
        quality_closure_truth=quality_closure_truth,
    )
    narrowest_scientific_gap = _narrowest_scientific_gap(
        publication_eval=publication_eval,
        route_repair_plan=route_repair_plan,
        quality_closure_truth=quality_closure_truth,
        quality_execution_lane=quality_execution_lane,
    )
    finalize_bundle_readiness = _finalize_bundle_readiness(
        quality_closure_truth=quality_closure_truth,
        quality_closure_basis=quality_closure_basis,
        reviewer_first=reviewer_first,
    )
    contract_state = str(quality_closure_truth.get("state") or "").strip() or "quality_repair_required"
    return {
        "study_id": study_id,
        "contract_state": contract_state,
        "contract_closed": contract_state in {"write_line_ready", "bundle_only_remaining"},
        "summary": str(quality_closure_truth.get("summary") or "").strip(),
        "narrowest_scientific_gap": narrowest_scientific_gap,
        "reviewer_first": reviewer_first,
        "bounded_analysis": bounded_analysis,
        "finalize_bundle_readiness": finalize_bundle_readiness,
        "publication_gate_required_action": _optional_text(promotion_gate_payload.get("current_required_action")),
    }
