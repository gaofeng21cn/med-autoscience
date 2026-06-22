from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from .shared import write_profile


FORBIDDEN_AUTHORITY_RELATIVE_PATHS = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "paper/current_package",
)
DM_CANARY_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "paper_mission_dm_canary"
)


def _write_profile_with_study(tmp_path: Path, *, study_id: str = "001-paper") -> Path:
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=workspace_root)
    (workspace_root / "studies" / study_id).mkdir(parents=True)
    return profile_path


def _assert_forbidden_authority_untouched(tmp_path: Path, *, study_id: str = "001-paper") -> None:
    study_root = tmp_path / "workspace" / "studies" / study_id
    for relative_path in FORBIDDEN_AUTHORITY_RELATIVE_PATHS:
        assert not (study_root / relative_path).exists()


def _write_candidate_manifest(
    tmp_path: Path,
    *,
    study_id: str = "001-paper",
    requested_outcome: str = "accepted_candidate",
) -> Path:
    candidate_path = tmp_path / "candidate.json"
    candidate = {
        "candidate_id": "pmc-001",
        "mission_id": f"paper-mission::{study_id}::gate-clearing::manual",
        "study_id": study_id,
        "requested_outcome": requested_outcome,
        "candidate_manifest_ref": "paper-mission/pmc-001.json",
        "candidate_artifact_refs": ["paper-mission/patch-plan.md"],
        "source_readiness_refs": ["source-readiness:001"],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "mas_authority_kernel",
        "resume_condition": "MAS consumes or routes back the mission candidate",
    }
    if requested_outcome == "typed_blocker_required":
        candidate["typed_blocker_request"] = {
            "blocker_id": "source_readiness_missing",
            "blocker_ref": "typed-blocker-request:pmc-001",
        }
    if requested_outcome == "human_gate_required":
        candidate["human_gate_request"] = {
            "decision_packet_ref": "human-gate-request:pmc-001",
        }
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return candidate_path


