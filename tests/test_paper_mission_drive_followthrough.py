from __future__ import annotations

import importlib
import json


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
    assert second_guard["required_next_executor_stage"] == (
        "paper_mission_semantic_progress_executor"
    )
    executor_stage = second_guard["mas_owned_executor_stage"]
    assert executor_stage["stage_type"] == "paper_mission_semantic_progress_executor"
    assert executor_stage["owner"] == "MedAutoScience"
    assert executor_stage["executor"] == "Codex CLI"
    assert executor_stage["required_outputs"] == list(
        commands.NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS
    )
    assert executor_stage["forbidden_next_action"] == "synonymous_route_back_redrive"
    assert executor_stage["authority_boundary"]["writes_authority"] is False
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


def test_semantic_progress_guard_ignores_followthrough_identity_wrappers() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    first = _route_back_consume_readback(
        mission_id="paper-mission::dm003",
        transaction_ref="paper-mission-transaction::dm003",
    )
    second = _route_back_consume_readback(
        mission_id="paper-mission::dm003::followthrough::followthrough",
        transaction_ref="paper-mission-transaction::dm003::followthrough::followthrough",
    )

    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first,
        handoff=_route_back_handoff(
            mission_id="paper-mission::dm003",
            transaction_ref="paper-mission-transaction::dm003",
        ),
    )
    second_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=second,
        handoff=_route_back_handoff(
            mission_id="paper-mission::dm003::followthrough::followthrough",
            transaction_ref="paper-mission-transaction::dm003::followthrough::followthrough",
        ),
        previous_guard=first_guard,
    )

    assert second_guard["status"] == "non_advancing_route_back"
    assert second_guard["semantic_progress_observed"] is False


def test_followthrough_transaction_uses_canonical_mission_identity() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    readback = _route_back_consume_readback(
        mission_id="paper-mission::dm003::followthrough::followthrough",
        transaction_ref="paper-mission-transaction::dm003::followthrough::followthrough",
    )
    readback["paper_mission_transaction"]["artifact_delta_refs"] = [
        {
            "ref_id": "existing-delta",
            "ref_kind": "submission_milestone_candidate_artifact",
            "uri": "artifact-delta::same",
        }
    ]
    readback["paper_mission_transaction"]["paper_audit_pack_refs"] = {
        family: [
            {
                "ref_id": f"{family}::same",
                "ref_kind": "submission_milestone_candidate_ref",
                "uri": f"audit-pack::{family}",
            }
        ]
        for family in commands.PAPER_AUDIT_PACK_FAMILIES
    }

    transaction = commands._followthrough_transaction_for_readback(readback)

    assert transaction["mission_id"] == "paper-mission::dm003"
    assert "::followthrough::followthrough" not in transaction["transaction_id"]
    route = transaction["opl_route_command"]
    assert "::followthrough::followthrough" not in route["source_terminal_decision_ref"]


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

    assert runtime_request["dedupe_key"] == (
        "paper-mission-route:"
        f"{commands.PAPER_MISSION_STAGE_ROUTE_RUNTIME_REQUEST_VERSION}:"
        "003-dpcc-primary-care-phenotype-treatment-gap:"
        "paper-mission-transaction::dm003:"
        "route_back"
    )
    payload = runtime_request["payload"]
    guard = payload["semantic_progress_guard"]
    assert guard["guard_kind"] == "non_advancing_route_back_detection"
    assert guard["can_claim_paper_progress"] is False
    assert payload["mas_owned_executor_stage"] == guard["mas_owned_executor_stage"]
    assert payload["mas_owned_executor_stage"]["stage_type"] == (
        "paper_mission_semantic_progress_executor"
    )
    assert guard["signature_payload"]["paper_mission_transaction_ref"] == (
        "paper-mission-transaction::dm003"
    )
    assert "typed_blocker_materialization" in guard["required_executor_outputs"]
    user_stage_log = payload["route_impact"]["user_stage_log"]
    assert payload["user_stage_log"] == user_stage_log
    assert user_stage_log["surface_kind"] == "opl_user_stage_log"
    assert user_stage_log["semantic_status"] == "provided_by_domain"
    assert user_stage_log["progress_delta_classification"] == "deliverable_progress"
    assert user_stage_log["deliverable_progress_delta"]["delta_count"] == 1
    assert user_stage_log["platform_repair_delta"]["delta_count"] == 0
    assert user_stage_log["next_forced_delta"] == (
        "domain_owner_answer_or_human_gate_or_non_synonymous_paper_delta"
    )
    assert user_stage_log["stage_work_done"]
    assert user_stage_log["changed_stage_surfaces"] == ["/tmp/package.json"]
    assert user_stage_log["outcome"] == "domain_gate_pending"
    assert user_stage_log["remaining_blockers"] == [
        "paper_mission_stage_route_domain_gate_pending"
    ]
    assert user_stage_log["evidence_refs"] == [
        "/tmp/package.json",
        "paper-mission-transaction::dm003",
        "/tmp/opl-route-command.json",
    ]
    assert user_stage_log["authority_boundary"]["can_claim_paper_progress"] is False
    assert user_stage_log["authority_boundary"]["can_claim_submission_ready"] is False
    assert payload["route_impact"]["domain_ready_verdict"] == "domain_gate_pending"
    assert payload["route_impact"]["progress_delta_classification"] == (
        "deliverable_progress"
    )


