from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_stage_run_readback.primitives import (
    idempotency_refs as _idempotency_refs,
    mapping as _mapping,
    text_list as _text_list,
    text_value as _text,
)
from med_autoscience.paper_mission_stage_run_readback.receipt_events import (
    DOMAIN_ROUTE_RECEIPT_REF_FIELDS as _DOMAIN_ROUTE_RECEIPT_REF_FIELDS,
    carrier_route_target as _carrier_route_target,
    matches_domain_route_identity as _matches_domain_route_identity,
)


def payload_binds_route_identity(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    return _matches_domain_route_identity(source=payload, carrier=carrier)


def matches_carrier(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    route_back: Mapping[str, Any] | None = None,
) -> bool:
    route_back = _mapping(route_back)
    if _text(closeout.get("surface_kind")) != "stage_attempt_closeout_packet":
        return False
    if _text(closeout.get("study_id")) != _text(carrier.get("study_id")):
        return False
    has_route_identity = carrier_has_opl_route_identity(carrier)
    binds_route_identity = closeout_binds_route_identity(
        closeout=closeout,
        carrier=carrier,
        route_back=route_back,
    )
    if not has_route_identity or not binds_route_identity:
        return False
    if not closeout_matches_route_target(
        closeout=closeout,
        carrier=carrier,
        route_back=route_back,
    ):
        return False
    if (
        non_current_closeout_reason(closeout.get("blocked_reason"))
        or (
            not closeout_binds_exact_route_identity(
                closeout=closeout,
                carrier=carrier,
                route_back=route_back,
            )
            and closeout_idempotency_mismatches_carrier(
                closeout=closeout,
                carrier=carrier,
            )
        )
        or closeout_lacks_current_candidate_binding(
            closeout=closeout,
            carrier=carrier,
            route_back=route_back,
        )
    ):
        return False
    if closeout.get("provider_completion_is_domain_completion") is True:
        return False
    if closeout.get("provider_completion_is_domain_ready") is True:
        return False
    if closeout.get("domain_completion_claimed") is True:
        return False
    if closeout.get("domain_ready_claimed") is True:
        return False
    return closeout_is_record_only(closeout)


def closeout_is_record_only(closeout: Mapping[str, Any]) -> bool:
    boundary = _mapping(closeout.get("authority_boundary"))
    if boundary.get("record_only_surface") is False:
        return False
    if boundary.get("record_only_surface") is True:
        return True
    false_authority_fields = (
        "writes_authority",
        "writes_runtime",
        "writes_yang_authority",
        "writes_current_package",
        "writes_publication_eval",
        "writes_controller_decision",
        "writes_owner_receipt",
        "writes_typed_blocker",
        "writes_human_gate",
        "writes_runtime_queue_or_provider_attempt",
    )
    if not false_authority_fields or not any(
        field in boundary for field in false_authority_fields
    ):
        return False
    if any(
        boundary.get(field) is not False
        for field in false_authority_fields
        if field in boundary
    ):
        return False
    false_claim_fields = (
        "can_claim_paper_progress",
        "can_claim_submission_ready",
        "can_claim_publication_ready",
        "can_claim_current_package",
    )
    return not any(boundary.get(field) is True for field in false_claim_fields)


def closeout_binds_route_identity(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    route_back: Mapping[str, Any] | None = None,
) -> bool:
    return _has_domain_route_identity(carrier) and _canonical_closeout_binds_route_identity(
        closeout=closeout,
        carrier=carrier,
        route_back=_mapping(route_back),
    )


def closeout_idempotency_mismatches_carrier(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    expected = _idempotency_refs(carrier)
    observed = _idempotency_refs(closeout)
    observed.update(_idempotency_refs(_mapping(closeout.get("opl_stage_attempt_receipt"))))
    return bool(expected and observed and not expected.intersection(observed))


def closeout_lacks_current_candidate_binding(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    route_back: Mapping[str, Any] | None = None,
) -> bool:
    route_back = _mapping(route_back)
    expected = _idempotency_refs(carrier)
    if not expected:
        return False
    if closeout_binds_exact_route_identity(
        closeout=closeout,
        carrier=carrier,
        route_back=route_back,
    ):
        return False
    observed = _idempotency_refs(closeout)
    observed.update(_idempotency_refs(_mapping(closeout.get("opl_stage_attempt_receipt"))))
    observed.update(_idempotency_refs(route_back))
    if observed:
        return False
    candidate_refs = closeout_candidate_refs(closeout, route_back)
    if not candidate_refs:
        return True
    return not any(
        _candidate_ref_matches_expected(candidate_ref, expected)
        for candidate_ref in candidate_refs
    )


def closeout_candidate_refs(
    closeout: Mapping[str, Any],
    route_back: Mapping[str, Any] | None = None,
) -> set[str]:
    route_back = _mapping(route_back)
    route_impact = _mapping(closeout.get("route_impact"))
    source_evidence = _mapping(route_back.get("source_evidence"))
    refs = {
        text
        for field in (
            "candidate_ref",
            "candidate_delta_ref",
            "candidate_package_ref",
            "package_manifest_ref",
            "paper_facing_delta_ref",
            "paper_facing_candidate_delta_ref",
            "paper_mission_candidate_package_manifest",
        )
        if (text := _text(closeout.get(field))) is not None
    }
    refs.update(
        text
        for text in (
            _text(route_impact.get("paper_facing_delta_ref")),
            _text(route_impact.get("paper_facing_candidate_delta_ref")),
            _text(route_back.get("candidate_ref")),
            _text(route_back.get("candidate_manifest_ref")),
            _text(route_back.get("candidate_delta_ref")),
            _text(route_back.get("write_repair_candidate_ref")),
            _text(route_back.get("paper_facing_delta_ref")),
            _text(route_back.get("paper_facing_candidate_delta_ref")),
            _text(source_evidence.get("paper_mission_candidate_package_ref")),
            _text(source_evidence.get("paper_facing_candidate_delta_ref")),
        )
        if text is not None
    )
    refs.update(
        text
        for text in _text_list(closeout.get("closeout_refs"))
        if _looks_like_candidate_package_ref(text)
    )
    return refs


def closeout_matches_route_target(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    route_back: Mapping[str, Any],
) -> bool:
    route_target = _carrier_route_target(carrier)
    if route_target is None:
        return True
    observed_stage_ids = {
        value
        for value in (
            _text(closeout.get("stage_id")),
            _text(route_back.get("stage_id")),
        )
        if value is not None
    }
    if route_target in observed_stage_ids:
        return True
    observed_work_unit_ids = {
        value
        for value in (
            _text(closeout.get("work_unit_id")),
            _text(route_back.get("work_unit_id")),
        )
        if value is not None
    }
    return (
        bool(observed_work_unit_ids)
        and _text(carrier.get("work_unit_id")) in observed_work_unit_ids
        and closeout_binds_route_identity(
            closeout=closeout,
            carrier=carrier,
            route_back=route_back,
        )
    )


def closeout_has_route_back_evidence(closeout: Mapping[str, Any]) -> bool:
    if _text(closeout.get("route_back_evidence_ref")) is not None:
        return True
    stage_attempt_receipt = _mapping(closeout.get("opl_stage_attempt_receipt"))
    if _text(stage_attempt_receipt.get("route_back_evidence_ref")) is not None:
        return True
    route_impact = _mapping(closeout.get("route_impact"))
    if _text(route_impact.get("owner_answer_kind")) == "route_back_evidence_ref":
        return _text(route_impact.get("route_back_evidence_ref")) is not None
    for item in closeout.get("closeout_refs") or ():
        if isinstance(item, str):
            if item.endswith("route_back_evidence_packet.json"):
                return True
            continue
        ref = _mapping(item)
        if not ref:
            continue
        if _text(ref.get("ref_kind")) == "route_back_evidence_packet":
            return bool(
                _text(ref.get("workspace_relative_ref"))
                or _text(ref.get("uri"))
                or _text(ref.get("ref"))
            )
    return False


def _looks_like_candidate_package_ref(value: str) -> bool:
    return (
        "paper_mission_candidate_package" in value
        and "package_manifest.json" in value
    )


def _candidate_ref_matches_expected(
    candidate_ref: str,
    expected_refs: set[str],
) -> bool:
    return any(
        candidate_ref in expected_ref or expected_ref in candidate_ref
        for expected_ref in expected_refs
    )


def closeout_binds_exact_route_identity(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    route_back: Mapping[str, Any] | None = None,
) -> bool:
    return _has_domain_route_identity(carrier) and _canonical_closeout_binds_route_identity(
        closeout=closeout,
        carrier=carrier,
        route_back=_mapping(route_back),
    )


def route_ref_matches(left: str | None, right: str | None) -> bool:
    return left is not None and left == right


def non_current_closeout_reason(value: object) -> bool:
    reason = _text(value)
    if reason is None:
        return False
    return reason == "stage_attempt_currentness_mismatch" or reason.startswith(
        "operator_retired_stale_runtime_residue:"
    )


def carrier_has_opl_route_identity(carrier: Mapping[str, Any]) -> bool:
    base_identity_present = (
        _text(carrier.get("study_id")) is not None
        and _text(carrier.get("work_unit_id")) is not None
        and _text(carrier.get("work_unit_fingerprint")) is not None
    )
    if not base_identity_present:
        return False
    return _has_domain_route_identity(carrier)


def _has_domain_route_identity(source: Mapping[str, Any]) -> bool:
    return all(_text(source.get(field)) is not None for field in _DOMAIN_ROUTE_RECEIPT_REF_FIELDS)


def _canonical_closeout_binds_route_identity(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    route_back: Mapping[str, Any],
) -> bool:
    for source in (
        closeout,
        route_back,
        _mapping(closeout.get("opl_stage_attempt_receipt")),
        _mapping(route_back.get("opl_stage_attempt_receipt")),
    ):
        if _matches_domain_route_identity(source=source, carrier=carrier):
            return True
    return False
