"""Consume an OPL-hosted paper-mission result without owning transport or I/O."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


REQUEST_KIND = "mas_paper_mission_authority_request"
RESULT_KIND = "mas_paper_mission_authority_result"
SCHEMA_VERSION = 1

_REF_KINDS = frozenset(
    {
        "opl_stage_run",
        "opl_stage_attempt",
        "opl_action_output",
        "mas_stage_goal",
        "mas_artifact",
        "mas_evidence",
        "mas_negative_result",
        "mas_failed_path",
        "mas_artifact_lineage",
        "mas_reproducibility",
        "mas_source_readiness_receipt",
        "mas_claim_boundary",
        "mas_reviewer_receipt",
        "mas_quality_rubric",
        "mas_review_defect",
        "mas_gate_evidence",
    }
)
_HARD_GATE_KINDS = frozenset(
    {
        "medical_safety",
        "source_identity",
        "source_currentness",
        "domain_authority",
        "credential",
        "irreversible_action",
    }
)
_AUTHORITY_BOUNDARY = {
    "owner": "MedAutoScience",
    "handler_role": "validate_ai_first_domain_records_and_return_exact_authority_result",
    "opl_role": "inject_typed_refs_and_persist_exact_result_bytes",
    "program_originates_medical_quality_verdict": False,
    "host_completion_counts_as_domain_completion": False,
    "selects_next_stage": False,
    "owns_profile_or_path_discovery": False,
    "owns_workspace_or_source_discovery": False,
    "owns_queue_session_dag_or_attempt_lifecycle": False,
    "owns_runtime_ledger": False,
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "invokes_opl_or_codex": False,
    "authorizes_publication_or_submission": False,
}


class RequestShapeError(ValueError):
    """Raised when a host-injected authority request is not exact and typed."""


def evaluate_paper_mission_authority(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic MAS authority result over host-injected refs."""

    try:
        normalized = _normalize_request(request)
        _validate_cross_record_lineage(normalized)
    except RequestShapeError as error:
        return _invalid_host_input(str(error))

    hard_gate = normalized["hard_gate"]
    gate_kind = hard_gate["kind"]
    if gate_kind == "human_decision":
        return _finalize(
            normalized,
            status="human_gate",
            stage_outcome=_stage_outcome("human_gate", transition_allowed=False),
            human_gate=_human_gate(normalized),
        )
    if gate_kind in _HARD_GATE_KINDS:
        return _finalize(
            normalized,
            status="typed_blocker",
            stage_outcome=_stage_outcome("typed_blocker", transition_allowed=False),
            typed_blocker=_typed_blocker(normalized),
        )

    evidence = normalized["medical_evidence"]
    if evidence["source_readiness_status"] != "ready":
        return _finalize(
            normalized,
            status="route_back",
            stage_outcome=_stage_outcome("route_back", transition_allowed=False),
            route_back=_route_back(
                normalized,
                reason_code="source_readiness_record_required",
                next_owner="mas_source_readiness_owner",
                resume_condition="provide a current MAS source-readiness receipt",
            ),
        )
    if evidence["claim_evidence_status"] != "aligned":
        return _finalize(
            normalized,
            status="route_back",
            stage_outcome=_stage_outcome("route_back", transition_allowed=False),
            route_back=_route_back(
                normalized,
                reason_code="claim_evidence_alignment_required",
                next_owner="mission_executor",
                resume_condition="repair claim boundaries against the accepted medical evidence refs",
            ),
        )
    if not evidence["evidence_refs"] and not evidence["negative_result_refs"]:
        return _finalize(
            normalized,
            status="route_back",
            stage_outcome=_stage_outcome("route_back", transition_allowed=False),
            route_back=_route_back(
                normalized,
                reason_code="medical_evidence_record_required",
                next_owner="mission_executor",
                resume_condition=(
                    "provide at least one accepted evidence or negative-result ref "
                    "before requesting MAS owner acceptance"
                ),
            ),
        )

    host = normalized["host_context"]
    if host["output_state"] != "consumable" or not evidence["candidate_artifact_refs"]:
        route_back = _route_back(
            normalized,
            reason_code="consumable_output_missing",
            next_owner="mission_executor",
            resume_condition="produce a readable candidate output bound to the hosted attempt",
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt",
                transition_allowed=True,
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=["consumable_output_missing"],
            ),
        )

    review = normalized["independent_review"]
    repair = normalized["repair_state"]
    if review["status"] in {"not_run", "unavailable"}:
        route_back = _route_back(
            normalized,
            reason_code="independent_reviewer_record_required",
            next_owner="independent_reviewer",
            resume_condition="run an independent reviewer invocation over the exact output digest",
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt",
                transition_allowed=True,
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=["independent_reviewer_record_required"],
            ),
        )

    if review["status"] in {"revision_required", "rejected"}:
        reason_code = (
            "independent_review_rejected_output"
            if review["status"] == "rejected"
            else "independent_review_requires_repair"
        )
        route_back = _route_back(
            normalized,
            reason_code=reason_code,
            next_owner="mission_repairer",
            resume_condition="repair the exact reviewed output and obtain a fresh independent review",
        )
        if repair["attempts_used"] < repair["max_attempts"]:
            return _finalize(
                normalized,
                status="route_back",
                stage_outcome=_stage_outcome("route_back", transition_allowed=False),
                route_back=route_back,
            )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt",
                transition_allowed=True,
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=[reason_code, "repair_budget_exhausted"],
            ),
        )

    open_quality_debt = list(review["quality_debt_codes"])
    if review["defect_refs"]:
        open_quality_debt.append("independent_review_open_defects")
    if open_quality_debt:
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt",
                transition_allowed=True,
            ),
            quality_debt=_quality_debt(
                normalized,
                reason_codes=_dedupe(open_quality_debt),
            ),
        )

    return _finalize(
        normalized,
        status="owner_receipt",
        stage_outcome=_stage_outcome("completed", transition_allowed=True),
        owner_receipt=_owner_receipt(normalized),
    )


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(request, "request")
    _exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "host_context",
            "mission",
            "medical_evidence",
            "independent_review",
            "repair_state",
            "hard_gate",
        },
        "request",
    )
    if payload.get("surface_kind") != REQUEST_KIND:
        raise RequestShapeError(f"surface_kind must be {REQUEST_KIND}")
    if payload.get("schema_version") != SCHEMA_VERSION or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("schema_version must be integer 1")
    return {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "host_context": _normalize_host_context(payload.get("host_context")),
        "mission": _normalize_mission(payload.get("mission")),
        "medical_evidence": _normalize_medical_evidence(payload.get("medical_evidence")),
        "independent_review": _normalize_review(payload.get("independent_review")),
        "repair_state": _normalize_repair(payload.get("repair_state")),
        "hard_gate": _normalize_hard_gate(payload.get("hard_gate")),
    }


