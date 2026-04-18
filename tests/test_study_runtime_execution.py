from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace


def _base_status_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/workspace/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": "/tmp/workspace/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "noop",
        "reason": "quest_already_running",
    }


def _patch_router(monkeypatch, module) -> None:
    managed_runtime_backend = SimpleNamespace(resolve_daemon_url=lambda *, runtime_root: "http://127.0.0.1:21999")
    monkeypatch.setattr(
        module,
        "_router_module",
        lambda: SimpleNamespace(
            managed_runtime_backend=managed_runtime_backend,
            managed_runtime_transport=managed_runtime_backend,
            med_deepscientist_transport=managed_runtime_backend,
            _managed_runtime_backend_for_execution=lambda execution: managed_runtime_backend,
        ),
    )


def test_runtime_execution_router_patch_exposes_generic_managed_runtime_transport_alias(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    _patch_router(monkeypatch, module)

    router = module._router_module()

    assert router.managed_runtime_transport is router.med_deepscientist_transport


def test_autonomous_runtime_notice_reports_live_runtime_only_when_liveness_is_strictly_live(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    status = typed_surface.StudyRuntimeStatus.from_payload(_base_status_payload())
    status.record_runtime_liveness_audit(
        {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        }
    )

    module._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=Path("/tmp/runtime"),
        launch_report_path=Path("/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"),
    )

    assert status.to_dict()["autonomous_runtime_notice"]["notification_reason"] == (
        "detected_existing_live_managed_runtime"
    )


def test_autonomous_runtime_notice_marks_unhealthy_runtime_without_claiming_live(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    status = typed_surface.StudyRuntimeStatus.from_payload(_base_status_payload())
    status.record_runtime_liveness_audit(
        {
            "status": "unknown",
            "active_run_id": "run-stale",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-stale",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
                "stale_progress": True,
            },
            "stale_progress": True,
            "liveness_guard_reason": "stale_progress_watchdog",
        }
    )

    module._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=Path("/tmp/runtime"),
        launch_report_path=Path("/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"),
    )

    notice = status.to_dict()["autonomous_runtime_notice"]
    assert notice["required"] is True
    assert notice["active_run_id"] == "run-stale"
    assert notice["notification_reason"] == "managed_runtime_degraded"


def test_autonomous_runtime_notice_does_not_claim_live_without_active_run_id(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    status = typed_surface.StudyRuntimeStatus.from_payload(_base_status_payload())
    status.record_runtime_liveness_audit(
        {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        }
    )

    module._record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=Path("/tmp/runtime"),
        launch_report_path=Path("/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"),
    )

    assert "autonomous_runtime_notice" not in status.to_dict()


def test_controller_owned_interaction_reply_message_prompts_write_stage_resume(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    payload = _base_status_payload()
    payload["reason"] = "quest_stale_decision_after_write_stage_ready"
    status = typed_surface.StudyRuntimeStatus.from_payload(payload)

    message = module._controller_owned_interaction_reply_message(status=status)

    assert message is not None
    assert "publication gate 已放行写作" in message
    assert "继续 write stage" in message


def test_force_restart_for_live_controller_reroute_supports_write_stage_ready(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    _patch_router(monkeypatch, module)
    quest_root = tmp_path / "runtime" / "quest-001"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-live-001",
                "same_fingerprint_auto_turn_count": 3,
                "pending_user_message_count": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = _base_status_payload()
    payload["reason"] = "quest_stale_decision_after_write_stage_ready"
    payload["quest_root"] = str(quest_root)
    status = typed_surface.StudyRuntimeStatus.from_payload(payload)
    status.record_runtime_liveness_audit(
        {
            "status": "live",
            "active_run_id": "run-live-001",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        }
    )
    status.record_publication_supervisor_state(
        {
            "status": "clear",
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "current_required_action": "continue_write_stage",
            "bundle_tasks_downstream_only": False,
            "deferred_downstream_actions": [],
            "controller_stage_note": "write stage is clear",
        }
    )

    assert module._should_skip_redundant_resume_for_live_controller_reroute(status=status) is True
    assert (
        module._should_force_restart_for_live_controller_reroute(
            status=status,
            context=SimpleNamespace(quest_root=quest_root),
        )
        is True
    )
