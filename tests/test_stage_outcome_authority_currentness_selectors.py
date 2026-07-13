from __future__ import annotations

from med_autoscience.controllers.stage_outcome_authority import (
    consumed_transition_currentness,
    fresh_progress_owner_actions,
    owner_request_currentness,
    owner_route_selection,
    persisted_dispatches,
    scan_route_currentness,
    stage_native_dispatch_selection,
)
from tests.stage_outcome_authority_helpers import opl_execution_authorization
from tests.stage_outcome_authority_helpers import write_json
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.opl_stage_attempt_readback_helpers import opl_stage_attempt_readback


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
ACTION_TYPE = "run_quality_repair_batch"
WORK_UNIT_ID = "medical_prose_write_repair"
WORK_UNIT_FINGERPRINT = "publication-blockers::0915410f804b3697"


def test_owner_request_route_requires_every_explicit_route_context_currentness_field() -> None:
    identity = {
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
        "source_eval_id": "publication-eval::current",
        "action_fingerprint": "sha256:action-current",
        "truth_epoch": "truth::current",
        "runtime_health_epoch": "runtime-health::current",
        "route_epoch": "route::current",
    }
    current_study = {
        "ai_route_context": {
            "surface_kind": "mas_ai_route_context",
            "route_selection_owner": "codex_cli",
            "currentness_basis": identity,
        }
    }

    assert owner_request_currentness.route_basis_matches_current_study(
        request_route={"source_refs": {"owner_route_currentness_basis": identity}},
        current_study=current_study,
        consumed_transition_route={},
    )
    for missing_key in identity:
        incomplete = {key: value for key, value in identity.items() if key != missing_key}
        assert not owner_request_currentness.route_basis_matches_current_study(
            request_route={"source_refs": {"owner_route_currentness_basis": incomplete}},
            current_study=current_study,
            consumed_transition_route={},
        )
    assert not owner_request_currentness.route_basis_matches_current_study(
        request_route={
            "source_refs": {
                "owner_route_currentness_basis": {
                    **identity,
                    "runtime_health_epoch": "runtime-health::stale",
                }
            }
        },
        current_study=current_study,
        consumed_transition_route={},
    )


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


def test_live_provider_attempt_route_accepts_bound_opl_stage_attempt_readback() -> None:
    dispatch = _running_attempt_dispatch()
    readback = opl_stage_attempt_readback(
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
                    "opl_stage_attempt_readback": readback,
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


def test_stage_native_workspace_next_action_file_is_not_default_dispatch_authority(tmp_path) -> None:
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, STUDY_ID, quest_id=f"quest-{STUDY_ID}")
    write_json(
        study_root / "control" / "next_action.json",
        {
            "schema_version": 1,
            "status": "ready_for_owner_action",
            "action_type": ACTION_TYPE,
            "owner": "write",
            "source_surface": "control/next_action.json",
            "current_stage_id": "08-publication_package_handoff",
            "semantic_route_boundary": {
                "semantic_route_owner": "codex_cli",
                "intent_can_write_stage_current_pointer": False,
                "intent_can_write_stage_run_terminal_state": False,
                "intent_can_publish_current_owner_delta": False,
            },
            "current_work_unit_binding": {
                "source": "canonical_current_work_unit",
                "work_unit_id": WORK_UNIT_ID,
                "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
            },
        },
    )
    route = _owner_route()
    dispatch = _stage_native_dispatch(route=route)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / f"{ACTION_TYPE}.json"
    )
    write_json(dispatch_path, {**dispatch, "refs": {"dispatch_path": str(dispatch_path)}})
    consumer_payload = {
        "ai_route_contexts": [
            {**dispatch, "refs": {"dispatch_path": str(dispatch_path)}}
        ]
    }

    assert not hasattr(stage_native_dispatch_selection, "next_action")
    assert not hasattr(stage_native_dispatch_selection, "next_action_matches_dispatch")
    assert persisted_dispatches.selected_dispatches(
        profile=profile,
        study_id=STUDY_ID,
        action_types=(),
        consumer_payload=consumer_payload,
        consumer_latest_path=profile.workspace_root / "missing-consumer-latest.json",
        scan_payload={"studies": []},
        supported_action_types=frozenset({ACTION_TYPE}),
        dispatch_relative_root=dispatch_path.parent.relative_to(study_root),
        fresh_progress={},
    ) == []