def _normalize_host_context(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "host_context")
    _exact_keys(
        payload,
        {"action_id", "run_ref", "producer_attempt_ref", "output_ref", "output_state"},
        "host_context",
    )
    if payload.get("action_id") != "paper_mission":
        raise RequestShapeError("host_context.action_id must be paper_mission")
    return {
        "action_id": "paper_mission",
        "run_ref": _typed_ref(payload.get("run_ref"), "host_context.run_ref", "opl_stage_run"),
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            "host_context.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "output_ref": _typed_ref(
            payload.get("output_ref"),
            "host_context.output_ref",
            "opl_action_output",
        ),
        "output_state": _enum_text(
            payload.get("output_state"),
            "host_context.output_state",
            {"consumable", "no_output", "damaged", "failed"},
        ),
    }


def _normalize_mission(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "mission")
    _exact_keys(
        payload,
        {"program_id", "study_id", "mission_id", "stage_id", "stage_goal_ref"},
        "mission",
    )
    return {
        "program_id": _text(payload.get("program_id"), "mission.program_id"),
        "study_id": _text(payload.get("study_id"), "mission.study_id"),
        "mission_id": _text(payload.get("mission_id"), "mission.mission_id"),
        "stage_id": _text(payload.get("stage_id"), "mission.stage_id"),
        "stage_goal_ref": _typed_ref(
            payload.get("stage_goal_ref"),
            "mission.stage_goal_ref",
            "mas_stage_goal",
        ),
    }


