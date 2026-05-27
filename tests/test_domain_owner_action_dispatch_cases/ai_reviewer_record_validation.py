from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _required_publication_input_refs(study_root: Path) -> dict[str, object]:
    return {
        "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
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


def _write_ai_reviewer_dispatch(profile, study_root: Path, study_id: str) -> None:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)


def test_execute_dispatch_blocks_mechanical_publication_eval_as_ai_reviewer_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": _required_publication_input_refs(study_root),
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "ai_reviewer_required": True,
            },
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
        },
    )
    _write_ai_reviewer_dispatch(profile, study_root, study_id)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_record_missing"
    assert execution["next_owner"] == "ai_reviewer"
    assert execution["owner_record_requirements"]["required_record_fields"] == [
        "quality_assessment",
        "future_facing_limitations_plan",
    ]


def test_execute_dispatch_rejects_request_record_without_future_facing_limitations_plan(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": _required_publication_input_refs(study_root)},
            "ai_reviewer_record": {
                "eval_id": "publication-eval::request-record-missing-limitations",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
                "recommended_actions": [{"specificity_targets": [{"target_kind": "claim"}]}],
            },
        },
    )
    _write_ai_reviewer_dispatch(profile, study_root, study_id)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_record_incomplete"
    assert execution["missing_record_fields"] == [
        "future_facing_limitations_plan",
        "reviewer_operating_system",
    ]


def test_execute_dispatch_rejects_request_record_with_invalid_evaluation_scope(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    manuscript_path = study_root / "paper" / "draft.md"
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": _required_publication_input_refs(study_root)},
            "ai_reviewer_record": {
                "eval_id": "publication-eval::request-record-invalid-scope",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "evaluation_scope": {
                    "scope_id": "record_only_publication_eval_after_analysis_harmonization",
                    "record_only": True,
                },
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
                "future_facing_limitations_plan": [
                    {
                        "limitation": "Residual uncertainty is bounded.",
                        "impact_on_claim": "Claims must remain limited.",
                        "required_future_analysis_data_or_design": "Independent validation.",
                        "current_manuscript_wording_must_be_restrained": True,
                    }
                ],
            },
        },
    )
    _write_ai_reviewer_dispatch(profile, study_root, study_id)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_record_invalid"
    assert execution["invalid_record_fields"] == ["evaluation_scope"]
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["request_kind"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert production_request["record_must_consume_refs"] == [str(manuscript_path)]
    assert execution["next_required_actions"] == [
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]


def test_execute_dispatch_rejects_request_record_with_invalid_reviewer_operating_system(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    manuscript_path = study_root / "paper" / "draft.md"
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": _required_publication_input_refs(study_root)},
            "ai_reviewer_record": {
                "eval_id": "publication-eval::request-record-invalid-reviewer-os",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "evaluation_scope": "publication",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    dimension: {"status": "blocked", "summary": f"{dimension} requires hardening."}
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
                        "limitation": "Residual uncertainty is bounded.",
                        "impact_on_claim": "Claims must remain limited.",
                        "required_future_analysis_data_or_design": "Independent validation.",
                        "current_manuscript_wording_must_be_restrained": True,
                    }
                ],
                "reviewer_operating_system": {
                    "currentness_checks": {
                        "current_manuscript": {
                            "status": "current",
                            "manuscript_ref": str(manuscript_path),
                            "manuscript_digest": "sha256:" + "c" * 64,
                        }
                    }
                },
            },
        },
    )
    _write_ai_reviewer_dispatch(profile, study_root, study_id)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_record_invalid"
    assert execution["invalid_record_fields"] == ["reviewer_operating_system"]
    assert "reviewer_operating_system.contract_id" in "\n".join(execution["reviewer_operating_system_errors"])
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["request_kind"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert production_request["record_must_consume_refs"] == [str(manuscript_path)]
