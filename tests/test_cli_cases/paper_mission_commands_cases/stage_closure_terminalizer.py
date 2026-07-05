from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_paper_mission_terminalize_stage_materializes_non_authority_decision(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260628Tterminalize"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone::terminalize"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Terminalize a consumed submission milestone candidate.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [
                    {
                        "delta_id": "delta::dm003::submission-candidate",
                        "artifact_ref": "mission://dm003/submission-candidate",
                        "delta_kind": "formal_paper_mission_owner_decision_packet",
                        "status": "candidate",
                    }
                ],
                "source_refs": [],
                "consume_result": {"status": "accepted"},
                "one_shot_migration_readback": {
                    "current_mission": {
                        "objective_kind": "submission_milestone_candidate",
                        "legacy_blocker_is_default_execution_state": False,
                    },
                    "required_output": {
                        "next_owner": "mission_executor",
                        "kind": "submission_milestone_candidate",
                    },
                    "stage_terminal_decision": transaction["stage_terminal_decision"],
                    "opl_route_command": transaction["opl_route_command"],
                    "consume_candidate_status": "accepted_submission_milestone_candidate",
                },
                "paper_mission_transaction": transaction,
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    initial = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert initial["stage_closure_outcome"] == "next_stage_transition"
    assert initial["stage_closure_decision_ref"] is None
    assert initial["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )
    assert initial["durable_mission_stop_guard"][
        "accepted_submission_milestone_candidate_is_durable_stop"
    ] is False
    assert initial["durable_mission_stop_guard"]["durable_stop_allowed"] is False
    assert initial["durable_mission_stop_guard"][
        "requires_terminalizer_outcome"
    ] is True

    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "20260628Tterminalize"
    )
    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--output-root",
            str(output_root),
            "--format",
            "json",
        ]
    )
    terminalized = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert terminalized["surface_kind"] == (
        "paper_mission_stage_closure_terminalizer_readback"
    )
    assert terminalized["status"] in {
        "terminalizer_outcome_materialized",
        "legacy_terminalizer_outcome_superseded",
    }
    assert terminalized["stage_closure_outcome"] in {
        "next_stage_transition",
        "typed_blocker",
        "human_gate",
        "owner_receipt",
    }
    output_manifest = terminalized["output_manifest"]
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False
    decision_ref = Path(output_manifest["stage_closure_decision_ref"])
    assert decision_ref.exists()

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    observed = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert observed["stage_closure_decision"]["projection_status"] == (
        "terminalizer_outcome_observed"
    )
    assert observed["stage_closure_decision_ref"] == str(decision_ref)
    assert observed["stage_closure_outcome"] == terminalized["stage_closure_outcome"]
    assert observed["mutation_policy"]["writes_authority"] is False
    assert observed["mutation_policy"]["writes_runtime"] is False
    assert observed["mutation_policy"]["writes_yang_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_terminalize_stage_defaults_to_workspace_ops_ledger(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260628Tterminalize"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::submission-milestone::terminalize"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": mission_id,
                "study_id": study_id,
                "objective": "Terminalize a consumed submission milestone candidate.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "consume_result": {"status": "accepted"},
                "one_shot_migration_readback": {
                    "current_mission": {
                        "objective_kind": "submission_milestone_candidate",
                        "legacy_blocker_is_default_execution_state": False,
                    },
                    "required_output": {
                        "next_owner": "mission_executor",
                        "kind": "submission_milestone_candidate",
                    },
                    "stage_terminal_decision": transaction["stage_terminal_decision"],
                    "opl_route_command": transaction["opl_route_command"],
                    "consume_candidate_status": "accepted_submission_milestone_candidate",
                },
                "paper_mission_transaction": transaction,
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    terminalized = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert terminalized["dry_run"] is False
    output_manifest = terminalized["output_manifest"]
    decision_ref = Path(output_manifest["stage_closure_decision_ref"])
    assert decision_ref == (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    assert decision_ref.exists()
    assert output_manifest["writes_authority"] is False
    assert output_manifest["writes_runtime"] is False
    assert output_manifest["writes_yang_authority"] is False

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    observed = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert observed["stage_closure_decision_ref"] == str(decision_ref)
    assert observed["stage_closure_decision"]["projection_status"] == (
        "terminalizer_outcome_observed"
    )
    assert observed["stage_closure_outcome"] == terminalized["stage_closure_outcome"]

    exit_code = cli.main(
        [
            "paper-mission",
            "drive",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--no-submit-opl-runtime",
            "--format",
            "json",
        ]
    )
    drive = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert drive["drive_result"]["status"] != "stage_closure_decision_missing"
    assert drive["stage_closure_decision_ref"] == str(decision_ref)
    assert drive["mutation_policy"]["writes_authority"] is False
    assert drive["mutation_policy"]["writes_yang_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_stage_closure_terminalizer_reads_nested_closeout_telemetry() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    decision = commands._terminalize_stage_closure_from_readback(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "mission_id": "mission-003",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": {
                "transaction_id": "txn-003",
                "stage_id": "submission_milestone_candidate",
            },
            "stage_terminal_decision": {
                "status": "accepted_submission_milestone_candidate",
                "reason": "paper_mission_stage_route_domain_gate_pending",
            },
            "opl_runtime_carrier_readback": {
                "carrier_status": "opl_runtime_terminal_readback_observed",
                "terminal_closeout": {
                    "status": "completed",
                    "stage_attempt_id": "sat-003",
                    "duration": {
                        "started_at": "2026-06-28T23:30:00Z",
                        "completed_at": "2026-06-28T23:40:00Z",
                    },
                    "token_usage": {"total_tokens": 1200},
                    "cost": {
                        "status": "missing",
                        "reason": "provider attempt cost telemetry is not exposed",
                    },
                },
            },
        }
    )

    assert "observability_gaps" not in decision
    assert decision["opl_closeout"]["stage_attempt_id"] == "sat-003"
    assert decision["opl_closeout"]["token_usage"]["total_tokens"] == 1200


def test_stage_closure_terminalizer_does_not_treat_accepted_status_as_blocker() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    decision = commands._terminalize_stage_closure_from_readback(
        {
            "study_id": "obesity_multicenter_phenotype_atlas",
            "mission_id": "mission-obesity",
            "consume_candidate_status": "accepted",
            "transaction_state": "accepted",
            "stage_closure_decision": {"known_blockers": ["accepted"]},
            "stage_terminal_decision": {"reason": "accepted"},
            "paper_mission_transaction": {
                "transaction_id": "txn-obesity",
                "stage_id": "paper_mission_import",
            },
        }
    )

    assert decision.get("known_blockers", []) == []
    assert decision.get("blocker_taxonomy", {}).get("unknown", []) == []
    assert decision["outcome"]["kind"] == "owner_receipt"


def test_stage_closure_terminalizer_does_not_treat_paper_facing_delta_acceptance_as_blocker() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    decision = commands._terminalize_stage_closure_from_readback(
        {
            "study_id": "obesity_multicenter_phenotype_atlas",
            "mission_id": "mission-obesity",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "transaction_state": "accepted_submission_milestone_candidate",
            "authority_consume_readback": {
                "consume_result": {
                    "paper_facing_delta_ref": "/tmp/paper-facing-delta.json",
                },
            },
            "paper_mission_transaction": {
                "transaction_id": "txn-obesity",
                "stage_id": "ai_reviewer_medical_prose_quality_review",
            },
            "stage_terminal_decision": {
                "status": "accepted_submission_milestone_candidate",
                "reason": "accepted_submission_milestone_candidate",
            },
            "current_package": {
                "status": "layout_migration_pending_sync",
                "freshness_status": "legacy",
                "delivery_status": "current",
                "package_kind": "submission_ready_package",
                "can_submit": True,
                "quality_gate_status": "clear",
                "generated_from_current_source": True,
                "root": "/tmp/current-package",
                "zip_exists": True,
                "known_blockers": [],
            },
        }
    )

    assert decision.get("known_blockers", []) == []
    assert decision.get("blocker_taxonomy", {}).get("route_back_checkpoint", []) == []
    assert decision["outcome"]["kind"] == "owner_receipt"


def test_stage_closure_terminalizer_reterminalizes_legacy_accepted_unknown_blocker() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    legacy_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "source_surface_kind": "paper_mission_stage_closure_ledger",
        "known_blockers": ["accepted"],
        "blocker_taxonomy": {"unknown": ["accepted"]},
        "identity": {
            "consume_candidate_status": "accepted",
            "transaction_state": "accepted",
        },
        "outcome": {
            "kind": "typed_blocker",
            "blocker_type": "unclassified_stage_closure_blocker",
        },
    }

    assert commands._stage_closure_decision_requires_reterminalize(legacy_decision)


