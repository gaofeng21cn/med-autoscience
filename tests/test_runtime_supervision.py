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


def test_runtime_supervision_materializes_runtime_health_snapshot_from_live_status(tmp_path: Path) -> None:
    runtime_health_kernel = importlib.import_module("med_autoscience.controllers.runtime_health_kernel")
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    _write_json(
        runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root),
        {
            "schema_version": 1,
            "surface": "runtime_health_snapshot",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "active_run_id": None,
            "worker_liveness_state": {"state": "missing_live_session", "worker_running": False},
            "blocking_reasons": ["quest_marked_running_but_no_live_session"],
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

    persisted = json.loads(runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root).read_text(encoding="utf-8"))
    assert payload is not None
    assert payload["health_status"] == "live"
    assert payload["runtime_health_snapshot"]["active_run_id"] == "run-live"
    assert persisted["attempt_state"] == "live"
    assert persisted["canonical_runtime_action"] == "continue_supervising_runtime"
    assert persisted["active_run_id"] == "run-live"
    assert persisted["worker_liveness_state"]["state"] == "live"
    assert persisted["worker_liveness_state"]["worker_running"] is True
    assert persisted["blocking_reasons"] == []


def test_runtime_supervision_does_not_persist_runtime_health_snapshot_when_not_apply(tmp_path: Path) -> None:
    runtime_health_kernel = importlib.import_module("med_autoscience.controllers.runtime_health_kernel")
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    snapshot_path = runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root)
    previous_snapshot = {
        "schema_version": 1,
        "surface": "runtime_health_snapshot",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "attempt_state": "escalated",
        "canonical_runtime_action": "external_supervisor_required",
        "active_run_id": None,
        "worker_liveness_state": {"state": "missing_live_session", "worker_running": False},
        "blocking_reasons": ["quest_marked_running_but_no_live_session"],
    }
    _write_json(snapshot_path, previous_snapshot)

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
        apply=False,
    )

    persisted = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert payload is not None
    assert payload["health_status"] == "live"
    assert payload["runtime_health_snapshot"]["active_run_id"] == "run-live"
    assert persisted == previous_snapshot


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


def test_runtime_supervision_recovers_active_quest_with_stale_tick_and_no_live_worker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload={
            **_managed_status_payload(
                study_root=study_root,
                quest_root=quest_root,
                status="none",
                worker_running=False,
                active_run_id=None,
                decision="noop",
                reason="quest_already_running",
                quest_status="active",
            ),
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
            },
        },
        recorded_at="2026-04-21T08:20:00+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "recovering"
    assert payload["last_transition"] == "auto_recovery_pending"
    assert payload["next_action"] == "wait_for_runtime_recovery_confirmation"
    assert payload["needs_human_intervention"] is False


def test_runtime_supervision_requires_active_run_id_for_live_projection(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "decision": "noop",
            "reason": "quest_already_running",
            "execution": {
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
            },
            "runtime_liveness_status": "live",
            "active_run_id": None,
            "worker_running": True,
            "supervisor_tick_audit": {
                "required": True,
                "status": "stale",
                "reason": "supervisor_tick_report_stale",
            },
        },
        recorded_at="2026-04-21T08:25:00+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "recovering"
    assert payload["runtime_liveness_status"] == "live"
    assert payload["active_run_id"] is None


def test_runtime_supervision_projects_strict_live_activity_timeout_as_recovering(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload={
            **_managed_status_payload(
                study_root=study_root,
                quest_root=quest_root,
                status="live",
                worker_running=True,
                active_run_id="run-live-stale",
                decision="noop",
                reason="quest_already_running",
                quest_status="running",
            ),
            "autonomy_slo": {
                "state": "breach",
                "breach_types": ["read_churn_without_artifact_delta"],
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "latest_recorded_at": "2026-05-02T11:07:28+00:00",
            },
        },
        recorded_at="2026-05-02T11:07:29+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "recovering"
    assert payload["runtime_liveness_status"] == "live"
    assert payload["active_run_id"] == "run-live-stale"
    assert payload["canonical_runtime_action"] == "recover_runtime"
    assert payload["runtime_health_snapshot"]["worker_liveness_state"]["state"] == "activity_timeout"
    assert payload["last_transition"] == "activity_timeout"
    assert payload["next_action"] == "wait_for_meaningful_artifact_delta"
    assert payload["needs_human_intervention"] is False


def test_runtime_supervision_escalates_when_runtime_health_retry_budget_is_exhausted(tmp_path: Path) -> None:
    runtime_health_kernel = importlib.import_module("med_autoscience.controllers.runtime_health_kernel")
    module = importlib.import_module("med_autoscience.controllers.runtime_supervision")

    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    for sequence in range(3):
        runtime_health_kernel.append_runtime_health_event(
            study_root=study_root,
            study_id="001-risk",
            quest_id="quest-001",
            event_type="recover_attempt",
            payload={
                "attempt_state": "failed",
                "failure_reason": "no_live_session",
                "active_run_id": "run-live-stale",
            },
            recorded_at=f"2026-05-02T11:0{sequence}:00+00:00",
        )

    payload = module.materialize_runtime_supervision(
        study_root=study_root,
        status_payload={
            **_managed_status_payload(
                study_root=study_root,
                quest_root=quest_root,
                status="live",
                worker_running=True,
                active_run_id="run-live-stale",
                decision="noop",
                reason="quest_already_running",
                quest_status="running",
            ),
            "autonomy_slo": {
                "state": "breach",
                "breach_types": ["read_churn_without_artifact_delta"],
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
            },
        },
        recorded_at="2026-05-02T11:07:29+00:00",
        apply=True,
    )

    assert payload is not None
    assert payload["health_status"] == "escalated"
    assert payload["runtime_liveness_status"] == "live"
    assert payload["canonical_runtime_action"] == "external_supervisor_required"
    assert payload["runtime_health_snapshot"]["retry_budget_remaining"] == 0
    assert "runtime_recovery_retry_budget_exhausted" in payload["runtime_health_snapshot"]["blocking_reasons"]
    assert payload["needs_human_intervention"] is True
    assert payload["next_action"] == "manual_intervention_required"
    assert "人工介入" in payload["next_action_summary"]
