from __future__ import annotations

import importlib

import pytest


def _snapshot(
    *,
    gate_state: str = "open",
    gate_blocking_reasons: list[str] | None = None,
    paper_write_allowed: bool = True,
    bundle_build_allowed: bool = True,
    runtime_recovery_allowed: bool = True,
    cleanup_apply_allowed: bool = True,
) -> dict[str, object]:
    return {
        "surface": "control_plane_snapshot",
        "control_state": "ready",
        "canonical_next_action": "continue",
        "authority_refs": {
            "study_truth": {"epoch": "truth-1"},
            "runtime_health": {"epoch": "health-1"},
        },
        "dispatch_gate": {
            "state": gate_state,
            "blocking_reasons": (
                list(gate_blocking_reasons)
                if gate_blocking_reasons is not None
                else ["supervisor_only"]
                if gate_state != "open"
                else []
            ),
        },
        "route_authorization": {
            "paper_write_allowed": paper_write_allowed,
            "bundle_build_allowed": bundle_build_allowed,
            "runtime_recovery_allowed": runtime_recovery_allowed,
            "cleanup_apply_allowed": cleanup_apply_allowed,
            "authorized": paper_write_allowed and bundle_build_allowed and runtime_recovery_allowed,
        },
    }


def test_route_gate_fails_closed_without_snapshot() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route("paper_write", {})

    assert gate["authorized"] is False
    assert gate["blocking_reasons"] == ["control_plane_snapshot_missing"]


def test_route_gate_blocks_closed_dispatch_gate_and_false_route_flag() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "bundle_build",
        {
            "control_plane_snapshot": _snapshot(
                gate_state="blocked",
                bundle_build_allowed=False,
            ),
        },
    )

    assert gate["authorized"] is False
    assert "dispatch_gate_blocked" in gate["blocking_reasons"]
    assert "bundle_build_allowed_false" in gate["blocking_reasons"]
    assert gate["snapshot_ref"]["study_truth_epoch"] == "truth-1"


def test_route_gate_allows_open_snapshot_for_submission_materialize() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "submission_materialize",
        {"control_plane_snapshot": _snapshot()},
    )

    assert gate["authorized"] is True
    assert gate["projection_only"] is False
    assert gate["blocking_reasons"] == []


def test_route_gate_allows_submission_notice_materialize_with_bundle_build_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "submission_notice_materialize",
        {"control_plane_snapshot": _snapshot()},
    )

    assert gate["authorized"] is True
    assert gate["route_authorization_flag"] == "bundle_build_allowed"
    assert gate["blocking_reasons"] == []


def test_route_gate_blocks_submission_notice_materialize_when_bundle_build_false() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "submission_notice_materialize",
        {"control_plane_snapshot": _snapshot(bundle_build_allowed=False)},
    )

    assert gate["authorized"] is False
    assert gate["route_authorization_flag"] == "bundle_build_allowed"
    assert "bundle_build_allowed_false" in gate["blocking_reasons"]


def test_route_gate_blocks_cleanup_apply_when_route_flag_false() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "cleanup_apply",
        {"control_plane_snapshot": _snapshot(cleanup_apply_allowed=False)},
    )

    assert gate["authorized"] is False
    assert gate["route_authorization_flag"] == "cleanup_apply_allowed"
    assert "cleanup_apply_allowed_false" in gate["blocking_reasons"]


def test_controller_owned_delivery_sync_route_cannot_override_supervisor_only_snapshot() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "delivery_sync",
        {
            "control_plane_snapshot": _snapshot(
                gate_state="blocked",
                bundle_build_allowed=False,
            ),
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "submission_delivery_sync_closure",
                "requires_human_confirmation": False,
                "source_eval_id": "publication-eval::001::latest",
            },
        },
    )

    assert gate["authorized"] is False
    assert gate["controller_route_gate"]["authorized"] is True
    assert gate["controller_repair_authorization_ref"]["surface"] == "controller_repair_authorization"
    assert gate["controller_repair_authorization_ref"]["authorized"] is True
    assert "dispatch_gate_blocked" in gate["blocking_reasons"]
    assert "bundle_build_allowed_false" in gate["blocking_reasons"]


def test_controller_owned_delivery_sync_route_allows_open_snapshot_with_repair_authorization() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "delivery_sync",
        {
            "control_plane_snapshot": _snapshot(),
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "submission_delivery_sync_closure",
                "requires_human_confirmation": False,
                "source_eval_id": "publication-eval::001::latest",
                "gate_fingerprint": "publication-gate::001",
            },
        },
    )

    assert gate["authorized"] is True
    assert gate["controller_route_gate"]["authorized"] is True
    assert gate["controller_repair_authorization_ref"]["source_eval_id"] == "publication-eval::001::latest"
    assert gate["controller_repair_authorization_ref"]["gate_fingerprint"] == "publication-gate::001"
    assert gate["blocking_reasons"] == []


