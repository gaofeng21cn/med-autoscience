from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_agent_lab_medical_manuscript_quality_cases.refs_only_feedback_obesity import (
    test_medical_manuscript_quality_agent_lab_suite_materializes_refs_only_surface,
    test_medical_manuscript_quality_suite_exposes_feedback_self_evolution_trigger,
    test_obesity_registry_quality_profile_requires_sci_draft_volume_and_clinical_value,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_medical_manuscript_quality_agent_lab_suite_projects_refs_only_patch_loop_closeout_bundle(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer must re-evaluate manuscript quality.",
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {"task_intent": "reviewer_revision", "summary": "HDL harmonization and calibration repair."},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "owner": "analysis_harmonization_owner",
            "status": "blocked",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {"blocker_id": "unit_harmonized_rerun_required"},
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    task = suite["tasks"][0]
    closeout = task["patch_loop_closeout_bundle"]

    assert closeout["surface_kind"] == "mas_agent_lab_refs_only_patch_loop_closeout_bundle"
    assert closeout["suite_status"] == "blocked"
    assert closeout["domain_verdict_claimed"] is False
    assert closeout["blocked_suite"]["suite_id"] == suite["suite_id"]
    assert closeout["blocked_suite"]["blocked_task_ids"] == [task["task_id"]]
    assert closeout["developer_work_order"]["work_order_id"] == (
        task["improvement_candidate"]["developer_patch_work_order"]["work_order_id"]
    )
    assert closeout["developer_work_order"]["can_write_study_truth"] is False
    assert "analysis_harmonization_owner_callable" in closeout["developer_work_order"]["required_patch_scopes"]
    trace = closeout["patch_traceability"]
    assert trace["source_task_id"] == task["task_id"]
    assert trace["source_gate_id"] == task["promotion_gate"]["gate_ref"]
    assert "source_task_id" in trace["required_traceability_axes"]
    assert "forbidden_write_proof_ref" in trace["required_traceability_axes"]
    assert "contracts/agent_lab_handoff.json#/meta_agent_work_order_contract" in trace["contract_refs"]
    assert "mechanism-edit-ref:mas/analysis-harmonization-owner-routing" in trace["editable_surface_refs"]
    assert closeout["target_verification"]["status"] == "blocked_until_verification_runs"
    assert "rtk make test-meta" in closeout["target_verification"]["verification_command_refs"]
    assert any(
        "tests/test_agent_lab_medical_manuscript_quality.py" in ref
        for ref in closeout["target_verification"]["focused_test_refs"]
    )
    assert closeout["runtime_read_model_consumption"]["status"] == "refs_only_projected"
    assert closeout["runtime_read_model_consumption"]["can_write_runtime_queue"] is False
    assert "owner_route" in closeout["runtime_read_model_consumption"]["consumable_ref_roles"]
    assert closeout["workspace_proof"]["workspace_body_included"] is False
    assert closeout["no_forbidden_write"]["result"] == "configured"
    assert "publication_eval/latest.json" in closeout["no_forbidden_write"]["forbidden_writes"]
    assert closeout["owner_receipt_or_typed_blocker"]["status"] == "typed_blocker"
    assert closeout["owner_receipt_or_typed_blocker"]["owner_route"] == "analysis_harmonization_owner"
    assert closeout["owner_receipt_or_typed_blocker"]["typed_blocker"]["blocker_id"] == (
        "unit_harmonized_rerun_required"
    )
    assert closeout["patch_absorption"]["status"] == "pending_verified_commit"
    assert closeout["patch_absorption"]["can_absorb_without_owner_receipt_or_typed_blocker"] is False
    assert closeout["worktree_cleanup"]["status"] == "pending_after_commit"
    assert closeout["agent_lab_re_evaluation_refs"] == [
        "opl-agent-lab-run-ref:mas/002-dm-china-us-mortality-attribution/patch-smoke",
        "opl-agent-lab-evolve-ref:mas/002-dm-china-us-mortality-attribution/patch-smoke",
    ]
