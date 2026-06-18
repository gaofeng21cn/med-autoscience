from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from tests.domain_action_request_materializer_cases.ai_reviewer_currentness_helpers import (
    disable_progress_projection as _disable_progress_projection,
)
from tests.domain_action_request_materializer_cases.ai_reviewer_currentness_helpers import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.ai_reviewer_currentness_helpers import write_json as _write_json
from tests.reviewer_os_fixture_helpers import (
    current_manuscript_routeback_record,
    current_manuscript_routeback_reviewer_os,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_materialize_domain_action_requests_refreshes_existing_ai_reviewer_request_to_latest_valid_record_without_new_queue_task(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript with numeric results and 95% CIs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    os.utime(manuscript_path, (0, 0))
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    old_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    new_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260522T203041Z_publication_eval_record.json"
    )
    quality_assessment = {
        dimension: {"status": "blocked", "summary": f"{dimension} remains blocked."}
        for dimension in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "medical_journal_prose_quality",
            "human_review_readiness",
        )
    }
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}::{quest_id}",
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(old_record_path.resolve()),
                "required_currentness_refs": [str(manuscript_path.resolve())],
                "missing_currentness_refs": [str(manuscript_path.resolve())],
                "currentness_evidence": {
                    "surface_kind": "ai_reviewer_record_currentness_evidence",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                },
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {
                        "path": str(study_root / "paper" / "claim_evidence_map.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_prose_review": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                        "present": True,
                        "valid": True,
                    },
                    "publication_gate_projection": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        "present": True,
                        "valid": True,
                    },
                }
            },
        },
    )
    _write_json(
        new_record_path,
        current_manuscript_routeback_record(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            study_id=study_id,
            quest_id=quest_id,
            eval_id="publication-eval::002::quest::2026-05-22T20:30:41+00:00::ai-reviewer",
            emitted_at="2026-05-22T20:30:41+00:00",
        )
        | {"quality_assessment": quality_assessment},
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id}],
            "action_queue": [],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    original_request = json.loads(request_path.read_text(encoding="utf-8"))
    assert result["ai_reviewer_request_refresh_count"] == 1
    assert result["ai_reviewer_request_refreshes"][0]["refresh_status"] == "refreshed"
    assert result["ai_reviewer_request_refreshes"][0]["publication_eval_record_ref"] == str(new_record_path.resolve())
    assert original_request["request_lifecycle"]["blocked_reason"] == (
        "ai_reviewer_record_stale_after_current_manuscript"
    )
    assert original_request["request_lifecycle"]["stale_record_ref"] == str(old_record_path.resolve())
    assert "publication_eval_record_ref" not in original_request
    assert "ai_reviewer_record" not in original_request


def test_materialize_current_ai_reviewer_record_work_unit_routes_to_publication_owner_when_current(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    review_manuscript_path = study_root / "paper" / "build" / "review_manuscript.md"
    manuscript_text = "# Draft\n\nCurrent story with reproducible numeric results and 95% CIs.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    review_manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::002::quest::2026-05-26T08:00:00+00:00::ai-reviewer"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260526T080000Z_publication_eval_record.json"
    )
    record_payload = {
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-26T08:00:00+00:00",
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
        "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            eval_id=eval_id,
        ),
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
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "surface": "quality_repair_execution_evidence",
            "schema_version": 1,
            "source_eval_id": eval_id,
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "manuscript_surface_hygiene": {
                "story_surface_delta_required": True,
                "story_surface_delta_present": True,
                "story_surface_delta_refs": [
                    str(manuscript_path.resolve()),
                    str(review_manuscript_path.resolve()),
                ],
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {"status": "current", "source_eval_id": eval_id},
    )
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
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
            "runtime_health_epoch": "runtime-health-dm002-materialization",
            "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
            "source_refs": {
                "runtime_health_epoch": "runtime-health-dm002-materialization",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
                "source_eval_id": eval_id,
            },
        }
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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

    assert result["request_task_count"] == 1
    assert result["domain_progress_transition_request_count"] == 1
    request = result["request_tasks"][0]
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert request["action_type"] == "run_gate_clearing_batch"
    assert request["request_owner"] == "gate_clearing_batch"
    assert request["reason"] == "publication_owner_materialization_required"
    assert request["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert dispatch["action_type"] == "run_gate_clearing_batch"
    assert dispatch["next_executable_owner"] == "gate_clearing_batch"
    assert dispatch["required_output_surface"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert dispatch["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    source_refs = dispatch["owner_route"]["source_refs"]
    assert source_refs["work_unit_id"] == work_unit_id
    assert source_refs["materialized_work_unit_id"] == "publication_gate_replay"
    assert source_refs["materialized_from_action_type"] == "run_quality_repair_batch"
    assert source_refs["bridge_authority"] == "domain_action_request_materializer_publication_owner_bridge"
    assert source_refs["bridged_from_owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert source_refs["bridged_from_idempotency_key"] == route["idempotency_key"]
    assert dispatch["source_action"]["controller_work_unit_id"] == work_unit_id
    assert dispatch["source_action"]["materialization_decision"] == "publication_gate_replay"
    assert dispatch["source_action"]["reviewer_record_ref"] == str(record_path.resolve())
    assert dispatch["source_action"]["story_surface_delta_refs"] == [
        str(manuscript_path.resolve()),
        str(review_manuscript_path.resolve()),
    ]


def test_materialize_current_ai_reviewer_record_work_unit_routes_missing_currentness_to_ai_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Draft\n\nCurrent story changed after review.\n", encoding="utf-8")
    work_unit_id = "materialize_current_ai_reviewer_record_through_mas_owner_surface"
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
            "runtime_health_epoch": "runtime-health-dm002-materialization",
            "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
            "source_refs": {
                "runtime_health_epoch": "runtime-health-dm002-materialization",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
            },
        }
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "required_currentness_refs": [str(manuscript_path.resolve())],
            },
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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
    dispatch = result["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatches"][0]
    assert request["action_type"] == "return_to_ai_reviewer_workflow"
    assert request["request_owner"] == "ai_reviewer"
    assert request["reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert dispatch["source_action"]["materialization_decision"] == "ai_reviewer_currentness_required"
    assert dispatch["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