def test_publication_gate_replay_route_authorizes_delivery_sync() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "delivery_sync",
        {
            "control_plane_snapshot": _snapshot(),
            "controller_route_context": {
                "control_surface": "gate_clearing_batch",
                "controller_action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "requires_human_confirmation": False,
                "source_eval_id": "publication-eval::003::latest",
                "work_unit_fingerprint": "publication-blockers::003",
            },
        },
    )

    assert gate["authorized"] is True
    assert gate["controller_route_gate"]["authorized"] is True
    assert gate["controller_repair_authorization_ref"]["work_unit_id"] == "publication_gate_replay"
    assert gate["controller_repair_authorization_ref"]["work_unit_fingerprint"] == "publication-blockers::003"
    assert gate["blocking_reasons"] == []


def test_publication_gate_replay_route_authorizes_delivery_sync_without_snapshot() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "delivery_sync",
        {
            "controller_route_context": {
                "control_surface": "gate_clearing_batch",
                "controller_action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "requires_human_confirmation": False,
                "source_eval_id": "publication-eval::003::latest",
                "work_unit_fingerprint": "publication-blockers::003",
            },
        },
    )

    assert gate["authorized"] is True
    assert gate["snapshot_ref"] is None
    assert gate["controller_route_gate"]["authorized"] is True
    assert gate["controller_repair_authorization_ref"]["work_unit_id"] == "publication_gate_replay"
    assert gate["blocking_reasons"] == []


def test_analysis_claim_evidence_route_authorizes_paper_repair_under_downstream_bundle_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "paper_write",
        {
            "control_plane_snapshot": _snapshot(
                gate_state="blocked",
                gate_blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
                bundle_build_allowed=False,
            ),
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "requires_human_confirmation": False,
                "source_eval_id": "publication-eval::003::latest",
                "work_unit_fingerprint": "publication-blockers::analysis",
            },
        },
    )

    assert gate["authorized"] is True
    assert gate["route_authorization_flag"] == "paper_write_allowed"
    assert gate["controller_route_gate"]["authorized"] is True
    assert gate["controller_repair_authorization_ref"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert gate["blocking_reasons"] == []


def test_analysis_claim_evidence_route_does_not_authorize_bundle_build_under_downstream_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "bundle_build",
        {
            "control_plane_snapshot": _snapshot(
                gate_state="blocked",
                gate_blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
                bundle_build_allowed=False,
            ),
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "requires_human_confirmation": False,
                "source_eval_id": "publication-eval::003::latest",
            },
        },
    )

    assert gate["authorized"] is False
    assert "dispatch_gate_blocked" in gate["blocking_reasons"]
    assert "bundle_build_allowed_false" in gate["blocking_reasons"]
    assert "controller_route_action_not_allowed_for_work_unit" in gate["controller_route_gate"]["blocking_reasons"]


def test_controller_owned_submission_refresh_route_can_proceed_when_only_runtime_recovery_is_exhausted() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "submission_materialize",
        {
            "control_plane_snapshot": _snapshot(
                gate_state="blocked",
                gate_blocking_reasons=["runtime_recovery_retry_budget_exhausted"],
                runtime_recovery_allowed=False,
            ),
            "controller_route_context": {
                "control_surface": "gate_clearing_batch",
                "controller_action_type": "run_gate_clearing_batch",
                "work_unit_id": "submission_minimal_refresh",
                "requires_human_confirmation": False,
                "source_eval_id": "publication-eval::003::latest",
                "work_unit_fingerprint": "submission-minimal::003",
            },
        },
    )

    assert gate["authorized"] is True
    assert gate["controller_route_gate"]["authorized"] is True
    assert gate["blocking_reasons"] == []


def test_controller_owned_route_does_not_authorize_unrelated_action() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "cleanup_apply",
        {
            "control_plane_snapshot": _snapshot(
                gate_state="blocked",
                cleanup_apply_allowed=False,
            ),
            "controller_route_context": {
                "control_surface": "quality_repair_batch",
                "controller_action_type": "run_quality_repair_batch",
                "work_unit_id": "submission_delivery_sync_closure",
                "requires_human_confirmation": False,
            },
        },
    )

    assert gate["authorized"] is False
    assert "cleanup_apply_allowed_false" in gate["blocking_reasons"]
    assert "controller_repair_authorization_blocked" in gate["blocking_reasons"]
    assert "controller_route_action_not_allowed_for_work_unit" in gate["controller_route_gate"]["blocking_reasons"]


def test_route_gate_projection_only_records_generated_surface_policy() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    gate = module.authorize_control_plane_route(
        "delivery_sync",
        {
            "projection_only": True,
            "paths": ["paper/submission_minimal/manuscript.docx", "manuscript/current_package"],
        },
    )

    assert gate["authorized"] is True
    assert gate["projection_only"] is True
    assert "projection_only_generated_surface:manuscript.docx" in gate["blocking_reasons"]
    assert "projection_only_generated_surface:current_package" in gate["blocking_reasons"]
    assert gate["authority_policy"]["generated_delivery_surfaces_can_be_edit_source"] is False
    assert gate["authority_policy"]["generated_delivery_surfaces_can_be_quality_authority"] is False
    assert gate["authority_policy"]["generated_delivery_surfaces_can_be_dispatch_authority"] is False


def test_route_gate_assertion_raises_for_blocked_managed_context() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_route_gate")

    with pytest.raises(PermissionError):
        module.assert_control_plane_route_authorized(
            "paper_write",
            {"control_plane_snapshot": _snapshot(paper_write_allowed=False)},
        )