def _normalize_medical_evidence(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "medical_evidence")
    _exact_keys(
        payload,
        {
            "source_readiness_status",
            "source_readiness_receipt_ref",
            "claim_evidence_status",
            "claim_boundary_ref",
            "candidate_artifact_refs",
            "evidence_refs",
            "negative_result_refs",
            "failed_path_refs",
            "artifact_lineage_refs",
            "reproducibility_refs",
        },
        "medical_evidence",
    )
    source_status = _enum_text(
        payload.get("source_readiness_status"),
        "medical_evidence.source_readiness_status",
        {"ready", "not_ready", "unknown"},
    )
    source_ref = _optional_typed_ref(
        payload.get("source_readiness_receipt_ref"),
        "medical_evidence.source_readiness_receipt_ref",
        "mas_source_readiness_receipt",
    )
    if source_status == "ready" and source_ref is None:
        raise RequestShapeError("ready source status requires source_readiness_receipt_ref")
    return {
        "source_readiness_status": source_status,
        "source_readiness_receipt_ref": source_ref,
        "claim_evidence_status": _enum_text(
            payload.get("claim_evidence_status"),
            "medical_evidence.claim_evidence_status",
            {"aligned", "revision_required", "unsafe", "unknown"},
        ),
        "claim_boundary_ref": _typed_ref(
            payload.get("claim_boundary_ref"),
            "medical_evidence.claim_boundary_ref",
            "mas_claim_boundary",
        ),
        "candidate_artifact_refs": _typed_ref_list(
            payload.get("candidate_artifact_refs"),
            "medical_evidence.candidate_artifact_refs",
            "mas_artifact",
        ),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"),
            "medical_evidence.evidence_refs",
            "mas_evidence",
        ),
        "negative_result_refs": _typed_ref_list(
            payload.get("negative_result_refs"),
            "medical_evidence.negative_result_refs",
            "mas_negative_result",
        ),
        "failed_path_refs": _typed_ref_list(
            payload.get("failed_path_refs"),
            "medical_evidence.failed_path_refs",
            "mas_failed_path",
        ),
        "artifact_lineage_refs": _typed_ref_list(
            payload.get("artifact_lineage_refs"),
            "medical_evidence.artifact_lineage_refs",
            "mas_artifact_lineage",
        ),
        "reproducibility_refs": _typed_ref_list(
            payload.get("reproducibility_refs"),
            "medical_evidence.reproducibility_refs",
            "mas_reproducibility",
        ),
    }


def _normalize_review(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "independent_review")
    _exact_keys(
        payload,
        {
            "status",
            "reviewer_attempt_ref",
            "reviewer_receipt_ref",
            "rubric_ref",
            "reviewed_output_sha256",
            "defect_refs",
            "quality_debt_codes",
        },
        "independent_review",
    )
    status = _enum_text(
        payload.get("status"),
        "independent_review.status",
        {"passed", "revision_required", "rejected", "not_run", "unavailable"},
    )
    review = {
        "status": status,
        "reviewer_attempt_ref": _optional_typed_ref(
            payload.get("reviewer_attempt_ref"),
            "independent_review.reviewer_attempt_ref",
            "opl_stage_attempt",
        ),
        "reviewer_receipt_ref": _optional_typed_ref(
            payload.get("reviewer_receipt_ref"),
            "independent_review.reviewer_receipt_ref",
            "mas_reviewer_receipt",
        ),
        "rubric_ref": _optional_typed_ref(
            payload.get("rubric_ref"),
            "independent_review.rubric_ref",
            "mas_quality_rubric",
        ),
        "reviewed_output_sha256": _optional_sha256(
            payload.get("reviewed_output_sha256"),
            "independent_review.reviewed_output_sha256",
        ),
        "defect_refs": _typed_ref_list(
            payload.get("defect_refs"),
            "independent_review.defect_refs",
            "mas_review_defect",
        ),
        "quality_debt_codes": _text_list(
            payload.get("quality_debt_codes"),
            "independent_review.quality_debt_codes",
        ),
    }
    if status in {"passed", "revision_required", "rejected"}:
        required = (
            "reviewer_attempt_ref",
            "reviewer_receipt_ref",
            "rubric_ref",
            "reviewed_output_sha256",
        )
        missing = [field for field in required if review[field] is None]
        if missing:
            raise RequestShapeError(
                "independent review record missing: " + ", ".join(missing)
            )
    return review


def _normalize_repair(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "repair_state")
    _exact_keys(
        payload,
        {
            "status",
            "attempts_used",
            "max_attempts",
            "repair_attempt_refs",
            "latest_repair_output_ref",
        },
        "repair_state",
    )
    attempts_used = _integer(payload.get("attempts_used"), "repair_state.attempts_used")
    max_attempts = _integer(payload.get("max_attempts"), "repair_state.max_attempts")
    if attempts_used > max_attempts:
        raise RequestShapeError("repair_state.attempts_used cannot exceed max_attempts")
    attempt_refs = _typed_ref_list(
        payload.get("repair_attempt_refs"),
        "repair_state.repair_attempt_refs",
        "opl_stage_attempt",
    )
    if len(attempt_refs) != attempts_used:
        raise RequestShapeError("repair_attempt_refs must exactly match attempts_used")
    return {
        "status": _enum_text(
            payload.get("status"),
            "repair_state.status",
            {"not_required", "pending", "completed", "exhausted", "failed"},
        ),
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "repair_attempt_refs": attempt_refs,
        "latest_repair_output_ref": _optional_typed_ref(
            payload.get("latest_repair_output_ref"),
            "repair_state.latest_repair_output_ref",
            "opl_action_output",
        ),
    }


