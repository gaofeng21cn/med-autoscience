from __future__ import annotations

import importlib
from pathlib import Path

from tests.reviewer_os_fixture_helpers import claim_evidence_map_payload, evidence_ledger_payload
from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_hands_off_ai_reviewer_record_production_when_request_record_stale_after_current_manuscript(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260521T213722Z_publication_eval_record.json"
    )
    manuscript_path = study_root / "paper" / "draft.md"
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "stale_record_ref": str(stale_record_path),
                "required_currentness_refs": [str(manuscript_path)],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path), "present": True, "valid": True},
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
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
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
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "ai_reviewer_record_stale_after_current_manuscript",
            "owner_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            },
        }
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
            owner_route=route,
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert execution["stale_record_ref"] == str(stale_record_path)
    assert execution["required_currentness_refs"] == [str(manuscript_path)]
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["request_kind"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    assert production_request["record_must_consume_refs"] == [str(manuscript_path)]
    assert execution["next_required_actions"] == [
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]
    handoff = execution["ai_reviewer_record_worker_handoff"]
    assert handoff["surface"] == "default_executor_dispatch_request"
    assert handoff["dispatch_status"] == "ready"
    assert handoff["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert handoff["next_executable_owner"] == "ai_reviewer"
    assert handoff["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    assert handoff["ai_reviewer_record_production_request"] == production_request
    assert handoff["owner_route"]["next_owner"] == "ai_reviewer"
    assert handoff["owner_route"]["owner_reason"] == "ai_reviewer_record_stale_after_current_manuscript"
    assert handoff["owner_route"]["source_refs"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    )
    assert handoff["prompt_contract"]["allowed_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]
    assert "artifacts/publication_eval/latest.json" in handoff["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in handoff["forbidden_surfaces"]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_routes_claim_evidence_alignment_blocker_to_write_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    paper_root = study_root / "paper"
    manuscript_path = paper_root / "draft.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("# Manuscript\n\nCurrent claim text.\n", encoding="utf-8")
    evidence_path = paper_root / "evidence_ledger.json"
    claim_map_path = paper_root / "claim_evidence_map.json"
    _write_json(claim_map_path, claim_evidence_map_payload(evidence_ledger_ref=str(evidence_path)))
    _write_json(evidence_path, evidence_ledger_payload(evidence_ledger_ref=str(evidence_path), evidence_id="renamed"))
    _write_json(paper_root / "review" / "review_ledger.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "controller" / "study_charter.json", {"schema_version": 1})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json", {"schema_version": 1})
    _write_json(study_root / "artifacts" / "publication_gate" / "latest.json", {"schema_version": 1})
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested", "blocked_reason": None},
            "ai_reviewer_record": {
                "schema_version": 1,
                "eval_id": "publication-eval::dm002::2026-05-24T20:09:53+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    key: {"status": "ready", "summary": "ready", "evidence_refs": [str(manuscript_path)]}
                    for key in (
                        "clinical_significance",
                        "evidence_strength",
                        "novelty_positioning",
                        "medical_journal_prose_quality",
                        "human_review_readiness",
                    )
                },
                "future_facing_limitations_plan": [{"limitation": "none"}],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path)},
                    "evidence_ledger": {"path": str(evidence_path)},
                    "review_ledger": {"path": str(paper_root / "review" / "review_ledger.json")},
                    "study_charter": {"path": str(study_root / "artifacts" / "controller" / "study_charter.json")},
                    "medical_manuscript_blueprint": {"path": str(paper_root / "medical_manuscript_blueprint.json")},
                    "claim_evidence_map": {"path": str(claim_map_path)},
                    "medical_prose_review": {
                        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")
                    },
                    "publication_gate_projection": {
                        "path": str(study_root / "artifacts" / "publication_gate" / "latest.json")
                    },
                }
            },
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
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        lambda **_: (_ for _ in ()).throw(ValueError("claim_evidence_alignment.status must be ready")),
    )

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
    assert execution["blocked_reason"] == "claim_evidence_alignment_required"
    assert execution["next_owner"] == "write"
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["owner_result"]["claim_evidence_alignment"]["status"] == "blocked"
    assert execution["owner_result"]["missing_evidence_item_refs"] == ["evidence-primary"]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
