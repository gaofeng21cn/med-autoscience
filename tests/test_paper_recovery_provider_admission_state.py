from __future__ import annotations

import copy
import importlib

from tests.provider_admission_current_control_helpers import opl_transition_readback


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WORK_UNIT_ID = "medical_prose_write_repair"
FINGERPRINT = "publication-blockers::0915410f804b3697"
IDEMPOTENCY_KEY = f"provider-admission::{STUDY_ID}::{FINGERPRINT}"


def _module():
    return importlib.import_module(
        "med_autoscience.controllers.paper_recovery_state_parts.provider_admission_state"
    )


def _transition_request() -> dict[str, object]:
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_owner": "one-person-lab",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "idempotency_key": IDEMPOTENCY_KEY,
        "source_generation": FINGERPRINT,
        "expected_version": FINGERPRINT,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "aggregate_identity": {
            "aggregate_kind": "study_work_unit",
            "aggregate_id": f"{STUDY_ID}::{WORK_UNIT_ID}",
            "study_id": STUDY_ID,
            "work_unit_id": WORK_UNIT_ID,
            "work_unit_fingerprint": FINGERPRINT,
        },
        "required_postcondition": {
            "kind": "owner_action_ref",
            "runtime_owner": "one-person-lab",
            "runtime_kind": "DomainProgressTransitionRuntime",
        },
    }


def _candidate(*, readback: dict[str, object] | None = None) -> dict[str, object]:
    candidate = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "route_identity_key": IDEMPOTENCY_KEY,
        "attempt_idempotency_key": IDEMPOTENCY_KEY,
        "idempotency_key": IDEMPOTENCY_KEY,
        "next_executable_owner": "write",
        "opl_domain_progress_transition_request": _transition_request(),
    }
    if readback is not None:
        candidate["opl_domain_progress_transition_live_readback"] = readback
    return candidate


def _live_readback() -> dict[str, object]:
    return opl_transition_readback(
        STUDY_ID,
        action_fingerprint=FINGERPRINT,
        work_unit_id=WORK_UNIT_ID,
        request_idempotency_key=IDEMPOTENCY_KEY,
    )


def test_request_only_candidate_is_transition_request_pending_not_provider_admission() -> None:
    state = _module()
    progress = {
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [_candidate()],
    }

    assert state.provider_admission_pending(progress) is False
    assert state.transition_request_pending(progress) is True


def test_same_identity_live_readback_promotes_request_to_provider_admission() -> None:
    state = _module()
    progress = {
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [_candidate(readback=_live_readback())],
    }

    assert state.provider_admission_pending(progress) is True
    assert state.transition_request_pending(progress) is False


def test_cross_identity_live_readback_remains_request_pending() -> None:
    state = _module()
    stale_readback = copy.deepcopy(_live_readback())
    stale_readback["identity"]["aggregate_identity"]["work_unit_id"] = "stale-work-unit"
    progress = {
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [_candidate(readback=stale_readback)],
    }

    assert state.provider_admission_pending(progress) is False
    assert state.transition_request_pending(progress) is True


def test_bare_event_outbox_or_stagerun_fragments_do_not_authorize_admission() -> None:
    state = _module()
    progress = {
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                **_candidate(),
                "opl_domain_progress_transition_event": {
                    "event_id": "dpte-fragment",
                    "runtime_owner": "one-person-lab",
                },
                "opl_domain_progress_transition_outbox_item": {
                    "outbox_item_id": "dpto-fragment",
                    "runtime_owner": "one-person-lab",
                },
                "stage_run_identity": {
                    "stage_run_id": "stage-run-fragment",
                    "route_identity_key": IDEMPOTENCY_KEY,
                    "attempt_idempotency_key": IDEMPOTENCY_KEY,
                },
            }
        ],
    }

    assert state.provider_admission_pending(progress) is False
    assert state.transition_request_pending(progress) is True


def test_current_work_unit_requires_same_identity_live_readback_for_admission() -> None:
    state = _module()
    current_work_unit = {
        **_candidate(readback=_live_readback()),
        "status": "executable_owner_action",
        "state": {
            "provider_admission_pending": True,
            "opl_domain_progress_transition_request": _transition_request(),
        },
    }
    progress = {
        "current_work_unit": current_work_unit,
    }

    assert state.provider_admission_pending(progress) is True
    assert state.transition_request_pending(progress) is False
