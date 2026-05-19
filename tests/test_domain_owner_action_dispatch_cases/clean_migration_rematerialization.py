from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
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
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
            "surface": "domain_action_request",
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

    result = module.dispatch_domain_owner_actions(
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


def test_clean_cutover_rematerializes_stale_review_request_with_missing_manuscript_digest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    _write_json(
        request_path,
        {
            "schema_version": 1,
            "surface": "medical_prose_review_request",
            "request_digest": "sha256:" + "0" * 64,
            "manuscript": {
                "path": str(study_root / "paper" / "draft.md"),
                "digest": "",
                "text": "stale request payload",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": {
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
                },
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    latest_request = json.loads(request_path.read_text(encoding="utf-8"))
    assert latest_request["manuscript"]["digest"].startswith("sha256:")
    assert latest_request["manuscript"]["text"].startswith("## Results")


def test_clean_cutover_missing_canonical_blueprint_routes_to_rehydrate_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "legacy-study-without-blueprint"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claims": [{"claim_id": "C1"}]})
    _write_json(study_root / "paper" / "evidence_ledger.json", {"items": [{"claim_id": "C1"}]})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"items": []})
    (study_root / "paper" / "draft.md").write_text("## Results\n\nThe manuscript exists.\n", encoding="utf-8")
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
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": {
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
                        "present": False,
                        "valid": False,
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
                },
                "all_required_refs_present": False,
                "missing_or_invalid_refs": ["medical_manuscript_blueprint", "medical_prose_review"],
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["blocked_count"] == 1
    assert execution["blocked_reason"] == "canonical_paper_inputs_rehydrate_required"
    assert execution["next_owner"] == "write"
    assert execution["owner_result"]["legacy_artifact_reader_allowed"] is False
    assert execution["owner_result"]["quality_verdict_written"] is False
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_clean_canonical_rehydrate_writes_source_only_without_canonical_blueprint(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "legacy-study-without-blueprint"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Shared baseline variables retain partial risk ordering.",
                    "status": "partially_supported",
                    "limitations": ["Absolute risk calibration remains cohort-specific."],
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "results_narrative_map.json",
        {
            "schema_version": 1,
            "sections": [
                {
                    "section_id": "primary-results",
                    "direct_answer": "Cross-cohort discrimination was partially retained.",
                    "key_quantitative_findings": ["C statistic and calibration metrics must be reported."],
                    "clinical_meaning": "Model transportability is incomplete without recalibration.",
                    "boundary": "Do not interpret the country gap causally.",
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "figure-2",
                    "story_role": "calibration",
                    "direct_message": "Calibration shift limits direct absolute-risk transport.",
                    "interpretation_boundary": "Figure supports validation, not clinical adoption.",
                }
            ],
        },
    )
    (study_root / "paper" / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "paper" / "draft.md").write_text(
        "## Results\n\nThe model retained partial risk ordering but calibration differed across cohorts.\n",
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "canonical_paper_inputs_rehydrate_required.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="canonical_paper_inputs_rehydrate_required",
            owner="write",
            required_output_surface="paper/medical_manuscript_blueprint_source.json",
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("canonical_paper_inputs_rehydrate_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    source_path = study_root / "paper" / "medical_manuscript_blueprint_source.json"
    canonical_path = study_root / "paper" / "medical_manuscript_blueprint.json"
    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert source_path.is_file()
    assert not canonical_path.exists()
    source = json.loads(source_path.read_text(encoding="utf-8"))
    assert source["surface"] == "medical_manuscript_blueprint"
    assert source["source_kind"] == "mechanical_draft"
    assert source["canonical_ready"] is False
    assert execution["execution_status"] == "executed"
    assert execution["next_owner"] == "write"
    assert execution["owner_result"]["artifact_path"] == str(source_path.resolve())
    assert execution["owner_result"]["canonical_surface_written"] is False
    assert "AI author/reviewer must authorize paper/medical_manuscript_blueprint.json" in (
        execution["owner_result"]["next_required_actions"]
    )


def test_clean_canonical_rehydrate_is_not_suppressed_by_prior_ai_reviewer_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "legacy-study-rehydrate-repeat"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Shared variables carry partial risk-ordering information.",
                    "status": "partially_supported",
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "results_narrative_map.json",
        {
            "schema_version": 1,
            "sections": [
                {
                    "section_id": "primary-results",
                    "direct_answer": "Transportability remained incomplete.",
                    "key_quantitative_findings": ["Calibration and discrimination estimates remain required."],
                    "clinical_meaning": "Absolute-risk use requires cohort-specific calibration.",
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "figure-1",
                    "story_role": "calibration",
                    "direct_message": "Calibration evidence constrains cross-cohort transportability.",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    route = _dispatch(
        study_id=study_id,
        action_type="canonical_paper_inputs_rehydrate_required",
        owner="write",
        required_output_surface="paper/medical_manuscript_blueprint_source.json",
    )["owner_route"]
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "canonical_paper_inputs_rehydrate_required",
                    "repeat_suppression_key": route["work_unit_fingerprint"],
                    "prompt_contract": {
                        "do_not_repeat": True,
                        "repeat_suppression_key": route["work_unit_fingerprint"],
                    },
                    "owner_route": route,
                    "owner_result": {
                        "surface_kind": "canonical_paper_inputs_rehydrate_blocker",
                        "authority_source_signature": "paper_authority_clean_migration",
                        "legacy_artifact_reader_allowed": False,
                        "mechanical_blueprint_as_canonical_allowed": False,
                    },
                }
            ],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "canonical_paper_inputs_rehydrate_required.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="canonical_paper_inputs_rehydrate_required",
            owner="write",
            required_output_surface="paper/medical_manuscript_blueprint_source.json",
            owner_route=dict(route),
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("canonical_paper_inputs_rehydrate_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert execution["execution_status"] == "executed"
    assert execution["repeat_suppression"]["repeat_suppressed"] is False
    assert (study_root / "paper" / "medical_manuscript_blueprint_source.json").is_file()
    assert not (study_root / "paper" / "medical_manuscript_blueprint.json").exists()


def test_clean_canonical_rehydrate_runs_when_terminal_stall_marks_missing_source_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "legacy-study-rehydrate-terminal-stall"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Shared baseline variables retain partial risk ordering.",
                    "status": "partially_supported",
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "results_narrative_map.json",
        {
            "schema_version": 1,
            "sections": [
                {
                    "section_id": "primary-results",
                    "direct_answer": "Risk ordering was partially transported but calibration was not.",
                    "key_quantitative_findings": ["Calibration metrics must be reported before absolute-risk claims."],
                    "clinical_meaning": "External use requires recalibration and transparent uncertainty.",
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "figure-1",
                    "story_role": "calibration",
                    "direct_message": "Calibration limits absolute-risk transport.",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    route = _dispatch(
        study_id=study_id,
        action_type="canonical_paper_inputs_rehydrate_required",
        owner="write",
        required_output_surface="paper/medical_manuscript_blueprint_source.json",
    )["owner_route"]
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper-progress-stall::rehydrate",
    }
    dispatch = _dispatch(
        study_id=study_id,
        action_type="canonical_paper_inputs_rehydrate_required",
        owner="write",
        required_output_surface="paper/medical_manuscript_blueprint_source.json",
        owner_route=dict(route),
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "canonical_paper_inputs_rehydrate_required.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_domain_route_scan",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": stall,
                }
            ],
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("canonical_paper_inputs_rehydrate_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    execution = result["executions"][0]
    assert result["executed_count"] == 1
    assert execution["execution_status"] == "executed"
    assert execution["paper_progress_stall_handoff_allowed"] is True
    assert (study_root / "paper" / "medical_manuscript_blueprint_source.json").is_file()
