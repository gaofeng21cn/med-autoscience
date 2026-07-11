from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    provider_admission_opl_transition_readback,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.workspace_contracts import build_workspace_runtime_layout_for_profile

from ..opl_current_control_state_handoff_values import _observability_mapping
from ..shared_base import _mapping_copy, _non_empty_text, _read_json_object

def _domain_progress_transition_command_event_log_path(*, profile: WorkspaceProfile) -> Path:
    return (
        build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
        / "supervision"
        / "domain_progress_transition_runtime"
        / "command_event_log.jsonl"
    )



def _matching_with_live_log_transition_readbacks(
    *,
    profile: WorkspaceProfile,
    matching: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(matching)
    for key in ("action_queue", "transition_request_candidates"):
        candidates = [dict(item) for item in updated.get(key) or [] if isinstance(item, Mapping)]
        if not candidates:
            continue
        attached = _transition_candidates_with_live_log_readback(
            profile=profile,
            candidates=candidates,
        )
        updated[key] = attached
    return updated


def _top_level_provider_admission_candidates_for_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in payload.get("provider_admission_candidates") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id
    ]


def _top_level_transition_request_candidates_for_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in payload.get("transition_request_candidates") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id
    ]


def _transition_candidates_with_live_log_readback(
    *,
    profile: WorkspaceProfile,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    log_path = _domain_progress_transition_command_event_log_path(profile=profile)
    readbacks_by_idempotency_key = _domain_progress_transition_log_readbacks_by_idempotency_key(log_path)
    if not readbacks_by_idempotency_key:
        return [dict(candidate) for candidate in candidates]
    updated: list[dict[str, Any]] = []
    for candidate in candidates:
        item = dict(candidate)
        if candidate_opl_transition_readback(item):
            updated.append(item)
            continue
        key = _transition_request_identity_key(item)
        readback = readbacks_by_idempotency_key.get(key) if key is not None else None
        if readback is not None and provider_admission_opl_transition_readback(
            {**item, "opl_domain_progress_transition_runtime_live_readback": readback},
            require_explicit_identity=True,
        ):
            item["opl_domain_progress_transition_runtime_live_readback"] = readback
            provider_identity = _observability_mapping(item.get("provider_admission_identity"))
            provider_identity["opl_domain_progress_transition_runtime_live_readback"] = readback
            item["provider_admission_identity"] = provider_identity
        updated.append(item)
    return updated


def _transition_request_identity_key(candidate: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(candidate.get("idempotency_key"))
        or _non_empty_text(candidate.get("request_idempotency_key"))
        or _non_empty_text(candidate.get("route_identity_key"))
        or _non_empty_text(candidate.get("attempt_idempotency_key"))
        or _non_empty_text(_observability_mapping(candidate.get("source_refs")).get("attempt_idempotency_key"))
    )


def _domain_progress_transition_log_readbacks_by_idempotency_key(
    path: Path,
) -> dict[str, dict[str, Any]]:
    transactions: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            entry = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, Mapping):
            continue
        if _non_empty_text(entry.get("runtime_id")) != "opl_domain_progress_transition_runtime":
            continue
        idempotency_key = _non_empty_text(entry.get("idempotency_key"))
        transaction_id = _non_empty_text(entry.get("transaction_id"))
        entry_kind = _non_empty_text(entry.get("entry_kind"))
        if idempotency_key is None or transaction_id is None or entry_kind is None:
            continue
        bucket = transactions.setdefault(
            (idempotency_key, transaction_id),
            {
                "idempotency_key": idempotency_key,
                "transaction_id": transaction_id,
            },
        )
        bucket[entry_kind] = dict(entry)
    readbacks: dict[str, dict[str, Any]] = {}
    for (idempotency_key, _transaction_id), transaction in transactions.items():
        readback = _readback_from_domain_progress_transaction(transaction)
        if readback:
            readbacks[idempotency_key] = readback
    return readbacks


