from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