def test_stage_closure_terminalizer_reads_workspace_consumption_closeout_accounting(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "full_cutover_20260623"
        / study_id
    )
    mission_root.mkdir(parents=True)
    transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::medical-prose::one-shot-migration",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "sat-dm003"
        / study_id
    )
    closeout_root.mkdir(parents=True)
    closeout_ref = closeout_root / "stage_attempt_closeout_packet.json"
    closeout_ref.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "blocked",
                "study_id": study_id,
                "stage_id": transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-dm003",
                "stage_packet_ref": transaction["transaction_id"]
                + "#stage_terminal_decision",
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "closeout_refs": [
                    transaction["transaction_id"] + "#opl_route_command",
                ],
                "paper_stage_log": {
                    "duration": {
                        "status": "missing",
                        "seconds": None,
                        "missing_duration_reason": "not_measured_for_full_stage",
                    },
                    "token_usage": {
                        "status": "missing",
                        "total_tokens": None,
                        "missing_token_usage_reason": (
                            "no_completed_runner_telemetry_token_usage_observed"
                        ),
                    },
                    "cost": {
                        "status": "missing",
                        "usd": None,
                        "missing_cost_reason": "provider_attempt_cost_not_exposed",
                    },
                },
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": transaction["mission_id"],
                "study_id": study_id,
                "objective": "Accepted paper mission waiting for OPL closeout readback.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": {
                    "candidate_writes_authority": False,
                    "blocked_paths": [
                        "publication_eval/latest.json",
                        "controller_decisions/latest.json",
                    ],
                    "forbidden_claims": ["publication_ready"],
                },
                "consume_result": {"status": "accepted"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": transaction,
                "one_shot_migration_readback": {
                    "current_mission": {
                        "objective_kind": "medical_prose_write_repair",
                        "legacy_blocker_is_default_execution_state": False,
                    },
                    "required_output": {"next_owner": "mission_executor"},
                    "consume_candidate_status": "accepted",
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    closeout = payload["stage_closure_decision"]["opl_closeout"]
    assert closeout["status"] == "opl_runtime_terminal_readback_observed"
    assert closeout["stage_attempt_id"] == "sat-dm003"
    assert closeout["duration"]["missing_duration_reason"] == "not_measured_for_full_stage"
    assert closeout["token_usage"]["missing_token_usage_reason"] == (
        "no_completed_runner_telemetry_token_usage_observed"
    )
    assert closeout["cost"]["missing_cost_reason"] == "provider_attempt_cost_not_exposed"
    assert "observability_gaps" not in payload["stage_closure_decision"]


def test_terminalize_stage_prefers_latest_consumption_closeout_over_inspect_placeholder(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260701Tstale-inspect"
        / study_id
    )
    mission_root.mkdir(parents=True)
    stale_transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::stale-inspect",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": stale_transaction["mission_id"],
                "study_id": study_id,
                "objective": "Stale inspect source that must not drive terminalize-stage.",
                "mission_state": "planned",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "claim_permissions": {
                    "can_claim_artifact_delta": False,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "consume_result": {"status": "not_consumed"},
                "paper_mission_transaction": stale_transaction,
            }
        ),
        encoding="utf-8",
    )
    transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::reviewer-revision",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "foreground-reviewer-revision"
        / study_id
    )
    _write_consumption_ledger(
        ledger_root=ledger_root,
        study_id=study_id,
        candidate_ref="/tmp/reviewer-revision/package_manifest.json",
        transaction=transaction,
    )
    closeout_ref = ledger_root / "stage_attempt_closeout_packet.json"
    closeout_ref.write_text(
        json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "completed",
                    "study_id": study_id,
                    "stage_id": transaction["opl_route_command"]["target"],
                    "stage_attempt_id": "sat-current-reviewer",
                    "stage_packet_ref": transaction["transaction_id"]
                + "#stage_terminal_decision",
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "route_identity_key": transaction["transaction_id"] + "::route",
                "work_unit_id": transaction["stage_id"],
                "work_unit_fingerprint": transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "closeout_refs": [
                    str(study_root / "artifacts/publication_eval/medical_prose_review.json"),
                ],
                "paper_stage_log": {
                    "duration": {"status": "observed", "seconds": 732},
                    "token_usage": {"status": "missing", "total_tokens": None},
                    "cost": {"status": "observed_or_unreported", "usd": 0},
                },
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--dry-run",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    summary = payload["source_readback_summary"]
    assert summary["surface_kind"] == "paper_mission_consumption_ledger_transaction_readback"
    assert payload["mission_id"] == transaction["mission_id"]
    assert payload["stage_closure_decision"]["stage_id"] == transaction["stage_id"]
    assert payload["stage_closure_decision"]["identity"][
        "paper_mission_transaction_ref"
    ] == transaction["transaction_id"]
    closeout = payload["stage_closure_decision"]["opl_closeout"]
    assert closeout["status"] == "opl_runtime_terminal_readback_observed"
    assert closeout["stage_attempt_id"] == "sat-current-reviewer"
    assert payload["authority_boundary"]["writes_authority"] is False


def test_inspect_prefers_latest_consumption_transaction_over_placeholder(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::reviewer-revision",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    _write_consumption_ledger(
        ledger_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_consumption_ledger"
            / "foreground-reviewer-revision"
            / study_id
        ),
        study_id=study_id,
        candidate_ref="/tmp/reviewer-revision/package_manifest.json",
        transaction=transaction,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_consumption_ledger_transaction_readback"
    assert payload["paper_mission_command"] == "inspect"
    assert payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["mission_id"] == transaction["mission_id"]
    assert payload["paper_mission_transaction"]["transaction_id"] == (
        transaction["transaction_id"]
    )
    assert payload["stage_terminal_decision"]["next_owner"] == "mission_executor"


def test_terminalize_stage_prefers_domain_transition_direct_closeout_over_old_consumption(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    stage_closure_ledger = importlib.import_module(
        "med_autoscience.paper_mission_stage_closure_ledger"
    )
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id

    old_transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::followthrough-02",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    old_ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "followthrough-02"
        / study_id
    )
    _write_consumption_ledger(
        ledger_root=old_ledger_root,
        study_id=study_id,
        candidate_ref="/tmp/followthrough-02/package_manifest.json",
        transaction=old_transaction,
    )
    (old_ledger_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": old_transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-old-followthrough",
                "paper_mission_transaction_ref": old_transaction["transaction_id"],
                "stage_packet_ref": (
                    old_transaction["transaction_id"] + "#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    old_transaction["transaction_id"] + "#opl_route_command"
                ),
                "work_unit_id": old_transaction["stage_id"],
                "work_unit_fingerprint": old_transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )
    stage_closure_ledger.write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "old-followthrough"
        ),
        study_id=study_id,
        decision={
            "stage_id": old_transaction["stage_id"],
            "work_unit_id": old_transaction["stage_id"],
            "work_unit_fingerprint": old_transaction["idempotency"][
                "transaction_fingerprint"
            ],
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "next_owner": "MedAutoScience",
                "next_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "authority_materialized": False,
            },
            "known_blockers": ["paper_mission_stage_route_domain_gate_pending"],
        },
        source_readback={
            "study_id": study_id,
            "source_ref": str(old_ledger_root / "consume_record.json"),
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "transaction_state": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": old_transaction,
        },
        source="test",
        forbidden_authority_writes=(),
        forbidden_authority_claims=(),
    )
    stale_receipt_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / "old-route-checkpoint"
        / study_id
    )
    stale_receipt_root.mkdir(parents=True)
    (stale_receipt_root / "receipt_owner_consumption.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_receipt_owner_consumption",
                "study_id": study_id,
                "status": "owner_consumption_applied",
                "authority_materialized": True,
                "stage_closure_decision": {
                    "surface_kind": "mas_stage_closure_decision",
                    "stage_id": old_transaction["stage_id"],
                    "work_unit_id": old_transaction["stage_id"],
                    "outcome": {
                        "kind": "next_stage_transition",
                        "transition_kind": "route_back_candidate_checkpoint",
                    },
                    "counts_as_typed_blocker": False,
                    "authority_boundary": {"writes_owner_receipt": False},
                },
            }
        ),
        encoding="utf-8",
    )

    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260704Tdomain-transition"
        / study_id
    )
    mission_root.mkdir(parents=True)
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": f"paper-mission::{study_id}::domain-transition",
                "study_id": study_id,
                "objective": "Current domain transition should drive AI reviewer.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "consume_result": {"status": "accepted"},
                "paper_mission_transaction": old_transaction,
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
            }
        ),
        encoding="utf-8",
    )

    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
    }

    monkeypatch.setattr(
        materialized_readback.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {"decision_type": "ai_reviewer_re_eval", "next_action": next_action},
    )
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-ai-reviewer"
        / study_id
    )
    closeout_root.mkdir(parents=True)
    inspect_projection = materialized_readback.build_materialized_mission_readback_if_available(
        profile=SimpleNamespace(
            name="Obesity",
            workspace_root=workspace_root,
            studies_root=workspace_root / "studies",
            default_publication_profile="general_medical_journal",
        ),
        profile_ref=profile_path,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source="test",
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    assert inspect_projection is not None
    direct_projection = inspect_projection["domain_transition_direct_stage_attempt"]
    carrier = direct_projection["opl_runtime_carrier"]
    (closeout_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": "review",
                "stage_attempt_id": "sat-ai-reviewer",
                "paper_mission_transaction_ref": carrier[
                    "paper_mission_transaction_ref"
                ],
                "stage_packet_ref": carrier["stage_terminal_decision_ref"],
                "opl_route_command_ref": carrier["opl_route_command_ref"],
                "route_identity_key": carrier["route_identity_key"],
                "work_unit_id": carrier["work_unit_id"],
                "work_unit_fingerprint": carrier["work_unit_fingerprint"],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "closeout_refs": [
                    str(study_root / "artifacts/publication_eval/latest.json")
                ],
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )
    inspect_projection = materialized_readback.build_materialized_mission_readback_if_available(
        profile=SimpleNamespace(
            name="Obesity",
            workspace_root=workspace_root,
            studies_root=workspace_root / "studies",
            default_publication_profile="general_medical_journal",
        ),
        profile_ref=profile_path,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source="test",
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    assert inspect_projection is not None
    direct_projection = inspect_projection["domain_transition_direct_stage_attempt"]
    assert direct_projection["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--dry-run",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["source_readback_summary"]["surface_kind"] == (
        "paper_mission_domain_transition_direct_stage_attempt_readback"
    )
    assert payload["stage_closure_decision"]["stage_id"] == "review"
    assert payload["stage_closure_decision"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["stage_closure_decision"]["outcome"]["kind"] != "typed_blocker"
    assert "not_applicable_domain_transition_direct" not in payload[
        "stage_closure_decision"
    ]["known_blockers"]
    assert "domain_transition_direct_stage_attempt" not in payload[
        "stage_closure_decision"
    ]["known_blockers"]
    assert payload["stage_closure_decision"]["opl_closeout"][
        "stage_attempt_id"
    ] == "sat-ai-reviewer"

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["stage_closure_decision"]["stage_id"] == "review"

    inspect_projection = materialized_readback.build_materialized_mission_readback_if_available(
        profile=SimpleNamespace(
            name="Obesity",
            workspace_root=workspace_root,
            studies_root=workspace_root / "studies",
            default_publication_profile="general_medical_journal",
        ),
        profile_ref=profile_path,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source="test",
        enable_opl_live_probe=True,
        opl_bin=None,
    )

    assert inspect_projection is not None
    assert inspect_projection["paper_mission_stage_closure_ledger_readback"][
        "stage_id"
    ] == "review"
    assert inspect_projection["stage_closure_decision"]["stage_id"] == "review"
    assert inspect_projection["stage_closure_decision"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert inspect_projection["stage_closure_decision"]["outcome"][
        "transition_kind"
    ] == "current_package_mirror_sync"
    assert inspect_projection["canonical_next_action_source"] == (
        "stage_closure.next_action"
    )
    assert inspect_projection["next_action"]["action_family"] == "paper.delivery.sync"


def test_terminalize_stage_prefers_domain_transition_direct_closeout_without_materialized_mission(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    direct_handoff = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.direct_next_action_handoff"
    )
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True, exist_ok=True)

    old_transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::followthrough-02",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    old_ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "followthrough-02"
        / study_id
    )
    _write_consumption_ledger(
        ledger_root=old_ledger_root,
        study_id=study_id,
        candidate_ref="/tmp/followthrough-02/package_manifest.json",
        transaction=old_transaction,
    )
    (old_ledger_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": old_transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-old-followthrough",
                "paper_mission_transaction_ref": old_transaction["transaction_id"],
                "stage_packet_ref": (
                    old_transaction["transaction_id"] + "#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    old_transaction["transaction_id"] + "#opl_route_command"
                ),
                "work_unit_id": old_transaction["stage_id"],
                "work_unit_fingerprint": old_transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )

    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
    }
    monkeypatch.setattr(
        materialized_readback.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {"decision_type": "ai_reviewer_re_eval", "next_action": next_action},
    )

    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )
    handoff = direct_handoff.build_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback={
            "mission_id": old_transaction["mission_id"],
            "study_id": study_id,
        },
        next_action=next_action,
    )
    carrier = handoff["opl_runtime_carrier"]
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-ai-reviewer"
        / study_id
    )
    closeout_root.mkdir(parents=True)
    (closeout_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": "review",
                "stage_attempt_id": "sat-ai-reviewer",
                "paper_mission_transaction_ref": carrier[
                    "paper_mission_transaction_ref"
                ],
                "stage_packet_ref": carrier["stage_terminal_decision_ref"],
                "opl_route_command_ref": carrier["opl_route_command_ref"],
                "route_identity_key": carrier["route_identity_key"],
                "work_unit_id": carrier["work_unit_id"],
                "work_unit_fingerprint": carrier["work_unit_fingerprint"],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--dry-run",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["source_readback_summary"]["surface_kind"] == (
        "paper_mission_domain_transition_direct_stage_attempt_readback"
    )
    assert payload["stage_closure_decision"]["stage_id"] == "review"
    assert payload["stage_closure_decision"]["opl_closeout"][
        "stage_attempt_id"
    ] == "sat-ai-reviewer"


