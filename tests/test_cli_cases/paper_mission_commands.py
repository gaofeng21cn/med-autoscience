from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from .shared import write_profile
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.consume_submission_package import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.consume_candidate_package_binding import *  # noqa: F401,F403
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
from tests.test_cli_cases.paper_mission_commands_cases.stage_closure_terminalizer import *  # noqa: F401,F403


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
