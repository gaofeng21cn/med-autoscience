from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.reviewer_os_fixture_helpers import (
    current_manuscript_routeback_reviewer_os,
    current_routeback_future_plan,
    current_routeback_quality_assessment,
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


def test_execute_dispatch_rejects_request_record_with_item_only_future_facing_limitations_plan(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_text = "# Current manuscript\n\nCurrent AI reviewer route-back manuscript snapshot.\n"
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::request-record-item-only-limitations"
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": _required_publication_input_refs(study_root)},
            "ai_reviewer_record": {
                "eval_id": eval_id,
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "evaluation_scope": "publication",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    dimension: {
                        "status": "blocked" if dimension == "medical_journal_prose_quality" else "ready",
                        "summary": f"{dimension} was reviewed against the current manuscript.",
                        "evidence_refs": [str(manuscript_path)],
                    }
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
                        "item": "Keep interpretation limited to the current descriptive evidence and rerun review after repair."
                    }
                ],
                "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
                    study_root=study_root,
                    manuscript_path=manuscript_path,
                    manuscript_text=manuscript_text,
                    eval_id=eval_id,
                ),
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
    assert execution["invalid_record_fields"] == ["future_facing_limitations_plan"]
    assert "future_facing_limitations_plan[0].limitation" in "\n".join(
        execution["future_facing_limitations_plan_errors"]
    )


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


def test_execute_dispatch_materializes_handoff_for_incomplete_current_ai_reviewer_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Current manuscript\n\nCurrent AI reviewer route-back manuscript snapshot.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": _required_publication_input_refs(study_root)},
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::current-incomplete",
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "emitted_at": "2026-05-30T03:45:22+00:00",
            "evaluation_scope": "publication",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "blocked",
                    "summary": "Reviewer operating system trace must be rebuilt.",
                    "evidence_refs": [str(manuscript_path)],
                }
            },
            "future_facing_limitations_plan": [
                {
                    "limitation": "The current manuscript needs record production trace hardening.",
                    "impact_on_claim": "Claims must remain bounded until a traced AI reviewer record exists.",
                    "required_future_analysis_data_or_design": "Repeat the AI reviewer record-production workflow.",
                    "current_manuscript_wording_must_be_restrained": True,
                }
            ],
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

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["next_owner"] == "ai_reviewer"
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["request_kind"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert production_request["stale_record_ref"] == "publication-eval::current-incomplete"
    assert production_request["record_must_consume_refs"] == [str(manuscript_path)]
    payload_ref = Path(production_request["owner_callable_payload_ref"])
    assert payload_ref.is_file()
    payload = json.loads(payload_ref.read_text(encoding="utf-8"))
    assert payload["surface"] == "ai_reviewer_record_payload_authoring_target"
    assert payload["record_payload"] is None
    assert payload["owner_callable_command"].startswith("medautosci publication materialize-ai-reviewer-record ")
    assert Path(execution["ai_reviewer_record_worker_handoff_path"]).is_file()


def test_execute_dispatch_materializes_handoff_when_request_record_only_needs_production_trace(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Current manuscript\n\nCurrent AI reviewer route-back manuscript snapshot.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": _required_publication_input_refs(study_root)},
            "ai_reviewer_record": {
                "schema_version": 1,
                "eval_id": "publication-eval::request-record-needs-trace",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "emitted_at": "2026-05-30T03:45:22+00:00",
                "evaluation_scope": "publication",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": current_routeback_quality_assessment(
                    manuscript_ref=str(manuscript_path),
                    evidence_ref=str(study_root / "paper" / "evidence_ledger.json"),
                    review_ref=str(study_root / "paper" / "review" / "review_ledger.json"),
                ),
                "future_facing_limitations_plan": current_routeback_future_plan(),
                "recommended_actions": [{"action_type": "route_back_same_line"}],
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

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["stale_record_ref"] == "publication-eval::request-record-needs-trace"
    assert production_request["request_kind"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    payload = json.loads(Path(production_request["owner_callable_payload_ref"]).read_text(encoding="utf-8"))
    assert payload["record_payload"] is None
    assert payload["record_payload_contract"]["record_payload_must_be_authored_by_ai_reviewer"] is True


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
