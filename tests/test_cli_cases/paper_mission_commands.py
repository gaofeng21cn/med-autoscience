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
from tests.test_cli_cases.paper_mission_command_cases.submission_milestone_candidate_package import *  # noqa: F401,F403


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
        "drive",
        "terminalize-stage",
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
    assert initial["stage_closure_outcome"] == "stage_closure_decision_missing"

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
    assert terminalized["status"] == "terminalizer_outcome_materialized"
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


def test_route_back_budget_counts_synonymous_followthrough_route_back(tmp_path: Path) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    def route_back_readback(*, followthrough: str = "") -> tuple[dict, dict]:
        mission_id = f"mission-001{followthrough}"
        transaction_id = (
            "paper-mission-transaction::study-001::paper-stage::gate::"
            f"mission-001{followthrough}"
        )
        decision = {
            "decision_kind": "route_back",
            "status": "route_back",
            "next_owner": "mission_executor",
            "target_stage_id": "paper-stage::gate",
            "route_back_evidence_ref": (
                "route-back:paper-mission-terminal-owner-gate:study-001:"
                f"sat-terminal{followthrough}"
            ),
        }
        readback = {
            "study_id": "study-001",
            "mission_id": mission_id,
            "candidate_ref": f"candidate{followthrough}.json",
            "paper_mission_transaction": {
                "transaction_id": transaction_id,
                "mission_id": mission_id,
                "study_id": "study-001",
                "stage_id": "paper-stage::gate",
                "stage_terminal_decision": decision,
            },
            "stage_terminal_decision": decision,
            "opl_route_command": {
                "command_kind": "route_back",
                "target": "paper-stage::gate",
                "paper_mission_transaction_ref": transaction_id,
            },
            "next_owner_or_human_decision": {"next_owner": "mission_executor"},
            "terminal_owner_gate": {
                "owner": "mas_authority_kernel",
                "gate_kind": "domain_gate",
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
            },
            "terminal_owner_gate_owner_answer_readback": {
                "status": "route_back",
                "owner_answer_shape": "route_back_evidence_ref",
                "route_back_evidence_ref": decision["route_back_evidence_ref"],
                "stage_terminal_decision": decision,
            },
        }
        handoff = {
            "study_id": "study-001",
            "mission_id": mission_id,
            "paper_mission_transaction_ref": transaction_id,
            "candidate_ref": f"candidate{followthrough}.json",
            "next_owner": "mission_executor",
            "route_command_kind": "route_back",
            "route_target": "paper-stage::gate",
        }
        return readback, handoff

    ledger = commands._empty_paper_mission_route_back_budget_ledger(
        study_id="study-001"
    )
    first_readback, first_handoff = route_back_readback()
    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first_readback,
        handoff=first_handoff,
        route_back_budget_ledger=ledger,
    )
    assert first_guard["route_back_budget"]["next_observed_count"] == 1
    assert first_guard["route_back_budget"]["budget_exhausted"] is False
    assert first_guard["signature_payload"]["semantic_delta_refs"] == {}

    ledger_ref = tmp_path / "route_back_budget_ledger.json"
    ledger = commands._record_paper_mission_route_back_budget_ledger(
        ledger=ledger,
        ledger_ref=ledger_ref,
        progress_guard=first_guard,
        consume_readback=first_readback,
        handoff=first_handoff,
        trigger="drive-initial",
        source="pytest",
    )

    second_readback, second_handoff = route_back_readback(
        followthrough="::followthrough-02"
    )
    second_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=second_readback,
        handoff=second_handoff,
        previous_guard=first_guard,
        route_back_budget_ledger=ledger,
    )

    assert second_guard["signature"] == first_guard["signature"]
    assert second_guard["status"] == "non_advancing_route_back"
    assert second_guard["route_back_budget"]["next_observed_count"] == 2
    assert second_guard["route_back_budget"]["budget_exhausted"] is True
    assert second_guard["route_back_budget"]["required_next_owner"] == (
        "mission_executor"
    )
    assert second_guard["route_back_budget"]["next_mode"] == (
        "mas_mission_executor_fallback"
    )
    assert second_guard["can_claim_submission_ready"] is False
    assert second_guard["can_claim_runtime_ready"] is False

    ledger = commands._record_paper_mission_route_back_budget_ledger(
        ledger=ledger,
        ledger_ref=ledger_ref,
        progress_guard=second_guard,
        consume_readback=second_readback,
        handoff=second_handoff,
        trigger="followthrough-02",
        source="pytest",
    )
    assert ledger_ref.exists()
    assert ledger["signatures"][second_guard["signature"]]["observed_count"] == 2
    assert ledger["latest_budget_status"]["budget_exhausted"] is True
    assert ledger["authority_boundary"]["ledger_is_authority"] is False


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


