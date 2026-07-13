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
) -> dict[str, object]:
    return {
        "surface": "authority_snapshot",
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
            "authorized": paper_write_allowed and bundle_build_allowed and runtime_recovery_allowed,
        },
    }


def _synthetic_route_policy() -> dict[str, object]:
    return {
        "canonical_next_action_fixture": {
            "surface_kind": "next_action_envelope",
            "action_family": "paper.write.prose_repair",
            "work_unit_id": "synthetic_new_study_prose_repair",
            "action_kind": "paper_write",
            "authority_boundary": {
                "action_family_authority": False,
                "exact_work_unit_id_authority": False,
            },
        },
        "legacy_fallback_negative_fixture": {
            "fixture_role": "negative_no_resurrection_guard",
            "work_unit_id": "synthetic_legacy_exact_work_unit",
            "controller_action_type": "legacy_exact_action",
            "control_surface": "legacy_route_projection",
            "must_not_select_default_next_action": True,
            "must_not_authorize_provider_attempt": True,
            "expected_blocking_reason": "controller_route_work_unit_unsupported",
        },
    }


@pytest.mark.parametrize(
    "work_unit_id",
    [
        "dm002_stage_outcome_current_manuscript_story_repair_after_owner_review",
        "dm003_stage_outcome_current_manuscript_prose_repair_after_owner_review",
    ],
)
def test_stage_outcome_paper_write_family_routes_exact_ids_to_paper_write_not_submission_materialize(
    work_unit_id: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.authority_route_gate")
    route_context = {
        "authority_snapshot": _snapshot(
            gate_state="blocked",
            gate_blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
            bundle_build_allowed=False,
        ),
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "action_family": "paper.write.prose_repair",
            "requires_human_confirmation": False,
            "source_eval_id": f"publication-eval::{work_unit_id}::latest",
            "work_unit_fingerprint": f"stage-outcome::{work_unit_id}",
        },
    }

    paper_write_gate = module.authorize_authority_route("paper_write", route_context)
    submission_gate = module.authorize_authority_route("submission_materialize", route_context)

    assert paper_write_gate["authorized"] is True
    assert paper_write_gate["controller_route_gate"]["action_family"] == "paper.write.prose_repair"
    assert paper_write_gate["controller_route_gate"]["work_unit_id"] == work_unit_id
    assert paper_write_gate["blocking_reasons"] == []
    assert submission_gate["authorized"] is False
    assert submission_gate["controller_route_gate"]["action_family"] == "paper.write.prose_repair"
    assert "controller_route_action_not_allowed_for_work_unit" in (
        submission_gate["controller_route_gate"]["blocking_reasons"]
    )


def test_synthetic_new_study_route_uses_action_family_not_exact_work_unit_mapping() -> None:
    module = importlib.import_module("med_autoscience.controllers.authority_route_gate")
    synthetic_work_unit_id = "dm004_never_mapped_stage_outcome_story_repair"

    base_context = {
        "authority_snapshot": _snapshot(
            gate_state="blocked",
            gate_blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
            bundle_build_allowed=False,
        ),
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": synthetic_work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": "publication-eval::dm004::latest",
            "work_unit_fingerprint": "stage-outcome::dm004::story-repair",
        },
    }
    family_context = {
        **base_context,
        "controller_route_context": {
            **base_context["controller_route_context"],
            "action_family": "paper.write.prose_repair",
        },
    }

    exact_id_only_gate = module.authorize_authority_route("paper_write", base_context)
    family_gate = module.authorize_authority_route("paper_write", family_context)

    assert exact_id_only_gate["authorized"] is False
    assert "controller_route_work_unit_unsupported" in (
        exact_id_only_gate["controller_route_gate"]["blocking_reasons"]
    )
    assert exact_id_only_gate["controller_route_gate"]["action_family"] is None
    assert family_gate["authorized"] is True
    assert family_gate["blocking_reasons"] == []
    assert family_gate["controller_route_gate"]["action_family"] == "paper.write.prose_repair"
    assert family_gate["controller_route_gate"]["work_unit_id"] == synthetic_work_unit_id
    assert family_gate["controller_route_gate"]["action_family_is_authority"] is True
    assert family_gate["controller_route_gate"]["work_unit_id_authority"] is False
    assert family_gate["controller_repair_authorization_ref"]["work_unit_id_role"] == (
        "provenance_currentness_only"
    )


