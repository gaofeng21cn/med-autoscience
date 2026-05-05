from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _dispatch(
    *,
    study_id: str,
    action_type: str,
    owner: str,
    required_output_surface: str,
) -> dict[str, object]:
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "executor_kind": "codex_cli_default",
        "executor_name": "Codex CLI",
        "executor_mode": "autonomous_agent_loop",
        "chat_completion_only_executor_forbidden": True,
        "dispatch_status": "ready",
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "action_type": action_type,
        "action_id": f"dispatch::{study_id}::{action_type}",
        "next_executable_owner": owner,
        "required_output_surface": required_output_surface,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "action_type": action_type,
            "next_executable_owner": owner,
            "required_output_surface": required_output_surface,
            "forbidden_surfaces": [
                "paper/**",
                "manuscript/**",
                "current_package/**",
                "paper/current_package/**",
                "manuscript/current_package/**",
                "src/med_autoscience/platform/**",
            ],
            "allowed_write_surfaces": ["artifacts/supervision/**"],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }


def test_execute_dispatch_blocks_ai_reviewer_without_owner_callable_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(
        dispatch_path,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "owner_callable_surface_missing"
    assert execution["next_owner"] == "repo_platform"
    assert execution["required_repo_surface"] == "structured_ai_reviewer_default_executor_workflow"
    latest = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_execution"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert latest["blocked_count"] == 1
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()


def test_execute_dispatch_runs_publication_gate_owner_surface(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_gate_specificity_required.json"
    )
    _write_json(
        dispatch_path,
        _dispatch(
            study_id=study_id,
            action_type="publication_gate_specificity_required",
            owner="publication_gate",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_build_gate_state(quest_root_arg) -> dict[str, object]:
        called["quest_root"] = quest_root_arg
        return {"quest_root": quest_root_arg}

    def fake_build_gate_report(state) -> dict[str, object]:
        called["state"] = state
        return {
            "generated_at": "2026-05-05T00:00:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        }

    def fake_write_gate_files(quest_root_arg, report) -> tuple[Path, Path]:
        called["write_quest_root"] = quest_root_arg
        called["report"] = report
        json_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        md_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.md"
        _write_json(json_path, report)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text("# gate\n", encoding="utf-8")
        return json_path, md_path

    def fake_materialize_publication_eval_latest(**kwargs) -> dict[str, str]:
        called["materialize_kwargs"] = kwargs
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "surface": "publication_eval",
                "recommended_actions": [
                    {
                        "action_type": "return_to_controller",
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "primary_claim",
                                "source_path": "paper/claim_evidence_map.json",
                                "blocking_reason": "claim_evidence_consistency_failed",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": "paper/figures/figure_catalog.json",
                                "blocking_reason": "figure_semantics_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "table",
                                "target_id": "submission_manifest",
                                "source_path": "paper/submission_minimal/submission_manifest.json",
                                "blocking_reason": "submission_hardening_incomplete",
                            },
                            {
                                "target_kind": "metric",
                                "target_id": "main_result_metrics",
                                "source_path": "artifacts/results/main_result.json",
                                "blocking_reason": "derived_analysis_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "source_path",
                                "target_id": "gate_report",
                                "source_path": "artifacts/reports/publishability_gate/latest.json",
                                "blocking_reason": "publication_gate_blocked",
                            },
                        ],
                    }
                ],
            },
        )
        return {"artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")}

    monkeypatch.setattr(module.publication_gate, "build_gate_state", fake_build_gate_state)
    monkeypatch.setattr(module.publication_gate, "build_gate_report", fake_build_gate_report)
    monkeypatch.setattr(module.publication_gate, "write_gate_files", fake_write_gate_files)
    monkeypatch.setattr(module.publication_gate, "_materialize_publication_eval_latest", fake_materialize_publication_eval_latest)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_callable_surface"] == "publication_gate.write_gate_files+_materialize_publication_eval_latest"
    assert called["quest_root"] == quest_root
    assert called["write_quest_root"] == quest_root
    assert called["materialize_kwargs"]["report"]["latest_gate_path"].endswith("latest.json")
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").is_file()


def test_execute_dispatch_rejects_incomplete_forbidden_surface_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch = _dispatch(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="external_engineering_agent",
        required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
    )
    dispatch["prompt_contract"]["forbidden_surfaces"] = ["paper/**"]
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json",
        dispatch,
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    assert result["executions"][0]["blocked_reason"] == "forbidden_surfaces_incomplete"


def test_runtime_platform_repair_dispatch_uses_non_persistent_scan(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    scan_module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "generated_at": "2026-05-05T00:00:00+00:00",
            "studies": [
                {"study_id": "001-dm-cvd-mortality-risk"},
                {"study_id": study_id},
            ],
        },
    )
    before = latest_path.read_text(encoding="utf-8")
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json",
        _dispatch(
            study_id=study_id,
            action_type="runtime_platform_repair",
            owner="external_engineering_agent",
            required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
        ),
    )
    called: dict[str, object] = {}

    def fake_supervisor_scan(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        assert kwargs["persist_surfaces"] is False
        return {
            "surface": "portable_runtime_supervisor_scan",
            "studies": [
                {
                    "study_id": study_id,
                    "runtime_platform_repair_apply": {
                        "dispatch_status": "applied",
                        "reason": "stale_specificity_terminal_gate_cleared",
                    },
                }
            ],
        }

    monkeypatch.setattr(scan_module, "supervisor_scan", fake_supervisor_scan)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("runtime_platform_repair",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert called["study_ids"] == (study_id,)
    assert called["apply_runtime_platform_repair"] is True
    assert latest_path.read_text(encoding="utf-8") == before
