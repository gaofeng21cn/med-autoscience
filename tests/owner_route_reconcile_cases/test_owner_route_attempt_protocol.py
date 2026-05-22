from __future__ import annotations

import importlib


def test_owner_route_protocol_attaches_registered_reason_and_priority_lattice() -> None:
    owner_route_module = importlib.import_module("med_autoscience.runtime_control.owner_route")

    status = {
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002",
            "source_signature": "truth-source-dm002",
        },
        "runtime_health_snapshot": {"runtime_health_epoch": "runtime-health-dm002"},
        "quest_status": "running",
    }
    actions = [
        {
            "action_type": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "reason": "ai_reviewer_request_pending",
            "work_unit_fingerprint": "ai-reviewer-request::dm002::current",
        }
    ]

    route = owner_route_module.build_owner_route(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        status=status,
        progress={},
        actions=actions,
        blocked_reason="ai_reviewer_request_pending",
        next_owner="ai_reviewer",
        active_run_id=None,
    )

    assert route["owner_route_attempt_protocol"]["version"] == "mas-owner-route-attempt-protocol.v1"
    assert route["owner_reason_contract"]["reason"] == "ai_reviewer_request_pending"
    assert route["owner_reason_contract"]["owner"] == "ai_reviewer"
    assert route["owner_reason_contract"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert route["owner_reason_contract"]["required_output"] == "artifacts/publication_eval/latest.json"
    assert route["owner_reason_contract"]["priority_class"] == "ai_reviewer_currentness"
    assert route["priority_lattice"] == [
        "hard_methodology_or_source_blocker",
        "pending_ai_reviewer_request",
        "ai_reviewer_currentness",
        "write_route_back",
        "package_freshness",
        "delivery_or_human_handoff",
    ]
    assert route["currentness_contract"]["status"] == "currentness_basis_required"
    assert "owner_route_currentness_basis" in route["source_refs"]


def test_owner_route_protocol_marks_unregistered_reason_non_dispatchable() -> None:
    owner_route_module = importlib.import_module("med_autoscience.runtime_control.owner_route")

    route = owner_route_module.build_owner_route(
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        status={"study_truth_snapshot": {"truth_epoch": "truth-epoch", "source_signature": "truth-source"}},
        progress={},
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "reason": "unregistered_local_reason",
            }
        ],
        blocked_reason="unregistered_local_reason",
        next_owner="write",
        active_run_id=None,
    )

    assert route["owner_reason_contract"]["registered"] is False
    assert route["owner_route_attempt_protocol"]["dispatchable"] is False
    assert route["allowed_actions"] == []