def _readback_from_domain_progress_transaction(transaction: Mapping[str, Any]) -> dict[str, Any]:
    command = _observability_mapping(transaction.get("command"))
    event = _observability_mapping(transaction.get("event"))
    outbox = _observability_mapping(transaction.get("outbox_item"))
    command_payload = _observability_mapping(command.get("payload"))
    event_payload = _observability_mapping(event.get("payload"))
    outbox_payload = _observability_mapping(outbox.get("payload"))
    transaction_id = _non_empty_text(transaction.get("transaction_id"))
    idempotency_key = _non_empty_text(transaction.get("idempotency_key"))
    event_id = _non_empty_text(event_payload.get("event_id")) or _non_empty_text(event.get("event_id"))
    outbox_item_id = _non_empty_text(outbox_payload.get("outbox_item_id")) or _non_empty_text(
        outbox.get("outbox_item_id")
    )
    command_id = _non_empty_text(command_payload.get("command_id")) or _non_empty_text(command.get("command_id"))
    aggregate_identity = _observability_mapping(event_payload.get("aggregate_identity")) or _observability_mapping(
        command_payload.get("aggregate_identity")
    ) or _observability_mapping(outbox_payload.get("aggregate_identity"))
    command_stage = _observability_mapping(command_payload.get("stage_run_identity"))
    event_stage = _observability_mapping(event_payload.get("stage_run_identity"))
    outbox_stage = _observability_mapping(outbox_payload.get("stage_run_identity"))
    if any(value is None for value in (transaction_id, idempotency_key, event_id, outbox_item_id, command_id)):
        return {}
    if not aggregate_identity or not command_stage or command_stage != event_stage or command_stage != outbox_stage:
        return {}
    transition_kind = _non_empty_text(event_payload.get("transition_kind")) or "StartProviderAttempt"
    outcome = _observability_mapping(event_payload.get("outcome"))
    outcome_kind = _non_empty_text(outcome.get("kind")) or (
        "non_advancing_apply_typed_blocker_ref"
        if transition_kind == "NonAdvancingApply"
        else "provider_admission_enqueued_or_blocked"
    )
    replay = {
        "surface_kind": "opl_domain_progress_transition_replay_audit",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "authority": False,
        "replay_status": "replay_ready",
        "read_model_projection_consumable": True,
        "exactly_one_complete_transaction": True,
        "transaction_complete": True,
        "transition_count": 1,
        "aggregate_identity": dict(aggregate_identity),
        "aggregate_version": event.get("aggregate_version") or command.get("aggregate_version") or 1,
        "transaction_id": transaction_id,
        "event_id": event_id,
        "outbox_item_id": outbox_item_id,
        "idempotency_key": idempotency_key,
        "command_id": command_id,
        "command_present": True,
        "event_present": True,
        "outbox_item_present": True,
        "same_outbox_identity": True,
        "same_transaction_event_and_outbox": True,
        "same_stage_run_identity": True,
        "stage_run_identity_readback": {
            "surface_kind": "opl_domain_progress_stage_run_identity_readback",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "same_stage_run_identity": True,
            "command_stage_run_identity_present": True,
            "event_stage_run_identity_present": True,
            "outbox_stage_run_identity_present": True,
            "command_stage_run_identity": dict(command_stage),
            "event_stage_run_identity": dict(event_stage),
            "outbox_stage_run_identity": dict(outbox_stage),
            **dict(command_stage),
            "fail_closed_reason": None,
        },
        "exactly_one_outcome": {
            "surface_kind": "opl_domain_progress_exactly_one_outcome",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "selected": True,
            "exactly_one_transition": True,
            "transition_count": 1,
            "transition_kind": transition_kind,
            "outcome_kind": outcome_kind,
            "stable_outcome": outcome.get("stable_outcome") is not False,
            "non_advancing_apply": transition_kind == "NonAdvancingApply",
            "fail_closed": False,
        },
        "projection_metadata": {
            "surface_kind": "opl_domain_progress_transition_replay_projection_metadata",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "authority": False,
            "projection_role": "replay_ready_complete_transaction",
            "read_model_projection_consumable": True,
            "transaction_complete": True,
            "replay_status": "replay_ready",
            "exactly_one_complete_transaction": True,
            "derived_from_event_id": event_id,
            "observed_generation": _non_empty_text(event_payload.get("source_generation"))
            or _non_empty_text(command_stage.get("source_generation")),
            "read_model_rebuild_owner": "one-person-lab",
        },
        "source_generation": _non_empty_text(event_payload.get("source_generation"))
        or _non_empty_text(command_stage.get("source_generation")),
        "expected_version": _non_empty_text(event_payload.get("expected_version"))
        or _non_empty_text(event_payload.get("source_generation"))
        or _non_empty_text(command_stage.get("source_generation")),
    }
    return candidate_opl_transition_readback({"opl_domain_progress_transition_result": replay})
