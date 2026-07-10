from __future__ import annotations

from med_autoscience.domain_projection_profile import (
    build_domain_next_action_projection,
    build_domain_projection_profile,
)


def _next_action() -> dict[str, object]:
    return {
        "surface_kind": "mas_next_action_envelope",
        "action_kind": "owner_action",
        "owner": "medical_writer",
        "stage_id": "manuscript_authoring",
        "action_type": "write_revision",
        "work_unit_id": "revise-results",
        "work_unit_fingerprint": "sha256:work-unit",
        "required_input_refs": ["mas:paper/results.md"],
        "diagnostic_refs": ["mas:review/latest.json"],
    }


def test_domain_projection_profile_uses_canonical_next_action_identity() -> None:
    profile = build_domain_projection_profile()

    assert profile["profile_id"] == "medautoscience.next_action.profile.v1"
    assert profile["projection_surface_kind"] == (
        "opl_domain_next_action_profile_projection"
    )
    assert profile["field_mapping"]["work_unit_id"] == "next_action.work_unit_id"
    assert profile["field_mapping"]["current_owner"] == "next_action.owner"
    assert profile["authority_boundary"]["projection_is_authority"] is False
    assert profile["authority_boundary"]["can_write_domain_truth"] is False


def test_domain_next_action_projection_exposes_refs_without_authority() -> None:
    projection = build_domain_next_action_projection(
        _next_action(),
        domain_display={"study_id": "study-001", "current_blockers": ["claim_gap"]},
    )

    assert projection["surface_kind"] == "opl_domain_next_action_profile_projection"
    assert projection["work_unit_id"] == "revise-results"
    assert projection["work_unit_fingerprint"] == "sha256:work-unit"
    assert projection["current_owner"] == "medical_writer"
    assert projection["source_refs"] == [
        "mas:paper/results.md",
        "mas:review/latest.json",
    ]
    assert projection["authority_boundary"] == {
        "projection_is_authority": False,
        "can_write_domain_truth": False,
        "can_write_current_owner_delta": False,
        "can_write_stage_current_pointer": False,
        "can_write_stage_terminal_state": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_create_human_gate": False,
        "can_mutate_artifact_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "provider_completion_is_domain_progress": False,
    }
    assert projection["domain_display"] == {
        "study_id": "study-001",
        "current_blockers": ["claim_gap"],
    }
