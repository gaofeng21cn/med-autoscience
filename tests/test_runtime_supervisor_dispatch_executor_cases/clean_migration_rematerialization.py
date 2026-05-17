from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_clean_migration_ai_reviewer_inputs(study_root: Path, study_id: str) -> None:
    _write_json(
        study_root / "paper" / "medical_manuscript_blueprint.json",
        {
            "schema_version": 1,
            "surface": "medical_manuscript_blueprint",
            "authoring_provenance": {
                "owner": "ai_author",
                "source_kind": "medical_manuscript_blueprint",
                "policy_id": "medical_manuscript_blueprint_v1",
                "ai_reviewer_required": False,
            },
            "argument_sequence": [
                "clinical_problem",
                "evidence_gap",
                "study_objective",
                "target_population",
                "study_design",
                "main_findings_by_clinical_importance",
                "clinical_interpretation",
                "discussion_claim_boundary",
                "limitations",
            ],
            "study_id": study_id,
            "clinical_problem": "Patients need clinically interpretable risk information.",
            "evidence_gap": "Prior reports do not define the publication claim boundary.",
            "study_objective": "To evaluate a restrained clinical prediction study.",
            "target_population": "Adults in the cohort.",
            "study_design": "Retrospective cohort study.",
            "main_findings_by_clinical_importance": [
                {"rank": 1, "clinical_finding": "The score stratified risk."}
            ],
            "clinical_interpretation": "Interpret as bounded risk stratification.",
            "claim_evidence_map": [{"claim_id": "C1", "statement": "Primary claim."}],
            "figure_table_rhetorical_roles": [
                {"display_id": "F1", "rhetorical_role": "Supports the main finding."}
            ],
            "discussion_claim_boundary": "Do not claim practice change.",
            "limitations": ["External validation is not established."],
            "journal_voice_target": {"voice": "neutral_clinical_original_research"},
            "source_refs": [str(study_root / "paper" / "claim_evidence_map.json")],
        },
    )
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claims": [{"claim_id": "C1"}]})
    _write_json(study_root / "paper" / "results_narrative_map.json", {"sections": [{"section_id": "results"}]})
    _write_json(study_root / "paper" / "figure_semantics_manifest.json", {"figures": [{"figure_id": "F1"}]})
    _write_json(study_root / "paper" / "evidence_ledger.json", {"items": [{"claim_id": "C1"}]})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"items": []})
    (study_root / "paper" / "draft.md").write_text(
        "## Results\n\nFigure 1 shows that the model stratified observed mortality risk.\n",
        encoding="utf-8",
    )


def test_execute_dispatch_after_clean_cutover_rematerializes_request_without_legacy_prose_review(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    cutover_module = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_clean_migration_ai_reviewer_inputs(study_root, study_id)
    receipt_path = study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json"
    _write_json(
        receipt_path,
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    input_refs = {
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
            "present": False,
            "valid": False,
        },
        "publication_gate_projection": {"path": str(receipt_path), "present": True, "valid": True},
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": False,
                "missing_or_invalid_refs": ["medical_prose_review"],
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

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    assert request_path.is_file()
    assert latest_path.is_file()
    assert not (study_root / "artifacts" / "publication_eval" / "medical_prose_review.json").exists()
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    prose_currentness = latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]
    assert latest["assessment_provenance"]["owner"] == "ai_reviewer"
    assert latest["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    assert latest["quality_assessment"]["medical_journal_prose_quality"]["status"] == "underdefined"
    assert prose_currentness["status"] == "requested"
    assert prose_currentness["authority_source_signature"] == "paper_authority_clean_migration"
    assert prose_currentness["request_ref"] == str(request_path.resolve())
    assert prose_currentness["request_digest"].startswith("sha256:")
    assert cutover_module.cutover_requires_ai_reviewer(study_root=study_root) is False
