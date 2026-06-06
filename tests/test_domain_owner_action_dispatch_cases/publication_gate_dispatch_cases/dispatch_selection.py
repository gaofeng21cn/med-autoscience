from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_default_dispatch_selects_stage_artifact_publication_handoff_over_stale_defaults(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    stale_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface="typed blocker:manuscript_story_surface_delta_missing",
        owner_route=stale_route,
    )
    current_route = _owner_route(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
    )
    current_route["source_refs"] = {
        "work_unit_id": "publication_handoff_owner_gate",
        "work_unit_fingerprint": current_route["work_unit_fingerprint"],
        "owner_route_currentness_basis": {
            "truth_epoch": current_route["truth_epoch"],
            "runtime_health_epoch": current_route["runtime_health_epoch"],
            "work_unit_id": "publication_handoff_owner_gate",
            "work_unit_fingerprint": current_route["work_unit_fingerprint"],
        },
    }
    current_dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_handoff_owner_gate",
        owner="publication_gate_owner",
        required_output_surface=(
            "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json "
            "or artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
        ),
        owner_route=current_route,
    )
    stale_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    current_path = stale_path.parent / "publication_handoff_owner_gate.json"
    _write_json(stale_path, stale_dispatch)
    _write_json(current_path, current_dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "publication_handoff_owner_gate",
                            "owner": "publication_gate_owner",
                            "owner_route": current_route,
                        }
                    ],
                    "stage_artifact_index": {
                        "surface_kind": "stage_artifact_index",
                        "current_stage": "08-publication_package_handoff",
                        "next_owner_action": {
                            "action_type": "publication_handoff_owner_gate",
                            "allowed_actions": ["publication_handoff_owner_gate"],
                            "next_owner": "publication_gate_owner",
                            "work_unit_id": "publication_handoff_owner_gate",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "source": "stage_artifact_index.next_owner_action",
                        "allowed_actions": ["publication_handoff_owner_gate"],
                        "next_owner": "publication_gate_owner",
                        "work_unit_id": "publication_handoff_owner_gate",
                    },
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [
                {**stale_dispatch, "refs": {"dispatch_path": str(stale_path)}},
                {**current_dispatch, "refs": {"dispatch_path": str(current_path)}},
            ],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert [execution["action_type"] for execution in result["executions"]] == [
        "publication_handoff_owner_gate"
    ]
