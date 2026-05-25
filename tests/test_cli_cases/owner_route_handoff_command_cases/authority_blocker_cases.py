from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_records_quality_repair_authority_gate_as_stable_typed_blocker(
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

    def blocked_quality_repair_batch(**_kwargs) -> dict[str, object]:
        raise PermissionError(
            "authority route blocked paper_write: dispatch_gate_blocked, "
            "opl_current_control_state.handoff_required, "
            "publication_supervisor_state.bundle_tasks_downstream_only"
        )

    monkeypatch.setattr(
        adapter.paper_repair_executor.quality_repair_batch,
        "run_quality_repair_batch",
        blocked_quality_repair_batch,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-quality-batch-authority-blocked",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-quality-batch-authority-blocked",
                    "work_unit_type": "text_repair",
                    "owner": "quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "source_fingerprint": "sha256:unit-quality-batch-authority-blocked",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "publication_eval/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    assert payload["stable_typed_blocker"] == "authority_route_blocked"
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["accepted"] is False
    assert paper_receipt["execution_status"] == "blocked"
    assert paper_receipt["typed_blocker"] == "authority_route_blocked"
    assert paper_receipt["owner_receipt"]["blocked_reason"] == "authority_route_blocked"
    evidence = paper_receipt["repair_execution_evidence"]
    assert "publication_supervisor_state.bundle_tasks_downstream_only" in evidence["review_finding"]["message"]
    assert evidence["status"] == "blocked"
    assert evidence["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    assert payload["receipt_ref"].startswith("artifacts/runtime/opl_family_domain_handler/dispatch_receipts/")
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()
