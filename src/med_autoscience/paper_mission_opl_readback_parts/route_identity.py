from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_opl_readback_parts.primitives import (
    first_text as _first_text,
    idempotency_refs as _idempotency_refs,
    mapping as _mapping,
    text_list as _text_list,
    text_value as _text,
)
from med_autoscience.paper_mission_opl_readback_parts.receipt_events import (
    carrier_route_target as _carrier_route_target,
)


def payload_binds_route_identity(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    expected_transaction_ref = _text(carrier.get("paper_mission_transaction_ref"))
    expected_route_ref = _text(carrier.get("opl_route_command_ref"))
    if expected_transaction_ref is None or expected_route_ref is None:
        return False
    return (
        _text(payload.get("paper_mission_transaction_ref")) == expected_transaction_ref
        and _text(payload.get("opl_route_command_ref")) == expected_route_ref
    )


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
    closeout_fingerprint = _text(closeout.get("work_unit_fingerprint"))
    if not has_route_identity or not closeout_binds_route_identity(
        closeout=closeout,
        carrier=carrier,
        route_back=route_back,
    ):
        if _text(closeout.get("work_unit_id")) != _text(carrier.get("work_unit_id")):
            return False
        if closeout_fingerprint is not None and closeout_fingerprint != _text(
            carrier.get("work_unit_fingerprint")
        ):
            return False
    if not closeout_matches_route_target(
        closeout=closeout,
        carrier=carrier,
        route_back=route_back,
    ):
        return False
    if has_route_identity and (
        non_current_closeout_reason(closeout.get("blocked_reason"))
        or not closeout_binds_route_identity(
            closeout=closeout,
            carrier=carrier,
            route_back=route_back,
        )
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
    route_back = _mapping(route_back)
    refs = {
        ref
        for ref in (
            _text(closeout.get("stage_packet_ref")),
            _text(closeout.get("paper_mission_transaction_ref")),
            _text(closeout.get("opl_route_command_ref")),
            _text(closeout.get("route_command_ref")),
            _text(route_back.get("stage_packet_ref")),
            _text(route_back.get("paper_mission_transaction_ref")),
            _text(route_back.get("opl_route_command_ref")),
            *_text_list(closeout.get("closeout_refs")),
        )
        if ref is not None
    }
    expected_refs = _carrier_route_identity_refs(carrier)
    return any(
        route_ref_matches(observed_ref, expected_ref)
        for observed_ref in refs
        for expected_ref in expected_refs
    )


def closeout_idempotency_mismatches_carrier(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    expected = _idempotency_refs(carrier)
    observed = _idempotency_refs(closeout)
    observed.update(_idempotency_refs(_mapping(closeout.get("opl_transition_receipt"))))
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
    observed.update(_idempotency_refs(_mapping(closeout.get("opl_transition_receipt"))))
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
            _text(route_back.get("candidate_manifest_ref")),
            _text(route_back.get("candidate_delta_ref")),
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
    route_impact = _mapping(closeout.get("route_impact"))
    if _text(route_impact.get("owner_answer_kind")) == "route_back_evidence_ref":
        return _text(route_impact.get("route_back_evidence_ref")) is not None
    for item in closeout.get("closeout_refs") or ():
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
    route_back = _mapping(route_back)
    expected_transaction_refs = _carrier_transaction_refs(carrier)
    if not expected_transaction_refs:
        return False
    closeout_transaction_ref = _first_text(
        closeout.get("paper_mission_transaction_ref"),
        route_back.get("paper_mission_transaction_ref"),
    )
    if any(
        route_ref_matches(closeout_transaction_ref, expected_transaction_ref)
        for expected_transaction_ref in expected_transaction_refs
    ):
        return True
    stage_packet_ref = _first_text(
        closeout.get("stage_packet_ref"),
        route_back.get("stage_packet_ref"),
    )
    if closeout_has_route_back_evidence(closeout) and any(
        route_ref_matches(stage_packet_ref, expected_transaction_ref)
        for expected_transaction_ref in expected_transaction_refs
    ):
        return True
    expected_stage_refs = {
        ref
        for ref in (
            _text(carrier.get("stage_terminal_decision_ref")),
            *(
                f"{transaction_ref}#stage_terminal_decision"
                for transaction_ref in expected_transaction_refs
            ),
        )
        if ref is not None
    }
    if any(
        route_ref_matches_same_fragment(stage_packet_ref, expected_stage_ref)
        for expected_stage_ref in expected_stage_refs
    ):
        return True
    expected_route_refs = {
        ref
        for ref in (
            _text(carrier.get("opl_route_command_ref")),
            *(
                f"{transaction_ref}#opl_route_command"
                for transaction_ref in expected_transaction_refs
            ),
        )
        if ref is not None
    }
    closeout_refs = {
        ref
        for ref in (
            _text(closeout.get("stage_packet_ref")),
            _text(closeout.get("paper_mission_transaction_ref")),
            _text(closeout.get("opl_route_command_ref")),
            _text(closeout.get("route_command_ref")),
            _text(route_back.get("stage_packet_ref")),
            _text(route_back.get("paper_mission_transaction_ref")),
            _text(route_back.get("opl_route_command_ref")),
            *_text_list(closeout.get("closeout_refs")),
        )
        if ref is not None
    }
    return bool(expected_route_refs) and any(
        route_ref_matches_same_fragment(ref, expected_route_ref)
        for ref in closeout_refs
        for expected_route_ref in expected_route_refs
    )


def _carrier_route_identity_refs(carrier: Mapping[str, Any]) -> set[str]:
    transaction_refs = _carrier_transaction_refs(carrier)
    return {
        ref
        for ref in (
            _text(carrier.get("paper_mission_transaction_ref")),
            _text(carrier.get("stage_terminal_decision_ref")),
            _text(carrier.get("opl_route_command_ref")),
            *transaction_refs,
            *(f"{ref}#stage_terminal_decision" for ref in transaction_refs),
            *(f"{ref}#opl_route_command" for ref in transaction_refs),
        )
        if ref is not None
    }


def _carrier_transaction_refs(carrier: Mapping[str, Any]) -> set[str]:
    refs = {
        ref
        for ref in (
            _text(carrier.get("paper_mission_transaction_ref")),
            _legacy_stage_run_transaction_ref(carrier),
        )
        if ref is not None
    }
    return refs


def _legacy_stage_run_transaction_ref(carrier: Mapping[str, Any]) -> str | None:
    stage_run_ref = _text(carrier.get("stage_run_ref"))
    if stage_run_ref is None:
        return None
    prefix = "opl-stage-run://"
    if not stage_run_ref.startswith(prefix):
        return None
    stage_run_id = stage_run_ref.removeprefix(prefix)
    if not stage_run_id:
        return None
    return f"paper-mission-transaction::{stage_run_id}"


def route_ref_matches(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return False
    if left == right:
        return True
    return _paper_mission_transaction_refs_match(left, right)


def route_ref_matches_same_fragment(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return False
    if left == right:
        return True
    left_base, left_fragment = _split_route_ref(left)
    right_base, right_fragment = _split_route_ref(right)
    if left_fragment != right_fragment:
        return False
    return _paper_mission_transaction_refs_match(left_base, right_base)


def _split_route_ref(value: str) -> tuple[str, str | None]:
    base, separator, fragment = value.partition("#")
    return base, fragment if separator else None


def _paper_mission_transaction_refs_match(left: str, right: str) -> bool:
    left_base = left.split("#", 1)[0]
    right_base = right.split("#", 1)[0]
    if left_base == right_base:
        return True
    if (
        _normalize_paper_mission_transaction_ref(left_base)
        == _normalize_paper_mission_transaction_ref(right_base)
    ):
        return True
    left_parts = left_base.split("::")
    right_parts = right_base.split("::")
    if len(left_parts) < 5 or len(left_parts) != len(right_parts):
        return False
    if left_parts[0] != "paper-mission-transaction":
        return False
    if right_parts[0] != "paper-mission-transaction":
        return False
    return left_parts[2:] == right_parts[2:]


def _normalize_paper_mission_transaction_ref(value: str) -> str:
    parts = value.split("::")
    if not parts or parts[0] != "paper-mission-transaction":
        return value
    normalized: list[str] = []
    index = 0
    while index < len(parts):
        if parts[index] == "followthrough":
            index += 2 if index + 1 < len(parts) else 1
            continue
        normalized.append(parts[index])
        index += 1
    return "::".join(normalized)


def non_current_closeout_reason(value: object) -> bool:
    reason = _text(value)
    if reason is None:
        return False
    return reason == "stage_attempt_currentness_mismatch" or reason.startswith(
        "operator_retired_stale_runtime_residue:"
    )


def carrier_has_opl_route_identity(carrier: Mapping[str, Any]) -> bool:
    return (
        _text(carrier.get("study_id")) is not None
        and _text(carrier.get("work_unit_id")) is not None
        and _text(carrier.get("work_unit_fingerprint")) is not None
        and _text(carrier.get("paper_mission_transaction_ref")) is not None
        and _text(carrier.get("opl_route_command_ref")) is not None
    )
