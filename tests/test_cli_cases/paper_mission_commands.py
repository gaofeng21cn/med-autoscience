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
