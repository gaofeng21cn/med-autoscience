from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from med_autoscience.domain_route_profile import build_domain_route_runtime_request
from med_autoscience.paper_mission_domain.transaction_readback import (
    PAPER_AUDIT_PACK_FAMILIES,
)
from med_autoscience.paper_mission_domain.drive_helpers import paper_mission_drive_result


def test_drive_initial_source_prefers_canonical_next_action_inspect() -> None:
    drive = importlib.import_module(
        "med_autoscience.paper_mission_domain.drive_readback"
    )
    calls: list[dict[str, object]] = []

    def fake_readback_builder(**kwargs):
        calls.append(kwargs)
        return {
            "surface_kind": "paper_mission_materialized_readback",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_type": "request_opl_stage_attempt",
                "owner": "write",
                "stage_id": "write",
                "work_unit_id": "medical_methods_and_registry_reporting_repair",
            },
        }

    source = drive._drive_canonical_next_action_source_readback(
        profile=SimpleNamespace(),
        profile_ref="/tmp/profile.toml",
        study_id="obesity_multicenter_phenotype_atlas",
        source="pytest",
        consume_candidate_readback_builder=fake_readback_builder,
    )

    assert source is not None
    assert source["next_action"]["work_unit_id"] == (
        "medical_methods_and_registry_reporting_repair"
    )
    assert calls[0]["paper_mission_command"] == "inspect"
    assert "opl_runtime_payload" not in calls[0]



def test_opl_stage_route_request_excludes_mas_runtime_policy() -> None:
    runtime_request = build_domain_route_runtime_request(_route_back_handoff())

    assert runtime_request["task_kind"] == "domain_route/stage-route"
    assert runtime_request["route_identity"]["dedupe_key"].startswith(
        "domain-route:v1:mas:"
    )
    assert runtime_request["surface_kind"] == "opl_domain_route_runtime_request"
    assert runtime_request["domain_route_transaction_ref"] == (
        "paper-mission-transaction::dm003"
    )
    assert "/tmp/package.json" in runtime_request["source_refs"]
    assert runtime_request["authority_boundary"]["can_claim_domain_progress"] is False
    assert "user_stage_log" not in runtime_request


def test_opl_runtime_handoff_exposes_typed_request_without_local_write() -> None:
    drive = importlib.import_module(
        "med_autoscience.paper_mission_domain.drive_readback"
    )

    handoff = drive._opl_runtime_handoff_readback(
        handoff=_route_back_handoff(),
        stage_closure_decision={
            "projection_status": "terminalizer_outcome_observed",
            "outcome": {"kind": "next_stage_transition"},
        },
    )

    assert handoff["status"] == "handoff_required"
    assert handoff["next_owner"] == "one-person-lab"
    assert handoff["required_next_action"] == "submit_typed_domain_route_request"
    assert handoff["writes_runtime"] is False
    assert handoff["runtime_request"]["surface_kind"] == (
        "opl_domain_route_runtime_request"
    )
    assert handoff["blockers"] == []


def test_opl_stage_route_request_dedupe_changes_with_candidate_content(
    tmp_path: Path,
) -> None:
    candidate_ref = tmp_path / "package_manifest.json"
    candidate_ref.write_text(
        json.dumps({"package": "submission", "version": 1}),
        encoding="utf-8",
    )
    first = build_domain_route_runtime_request(
        _route_back_handoff(candidate_ref=str(candidate_ref))
    )
    same = build_domain_route_runtime_request(
        _route_back_handoff(candidate_ref=str(candidate_ref))
    )

    candidate_ref.write_text(
        json.dumps({"package": "submission", "version": 2}),
        encoding="utf-8",
    )
    second = build_domain_route_runtime_request(
        _route_back_handoff(candidate_ref=str(candidate_ref))
    )

    assert first["route_identity"]["dedupe_key"] == same["route_identity"][
        "dedupe_key"
    ]
    assert first["route_identity"]["source_fingerprint"] == same["route_identity"][
        "source_fingerprint"
    ]
    assert first["route_identity"]["dedupe_key"] != second["route_identity"][
        "dedupe_key"
    ]
    assert first["route_identity"]["source_fingerprint"] != second[
        "route_identity"
    ]["source_fingerprint"]
    assert first["route_identity"]["request_idempotency_key"] == (
        second["route_identity"]["request_idempotency_key"]
    )


