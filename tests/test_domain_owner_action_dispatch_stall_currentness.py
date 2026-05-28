from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_quality_repair_batch_ignores_nonterminal_stall_fingerprint_drift(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "failure_signature": "publication_gate_route_back_write_required",
            "owner_reason": "publication_gate_route_back_write_required",
            "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::dm003",
            "idempotency_key": "owner-route::dm003::write::publication-gate-route-back",
        }
    )
    stale_dispatch_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": False,
        "terminal": False,
        "action_fingerprint": "paper_progress_stall::old-read-model",
        "stall_reasons": [],
    }
    current_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": False,
        "terminal": False,
        "action_fingerprint": "paper_progress_stall::fresh-read-model",
        "stall_reasons": [],
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "next_work_unit": {
            "unit_id": "manuscript_story_repair",
            "lane": "write",
        },
        "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::dm003",
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": "manuscript_story_repair",
        "lane": "write",
    }
    dispatch_payload["paper_progress_stall"] = stale_dispatch_stall
    dispatch_payload["prompt_contract"]["paper_progress_stall"] = stale_dispatch_stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "write",
            "owner_route": route,
        },
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": current_stall,
                    "action_queue": [],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall"]["action_fingerprint"] == "paper_progress_stall::old-read-model"
    assert execution["current_paper_progress_stall"]["action_fingerprint"] == "paper_progress_stall::fresh-read-model"
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["authority_route_context"]["work_unit_id"] == "manuscript_story_repair"
