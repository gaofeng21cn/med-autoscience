from __future__ import annotations

import importlib

import pytest


def _snapshot(
    *,
    gate_state: str = "open",
    paper_write_allowed: bool = True,
    bundle_build_allowed: bool = True,
    runtime_recovery_allowed: bool = True,
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
            "blocking_reasons": ["supervisor_only"] if gate_state != "open" else [],
        },
        "route_authorization": {
            "paper_write_allowed": paper_write_allowed,
            "bundle_build_allowed": bundle_build_allowed,
            "runtime_recovery_allowed": runtime_recovery_allowed,
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