def test_opl_stage_route_request_requires_request_idempotency_key() -> None:
    handoff = _route_back_handoff()
    handoff["attempt_idempotency_key"] = "attempt::legacy"
    handoff["route_identity_key"] = "route::legacy"
    handoff["candidate_ref"] = "/tmp/legacy-candidate.json"
    handoff.pop("request_idempotency_key")

    assert (
        build_domain_route_runtime_request(handoff) is None
    )



def test_missing_stage_closure_projection_does_not_block_single_pass_drive() -> None:
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
    terminalizer = importlib.import_module(
        "med_autoscience.controllers.stage_closure_terminalizer"
    )
    readback = _route_back_consume_readback()
    readback["consume_candidate_status"] = "accepted_submission_milestone_candidate"
    readback["opl_stage_attempt_readback_status"] = "opl_runtime_terminal_readback_observed"
    handoff = _route_back_handoff()

    decision = terminalizer.stage_closure_decision_projection(
        readback=readback,
        handoff=handoff,
    )
    drive_result = paper_mission_drive_result(
        consume_readback=readback,
        handoff=handoff,
        stage_closure_decision=decision,
    )

    assert decision["projection_status"] == (
        "quality_debt_stage_closure_context_missing"
    )
    assert decision["decision_ref"] == (
        "paper-mission-transaction::dm003#stage_closure_decision"
    )
    assert decision["outcome"]["kind"] == "next_stage_transition"
    assert decision.get("repair_budget") is None
    assert "accepted_submission_milestone_candidate" in decision["known_blockers"]
    assert decision["can_continue_same_stage"] is True
    assert decision["next_stage_may_start"] is True
    assert drive_result["status"] == "opl_terminal_closeout_observed"
    assert drive_result["stage_closure_outcome"] == "next_stage_transition"


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


def test_drive_stage_closure_terminalizer_attaches_current_decision() -> None:
    commands = importlib.import_module(
        "med_autoscience.paper_mission_domain.stage_closure_terminalizer"
    )
    result = commands.materialize_stage_closure_for_drive_readback(
        consume_readback=_route_back_consume_readback(),
    )

    assert result["stage_closure_decision"]["outcome"]["kind"] in {
        "next_stage_transition",
        "typed_blocker",
    }
    assert result["stage_closure_outcome"] == result["stage_closure_decision"][
        "outcome"
    ]["kind"]


def _route_back_consume_readback() -> dict[str, object]:
    transaction = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mission_id": "paper-mission::dm003",
        "transaction_id": "paper-mission-transaction::dm003",
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
        "ai_route_context": {
            "command_kind": "route_back",
            "target": "submission_milestone_candidate",
        },
        "artifact_delta_refs": [],
        "paper_audit_pack_refs": {},
    }
    return {
        "study_id": transaction["study_id"],
        "mission_id": transaction["mission_id"],
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": transaction["stage_terminal_decision"],
        "ai_route_context": transaction["ai_route_context"],
        "next_owner_or_human_decision": {
            "next_owner": "mission_executor",
            "human_decision_required": False,
        },
        "terminal_owner_gate": {
            "owner": "mas_authority_kernel",
            "gate_kind": "domain_gate",
            "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        },
        "terminal_owner_gate_owner_answer_readback": {
            "status": "route_back",
            "owner_answer_shape": "route_back_evidence_ref",
            "route_back_evidence_ref": "route-back-evidence::same",
            "stage_terminal_decision": transaction["stage_terminal_decision"],
        },
        "authority_consume_readback": {"consume_result": {}},
    }


def _route_back_handoff(
    *, candidate_ref: str = "/tmp/package.json"
) -> dict[str, object]:
    transaction_ref = "paper-mission-transaction::dm003"
    return {
        "handoff_status": "ready_for_ai_route_context",
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "mission_id": "paper-mission::dm003",
        "candidate_ref": candidate_ref,
        "paper_mission_transaction_ref": transaction_ref,
        "ai_route_context_ref": "/tmp/opl-route-command.json",
        "route_command_kind": "route_back",
        "route_target": "submission_milestone_candidate",
        "declarative_target_stage_id": "review_and_quality_gate",
        "next_owner": "mission_executor",
        "workspace_root": "/tmp/dm-cvd-workspace",
        "request_idempotency_key": transaction_ref,
        "transaction_materialized": True,
        "ai_route_context": {
            "command_kind": "route_back",
            "target": "submission_milestone_candidate",
            "declarative_target_stage_id": "review_and_quality_gate",
        },
    }
