from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from .shared import write_profile
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.consume_submission_package import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.output_guards import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.one_shot_migration import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.package_candidate import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.drive_and_route_handoff import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.domain_handler_dispatch import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.materialized_readback import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.receipt_owner_consumption import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.typed_blocker_resolution import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.submission_milestone_candidate_package import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_commands_cases.materialized_terminal_closeout import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_commands_cases.route_back_budget import *  # noqa: F401,F403


FORBIDDEN_AUTHORITY_RELATIVE_PATHS = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "paper/current_package",
)
DM_CANARY_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "paper_mission_dm_canary"
)


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))

def test_paper_mission_help_exposes_default_commands(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["paper-mission", "--help"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    for command in (
        "inspect",
        "start",
        "resume",
        "consume-candidate",
        "package-candidate",
        "receipt-owner-consumption",
        "typed-blocker-resolution",
        "drive",
        "terminalize-stage",
        "typed-blocker-resolution",
    ):
        assert command in captured.out


@pytest.mark.parametrize(
    ("argv_tail", "expected_command", "expected_intent", "expected_dry_run"),
    (
        (["inspect"], "inspect", "paper_mission/inspect", False),
        (
            ["start", "--objective", "gate clearing", "--dry-run"],
            "start",
            "paper_mission/start_or_resume",
            True,
        ),
        (
            ["resume", "--mission-id", "mission-001", "--dry-run"],
            "resume",
            "paper_mission/start_or_resume",
            True,
        ),
        (
            ["consume-candidate", "--candidate", "candidates/mission.json", "--dry-run"],
            "consume-candidate",
            "paper_mission/consume_candidate",
            True,
        ),
    ),
)
def test_paper_mission_cli_returns_no_write_json_plan(
    tmp_path: Path,
    capsys,
    argv_tail: list[str],
    expected_command: str,
    expected_intent: str,
    expected_dry_run: bool,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)

    exit_code = cli.main(
        [
            "paper-mission",
            *argv_tail,
            "--profile",
            str(profile_path),
            "--study-id",
            "001-paper",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_no_write_readback"
    assert payload["paper_mission_command"] == expected_command
    assert payload["action_intent"] == expected_intent
    assert payload["dry_run"] is expected_dry_run
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_runtime"] is False
    assert payload["transaction_state"] == "not_materialized"
    assert payload["stage_terminal_decision"]["authority_materialized"] is False
    assert payload["opl_route_command"]["authority_materialized"] is False
    assert payload["opl_runtime_carrier"]["surface_kind"] == (
        "mas_domain_progress_transition_request"
    )
    assert payload["opl_runtime_carrier"]["provider_admission_pending"] is False
    assert payload["opl_runtime_carrier"][
        "provider_admission_requires_opl_runtime_result"
    ] is True
    assert payload["paper_mission_run_candidate"]["transaction_state"] == (
        "not_materialized"
    )
    assert "publication_eval/latest.json" in payload["forbidden_authority_writes"]
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_typed_blocker_resolution_action_intent(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "readback.json"
    readback_file.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "stage_closure_decision": {"outcome": {"kind": "typed_blocker"}},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "typed-blocker-resolution",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_typed_blocker_resolution"


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


def test_paper_mission_start_reads_materialized_one_shot_mission_when_present(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260623T2032Z"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::one-shot-migration",
        "study_id": study_id,
        "objective": "Consume DM002 publication blockers and repair claim/evidence gaps.",
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::claim-evidence-repair",
                "artifact_ref": "mission://dm002/claim-evidence-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "route_back"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "route_back",
        },
    }
    mission_payload["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission_id=mission_payload["mission_id"],
        study_id=study_id,
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps({"candidate_id": "pmc-dm002"}),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "start",
            "--dry-run",
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
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["paper_mission_run"]["mission_id"] == mission_payload["mission_id"]
    assert payload["paper_mission_run"]["mission_state"] == (
        "candidate_ready_for_consumption"
    )
    assert payload["default_readback"]["current_mission"]["objective_kind"] == (
        "gate_clearing_claim_evidence_repair"
    )
    assert payload["consume_candidate_status"] == "route_back"
    assert payload["transaction_state"] == "terminal_decision_recorded"
    assert payload["stage_terminal_decision"] == (
        mission_payload["paper_mission_transaction"]["stage_terminal_decision"]
    )
    assert payload["opl_route_command"] == (
        mission_payload["paper_mission_transaction"]["opl_route_command"]
    )
    assert payload["opl_runtime_carrier"]["paper_mission_transaction_ref"] == (
        mission_payload["paper_mission_transaction"]["transaction_id"]
    )
    assert payload["opl_runtime_carrier"]["opl_route_command"] == payload[
        "opl_route_command"
    ]
    assert payload["opl_runtime_carrier"]["can_write_opl_stage_run"] is False
    assert payload["dispatch_plan"]["domain_handler_dispatch_mode"] == (
        "materialized_mission_readback_no_write"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)

def test_paper_mission_start_reads_materialized_mission_for_dm_alias(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    canonical_study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=canonical_study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260623T2032Z"
        / canonical_study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": (
            f"paper-mission::{canonical_study_id}::gate-clearing::one-shot-migration"
        ),
        "study_id": canonical_study_id,
        "objective": "Consume DM002 publication blockers and repair claim/evidence gaps.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::claim-evidence-repair",
                "artifact_ref": "mission://dm002/claim-evidence-repair",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate_consumed",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "start",
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "DM002",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["requested_study_id"] == "DM002"
    assert payload["study_id"] == canonical_study_id
    assert payload["study_root"].endswith(f"/studies/{canonical_study_id}")
    assert payload["study_root_exists"] is True
    assert payload["paper_mission_run"]["mission_id"] == mission_payload["mission_id"]
    assert payload["consume_candidate_status"] == "accepted"
    assert payload["dispatch_plan"]["domain_handler_dispatch_mode"] == (
        "materialized_mission_readback_no_write"
    )
    _assert_forbidden_authority_untouched(tmp_path, study_id=canonical_study_id)


def test_paper_mission_materialized_legacy_run_without_transaction_terminalizes_consume_result(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "legacy"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": f"paper-mission::{study_id}::legacy::one-shot-migration",
        "study_id": study_id,
        "objective": "Legacy materialized mission without a transaction field.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::legacy",
                "artifact_ref": "mission://legacy/artifact-delta",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate_consumed",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": str(mission_root / "legacy_truth_import_pack.json"),
            }
        ],
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            }
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": [
                "publication_ready",
                "current_package",
                "owner_receipt_written",
            ],
        },
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "analysis-campaign",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "consume_candidate_status": "accepted",
        },
    }
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
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
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["paper_mission_transaction"]["transaction_id"].startswith(
        f"paper-mission-transaction::{study_id}::gate_clearing_claim_evidence_repair"
    )
    assert payload["transaction_state"] == "accepted"
    assert payload["stage_terminal_decision"]["decision_kind"] == "advance"
    assert payload["stage_terminal_decision"]["next_stage_id"] == (
        "publication_gate_replay"
    )
    assert payload["opl_route_command"]["command_kind"] == "start_next_stage"
    assert payload["opl_route_command"]["target"] == "publication_gate_replay"
    assert payload["opl_runtime_carrier"]["surface_kind"] == (
        "mas_domain_progress_transition_request"
    )
    assert payload["opl_runtime_carrier"]["carrier_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert payload["opl_runtime_carrier"]["can_claim_provider_running"] is False
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "materialized_paper_mission_run"
    )
    assert payload["paper_mission_transaction_readback"]["validation"]["status"] == (
        "validated"
    )
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["paper_mission_run"]["paper_audit_pack"]
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)
