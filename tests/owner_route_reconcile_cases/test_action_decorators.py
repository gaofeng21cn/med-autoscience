from __future__ import annotations

from med_autoscience.controllers.owner_route_reconcile_parts import action_decorators


def test_decorate_action_defaults_request_only_handoff_packet() -> None:
    result = action_decorators.decorate_action(
        study_id="dm002",
        quest_id="quest-dm002",
        action={"action_type": "run_quality_repair_batch", "owner": "write"},
        request_allowed_write_surfaces=["paper/draft.md"],
        control_allowed_write_surfaces=["runtime/control.json"],
        forbidden_actions=["publish_release"],
    )

    assert result["action_id"] == "supervisor-action::dm002::run_quality_repair_batch::run_quality_repair_batch"
    assert result["status"] == "queued"
    assert result["reason"] == "run_quality_repair_batch"
    assert result["quality_gate_relaxation_allowed"] is False
    assert result["paper_package_mutation_allowed"] is False
    assert result["manual_study_patch_allowed"] is False
    assert result["medical_claim_authoring_allowed"] is False
    assert result["allowed_write_surfaces"] == ["paper/draft.md"]
    assert result["forbidden_actions"] == ["publish_release"]
    assert result["handoff_packet"] == {
        "packet_type": "external_supervisor_handoff",
        "schema_version": 1,
        "study_id": "dm002",
        "quest_id": "quest-dm002",
        "action_type": "run_quality_repair_batch",
        "reason": "run_quality_repair_batch",
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "next_executable_owner": "write",
        "supervisor_authority_boundary": "request_only",
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "allowed_write_surfaces": ["paper/draft.md"],
        "forbidden_actions": ["publish_release"],
    }


def test_decorate_action_uses_control_surfaces_for_external_supervisor() -> None:
    result = action_decorators.decorate_action(
        study_id="dm003",
        quest_id=None,
        action={
            "action_type": "request_opl_stage_attempt",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "authority": "external_supervisor",
        },
        request_allowed_write_surfaces=["paper/draft.md"],
        control_allowed_write_surfaces=["runtime/control.json"],
        forbidden_actions=["write_domain_truth"],
    )

    handoff = result["handoff_packet"]
    assert result["action_id"] == (
        "supervisor-action::dm003::request_opl_stage_attempt::quest_waiting_opl_runtime_owner_route"
    )
    assert handoff["authority"] == "external_supervisor"
    assert handoff["recommended_owner"] == "external_engineering_agent"
    assert handoff["next_executable_owner"] == "external_engineering_agent"
    assert handoff["supervisor_authority_boundary"] == "control_handoff"
    assert handoff["allowed_write_surfaces"] == ["runtime/control.json"]
    assert result["allowed_write_surfaces"] == ["paper/draft.md"]


def test_decorate_action_preserves_explicit_mutation_flags() -> None:
    result = action_decorators.decorate_action(
        study_id="dm004",
        quest_id="quest-dm004",
        action={
            "action_type": "publication_handoff_owner_gate",
            "reason": "publication_gate_blocker",
            "request_owner": "publication_gate_owner",
            "paper_package_mutation_allowed": True,
            "allowed_write_surfaces": ["paper/package.json"],
            "forbidden_actions": ["claim_release_ready"],
        },
        request_allowed_write_surfaces=["paper/draft.md"],
        control_allowed_write_surfaces=["runtime/control.json"],
        forbidden_actions=["claim_release_ready"],
    )

    assert result["paper_package_mutation_allowed"] is True
    assert result["allowed_write_surfaces"] == ["paper/package.json"]
    assert result["forbidden_actions"] == ["claim_release_ready"]
    assert result["handoff_packet"]["owner"] == "publication_gate_owner"
    assert result["handoff_packet"]["request_owner"] == "publication_gate_owner"
