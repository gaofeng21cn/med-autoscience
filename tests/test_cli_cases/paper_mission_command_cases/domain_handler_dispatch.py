from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.test_cli_cases.paper_mission_command_helpers import (
    DM_CANARY_FIXTURE_ROOT,
    FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
    _assert_forbidden_authority_untouched,
    _paper_mission_forbidden_write_guard,
    _paper_mission_transaction_payload,
    _write_candidate_manifest,
    _write_matching_domain_gate_closeout,
    _write_paper_source_fixture,
    _write_profile_with_study,
    _write_submission_milestone_package,
)


@pytest.fixture(autouse=True)
def _disable_default_opl_live_probe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_BIN", str(tmp_path / "missing-opl"))


def test_domain_entry_dispatch_handles_paper_mission_dry_run_without_authority_writes(
    tmp_path: Path,
) -> None:
    domain_entry = importlib.import_module("med_autoscience.domain_entry")
    profile_path = _write_profile_with_study(tmp_path)

    result = domain_entry.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "paper-mission",
            "paper_mission_command": "resume",
            "profile_ref": str(profile_path),
            "study_id": "001-paper",
            "mission_id": "mission-001",
            "dry_run": True,
        }
    )

    assert result["command"] == "paper-mission"
    assert result["paper_mission_command"] == "resume"
    assert result["action_intent"] == "paper_mission/start_or_resume"
    assert result["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path)


def test_domain_handler_export_defaults_to_paper_mission_start_or_resume(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)

    exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["dispatch"]["default_action_intent"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["default_queue_source"] == "/paper_mission_default_tasks"
    assert payload["dispatch"]["legacy_queue_source"] == "/pending_family_tasks"
    assert "paper_mission/start_or_resume" in payload["dispatch"]["allowed_task_kinds"]
    assert payload["pending_family_tasks_policy"] == {
        "default_paper_mission_queue_source": "/paper_mission_default_tasks",
        "legacy_mixed_queue_source": "/pending_family_tasks",
        "pending_family_tasks_role": "mixed_explicit_owner_handoff_and_migration_compatibility_queue",
        "legacy_dispatch_diagnostics_source": "/retired_default_paper_dispatch_diagnostics",
        "ordinary_consumer_forbidden_task_kinds": [
            "domain_owner/default-executor-dispatch",
            "domain_owner/owner-callable-adapter",
            "domain_route/reconcile-apply",
        ],
        "legacy_task_kinds_must_not_hydrate_from_pending_family_tasks": True,
        "ordinary_consumer_rule": (
            "OPL consumers that want the MAS paper loop must hydrate only "
            "/paper_mission_default_tasks unless an explicit owner handoff task "
            "was selected by a MAS StageTerminalDecision or authority receipt."
        ),
        "non_default_task_policy": {
            "default_paper_mission_entry": False,
            "paper_mission_default_role": "diagnostic_or_explicit_owner_handoff",
            "can_select_next_paper_stage": False,
            "can_authorize_provider_admission": False,
            "counts_as_paper_progress": False,
        },
    }
    paper_mission_tasks = payload["paper_mission_default_tasks"]
    assert paper_mission_tasks
    assert paper_mission_tasks[0]["default_paper_mission_entry"] is True
    assert paper_mission_tasks[0]["payload"]["paper_mission_command"] == "drive"
    assert paper_mission_tasks[0]["payload"]["dry_run"] is False
    assert paper_mission_tasks[0]["payload"]["submit_opl_runtime"] is False
    assert paper_mission_tasks[0]["payload"]["run_id"].startswith(
        "domain-handler-default-drive-"
    )
    assert paper_mission_tasks[0]["payload"]["dispatch_execution_boundary"] == {
        "mode": "non_authority_candidate_package_and_consumption_ledger",
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "runtime_queue_submission_requires_explicit_submit_opl_runtime": True,
    }
    assert paper_mission_tasks[0]["payload"]["diagnostic_readback_command"] == "start"
    assert paper_mission_tasks[0]["payload"]["diagnostic_readback_dry_run"] is True
    assert paper_mission_tasks[0]["payload"]["paper_mission"]["dry_run"] is True
    assert not [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
    ]
    for task in payload["pending_family_tasks"]:
        assert task["default_paper_mission_entry"] is False
        assert task["paper_mission_default_role"] == "diagnostic_or_explicit_owner_handoff"
        assert task["can_select_next_paper_stage"] is False
        assert task["can_authorize_provider_admission"] is False
        assert task["counts_as_paper_progress"] is False


def test_domain_handler_export_paper_mission_task_carries_opl_runtime_carrier_for_materialized_mission(
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
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    paper_mission_task = next(
        task
        for task in payload["paper_mission_default_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
        and task["study_id"] == study_id
    )
    task_payload = paper_mission_task["payload"]
    carrier = task_payload["opl_runtime_carrier"]
    assert carrier["surface_kind"] == "mas_domain_progress_transition_request"
    assert task_payload["opl_domain_progress_transition_request"] == carrier
    assert task_payload["dispatch_authority"] == "paper_mission_transaction"
    assert task_payload["action_type"] == carrier["action_type"]
    assert task_payload["work_unit_id"] == carrier["work_unit_id"]
    assert task_payload["work_unit_fingerprint"] == carrier["work_unit_fingerprint"]
    assert task_payload["route_identity_key"] == carrier["route_identity_key"]
    assert task_payload["attempt_idempotency_key"] == carrier["attempt_idempotency_key"]
    assert task_payload["provider_completion_is_domain_completion"] is False
    assert task_payload["stage_transition_authority_boundary"] == carrier[
        "authority_boundary"
    ]
    assert task_payload["stage_packet_ref"] == carrier["stage_run_ref"]
    assert carrier["stage_run_ref"] in task_payload["stage_packet_refs"]
    assert task_payload["paper_mission"]["materialized_mission_ref"].endswith(
        "/paper_mission_run.json"
    )
    assert task_payload["paper_mission"]["candidate_manifest_ref"].endswith(
        "/candidate_manifest.json"
    )
    assert task_payload["paper_mission"]["opl_runtime_carrier"] == carrier


def test_domain_handler_export_default_task_dispatches_to_drive(
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
        / "20260624Texportdispatch"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::exportdispatch"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Exported default task must dispatch to paper mission drive.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
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
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-exportdispatch",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )

    export_exit_code = cli.main(
        ["domain-handler", "export", "--profile", str(profile_path), "--format", "json"]
    )
    export_payload = json.loads(capsys.readouterr().out)
    assert export_exit_code == 0
    exported_task = next(
        task
        for task in export_payload["paper_mission_default_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
        and task["study_id"] == study_id
    )
    task_path = tmp_path / "exported-paper-mission-task.json"
    task_path.write_text(json.dumps(exported_task), encoding="utf-8")

    dispatch_exit_code = cli.main(
        ["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]
    )
    dispatch_payload = json.loads(capsys.readouterr().out)

    assert dispatch_exit_code == 0
    assert dispatch_payload["dispatch"]["execution_policy"] == (
        "paper_mission_drive_non_authority_candidate_and_ledger"
    )
    result = dispatch_payload["dispatch"]["result"]
    assert result["surface_kind"] == "paper_mission_drive_readback"
    assert result["paper_mission_command"] == "drive"
    assert result["output_manifest"]["writes_authority"] is False
    assert result["output_manifest"]["writes_runtime"] is False
    assert result["output_manifest"]["writes_yang_authority"] is False
    assert result["candidate_package_readback"]["output_manifest"][
        "package_manifest_ref"
    ].endswith(f"/{study_id}/package_manifest.json")
    assert result["consume_readback"]["consume_output_manifest"][
        "opl_route_handoff_ref"
    ].endswith(f"/{study_id}/opl_route_handoff.json")
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_domain_handler_dispatch_accepts_paper_mission_dry_run_without_authority_writes(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    task_path = tmp_path / "paper-mission-task.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "paper-mission-001",
                "domain_id": "medautoscience",
                "task_kind": "paper_mission/start_or_resume",
                "action_intent": "paper_mission/start_or_resume",
                "payload": {
                    "profile": str(profile_path),
                    "study_id": "001-paper",
                    "paper_mission_command": "start",
                    "objective": "gate clearing",
                    "dry_run": True,
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        ["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["task_kind"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["action_intent"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["execution_policy"] == "paper_mission_no_write_dry_run"
    assert payload["dispatch"]["result"]["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path)


def test_domain_handler_dispatch_drives_default_paper_mission_without_authority_writes(
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
        / "20260624Tdispatch"
        / study_id
    )
    mission_root.mkdir(parents=True)
    mission_id = f"paper-mission::{study_id}::gate-clearing::dispatch"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    mission_payload = {
        "schema_version": "paper-mission-run.v1",
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": "Dispatch default paper mission into submission milestone packaging.",
        "mission_state": "route_back",
        "artifact_delta_ledger": [],
        "source_refs": [],
        "consume_result": {"status": "route_back"},
        "one_shot_migration_readback": {
            "current_mission": {
                "objective_kind": "gate_clearing_claim_evidence_repair",
                "legacy_blocker_is_default_execution_state": False,
            },
            "required_output": {
                "next_owner": "mission_executor",
                "kind": "owner_decision_packet_or_consumable_artifact_delta",
            },
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": transaction["opl_route_command"],
            "consume_candidate_status": "route_back",
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
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(mission_payload),
        encoding="utf-8",
    )
    (mission_root / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "pmc-dm002-dispatch",
                "mission_id": mission_id,
                "study_id": study_id,
                "next_owner": "mission_executor",
                "source_readiness_refs": ["source-readiness:dm002"],
            }
        ),
        encoding="utf-8",
    )
    task_path = tmp_path / "paper-mission-default-task.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "paper-mission-start-or-resume::dm002",
                "domain_id": "medautoscience",
                "task_kind": "paper_mission/start_or_resume",
                "action_intent": "paper_mission/start_or_resume",
                "payload": {
                    "profile": str(profile_path),
                    "study_id": study_id,
                    "paper_mission_command": "start",
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        ["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_intent"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["execution_policy"] == (
        "paper_mission_drive_non_authority_candidate_and_ledger"
    )
    result = payload["dispatch"]["result"]
    assert result["surface_kind"] == "paper_mission_drive_readback"
    assert result["paper_mission_command"] == "drive"
    assert result["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert result["stage_terminal_decision"]["decision_kind"] == "continue_same_stage"
    assert result["opl_route_command"]["command_kind"] == "resume_stage"
    assert result["drive_result"]["status"] != "stage_closure_decision_missing"
    assert result["stage_closure_outcome"] == "next_stage_transition"
    assert result["output_manifest"]["stage_closure"]["writes_authority"] is False
    assert result["drive_result"]["opl_runtime_submission_status"] in {
        "not_requested",
        "not_configured",
        "submitted",
    }
    assert result["opl_runtime_submission"]["status"] in {
        "not_requested",
        "not_configured",
        "submitted",
    }
    assert result["mutation_policy"]["writes_authority"] is False
    assert result["mutation_policy"]["writes_runtime"] in {False, True}
    assert result["mutation_policy"]["writes_yang_authority"] is False
    package_manifest = result["candidate_package_readback"]["output_manifest"]
    consume_manifest = result["consume_readback"]["consume_output_manifest"]
    assert package_manifest["mode"] == "non_authority_candidate_package"
    assert consume_manifest["mode"] == "governed_consume_record"
    assert Path(package_manifest["package_manifest_ref"]).exists()
    assert Path(consume_manifest["opl_route_handoff_ref"]).exists()
    assert str(workspace_root / "ops" / "medautoscience") in result["output_root"]
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)
