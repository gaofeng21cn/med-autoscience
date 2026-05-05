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
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json"
    )
    assert result["dry_run"] is False
    assert result["repair_tasks"][0]["dispatch_status"] == "applied"
    assert consumer_path.is_file()
    assert repair_packet_path.is_file()
    assert dispatch_path.is_file()
    consumer = json.loads(consumer_path.read_text(encoding="utf-8"))
    repair_packet = json.loads(repair_packet_path.read_text(encoding="utf-8"))
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    assert consumer["written_files"] == [str(repair_packet_path), str(dispatch_path), str(consumer_path)]
    assert repair_packet["surface"] == "runtime_platform_repair_handoff_packet"
    assert repair_packet["action_type"] == "runtime_platform_repair"
    assert dispatch["surface"] == "default_executor_dispatch_request"
    assert dispatch["executor_kind"] == "codex_cli_default"
    assert dispatch["consumer_mutation_scope"] == "executor_dispatch_request_only"
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


def test_supervisor_consume_writes_request_handoff_for_publication_gate_and_ai_reviewer_actions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm",
                    "action_type": "publication_gate_specificity_required",
                    "authority": "observability_only",
                    "owner": "publication_gate",
                    "recommended_owner": "publication_gate",
                    "reason": "publication_gate_specificity_required",
                    "handoff_packet": {
                        "request_kind": "publication_gate_specificity_required",
                        "authority": "observability_only",
                        "request_owner": "publication_gate",
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dm",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "recommended_owner": "ai_reviewer",
                    "reason": "ai_reviewer_assessment_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "paper_package_mutation_allowed": False,
                        "quality_gate_relaxation_allowed": False,
                    },
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

    gate_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "publication_gate_specificity_required.json"
    )
    ai_packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "return_to_ai_reviewer_workflow.json"
    )
    assert result["repair_tasks"] == []
    assert result["request_tasks"][0]["action_type"] == "publication_gate_specificity_required"
    assert result["request_tasks"][1]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["request_tasks"][0]["request_owner"] == "publication_gate"
    assert result["request_tasks"][1]["request_owner"] == "ai_reviewer"
    assert result["request_tasks"][0]["expected_owner"] == "publication_gate"
    assert result["request_tasks"][1]["expected_owner"] == "ai_reviewer"
    assert result["request_tasks"][0]["owner_pickup"]["owner"] == "publication_gate"
    assert result["request_tasks"][1]["owner_pickup"]["owner"] == "ai_reviewer"
    assert result["request_tasks"][1]["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert result["ignored_actions"] == []
    assert gate_packet_path.is_file()
    assert ai_packet_path.is_file()
    gate_packet = json.loads(gate_packet_path.read_text(encoding="utf-8"))
    ai_packet = json.loads(ai_packet_path.read_text(encoding="utf-8"))
    assert gate_packet["authority"] == "observability_only"
    assert ai_packet["authority"] == "observability_only"
    assert gate_packet["request_owner"] == "publication_gate"
    assert ai_packet["request_owner"] == "ai_reviewer"
    assert gate_packet["next_executable_owner"] == "publication_gate"
    assert ai_packet["next_executable_owner"] == "ai_reviewer"
    assert gate_packet["owner_pickup"]["owner"] == "publication_gate"
    assert ai_packet["owner_pickup"]["owner"] == "ai_reviewer"
    assert ai_packet["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert gate_packet["supervisor_authority_boundary"] == "request_only"
    assert ai_packet["supervisor_authority_boundary"] == "request_only"
    assert "publication_eval" in ai_packet["consumer_does_not_mutate"]
    assert gate_packet["paper_package_mutation_allowed"] is False
    assert ai_packet["quality_gate_relaxation_allowed"] is False
    assert (profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json").is_file()


def test_supervisor_consume_mixed_queue_writes_default_executor_dispatches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_consumer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dpcc")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "action_queue": [
                _runtime_platform_repair_action(study_id, "quest-dpcc"),
                {
                    "study_id": study_id,
                    "quest_id": "quest-dpcc",
                    "action_type": "publication_gate_specificity_required",
                    "authority": "observability_only",
                    "owner": "publication_gate",
                    "reason": "publication_gate_specificity_required",
                    "handoff_packet": {
                        "request_kind": "publication_gate_specificity_required",
                        "authority": "observability_only",
                        "request_owner": "publication_gate",
                    },
                },
                {
                    "study_id": study_id,
                    "quest_id": "quest-dpcc",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_assessment_required",
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                    },
                },
            ],
        },
    )

    result = module.supervisor_consume(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatches = result["default_executor_dispatches"]
    assert result["default_executor_dispatch_count"] == 3
    assert [dispatch["executor_kind"] for dispatch in dispatches] == [
        "codex_cli_default",
        "codex_cli_default",
        "codex_cli_default",
    ]
    assert [dispatch["action_type"] for dispatch in dispatches] == [
        "runtime_platform_repair",
        "publication_gate_specificity_required",
        "return_to_ai_reviewer_workflow",
    ]
    assert dispatches[0]["next_executable_owner"] == "external_engineering_agent"
    assert dispatches[1]["next_executable_owner"] == "publication_gate"
    assert dispatches[2]["next_executable_owner"] == "ai_reviewer"
    assert dispatches[1]["default_model_policy"] == "inherit_current_codex_configuration"
    assert dispatches[2]["prompt_contract"]["forbidden_surfaces"] == module.FORBIDDEN_SURFACES
    assert "publication_eval/latest.json" in dispatches[2]["prompt_contract"]["required_output_surface"]
    assert dispatches[2]["prompt_contract"]["manual_study_patch_allowed"] is False

    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    written_dispatches = sorted(dispatch_dir.glob("*.json"))
    assert len(written_dispatches) == 3
    ai_dispatch = json.loads((dispatch_dir / "return_to_ai_reviewer_workflow.json").read_text(encoding="utf-8"))
    assert ai_dispatch["surface"] == "default_executor_dispatch_request"
    assert ai_dispatch["executor_kind"] == "codex_cli_default"
    assert ai_dispatch["dispatch_status"] == "ready"
    assert ai_dispatch["consumer_mutation_scope"] == "executor_dispatch_request_only"
    assert ai_dispatch["prompt_contract"]["quality_gate_relaxation_allowed"] is False
    assert ai_dispatch["prompt_contract"]["paper_package_mutation_allowed"] is False
    assert "current_package" in "\n".join(ai_dispatch["prompt_contract"]["forbidden_surfaces"])
    assert "Codex CLI" in ai_dispatch["executor_prompt"]

    assert (study_root / "artifacts" / "supervision" / "consumer" / "runtime_platform_repair.json").is_file()
    assert (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "publication_gate_specificity_required.json"
    ).is_file()
    assert (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "return_to_ai_reviewer_workflow.json"
    ).is_file()
    assert (profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json").is_file()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()