def test_drive_reports_mas_executor_delta_when_opl_readback_is_missing() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    consume_readback = _route_back_consume_readback()
    consume_readback["opl_runtime_readback_status"] = "waiting_for_opl_runtime_live_readback"
    handoff = _route_back_handoff()
    progress_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=consume_readback,
        handoff=handoff,
    )
    package_readback = {
        "output_manifest": {
            "package_manifest_ref": "/tmp/package/package_manifest.json",
            "owner_decision_packet_ref": "/tmp/package/owner_decision_packet.json",
            "paper_facing_candidate_delta_ref": (
                "/tmp/package/paper_facing_candidate_delta.json"
            ),
            "owner_consumption_request_ref": "/tmp/package/owner_consumption_request.json",
            "owner_blocker_packet_ref": "/tmp/package/owner_blocker_packet.json",
            "submission_milestone_checklist_ref": (
                "/tmp/package/submission_milestone_checklist.json"
            ),
        }
    }

    checkpoint = commands._paper_mission_mas_owned_executor_delta_checkpoint(
        package_readback=package_readback,
        consume_readback=consume_readback,
        handoff=handoff,
        progress_guard=progress_guard,
    )
    result = commands._paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=handoff,
        opl_runtime_submission={"status": "not_requested"},
        mas_owned_executor_delta=checkpoint,
    )

    assert checkpoint["status"] == "mas_owned_executor_delta_ready"
    assert checkpoint["owner"] == "MedAutoScience"
    assert checkpoint["executor"] == "Codex CLI"
    assert checkpoint["produced_outputs"] == {
        "owner_decision_packet_ref": "/tmp/package/owner_decision_packet.json",
        "paper_facing_delta_ref": "/tmp/package/paper_facing_candidate_delta.json",
        "owner_consumption_request_ref": "/tmp/package/owner_consumption_request.json",
        "owner_blocker_packet_ref": "/tmp/package/owner_blocker_packet.json",
        "submission_milestone_checklist_ref": (
            "/tmp/package/submission_milestone_checklist.json"
        ),
        "package_manifest_ref": "/tmp/package/package_manifest.json",
    }
    assert checkpoint["mas_owned_executor_stage"]["stage_type"] == (
        "paper_mission_semantic_progress_executor"
    )
    assert checkpoint["stop_same_semantic_redrive"] is True
    assert checkpoint["forbidden_next_action"] == "synonymous_route_back_redrive"
    assert checkpoint["authority_boundary"]["writes_authority"] is False
    assert checkpoint["authority_boundary"]["writes_runtime"] is False
    assert checkpoint["authority_boundary"]["can_claim_submission_ready"] is False
    assert result["status"] == "mas_owned_executor_delta_ready"
    assert result["can_claim_paper_progress"] is False
    assert result["can_claim_runtime_ready"] is False


def test_stage_closure_projection_missing_blocks_same_stage_followthrough() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    terminalizer = importlib.import_module(
        "med_autoscience.controllers.stage_closure_terminalizer"
    )
    readback = _route_back_consume_readback()
    readback["consume_candidate_status"] = "accepted_submission_milestone_candidate"
    readback["opl_runtime_readback_status"] = "opl_runtime_terminal_readback_observed"
    handoff = _route_back_handoff()

    decision = terminalizer.stage_closure_decision_projection(
        readback=readback,
        handoff=handoff,
        opl_runtime_submission={"status": "submitted"},
    )
    drive_result = commands._paper_mission_drive_result(
        consume_readback=readback,
        handoff=handoff,
        opl_runtime_submission={"status": "submitted"},
        stage_closure_decision=decision,
    )

    assert decision["projection_status"] == "stage_closure_decision_missing"
    assert decision["decision_ref"] == (
        "paper-mission-transaction::dm003#stage_closure_decision"
    )
    assert decision["outcome"]["kind"] == "stage_closure_decision_missing"
    assert decision.get("repair_budget") is None
    assert "accepted_submission_milestone_candidate" in decision["known_blockers"]
    assert decision["can_continue_same_stage"] is False
    assert drive_result["status"] == "stage_closure_decision_missing"
    assert drive_result["stage_closure_outcome"] == "stage_closure_decision_missing"


