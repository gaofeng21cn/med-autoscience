from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from med_autoscience import profiles
from tests.domain_owner_action_dispatch_helpers import dispatch as _dispatch
from tests.domain_owner_action_dispatch_helpers import owner_route as _owner_route
from tests.domain_owner_action_dispatch_helpers import write_json as _write_json
from .shared import write_profile


@pytest.mark.parametrize(
    "command",
    (
        ["runtime", "domain-route-reconcile"],
        ["domain-route-reconcile"],
    ),
)
def test_domain_route_reconcile_command_runs_one_shot_and_writes_receipt(
    command: list[str],
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    reconcile = importlib.import_module("med_autoscience.controllers.domain_route_reconcile")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_scan_domain_routes(
        *,
        profile,
        study_ids,
        apply_safe_actions: bool,
        apply_runtime_platform_repair: bool = False,
        developer_supervisor_mode: str | None = None,
    ) -> dict[str, object]:
        calls.append(("scan", tuple(study_ids)))
        suffix = len([name for name, _ in calls if name == "scan"])
        return {
            "surface": "portable_owner_route_reconcile",
            "workspace_root": str(profile.workspace_root),
            "studies": [
                {
                    "study_id": "DM002",
                    "owner_route": {"next_owner": f"owner-{suffix}", "idempotency_key": f"route-{suffix}"},
                    "action_queue": [{"action_type": f"action-{suffix}"}],
                    "why_not_applied": None if suffix == 1 else "publication_gate_blocked",
                    "owner_forwarded": suffix == 2,
                    "stable_blocker": {"kind": "publication_gate", "status": "blocked"},
                }
            ],
            "action_queue": [{"study_id": "DM002", "action_type": f"action-{suffix}"}],
        }

    def fake_materialize_domain_action_requests(
        *,
        profile,
        study_ids,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        calls.append(("consume", tuple(study_ids)))
        return {
            "surface": "domain_action_request_materializer",
            "requested_studies": list(study_ids),
            "request_tasks": [{"study_id": "DM002", "dispatch_status": "applied"}],
            "default_executor_dispatches": [
                {"study_id": "DM002", "action_type": "publication_gate_specificity_required", "dispatch_status": "ready"}
            ],
        }

    def fake_dispatch_domain_owner_actions(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
        managed_runtime_worker: bool = False,
        consumer_payload=None,
    ) -> dict[str, object]:
        calls.append(("execute-dispatch", tuple(study_ids)))
        assert consumer_payload is not None
        assert consumer_payload["default_executor_dispatches"][0]["study_id"] == "DM002"
        return {
            "surface": "default_executor_dispatch_executor",
            "requested_studies": list(study_ids),
            "codex_dispatch_count": 0,
            "suppressed_dispatch_count": 1,
            "dry_run_count": 0,
            "blocked_count": 1,
            "executions": [
                {
                    "study_id": "DM002",
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "blocked",
                    "blocked_reason": "quest_root_missing",
                }
            ],
        }

    monkeypatch.setattr(reconcile.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(reconcile.domain_action_request_materializer, "materialize_domain_action_requests", fake_materialize_domain_action_requests)
    monkeypatch.setattr(
        reconcile.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )

    exit_code = cli.main(
        [
            *command,
            "--profile",
            str(profile_path),
            "--studies",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert calls == [
        ("scan", ("DM002",)),
        ("consume", ("DM002",)),
        ("execute-dispatch", ("DM002",)),
        ("scan", ("DM002",)),
    ]
    assert payload["surface"] == "domain_route_reconcile_receipt"
    assert payload["before"]["studies"][0]["owner_route"]["next_owner"] == "owner-1"
    assert payload["after"]["studies"][0]["owner_route"]["next_owner"] == "owner-2"
    assert payload["executed_dispatch"]["executions"][0]["blocked_reason"] == "quest_root_missing"
    assert payload["codex_dispatch_count"] == 0
    assert payload["suppressed_dispatch_count"] == 1
    assert payload["will_start_llm"] is False
    assert payload["action_cost"]["action_class"] == "controller_apply"
    assert payload["action_cost"]["will_start_llm"] is False
    assert payload["paper_progress_reconcile"]["surface"] == "paper_progress_reconcile_receipt"
    assert payload["paper_progress_reconcile"]["decisions"][0]["current_state"]["surface"] == "paper_progress_state"
    assert payload["study_receipts"][0]["before"]["action_queue"][0]["action_type"] == "action-1"
    assert payload["study_receipts"][0]["after"]["why_not_applied"] == "publication_gate_blocked"
    assert payload["study_receipts"][0]["after"]["owner_forwarded"] is True
    assert payload["study_receipts"][0]["after"]["stable_blocker"]["kind"] == "publication_gate"
    latest_path = workspace_root / "artifacts" / "supervision" / "reconcile" / "latest.json"
    history_path = workspace_root / "artifacts" / "supervision" / "reconcile" / "history.jsonl"
    assert json.loads(latest_path.read_text(encoding="utf-8"))["surface"] == "domain_route_reconcile_receipt"
    assert history_path.read_text(encoding="utf-8").strip()


def test_domain_route_reconcile_dry_run_never_dispatches_llm(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    reconcile = importlib.import_module("med_autoscience.controllers.domain_route_reconcile")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        return {
            "surface": "portable_owner_route_reconcile",
            "workspace_root": str(kwargs["profile"].workspace_root),
            "studies": [
                {
                    "study_id": "DM002",
                    "owner_route": {"next_owner": "mas_controller", "idempotency_key": "route-dry-run"},
                    "action_queue": [{"action_type": "runtime_platform_repair"}],
                    "paper_progress_stall": {
                        "surface_kind": "paper_progress_stall",
                        "stalled": True,
                        "stall_reasons": ["same_fingerprint_loop"],
                    },
                }
            ],
            "action_queue": [{"study_id": "DM002", "action_type": "runtime_platform_repair"}],
        }

    monkeypatch.setattr(reconcile.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        reconcile.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **_: {"surface": "domain_action_request_materializer", "default_executor_dispatch_count": 1},
    )
    monkeypatch.setattr(
        reconcile.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        lambda **kwargs: {
            "surface": "default_executor_dispatch_executor",
            "execution_count": 1,
            "executed_count": 0,
            "blocked_count": 0,
            "dry_run_count": 1,
            "codex_dispatch_count": 0,
            "suppressed_dispatch_count": 0,
            "action_fingerprints": ["runtime_platform_repair::same_fingerprint_loop"],
            "executions": [
                {
                    "study_id": "DM002",
                    "action_type": "runtime_platform_repair",
                    "execution_status": "dry_run",
                    "will_start_llm": False,
                }
            ],
        },
    )

    exit_code = cli.main(
        [
            "domain-route-reconcile",
            "--profile",
            str(profile_path),
            "--studies",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--dry-run",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["dry_run"] is True
    assert payload["will_start_llm"] is False
    assert payload["codex_dispatch_count"] == 0
    assert payload["action_cost"]["action_class"] == "reconcile_dry_run"
    assert payload["action_cost"]["will_start_llm"] is False
    assert payload["paper_progress_reconcile"]["dry_run"] is True
    assert payload["paper_progress_reconcile"]["decisions"][0]["action_receipt"]["receipt_status"] == "dry_run_not_recorded"
    assert payload["executed_dispatch"]["executions"][0]["will_start_llm"] is False


def test_domain_route_reconcile_executes_current_consume_payload_without_writing_consumer_latest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.domain_route_reconcile")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = profiles.load_profile(profile_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=stale_route,
    )
    stale_dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, stale_dispatch)
    _write_json(
        workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [stale_dispatch],
        },
    )
    current_route = dict(
        stale_route,
        runtime_health_epoch="runtime-health-current",
        work_unit_fingerprint="truth-snapshot::current-ai-reviewer",
        source_fingerprint="truth-snapshot::current-ai-reviewer",
        idempotency_key="owner-route::003::current-ai-reviewer",
    )
    current_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=current_route,
    )
    current_dispatch["refs"] = {"dispatch_path": str(dispatch_path)}

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        payload = {
            "surface": "portable_owner_route_reconcile",
            "workspace_root": str(kwargs["profile"].workspace_root),
            "studies": [{"study_id": study_id, "owner_route": current_route}],
            "action_queue": [],
        }
        _write_json(workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json", payload)
        return payload

    monkeypatch.setattr(reconcile.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)
    monkeypatch.setattr(
        reconcile.domain_action_request_materializer,
        "materialize_domain_action_requests",
        lambda **_: {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "dry_run": True,
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [current_dispatch],
        },
    )
    monkeypatch.setattr(
        reconcile.domain_owner_action_dispatch,
        "_execute_ai_reviewer_workflow",
        lambda **_: {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow",
        },
    )

    result = reconcile.reconcile_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    execution = result["executed_dispatch"]["executions"][0]
    assert execution["blocked_reason"] is None
    assert execution["execution_status"] == "dry_run"
    assert execution["owner_route"]["work_unit_fingerprint"] == "truth-snapshot::current-ai-reviewer"
    consumer_latest = json.loads(
        (workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json").read_text(encoding="utf-8")
    )
    assert consumer_latest["default_executor_dispatches"][0]["owner_route"]["work_unit_fingerprint"] != (
        "truth-snapshot::current-ai-reviewer"
    )


def test_domain_route_reconcile_dispatches_medical_prose_quality_repair_batch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.domain_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = profiles.load_profile(profile_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            "source_fingerprint": "truth-source::medical-prose",
            "idempotency_key": "owner-route::003::medical-prose",
        }
    )
    scan_payload = {
        "surface": "portable_owner_route_reconcile",
        "workspace_root": str(workspace_root),
        "studies": [
            {
                "study_id": study_id,
                "quest_id": study_id,
                "owner_route": route,
                "action_queue": [
                    {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "request_owner": "write",
                        "recommended_owner": "write",
                        "next_work_unit": "medical_prose_write_repair",
                        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
                        "owner_route": route,
                    }
                ],
            }
        ],
        "action_queue": [],
    }
    _write_json(workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json", scan_payload)

    monkeypatch.setattr(reconcile.owner_route_reconcile, "scan_domain_routes", lambda **_: scan_payload)
    called: dict[str, object] = {}

    def fake_execute_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "execution_status": "blocked",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
        }

    monkeypatch.setattr(
        reconcile.domain_owner_action_dispatch.action_execution.quality_repair,
        "execute_quality_repair_batch",
        fake_execute_quality_repair_batch,
    )

    result = reconcile.reconcile_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    consumer = result["consumed"]
    assert consumer["default_executor_dispatch_count"] == 1
    dispatch = consumer["default_executor_dispatches"][0]
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "write"
    execution = result["executed_dispatch"]["executions"][0]
    assert execution["action_type"] == "run_quality_repair_batch"
    assert execution["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert called["study_id"] == study_id
    assert called["apply"] is True
