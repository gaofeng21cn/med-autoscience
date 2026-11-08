"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    first_draft_applicable_ref_fields,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    dedupe,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_sha256,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)
from ..candidate_admission import normalize_candidate_admission_receipt

from .constants import (
    RESULT_KIND,
    SCHEMA_VERSION,
    _AUTHORITY_BOUNDARY,
)
from .quality import (
    _aggregate_review_status,
    _review_quality_debt,
)
from .receipt import (
    _generation_identity,
    _host_refs,
)

def _first_draft_quality_debt_result(
    request: Mapping[str, Any],
    *,
    next_owner: str,
    reason_codes: list[str],
    resume_condition: str,
) -> dict[str, Any]:
    reason_codes = dedupe(reason_codes)
    if request["mission"]["stage_id"] == "finalize_and_publication_handoff":
        return _route_result(
            request,
            reason_code=reason_codes[0],
            next_owner=next_owner,
            resume_condition=resume_condition,
        )
    route_back = _route_back(
        request,
        reason_code=reason_codes[0],
        next_owner=next_owner,
        resume_condition=resume_condition,
    )
    return _finalize(
        request,
        status="completed_with_quality_debt",
        stage_outcome=_stage_outcome(
            "completed_with_quality_debt", transition_allowed=True
        ),
        route_back=route_back,
        quality_debt=_quality_debt(request, reason_codes=reason_codes),
    )


def _professional_skill_debt_result(
    request: Mapping[str, Any],
    *,
    reason_codes: list[str],
    resume_condition: str,
) -> dict[str, Any]:
    reason_code = reason_codes[0]
    if request["mission"]["stage_id"] == "finalize_and_publication_handoff":
        return _route_result(
            request,
            reason_code=reason_code,
            next_owner="mission_executor",
            resume_condition=resume_condition,
        )
    route_back = _route_back(
        request,
        reason_code=reason_code,
        next_owner="mission_executor",
        resume_condition=resume_condition,
    )
    return _finalize(
        request,
        status="completed_with_quality_debt",
        stage_outcome=_stage_outcome(
            "completed_with_quality_debt", transition_allowed=True
        ),
        route_back=route_back,
        quality_debt=_quality_debt(request, reason_codes=reason_codes),
    )


def _route_result(
    request: Mapping[str, Any],
    *,
    reason_code: str,
    next_owner: str,
    resume_condition: str,
    affected_review_lanes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return _finalize(
        request,
        status="route_back",
        stage_outcome=_stage_outcome("route_back", transition_allowed=False),
        route_back=_route_back(
            request,
            reason_code=reason_code,
            next_owner=next_owner,
            resume_condition=resume_condition,
            affected_review_lanes=affected_review_lanes,
        ),
    )


def _route_back(
    request: Mapping[str, Any],
    *,
    reason_code: str,
    next_owner: str,
    resume_condition: str,
    affected_review_lanes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    repair = request["repair_state"]
    debt_codes, defect_refs = _review_quality_debt(request)
    route_back = {
        "reason_code": reason_code,
        "next_owner": next_owner,
        "resume_condition": resume_condition,
        "review_verdicts": [
            {
                "review_lane": item["receipt"]["review_lane"],
                "verdict": item["receipt"]["verdict"],
            }
            for item in request["generation_manifest"]["independent_review_receipts"]
        ],
        "quality_debt_codes": debt_codes,
        "defect_refs": defect_refs,
        "repair_attempt_refs": list(repair["repair_attempt_refs"]),
        "remaining_repair_attempts": max(
            repair["max_attempts"] - repair["attempts_used"], 0
        ),
        "selects_next_stage": False,
    }
    if affected_review_lanes is not None:
        route_back["affected_review_lanes"] = [
            dict(item) for item in affected_review_lanes
        ]
    return route_back


def _typed_blocker(request: Mapping[str, Any]) -> dict[str, Any]:
    gate = request["hard_gate"]
    return {
        "blocker_kind": "mas_paper_mission_typed_blocker",
        "gate_kind": gate["kind"],
        "reason_code": gate["reason_code"],
        "evidence_refs": list(gate["evidence_refs"]),
        "next_owner": gate["next_owner"],
        "resume_condition": gate["resume_condition"],
        "blocks_stage_transition": True,
        "requires_host_exact_byte_persistence": True,
    }


def _human_gate(request: Mapping[str, Any]) -> dict[str, Any]:
    gate = request["hard_gate"]
    return {
        "gate_kind": "mas_paper_mission_human_gate",
        "reason_code": gate["reason_code"],
        "evidence_refs": list(gate["evidence_refs"]),
        "next_owner": gate["next_owner"],
        "resume_condition": gate["resume_condition"],
        "blocks_stage_transition": True,
        "requires_host_exact_byte_persistence": True,
    }


def _quality_debt(
    request: Mapping[str, Any], *, reason_codes: list[str]
) -> dict[str, Any]:
    _, defect_refs = _review_quality_debt(request)
    return {
        "reason_codes": reason_codes,
        "review_verdict": _aggregate_review_status(request),
        "defect_refs": defect_refs,
        "transition_allowed": True,
        "blocks_quality_publication_export_and_submission_claims": True,
        "counts_as_owner_acceptance": False,
    }


def _stage_outcome(kind: str, *, transition_allowed: bool) -> dict[str, Any]:
    return {
        "kind": kind,
        "stage_transition_allowed": transition_allowed,
        "selects_next_stage": False,
        "publication_or_submission_ready": False,
    }


def _finalize(
    request: Mapping[str, Any],
    *,
    status: str,
    stage_outcome: Mapping[str, Any],
    owner_receipt: Mapping[str, Any] | None = None,
    route_back: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    human_gate: Mapping[str, Any] | None = None,
    quality_debt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "mission_identity": dict(request["mission"]),
        "host_refs": _host_refs(request),
        "generation_identity": _generation_identity(request),
        "stage_outcome": dict(stage_outcome),
        "owner_receipt": dict(owner_receipt) if owner_receipt is not None else None,
        "route_back": dict(route_back) if route_back is not None else None,
        "typed_blocker": dict(typed_blocker) if typed_blocker is not None else None,
        "human_gate": dict(human_gate) if human_gate is not None else None,
        "quality_debt": dict(quality_debt) if quality_debt is not None else None,
        "error": None,
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    decision_fingerprint = fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-paper-mission-authority:"
            f"{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }


def _invalid_host_input(detail: str) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "invalid_host_input",
        "mission_identity": None,
        "host_refs": None,
        "generation_identity": None,
        "stage_outcome": _stage_outcome("invalid_host_input", transition_allowed=False),
        "owner_receipt": None,
        "route_back": None,
        "typed_blocker": None,
        "human_gate": None,
        "quality_debt": None,
        "error": {"code": "invalid_host_input", "detail": detail},
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    decision_fingerprint = fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-paper-mission-authority:"
            f"{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }
