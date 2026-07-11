from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _scoped_attempt_list_args(study_id: str) -> tuple[str, ...]:
    return (
        "family-runtime",
        "attempt",
        "list",
        "--domain",
        "mas",
        "--study",
        study_id,
        "--full",
        "--json",
    )


def _attempt(
    *,
    profile,
    study_id: str,
    stage_attempt_id: str,
    status: str,
    action_type: str = "run_quality_repair_batch",
    work_unit_id: str = "medical_prose_write_repair",
) -> dict[str, object]:
    return {
        "stage_attempt_id": stage_attempt_id,
        "domain_id": "medautoscience",
        "stage_id": "stage_outcome/opl-handoff",
        "status": status,
        "task_id": f"task-{stage_attempt_id}",
        "provider_kind": "temporal",
        "workflow_id": f"workflow-{stage_attempt_id}",
        "closeout_receipt_status": "accepted_typed_closeout"
        if status == "completed"
        else None,
        "closeout_refs": [f"opl://stage-attempts/{stage_attempt_id}/closeout"]
        if status == "completed"
        else [],
        "provider_run": {
            "provider_status": status,
            "workflow_id": f"workflow-{stage_attempt_id}",
            "last_heartbeat_at": "2026-07-11T10:00:00Z",
        },
        "route_impact": {
            "next_owner": "medautoscience",
            "domain_ready_verdict": "domain_gate_pending",
        },
        "workspace_locator": {
            "workspace_root": str(profile.workspace_root),
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "dispatch_ref": f"studies/{study_id}/dispatch/{stage_attempt_id}.json",
        },
    }


def _compact_attempt(attempt: dict[str, object]) -> dict[str, object]:
    return {
        key: attempt[key]
        for key in (
            "stage_attempt_id",
            "domain_id",
            "stage_id",
            "status",
            "task_id",
            "provider_kind",
            "workflow_id",
            "closeout_receipt_status",
        )
        if key in attempt
    } | {"study_id": _mapping(attempt.get("workspace_locator")).get("study_id")}


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _write_stage_attempt_closeout(
    *,
    profile,
    study_id: str,
    stage_attempt_id: str,
) -> None:
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipt"
        / f"{stage_attempt_id}.closeout.json"
    )
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_attempt_id": stage_attempt_id,
                "study_id": study_id,
                "status": "blocked",
            }
        ),
        encoding="utf-8",
    )


def test_live_provider_attempt_reads_only_scoped_stage_attempts(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    attempt = _attempt(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-live",
        status="running",
    )
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict[str, object]:
        commands.append(args)
        if args == _scoped_attempt_list_args(study_id):
            return {"family_runtime_stage_attempts": {"attempts": [_compact_attempt(attempt)]}}
        if args == ("family-runtime", "attempt", "inspect", "sat-live", "--json"):
            return {"family_runtime_stage_attempt": {"attempt": attempt}}
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id=study_id)

    assert result is not None
    assert result["source"] == "opl_family_runtime_attempt_inspect"
    assert result["active_stage_attempt_id"] == "sat-live"
    assert result["active_workflow_id"] == "workflow-sat-live"
    assert result["action_type"] == "run_quality_repair_batch"
    assert result["runtime_health"]["runtime_liveness_status"] == "live"
    assert commands == [
        _scoped_attempt_list_args(study_id),
        ("family-runtime", "attempt", "inspect", "sat-live", "--json"),
    ]


def test_live_provider_attempt_skips_stage_attempt_with_mas_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    _write_stage_attempt_closeout(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-closed",
    )
    closed = _attempt(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-closed",
        status="running",
    )
    live = _attempt(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-live",
        status="running",
    )
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict[str, object]:
        commands.append(args)
        if args == _scoped_attempt_list_args(study_id):
            return {
                "family_runtime_stage_attempts": {
                    "attempts": [_compact_attempt(closed), _compact_attempt(live)]
                }
            }
        if args == ("family-runtime", "attempt", "inspect", "sat-live", "--json"):
            return {"family_runtime_stage_attempt": {"attempt": live}}
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.live_provider_attempt_for_study(profile=profile, study_id=study_id)

    assert result is not None
    assert result["active_stage_attempt_id"] == "sat-live"
    assert commands == [
        _scoped_attempt_list_args(study_id),
        ("family-runtime", "attempt", "inspect", "sat-live", "--json"),
    ]


def test_terminal_provider_attempt_uses_scoped_stage_attempt_inspect(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.opl_provider_attempts"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    terminal = _attempt(
        profile=profile,
        study_id=study_id,
        stage_attempt_id="sat-terminal",
        status="completed",
    )
    commands: list[tuple[str, ...]] = []

    def fake_run(_: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict[str, object]:
        commands.append(args)
        if args == _scoped_attempt_list_args(study_id):
            return {"family_runtime_stage_attempts": {"attempts": [_compact_attempt(terminal)]}}
        if args == ("family-runtime", "attempt", "inspect", "sat-terminal", "--json"):
            return {"family_runtime_stage_attempt": {"attempt": terminal}}
        raise AssertionError(args)

    monkeypatch.setattr(module, "_opl_bin", lambda: Path("/tmp/opl"))
    monkeypatch.setattr(module, "_run_opl_json", fake_run)

    result = module.terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        max_inspect_count=1,
    )

    assert result is not None
    assert result["source"] == "opl_family_runtime_attempt_inspect"
    assert result["stage_attempt_id"] == "sat-terminal"
    assert result["closeout_receipt_status"] == "accepted_typed_closeout"
    assert result["authority_boundary"]["provider_completion_is_domain_completion"] is False
    assert commands == [
        _scoped_attempt_list_args(study_id),
        ("family-runtime", "attempt", "inspect", "sat-terminal", "--json"),
    ]
