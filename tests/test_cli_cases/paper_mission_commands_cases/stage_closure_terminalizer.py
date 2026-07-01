from __future__ import annotations

import importlib
import json
from pathlib import Path

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


def test_stage_closure_terminalizer_reterminalizes_waiting_opl_closeout_when_terminal_readback_arrives() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    existing_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "outcome": {
            "kind": "typed_blocker",
            "blocker_type": "route_back_checkpoint_without_semantic_delta",
        },
        "opl_closeout": {"status": "waiting_for_opl_runtime_live_readback"},
    }
    assert commands._stage_closure_decision_requires_reterminalize(
        existing_decision
    ) is True

    decision = commands._terminalize_stage_closure_from_readback(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "mission_id": "mission-002",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": {
                "transaction_id": "txn-002",
                "stage_id": "submission_milestone_candidate::followthrough::followthrough-02",
            },
            "stage_terminal_decision": {
                "status": "accepted_submission_milestone_candidate",
            },
            "stage_closure_decision": existing_decision,
            "opl_runtime_carrier_readback": {
                "carrier_status": "opl_runtime_terminal_readback_observed",
                "terminal_closeout": {
                    "status": "completed",
                    "stage_attempt_id": "sat-002-terminal",
                },
            },
        }
    )

    assert decision["opl_closeout"]["status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    assert decision["opl_closeout"]["stage_attempt_id"] == "sat-002-terminal"


def test_stage_closure_terminalizer_keeps_receipt_owner_consumed_typed_blocker() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    receipt_owner_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "authority_materialized": True,
        "counts_as_typed_blocker": True,
        "authority_boundary": {
            "surface_role": "paper_mission_receipt_owner_consumption",
        },
        "outcome": {
            "kind": "typed_blocker",
            "blocker_type": "paper_mission_stage_route_domain_gate_pending",
        },
    }

    assert (
        commands._stage_closure_decision_requires_reterminalize(
            receipt_owner_decision,
            current_package={
                "package_kind": "submission_ready_package",
                "can_submit": True,
                "quality_gate_status": "clear",
                "known_blockers": [],
                "generated_from_current_source": True,
                "root": "/tmp/current_package",
                "zip_exists": True,
                "freshness_status": "current",
            },
        )
        is False
    )


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
        "work_unit_id": transaction["stage_id"],
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
            "work_unit_id": transaction["stage_id"],
            "work_unit_fingerprint": identity["transaction_fingerprint"],
        },
    }
