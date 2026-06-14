from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_accepts_paper_recovery_owner_callable_route_without_scan_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    fingerprint = "current-readiness-typed-blocker::002-dm::current"
    route = _owner_route(
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        owner="MedAutoScience",
    )
    route.update(
        {
            "truth_epoch": fingerprint,
            "route_epoch": fingerprint,
            "runtime_health_epoch": fingerprint,
            "work_unit_fingerprint": fingerprint,
            "source_fingerprint": fingerprint,
            "owner_reason": "medical_paper_readiness_missing",
            "failure_signature": "medical_paper_readiness_missing",
            "source_refs": {
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "work_unit_fingerprint": fingerprint,
                "bridge_authority": "domain_action_request_materializer_paper_recovery_owner_callable",
                "source_surface": "paper_recovery_state",
                "owner_route_currentness_basis": {
                    "truth_epoch": fingerprint,
                    "runtime_health_epoch": fingerprint,
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        }
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="complete_medical_paper_readiness_surface",
        owner="MedAutoScience",
        required_output_surface="artifacts/medical_paper/readiness.json",
        owner_route=route,
    )
    dispatch_payload["authority"] = "paper_recovery_state"
    dispatch_payload["source_action"] = {
        "authority": "paper_recovery_state",
        "source_surface": "paper_recovery_state",
        "action_type": "complete_medical_paper_readiness_surface",
        "work_unit_id": "complete_medical_paper_readiness_surface",
        "work_unit_fingerprint": fingerprint,
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id}],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch_payload, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )
    monkeypatch.setattr(
        module.action_execution,
        "execute_complete_medical_paper_readiness_surface",
        lambda **_: {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "medical_paper_readiness.complete_medical_paper_readiness_surface",
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("complete_medical_paper_readiness_surface",),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "paper_recovery_owner_callable"
    assert execution["current_owner_route"]["idempotency_key"] == route["idempotency_key"]