def test_paper_mission_help_exposes_default_commands(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["paper-mission", "--help"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    for command in ("inspect", "start", "resume", "consume-candidate"):
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
    assert "publication_eval/latest.json" in payload["forbidden_authority_writes"]
    _assert_forbidden_authority_untouched(tmp_path)


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

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["dispatch"]["default_action_intent"] == "paper_mission/start_or_resume"
    assert "paper_mission/start_or_resume" in payload["dispatch"]["allowed_task_kinds"]
    paper_mission_tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_mission/start_or_resume"
    ]
    assert paper_mission_tasks
    assert paper_mission_tasks[0]["default_paper_mission_entry"] is True
    assert paper_mission_tasks[0]["payload"]["paper_mission"]["dry_run"] is True
    for task in payload["pending_family_tasks"]:
        if task["task_kind"] == "domain_owner/default-executor-dispatch":
            assert task["migration_diagnostic_only"] is True
            assert task["default_paper_mission_entry"] is False


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

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["task_kind"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["action_intent"] == "paper_mission/start_or_resume"
    assert payload["dispatch"]["execution_policy"] == "paper_mission_no_write_dry_run"
    assert payload["dispatch"]["result"]["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_consume_candidate_uses_authority_consume_readback(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    candidate_path = _write_candidate_manifest(tmp_path)

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
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
    assert payload["paper_mission_command"] == "consume-candidate"
    assert payload["action_intent"] == "paper_mission/consume_candidate"
    assert payload["authority_consume_readback"]["status"] == "accepted_candidate"
    assert payload["authority_consume_readback"]["consume_result"]["status"] == "accepted"
    assert (
        payload["paper_mission_run_candidate"]["consume_result"]
        == payload["authority_consume_readback"]["consume_result"]
    )
    assert payload["paper_mission_run_candidate"]["mission_state"] == "consumed"
    assert payload["paper_mission_run_candidate"]["artifact_delta_ledger"][0]["status"] == (
        "candidate_consumed"
    )
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["authority_consume_readback"]["write_plan"]["written_files"] == []
    _assert_forbidden_authority_untouched(tmp_path)


@pytest.mark.parametrize(
    ("requested_outcome", "expected_consume_status", "expected_mission_state"),
    (
        ("route_back", "route_back", "route_back"),
        ("typed_blocker_required", "typed_blocker", "stable_blocker"),
        ("human_gate_required", "human_gate", "waiting_human_decision"),
    ),
)
def test_paper_mission_consume_candidate_maps_non_accept_outcomes(
    tmp_path: Path,
    capsys,
    requested_outcome: str,
    expected_consume_status: str,
    expected_mission_state: str,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(tmp_path)
    candidate_path = _write_candidate_manifest(
        tmp_path,
        requested_outcome=requested_outcome,
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(candidate_path),
            "--dry-run",
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
    assert payload["authority_consume_readback"]["consume_result"]["status"] == (
        expected_consume_status
    )
    assert payload["paper_mission_run_candidate"]["consume_result"]["status"] == (
        expected_consume_status
    )
    assert payload["paper_mission_run_candidate"]["mission_state"] == expected_mission_state
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["authority_consume_readback"]["write_plan"]["written_files"] == []
    _assert_forbidden_authority_untouched(tmp_path)


def test_paper_mission_inspect_one_shot_migration_returns_default_readback(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(
        tmp_path,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--one-shot-migration",
            "--study-progress-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dm003_progress.json"),
            "--domain-health-diagnostic-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dhd_dry_run.json"),
            "--profile",
            str(profile_path),
            "--study-id",
            "003-dpcc-primary-care-phenotype-treatment-gap",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_one_shot_migration_cli_readback"
    assert payload["contract_validation"]["status"] == "validated"
    assert payload["default_readback"]["current_mission"]["objective_kind"] == (
        "medical_prose_write_repair_publication_gate_replay"
    )
    assert (
        payload["default_readback"]["current_mission"][
            "legacy_blocker_is_default_execution_state"
        ]
        is False
    )
    assert payload["default_readback"]["next_owner"] == "one-person-lab"
    assert payload["consume_candidate_status"] == "typed_blocker"
    assert payload["legacy_truth_import_pack"]["legacy_constraints"][
        "old_blocker_is_default_execution_state"
    ] is False
    assert payload["output_manifest"]["written_files"] == []
    assert payload["mutation_policy"]["writes_authority"] is False
    assert payload["mutation_policy"]["writes_yang_authority"] is False
    assert payload["mutation_policy"]["writes_yang_ops_candidate_package"] is False
    _assert_forbidden_authority_untouched(
        tmp_path,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
    )


def test_one_shot_migration_can_write_non_authority_candidate_package_and_consume_it(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = _write_profile_with_study(
        tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
    )
    output_root = tmp_path / "candidate-packages"

    exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--one-shot-migration",
            "--study-progress-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dm002_progress.json"),
            "--domain-health-diagnostic-payload",
            str(DM_CANARY_FIXTURE_ROOT / "dhd_dry_run.json"),
            "--output-root",
            str(output_root),
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--format",
            "json",
        ]
    )
    first = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    written_files = first["output_manifest"]["written_files"]
    assert len(written_files) == 4
    assert first["output_manifest"]["writes_authority"] is False
    assert first["output_manifest"]["writes_yang_authority"] is False
    assert first["output_manifest"]["writes_yang_ops_candidate_package"] is False
    candidate_manifest_ref = first["output_manifest"]["candidate_manifest_ref"]
    assert Path(candidate_manifest_ref).exists()
    _assert_forbidden_authority_untouched(
        tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            candidate_manifest_ref,
            "--dry-run",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--format",
            "json",
        ]
    )
    second = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert second["authority_consume_readback"]["status"] == "accepted_candidate"
    assert second["authority_consume_readback"]["consume_result"]["status"] == "accepted"
    assert second["authority_consume_readback"]["write_plan"]["written_files"] == []
    assert second["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(
        tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
    )


def test_one_shot_migration_allows_only_yang_ops_candidate_output_root() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    commands._assert_safe_candidate_output_root(
        Path(
            "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
            "ops/medautoscience/paper_mission_one_shot_migration/20260623"
        )
    )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "studies/002-dm-china-us-mortality-attribution/artifacts/publication_eval"
            )
        )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "runtime/quests/002-dm-china-us-mortality-attribution/provider_attempt"
            )
        )