def test_terminalize_stage_route_back_autodiscovery_reads_nested_attempt_packets(
    tmp_path: Path,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )
    packets_root = workspace_root / "ops" / "medautoscience" / "paper_mission_stage_attempts"
    work_unit_id = "submission_milestone_candidate::followthrough::followthrough-01"

    def write_packet(root: Path, attempt_id: str, mtime: float) -> None:
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            "ops/medautoscience/paper_mission_stage_attempts/"
            f"{attempt_id}/{study_id}/route_back_evidence_packet.json"
        )
        route_path = workspace_root / route_ref
        route_path.parent.mkdir(parents=True, exist_ok=True)
        route_path.write_text(
            json.dumps(
                {
                    "surface_kind": "paper_mission_stage_route_back_evidence_packet",
                    "study_id": study_id,
                    "stage_id": work_unit_id,
                    "work_unit_id": work_unit_id,
                }
            ),
            encoding="utf-8",
        )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(
            json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "owner_answer_candidate_materialized",
                    "study_id": study_id,
                    "stage_id": work_unit_id,
                    "work_unit_id": work_unit_id,
                    "stage_attempt_id": attempt_id,
                    "route_back_evidence_ref": route_ref,
                    "owner_answer_kind": "route_back_evidence_ref",
                    "provider_completion_is_domain_completion": False,
                    "provider_completion_is_domain_ready": False,
                }
            ),
            encoding="utf-8",
        )
        os.utime(packet_path, (mtime, mtime))

    write_packet(packets_root / "sat-old", "sat-old", 1_000.0)
    write_packet(packets_root / "sat-new" / study_id, "sat-new", 2_000.0)

    readback = commands._latest_stage_attempt_route_back_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source_readback={
            "stage_terminal_decision": {
                "next_work_unit": work_unit_id,
            },
        },
        source="test",
    )

    assert readback is not None
    assert readback["source_ref"].endswith(
        f"paper_mission_stage_attempts/sat-new/{study_id}/stage_attempt_closeout_packet.json"
    )
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-new"


