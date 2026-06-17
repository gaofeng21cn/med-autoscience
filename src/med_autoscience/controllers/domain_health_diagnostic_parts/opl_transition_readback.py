from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

OPL_TRANSITION_RUNTIME_OWNER = "one-person-lab"
OPL_TRANSITION_RUNTIME_KIND = "DomainProgressTransitionRuntime"
OPL_TRANSITION_RESULT_SURFACE = "opl_domain_progress_transition_result"
PROVIDER_ADMISSION_OUTCOME = "provider_admission_pending"

REQUIRED_READBACK_SECTIONS = (
    "identity",
    "causality",
    "authority_boundary",
    "exactly_one_outcome",
    "projection_metadata",
)
REQUIRED_RUNTIME_REFS = (
    "event_id",
    "outbox_item_id",
    "stage_run_identity",
)


def valid_opl_transition_readback(value: Mapping[str, Any]) -> bool:
    result = _mapping(value)
    if not result:
        return False
    if _text(result.get("surface_kind")) != OPL_TRANSITION_RESULT_SURFACE:
        return False
    if _text(result.get("runtime_owner")) != OPL_TRANSITION_RUNTIME_OWNER:
        return False
    runtime_kind = _text(result.get("runtime_kind")) or _text(result.get("target_runtime_kind"))
    if runtime_kind != OPL_TRANSITION_RUNTIME_KIND:
        return False
    if _text(result.get("outcome_kind")) != PROVIDER_ADMISSION_OUTCOME:
        return False
    if not _has_runtime_refs(result):
        return False
    return all(
        validator(_mapping(result.get(section)))
        for section, validator in (
            ("identity", _valid_identity),
            ("causality", _valid_causality),
            ("authority_boundary", _valid_authority_boundary),
            ("exactly_one_outcome", _valid_exactly_one_outcome),
            ("projection_metadata", _valid_projection_metadata),
        )
    )


def required_opl_transition_readback_shape() -> dict[str, Any]:
    return {
        "surface_kind": OPL_TRANSITION_RESULT_SURFACE,
        "runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
        "runtime_kind": OPL_TRANSITION_RUNTIME_KIND,
        "required_sections": list(REQUIRED_READBACK_SECTIONS),
        "required_runtime_refs": list(REQUIRED_RUNTIME_REFS),
        "accepted_outcome_kind": PROVIDER_ADMISSION_OUTCOME,
        "deprecated_projection_fields_not_authority": [
            "stage_run_id",
            "event_id_without_causality",
            "outbox_item_id_without_authority_boundary",
        ],
    }


def _has_runtime_refs(result: Mapping[str, Any]) -> bool:
    stage_run_identity = _mapping(result.get("stage_run_identity"))
    return (
        _text(result.get("event_id")) is not None
        and _text(result.get("outbox_item_id")) is not None
        and (
            _text(stage_run_identity.get("stage_run_id")) is not None
            or _text(stage_run_identity.get("stage_run_identity_ref")) is not None
        )
    )


def _valid_identity(identity: Mapping[str, Any]) -> bool:
    return all(
        _text(identity.get(key)) is not None
        for key in (
            "study_id",
            "work_unit_id",
            "work_unit_fingerprint",
            "route_identity_key",
            "attempt_idempotency_key",
        )
    )


def _valid_causality(causality: Mapping[str, Any]) -> bool:
    if causality.get("derived_from_request") is not True:
        return False
    request_key = _text(causality.get("mas_transition_request_idempotency_key")) or _text(
        causality.get("transition_request_idempotency_key")
    )
    return (
        request_key is not None
        and _text(causality.get("source_generation")) is not None
        and _text(causality.get("expected_version")) is not None
    )


def _valid_authority_boundary(boundary: Mapping[str, Any]) -> bool:
    return (
        _text(boundary.get("runtime_owner")) == OPL_TRANSITION_RUNTIME_OWNER
        and _text(boundary.get("domain_state_owner")) == "med-autoscience"
        and boundary.get("mas_can_authorize_provider_admission") is False
        and boundary.get("mas_can_create_opl_outbox_record") is False
        and boundary.get("mas_can_create_opl_event") is False
        and boundary.get("mas_can_create_opl_stage_run") is False
        and boundary.get("provider_completion_is_domain_completion") is False
    )


