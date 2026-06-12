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
from tests.reviewer_os_fixture_helpers import (
    claim_evidence_map_payload,
    current_manuscript_routeback_reviewer_os,
    evidence_ledger_payload,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_rebinds_record_production_to_eval_owned_medical_prose_review(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    body_authority_prose_review = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_prose_review.json"
    )
    stable_prose_review = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    _write_json(
        body_authority_prose_review,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        },
    )
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": "sha256:" + "1" * 64,
            "manuscript": {"path": str(manuscript_path), "digest": "sha256:" + "2" * 64},
        },
    )
    _write_json(
        stable_prose_review,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "ai_reviewer_required": False,
                "request_ref": str(request_path),
                "request_digest": "sha256:" + "1" * 64,
                "manuscript_ref": str(manuscript_path),
                "manuscript_digest": "sha256:" + "2" * 64,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "study_id": study_id,
            "quest_id": study_id,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "stale_record_ref": "publication-eval::stale-record",
                "required_currentness_refs": [str(manuscript_path), str(stable_prose_review)],
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
                    "medical_prose_review": {
                        "path": str(body_authority_prose_review),
                        "present": True,
                        "valid": True,
                    },
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "return_to_ai_reviewer_workflow",
            "owner_reason": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            },
        }
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
    execution = result["executions"][0]
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["required_input_refs"]["medical_prose_review"] == str(stable_prose_review.resolve())
    payload_ref = production_request["owner_callable_payload_ref"]
    payload = json.loads(Path(payload_ref).read_text(encoding="utf-8"))
    assert payload["required_input_refs"]["medical_prose_review"] == str(stable_prose_review.resolve())


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
    manuscript_text = "# Manuscript\n\nCurrent claim text.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
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
                "evaluation_scope": "publication",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "source_refs": [str(manuscript_path), str(evidence_path), str(claim_map_path)],
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
                "future_facing_limitations_plan": [
                    {
                        "limitation": "Recorded treatment coverage may be incomplete.",
                        "impact_on_claim": "Coverage claims remain documentation-aware.",
                        "required_future_analysis_data_or_design": "Link dispensing records.",
                        "current_manuscript_wording_must_be_restrained": True,
                    }
                ],
                "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
                    study_root=study_root,
                    manuscript_path=manuscript_path,
                    manuscript_text=manuscript_text,
                    eval_id="publication-eval::dm002::2026-05-24T20:09:53+00:00",
                ),
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
