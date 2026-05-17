from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_runs_current_package_freshness_owner_workflow(monkeypatch, tmp_path: Path) -> None:
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
        / "current_package_freshness_required.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        }

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("current_package_freshness_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "gate_clearing_batch.run_gate_clearing_batch"
    assert called["profile"] == profile
    assert called["study_id"] == study_id
    assert called["study_root"] == study_root
    assert called["quest_id"] == f"quest-{study_id}"
    assert called["source"] == "runtime_supervisor_dispatch_executor"
    route_context = called["control_plane_route_context"]["controller_route_context"]
    assert route_context["control_surface"] == "gate_clearing_batch"
    assert route_context["controller_action_type"] == "run_gate_clearing_batch"
    assert route_context["work_unit_id"] == "submission_minimal_refresh"


def test_execute_dispatch_runs_current_package_freshness_when_stalled_and_previous_attempt_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    route = _owner_route(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
    )
    route.update(
        {
            "truth_epoch": "truth-event-current-package",
            "route_epoch": "truth-event-current-package",
            "source_fingerprint": "truth-snapshot::current-package",
            "work_unit_fingerprint": "publication-blockers::current-package",
            "idempotency_key": "owner-route::current-package-freshness",
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::current-package",
        "stall_reasons": ["same_fingerprint_loop", "runtime_recovery_retry_budget_exhausted"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "current_package_freshness_required.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "current_package_freshness_required",
                    "execution_status": "blocked",
                    "blocked_reason": "paper_progress_stall_terminal",
                    "owner_route": route,
                    "prompt_contract": dispatch["prompt_contract"],
                    "repeat_suppression_key": "publication-blockers::current-package",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        proof_path = study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json"
        proof_path.parent.mkdir(parents=True, exist_ok=True)
        proof_path.write_text(json.dumps({"status": "fresh"}) + "\n", encoding="utf-8")
        return {
            "ok": True,
            "status": "executed",
            "current_package_freshness_proof": {"status": "fresh", "proof_path": str(proof_path)},
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        }

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("current_package_freshness_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["repeat_suppressed_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["repeat_suppression"]["repeat_suppressed"] is False
    assert execution["action_class"] == "controller_apply"
    assert called["study_id"] == study_id


def test_execute_dispatch_reruns_when_freshness_proof_exists_but_batch_still_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    route = _owner_route(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "current_package_freshness_required.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"status": "fresh"},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "status": "executed",
            "unit_results": [
                {
                    "unit_id": "create_submission_minimal_package",
                    "status": "failed",
                    "error": "pandoc returned non-zero exit status 1",
                }
            ],
            "gate_replay": {
                "status": "blocked",
                "blockers": ["submission_surface_qc_failure_present"],
            },
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "current_package_freshness_required",
                    "execution_status": "executed",
                    "owner_route": route,
                    "prompt_contract": dispatch["prompt_contract"],
                    "repeat_suppression_key": route["work_unit_fingerprint"],
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "current_package_freshness_proof": {"status": "fresh"},
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        }

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("current_package_freshness_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["repeat_suppressed_count"] == 0
    assert execution["execution_status"] == "executed"
    assert execution["repeat_suppression"]["repeat_suppressed"] is False
    assert called["study_id"] == study_id


def test_execute_dispatch_reruns_when_freshness_proof_source_eval_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    current_eval_id = "publication-eval::dm002::current"
    stale_eval_id = "publication-eval::dm002::stale"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    route = _owner_route(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::stale-source-eval",
        "stall_reasons": ["same_fingerprint_loop", "runtime_recovery_retry_budget_exhausted"],
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "current_package_freshness_required.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"schema_version": 1, "eval_id": current_eval_id},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"schema_version": 1, "status": "fresh", "source_eval_id": stale_eval_id},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {"schema_version": 1, "status": "executed", "source_eval_id": stale_eval_id, "unit_results": []},
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "current_package_freshness_proof": {"status": "fresh", "source_eval_id": current_eval_id},
        }

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("current_package_freshness_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert called["study_id"] == study_id
