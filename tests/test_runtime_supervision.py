from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _managed_status_payload(
    *,
    study_root: Path,
    quest_root: Path,
    status: str,
    worker_running: bool,
    active_run_id: str | None,
    decision: str,
    reason: str,
    quest_status: str = "running",
) -> dict[str, object]:
    return {
        "study_id": "001-risk",
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": quest_status,
        "decision": decision,
        "reason": reason,
        "execution": {
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
        },
        "runtime_liveness_audit": {
            "status": status,
            "active_run_id": active_run_id,
            "runtime_audit": {
                "status": status,
                "active_run_id": active_run_id,
                "worker_running": worker_running,
            },
        },
    }


def test_runtime_supervision_escalation_points_user_back_to_mas_control_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    latest_report_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    _write_json(
        latest_report_path,
        {
            "health_status": "degraded",
            "consecutive_failure_count": 1,
            "recovery_attempt_count": 1,
        },
    )

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "decision": "blocked",
            "reason": "resume_request_failed",
            "quest_status": "running",
            "execution": {
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
            },
        },
        recorded_at="2026-04-21T08:00:00+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "escalated"
    assert payload["next_action"] == "manual_intervention_required"
    assert payload["next_action_summary"] == "请回到 MAS 控制面确认当前托管运行策略，并决定是否暂停、重启或接管。"
    assert "MedDeepScientist" not in payload["next_action_summary"]


def test_runtime_supervision_marks_first_live_after_recovery_as_stabilizing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "health_status": "recovering",
            "stable_live_observation_count": 0,
            "flapping_episode_count": 0,
        },
    )

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload=_managed_status_payload(
            study_root=study_root,
            quest_root=quest_root,
            status="live",
            worker_running=True,
            active_run_id="run-live",
            decision="noop",
            reason="quest_already_running",
        ),
        recorded_at="2026-04-21T08:05:00+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "live"
    assert payload["runtime_stability_status"] == "stabilizing"
    assert payload["stable_live_observation_count"] == 1
    assert payload["stable_live_required_count"] == 2
    assert payload["flapping_episode_count"] == 0
    assert payload["flapping_circuit_breaker"] is False


def test_runtime_supervision_marks_live_stable_after_required_consecutive_observations(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "health_status": "live",
            "runtime_stability_status": "stabilizing",
            "stable_live_observation_count": 1,
            "stable_live_required_count": 2,
            "flapping_episode_count": 0,
        },
    )

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload=_managed_status_payload(
            study_root=study_root,
            quest_root=quest_root,
            status="live",
            worker_running=True,
            active_run_id="run-live",
            decision="noop",
            reason="quest_already_running",
        ),
        recorded_at="2026-04-21T08:10:00+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "live"
    assert payload["runtime_stability_status"] == "stable"
    assert payload["stable_live_observation_count"] == 2
    assert payload["stable_live_required_count"] == 2
    assert payload["flapping_episode_count"] == 0
    assert payload["flapping_circuit_breaker"] is False


def test_runtime_supervision_flags_flapping_when_live_drops_back_to_recovery(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "health_status": "live",
            "runtime_stability_status": "stabilizing",
            "stable_live_observation_count": 1,
            "stable_live_required_count": 2,
            "flapping_episode_count": 0,
        },
    )

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload=_managed_status_payload(
            study_root=study_root,
            quest_root=quest_root,
            status="none",
            worker_running=False,
            active_run_id="run-live",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        recorded_at="2026-04-21T08:15:00+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "recovering"
    assert payload["runtime_stability_status"] == "flapping"
    assert payload["stable_live_observation_count"] == 0
    assert payload["flapping_episode_count"] == 1
    assert payload["flapping_circuit_breaker"] is True
