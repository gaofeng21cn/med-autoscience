from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _runtime_platform_repair_action(study_id: str, quest_id: str) -> dict[str, object]:
    return {
        "study_id": study_id,
        "action_type": "runtime_platform_repair",
        "authority": "external_supervisor",
        "reason": "runtime_recovery_retry_budget_exhausted",
        "action_id": f"supervisor-action::{study_id}::runtime_platform_repair::runtime_recovery_retry_budget_exhausted",
        "handoff_packet": {
            "packet_type": "external_supervisor_handoff",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "runtime_platform_repair",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "authority": "external_supervisor",
            "recommended_owner": "external_engineering_agent",
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "allowed_write_surfaces": [
                "artifacts/supervision/**",
                "artifacts/autonomy/repair_lifecycle/latest.json",
                "artifacts/autonomy/repair_actions/latest.json",
            ],
            "forbidden_actions": [
                "paper_package_mutation",
                "manual_study_patch",
                "quality_gate_relaxation",
                "medical_claim_authoring",
            ],
        },
    }


def test_supervisor_consume_dry_run_projects_runtime_platform_repair_without_writes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [_runtime_platform_repair_action(study_id, "quest-nf")],
        },
    )

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    task = result["repair_tasks"][0]
    assert result["surface"] == "runtime_supervisor_consumer"
    assert result["dry_run"] is True
    assert result["effective_mode"] == "developer_apply_safe"
    assert result["github_gate"]["allowed"] is True
    assert task["dispatch_status"] == "dry_run"
    assert task["action_type"] == "runtime_platform_repair"
    assert task["branch_name"] == "codex/mas-supervisor-queue-consumer"
    assert task["owned_files"] == [
        "src/med_autoscience/cli.py",
        "src/med_autoscience/cli_parts/parser.py",
        "src/med_autoscience/cli_public_surface.py",
        "src/med_autoscience/controllers/runtime_supervisor_consumer.py",
        "tests/test_cli.py",
        "tests/test_cli_cases/runtime_supervisor_consume_command.py",
        "tests/test_runtime_supervisor_consumer.py",
    ]
    assert task["forbidden_surfaces"] == [
        "paper/**",
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
    ]
    assert not (profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json").exists()
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "runtime_platform_repair.json").exists()


def test_supervisor_consume_apply_writes_only_consumer_handoff_surfaces(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [_runtime_platform_repair_action(study_id, "quest-nf")],
        },
    )

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    consumer_path = profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json"
    repair_packet_path = study_root / "artifacts" / "supervision" / "consumer" / "runtime_platform_repair.json"
    assert result["dry_run"] is False
    assert result["repair_tasks"][0]["dispatch_status"] == "applied"
    assert consumer_path.is_file()
    assert repair_packet_path.is_file()
    consumer = json.loads(consumer_path.read_text(encoding="utf-8"))
    repair_packet = json.loads(repair_packet_path.read_text(encoding="utf-8"))
    assert consumer["written_files"] == [str(repair_packet_path), str(consumer_path)]
    assert repair_packet["surface"] == "runtime_platform_repair_handoff_packet"
    assert repair_packet["action_type"] == "runtime_platform_repair"
    assert repair_packet["paper_package_mutation_allowed"] is False
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()


def test_supervisor_consume_blocks_apply_for_non_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "someone-else")
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [_runtime_platform_repair_action(study_id, "quest-nf")],
        },
    )

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["effective_mode"] == "external_observe"
    assert result["apply_allowed"] is False
    assert result["repair_tasks"][0]["dispatch_status"] == "blocked"
    assert result["repair_tasks"][0]["blocked_reason"] == "github_user_not_authorized_for_developer_supervisor_mode"
    assert not (profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json").exists()
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "runtime_platform_repair.json").exists()


def test_supervisor_consume_blocks_apply_for_non_developer_apply_safe_mode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [_runtime_platform_repair_action(study_id, "quest-nf")],
        },
    )

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="external_observe",
        apply=True,
    )

    assert result["effective_mode"] == "external_observe"
    assert result["apply_allowed"] is False
    assert result["repair_tasks"][0]["dispatch_status"] == "blocked"
    assert result["repair_tasks"][0]["blocked_reason"] == "developer_apply_safe_required"
    assert not (profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json").exists()
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "runtime_platform_repair.json").exists()


def test_supervisor_consume_ignores_non_runtime_platform_repair_actions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "reason": "ai_reviewer_assessment_required",
                }
            ],
        },
    )

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["repair_tasks"] == []
    assert result["ignored_actions"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert not (profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json").exists()