def test_stage_closure_projection_exposes_terminalizer_outcome() -> None:
    terminalizer = importlib.import_module(
        "med_autoscience.controllers.stage_closure_terminalizer"
    )
    readback = _route_back_consume_readback()
    readback["stage_closure_decision"] = {
        "decision_ref": "stage-closure::dm003",
        "outcome": {
            "kind": "typed_blocker",
            "next_owner": "MedAutoScience",
        },
        "repair_budget": {
            "repair_budget_max": 3,
            "repair_attempt_count": 3,
            "repair_budget_status": "exhausted",
        },
        "package_kind": "degraded_handoff_package",
        "known_blockers": ["claim_evidence_consistency_failed"],
    }

    decision = terminalizer.stage_closure_decision_projection(readback=readback)

    assert decision["projection_status"] == "terminalizer_outcome_observed"
    assert decision["decision_ref"] == "stage-closure::dm003"
    assert decision["outcome"]["kind"] == "typed_blocker"
    assert decision["package_kind"] == "degraded_handoff_package"
    assert decision["known_blockers"] == ["claim_evidence_consistency_failed"]


def test_route_back_budget_ledger_escalates_same_signature_across_runs(tmp_path) -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    ledger_ref = tmp_path / "ledger" / "study" / "route_back_budget_ledger.json"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    first_readback = _route_back_consume_readback(candidate_ref="/tmp/run-01/package.json")
    first_handoff = _route_back_handoff(candidate_ref="/tmp/run-01/package.json")
    ledger = commands._load_paper_mission_route_back_budget_ledger(
        ledger_ref=ledger_ref,
        study_id=study_id,
    )

    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first_readback,
        handoff=first_handoff,
        route_back_budget_ledger=ledger,
    )
    ledger = commands._record_paper_mission_route_back_budget_ledger(
        ledger=ledger,
        ledger_ref=ledger_ref,
        progress_guard=first_guard,
        consume_readback=first_readback,
        handoff=first_handoff,
        trigger="drive-initial",
        source="pytest",
    )
    second_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=_route_back_consume_readback(
            candidate_ref="/tmp/run-02/package.json"
        ),
        handoff=_route_back_handoff(candidate_ref="/tmp/run-02/package.json"),
        route_back_budget_ledger=ledger,
    )

    assert first_guard["status"] == "semantic_progress_observed"
    assert first_guard["route_back_budget"]["next_mode"] == (
        "opl_targeted_redrive_allowed"
    )
    assert first_guard["route_back_budget"]["opl_redrive_budget_remaining"] == 1
    assert second_guard["status"] == "non_advancing_route_back"
    assert second_guard["route_back_budget"]["budget_exhausted"] is True
    assert second_guard["route_back_budget"]["next_mode"] == (
        "mas_mission_executor_fallback"
    )
    assert second_guard["stop_same_semantic_redrive"] is True
    assert ledger_ref.exists()
    ledger_payload = json.loads(ledger_ref.read_text(encoding="utf-8"))
    assert ledger_payload["surface_kind"] == "paper_mission_route_back_budget_ledger"
    assert ledger_payload["latest_budget_status"]["next_mode"] == (
        "opl_targeted_redrive_allowed"
    )
    assert ledger_payload["authority_boundary"]["writes_authority"] is False
    assert ledger_payload["authority_boundary"]["writes_runtime"] is False
    assert ledger_payload["authority_boundary"]["can_claim_publication_ready"] is False


def _route_back_consume_readback(
    *,
    candidate_ref: str = "/tmp/package.json",
    mission_id: str = "paper-mission::dm003",
    transaction_ref: str = "paper-mission-transaction::dm003",
    consume_output_manifest: dict[str, object] | None = None,
    consume_result: dict[str, object] | None = None,
) -> dict[str, object]:
    transaction = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mission_id": mission_id,
        "transaction_id": transaction_ref,
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
        "mission_id": mission_id,
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
    *,
    candidate_ref: str = "/tmp/package.json",
    mission_id: str = "paper-mission::dm003",
    transaction_ref: str = "paper-mission-transaction::dm003",
) -> dict[str, object]:
    return {
        "handoff_status": "ready_for_opl_route_command",
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mission_id": mission_id,
        "candidate_ref": candidate_ref,
        "paper_mission_transaction_ref": transaction_ref,
        "opl_route_command_ref": "/tmp/opl-route-command.json",
        "route_command_kind": "route_back",
        "route_target": "submission_milestone_candidate",
        "next_owner": "mission_executor",
        "workspace_root": "/tmp/dm-cvd-workspace",
        "request_idempotency_key": transaction_ref,
        "transaction_materialized": True,
        "opl_route_command": {
            "command_kind": "route_back",
            "target": "submission_milestone_candidate",
        },
    }