def test_paper_mission_materialized_readback_consumes_matching_opl_terminal_closeout(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
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
        mission_id=f"paper-mission::{study_id}::gate-clearing::one-shot-migration",
        study_id=study_id,
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": transaction["mission_id"],
        "study_id": study_id,
        "objective": "Accepted paper mission waiting for OPL closeout readback.",
        "mission_state": "consumed",
        "artifact_delta_ledger": [
            {
                "delta_id": "delta::dm002::one-shot",
                "artifact_ref": "mission://dm002/owner-decision",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate_consumed",
            }
        ],
        "source_refs": [
            {
                "ref_id": "legacy_truth_import_pack",
                "ref_kind": "legacy_truth_import_pack",
                "uri": "mission://dm002/import-pack",
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
        "paper_mission_transaction": transaction,
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
    _write_matching_domain_gate_closeout(
        study_root=study_root,
        study_id=study_id,
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
    assert payload["surface_kind"] == "paper_mission_materialized_readback"
    assert payload["opl_runtime_carrier"]["carrier_status"] == (
        "waiting_for_opl_runtime_live_readback"
    )
    assert payload["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    carrier_readback = payload["opl_runtime_carrier_readback"]
    assert carrier_readback["runtime_readback_status"] == "terminal_closeout_observed"
    assert carrier_readback["domain_ready_verdict"] == "domain_gate_pending"
    assert carrier_readback["can_claim_paper_progress"] is False
    assert carrier_readback["provider_completion_is_domain_completion"] is False
    assert carrier_readback["provider_completion_is_domain_ready"] is False
    assert carrier_readback["authority_materialized"] is False
    assert carrier_readback["terminal_closeout"]["stage_attempt_id"] == "sat-terminal"
    assert carrier_readback["terminal_closeout"]["closeout_ref"] == (
        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
        "sat-terminal.closeout.json"
    )
    assert payload["terminal_owner_gate"] == {
        "surface_kind": "paper_mission_terminal_owner_gate",
        "owner": "mas_authority_kernel",
        "gate_kind": "domain_gate",
        "blocked_reason": "domain_gate_pending",
        "typed_blocker_ref": (
            "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
            "sat-terminal.closeout.json#domain_blocker"
        ),
        "closeout_ref": (
            "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
            "sat-terminal.closeout.json"
        ),
        "stage_attempt_id": "sat-terminal",
        "work_unit_id": "paper-stage::gate-clearing",
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "legal_next_action": "route_to_owner_or_human_gate",
    }
    assert {
        key: payload["next_owner_or_human_decision"][key]
        for key in (
            "kind",
            "next_owner",
            "human_decision_required",
            "summary",
            "route_back_evidence_ref",
            "opl_route_command_ref",
            "can_execute",
            "can_authorize_provider_admission",
        )
    } == {
        "kind": "owner_or_route",
        "next_owner": "mission_executor",
        "human_decision_required": False,
        "summary": "route_back",
        "route_back_evidence_ref": payload[
            "terminal_owner_gate_owner_answer_readback"
        ]["route_back_evidence_ref"],
        "opl_route_command_ref": payload[
            "terminal_owner_gate_owner_answer_readback"
        ]["opl_route_command"]["source_terminal_decision_ref"],
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }
    authority_readback = payload["terminal_owner_gate_authority_readback"]
    assert authority_readback["surface_kind"] == (
        "mas_terminal_owner_gate_authority_readback"
    )
    assert authority_readback["status"] == "route_back"
    assert authority_readback["next_owner"] == "mas_authority_kernel"
    assert authority_readback["owner_answer_materialized"] is True
    assert authority_readback["consume_result"]["status"] == "route_back"
    assert authority_readback["consume_result"]["outcome"] == "route_back_evidence_ref"
    assert authority_readback["consume_result"]["authority_materialized"] is False
    assert authority_readback["consume_result"][
        "authority_answer_readback_materialized"
    ] is True
    assert authority_readback["consume_result"]["authority_file_materialized"] is False
    assert authority_readback["route_back_evidence_ref"].startswith(
        f"route-back:paper-mission-terminal-owner-gate:{study_id}:"
    )
    owner_answer = payload["terminal_owner_gate_owner_answer_readback"]
    assert owner_answer["surface_kind"] == (
        "mas_terminal_owner_gate_owner_answer_readback"
    )
    assert owner_answer["status"] == "route_back"
    assert owner_answer["owner_answer_shape"] == "route_back_evidence_ref"
    assert owner_answer["authority_materialized"] is False
    assert owner_answer["authority_answer_readback_materialized"] is True
    assert owner_answer["authority_file_materialized"] is False
    assert owner_answer["can_claim_paper_progress"] is False
    assert owner_answer["can_claim_runtime_ready"] is False
    assert owner_answer["write_plan"]["written_files"] == []
    assert owner_answer["write_plan"]["can_write_owner_receipts"] is False
    assert owner_answer["write_plan"]["can_write_typed_blockers"] is False
    assert owner_answer["write_plan"]["can_write_human_gate_authority_records"] is False
    assert owner_answer["stage_terminal_decision"]["decision_kind"] == "route_back"
    assert owner_answer["opl_route_command"]["command_kind"] == "route_back"
    assert owner_answer["route_back_budget"]["opl_redrive_budget_remaining"] == 0
    assert owner_answer["route_back_budget"]["next_mode"] == (
        "mas_mission_executor_fallback"
    )
    assert owner_answer["mission_executor_fallback_action"]["stage_type"] == (
        "paper_mission_semantic_progress_executor"
    )
    assert owner_answer["mission_executor_fallback_action"]["default_action"] == (
        "materialize_submission_milestone_candidate"
    )
    assert owner_answer["carry_forward_risk_receipt_ref"].startswith(
        f"carry-forward-risk:paper-mission-owner-fallback:{study_id}:"
    )
    assert payload["route_back_budget"] == owner_answer["route_back_budget"]
    assert payload["semantic_progress_signature"] == (
        owner_answer["semantic_progress_signature"]
    )
    assert payload["mission_executor_fallback_action"] == (
        owner_answer["mission_executor_fallback_action"]
    )
    assert payload["carry_forward_risk_receipt_ref"] == (
        owner_answer["carry_forward_risk_receipt_ref"]
    )
    assert payload["next_owner_or_human_decision"]["route_back_budget"] == (
        owner_answer["route_back_budget"]
    )
    assert payload["next_owner_or_human_decision"][
        "mission_executor_fallback_action"
    ] == owner_answer["mission_executor_fallback_action"]
    assert payload["stage_terminal_decision"] == owner_answer["stage_terminal_decision"]
    assert payload["opl_route_command"] == owner_answer["opl_route_command"]
    assert payload["paper_mission_transaction"] == owner_answer["paper_mission_transaction"]
    assert payload["transaction_state"] == "route_back"
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "terminal_owner_gate_owner_answer"
    )
    assert authority_readback["owner_answer_contract"]["accepted_shapes"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "paper_facing_delta_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert authority_readback["owner_answer_contract"]["typed_blocker_ref"] == (
        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
        "sat-terminal.closeout.json#domain_blocker"
    )
    assert authority_readback["authority_boundary"]["can_claim_paper_progress"] is False
    assert authority_readback["authority_boundary"][
        "can_authorize_provider_admission"
    ] is False
    assert authority_readback["write_plan"]["written_files"] == []
    assert payload["paper_mission_transaction_readback"][
        "terminal_owner_gate_authority_readback"
    ] == authority_readback
    assert payload["paper_mission_transaction_readback"][
        "terminal_owner_gate_owner_answer_readback"
    ] == owner_answer
    assert payload["paper_mission_transaction_readback"]["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)
