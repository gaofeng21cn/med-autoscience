from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
)
from med_autoscience.controllers.provider_admission_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission_parts.provider_admission_helpers import (
    mapping as _mapping,
)


def provider_admission_candidate_key(
    candidate: Mapping[str, Any],
) -> tuple[str | None, str | None, str | None, str | None]:
    return (
        _non_empty_text(candidate.get("study_id")),
        _non_empty_text(candidate.get("action_type")),
        _non_empty_text(candidate.get("work_unit_id")),
        _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint")),
    )


def transition_request_key(
    candidate: Mapping[str, Any],
) -> tuple[str | None, str | None, str | None, str | None]:
    return (
        _non_empty_text(candidate.get("study_id")),
        _non_empty_text(candidate.get("action_type")),
        _non_empty_text(candidate.get("work_unit_id")),
        _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint")),
    )


def merge_provider_admission_candidates(
    *candidate_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str | None, str | None, str | None, str | None], int] = {}
    for group in candidate_groups:
        for candidate in group:
            key = _provider_admission_candidate_merge_key(candidate)
            if key in index_by_key:
                existing_index = index_by_key[key]
                existing = merged[existing_index]
                if _provider_admission_identity_rank(candidate) > _provider_admission_identity_rank(existing):
                    merged[existing_index] = _merge_provider_admission_candidate_payloads(
                        existing,
                        candidate,
                    )
                else:
                    merged[existing_index] = _merge_provider_admission_candidate_payloads(
                        candidate,
                        existing,
                    )
                continue
            index_by_key[key] = len(merged)
            merged.append(dict(candidate))
    return merged


def merge_transition_request_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str | None, str | None, str | None, str | None], int] = {}
    for candidate in candidates:
        key = transition_request_key(candidate)
        if key in index_by_key:
            existing_index = index_by_key[key]
            existing = merged[existing_index]
            if _provider_admission_identity_rank(candidate) > _provider_admission_identity_rank(existing):
                merged[existing_index] = _merge_provider_admission_candidate_payloads(
                    existing,
                    candidate,
                )
            else:
                merged[existing_index] = _merge_provider_admission_candidate_payloads(
                    candidate,
                    existing,
                )
            continue
        index_by_key[key] = len(merged)
        merged.append(dict(candidate))
    return merged


def _provider_admission_candidate_merge_key(
    candidate: Mapping[str, Any],
) -> tuple[str | None, str | None, str | None, str | None]:
    opl_readback_key = _provider_admission_opl_transition_readback_merge_key(candidate)
    if opl_readback_key is not None:
        return opl_readback_key
    fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    stable_ref = (
        fingerprint
        or _non_empty_text(candidate.get("route_identity_key"))
        or _non_empty_text(candidate.get("dispatch_path"))
        or _non_empty_text(candidate.get("dispatch_ref"))
    )
    return (
        _non_empty_text(candidate.get("study_id")),
        _non_empty_text(candidate.get("action_type")),
        _non_empty_text(candidate.get("work_unit_id")),
        stable_ref,
    )


def _provider_admission_opl_transition_readback_merge_key(
    candidate: Mapping[str, Any],
) -> tuple[str | None, str | None, str | None, str | None] | None:
    readback = candidate_opl_transition_readback(candidate)
    if not readback:
        return None
    identity = _mapping(readback.get("identity"))
    aggregate = _mapping(identity.get("aggregate_identity"))
    stage_run = _mapping(identity.get("stage_run_identity"))
    stage_run_id = (
        _non_empty_text(stage_run.get("stage_run_id"))
        or _non_empty_text(stage_run.get("route_identity_key"))
        or _non_empty_text(stage_run.get("attempt_idempotency_key"))
    )
    event_id = _non_empty_text(identity.get("latest_event_id"))
    outbox_item_id = _non_empty_text(identity.get("latest_outbox_item_id"))
    transaction_id = _non_empty_text(identity.get("latest_transaction_id"))
    if not all((stage_run_id, event_id, outbox_item_id, transaction_id)):
        return None
    aggregate_study_id = _non_empty_text(aggregate.get("study_id")) or _non_empty_text(
        candidate.get("study_id")
    )
    aggregate_work_unit_id = _non_empty_text(aggregate.get("work_unit_id")) or _non_empty_text(
        candidate.get("work_unit_id")
    )
    aggregate_fingerprint = (
        _non_empty_text(aggregate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint"))
    )
    return (
        aggregate_study_id,
        "opl-runtime-readback",
        aggregate_work_unit_id,
        "::".join(
            item
            for item in (
                aggregate_fingerprint,
                stage_run_id,
                event_id,
                outbox_item_id,
                transaction_id,
            )
            if item is not None
        ),
    )


def _merge_provider_admission_candidate_payloads(
    weaker: Mapping[str, Any],
    stronger: Mapping[str, Any],
) -> dict[str, Any]:
    merged = {
        **dict(weaker),
        **dict(stronger),
        **{
            key: dict(value)
            for key in (
                "current_execution_envelope",
                "paper_progress_policy_result",
                "opl_domain_progress_transition_request",
                "projection_metadata",
                "authority_boundary",
                "stage_transition_authority_boundary",
            )
            if isinstance((value := stronger.get(key)), Mapping)
        },
    }
    for key, value in weaker.items():
        if merged.get(key) in (None, "", [], {}):
            merged[key] = value
    return merged


def _provider_admission_identity_rank(candidate: Mapping[str, Any]) -> tuple[int, int, int, int]:
    stage_packet_refs = [
        item
        for item in candidate.get("stage_packet_refs") or []
        if _non_empty_text(item) is not None
    ]
    has_stage_packet_identity = int(
        _non_empty_text(candidate.get("stage_packet_ref")) is not None
        or bool(stage_packet_refs)
    )
    has_route_identity = int(
        _non_empty_text(candidate.get("route_identity_key")) is not None
        and _non_empty_text(candidate.get("attempt_idempotency_key")) is not None
    )
    basis = _mapping(candidate.get("currentness_basis"))
    has_currentness_basis = int(
        _non_empty_text(basis.get("work_unit_id")) is not None
        and _non_empty_text(basis.get("work_unit_fingerprint")) is not None
        and _non_empty_text(basis.get("truth_epoch")) is not None
        and (
            _non_empty_text(basis.get("runtime_health_epoch")) is not None
            or _non_empty_text(basis.get("source_eval_id")) is not None
        )
    )
    same_tick_materialized = int(
        _non_empty_text(candidate.get("source")) == "same_tick_materialized_dispatch"
        or candidate.get("same_tick_materialized_provider_admission") is True
    )
    return (
        same_tick_materialized,
        has_stage_packet_identity,
        has_route_identity,
        has_currentness_basis,
    )


__all__ = [
    "merge_provider_admission_candidates",
    "merge_transition_request_candidates",
    "provider_admission_candidate_key",
    "transition_request_key",
]
