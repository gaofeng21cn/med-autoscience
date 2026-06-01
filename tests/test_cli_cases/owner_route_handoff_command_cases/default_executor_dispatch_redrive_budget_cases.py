from __future__ import annotations

from .shared import *  # noqa: F403,F401
from .default_executor_dispatch_export_cases import _write_default_executor_dispatch


def test_domain_handler_export_stops_repeated_nonconsumable_same_work_unit_closeout(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_default_executor_dispatch(
        dispatch_path=dispatch_path,
        study_root=study_root,
        include_owner_route=True,
    )
    owner_route = json.loads(dispatch_path.read_text(encoding="utf-8"))["prompt_contract"]["owner_route"]
    execution_base = {
        "surface": "default_executor_dispatch_execution",
        "schema_version": 1,
        "study_id": study_root.name,
        "quest_id": study_root.name,
        "action_type": "run_quality_repair_batch",
        "execution_status": "executed",
        "idempotency_key": owner_route["idempotency_key"],
        "current_owner_route": owner_route,
        "prompt_contract": {"owner_route": owner_route},
        "owner_result": {
            "status": "executed",
            "ok": True,
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                },
                "changed_artifact_refs": [{"path": str(study_root / "paper" / "claim_evidence_map.json")}],
            },
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_root.name,
            "executions": [],
            "execution_ledger": [
                {**execution_base, "execution_id": "execution::dm002::run_quality_repair_batch::first"},
                {**execution_base, "execution_id": "execution::dm002::run_quality_repair_batch::second"},
            ],
        },
    )

    exit_code = cli.main(["domain-handler", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_owner/default-executor-dispatch"
    ] == []
