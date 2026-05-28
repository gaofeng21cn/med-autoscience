from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
    }


def test_materialize_domain_action_requests_writes_quality_repair_request_to_canonical_requests_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dpcc")
    route = _owner_route(
        study_id=study_id,
        quest_id="quest-dpcc",
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": "quest-dpcc",
                    "action_type": "run_quality_repair_batch",
                    "authority": "observability_only",
                    "owner": "write",
                    "recommended_owner": "write",
                    "reason": "manuscript_story_surface_delta_missing",
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "run_quality_repair_batch",
                        "authority": "observability_only",
                        "request_owner": "write",
                        "owner_route": route,
                    },
                },
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    canonical_request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "quality_repair_batch"
        / "latest.json"
    )
    legacy_consumer_request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "run_quality_repair_batch.json"
    )
    task = result["request_tasks"][0]
    assert task["dispatch_status"] == "applied"
    assert task["request_packet_ref"] == "artifacts/supervision/requests/quality_repair_batch/latest.json"
    assert task["refs"]["request_packet_path"] == str(canonical_request_path)
    assert canonical_request_path.is_file()
    assert not legacy_consumer_request_path.exists()
    request_packet = json.loads(canonical_request_path.read_text(encoding="utf-8"))
    assert request_packet["request_kind"] == "run_quality_repair_batch"
    assert request_packet["request_owner"] == "write"
