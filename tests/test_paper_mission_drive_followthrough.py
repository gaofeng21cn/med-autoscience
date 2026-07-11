from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from med_autoscience.paper_mission_domain import opl_runtime_submission
from med_autoscience.domain_route_profile import build_domain_route_runtime_request
from med_autoscience.paper_mission_domain.followthrough_materialized_readback import (
    followthrough_transaction_for_readback,
)
from med_autoscience.paper_mission_domain.route_back_budget import (
    NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS,
    _load_paper_mission_route_back_budget_ledger,
    _record_paper_mission_route_back_budget_ledger,
)
from med_autoscience.paper_mission_domain.transaction_readback import (
    PAPER_AUDIT_PACK_FAMILIES,
)
from med_autoscience.paper_mission_domain.drive_helpers import (
    paper_mission_drive_result,
    paper_mission_mas_owned_executor_delta_checkpoint,
)


def test_opl_runtime_submission_creates_and_starts_explicit_stage_attempt(
    monkeypatch, tmp_path
) -> None:
    observed: dict[str, object] = {}
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("", encoding="utf-8")

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["timeout"] = kwargs["timeout"]
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "family_runtime_stage_attempt": {
                        "created": True,
                        "idempotent_noop": False,
                        "attempt": {
                            "stage_attempt_id": "attempt::review::1",
                            "stage_id": "review_and_quality_gate",
                            "status": "running",
                        },
                        "stage_launch_admission_gate": {"status": "admitted"},
                        "temporal_start": {"started": True},
                    }
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(opl_runtime_submission.subprocess, "run", fake_run)
    handoff = _route_back_handoff()
    handoff["domain_action_id"] = (
        "research_integrity_review_publication_gate_stage_hook"
    )

    result = opl_runtime_submission.opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=True,
        opl_bin=opl_bin,
    )

    command = observed["command"]
    assert command[:4] == [str(opl_bin), "family-runtime", "attempt", "create"]
    assert command[command.index("--domain") + 1] == "medautoscience"
    assert command[command.index("--stage") + 1] == "review_and_quality_gate"
    assert json.loads(command[command.index("--workspace-locator") + 1]) == {
        "workspace_root": str(Path("/tmp/dm-cvd-workspace").resolve())
    }
    assert command[command.index("--action") + 1] == (
        "research_integrity_review_publication_gate_stage_hook"
    )
    assert "--start" in command
    assert "--json" in command
    assert "enqueue" not in command
    assert "tick" not in command
    assert "submission_milestone_candidate" not in command
    assert result["status"] == "submitted"
    assert result["attempt_readback"]["stage_attempt_id"] == "attempt::review::1"
    assert result["can_claim_opl_stage_run_created"] is False
    assert result["can_claim_provider_running"] is False
    assert result["can_claim_paper_progress"] is False


def test_opl_runtime_submission_rejects_missing_workspace_locator(monkeypatch) -> None:
    handoff = _route_back_handoff()
    handoff.pop("workspace_root")
    monkeypatch.setattr(
        opl_runtime_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    result = opl_runtime_submission.opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=True,
        opl_bin="opl",
    )

    assert result["status"] == "not_actionable"
    assert result["reason"] == "opl_stage_attempt_workspace_locator_missing"


def test_opl_runtime_submission_rejects_stage_identity_mismatch(monkeypatch) -> None:
    handoff = _route_back_handoff()
    handoff["opl_route_command"]["declarative_target_stage_id"] = (
        "manuscript_authoring"
    )
    monkeypatch.setattr(
        opl_runtime_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    result = opl_runtime_submission.opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=True,
        opl_bin="opl",
    )

    assert result["status"] == "not_actionable"
    assert result["reason"] == "opl_stage_attempt_target_stage_mismatch"


def test_opl_runtime_submission_rejects_missing_explicit_stage(monkeypatch) -> None:
    handoff = _route_back_handoff()
    handoff.pop("declarative_target_stage_id")
    handoff["opl_route_command"].pop("declarative_target_stage_id")
    monkeypatch.setattr(
        opl_runtime_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    result = opl_runtime_submission.opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=True,
        opl_bin="opl",
    )

    assert result["status"] == "not_actionable"
    assert result["reason"] == "opl_stage_attempt_target_stage_missing"


def test_opl_runtime_submission_reports_stage_admission_failure(monkeypatch, tmp_path) -> None:
    opl_bin = tmp_path / "opl"
    opl_bin.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        opl_runtime_submission.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "family_runtime_stage_attempt": {
                        "created": True,
                        "idempotent_noop": False,
                        "attempt": {
                            "stage_attempt_id": "attempt::blocked::1",
                            "stage_id": "review_and_quality_gate",
                            "status": "blocked",
                            "blocked_reason": "stage_not_admitted",
                        },
                        "stage_launch_admission_gate": {
                            "status": "blocked",
                            "blocked_reason": "stage_not_admitted",
                        },
                        "temporal_start": None,
                    }
                }
            ),
            stderr="",
        ),
    )

    result = opl_runtime_submission.opl_runtime_submission_readback(
        handoff=_route_back_handoff(),
        submit_opl_runtime=True,
        opl_bin=opl_bin,
    )

    assert result["status"] == "failed"
    assert result["reason"] == "opl_stage_attempt_admission_blocked"
    assert result["attempt_readback"]["status"] == "blocked"


