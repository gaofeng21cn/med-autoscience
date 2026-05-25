from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_sidecar_dispatch_routes_embedded_ai_reviewer_callable_inside_mas_owner(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 1,
            "blocked_count": 0,
        }

    monkeypatch.setattr(
        adapter.paper_repair_executor.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-callable",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-ai-reviewer",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:unit-ai-reviewer",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["execution_status"] == "executed"
    assert paper_receipt["owner_callable_surface"] == (
        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    )
    assert len(calls) == 1
    assert calls[0]["profile"].name == "nfpitnet"
    assert calls[0]["study_ids"] == ("001-risk",)
    assert calls[0]["action_types"] == ("return_to_ai_reviewer_workflow",)
    assert calls[0]["mode"] == "developer_apply_safe"
    assert calls[0]["apply"] is True
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_sidecar_dispatch_preserves_embedded_ai_reviewer_callable_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    def fake_dispatch_domain_owner_actions(**_kwargs) -> dict[str, object]:
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 0,
            "blocked_count": 1,
            "repeat_suppressed_count": 0,
            "executions": [
                {
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_request_missing",
                    "owner_callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                }
            ],
        }

    monkeypatch.setattr(
        adapter.paper_repair_executor.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-callable-blocked",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-ai-reviewer-blocked",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:unit-ai-reviewer-blocked",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["accepted"] is False
    assert paper_receipt["execution_status"] == "blocked"
    assert paper_receipt["typed_blocker"] == "ai_reviewer_request_missing"


def test_sidecar_dispatch_accepts_ai_reviewer_currentness_blocker_as_stable_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)

    def fake_dispatch_domain_owner_actions(**_kwargs) -> dict[str, object]:
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 0,
            "blocked_count": 1,
            "repeat_suppressed_count": 0,
            "executions": [
                {
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "owner_callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                }
            ],
        }

    monkeypatch.setattr(
        adapter.paper_repair_executor.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-current-manuscript-stale",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "repair_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:current-manuscript-stale-record",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    assert payload["stable_typed_blocker"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert "reason" not in payload
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["accepted"] is False
    assert paper_receipt["execution_status"] == "blocked"
    assert paper_receipt["typed_blocker"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert paper_receipt["owner_receipt"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert payload["receipt_ref"].startswith("artifacts/runtime/opl_family_sidecar/dispatch_receipts/")
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()
