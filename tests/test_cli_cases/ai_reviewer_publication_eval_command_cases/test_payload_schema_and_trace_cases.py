from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def test_ai_reviewer_record_dry_run_rejects_schema_invalid_authoring_target(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    paper_root = study_root / "paper"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_path = paper_root / "draft.md"
    evidence_path = paper_root / "evidence_ledger.json"
    review_path = paper_root / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, manuscript_path, evidence_path, review_path, charter_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "manuscript": {"path": str(manuscript_path.resolve())},
                        "evidence_ledger": {"path": str(evidence_path.resolve())},
                        "review_ledger": {"path": str(review_path.resolve())},
                        "study_charter": {"path": str(charter_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [str(evidence_path.resolve())],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::"
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                ),
            },
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "stale_record_ref": current_record_ref,
            "required_currentness_refs": [str(evidence_path.resolve())],
            "required_input_refs": {
                "manuscript": str(manuscript_path.resolve()),
                "evidence_ledger": str(evidence_path.resolve()),
                "review_ledger": str(review_path.resolve()),
                "study_charter": str(charter_path.resolve()),
            },
            "record_payload": {
                "schema_version": 1,
                "eval_id": "publication-eval::002::current",
                "study_id": study_id,
                "quest_id": study_id,
                "emitted_at": "2026-06-29T00:00:00Z",
                "evaluation_scope": "publication",
                "charter_context_ref": {
                    "ref": str(charter_path.resolve()),
                    "charter_id": f"charter::{study_id}::v1",
                    "publication_objective": "Evaluate current inputs.",
                },
                "runtime_context_refs": {
                    "runtime_escalation_ref": str((study_root / "runtime_escalation.json").resolve()),
                    "main_result_ref": str(evidence_path.resolve()),
                    "unexpected_extra_ref": str(evidence_path.resolve()),
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(paper_root.resolve()),
                    "submission_minimal_ref": str((paper_root / "submission_minimal.json").resolve()),
                },
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "source_refs": [str(evidence_path.resolve())],
                    "ai_reviewer_required": False,
                    "mechanical_projection_used_as_quality_authority": False,
                },
                "verdict": {
                    "overall_verdict": "blocked",
                    "primary_claim_status": "partial",
                    "summary": "Current record is not submission-ready.",
                    "stop_loss_pressure": "watch",
                },
                "gaps": [
                    {
                        "gap_id": "schema-invalid-extra-runtime-ref",
                        "gap_type": "delivery",
                        "severity": "must_fix",
                        "summary": "The authoring target must fail in dry-run before materialization.",
                        "evidence_refs": [str(evidence_path.resolve())],
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "route-controller",
                        "action_type": "return_to_controller",
                        "priority": "now",
                        "reason": "Schema-invalid authoring target cannot be consumed.",
                        "evidence_refs": [str(evidence_path.resolve())],
                        "requires_controller_decision": True,
                    }
                ],
                "reviewer_operating_system": {
                    "input_bundle": {
                        "manuscript": str(manuscript_path.resolve()),
                        "evidence_ledger": str(evidence_path.resolve()),
                        "review_ledger": str(review_path.resolve()),
                        "study_charter": str(charter_path.resolve()),
                    }
                },
            },
        },
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "record_payload_schema_invalid"
    assert result["payload_guard"]["matched"] is True
    assert result["record_schema_guard"]["matched"] is False
    assert result["record_schema_guard"]["error"]
    assert result["written_files"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_build_production_trace_covers_extra_required_currentness_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    paper_root = study_root / "paper"
    study_yaml = study_root / "study.yaml"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    manuscript_path = paper_root / "draft.md"
    evidence_path = paper_root / "evidence_ledger.json"
    review_path = paper_root / "review" / "review_ledger.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    blueprint_path = paper_root / "medical_manuscript_blueprint.json"
    claim_map_path = paper_root / "claim_evidence_map.json"
    prose_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    prose_request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    gate_path = study_root / "runtime" / "publishability_gate" / "latest.json"
    submission_path = paper_root / "submission_minimal.json"
    claim_map_payload = {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary care treatment gaps remain clinically important.",
                "status": "draft",
                "paper_role": "primary_result",
                "display_bindings": ["table-1"],
                "sections": ["Results"],
                "evidence_items": [
                    {
                        "item_id": "evidence-primary",
                        "support_level": "partial",
                        "source_paths": [str(evidence_path.resolve())],
                    }
                ],
            }
        ]
    }
    evidence_ledger_payload = {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary care treatment gaps remain clinically important.",
                "status": "draft",
                "submission_scope": "current_submission_minimal",
                "evidence": [
                    {
                        "evidence_id": "evidence-primary",
                        "kind": "analysis_result",
                        "source_paths": [str(evidence_path.resolve())],
                        "support_level": "partial",
                        "summary": "Minimal fixture evidence for trace currentness coverage.",
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "gap-primary",
                        "description": "Fixture gap remains for submission readiness.",
                        "submission_impact": "blocks final submission readiness",
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "repair-primary",
                        "priority": "now",
                        "description": "Repair evidence before submission.",
                    }
                ],
            }
        ]
    }
    for path, body in (
        (request_path, "{}"),
        (manuscript_path, "current manuscript"),
        (evidence_path, json.dumps(evidence_ledger_payload)),
        (review_path, '{"review": true}'),
        (charter_path, '{"charter": true}'),
        (blueprint_path, '{"blueprint": true}'),
        (claim_map_path, json.dumps(claim_map_payload)),
        (
            prose_review_path,
            '{"medical_journal_prose_quality": {"route_back_recommendation": '
            '{"required": true, "route_target": "write"}}}',
        ),
        (gate_path, '{"gate": "blocked"}'),
        (submission_path, "{}"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    manuscript_digest = "sha256:" + hashlib.sha256(manuscript_path.read_bytes()).hexdigest()
    prose_review_path.write_text(
        json.dumps(
            {
                "assessment_provenance": {
                    "request_digest": "sha256:test-request",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": manuscript_digest,
                },
                "medical_journal_prose_quality": {
                    "status": "partial",
                    "overall_style_verdict": "revise",
                    "route_back_recommendation": {"required": True, "route_target": "write"},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    prose_request_path.write_text(
        json.dumps(
            {
                "request_digest": "sha256:test-request",
                "manuscript": {
                    "path": str(manuscript_path.resolve()),
                    "digest": manuscript_digest,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    study_yaml.write_text(
        f"study_id: {study_id}\nquest_id: {study_id}\n",
        encoding="utf-8",
    )
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260629T010203Z_publication_eval_record.json"
        ).resolve()
    )
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "manuscript": {"path": str(manuscript_path.resolve())},
                        "evidence_ledger": {"path": str(evidence_path.resolve())},
                        "review_ledger": {"path": str(review_path.resolve())},
                        "study_charter": {"path": str(charter_path.resolve())},
                        "medical_manuscript_blueprint": {"path": str(blueprint_path.resolve())},
                        "claim_evidence_map": {"path": str(claim_map_path.resolve())},
                        "medical_prose_review": {"path": str(prose_review_path.resolve())},
                        "publication_gate_projection": {"path": str(gate_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [
                        str(evidence_path.resolve()),
                        str(charter_path.resolve()),
                        str(gate_path.resolve()),
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    contract = importlib.import_module("med_autoscience.policies").build_ai_reviewer_operating_system_contract(
        importlib.import_module("med_autoscience.policies").DEFAULT_PUBLICATION_CRITIQUE_POLICY
    )
    quality_assessment = {
        dimension: {
            "status": "blocked",
            "summary": f"{dimension} needs repair.",
            "reviewer_reason": f"{dimension} needs repair.",
            "evidence_refs": [str(gate_path.resolve())],
        }
        for dimension in contract["rubric_dimensions"]
    }
    record_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::003::current",
        "study_id": study_id,
        "quest_id": study_id,
        "emitted_at": "2026-06-29T00:00:00Z",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(charter_path.resolve()),
            "charter_id": f"charter::{study_id}::v1",
            "publication_objective": "Evaluate current inputs.",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str((study_root / "runtime_escalation.json").resolve()),
            "main_result_ref": str(evidence_path.resolve()),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(paper_root.resolve()),
            "submission_minimal_ref": str(submission_path.resolve()),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(evidence_path.resolve())],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "quality_assessment": quality_assessment,
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Current record is not submission-ready.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "extra-currentness-ref",
                "gap_type": "delivery",
                "severity": "must_fix",
                "summary": "The extra required currentness ref must be covered.",
                "evidence_refs": [str(gate_path.resolve())],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "route-write",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "route_key_question": "Repair the publication gate blockers before submission.",
                "route_rationale": "The current reviewer record still routes back to writing repair.",
                "priority": "now",
                "reason": "Gate remains blocked.",
                "evidence_refs": [str(gate_path.resolve())],
                "requires_controller_decision": True,
            }
        ],
        "future_facing_limitations_plan": [
            {
                "limitation": "Residual reporting gap.",
                "impact_on_claim": "Limits submission readiness.",
                "required_future_analysis_data_or_design": "Complete reporting repair.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "sci_clinical_registry_review": [
            {
                "concern_id": f"extra-currentness-ref-{domain}",
                "domain": domain,
                "status": "blocked",
                "severity": "must_fix",
                "finding": f"{domain} remains part of the reviewer trace.",
                "evidence_refs": [str(gate_path.resolve())],
                "required_disposition": "revise",
            }
            for domain in contract["sci_clinical_registry_review"]["required_domains"]
        ],
        "reviewer_operating_system": {
            "input_bundle": {
                "manuscript": str(manuscript_path.resolve()),
                "evidence_ledger": str(evidence_path.resolve()),
                "review_ledger": str(review_path.resolve()),
                "study_charter": str(charter_path.resolve()),
                "medical_manuscript_blueprint": str(blueprint_path.resolve()),
                "claim_evidence_map": str(claim_map_path.resolve()),
                "medical_prose_review": str(prose_review_path.resolve()),
                "publication_gate_projection": str(gate_path.resolve()),
            }
        },
    }

    result = module.materialize_ai_reviewer_publication_eval_record(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        record=record_payload,
        source="test",
        build_production_trace=True,
    )

    written = json.loads(Path(result["publication_eval_record_ref"]).read_text(encoding="utf-8"))
    currentness = written["reviewer_operating_system"]["currentness_checks"]
    assert currentness["study_charter"]["ref"] == str(charter_path.resolve())
    assert currentness["study_charter"]["digest"].startswith("sha256:")
    assert currentness["publication_gate_projection"]["ref"] == str(gate_path.resolve())
    assert currentness["publication_gate_projection"]["digest"].startswith("sha256:")
