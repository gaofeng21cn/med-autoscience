from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_sidecar_export_hydrates_owner_route_handoff_artifact_without_runtime_state_mutation(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.sidecar_family_adapter")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    handoff_path = study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json"
    runtime_state_path = profile.runtime_root / study_id / ".ds" / "runtime_state.json"
    _write_json(
        runtime_state_path,
        {
            "status": "waiting_for_user",
            "quest_id": study_id,
            "active_run_id": "run-opl-owned",
            "worker_running": True,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
        },
    )
    _write_json(
        handoff_path,
        {
            "surface_kind": "mas_runtime_owner_route_handoff_record",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_state_mutated": False,
            "handoff": {
                "surface_kind": "mas_runtime_owner_route_handoff",
                "domain_truth_owner": "med-autoscience",
                "queue_owner": "one-person-lab",
                "dispatch_surface": "medautosci sidecar export -> medautosci sidecar dispatch",
                "recommended_task_kind": "domain_route/reconcile-apply",
                "study_id": study_id,
                "quest_id": study_id,
                "runtime_state_path": str(runtime_state_path),
                "source": "domain_route_scan_platform_repair",
                "reason": "quest_waiting_opl_runtime_owner_route",
                "repair_kind": "controller_work_unit_pending_redrive",
                "authority_boundary": {
                    "mas_writes_generic_runtime_queue": False,
                    "mas_submits_runtime_chat": False,
                    "mas_resumes_provider_worker": False,
                    "opl_writes_mas_truth": False,
                    "mas_owner_receipt_required": True,
                },
            },
        },
    )

    export = module.export_family_sidecar(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
    )

    tasks = [
        task
        for task in export["pending_family_tasks"]
        if task["task_kind"] == "domain_route/reconcile-apply"
        and task["dedupe_key"] == (
            "mas:diabetes:002-dm-china-us-mortality-attribution:"
            "owner-route-handoff:quest_waiting_opl_runtime_owner_route"
        )
    ]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["queue_owner"] == "one-person-lab"
    assert task["domain_truth_owner"] == "med-autoscience"
    assert task["opl_runtime_owner_route_handoff"]["authority_boundary"]["mas_resumes_provider_worker"] is False
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["active_run_id"] == "run-opl-owned"
    assert runtime_state["worker_running"] is True
    assert "last_opl_runtime_owner_route_handoff" not in runtime_state
