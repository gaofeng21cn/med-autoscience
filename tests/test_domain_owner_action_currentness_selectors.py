from __future__ import annotations

from med_autoscience.controllers.domain_owner_action_dispatch_parts import (
    consumed_transition_currentness,
    fresh_progress_owner_actions,
    scan_route_currentness,
)
from tests.domain_owner_action_dispatch_helpers import opl_execution_authorization
from tests.provider_admission_current_control_helpers import opl_transition_readback


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
ACTION_TYPE = "run_quality_repair_batch"
WORK_UNIT_ID = "medical_prose_write_repair"
WORK_UNIT_FINGERPRINT = "publication-blockers::0915410f804b3697"


def test_owner_action_dispatch_requires_source_eval_when_current_route_has_eval() -> None:
    route = {
        "next_owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "source_refs": {
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "work_unit_fingerprint": "sha256:current",
            "source_eval_id": "publication-eval::current",
            "owner_route_currentness_basis": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "work_unit_fingerprint": "sha256:current",
                "source_eval_id": "publication-eval::current",
            },
        },
    }
    dispatch_without_eval = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "action_type": "return_to_ai_reviewer_workflow",
        "next_executable_owner": "ai_reviewer",
        "owner_route": {
            "next_owner": "ai_reviewer",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "work_unit_fingerprint": "sha256:current",
                "owner_route_currentness_basis": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "work_unit_fingerprint": "sha256:current",
                },
            },
        },
    }

    assert not consumed_transition_currentness.owner_action_matches_dispatch(
        dispatch=dispatch_without_eval,
        route=route,
    )


def test_fresh_progress_current_owner_action_requires_shared_fingerprint() -> None:
    progress = {"study_id": "003-dpcc-primary-care-phenotype-treatment-gap"}
    action = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "action_type": "return_to_ai_reviewer_workflow",
        "next_owner": "ai_reviewer",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "work_unit_fingerprint": "sha256:current",
        "source_eval_id": "publication-eval::current",
    }
    dispatch_without_fingerprint = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "action_type": "return_to_ai_reviewer_workflow",
        "next_executable_owner": "ai_reviewer",
        "owner_route": {
            "next_owner": "ai_reviewer",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "source_eval_id": "publication-eval::current",
                "owner_route_currentness_basis": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "source_eval_id": "publication-eval::current",
                },
            },
        },
    }
    dispatch_with_fingerprint = {
        **dispatch_without_fingerprint,
        "owner_route": {
            **dispatch_without_fingerprint["owner_route"],
            "source_refs": {
                **dispatch_without_fingerprint["owner_route"]["source_refs"],
                "work_unit_fingerprint": "sha256:current",
                "owner_route_currentness_basis": {
                    **dispatch_without_fingerprint["owner_route"]["source_refs"][
                        "owner_route_currentness_basis"
                    ],
                    "work_unit_fingerprint": "sha256:current",
                },
            },
        },
    }

    assert not fresh_progress_owner_actions.current_owner_action_identity_matches_dispatch(
        progress=progress,
        action=action,
        dispatch=dispatch_without_fingerprint,
    )
    assert fresh_progress_owner_actions.current_owner_action_identity_matches_dispatch(
        progress=progress,
        action=action,
        dispatch=dispatch_with_fingerprint,
    )


def test_live_provider_attempt_route_requires_opl_execution_proof() -> None:
    dispatch = _running_attempt_dispatch()
    scan_payload = {"studies": [_running_attempt_study()]}

    assert (
        scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload(
            scan_payload=scan_payload,
            study_id=STUDY_ID,
            dispatch=dispatch,
        )
        is None
    )


def test_live_provider_attempt_route_accepts_trusted_opl_authorization() -> None:
    dispatch = _running_attempt_dispatch()
    scan_payload = {
        "studies": [
            _running_attempt_study(
                opl_provider_attempt={
                    **_running_attempt_payload(),
                    "opl_execution_authorization": opl_execution_authorization(
                        study_id=STUDY_ID,
                        action_type=ACTION_TYPE,
                    ),
                }
            )
        ]
    }

    route = scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload(
        scan_payload=scan_payload,
        study_id=STUDY_ID,
        dispatch=dispatch,
    )

    assert route is not None
    assert route["next_owner"] == "write"
    assert ACTION_TYPE in route["allowed_actions"]


def test_live_provider_attempt_route_accepts_bound_opl_transition_readback() -> None:
    dispatch = _running_attempt_dispatch()
    readback = opl_transition_readback(
        STUDY_ID,
        action_fingerprint=WORK_UNIT_FINGERPRINT,
        work_unit_id=WORK_UNIT_ID,
        route_identity_key="owner-route::dm003::repair",
        attempt_idempotency_key="owner-route::dm003::repair",
        request_idempotency_key="owner-route::dm003::repair",
        stage_run_id="stage-run::dm003::repair",
    )
    scan_payload = {
        "studies": [
            _running_attempt_study(
                opl_provider_attempt={
                    **_running_attempt_payload(),
                    "opl_domain_progress_transition_result": readback,
                }
            )
        ]
    }

    route = scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload(
        scan_payload=scan_payload,
        study_id=STUDY_ID,
        dispatch=dispatch,
    )

    assert route is not None
    assert route["next_owner"] == "write"
    assert ACTION_TYPE in route["allowed_actions"]


def _running_attempt_dispatch() -> dict[str, object]:
    return {
        "study_id": STUDY_ID,
        "action_type": ACTION_TYPE,
        "next_executable_owner": "write",
        "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
        "refs": {"dispatch_path": "runtime/dispatches/run_quality_repair_batch.json"},
        "owner_route": {
            "next_owner": "write",
            "allowed_actions": [ACTION_TYPE],
            "source_refs": {
                "work_unit_id": WORK_UNIT_ID,
                "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
                "owner_route_currentness_basis": {
                    "work_unit_id": WORK_UNIT_ID,
                    "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
                },
            },
        },
        "prompt_contract": {
            "next_work_unit": {"unit_id": WORK_UNIT_ID},
            "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
        },
    }


def _running_attempt_study(
    *,
    opl_provider_attempt: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "study_id": STUDY_ID,
        "running_provider_attempt": True,
        "opl_provider_attempt": opl_provider_attempt or _running_attempt_payload(),
    }


def _running_attempt_payload() -> dict[str, object]:
    return {
        "running_provider_attempt": True,
        "study_id": STUDY_ID,
        "action_type": ACTION_TYPE,
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
        "dispatch_ref": "runtime/dispatches/run_quality_repair_batch.json",
    }
