from __future__ import annotations

import importlib
import importlib.util


RETIRED_CONTROLLER_PACKAGES = (
    "med_autoscience.controllers.current_work_unit",
    "med_autoscience.controllers.domain_action_request_materializer",
    "med_autoscience.controllers.paper_recovery_state",
    "med_autoscience.controllers.provider_admission",
)


def _module_absent(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is None
    except ModuleNotFoundError:
        return True


def _legacy_payload() -> dict[str, object]:
    legacy_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "legacy-write-repair",
        "work_unit_fingerprint": "legacy-write-repair::fingerprint",
    }
    return {
        "study_id": "002-dm-china-us-mortality-attribution",
        "current_executable_owner_action": legacy_action,
        "current_work_unit": {"state": {"current_executable_owner_action": legacy_action}},
        "domain_transition": {"next_work_unit": {"unit_id": "legacy-write-repair"}},
        "paper_recovery_state": {
            "next_safe_action": {"successor_owner_action": legacy_action}
        },
        "provider_admission": {"status": "ready"},
    }


def test_legacy_private_next_action_controller_packages_are_physically_retired() -> None:
    assert all(_module_absent(name) for name in RETIRED_CONTROLLER_PACKAGES)


def test_missing_next_action_does_not_resurrect_legacy_owner_inputs() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress.canonical_owner_action_projection"
    )

    assert projection.build_canonical_owner_action_projection(_legacy_payload()) is None


def test_domain_handler_exports_only_identity_complete_next_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff.domain_handler_export"
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "action_id": "next-action-owner-route",
        "idempotency_key": "next-action-owner-route::idempotency",
        "action_family": "paper.write.prose_repair",
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "canonical-write-repair",
        "work_unit_fingerprint": "canonical-write-repair::fingerprint",
        "expected_output_contract": {
            "output_kind": "opl_domain_route_transition_receipt"
        },
    }

    assert module._export_current_owner_action(
        study={"current_owner_action": _legacy_payload()["current_executable_owner_action"]},
        current_progress={**_legacy_payload(), "next_action": next_action},
    ) == next_action
    assert module._export_current_owner_action(
        study={"current_owner_action": _legacy_payload()["current_executable_owner_action"]},
        current_progress=_legacy_payload(),
    ) == {}


def test_next_action_cleanup_does_not_back_project_legacy_owner_surfaces() -> None:
    mission_summary = importlib.import_module(
        "med_autoscience.controllers.study_progress.mission_summary"
    )
    payload = {
        **_legacy_payload(),
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_family": "paper.package.submission_minimal",
            "action_type": "materialize_submission_ready_owner_verdict_or_human_gate",
            "study_id": "002-dm-china-us-mortality-attribution",
            "owner": "mas_authority_kernel",
            "work_unit_id": "submission_ready_authority_closeout",
            "work_unit_fingerprint": "sha256:submission-authority",
        },
    }

    cleaned = mission_summary.without_legacy_next_action_authority(payload)

    assert cleaned["next_action"]["surface_kind"] == "mas_next_action_envelope"
    assert "current_executable_owner_action" not in cleaned
    assert "current_work_unit" not in cleaned
    assert cleaned["legacy_next_action_authority_retired"]["authority"] == (
        "NextActionEnvelope"
    )


def test_retired_successor_diagnostic_producers_stay_absent() -> None:
    modules = (
        "med_autoscience.controllers.study_progress.owner_action_diagnostics.action_types",
        "med_autoscience.controllers.study_progress.owner_action_diagnostics.non_advancing_terminal_closeout",
        "med_autoscience.controllers.study_progress.owner_action_diagnostics.paper_recovery",
        "med_autoscience.controllers.study_progress.owner_action_diagnostics.repair_progress",
        "med_autoscience.controllers.study_progress.owner_action_diagnostics.stage_artifact_index",
        "med_autoscience.controllers.study_progress.owner_action_diagnostics.terminal_next_forced_delta",
    )

    assert all(_module_absent(name) for name in modules)
