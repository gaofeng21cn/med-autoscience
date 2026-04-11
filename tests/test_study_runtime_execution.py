from __future__ import annotations

import importlib
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