def test_terminalize_stage_prefers_current_transaction_stage_closure_over_stale_direct(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    transaction_id = (
        "paper-mission-transaction::002::submission_milestone_candidate::"
        "followthrough-02"
    )
    source_readback = {
        "study_id": study_id,
        "mission_id": "paper-mission::002",
        "paper_mission_transaction": {
            "transaction_id": transaction_id,
            "study_id": study_id,
            "stage_id": "submission_milestone_candidate::followthrough::followthrough-02",
        },
        "consume_candidate_status": "accepted_submission_milestone_candidate",
        "transaction_state": "accepted_submission_milestone_candidate",
        "stage_closure_decision": {
            "surface_kind": "mas_stage_closure_decision",
            "stage_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "identity": {"paper_mission_transaction_ref": transaction_id},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-current-followthrough",
                "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
            },
        },
        "domain_transition": {
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            }
        },
        "current_package": {"status": "current", "can_submit": False},
        "opl_runtime_carrier_readback": {
            "carrier_status": "opl_runtime_terminal_readback_observed",
            "terminal_closeout": {
                "stage_attempt_id": "sat-current-followthrough",
                "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
                "closeout_refs": [
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current-followthrough/"
                    f"{study_id}/stage_attempt_closeout_packet.json"
                ],
            },
        },
        "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
    }
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )

    monkeypatch.setattr(
        commands,
        "_build_materialized_mission_readback_if_available",
        lambda **_: source_readback,
    )

    def fail_if_stale_direct_is_used(**_: object) -> None:
        raise AssertionError("stale domain-transition direct closeout should not win")

    monkeypatch.setattr(
        commands,
        "_domain_transition_direct_terminal_source_readback",
        fail_if_stale_direct_is_used,
    )

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )
    decision = commands._terminalize_stage_closure_from_readback(readback)

    assert readback is source_readback
    assert decision["stage_id"] == (
        "submission_milestone_candidate::followthrough::followthrough-01"
    )
    assert decision["opl_closeout"]["stage_attempt_id"] == "sat-current-followthrough"