def _normalize_hard_gate(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "hard_gate")
    _exact_keys(
        payload,
        {"kind", "reason_code", "evidence_refs", "next_owner", "resume_condition"},
        "hard_gate",
    )
    kind = _enum_text(
        payload.get("kind"),
        "hard_gate.kind",
        {"none", "human_decision", *_HARD_GATE_KINDS},
    )
    normalized = {
        "kind": kind,
        "reason_code": _optional_text(payload.get("reason_code"), "hard_gate.reason_code"),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"),
            "hard_gate.evidence_refs",
            "mas_gate_evidence",
        ),
        "next_owner": _optional_text(payload.get("next_owner"), "hard_gate.next_owner"),
        "resume_condition": _optional_text(
            payload.get("resume_condition"),
            "hard_gate.resume_condition",
        ),
    }
    if kind != "none":
        missing = [
            field
            for field in ("reason_code", "next_owner", "resume_condition")
            if normalized[field] is None
        ]
        if not normalized["evidence_refs"]:
            missing.append("evidence_refs")
        if missing:
            raise RequestShapeError("hard gate missing: " + ", ".join(missing))
    elif any(
        (
            normalized["reason_code"] is not None,
            bool(normalized["evidence_refs"]),
            normalized["next_owner"] is not None,
            normalized["resume_condition"] is not None,
        )
    ):
        raise RequestShapeError("hard_gate.kind none requires an empty gate record")
    return normalized


def _validate_cross_record_lineage(request: Mapping[str, Any]) -> None:
    host = request["host_context"]
    review = request["independent_review"]
    reviewer_attempt = review["reviewer_attempt_ref"]
    if reviewer_attempt is not None:
        producer_attempt = host["producer_attempt_ref"]
        if reviewer_attempt["ref"] == producer_attempt["ref"]:
            raise RequestShapeError("reviewer attempt must differ from producer attempt")
        if reviewer_attempt["sha256"] == producer_attempt["sha256"]:
            raise RequestShapeError("reviewer attempt digest must differ from producer attempt digest")
    reviewed_output_sha256 = review["reviewed_output_sha256"]
    if reviewed_output_sha256 is not None and reviewed_output_sha256 != host["output_ref"]["sha256"]:
        raise RequestShapeError("reviewer receipt is not bound to the exact hosted output digest")


def _owner_receipt(request: Mapping[str, Any]) -> dict[str, Any]:
    evidence = request["medical_evidence"]
    review = request["independent_review"]
    receipt = {
        "receipt_kind": "mas_paper_mission_owner_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "mission_identity": dict(request["mission"]),
        "host_refs": _host_refs(request),
        "candidate_artifact_refs": list(evidence["candidate_artifact_refs"]),
        "medical_evidence_refs": list(evidence["evidence_refs"]),
        "negative_result_refs": list(evidence["negative_result_refs"]),
        "failed_path_refs": list(evidence["failed_path_refs"]),
        "artifact_lineage_refs": list(evidence["artifact_lineage_refs"]),
        "reproducibility_refs": list(evidence["reproducibility_refs"]),
        "source_readiness_receipt_ref": evidence["source_readiness_receipt_ref"],
        "claim_boundary_ref": evidence["claim_boundary_ref"],
        "independent_reviewer_attempt_ref": review["reviewer_attempt_ref"],
        "independent_reviewer_receipt_ref": review["reviewer_receipt_ref"],
        "quality_rubric_ref": review["rubric_ref"],
        "verdict": "accepted_domain_delta",
        "authorizes_stage_domain_completion": True,
        "authorizes_publication_or_submission": False,
        "requires_host_exact_byte_persistence": True,
    }
    fingerprint = _fingerprint(receipt)
    return {
        **receipt,
        "receipt_id": f"mas-paper-mission-owner-receipt:{fingerprint.removeprefix('sha256:')}",
        "receipt_fingerprint": fingerprint,
    }


