from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.runtime_status_summary"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _minimal_payload(study_root: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "summary_id": "runtime-status::001-risk::quest-001::2026-04-20T04:46:03+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "generated_at": "2026-04-20T04:46:03+00:00",
        "runtime_status_ref": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
        "runtime_artifact_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        "runtime_escalation_record_ref": str(
            study_root.parents[1]
            / "ops"
            / "med-deepscientist"
            / "runtime"
            / "quests"
            / "quest-001"
            / "artifacts"
            / "reports"
            / "escalation"
            / "runtime_escalation_record.json"
        ),
        "runtime_watch_ref": str(
            study_root.parents[1]
            / "ops"
            / "med-deepscientist"
            / "runtime"
            / "quests"
            / "quest-001"
            / "artifacts"
            / "reports"
            / "runtime_watch"
            / "latest.json"
        ),
        "health_status": "escalated",
        "runtime_decision": "blocked",
        "runtime_reason": "resume_request_failed",
        "recovery_action_mode": "refresh_supervision",
        "supervisor_tick_status": "stale",
        "current_required_action": "human_confirmation_required",
        "controller_stage_note": "当前先恢复监管，再决定是否继续自动推进。",
        "status_summary": "托管运行已经进入升级告警，MAS 正在协调恢复动作。",
        "next_action_summary": "先恢复外环监管，再决定是否继续自动推进。",
        "needs_human_intervention": True,
    }


def test_resolve_runtime_status_summary_ref_defaults_to_runtime_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_runtime_status_summary_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "runtime" / "runtime_status_summary.json").resolve()


def test_read_runtime_status_summary_reads_stable_runtime_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    summary_path = study_root / "artifacts" / "runtime" / "runtime_status_summary.json"
    payload = _minimal_payload(study_root)
    _write_json(summary_path, payload)

    resolved = module.read_runtime_status_summary(study_root=study_root)

    assert resolved == payload


def test_resolve_runtime_status_summary_ref_rejects_controller_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    controller_ref = study_root / "artifacts" / "controller" / "controller_summary.json"

    with pytest.raises(ValueError, match="stable runtime artifact"):
        module.resolve_runtime_status_summary_ref(study_root=study_root, ref=controller_ref)


def test_materialize_runtime_status_summary_writes_stable_runtime_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    written_ref = module.materialize_runtime_status_summary(
        study_root=study_root,
        summary=module.build_runtime_status_summary(
            study_id="001-risk",
            quest_id="quest-001",
            generated_at="2026-04-20T04:46:03+00:00",
            runtime_status_ref=str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
            runtime_artifact_ref=str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            runtime_escalation_record_ref=str(
                study_root.parents[1]
                / "ops"
                / "med-deepscientist"
                / "runtime"
                / "quests"
                / "quest-001"
                / "artifacts"
                / "reports"
                / "escalation"
                / "runtime_escalation_record.json"
            ),
            runtime_watch_ref=str(
                study_root.parents[1]
                / "ops"
                / "med-deepscientist"
                / "runtime"
                / "quests"
                / "quest-001"
                / "artifacts"
                / "reports"
                / "runtime_watch"
                / "latest.json"
            ),
            health_status="live",
            runtime_decision="resume",
            runtime_reason="quest_already_running",
            recovery_action_mode="continue_or_relaunch",
            supervisor_tick_status="fresh",
            current_required_action="supervise_runtime_only",
            controller_stage_note="当前先继续监督托管运行。",
            status_summary="托管运行健康在线，当前由 MAS 持续监督。",
            next_action_summary="继续监督当前托管运行。",
            needs_human_intervention=False,
        ),
    )

    summary_path = study_root / "artifacts" / "runtime" / "runtime_status_summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))

    assert written_ref == {
        "summary_id": "runtime-status::001-risk::quest-001::2026-04-20T04:46:03+00:00",
        "artifact_path": str(summary_path.resolve()),
    }
    assert payload["health_status"] == "live"
    assert payload["runtime_decision"] == "resume"
    assert payload["status_summary"] == "托管运行健康在线，当前由 MAS 持续监督。"
    assert payload["next_action_summary"] == "继续监督当前托管运行。"
    assert payload["needs_human_intervention"] is False
