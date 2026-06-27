from __future__ import annotations

import importlib


def test_opl_tick_followthrough_timeout_is_bounded(monkeypatch) -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["timeout"] = kwargs["timeout"]
        raise commands.subprocess.TimeoutExpired(
            cmd=command,
            timeout=kwargs["timeout"],
        )

    monkeypatch.setattr(commands.subprocess, "run", fake_run)

    result = commands._opl_runtime_tick_readback(
        opl_bin="/tmp/opl",
        runtime_request={
            "payload": {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "paper_mission_transaction_ref": "paper-mission-transaction::dm003",
            }
        },
    )

    assert observed["timeout"] == commands.OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS
    assert observed["timeout"] <= 15
    assert "--hydrate" in observed["command"]
    assert result["status"] == "timeout"
    assert result["reason"] == "opl_tick_followthrough_timeout"
    assert result["followthrough_observation_window_seconds"] == observed["timeout"]
    assert result["can_claim_stage_run_created"] is False
    assert result["can_claim_provider_running"] is False
    assert result["can_claim_paper_progress"] is False


def test_semantic_progress_guard_stops_same_route_back_without_paper_delta() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    first = _route_back_consume_readback(candidate_ref="/tmp/round-00/package.json")
    second = _route_back_consume_readback(candidate_ref="/tmp/round-01/package.json")

    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first,
        handoff=_route_back_handoff(candidate_ref="/tmp/round-00/package.json"),
    )
    second_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=second,
        handoff=_route_back_handoff(candidate_ref="/tmp/round-01/package.json"),
        previous_guard=first_guard,
    )

    assert first_guard["status"] == "semantic_progress_observed"
    assert second_guard["status"] == "non_advancing_route_back"
    assert second_guard["requires_mas_owned_executor_delta"] is True
    assert second_guard["stop_same_semantic_redrive"] is True
    assert second_guard["can_claim_paper_progress"] is False
    assert "paper_facing_delta" in second_guard["next_legal_actions"]


def test_semantic_progress_guard_ignores_candidate_packet_refs_without_owner_delta() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    first = _route_back_consume_readback()
    second = _route_back_consume_readback(
        consume_result={"paper_facing_delta_ref": "/tmp/paper-facing-delta.json"}
    )

    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first,
        handoff=_route_back_handoff(),
    )
    second_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=second,
        handoff=_route_back_handoff(),
        previous_guard=first_guard,
    )

    assert second_guard["status"] == "non_advancing_route_back"
    assert second_guard["required_executor_delta_present"] is False
    assert second_guard["progress_refs"]["paper_facing_delta_ref"] == (
        "/tmp/paper-facing-delta.json"
    )


def test_semantic_progress_guard_allows_new_owner_receipt_delta() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    first = _route_back_consume_readback()
    second = _route_back_consume_readback(
        consume_result={"domain_owner_receipt_ref": "owner-receipt::dm003"}
    )

    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first,
        handoff=_route_back_handoff(),
    )
    second_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=second,
        handoff=_route_back_handoff(),
        previous_guard=first_guard,
    )

    assert second_guard["status"] == "semantic_progress_observed"
    assert second_guard["required_executor_delta_present"] is True
    assert second_guard["signature_payload"]["semantic_delta_refs"] == {
        "accepted_owner_receipt_ref": "owner-receipt::dm003"
    }


def test_opl_stage_route_request_carries_non_advancing_guard() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    runtime_request = commands._opl_stage_route_runtime_request_from_handoff(
        _route_back_handoff()
    )

    payload = runtime_request["payload"]
    guard = payload["semantic_progress_guard"]
    assert guard["guard_kind"] == "non_advancing_route_back_detection"
    assert guard["can_claim_paper_progress"] is False
    assert guard["signature_payload"]["paper_mission_transaction_ref"] == (
        "paper-mission-transaction::dm003"
    )
    assert "typed_blocker_materialization" in guard["required_executor_outputs"]


def _route_back_consume_readback(
    *,
    candidate_ref: str = "/tmp/package.json",
    consume_output_manifest: dict[str, object] | None = None,
    consume_result: dict[str, object] | None = None,
) -> dict[str, object]:
    transaction = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mission_id": "paper-mission::dm003",
        "stage_id": "submission_milestone_candidate",
        "stage_run_ref": "stage-run::same",
        "stage_terminal_decision": {
            "decision_kind": "route_back",
            "status": "route_back",
            "next_owner": "mission_executor",
            "target_stage_id": "submission_milestone_candidate",
            "repair_scope": "continue paper-facing submission milestone work",
            "route_back_evidence_ref": "route-back-evidence::same",
        },
        "opl_route_command": {
            "command_kind": "route_back",
            "target": "submission_milestone_candidate",
        },
        "artifact_delta_refs": [
            {"ref_id": "existing-delta", "uri": "artifact-delta::same"}
        ],
        "paper_audit_pack_refs": {"decision_trace": "decision-trace::same"},
    }
    owner_answer = {
        "status": "route_back",
        "owner_answer_shape": "route_back_evidence_ref",
        "stage_terminal_decision": transaction["stage_terminal_decision"],
    }
    return {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mission_id": "paper-mission::dm003",
        "candidate_ref": candidate_ref,
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": transaction["stage_terminal_decision"],
        "opl_route_command": transaction["opl_route_command"],
        "next_owner_or_human_decision": {
            "next_owner": "mission_executor",
            "human_decision_required": False,
        },
        "terminal_owner_gate": {
            "owner": "mas_authority_kernel",
            "gate_kind": "domain_gate",
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        },
        "terminal_owner_gate_owner_answer_readback": owner_answer,
        "authority_consume_readback": {
            "consume_result": consume_result or {},
        },
        "consume_output_manifest": consume_output_manifest or {},
    }


def _route_back_handoff(
    *, candidate_ref: str = "/tmp/package.json"
) -> dict[str, object]:
    return {
        "handoff_status": "ready_for_opl_route_command",
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mission_id": "paper-mission::dm003",
        "candidate_ref": candidate_ref,
        "paper_mission_transaction_ref": "paper-mission-transaction::dm003",
        "opl_route_command_ref": "/tmp/opl-route-command.json",
        "route_command_kind": "route_back",
        "route_target": "submission_milestone_candidate",
        "next_owner": "mission_executor",
        "workspace_root": "/tmp/dm-cvd-workspace",
        "transaction_materialized": True,
        "opl_route_command": {
            "command_kind": "route_back",
            "target": "submission_milestone_candidate",
        },
    }
