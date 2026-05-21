from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_builds_ai_reviewer_routeback_record_from_current_prose_review(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    refs = {
        "manuscript": str(study_root / "paper" / "draft.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    for ref in refs.values():
        Path(ref).parent.mkdir(parents=True, exist_ok=True)
        if not Path(ref).exists():
            Path(ref).write_text("{}\n", encoding="utf-8")
    (study_root / "paper" / "draft.md").write_text("Current manuscript snapshot.\n", encoding="utf-8")
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_request_handoff_task",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested", "blocked_reason": None},
            "input_contract": {
                "required_refs": {
                    surface: {"surface": surface, "path": ref, "present": True, "valid": True}
                    for surface, ref in refs.items()
                }
            },
        },
    )
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = "sha256:" + "c" * 64
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json",
        {
            "surface": "medical_prose_review_request",
            "request_digest": request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": manuscript_digest},
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "medical_prose_review",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
                "request_ref": refs["medical_prose_review"].replace(
                    "medical_prose_review.json",
                    "medical_prose_review_request.json",
                ),
                "request_digest": request_digest,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "summary": "Methods reproducibility and treatment-gap denominator rules need write-owner repair.",
                "section_level_diagnosis": {
                    "methods": "Phenotype derivation, medication-source handling, and missingness rules remain underreported.",
                    "tables_and_figures": "Table 1 should become a real baseline table or be relabeled.",
                    "discussion": "Reduce repeated defensive language while preserving claim boundaries.",
                },
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Route back to write for manuscript-surface repair using current evidence.",
                },
            },
            "source_refs": [refs["medical_prose_review"], refs["manuscript"]],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::old-clean-migration",
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "emitted_at": "2026-05-17T00:00:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": refs["study_charter"],
                "charter_id": f"charter::{study_id}::old",
                "publication_objective": "Old clean migration projection.",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(study_root / "artifacts" / "runtime" / "escalation.json"),
                "main_result_ref": refs["evidence_ledger"],
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [refs["manuscript"]],
                "ai_reviewer_required": False,
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Old clean migration projection.",
                "stop_loss_pressure": "watch",
            },
            "quality_assessment": {
                "clinical_significance": {
                    "status": "underdefined",
                    "summary": "Old projection.",
                    "evidence_refs": [refs["study_charter"]],
                },
                "evidence_strength": {
                    "status": "underdefined",
                    "summary": "Old projection.",
                    "evidence_refs": [refs["evidence_ledger"]],
                },
                "novelty_positioning": {
                    "status": "underdefined",
                    "summary": "Old projection.",
                    "evidence_refs": [refs["study_charter"]],
                },
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "Old projection.",
                    "evidence_refs": [refs["manuscript"]],
                },
                "human_review_readiness": {
                    "status": "blocked",
                    "summary": "Old projection.",
                    "evidence_refs": [refs["review_ledger"]],
                },
            },
            "gaps": [
                {
                    "gap_id": "old-clean-migration",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "Old projection.",
                    "evidence_refs": [refs["manuscript"]],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "old-return-controller",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Old projection.",
                    "evidence_refs": [refs["manuscript"]],
                    "requires_controller_decision": True,
                }
            ],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))

    assert result["executed_count"] == 1
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert latest["quality_assessment"]["medical_journal_prose_quality"]["status"] == "partial"
    assert latest["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert latest["recommended_actions"][0]["route_target"] == "write"
    assert latest["future_facing_limitations_plan"][0]["current_manuscript_wording_must_be_restrained"] is True
    assert latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]["status"] == "current"
    assert latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]["route_target"] == "write"