def test_terminalize_stage_prefers_newer_workspace_stage_packet_over_matching_source_closeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    packets_root = (
        workspace_root / "ops" / "medautoscience" / "paper_mission_stage_attempts"
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    transaction_id = "paper-mission-transaction::dm003::write::current"

    def write_packet(attempt_id: str, stage_id: str, mtime: float) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        (workspace_root / route_ref).write_text(
            json.dumps(
                {
                    "surface_kind": "paper_mission_stage_route_back_evidence_packet",
                    "study_id": study_id,
                    "stage_id": "write",
                    "work_unit_id": work_unit_id,
                    "owner_answer_kind": "route_back_evidence_ref",
                }
            ),
            encoding="utf-8",
        )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(
            json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "route_back_evidence_candidate",
                    "study_id": study_id,
                    "stage_id": stage_id,
                    "stage_attempt_id": attempt_id,
                    "route_back_evidence_ref": route_ref,
                    "owner_answer_kind": "route_back_evidence_ref",
                }
            ),
            encoding="utf-8",
        )
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    old_packet = write_packet("sat-old", "write", 1_000.0)
    new_packet = write_packet("sat-new", work_unit_id, 2_000.0)
    source_readback = {
        "study_id": study_id,
        "mission_id": f"paper-mission::{study_id}::terminalize-test",
        "mission_state": "route_back",
        "consume_candidate_status": "route_back",
        "paper_mission_transaction": {
            "transaction_id": transaction_id,
            "stage_id": "write",
            "work_unit_id": work_unit_id,
        },
        "stage_closure_decision": {
            "identity": {
                "paper_mission_transaction_ref": transaction_id,
            },
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-old",
            },
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_attempt_id": "sat-old",
                "closeout_refs": [str(old_packet)],
            }
        },
    }
    monkeypatch.setattr(
        commands,
        "_build_materialized_mission_readback_if_available",
        lambda **_: source_readback,
    )
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )

    readback = commands._build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source="test",
    )

    assert readback["source_ref"] == str(new_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-new"


def test_latest_stage_attempt_route_back_source_readback_prefers_current_terminal_attempt_over_newer_stale_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    packets_root = (
        workspace_root / "ops" / "medautoscience" / "paper_mission_stage_attempts"
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    transaction_id = "paper-mission-transaction::dm003::write::current"

    def write_packet(attempt_id: str, stage_id: str, mtime: float) -> Path:
        root = packets_root / attempt_id
        root.mkdir(parents=True, exist_ok=True)
        route_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            "route_back_evidence_packet.json"
        )
        (workspace_root / route_ref).write_text(
            json.dumps(
                {
                    "surface_kind": "paper_mission_stage_route_back_evidence_packet",
                    "study_id": study_id,
                    "stage_id": "write",
                    "work_unit_id": work_unit_id,
                    "owner_answer_kind": "route_back_evidence_ref",
                }
            ),
            encoding="utf-8",
        )
        packet_path = root / "stage_attempt_closeout_packet.json"
        packet_path.write_text(
            json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "route_back_evidence_candidate",
                    "study_id": study_id,
                    "stage_id": stage_id,
                    "stage_attempt_id": attempt_id,
                    "route_back_evidence_ref": route_ref,
                    "owner_answer_kind": "route_back_evidence_ref",
                }
            ),
            encoding="utf-8",
        )
        os.utime(packet_path, (mtime, mtime))
        return packet_path

    current_packet = write_packet("sat-current", work_unit_id, 1_000.0)
    stale_packet = write_packet("sat-stale", work_unit_id, 2_000.0)
    source_readback = {
        "study_id": study_id,
        "mission_id": f"paper-mission::{study_id}::terminalize-test",
        "mission_state": "route_back",
        "consume_candidate_status": "route_back",
        "paper_mission_transaction": {
            "transaction_id": transaction_id,
            "stage_id": "write",
            "work_unit_id": work_unit_id,
        },
        "stage_closure_decision": {
            "identity": {
                "paper_mission_transaction_ref": transaction_id,
            },
            "opl_closeout": {
                "status": "opl_runtime_terminal_readback_observed",
                "stage_attempt_id": "sat-stale",
            },
        },
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "stage_attempt_id": "sat-current",
                "closeout_ref": "opl://family-runtime/tasks/frt-current/terminal-closeout-readback",
                "runtime_readback_source": "opl_family_runtime_queue_inspect",
                "closeout_refs": [str(current_packet)],
            }
        },
        "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
    }
    monkeypatch.setattr(
        commands,
        "_build_materialized_mission_readback_if_available",
        lambda **_: source_readback,
    )
    profile = SimpleNamespace(
        name="DM",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )

    readback = commands._latest_stage_attempt_route_back_source_readback(
        profile=profile,
        profile_ref=profile_path,
        study_id=study_id,
        source_readback=source_readback,
        source="test",
    )

    assert readback is not None
    assert readback["source_ref"] == str(current_packet)
    assert readback["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-current"
    assert stale_packet.stat().st_mtime > current_packet.stat().st_mtime


def test_consumption_ledger_inspect_prefers_current_handoff_after_owner_consumed_route_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "workspace" / "studies" / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM",
        workspace_root=tmp_path / "workspace",
        studies_root=tmp_path / "workspace" / "studies",
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone::current-write"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    work_unit_fingerprint = (
        "domain-transition::route_back_same_line::"
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )
    stage_terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": "MAS canonical next action requests the current write repair work unit.",
        "next_owner": "write",
        "next_work_unit": work_unit_id,
        "recommended_next_action": "request_opl_stage_attempt",
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_next_action_ref": work_unit_fingerprint,
    }
    opl_route_command = {
        "command_kind": "resume_stage",
        "target": work_unit_id,
        "reason": "MAS canonical next action requests the current write repair work unit.",
        "runtime_owner": "one-person-lab",
    }
    opl_runtime_carrier = {
        "surface_kind": "mas_domain_progress_transition_request",
        "study_id": study_id,
        "stage_id": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "target_runtime_owner": "one-person-lab",
        "route_identity_key": "route::dm003-current-write",
        "attempt_idempotency_key": "attempt::dm003-current-write",
        "request_idempotency_key": "request::dm003-current-write",
    }

    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: {
            "status": "owner_consumption_applied",
            "stage_closure_decision": {
                "decision_ref": f"{mission_id}#stage-closure",
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "next_owner": "MedAutoScience",
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-review/stage_attempt_closeout_packet.json"
                    ),
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "next_legal_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-review",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-review/stage_attempt_closeout_packet.json"
                ),
                "can_claim_paper_progress": False,
            },
        },
    )
    monkeypatch.setattr(
        commands.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
            },
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai-reviewer",
            },
        },
    )

    payload = commands._consumption_ledger_inspect_readback(
        profile=profile,
        profile_ref=tmp_path / "dm.local.toml",
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        consumption_readback={
            "surface_kind": "paper_mission_consumption_readback",
            "mission_id": mission_id,
            "study_id": study_id,
            "selected_outcome": "accepted_submission_milestone_candidate",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": transaction,
            "stage_terminal_decision": stage_terminal_decision,
            "opl_route_command": opl_route_command,
            "opl_runtime_carrier": opl_runtime_carrier,
            "opl_route_handoff": {
                "handoff_status": "ready_for_opl_route_command",
                "next_owner": "write",
                "can_submit_to_opl_runtime": True,
                "stage_terminal_decision": stage_terminal_decision,
                "opl_route_command": opl_route_command,
                "opl_runtime_carrier": opl_runtime_carrier,
            },
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["canonical_next_action_source"] == (
        "paper_mission_next_action_envelope"
    )
    assert payload["next_action"]["action_family"] == "runtime.opl_route"
    assert payload["next_action"]["owner"] == "one-person-lab"
    assert payload["next_action"]["work_unit_id"] == work_unit_id
    assert payload["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert payload["domain_transition_direct_stage_attempt"]["opl_route_handoff"][
        "work_unit_id"
    ] == work_unit_id


def test_stage_closure_terminalizer_supersedes_legacy_route_back_checkpoint() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    decision = commands._terminalize_stage_closure_from_readback(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "mission_id": "mission-002",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": {
                "transaction_id": "txn-002",
                "stage_id": "submission_milestone_candidate",
            },
            "stage_terminal_decision": {
                "status": "accepted_submission_milestone_candidate",
                "reason": "paper_mission_stage_route_domain_gate_pending",
            },
            "stage_closure_decision": {
                "decision_signature": "legacy-signature-before-blocker-normalization",
                "outcome": {"transition_kind": "route_back_candidate_checkpoint"},
                "observability_gaps": [
                    "duration_ms_missing",
                    "token_usage_missing",
                    "cost_usd_missing",
                ],
            },
        }
    )

    assert decision["repeated_without_semantic_delta"] is True
    assert decision["outcome"]["kind"] == "typed_blocker"
    assert (
        decision["outcome"]["blocker_type"]
        == "route_back_checkpoint_without_semantic_delta"
    )
    assert "observability_gaps" not in decision
    assert decision["opl_closeout"]["duration"]["missing_duration_reason"] == (
        "stage_closeout_status_missing::duration_not_recorded"
    )
    assert decision["opl_closeout"]["token_usage"]["missing_token_usage_reason"] == (
        "stage_closeout_status_missing::token_usage_not_recorded"
    )
    assert decision["opl_closeout"]["cost"]["missing_cost_reason"] == (
        "stage_closeout_status_missing::cost_not_recorded"
    )


