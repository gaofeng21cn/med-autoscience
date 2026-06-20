from __future__ import annotations

from collections.abc import Mapping
from typing import Any


FATAL_BLOCKER = "fatal_blocker"
MUST_FIX_BEFORE_CURRENT_GATE = "must_fix_before_current_gate"
CARRY_FORWARD_ADVISORY = "carry_forward_advisory"
OPTIONAL_POLISH = "optional_polish"

SEVERITY_LEVELS = frozenset(
    {
        FATAL_BLOCKER,
        MUST_FIX_BEFORE_CURRENT_GATE,
        CARRY_FORWARD_ADVISORY,
        OPTIONAL_POLISH,
    }
)

FATAL_DEFAULT_REASONS = frozenset(
    {
        "claim_loses_direct_evidence_support",
        "unsupported_claim",
        "evidence_fabrication_risk",
        "source_evidence_invalid",
        "forbidden_write",
        "human_gate_required",
        "publication_or_submission_authorization_required",
        "ethical_or_compliance_blocker",
    }
)

NONFATAL_DEFAULT_REASONS = frozenset(
    {
        "typed_closeout_packet_required",
        "manuscript_story_surface_delta_missing",
        "publication_gate_replay_blocked",
        "ai_reviewer_request_missing",
        "medical_prose_review_request_rehydrate_required",
        "visual_polish_remaining",
        "optional_style_repair_remaining",
    }
)


def severity_for_blocker_reason(reason: object) -> str:
    text = _text(reason)
    if text in FATAL_DEFAULT_REASONS:
        return FATAL_BLOCKER
    if text in NONFATAL_DEFAULT_REASONS:
        return CARRY_FORWARD_ADVISORY
    return MUST_FIX_BEFORE_CURRENT_GATE


def budget_exhausted_decision(
    *,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    blocker_reason: object,
    failure_count: int,
    max_automatic_failures: int,
) -> dict[str, Any]:
    severity = severity_for_blocker_reason(blocker_reason)
    fatal = severity == FATAL_BLOCKER
    decision = "block_for_fatal_risk" if fatal else "advance_with_carry_forward_risk"
    next_allowed_outcomes = (
        ["single_typed_blocker", "human_or_operator_gate", "route_redesign"]
        if fatal
        else [
            "carry_forward_risk_receipt",
            "advance_next_route",
            "publishability_repair_sprint",
            "single_typed_blocker_if_new_fatal_evidence",
        ]
    )
    carry_forward_receipt = None
    if not fatal:
        carry_forward_receipt = {
            "surface_kind": "mas_progress_first_carry_forward_risk_receipt",
            "schema_version": 1,
            "study_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "unresolved_reason": _text(blocker_reason),
            "severity": severity,
            "attempt_count": failure_count,
            "max_attempts": max_automatic_failures,
            "risk_owner": "MedAutoScience",
            "next_route_policy": "advance_ordinary_progress_without_readiness_claim",
            "revisit_condition": (
                "Reopen only when a new fatal finding, new work-unit identity, human gate, "
                "or owner-authorized readiness/submission decision appears."
            ),
            "authority_boundary": {
                "can_claim_publication_ready": False,
                "can_claim_submission_ready": False,
                "can_write_publication_eval": False,
                "can_write_controller_decision": False,
                "can_write_paper_body": False,
                "can_write_current_package": False,
            },
        }
    return {
        "surface_kind": "mas_progress_first_budget_exhausted_decision",
        "schema_version": 1,
        "decision": decision,
        "severity": severity,
        "fatal": fatal,
        "study_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "blocker_reason": _text(blocker_reason),
        "attempt_count": failure_count,
        "max_attempts": max_automatic_failures,
        "ordinary_progress_may_advance": not fatal,
        "readiness_claim_allowed": False,
        "next_allowed_outcomes": next_allowed_outcomes,
        "carry_forward_risk_receipt": carry_forward_receipt,
    }


def summarize_budget_decision(decision: Mapping[str, Any] | None) -> dict[str, Any]:
    mapping = _mapping(decision)
    if not mapping:
        return {}
    return {
        "decision": _text(mapping.get("decision")),
        "severity": _text(mapping.get("severity")),
        "fatal": mapping.get("fatal") is True,
        "ordinary_progress_may_advance": mapping.get("ordinary_progress_may_advance") is True,
        "readiness_claim_allowed": mapping.get("readiness_claim_allowed") is True,
        "next_allowed_outcomes": _string_items(mapping.get("next_allowed_outcomes")),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Mapping | bytes):
        return []
    if not isinstance(value, list | tuple | set):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "CARRY_FORWARD_ADVISORY",
    "FATAL_BLOCKER",
    "MUST_FIX_BEFORE_CURRENT_GATE",
    "OPTIONAL_POLISH",
    "SEVERITY_LEVELS",
    "budget_exhausted_decision",
    "severity_for_blocker_reason",
    "summarize_budget_decision",
]