def _valid_exactly_one_outcome(outcome: Mapping[str, Any]) -> bool:
    selected = _text(outcome.get("selected"))
    allowed = {
        text
        for item in outcome.get("allowed") or []
        if (text := _text(item)) is not None
    }
    if selected != PROVIDER_ADMISSION_OUTCOME or selected not in allowed:
        return False
    rejected = [
        text
        for item in outcome.get("rejected") or []
        if (text := _text(item)) is not None
    ]
    return selected not in rejected


def _valid_projection_metadata(metadata: Mapping[str, Any]) -> bool:
    return (
        metadata.get("authority") is False
        and _text(metadata.get("projection_owner")) == OPL_TRANSITION_RUNTIME_OWNER
        and _text(metadata.get("consumer")) == "med-autoscience"
        and _text(metadata.get("observed_generation")) is not None
    )


def candidate_opl_transition_readback(candidate: Mapping[str, Any]) -> dict[str, Any]:
    for value in (
        candidate.get("opl_domain_progress_transition_result"),
        candidate.get("opl_domain_progress_runtime_result"),
        candidate.get("opl_runtime_result"),
        _mapping(candidate.get("paper_progress_policy_result")).get("opl_runtime_result"),
        _mapping(candidate.get("state")).get("opl_domain_progress_transition_result"),
        _mapping(candidate.get("state")).get("opl_runtime_result"),
    ):
        result = _mapping(value)
        if valid_opl_transition_readback(result):
            return dict(result)
    return {}


