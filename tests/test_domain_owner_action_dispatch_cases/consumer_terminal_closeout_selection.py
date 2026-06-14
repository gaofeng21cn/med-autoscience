from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
    write_scan_latest as _write_scan_latest,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_allows_terminal_closeout_owner_answer_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    action_type = "run_gate_clearing_batch"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
    )
    route["source_refs"] = {
        "work_unit_id": work_unit_id,
        "source_eval_id": "publication-eval::dm002::gate",
    }
    route["work_unit_fingerprint"] = "truth-snapshot::dm002::gate"
    route["source_fingerprint"] = "truth-source::dm002::gate"
    route["idempotency_key"] = "owner-route::dm002::gate"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    dispatch_payload["source_action"] = {
        "action_type": action_type,
        "next_work_unit": {"unit_id": work_unit_id},
        "source_eval_id": "publication-eval::dm002::gate",
    }
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "action_type": action_type,
                        "owner": "one-person-lab",
                        "currentness_basis": {"work_unit_id": work_unit_id},
                    },
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_id": "terminal_closeout_owner_answer_required",
                            "action_type": action_type,
                            "work_unit_id": work_unit_id,
                        },
                    },
                }
            ],
        },
    )

    def fake_read_study_progress(**kwargs) -> dict[str, object]:
        return {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "terminal_closeout_owner_answer_required",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "closeout_refs": [
                        str(dispatch_path),
                    ],
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(action_type,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    assert result["dry_run_count"] == 1
    assert result["blocked_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 1
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] is None
    assert result["executions"][0]["action_type"] == action_type
    assert result["executions"][0]["execution_status"] == "dry_run"
    assert result["executions"][0]["owner_route_basis"] == "terminal_closeout_owner_answer_dispatch"


def test_execute_dispatch_rejects_terminal_closeout_owner_answer_dispatch_with_stale_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    action_type = "run_gate_clearing_batch"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
    )
    route["source_refs"] = {
        "work_unit_id": work_unit_id,
        "source_eval_id": "publication-eval::dm002::old-gate",
        "owner_route_currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": "truth-snapshot::dm002::old-gate",
            "source_eval_id": "publication-eval::dm002::old-gate",
        },
    }
    route["work_unit_fingerprint"] = "truth-snapshot::dm002::old-gate"
    route["source_fingerprint"] = "truth-source::dm002::old-gate"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    dispatch_payload["source_action"] = {
        "action_type": action_type,
        "next_work_unit": {"unit_id": work_unit_id},
        "source_eval_id": "publication-eval::dm002::old-gate",
    }
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "action_type": action_type,
                        "owner": "one-person-lab",
                        "currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": "truth-snapshot::dm002::fresh-gate",
                            "source_eval_id": "publication-eval::dm002::fresh-gate",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_id": "terminal_closeout_owner_answer_required",
                            "action_type": action_type,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": "truth-snapshot::dm002::fresh-gate",
                            "source_eval_id": "publication-eval::dm002::fresh-gate",
                        },
                    },
                }
            ],
        },
    )

    def fake_read_study_progress(**kwargs) -> dict[str, object]:
        return {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "terminal_closeout_owner_answer_required",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": "truth-snapshot::dm002::fresh-gate",
                    "source_eval_id": "publication-eval::dm002::fresh-gate",
                    "closeout_refs": [
                        "artifacts/supervision/consumer/default_executor_execution/latest.json",
                    ],
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(action_type,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )


def test_execute_dispatch_keeps_unrelated_typed_blocker_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    action_type = "run_gate_clearing_batch"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_scan_latest(profile, study_id, route)

    def fake_read_study_progress(**kwargs) -> dict[str, object]:
        return {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "anti_loop_budget_exhausted",
                    "action_type": action_type,
                    "work_unit_id": "same-work-unit",
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(action_type,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )
