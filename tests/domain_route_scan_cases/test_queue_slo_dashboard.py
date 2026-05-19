from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_aggregates_queue_slo_from_repeat_action_fingerprints(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-risk")
    quest_root = profile.runtime_root / "quest-risk"

    monkeypatch.setattr(
        module,
        "_utc_now",
        lambda: "2026-05-04T06:00:00+00:00",
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_domain_route_scan",
            "schema_version": 1,
            "generated_at": "2026-05-04T00:00:00+00:00",
            "studies": [
                {
                    "study_id": "001-risk",
                    "action_queue": [
                        {
                            "action_id": (
                                "supervisor-action::001-risk::"
                                "publication_gate_specificity_required::"
                                "publication_gate_specificity_required"
                            ),
                            "action_type": "publication_gate_specificity_required",
                            "status": "queued",
                            "fingerprint": "publication_gate_specificity_required::publication_gate_specificity_required",
                            "queued_first_seen_at": "2026-05-04T00:00:00+00:00",
                            "owner_pickup": {
                                "state": "pending",
                                "owner": "publication_gate",
                                "first_seen_at": "2026-05-04T00:00:00+00:00",
                                "pickup_overdue": True,
                            },
                            "consumption": {
                                "state": "unconsumed",
                                "first_seen_at": "2026-05-04T00:00:00+00:00",
                            },
                        }
                    ],
                }
            ],
            "action_queue": [
                {
                    "study_id": "001-risk",
                    "action_id": (
                        "supervisor-action::001-risk::"
                        "publication_gate_specificity_required::"
                        "publication_gate_specificity_required"
                    ),
                    "fingerprint": "publication_gate_specificity_required::publication_gate_specificity_required",
                    "queued_first_seen_at": "2026-05-04T00:00:00+00:00",
                    "status": "queued",
                    "owner_pickup": {
                        "state": "pending",
                        "owner": "publication_gate",
                        "first_seen_at": "2026-05-04T00:00:00+00:00",
                        "pickup_overdue": True,
                    },
                    "consumption": {
                        "state": "unconsumed",
                        "first_seen_at": "2026-05-04T00:00:00+00:00",
                    },
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-risk",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "publication_gate_specificity_required",
            "execution_owner_guard": {"supervisor_only": True},
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_gate"},
                "blockers": ["generic blocker"],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "current_blockers": ["generic blocker"],
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    action = study["action_queue"][0]
    assert action["fingerprint"] == "publication_gate_specificity_required::publication_gate_specificity_required"
    assert action["queue_age_hours"] == 6.0
    assert action["repeat_fingerprint"]["consecutive_scan_count"] == 2
    assert action["repeat_fingerprint"]["duration_hours"] == 6.0
    assert action["owner_pickup"] == {
        "state": "overdue",
        "owner": "publication_gate",
        "first_seen_at": "2026-05-04T00:00:00+00:00",
        "overdue_after_hours": 2,
        "duration_hours": 6.0,
        "pickup_overdue": True,
    }
    assert action["consumption"] == {
        "state": "attention_required",
        "first_seen_at": "2026-05-04T00:00:00+00:00",
        "unconsumed_duration_hours": 6.0,
        "attention_required_after_hours": 6,
        "developer_supervisor_attention_required": True,
    }
    assert study["owner_pickup_overdue"] is True
    assert study["developer_supervisor_attention_required"] is True
    assert study["scan_delta"]["owner_pickup_overdue_count"] == 1
    assert study["scan_delta"]["developer_supervisor_attention_required_count"] == 1
    assert result["queue_history"]["owner_pickup_overdue_count"] == 1
    assert result["queue_history"]["developer_supervisor_attention_required_count"] == 1
    assert result["queue_history"]["repeat_fingerprints"][0]["fingerprint"] == action["fingerprint"]

