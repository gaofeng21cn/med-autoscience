from __future__ import annotations

import importlib
import importlib.util


def _canonical_payload() -> dict[str, object]:
    legacy_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "domain_transition",
        "next_owner": "write",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "legacy-write-repair",
        "work_unit_fingerprint": "legacy-write-repair::fingerprint",
        "action_fingerprint": "legacy-write-repair::fingerprint",
    }
    return {
        "study_id": "002-dm-china-us-mortality-attribution",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "runtime.opl_route",
            "owner": "one-person-lab",
        },
        "canonical_next_action_source": "paper_mission_next_action_envelope",
        "current_executable_owner_action": legacy_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "legacy-write-repair",
            "work_unit_fingerprint": "legacy-write-repair::fingerprint",
            "state": {"source": "current_executable_owner_action"},
        },
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "owner": "write",
            "controller_action": "run_quality_repair_batch",
            "work_unit_fingerprint": "legacy-write-repair::fingerprint",
            "next_work_unit": {"unit_id": "legacy-write-repair"},
        },
        "paper_recovery_state": {
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "successor_owner_action": legacy_action,
            },
        },
    }


def test_canonical_next_action_blocks_legacy_current_owner_producers() -> None:
    payload = _canonical_payload()

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    current_work_unit = importlib.import_module("med_autoscience.controllers.current_work_unit")
    domain_transition = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action_parts.domain_transition"
    )

    assert current_action.build_current_executable_owner_action(payload) is None
    assert current_work_unit.build_current_work_unit(progress=payload) == {}
    assert (
        importlib.util.find_spec(
            "med_autoscience.controllers.domain_action_request_materializer_parts.current_work_unit_action"
        )
        is None
    )
    assert (
        domain_transition.owner_action_from_domain_transition(
            payload,
            surface_kind="current_executable_owner_action",
        )
        is None
    )


def test_canonical_next_action_blocks_provider_admission_current_control_candidate() -> None:
    payload = _canonical_payload()
    provider_actions = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions"
    )

    assert provider_actions._study_current_action_for_provider_admission(payload) is None


def test_missing_canonical_next_action_does_not_resurrect_legacy_default_owner_action() -> None:
    payload = _canonical_payload()
    payload.pop("next_action")
    payload.pop("canonical_next_action_source")

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    assert current_action.build_current_executable_owner_action(payload) is None


def test_legacy_owner_action_selector_has_no_callable_diagnostic_escape_hatch() -> None:
    payload = _canonical_payload()
    payload.pop("next_action")
    payload.pop("canonical_next_action_source")

    current_action = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    assert current_action.build_current_executable_owner_action(payload) is None
    assert not hasattr(current_action, "legacy_current_executable_owner_action_diagnostic")


def test_missing_canonical_next_action_does_not_promote_bare_action_queue() -> None:
    current_work_unit = importlib.import_module("med_autoscience.controllers.current_work_unit")

    work_unit = current_work_unit.build_current_work_unit(
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:legacy-queue-action",
                "action_fingerprint": "sha256:legacy-queue-action",
            }
        ],
        blocked_reason="domain_transition_ai_reviewer_re_eval",
        next_owner="ai_reviewer",
    )

    assert work_unit == {}


def test_missing_canonical_next_action_does_not_resurrect_current_execution_envelope() -> None:
    current_work_unit = importlib.import_module("med_autoscience.controllers.current_work_unit")

    work_unit = current_work_unit.build_current_work_unit(
        current_execution_envelope={
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "legacy-envelope-work-unit",
        },
        blocked_reason="current_work_unit_unresolved",
        next_owner="write",
    )

    assert work_unit == {}
