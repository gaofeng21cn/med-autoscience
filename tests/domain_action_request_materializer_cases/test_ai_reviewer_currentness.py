from __future__ import annotations

import hashlib
import importlib
import json
import os
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


def test_materialize_domain_action_requests_keeps_current_prose_routeback_dispatch_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = "quest-dpcc"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_assessment_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "reason": "ai_reviewer_assessment_required",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": str(study_root / "paper" / "draft.md"),
                "manuscript_digest": "sha256:" + "b" * 64,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Repair medical manuscript prose against current evidence.",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::003::stale",
            "assessment_provenance": {"owner": "ai_reviewer"},
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                }
            ],
            "action_queue": [action],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "repeat_suppressed",
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
            "prompt_contract": {
                "do_not_repeat": True,
                "repeat_suppression_key": route["source_fingerprint"],
            },
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["repeat_suppressed"] is False
    assert dispatch["blocked_reason"] is None
    assert result["repeat_suppressed_count"] == 0


def test_materialize_ai_reviewer_dispatch_inherits_owner_reason_forbidden_surfaces(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    dispatch_contract = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    owner_forbidden_surfaces = [
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_manuscript",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route["owner_reason_contract"] = {
        "registered": True,
        "reason": "ai_reviewer_record_stale_after_current_manuscript",
        "owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "required_output": "artifacts/publication_eval/latest.json",
        "forbidden_surfaces": [
            "manuscript/**",
            "current_package/**",
            "paper/current_package/**",
            "manuscript/current_package/**",
            *owner_forbidden_surfaces,
        ],
        "priority_class": "ai_reviewer_currentness",
    }
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
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "ai_reviewer_record_stale_after_current_manuscript",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "owner_route": route,
                    },
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

    dispatch = result["default_executor_dispatches"][0]
    prompt_forbidden_surfaces = set(dispatch["prompt_contract"]["forbidden_surfaces"])
    for surface in owner_forbidden_surfaces:
        assert surface in prompt_forbidden_surfaces
    assert dispatch_contract.prompt_contract_error(
        dispatch["prompt_contract"],
        forbidden_surfaces=module.FORBIDDEN_SURFACES,
    ) is None
    persisted = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ).read_text(encoding="utf-8")
    )
    assert set(persisted["prompt_contract"]["forbidden_surfaces"]) == prompt_forbidden_surfaces


def test_materialize_domain_action_requests_refreshes_existing_ai_reviewer_request_to_latest_valid_record_without_new_queue_task(
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
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
                    "review_ledger": {"path": str(study_root / "paper" / "review" / "review_ledger.json"), "present": True, "valid": True},
                    "study_charter": {"path": str(study_root / "artifacts" / "controller" / "study_charter.json"), "present": True, "valid": True},
                    "medical_manuscript_blueprint": {"path": str(study_root / "paper" / "medical_manuscript_blueprint.json"), "present": True, "valid": True},
                    "claim_evidence_map": {"path": str(study_root / "paper" / "claim_evidence_map.json"), "present": True, "valid": True},
                    "medical_prose_review": {"path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"), "present": True, "valid": True},
                    "publication_gate_projection": {"path": str(study_root / "artifacts" / "publication_eval" / "latest.json"), "present": True, "valid": True},
                }
            },
        },
    )
    _write_json(
        new_record_path,
        {
            "eval_id": "publication-eval::002::quest::2026-05-22T20:30:41+00:00::ai-reviewer",
            "study_id": study_id,
            "quest_id": quest_id,
            "emitted_at": "2026-05-22T20:30:41+00:00",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
                "source_refs": [str(manuscript_path.resolve())],
            },
            "quality_assessment": quality_assessment,
            "future_facing_limitations_plan": [
                {
                    "limitation": "Current manuscript remains below publication quality.",
                    "impact_on_claim": "The external-validation story must stay restrained.",
                    "required_future_analysis_data_or_design": "Repair prose and display alignment before package refresh.",
                    "current_manuscript_wording_must_be_restrained": True,
                }
            ],
            "reviewer_operating_system": {
                "currentness_checks": {
                    "manuscript": {
                        "status": "current",
                        "manuscript_ref": str(manuscript_path.resolve()),
                        "manuscript_digest": _sha256_text(manuscript_text),
                    }
                }
            },
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
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

    refreshed = json.loads(request_path.read_text(encoding="utf-8"))
    assert result["ai_reviewer_request_refresh_count"] == 1
    assert result["ai_reviewer_request_refreshes"][0]["refresh_status"] == "refreshed"
    assert result["ai_reviewer_request_refreshes"][0]["publication_eval_record_ref"] == str(new_record_path.resolve())
    assert refreshed["request_lifecycle"]["blocked_reason"] is None
    assert "stale_record_ref" not in refreshed["request_lifecycle"]
    assert "required_currentness_refs" not in refreshed["request_lifecycle"]
    assert refreshed["publication_eval_record_ref"] == str(new_record_path.resolve())
    assert refreshed["ai_reviewer_record"]["eval_id"] == "publication-eval::002::quest::2026-05-22T20:30:41+00:00::ai-reviewer"
