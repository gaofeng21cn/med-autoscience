from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_quality_repair_batch_from_persisted_dispatch_and_owner_request(
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
            "unit_id": "medical_prose_write_repair",
            "lane": "write",
        },
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
    }
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
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": {
                        **route,
                        "truth_epoch": "newer-scan-epoch",
                        "route_epoch": "newer-scan-epoch",
                        "source_fingerprint": "newer-scan-source",
                        "idempotency_key": "owner-route::newer-scan-epoch",
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
            "default_executor_dispatches": [],
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

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["owner_route_basis"] == "owner_request"
    assert execution["execution_status"] == "executed"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["study_id"] == study_id
    assert called["quest_id"] == f"quest-{study_id}"
    assert called["control_plane_route_context"]["work_unit_id"] == "medical_prose_write_repair"


@pytest.mark.parametrize(
    ("failure_signature", "idempotency_key", "string_work_unit_payload"),
    (
        (
            "manuscript_story_surface_delta_missing",
            "owner-route::dm003::write::story-surface-delta-missing",
            False,
        ),
        (
            "quest_waiting_opl_runtime_owner_route",
            "owner-route::dm003::write::quest-waiting-opl-runtime-owner-route",
            False,
        ),
        (
            "quest_waiting_opl_runtime_owner_route",
            "owner-route::dm003::write::quest-waiting-opl-runtime-owner-route-string-work-unit",
            True,
        ),
    ),
)
def test_execute_quality_repair_batch_honors_write_owner_route_despite_terminal_stall(
    monkeypatch,
    tmp_path: Path,
    failure_signature: str,
    idempotency_key: str,
    string_work_unit_payload: bool,
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
            "failure_signature": failure_signature,
            "owner_reason": failure_signature,
            "work_unit_fingerprint": "medical-prose-routeback::write::sha256-dm003",
            "idempotency_key": idempotency_key,
        }
    )
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::dm003-write",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
        "action_cost": {
            "surface_kind": "runtime_dispatch_cost_contract",
            "action_class": "observe_only",
            "will_start_llm": False,
            "reason": "paper_progress_stall_read_model",
            "llm_dispatch_allowed": False,
            "codex_worker_dispatch": False,
        },
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
    if string_work_unit_payload:
        dispatch_payload["next_work_unit"] = "medical_prose_write_repair"
    else:
        dispatch_payload["source_action"] = {
            "action_type": "run_quality_repair_batch",
            "route_target": "write",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
            },
            "work_unit_fingerprint": "medical-prose-routeback::write::sha256-dm003",
        }
        dispatch_payload["prompt_contract"]["next_work_unit"] = {
            "unit_id": "medical_prose_write_repair",
            "lane": "write",
        }
    dispatch_payload["paper_progress_stall"] = stall
    dispatch_payload["prompt_contract"]["paper_progress_stall"] = stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
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
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["control_plane_route_context"]["work_unit_id"] == "medical_prose_write_repair"


def test_execute_quality_repair_batch_uses_current_terminal_stall_when_dispatch_stall_fingerprint_is_stale(
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
            "failure_signature": "quest_waiting_opl_runtime_owner_route",
            "owner_reason": "quest_waiting_opl_runtime_owner_route",
            "work_unit_fingerprint": "truth-snapshot::dm003-medical-prose",
            "idempotency_key": "owner-route::dm003::write::quest-waiting-opl-runtime-owner-route",
        }
    )
    stale_dispatch_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::old",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
    }
    current_terminal_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::current",
        "stall_reasons": ["runtime_recovery_retry_budget_exhausted"],
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
            "unit_id": "medical_prose_write_repair",
            "lane": "write",
        },
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
    }
    dispatch_payload["prompt_contract"]["next_work_unit"] = {
        "unit_id": "medical_prose_write_repair",
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
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": current_terminal_stall,
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
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert execution["current_paper_progress_stall"]["action_fingerprint"] == "paper_progress_stall::current"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["control_plane_route_context"]["work_unit_id"] == "medical_prose_write_repair"


def test_execute_quality_repair_batch_prefers_fresh_persisted_dispatch_over_stale_consumer_inline(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
            "idempotency_key": "owner-route::dm002::write::story-surface-delta-missing",
        }
    )
    stale_dispatch_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": False,
        "terminal": False,
        "action_fingerprint": "paper_progress_stall::old",
        "stall_reasons": [],
    }
    current_stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": False,
        "terminal": False,
        "action_fingerprint": "paper_progress_stall::current",
        "stall_reasons": [],
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    stale_dispatch["paper_progress_stall"] = stale_dispatch_stall
    stale_dispatch["prompt_contract"]["paper_progress_stall"] = stale_dispatch_stall
    fresh_dispatch = {
        **stale_dispatch,
        "paper_progress_stall": current_stall,
        "prompt_contract": {
            **stale_dispatch["prompt_contract"],
            "paper_progress_stall": current_stall,
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
            },
        },
        "source_action": {
            "action_type": "run_quality_repair_batch",
            "route_target": "write",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
            },
            "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
        },
    }
    _write_json(dispatch_path, fresh_dispatch)
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
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": current_stall,
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
                {**stale_dispatch, "refs": {"dispatch_path": str(dispatch_path)}},
            ],
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
    assert execution["paper_progress_stall"]["action_fingerprint"] == "paper_progress_stall::current"
    assert execution["current_paper_progress_stall"]["action_fingerprint"] == "paper_progress_stall::current"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["control_plane_route_context"]["work_unit_id"] == "dm002_same_line_publication_paper_repair"
    assert called["control_plane_route_context"]["current_owner_route"]["idempotency_key"] == route["idempotency_key"]
    assert called["control_plane_route_context"]["current_owner_route"]["work_unit_fingerprint"] == (
        "dm002_same_line_publication_paper_repair_20260521"
    )