def opl_transition_readback_from_log_entries(
    entries: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    *,
    idempotency_key: str,
    study_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> dict[str, Any]:
    transaction_entries = _matching_transaction_entries(
        entries,
        idempotency_key=idempotency_key,
        study_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )
    if not transaction_entries:
        return {}
    command = _entry_payload(transaction_entries, "command")
    event = _entry_payload(transaction_entries, "event")
    outbox = _entry_payload(transaction_entries, "outbox_item")
    if not command or not event or not outbox:
        return {}
    event_id = _text(event.get("event_id"))
    outbox_item_id = _text(outbox.get("outbox_item_id"))
    if event_id is None or outbox_item_id is None:
        return {}
    observed_idempotency_key = _transaction_idempotency_key(transaction_entries) or idempotency_key
    stage_run_identity = (
        _mapping(event.get("stage_run_identity"))
        or _mapping(outbox.get("stage_run_identity"))
        or _mapping(command.get("stage_run_identity"))
    )
    route_identity_key = _text(stage_run_identity.get("route_identity_key")) or observed_idempotency_key
    attempt_idempotency_key = _text(stage_run_identity.get("attempt_idempotency_key")) or observed_idempotency_key
    source_generation = (
        _text(event.get("source_generation"))
        or _text(command.get("source_generation"))
        or _text(stage_run_identity.get("source_generation"))
    )
    expected_version = _text(event.get("expected_version")) or _text(command.get("expected_version"))
    if source_generation is None or expected_version is None:
        return {}
    causality = {
        "mas_transition_request_idempotency_key": observed_idempotency_key,
        "source_generation": source_generation,
        "expected_version": expected_version,
        "derived_from_request": True,
        "command_id": _text(event.get("command_id")) or _text(command.get("command_id")),
        "transaction_id": _text(_entry_for_kind(transaction_entries, "event").get("transaction_id")),
    }
    if observed_idempotency_key != idempotency_key:
        causality["consumer_requested_idempotency_key"] = idempotency_key
    result = {
        "surface_kind": OPL_TRANSITION_RESULT_SURFACE,
        "runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
        "runtime_kind": OPL_TRANSITION_RUNTIME_KIND,
        "transition_kind": _text(event.get("transition_kind")) or _text(command.get("transition_kind")),
        "outcome_kind": PROVIDER_ADMISSION_OUTCOME,
        "event_id": event_id,
        "outbox_item_id": outbox_item_id,
        "stage_run_identity": {
            key: value
            for key, value in {
                **dict(stage_run_identity),
                "stage_run_identity_ref": _text(stage_run_identity.get("stage_run_identity_ref")),
                "observed_generation": source_generation,
            }.items()
            if value not in (None, "", [], {})
        },
        "identity": {
            "study_id": study_id,
            "quest_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "route_identity_key": route_identity_key,
            "attempt_idempotency_key": attempt_idempotency_key,
        },
        "causality": causality,
        "authority_boundary": {
            "runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
            "domain_state_owner": "med-autoscience",
            "mas_can_authorize_provider_admission": False,
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
            "provider_completion_is_domain_completion": False,
        },
        "exactly_one_outcome": {
            "selected": PROVIDER_ADMISSION_OUTCOME,
            "allowed": [
                PROVIDER_ADMISSION_OUTCOME,
                "running_provider_attempt",
                "owner_receipt_ref",
                "typed_blocker_ref",
                "human_gate_ref",
                "route_back_evidence_ref",
                "NonAdvancingApply",
            ],
            "rejected": [],
            "source_outcome_kind": _text(_mapping(event.get("outcome")).get("kind")),
        },
        "projection_metadata": {
            "authority": False,
            "projection_owner": OPL_TRANSITION_RUNTIME_OWNER,
            "consumer": "med-autoscience",
            "observed_generation": source_generation,
            "derived_from_event_id": event_id,
            "derived_from_outbox_item_id": outbox_item_id,
        },
    }
    return result if valid_opl_transition_readback(result) else {}


def opl_transition_readback_from_log_file(
    log_path: Path,
    *,
    idempotency_key: str,
    study_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> dict[str, Any]:
    entries = _read_jsonl_records(log_path)
    if not entries:
        return {}
    return opl_transition_readback_from_log_entries(
        entries,
        idempotency_key=idempotency_key,
        study_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )


def has_opl_transition_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(candidate_opl_transition_readback(candidate))


def _read_jsonl_records(path: Path) -> list[Mapping[str, Any]]:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records: list[Mapping[str, Any]] = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return []
        record = _mapping(value)
        if not record:
            return []
        records.append(record)
    return records


def _matching_transaction_entries(
    entries: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    *,
    idempotency_key: str,
    study_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> list[Mapping[str, Any]]:
    matches = [
        entry
        for entry in entries
        if _entry_matches_identity(
            entry,
            idempotency_key=idempotency_key,
            study_id=study_id,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
        )
    ]
    if transaction_entries := _first_complete_transaction(matches):
        return transaction_entries
    aggregate_matches = [
        entry
        for entry in entries
        if _entry_matches_aggregate_identity(
            entry,
            study_id=study_id,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
        )
    ]
    return _first_complete_transaction(aggregate_matches)


def _first_complete_transaction(entries: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    transaction_ids: list[str] = []
    for entry in entries:
        transaction_id = _text(entry.get("transaction_id"))
        if transaction_id is not None and transaction_id not in transaction_ids:
            transaction_ids.append(transaction_id)
    for transaction_id in reversed(transaction_ids):
        transaction_entries = [
            entry for entry in entries if _text(entry.get("transaction_id")) == transaction_id
        ]
        if (
            _entry_payload(transaction_entries, "command")
            and _entry_payload(transaction_entries, "event")
            and _entry_payload(transaction_entries, "outbox_item")
        ):
            return transaction_entries
    return []


def _entry_matches_identity(
    entry: Mapping[str, Any],
    *,
    idempotency_key: str,
    study_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> bool:
    if _text(entry.get("idempotency_key")) != idempotency_key:
        return False
    return _entry_matches_aggregate_identity(
        entry,
        study_id=study_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )


def _entry_matches_aggregate_identity(
    entry: Mapping[str, Any],
    *,
    study_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> bool:
    aggregate_identity = _mapping(entry.get("aggregate_identity"))
    return (
        _text(aggregate_identity.get("study_id")) == study_id
        and _text(aggregate_identity.get("work_unit_id")) == work_unit_id
        and _text(aggregate_identity.get("work_unit_fingerprint")) == work_unit_fingerprint
    )


def _entry_payload(entries: list[Mapping[str, Any]], entry_kind: str) -> Mapping[str, Any]:
    return _mapping(_entry_for_kind(entries, entry_kind).get("payload"))


def _transaction_idempotency_key(entries: list[Mapping[str, Any]]) -> str | None:
    for entry in entries:
        if text := _text(entry.get("idempotency_key")):
            return text
        payload = _mapping(entry.get("payload"))
        if text := _text(payload.get("idempotency_key")):
            return text
    return None


def _entry_for_kind(entries: list[Mapping[str, Any]], entry_kind: str) -> Mapping[str, Any]:
    for entry in entries:
        if _text(entry.get("entry_kind")) == entry_kind:
            return entry
    return {}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "OPL_TRANSITION_RUNTIME_KIND",
    "OPL_TRANSITION_RUNTIME_OWNER",
    "OPL_TRANSITION_RESULT_SURFACE",
    "candidate_opl_transition_readback",
    "has_opl_transition_readback",
    "opl_transition_readback_from_log_file",
    "opl_transition_readback_from_log_entries",
    "required_opl_transition_readback_shape",
    "valid_opl_transition_readback",
]
