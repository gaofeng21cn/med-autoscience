from __future__ import annotations

from med_autoscience.paper_mission_candidate_package import (
    REQUIRED_AUTHORITY_MATERIALIZATION_REFS,
    REQUIRED_QUALITY_GATE_REFS,
    paper_mission_owner_blocker_packet,
    paper_mission_owner_consumption_request,
    paper_mission_submission_milestone_checklist,
)


def test_submission_milestone_checklist_exposes_pending_owner_authority_refs() -> None:
    checklist = paper_mission_submission_milestone_checklist(
        output_kinds=[
            "manuscript_patch_plan",
            "reviewer_gate_response_draft",
            "owner_decision_packet",
        ],
        owner_blocker_context=True,
    )

    assert checklist["authority_materialized"] is False
    assert {
        item["ref_kind"]
        for item in checklist["required_authority_materialization_refs"]
    } == set(REQUIRED_AUTHORITY_MATERIALIZATION_REFS)
    assert {
        item["ref_kind"] for item in checklist["required_quality_gate_refs"]
    } == set(REQUIRED_QUALITY_GATE_REFS)
    assert all(
        item["candidate_package_can_satisfy_without_authority"] is False
        for item in checklist["required_authority_materialization_refs"]
    )


def test_owner_packets_keep_authority_and_reviewer_gaps_explicit() -> None:
    readback = {
        "study_id": "study-1",
        "mission_id": "mission-1",
        "stage_terminal_decision": {
            "decision_kind": "typed_blocker",
            "status": "blocked",
            "reason": "missing_opl_runtime_readback",
            "blocker_id": "typed-blocker:demo",
        },
        "opl_route_command": {
            "command_kind": "stop_with_typed_blocker",
            "target": "one-person-lab",
        },
        "next_owner_or_human_decision": {"next_owner": "one-person-lab"},
        "opl_runtime_readback_status": "waiting_for_opl_runtime_live_readback",
    }
    summary = {"next_owner": "one-person-lab"}
    handoff = {"status": "not_routed_to_mission_executor"}

    owner_blocker = paper_mission_owner_blocker_packet(
        readback=readback,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=handoff,
        forbidden_authority_writes=["owner_receipt"],
        forbidden_authority_claims=["publication_ready"],
    )
    owner_request = paper_mission_owner_consumption_request(
        readback=readback,
        candidate_manifest={"next_owner": "one-person-lab"},
        owner_decision_packet={"packet_id": "packet-1"},
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=handoff,
        paper_facing_candidate_delta={"status": "candidate_ready"},
        owner_blocker_packet=owner_blocker,
        candidate_refs={"package_manifest": "candidate_manifest.json"},
        forbidden_authority_writes=["owner_receipt"],
        forbidden_authority_claims=["publication_ready"],
    )

    assert owner_blocker["authority_materialized"] is False
    assert owner_blocker["typed_blocker_authority_materialized"] is False
    assert owner_blocker["human_gate_materialized"] is False
    assert {
        item["ref_kind"]
        for item in owner_blocker["required_authority_materialization_refs"]
    } == set(REQUIRED_AUTHORITY_MATERIALIZATION_REFS)
    assert {
        item["ref_kind"] for item in owner_blocker["required_quality_gate_refs"]
    } == set(REQUIRED_QUALITY_GATE_REFS)
    assert owner_request["consume_path"][
        "authority_materialized_by_this_request"
    ] is False
    assert set(
        owner_request["consume_path"]["required_authority_materialization_refs"]
    ) == set(REQUIRED_AUTHORITY_MATERIALIZATION_REFS)
    assert set(owner_request["consume_path"]["required_quality_gate_refs"]) == set(
        REQUIRED_QUALITY_GATE_REFS
    )
