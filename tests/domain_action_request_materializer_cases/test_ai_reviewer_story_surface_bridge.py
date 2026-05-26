from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def test_materialize_current_ai_reviewer_record_work_unit_bridges_runtime_route_to_story_surface_writer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_text = "# Draft\n\nCurrent story still needs a canonical story-surface delta.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    review_manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::002::quest::2026-05-26T08:30:00+00:00::ai-reviewer"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260526T083000Z_publication_eval_record.json"
    )
    record_payload = {
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-26T08:30:00+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(manuscript_path.resolve()), str(review_manuscript_path.resolve())],
        },
        "quality_assessment": {
            dimension: {"status": "ready", "summary": f"{dimension} current."}
            for dimension in (
                "clinical_significance",
                "evidence_strength",
                "novelty_positioning",
                "medical_journal_prose_quality",
                "human_review_readiness",
            )
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "External-validation limitations remain explicit.",
                "impact_on_claim": "Claims stay restrained.",
                "required_future_analysis_data_or_design": "None for this replay.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": {
            "currentness_checks": {
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "draft": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
                "review_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(review_manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                },
            }
        },
    }
    _write_json(record_path, record_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "assessment_written", "blocked_reason": None},
            "publication_eval_record_ref": str(record_path.resolve()),
            "ai_reviewer_record": record_payload,
        },
    )
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    work_unit_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": "truth-event-000022",
            "route_epoch": "truth-event-000022",
            "source_fingerprint": "truth-snapshot::dm002-current",
            "runtime_health_epoch": "runtime-health-event-006239",
            "work_unit_fingerprint": work_unit_fingerprint,
            "idempotency_key": "owner-route::dm002::runtime-handoff",
            "source_refs": {
                "study_truth_epoch": "truth-event-000022",
                "runtime_health_epoch": "runtime-health-event-006239",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "truth_epoch": "truth-event-000022",
                    "runtime_health_epoch": "runtime-health-event-006239",
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                },
            },
        }
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "request_owner": "write",
                    "reason": "quest_waiting_opl_runtime_owner_route",
                    "next_work_unit": work_unit_id,
                    "controller_work_unit_id": work_unit_id,
                    "executable_work_unit": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "required_output_surface": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                    "owner_route": route,
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    request = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert request["action_type"] == "run_quality_repair_batch"
    assert request["request_owner"] == "write"
    assert request["reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_story_surface_bridge"
    assert source_refs["bridged_from_owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert source_refs["bridged_from_idempotency_key"] == route["idempotency_key"]
    assert source_refs["work_unit_id"] == work_unit_id
    assert source_refs["materialized_work_unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert dispatch["source_action"]["materialization_decision"] == "story_surface_delta_or_typed_blocker_required"
