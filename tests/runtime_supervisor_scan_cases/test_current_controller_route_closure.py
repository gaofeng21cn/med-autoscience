from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_controller_route_ignores_closed_publication_work_unit(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.runtime_supervisor_scan_parts.current_truth_owner"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    work_unit_fingerprint = "publication-blockers::authority-sync"
    source_eval_id = f"publication-eval::{study_id}::{quest_id}::2026-05-12T10:36:52+00:00"
    study_root = write_study(tmp_path, study_id, quest_id=quest_id)
    publication_eval = {
        "schema_version": 1,
        "eval_id": source_eval_id,
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "submission_authority_sync_closure",
                    "lane": "controller",
                    "summary": "Regenerate submission authority signatures, then replay the publication gate.",
                },
            }
        ],
    }
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "authority-sync-route",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "finalize",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
                "summary": "Regenerate submission authority signatures, then replay the publication gate.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "quest_id": quest_id,
            "status": "done",
            "work_unit": {
                "unit_id": "submission_authority_sync_closure",
                "lane": "controller",
            },
            "unit_statuses": [
                {"unit_id": "create_submission_minimal_package", "status": "ok"},
                {"unit_id": "sync_submission_minimal_delivery", "status": "skipped_authority_not_settled"},
            ],
            "gate_replay_status": "clear",
        },
    )

    assert module.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    ) is None
