from __future__ import annotations

import copy
import importlib

import pytest

from tests.opl_transition_readback_helpers import (
    opl_transition_readback,
    opl_transition_replay_audit_readback,
)


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WORK_UNIT_ID = "medical_prose_write_repair"
FINGERPRINT = "publication-blockers::0915410f804b3697"
IDEMPOTENCY_KEY = f"provider-admission::{STUDY_ID}::{FINGERPRINT}"


def _live_readback() -> dict[str, object]:
    return opl_transition_readback(
        STUDY_ID,
        action_fingerprint=FINGERPRINT,
        work_unit_id=WORK_UNIT_ID,
        request_idempotency_key=IDEMPOTENCY_KEY,
    )


def _candidate(readback: dict[str, object]) -> dict[str, object]:
    return {
        "study_id": STUDY_ID,
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FINGERPRINT,
        "route_identity_key": IDEMPOTENCY_KEY,
        "attempt_idempotency_key": IDEMPOTENCY_KEY,
        "idempotency_key": IDEMPOTENCY_KEY,
        "opl_domain_progress_transition_live_readback": readback,
    }


def _set_nested(payload: dict[str, object], path: tuple[str, ...], value: object) -> None:
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def test_trusted_opl_transition_live_readback_requires_full_transaction_shape() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_transition_readback")
    contract = importlib.import_module(
        "med_autoscience.controllers.opl_domain_progress_transition_contract"
    )
    trusted = _live_readback()
    assert module.required_opl_transition_readback_shape() == contract.required_readback_shape()
    assert module.valid_opl_transition_readback(trusted) is True
    assert module.candidate_opl_transition_readback(_candidate(trusted)) == trusted
    assert module.provider_admission_opl_transition_readback(_candidate(trusted)) == trusted


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("runtime_readback_status",), "incomplete_transaction"),
        (("latest_transaction_readback", "outbox_item_present"), False),
        (("identity", "stage_run_identity", "stage_run_id"), ""),
        (("latest_transaction_readback", "event_id"), "dpte-stale"),
        (("latest_transaction_readback", "transaction_id"), "dptx-stale"),
        (("causality", "outbox_item_id"), "dpto-stale"),
        (("projection_metadata", "derived_from_event_id"), "dpte-stale"),
        (("read_model_readback", "identity", "latest_event_id"), "dpte-stale"),
    ],
)
def test_live_readback_rejects_transaction_inconsistency(
    path: tuple[str, ...],
    value: object,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_transition_readback")
    readback = copy.deepcopy(_live_readback())
    _set_nested(readback, path, value)
    assert module.valid_opl_transition_readback(readback) is False


def test_replay_ready_complete_transaction_is_consumable_readback_projection() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_transition_readback")
    replay = opl_transition_replay_audit_readback(
        STUDY_ID,
        action_fingerprint=FINGERPRINT,
        work_unit_id=WORK_UNIT_ID,
        request_idempotency_key=IDEMPOTENCY_KEY,
    )
    candidate = {
        **_candidate({}),
        "opl_domain_progress_transition_result": replay,
    }
    candidate.pop("opl_domain_progress_transition_live_readback")
    readback = module.candidate_opl_transition_readback(candidate)
    assert readback["runtime_readback_status"] == "complete_transaction"
    assert module.valid_opl_transition_readback(readback) is True
    stale = copy.deepcopy(replay)
    stale["aggregate_identity"]["work_unit_id"] = "stale-work-unit"
    assert module.provider_admission_opl_transition_readback(
        {**candidate, "opl_domain_progress_transition_result": stale}
    ) == {}


def test_non_advancing_readback_is_valid_but_not_provider_admission() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_transition_readback")
    readback = copy.deepcopy(_live_readback())
    for target in (readback, readback["read_model_readback"]):
        target["identity"]["transition_kind"] = "NonAdvancingApply"
        target["identity"]["outcome_kind"] = "non_advancing_apply_typed_blocker_ref"
        target["exactly_one_outcome"].update(
            {
                "transition_kind": "NonAdvancingApply",
                "outcome_kind": "non_advancing_apply_typed_blocker_ref",
                "non_advancing_apply": True,
            }
        )
    candidate = _candidate(readback)
    assert module.valid_opl_transition_readback(readback) is True
    assert module.non_advancing_apply_opl_transition_readback(candidate) == readback
    assert module.provider_admission_opl_transition_readback(candidate) == {}
    mixed = copy.deepcopy(_live_readback())
    mixed["exactly_one_outcome"]["non_advancing_apply"] = True
    mixed["read_model_readback"]["exactly_one_outcome"] = mixed["exactly_one_outcome"]
    assert module.valid_opl_transition_readback(mixed) is False


def test_opl_transition_readback_exposes_source_claimability() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_transition_readback")
    runtime = {**_live_readback(), "evidence_source": {
        "source_kind": "opl_runtime_live_readback",
        "source_ref": "opl://runtime/domain-progress/transactions/dptx-1",
    }}
    fixture = {**_live_readback(), "evidence_source": {
        "source_kind": "fixture_or_replay_readback",
        "source_ref": "tests/opl_transition_readback_helpers.py",
    }}
    missing = _live_readback()
    missing.pop("evidence_source")
    runtime_claim = module.opl_transition_readback_source_claimability(runtime)
    fixture_claim = module.opl_transition_readback_source_claimability(fixture)
    missing_claim = module.opl_transition_readback_source_claimability(missing)
    assert runtime_claim["fresh_live_claim_allowed"] is True
    assert runtime_claim["runtime_claimable"] is True
    assert fixture_claim["replay_or_fixture"] is True
    assert fixture_claim["runtime_claimable"] is False
    assert missing_claim["missing_source_kind"] is True


def test_provider_admission_readback_must_match_current_transition_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_transition_readback")
    trusted = _live_readback()
    matching = _candidate(trusted)
    assert module.provider_admission_opl_transition_readback(matching) == trusted
    assert module.provider_admission_opl_transition_readback(
        {"opl_domain_progress_transition_live_readback": trusted}
    ) == {}
    for override in (
        {"work_unit_id": "stale-work-unit"},
        {"route_identity_key": "provider-admission::stale"},
        {"idempotency_key": "provider-admission::stale-request"},
    ):
        assert module.provider_admission_opl_transition_readback(
            {**matching, **override}
        ) == {}


def test_mas_consumer_rejects_legacy_and_log_containers() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_transition_readback")
    trusted = _live_readback()
    weak = {
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "event_id": "legacy-event-only",
        "stage_run_id": "legacy-stage-run-only",
    }
    containers = [
        weak,
        {"entry_kind": "command", "payload": {"command_id": "fragment"}},
        {"entry_kind": "runtime_live_readback", "payload": {
            "opl_domain_progress_transition_runtime_live_readback": trusted
        }},
        {"entry_kind": "generic_result", "payload": {"result": trusted}},
    ]
    assert module.valid_opl_transition_readback(weak) is False
    assert all(module.candidate_opl_transition_readback(item) == {} for item in containers)
    assert not hasattr(module, "opl_transition_readback_from_log_entries")
    assert not hasattr(module, "opl_transition_readback_from_log_file")
