from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_unique_control_plane_boundary_parts.consumer_migration import (
    MINIMAL_AUTHORITY_FUNCTION_MANIFEST,
)


MECHANICAL_SUBSTITUTE_BY_FUNCTION_ID = {
    "publication_quality_verdict": "script_exit_code_as_publication_quality_verdict",
    "ai_reviewer_quality_decision": "function_return_value_as_ai_reviewer_quality_decision",
    "artifact_mutation_authorization": "test_pass_as_artifact_mutation_authorization",
    "publication_route_memory_accept_reject": "queue_completion_as_publication_route_memory_accept_reject",
    "source_readiness_verdict": "file_presence_as_source_readiness_verdict",
}


def validate_ai_first_private_authority_gate(
    *,
    function_id: str,
    candidate_record: Mapping[str, Any],
    executor_receipt: Mapping[str, Any],
    reviewer_receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    function = _function_by_id(function_id)
    if function is None:
        return _typed_blocker(
            function_id=function_id,
            blocker_id="unknown_private_authority_function",
            route_back="route_back_to_private_authority_audit",
        )

    judgment_mode = _text(function.get("judgment_mode"))
    if judgment_mode == "mechanical_guard":
        return {
            "surface_kind": "mas_ai_first_private_authority_gate_validation",
            "function_id": function_id,
            "status": "mechanical_guard_allowed",
            "judgment_mode": judgment_mode,
            "program_role": _text(function.get("program_role")),
            "can_close_quality_gate": False,
            "program_may_emit_pass_ready_verdict": False,
        }
    if judgment_mode not in {"ai_first_stage_gate", "ai_first_record_validator"}:
        return _typed_blocker(
            function_id=function_id,
            blocker_id="unsupported_private_authority_judgment_mode",
            route_back="route_back_to_private_authority_audit",
            function=function,
        )

    receipt_blocker = _independent_reviewer_receipt_blocker(
        function_id=function_id,
        function=function,
        executor_receipt=executor_receipt,
        reviewer_receipt=reviewer_receipt,
    )
    if receipt_blocker:
        return receipt_blocker

    record_blocker = _candidate_record_blocker(
        function_id=function_id,
        function=function,
        candidate_record=candidate_record,
    )
    if record_blocker:
        return record_blocker

    return {
        "surface_kind": "mas_ai_first_private_authority_gate_validation",
        "function_id": function_id,
        "status": "ai_first_record_validated",
        "judgment_mode": judgment_mode,
        "program_role": _text(function.get("program_role")),
        "can_close_quality_gate": True,
        "program_may_emit_pass_ready_verdict": False,
        "decision_output_owner": _text(function.get("decision_output_owner")),
        "reviewer_receipt_ref": _text((reviewer_receipt or {}).get("receipt_ref")) or None,
        "independent_reviewer_or_auditor_evidence_refs": _independent_quality_evidence_refs(
            reviewer_receipt or {}
        ),
    }


def _function_by_id(function_id: str) -> dict[str, Any] | None:
    for item in MINIMAL_AUTHORITY_FUNCTION_MANIFEST["functions"]:
        if item.get("function_id") == function_id:
            return dict(item)
    return None


def _independent_reviewer_receipt_blocker(
    *,
    function_id: str,
    function: Mapping[str, Any],
    executor_receipt: Mapping[str, Any],
    reviewer_receipt: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if reviewer_receipt is None:
        return _typed_blocker(
            function_id=function_id,
            blocker_id="missing_independent_reviewer_record",
            route_back=_text(function.get("route_back_semantics")),
            function=function,
        )

    required_keys = ("agent_invocation_id", "task_record_ref", "context_record_ref", "receipt_ref")
    missing = [
        key
        for key in required_keys
        if not _text(executor_receipt.get(key)) or not _text(reviewer_receipt.get(key))
    ]
    if missing:
        return _typed_blocker(
            function_id=function_id,
            blocker_id="incomplete_independent_agent_record",
            route_back=_text(function.get("route_back_semantics")),
            function=function,
            details={"missing_record_keys": missing},
        )

    reused_keys = [
        key
        for key in required_keys
        if _text(executor_receipt.get(key)) == _text(reviewer_receipt.get(key))
    ]
    if reused_keys:
        return _typed_blocker(
            function_id=function_id,
            blocker_id="self_review_context_reuse",
            route_back=_text(function.get("route_back_semantics")),
            function=function,
            details={"reused_record_keys": reused_keys},
        )
    return None


def _candidate_record_blocker(
    *,
    function_id: str,
    function: Mapping[str, Any],
    candidate_record: Mapping[str, Any],
) -> dict[str, Any] | None:
    provenance = _mapping(candidate_record.get("assessment_provenance"))
    if _text(provenance.get("owner")) == "mechanical_projection":
        return _typed_blocker(
            function_id=function_id,
            blocker_id="mechanical_projection_cannot_close_ai_first_gate",
            route_back=_text(function.get("route_back_semantics")),
            function=function,
        )

    missing_refs = [
        ref for ref in _required_record_refs(function) if not _candidate_has_required_ref(candidate_record, ref)
    ]
    if missing_refs:
        return _typed_blocker(
            function_id=function_id,
            blocker_id="missing_ai_first_gate_record_refs",
            route_back=_text(function.get("route_back_semantics")),
            function=function,
            details={"missing_required_record_refs": missing_refs},
        )
    return None


def _independent_quality_evidence_refs(receipt: Mapping[str, Any]) -> list[str]:
    return [
        ref
        for ref in (
            _text(receipt.get("task_record_ref")),
            _text(receipt.get("context_record_ref")),
            _text(receipt.get("receipt_ref")),
        )
        if ref
    ]


def _candidate_has_required_ref(candidate_record: Mapping[str, Any], required_ref: str) -> bool:
    if required_ref == "ai_reviewer_record":
        return bool(
            _text(candidate_record.get("ai_reviewer_record_ref"))
            or _mapping(candidate_record.get("ai_reviewer_record"))
            or _text(_mapping(candidate_record.get("assessment_provenance")).get("owner")) == "ai_reviewer"
        )
    if required_ref == "quality_pack_evidence_refs":
        return bool(_text_list(candidate_record.get("quality_pack_evidence_refs")))
    if required_ref == "reviewer_operating_system_trace":
        return bool(
            _text(candidate_record.get("reviewer_operating_system_trace_ref"))
            or _mapping(candidate_record.get("reviewer_operating_system"))
        )
    if required_ref == "study_charter":
        return bool(_text(candidate_record.get("study_charter_ref")) or _mapping(candidate_record.get("study_charter")))
    if required_ref == "artifact_rebuild_proof":
        return bool(
            _text(candidate_record.get("artifact_rebuild_proof_ref"))
            or _mapping(candidate_record.get("artifact_rebuild_proof"))
        )
    if required_ref == "publication_route_memory_body":
        return bool(
            _text(candidate_record.get("publication_route_memory_body_ref"))
            or _mapping(candidate_record.get("publication_route_memory_body"))
        )
    if required_ref == "memory_writeback_receipt_refs":
        return bool(_text_list(candidate_record.get("memory_writeback_receipt_refs")))
    return bool(_text(candidate_record.get(f"{required_ref}_ref")) or candidate_record.get(required_ref))


def _typed_blocker(
    *,
    function_id: str,
    blocker_id: str,
    route_back: str,
    function: Mapping[str, Any] | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "surface_kind": "mas_ai_first_private_authority_gate_validation",
        "function_id": function_id,
        "status": "typed_blocker",
        "blocker_id": blocker_id,
        "can_close_quality_gate": False,
        "route_back": route_back or "route_back_to_ai_first_gate_repair",
        "forbidden_mechanical_substitute": MECHANICAL_SUBSTITUTE_BY_FUNCTION_ID.get(function_id),
        "program_may_emit_pass_ready_verdict": False,
    }
    if function is not None:
        payload["judgment_mode"] = _text(function.get("judgment_mode"))
        payload["program_role"] = _text(function.get("program_role"))
    if details:
        payload["details"] = dict(details)
    return payload


def _required_record_refs(function: Mapping[str, Any]) -> list[str]:
    refs = function.get("required_record_refs")
    if isinstance(refs, list):
        return [_text(item) for item in refs if _text(item)]
    return []


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


__all__ = ["validate_ai_first_private_authority_gate"]