def test_durable_stop_guard_rejects_non_terminal_next_stage_transitions() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    for transition_kind in (
        "current_package_mirror_sync",
        "route_back_candidate_checkpoint",
        "bounded_quality_repair_iteration",
    ):
        guard = commands._durable_mission_stop_guard(
            consume_candidate_status="stage_closure_observed",
            stage_closure_decision={
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": transition_kind,
                }
            },
        )

        assert guard["durable_stop_allowed"] is False

    degraded_guard = commands._durable_mission_stop_guard(
        consume_candidate_status="stage_closure_observed",
        stage_closure_decision={
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "degraded_handoff",
            }
        },
    )
    assert degraded_guard["durable_stop_allowed"] is True


def _write_consumption_ledger(
    *,
    ledger_root: Path,
    study_id: str,
    candidate_ref: str,
    transaction: dict,
) -> None:
    ledger_root.mkdir(parents=True)
    stage_ref = transaction["transaction_id"] + "#stage_terminal_decision"
    route_ref = transaction["transaction_id"] + "#opl_route_command"
    carrier = _paper_mission_carrier_for_transaction(transaction)
    consume_record = {
        "surface_kind": "mas_paper_mission_candidate_consumption_record",
        "study_id": study_id,
        "candidate_ref": candidate_ref,
        "candidate_id": "reviewer-revision-v3",
        "status": "accepted",
        "selected_outcome": "accepted",
        "route_handoff_status": "ready_for_opl_route_command",
        "paper_mission_transaction_ref": transaction["transaction_id"],
        "stage_terminal_decision_ref": stage_ref,
        "opl_route_command_ref": route_ref,
        "counts_as_stage_terminalizer_evidence": True,
        "counts_as_opl_route_handoff_evidence": True,
        "authority_materialized": False,
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": {"writes_authority": False},
        "consume_result": {"status": "accepted"},
    }
    (ledger_root / "consume_record.json").write_text(
        json.dumps(consume_record),
        encoding="utf-8",
    )
    (ledger_root / "consume_readback.json").write_text(
        json.dumps({"paper_mission_transaction": transaction}),
        encoding="utf-8",
    )
    (ledger_root / "stage_terminal_decision.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_stage_terminal_decision_packet",
                "study_id": study_id,
                "candidate_ref": candidate_ref,
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "stage_terminal_decision_ref": stage_ref,
                "stage_id": transaction["stage_id"],
                "stage_run_ref": transaction["stage_run_ref"],
                "stage_terminal_decision": transaction["stage_terminal_decision"],
                "transaction_state": "accepted_submission_milestone_candidate",
                "authority_boundary": {"writes_authority": False},
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_command.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_opl_route_command_packet",
                "study_id": study_id,
                "candidate_ref": candidate_ref,
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "opl_route_command_ref": route_ref,
                "opl_route_command": transaction["opl_route_command"],
                "opl_runtime_carrier": carrier,
                "authority_boundary": {"writes_authority": False},
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_handoff.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_opl_route_handoff_record",
                "study_id": study_id,
                "handoff_status": "ready_for_opl_route_command",
                "can_submit_to_opl_runtime": True,
                "transaction_materialized": True,
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "stage_terminal_decision_ref": stage_ref,
                "opl_route_command_ref": route_ref,
                "stage_terminal_decision": transaction["stage_terminal_decision"],
                "opl_route_command": transaction["opl_route_command"],
                "route_command_kind": transaction["opl_route_command"]["command_kind"],
                "opl_runtime_carrier": carrier,
                "authority_boundary": {"writes_authority": False},
            }
        ),
        encoding="utf-8",
    )


