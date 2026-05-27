from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_reviewer_os
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_pending_ai_reviewer_recheck_request_preempts_consumed_write_routeback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    canonical_inputs = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.canonical_inputs"
    )
    transition_table = importlib.import_module("med_autoscience.controllers.study_domain_transition_table")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent DPCC descriptive manuscript.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    stale_latest = {
        "schema_version": 1,
        "eval_id": "publication-eval::003::stale::2026-05-27T05:51:22+00:00",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-27T05:51:22+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "reviewer_operating_system": {
            "currentness_checks": {
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": "sha256:stale",
                }
            }
        },
    }
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(latest_path, stale_latest)
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260527T111037Z_publication_eval_record.json"
    )
    current_eval_id = "publication-eval::003::current::2026-05-27T11:10:37+00:00"
    current_record = {
        "schema_version": 1,
        "eval_id": current_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-27T11:10:37+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            dimension: {"status": "blocked", "summary": f"{dimension} still requires review."}
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
                "limitation": "Medication coverage is record-based.",
                "impact_on_claim": "Use recorded medication-coverage terminology.",
                "required_future_analysis_data_or_design": "Repeat review after evidence repair.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": current_manuscript_routeback_reviewer_os(
            study_root=study_root,
            manuscript_path=manuscript_path,
            manuscript_text=manuscript_text,
            eval_id=current_eval_id,
        ),
        "recommended_actions": [
            {
                "action_id": "route-back-same-line-dm003-claim-evidence",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "current_manuscript_claim_evidence_alignment_repair"
                ),
                "next_work_unit": {
                    "unit_id": "current_manuscript_claim_evidence_alignment_repair",
                    "lane": "write",
                    "summary": "Repair or explicitly reconcile A1 boundary-metric evidence path.",
                },
            }
        ],
    }
    _write_json(current_record_path, current_record)
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "surface": "repair_execution_evidence",
            "schema_version": 1,
            "status": "progress_delta_candidate",
            "repair_work_unit": {"unit_id": "current_manuscript_claim_evidence_alignment_repair"},
            "review_finding": {"source_eval_id": current_eval_id},
            "changed_artifact_refs": [
                {"path": str(study_root / "paper" / "claim_evidence_map.json")},
                {"path": str(study_root / "paper" / "evidence_ledger.json")},
            ],
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(
                study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
            ),
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}::{quest_id}",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "source_surface": "quality_repair_batch",
            "request_lifecycle": {
                "state": "requested",
                "assessment_ref": str(current_record_path.resolve()),
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
                        "path": str(latest_path),
                        "present": True,
                        "valid": True,
                    },
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": stale_latest,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-recheck-request",
            "source_signature": "truth-source-dm003-recheck-request",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(latest_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }
    status_payload["domain_transition"] = transition_table.project_domain_transition(
        study_id=study_id,
        study_root=study_root,
        status=status_payload,
        macro_state={"writer_state": "queued", "reason": "quality"},
        active_run_id=None,
    )
    selected_publication_eval = canonical_inputs.publication_eval_payload(status_payload, progress_payload)
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, selected_publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["domain_transition"]["completion_receipt_consumption"]["receipt_ref"] == str(
        current_record_path.resolve()
    )
    assert study["ai_reviewer_assessment"]["missing"] is True
    assert study["ai_reviewer_assessment"]["request_state"] == "requested"
    assert [action["action_type"] for action in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "ai_reviewer_assessment_required"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