def _route_back(
    request: Mapping[str, Any],
    *,
    reason_code: str,
    next_owner: str,
    resume_condition: str,
) -> dict[str, Any]:
    review = request["independent_review"]
    repair = request["repair_state"]
    return {
        "reason_code": reason_code,
        "next_owner": next_owner,
        "resume_condition": resume_condition,
        "reviewer_verdict": review["status"],
        "defect_refs": list(review["defect_refs"]),
        "repair_attempt_refs": list(repair["repair_attempt_refs"]),
        "remaining_repair_attempts": max(
            repair["max_attempts"] - repair["attempts_used"],
            0,
        ),
        "selects_next_stage": False,
    }


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
    request: Mapping[str, Any],
    *,
    reason_codes: list[str],
) -> dict[str, Any]:
    review = request["independent_review"]
    return {
        "reason_codes": reason_codes,
        "reviewer_verdict": review["status"],
        "defect_refs": list(review["defect_refs"]),
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
        "stage_outcome": dict(stage_outcome),
        "owner_receipt": dict(owner_receipt) if owner_receipt is not None else None,
        "route_back": dict(route_back) if route_back is not None else None,
        "typed_blocker": dict(typed_blocker) if typed_blocker is not None else None,
        "human_gate": dict(human_gate) if human_gate is not None else None,
        "quality_debt": dict(quality_debt) if quality_debt is not None else None,
        "error": None,
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    fingerprint = _fingerprint(core)
    return {
        **core,
        "decision_id": f"mas-paper-mission-authority:{fingerprint.removeprefix('sha256:')}",
        "decision_fingerprint": fingerprint,
    }


def _invalid_host_input(detail: str) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "invalid_host_input",
        "mission_identity": None,
        "host_refs": None,
        "stage_outcome": _stage_outcome("invalid_host_input", transition_allowed=False),
        "owner_receipt": None,
        "route_back": None,
        "typed_blocker": None,
        "human_gate": None,
        "quality_debt": None,
        "error": {"code": "invalid_host_input", "detail": detail},
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    fingerprint = _fingerprint(core)
    return {
        **core,
        "decision_id": f"mas-paper-mission-authority:{fingerprint.removeprefix('sha256:')}",
        "decision_fingerprint": fingerprint,
    }


def _host_refs(request: Mapping[str, Any]) -> dict[str, Any]:
    host = request["host_context"]
    return {
        "run_ref": dict(host["run_ref"]),
        "producer_attempt_ref": dict(host["producer_attempt_ref"]),
        "output_ref": dict(host["output_ref"]),
    }


def _typed_ref(value: Any, field: str, expected_kind: str) -> dict[str, str]:
    payload = _mapping(value, field)
    _exact_keys(payload, {"kind", "ref", "sha256"}, field)
    kind = _text(payload.get("kind"), f"{field}.kind")
    if kind not in _REF_KINDS:
        raise RequestShapeError(f"{field}.kind is unsupported")
    if kind != expected_kind:
        raise RequestShapeError(f"{field}.kind must be {expected_kind}")
    return {
        "kind": kind,
        "ref": _text(payload.get("ref"), f"{field}.ref"),
        "sha256": _sha256(payload.get("sha256"), f"{field}.sha256"),
    }


def _optional_typed_ref(value: Any, field: str, expected_kind: str) -> dict[str, str] | None:
    if value is None:
        return None
    return _typed_ref(value, field, expected_kind)


def _typed_ref_list(value: Any, field: str, expected_kind: str) -> list[dict[str, str]]:
    items = _sequence(value, field)
    refs = [_typed_ref(item, f"{field}[{index}]", expected_kind) for index, item in enumerate(items)]
    identities = [(item["ref"], item["sha256"]) for item in refs]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate refs")
    return refs


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RequestShapeError(f"{field} must be an object")
    return dict(value)


def _sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RequestShapeError(f"{field} must be an array")
    return list(value)


def _exact_keys(payload: Mapping[str, Any], allowed: set[str], field: str) -> None:
    missing = sorted(allowed - set(payload))
    unknown = sorted(set(payload) - allowed)
    if missing:
        raise RequestShapeError(f"{field} missing fields: {', '.join(missing)}")
    if unknown:
        raise RequestShapeError(f"{field} contains unsupported fields: {', '.join(unknown)}")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestShapeError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _text_list(value: Any, field: str) -> list[str]:
    return _dedupe([_text(item, f"{field}[{index}]") for index, item in enumerate(_sequence(value, field))])


def _enum_text(value: Any, field: str, allowed: set[str]) -> str:
    text = _text(value, field)
    if text not in allowed:
        raise RequestShapeError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return text


def _integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RequestShapeError(f"{field} must be a non-negative integer")
    return value


def _sha256(value: Any, field: str) -> str:
    text = _text(value, field).lower()
    digest = text.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RequestShapeError(f"{field} must be a SHA-256 digest")
    return f"sha256:{digest}"


def _optional_sha256(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _sha256(value, field)


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


__all__ = ["evaluate_paper_mission_authority"]