def _paper_mission_carrier_for_transaction(transaction: dict) -> dict:
    identity = transaction["idempotency"]
    decision = transaction["stage_terminal_decision"]
    work_unit_id = (
        decision.get("next_work_unit")
        if decision.get("decision_kind") == "continue_same_stage"
        else None
    ) or transaction["stage_id"]
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "source_kind": "paper_mission_transaction_opl_route_command",
        "projection_only": True,
        "paper_mission_transaction_ref": transaction["transaction_id"],
        "stage_terminal_decision_ref": transaction["transaction_id"]
        + "#stage_terminal_decision",
        "opl_route_command_ref": transaction["transaction_id"] + "#opl_route_command",
        "study_id": transaction["study_id"],
        "stage_run_ref": transaction["stage_run_ref"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": identity["transaction_fingerprint"],
        "route_identity_key": transaction["transaction_id"] + "::route",
        "idempotency_key": identity["idempotency_key"],
        "attempt_idempotency_key": identity["idempotency_key"] + "::opl-attempt",
        "request_idempotency_key": identity["idempotency_key"] + "::opl-request",
        "opl_route_command": transaction["opl_route_command"],
        "aggregate_identity": {
            "aggregate_id": transaction["transaction_id"],
            "mission_id": transaction["mission_id"],
            "study_id": transaction["study_id"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": identity["transaction_fingerprint"],
        },
    }
