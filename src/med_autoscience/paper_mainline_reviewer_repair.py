from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SURFACE_KIND = "mas_reviewer_repair_action_projection"
SCHEMA_VERSION = 1
VALID_REPAIR_ACTIONS = frozenset(
    (
        "add_evidence",
        "downgrade_claim",
        "revise_method",
        "add_limitation",
        "fix_citation",
        "route_to_human",
    )
)
VALID_SEVERITIES = frozenset(("minor", "major", "critical", "not_assessable"))
REQUIRED_FIELDS = ("finding_id", "comment_ref", "comment_type", "target_ref", "severity")


def build_reviewer_repair_action_projection(
    findings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    repair_action_candidates: list[dict[str, Any]] = []
    typed_blocker_candidates: list[dict[str, Any]] = []

    for index, finding in enumerate(findings):
        action, blockers = _repair_action_candidate(finding, index=index)
        repair_action_candidates.append(action)
        typed_blocker_candidates.extend(blockers)

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "typed_blocker_candidate" if typed_blocker_candidates else "complete",
        "refs_only": True,
        "fail_open": True,
        "mainline_waits_for_repair_projection": False,
        "can_block_current_owner_action": False,
        "repair_action_candidates": repair_action_candidates,
        "typed_blocker_candidates": typed_blocker_candidates,
        "source_refs": _source_refs(),
        "authority_boundary": _authority_boundary(),
    }


def _repair_action_candidate(
    finding: Mapping[str, Any],
    *,
    index: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    finding_id = _text(finding.get("finding_id")) or f"finding_index_{index}"
    missing_fields = _missing_fields(finding)
    raw_action = _text(finding.get("repair_action")) or _text(finding.get("proposed_action"))
    normalized_action = raw_action if raw_action in VALID_REPAIR_ACTIONS else "route_to_human"
    required_refs = _refs(finding.get("required_refs"), preferred_keys=("ref", "required_ref"))
    severity = _text(finding.get("severity"))
    missing_author_input_state = _text(finding.get("missing_author_input_state"))
    appeal_like_case_route = _text(finding.get("appeal_like_case_route"))

    blockers: list[dict[str, Any]] = []
    if missing_fields:
        blockers.append(
            _typed_blocker_candidate(
                finding_id=finding_id,
                reason="missing_required_reviewer_ref",
                missing_fields=missing_fields,
            )
        )
    if raw_action is None:
        blockers.append(
            _typed_blocker_candidate(
                finding_id=finding_id,
                reason="missing_repair_action",
                missing_fields=["repair_action"],
            )
        )
    elif raw_action not in VALID_REPAIR_ACTIONS:
        blockers.append(
            _typed_blocker_candidate(
                finding_id=finding_id,
                reason="unknown_repair_action",
                missing_fields=[],
            )
        )
    if severity not in VALID_SEVERITIES:
        blockers.append(
            _typed_blocker_candidate(
                finding_id=finding_id,
                reason="invalid_reviewer_severity",
                missing_fields=["severity"],
            )
        )
    if missing_author_input_state == "needed":
        blockers.append(
            _typed_blocker_candidate(
                finding_id=finding_id,
                reason="author_input_needed",
                missing_fields=[],
            )
        )
    if appeal_like_case_route:
        blockers.append(
            _typed_blocker_candidate(
                finding_id=finding_id,
                reason="appeal_like_case_requires_human_route",
                missing_fields=[],
            )
        )

    candidate = {
        "candidate_ref": f"reviewer-repair:{finding_id}:{normalized_action}",
        "finding_id": finding_id,
        "comment_ref": _text(finding.get("comment_ref")),
        "comment_type": _text(finding.get("comment_type")),
        "target_ref": _text(finding.get("target_ref")),
        "severity": severity,
        "repair_action": normalized_action,
        "original_action": raw_action,
        "required_refs": required_refs,
        "missing_author_input_state": missing_author_input_state,
        "appeal_like_case_route": appeal_like_case_route,
        "status": "typed_blocker_candidate" if blockers else "complete",
        "typed_blocker_candidate_refs": [
            blocker["candidate_ref"] for blocker in blockers
        ],
        "refs_only": True,
        "can_mutate_paper_body": False,
        "can_close_quality_gate": False,
    }
    return candidate, blockers


def _missing_fields(finding: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        if _text(finding.get(field)) is None:
            missing.append(field)
    return missing


def _typed_blocker_candidate(
    *,
    finding_id: str,
    reason: str,
    missing_fields: list[str],
) -> dict[str, Any]:
    return {
        "candidate_ref": f"reviewer-repair-blocker:{finding_id}:{reason}",
        "blocker_type": "journal_response_traceability_blocker",
        "finding_id": finding_id,
        "reason": reason,
        "missing_fields": list(missing_fields),
        "refs_only": True,
        "fail_open": True,
        "can_block_current_owner_action": False,
        "recommended_owner_action": _recommended_owner_action(reason),
        "authority_boundary": _authority_boundary(),
    }


def _recommended_owner_action(reason: str) -> str:
    if reason == "missing_required_reviewer_ref":
        return "repair_reviewer_comment_traceability_refs"
    if reason == "missing_repair_action":
        return "classify_reviewer_repair_action"
    if reason == "unknown_repair_action":
        return "route_to_human"
    if reason == "invalid_reviewer_severity":
        return "normalize_reviewer_finding_severity"
    if reason == "author_input_needed":
        return "request_missing_author_input"
    if reason == "appeal_like_case_requires_human_route":
        return "route_appeal_like_case_to_human"
    return "route_to_ai_reviewer"


def _refs(value: object, *, preferred_keys: tuple[str, ...]) -> list[str]:
    if isinstance(value, Mapping):
        ref = _ref_from_mapping(value, preferred_keys=preferred_keys)
        return [ref] if ref else []
    if isinstance(value, str):
        ref = _text(value)
        return [ref] if ref else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        refs: list[str] = []
        for item in value:
            ref = (
                _ref_from_mapping(item, preferred_keys=preferred_keys)
                if isinstance(item, Mapping)
                else _text(item)
            )
            if ref and ref not in refs:
                refs.append(ref)
        return refs
    return []


def _ref_from_mapping(
    value: Mapping[str, Any],
    *,
    preferred_keys: tuple[str, ...],
) -> str | None:
    for key in preferred_keys:
        ref = _text(value.get(key))
        if ref:
            return ref
    return None


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _source_refs() -> dict[str, list[str]]:
    return {
        "external_skill_refs": [
            "nature-skills@1cb9070:skills/nature-response",
            "nature-skills@1cb9070:skills/nature-reader",
            "nature-skills@1cb9070:skills/nature-reviewer",
        ],
        "mas_contract_refs": [
            "journal_response_pack",
            "paper_reader_grounding_pack",
        ],
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "can_write_mas_truth": False,
        "can_mutate_paper_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_close_quality_gate": False,
    }


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_reviewer_repair_action_projection",
]