def test_synthetic_next_action_envelope_is_nonbinding_context_for_open_authority_snapshot() -> None:
    module = importlib.import_module("med_autoscience.controllers.authority_route_gate")
    policy = _synthetic_route_policy()
    canonical_next_action = policy["canonical_next_action_fixture"]
    legacy_fallback = policy["legacy_fallback_negative_fixture"]
    assert legacy_fallback["fixture_role"] == "negative_no_resurrection_guard"
    assert legacy_fallback["must_not_select_default_next_action"] is True
    assert legacy_fallback["must_not_authorize_provider_attempt"] is True
    synthetic_work_unit_id = canonical_next_action["work_unit_id"]
    base_context = {
        "authority_snapshot": _snapshot(
            gate_state="blocked",
            gate_blocking_reasons=["publication_supervisor_state.bundle_tasks_downstream_only"],
            paper_write_allowed=False,
            bundle_build_allowed=False,
        )
    }

    legacy_only_gate = module.authorize_authority_route(
        "paper_write",
        {
            **base_context,
            "work_unit_id": legacy_fallback["work_unit_id"],
            "controller_action_type": legacy_fallback["controller_action_type"],
            "control_surface": legacy_fallback["control_surface"],
        },
    )
    unknown_family_gate = module.authorize_authority_route(
        "paper_write",
        {
            **base_context,
            "next_action": {
                **canonical_next_action,
                "action_family": "paper.unknown.synthetic",
            },
        },
    )
    open_snapshot = {"authority_snapshot": _snapshot()}
    context_gate = module.authorize_authority_route(
        "paper_write",
        {
            **open_snapshot,
            "next_action": canonical_next_action,
        },
    )
    snapshot_only_gate = module.authorize_authority_route("paper_write", open_snapshot)
    queue_attempt_fallback_gate = module.authorize_authority_route(
        "paper_write",
        {
            **base_context,
            "action_queue": [
                {
                    "surface_kind": "runtime_queue_row",
                    "action_family": "paper.write.prose_repair",
                    "work_unit_id": synthetic_work_unit_id,
                }
            ],
            "provider_attempt": {
                "surface_kind": "provider_attempt",
                "action_family": "paper.write.prose_repair",
                "work_unit_id": synthetic_work_unit_id,
            },
        },
    )

    assert legacy_only_gate["authorized"] is False
    assert legacy_fallback["expected_blocking_reason"] in (
        legacy_only_gate["controller_route_gate"]["blocking_reasons"]
    )
    assert unknown_family_gate["authorized"] is False
    assert unknown_family_gate["blocking_reasons"]
    assert queue_attempt_fallback_gate["authorized"] is False
    assert "controller_route_gate" not in queue_attempt_fallback_gate
    assert "paper_write_allowed_false" in queue_attempt_fallback_gate["blocking_reasons"]
    assert context_gate == snapshot_only_gate
    assert context_gate["authorized"] is True
    assert context_gate["blocking_reasons"] == []
    assert "controller_route_gate" not in context_gate


@pytest.mark.parametrize(
    "route_action",
    [
        "bundle_build",
        "delivery_sync",
        "submission_materialize",
        "submission_notice_materialize",
    ],
)
def test_synthetic_submission_next_action_cannot_override_authority_snapshot(
    route_action: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.authority_route_gate")
    synthetic_work_unit_id = "dm004_never_mapped_submission_refresh"
    canonical_next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "study_id": "004-synthetic-submission-route",
        "stage_id": "submission_milestone_candidate",
        "action_id": "next-action::dm004::submission-refresh",
        "action_family": "paper.package.submission_minimal",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": synthetic_work_unit_id,
        "work_unit_fingerprint": "stage-outcome::dm004::submission-refresh",
        "authority_boundary": {
            "action_family_authority": False,
            "exact_work_unit_id_authority": False,
        },
    }
    base_context = {
        "authority_snapshot": _snapshot(
            gate_state="blocked",
            gate_blocking_reasons=["runtime_recovery_retry_budget_exhausted"],
            paper_write_allowed=False,
            bundle_build_allowed=False,
        )
    }

    exact_id_only_gate = module.authorize_authority_route(
        route_action,
        {
            **base_context,
            "work_unit_id": synthetic_work_unit_id,
            "controller_action_type": "run_quality_repair_batch",
            "control_surface": "quality_repair_batch",
        },
    )
    context_gate = module.authorize_authority_route(
        route_action,
        {**base_context, "next_action": canonical_next_action},
    )

    assert exact_id_only_gate["authorized"] is False
    assert "controller_route_work_unit_unsupported" in (
        exact_id_only_gate["controller_route_gate"]["blocking_reasons"]
    )
    assert context_gate["authorized"] is False
    assert "controller_route_gate" not in context_gate
    assert f"{context_gate['route_authorization_flag']}_false" in context_gate[
        "blocking_reasons"
    ]
