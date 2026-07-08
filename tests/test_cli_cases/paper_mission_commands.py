from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.test_cli_cases.shared import write_profile
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403
from tests.test_cli_cases.paper_mission_command_cases.consume_submission_package import (
    test_paper_mission_consume_candidate_accepts_submission_package_manifest,
    test_paper_mission_consume_candidate_counts_accepted_package_delta_as_semantic_progress,
    test_paper_mission_consume_candidate_preserves_canonical_next_action_transaction,
    test_paper_mission_consume_candidate_refreshes_typed_blocker_package_artifacts,
    test_paper_mission_consume_candidate_auto_discovers_latest_package_manifest,
    test_paper_mission_consume_candidate_can_write_governed_consume_record,
    test_paper_mission_consume_candidate_reports_repeated_route_back_as_non_advancing,
    test_paper_mission_consume_candidate_uses_authority_consume_readback,
    test_paper_mission_consume_candidate_route_back_owner_comes_from_terminal_decision,
)
from tests.test_cli_cases.paper_mission_command_cases.consume_candidate_package_binding import (
    test_paper_mission_consume_candidate_rebinds_typed_blocker_package_refs,
    test_paper_mission_consume_candidate_materializes_reviewer_revision_route,
    test_paper_mission_consume_candidate_accepts_versioned_reviewer_revision_action,
)
from tests.test_cli_cases.paper_mission_command_cases.output_guards import (
    test_paper_mission_output_guards_allow_matching_yang_ops_roots,
    test_paper_mission_output_guards_reject_wrong_non_authority_bucket,
    test_paper_mission_drive_yang_output_root_uses_allowed_sibling_buckets,
    test_one_shot_migration_rejects_yang_authority_and_runtime_output_roots,
)
from tests.test_cli_cases.paper_mission_command_cases.one_shot_migration import (
    test_paper_mission_inspect_one_shot_migration_returns_default_readback,
    test_one_shot_migration_can_write_non_authority_candidate_package_and_consume_it,
)
from tests.test_cli_cases.paper_mission_command_cases.package_candidate import (
    test_paper_mission_package_candidate_materializes_route_back_executor_handoff,
    test_paper_mission_package_candidate_repackages_accepted_consumption_ledger_with_external_delta,
    test_paper_mission_package_candidate_preserves_display_pack_figure_digests,
    test_paper_mission_package_candidate_materializes_typed_blocker_owner_packet,
)
from tests.test_cli_cases.paper_mission_command_cases.drive_and_route_handoff import (
    test_domain_handler_export_default_route_handoff_carries_top_level_identity,
    test_paper_mission_drive_packages_consumes_and_returns_opl_route_handoff,
    test_paper_mission_drive_reuses_existing_reviewer_revision_handoff_without_one_shot_migration,
    test_direct_write_handoff_carries_latest_task_intake_scope_into_runtime_request,
    test_paper_mission_drive_packages_when_submission_minimal_owner_action_ready,
    test_paper_mission_drive_stops_when_route_back_checkpoint_owner_action_ready,
    test_paper_mission_drive_auto_consumes_route_back_checkpoint_before_direct_write_handoff,
    test_paper_mission_drive_does_not_stop_runtime_route_on_stale_owner_gate,
    test_paper_mission_drive_does_not_stop_domain_next_action_on_current_consumption,
)
from tests.test_cli_cases.paper_mission_command_cases.domain_handler_dispatch import (
    test_domain_entry_dispatch_handles_paper_mission_dry_run_without_authority_writes,
    test_domain_handler_export_defaults_to_paper_mission_start_or_resume,
    test_domain_handler_export_paper_mission_task_carries_opl_runtime_carrier_for_materialized_mission,
    test_domain_handler_export_default_task_dispatches_to_drive,
    test_domain_handler_dispatch_accepts_paper_mission_dry_run_without_authority_writes,
    test_domain_handler_dispatch_drives_default_paper_mission_without_authority_writes,
)
from tests.test_cli_cases.paper_mission_command_cases.materialized_readback import (
    test_paper_mission_inspect_materialized_readback_defaults_to_no_live_opl_probe,
    test_paper_mission_inspect_can_request_opl_transition_receipt_readback,
    test_transaction_readback_reattaches_runtime_receipt_after_owner_answer_route,
    test_authority_consumed_candidate_delta_suppresses_stale_terminal_owner_gate,
    test_consumption_ledger_candidate_delta_suppresses_older_terminal_owner_gate,
    test_consumption_ledger_inspect_routes_transaction_bound_route_back_evidence_to_owner_consumption,
    test_paper_mission_materialized_readback_keeps_governed_consumption_current_when_terminal_residue_exists,
)
from tests.test_cli_cases.paper_mission_command_cases.receipt_owner_consumption import (
    test_align_carrier_readback_projects_owner_consumed_status_for_same_attempt,
    test_align_carrier_readback_keeps_newer_unconsumed_attempt_pending,
    test_align_carrier_readback_projects_owner_consumed_current_attempt,
    test_materialize_receipt_owner_consumption_prefers_current_carrier_route_back_closeout,
    test_receipt_owner_consumption_classifies_dm002_typed_blocker_without_authority_write,
    test_receipt_owner_consumption_prefers_current_direct_stage_carrier_over_legacy,
    test_receipt_owner_consumption_prefers_unconsumed_terminal_over_consumed_current,
    test_receipt_owner_consumption_keeps_newer_consumed_current_over_older_terminal,
    test_receipt_owner_consumption_prefers_stage_decision_terminal_over_touched_consumed_current,
    test_receipt_owner_consumption_prefers_newer_unconsumed_terminal_over_unconsumed_current,
    test_receipt_owner_consumption_prefers_terminal_receipt_over_running_projection,
)
from tests.test_cli_cases.paper_mission_command_cases.typed_blocker_resolution import (
    test_typed_blocker_resolution_accepts_successor_owner_action_envelope,
    test_typed_blocker_resolution_accepts_route_back_owner_action_without_receipt,
    test_typed_blocker_resolution_reports_missing_owner_apply_surface,
    test_typed_blocker_resolution_hydrates_existing_audit_current_package,
    test_typed_blocker_resolution_fails_closed_without_consumed_receipt,
    test_typed_blocker_resolution_route_redesign_writes_non_authority_packet,
    test_typed_blocker_resolution_owner_decision_writes_non_authority_packet,
    test_typed_blocker_resolution_human_gate_writes_non_authority_packet,
    test_typed_blocker_resolution_packet_projects_canonical_next_action,
    test_paper_mission_inspect_prefers_domain_transition_ai_reviewer_over_old_resolution,
    test_paper_mission_inspect_prefers_domain_transition_write_attempt_over_old_resolution,
    test_typed_blocker_resolution_rejects_forbidden_output_root,
)
from tests.test_cli_cases.paper_mission_command_cases.submission_milestone_candidate_package import (
    test_paper_mission_package_candidate_writes_non_authority_owner_decision_package,
)
from tests.test_cli_cases.paper_mission_commands_cases.materialized_terminal_closeout import (
    test_paper_mission_materialized_readback_consumes_matching_opl_terminal_closeout,
)
from tests.test_cli_cases.paper_mission_commands_cases.route_back_budget import (
    test_route_back_budget_counts_synonymous_followthrough_route_back,
)
from tests.test_cli_cases.paper_mission_commands_cases.stage_closure_terminalizer import (
    test_paper_mission_terminalize_stage_materializes_non_authority_decision,
    test_paper_mission_terminalize_stage_defaults_to_workspace_ops_ledger,
    test_stage_closure_terminalizer_reads_nested_closeout_telemetry,
    test_stage_closure_terminalizer_does_not_treat_accepted_status_as_blocker,
    test_stage_closure_terminalizer_does_not_treat_paper_facing_delta_acceptance_as_blocker,
    test_stage_closure_terminalizer_reterminalizes_legacy_accepted_unknown_blocker,
    test_stage_closure_terminalizer_reads_workspace_consumption_closeout_accounting,
)


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