def test_semantic_progress_guard_stops_same_route_back_without_paper_delta() -> None:
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
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
        NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS
    )
    assert executor_stage["forbidden_next_action"] == "synonymous_route_back_redrive"
    assert executor_stage["authority_boundary"]["writes_authority"] is False
    assert second_guard["can_claim_paper_progress"] is False
    assert "paper_facing_delta" in second_guard["next_legal_actions"]


def test_semantic_progress_guard_ignores_candidate_packet_refs_without_owner_delta() -> None:
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
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
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
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
        for family in PAPER_AUDIT_PACK_FAMILIES
    }

    transaction = followthrough_transaction_for_readback(readback)

    assert transaction["mission_id"] == "paper-mission::dm003"
    assert "::followthrough::followthrough" not in transaction["transaction_id"]
    route = transaction["opl_route_command"]
    assert "::followthrough::followthrough" not in route["source_terminal_decision_ref"]


def test_followthrough_transaction_prefers_canonical_next_action_route() -> None:
    readback = _route_back_consume_readback(
        mission_id="paper-mission::obesity",
        transaction_ref="paper-mission-transaction::obesity::old-submission-route",
    )
    readback["consume_candidate_status"] = "accepted_submission_milestone_candidate"
    readback["paper_mission_transaction"]["stage_id"] = (
        "submission_milestone_candidate::followthrough::followthrough-02"
    )
    readback["paper_mission_transaction"]["stage_terminal_decision"] = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": "Old submission milestone followthrough.",
        "next_owner": "mission_executor",
        "next_work_unit": "submission_milestone_candidate::followthrough::followthrough-01",
    }
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
        for family in PAPER_AUDIT_PACK_FAMILIES
    }
    readback["next_action"] = {
        "surface_kind": "mas_next_action_envelope",
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "stage_id": "write",
        "work_unit_id": "medical_methods_and_registry_reporting_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
        "outcome_ref": (
            "domain-transition::route_back_same_line::"
            "medical_methods_and_registry_reporting_repair"
        ),
    }

    transaction = followthrough_transaction_for_readback(readback)

    assert transaction["stage_id"] == "write"
    decision = transaction["stage_terminal_decision"]
    assert decision["next_owner"] == "write"
    assert decision["next_work_unit"] == "medical_methods_and_registry_reporting_repair"
    assert decision["recommended_next_action"] == "request_opl_stage_attempt"
    assert decision["work_unit_fingerprint"] == (
        "domain-transition::route_back_same_line::"
        "medical_methods_and_registry_reporting_repair"
    )
    route = transaction["opl_route_command"]
    assert route["command_kind"] == "resume_stage"
    assert route["target"] == "medical_methods_and_registry_reporting_repair"


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
    assert calls[0]["enable_opl_live_probe"] is False


def test_semantic_progress_guard_allows_new_owner_receipt_delta() -> None:
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
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
    assert "semantic_progress_guard" not in runtime_request
    assert "user_stage_log" not in runtime_request


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


def test_drive_reports_mas_executor_delta_when_opl_readback_is_missing() -> None:
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
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

    checkpoint = paper_mission_mas_owned_executor_delta_checkpoint(
        package_readback=package_readback,
        consume_readback=consume_readback,
        handoff=handoff,
        progress_guard=progress_guard,
    )
    result = paper_mission_drive_result(
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
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
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
    drive_result = paper_mission_drive_result(
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


def test_route_back_budget_ledger_escalates_same_signature_across_runs(tmp_path) -> None:
    commands = importlib.import_module("med_autoscience.paper_mission_domain")
    ledger_ref = tmp_path / "ledger" / "study" / "route_back_budget_ledger.json"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    first_readback = _route_back_consume_readback(candidate_ref="/tmp/run-01/package.json")
    first_handoff = _route_back_handoff(candidate_ref="/tmp/run-01/package.json")
    ledger = _load_paper_mission_route_back_budget_ledger(
        ledger_ref=ledger_ref,
        study_id=study_id,
    )

    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first_readback,
        handoff=first_handoff,
        route_back_budget_ledger=ledger,
    )
    ledger = _record_paper_mission_route_back_budget_ledger(
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
        "declarative_target_stage_id": "review_and_quality_gate",
        "next_owner": "mission_executor",
        "workspace_root": "/tmp/dm-cvd-workspace",
        "request_idempotency_key": transaction_ref,
        "transaction_materialized": True,
        "opl_route_command": {
            "command_kind": "route_back",
            "target": "submission_milestone_candidate",
            "declarative_target_stage_id": "review_and_quality_gate",
        },
    }