def test_ai_route_context_is_not_materialized_as_a_blocker_dispatch(tmp_path) -> None:
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, STUDY_ID, quest_id=f"quest-{STUDY_ID}")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / f"{ACTION_TYPE}.json"
    )
    consumer_payload = {
        "ai_route_contexts": [
            {
                "surface": "mas_ai_route_context_projection",
                "projection_only": True,
                "owner_callable_carrier_projection_only": True,
                "study_id": STUDY_ID,
                "action_type": ACTION_TYPE,
                "dispatch_status": "context_available",
                "refs": {"dispatch_path": str(dispatch_path)},
            }
        ]
    }

    selected = persisted_dispatches.selected_dispatches(
        profile=profile,
        study_id=STUDY_ID,
        action_types=(ACTION_TYPE,),
        consumer_payload=consumer_payload,
        consumer_latest_path=profile.workspace_root / "missing-consumer-latest.json",
        scan_payload={"studies": []},
        supported_action_types=frozenset({ACTION_TYPE}),
        dispatch_relative_root=dispatch_path.parent.relative_to(study_root),
        fresh_progress={},
    )

    assert selected == []


def test_current_execution_proof_drives_stage_native_dispatch_without_envelope() -> None:
    route = _owner_route()
    dispatch = _stage_native_dispatch(
        route=route,
        opl_proof=opl_execution_authorization(study_id=STUDY_ID, action_type=ACTION_TYPE),
    )

    assert stage_native_dispatch_selection.dispatch_has_current_execution_proof(
        profile=object(),
        study_id=STUDY_ID,
        dispatch=dispatch,
    ) is True

    selected_route, basis = owner_route_selection.execution_owner_route(
        profile=object(),
        study_id=STUDY_ID,
        action_type=ACTION_TYPE,
        dispatch=dispatch,
        scan_payload={"studies": []},
        fresh_progress={},
    )

    assert selected_route is not None
    assert selected_route["next_owner"] == "write"
    assert selected_route["allowed_actions"] == [ACTION_TYPE]
    assert selected_route["source_refs"]["work_unit_id"] == WORK_UNIT_ID
    assert selected_route["source_refs"]["work_unit_fingerprint"] == WORK_UNIT_FINGERPRINT
    assert basis == "codex_selected_stage_current_execution_proof"


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


def _owner_route() -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": STUDY_ID,
        "quest_id": f"quest-{STUDY_ID}",
        "truth_epoch": f"truth-epoch::{STUDY_ID}::{ACTION_TYPE}",
        "runtime_health_epoch": f"runtime-health::{STUDY_ID}::{ACTION_TYPE}",
        "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
        "source_fingerprint": WORK_UNIT_FINGERPRINT,
        "route_epoch": f"truth-epoch::{STUDY_ID}::{ACTION_TYPE}",
        "current_owner": "mas_controller",
        "next_owner": "write",
        "owner_reason": ACTION_TYPE,
        "allowed_actions": [ACTION_TYPE],
        "blocked_actions": [],
        "idempotency_key": "owner-route::dm003::repair",
        "source_refs": {
            "work_unit_id": WORK_UNIT_ID,
            "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
            "owner_route_currentness_basis": {
                "work_unit_id": WORK_UNIT_ID,
                "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
            },
        },
    }


def _stage_native_dispatch(
    *,
    route: dict[str, object],
    next_action: dict[str, object] | None = None,
    opl_proof: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "surface": "mas_ai_route_context_projection",
        "dispatch_status": "ready",
        "study_id": STUDY_ID,
        "quest_id": f"quest-{STUDY_ID}",
        "action_type": ACTION_TYPE,
        "next_executable_owner": "write",
        "work_unit_id": WORK_UNIT_ID,
        "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
        "owner_route": route,
        "source_action": {
            "authority": "stage_native_workspace_next_action",
            "action_type": ACTION_TYPE,
            "source_surface": "artifacts/reports/medical_publication_surface/latest.json",
            "current_stage_id": "08-publication_package_handoff",
        },
    }
    if next_action is not None:
        payload["next_action"] = next_action
    if opl_proof is not None:
        payload["opl_execution_authorization"] = opl_proof
    return payload


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
