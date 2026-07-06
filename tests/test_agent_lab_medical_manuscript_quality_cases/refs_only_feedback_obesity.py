from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_medical_manuscript_quality_agent_lab_suite_materializes_refs_only_surface(
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
                    "status": "ready",
                    "summary": "AI reviewer judged the manuscript ready.",
                }
            },
        },
    )

    result = module.materialize_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    path = Path(result["suite_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert result["surface_kind"] == "mas_agent_lab_medical_manuscript_quality_suite"
    assert result["status"] == "materialized"
    assert payload["tasks"][0]["scorecard"]["passed"] is True
    assert payload["tasks"][0]["promotion_gate"]["gate_status"] == "passed"
    assert payload["authority_boundary"]["can_write_domain_truth"] is False


def test_medical_manuscript_quality_suite_exposes_feedback_self_evolution_trigger(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "obesity_multicenter_phenotype_atlas"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_intent": (
                "按高质量医学 SCI 论文角度修订肥胖 registry 初稿，补引用、扩正文、"
                "增加结果图并清除内部报告式文风。"
            ),
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    trigger = suite["feedback_self_evolution_trigger"]
    task_trigger = suite["tasks"][0]["improvement_candidate"]["feedback_self_evolution_trigger"]

    assert trigger == task_trigger
    assert trigger["surface_kind"] == "mas_agent_lab_feedback_self_evolution_trigger"
    assert trigger["feedbackops_event_kind"] == "target_agent_feedback_external_suite"
    assert trigger["accepted_feedback_profile"] == "target_agent_feedback_external_suite"
    assert trigger["feedback_profiles"] == [
        "target_agent_feedback_external_suite",
        "high_quality_medical_manuscript_feedback",
    ]
    assert trigger["target_agent_id"] == "med-autoscience"
    assert trigger["idempotency_key"] == (
        "feedbackops:mas/obesity_multicenter_phenotype_atlas/high_quality_medical_manuscript/latest_suite"
    )
    assert trigger["feedback_capture_requires_developer_mode"] is False
    assert trigger["repo_fix_execution_requires_opl_developer_mode"] is True
    assert "opl-developer-mode:repo-fix-execution" in trigger["developer_mode_execution_gate_refs"]
    assert trigger["refs_only"] is True
    assert trigger["writes_study_truth"] is False
    assert trigger["status"] == "runnable_after_suite_materialized"
    assert trigger["adapter_role"] == "domain_thin_feedback_adapter"
    assert trigger["paper_mission_subordination"] == {
        "surface_kind": "mas_paper_mission_subordination",
        "authority_owner": "MedAutoScience",
        "mainline_route": [
            "PaperMission",
            "submission_authority",
            "submission_authority_owner_gate_or_typed_blocker",
        ],
        "control_plane_role": "subordinate_input_or_advisory_only",
        "can_start_parallel_mainline": False,
        "can_bypass_submission_authority": False,
        "can_close_without_owner_gate_or_typed_blocker": False,
    }
    assert trigger["oma_evolution_skill_ref"] == "opl-meta-agent:oma-agent-evolution"
    assert trigger["contract_itself_triggers_execution"] is False
    assert trigger["target_route"] == {
        "domain_owner": "med-autoscience",
        "agent_lab_owner": "one-person-lab",
        "meta_agent_owner": "opl-meta-agent",
        "target_repo": "med-autoscience",
    }
    assert trigger["owner_chain"] == [
        "med-autoscience:reviewer_revision_intake",
        "med-autoscience:agent_lab_medical_manuscript_quality_suite",
        "one-person-lab:feedbackops_agent_lab_projection",
        "opl-meta-agent:oma-agent-evolution",
        "med-autoscience:owner_closeout_readback",
    ]
    assert trigger["target_action_contracts"]["oma_improve"] == (
        "opl-meta-agent.improve-from-external-agent-lab-suite"
    )
    assert trigger["owner_closeout_readback_refs"] == [
        "paper_mission_readback_ref",
        "submission_authority_owner_gate_readback_ref",
        "target_owner_receipt_or_typed_blocker_ref",
    ]
    assert trigger["opl_app_status_projection"]["should_register_stage_run"] is True
    assert trigger["authority_boundary"]["can_write_domain_truth"] is False
    assert trigger["authority_boundary"]["can_authorize_quality_verdict"] is False


def test_obesity_registry_quality_profile_requires_sci_draft_volume_and_clinical_value(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "obesity_multicenter_phenotype_atlas"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                }
            },
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    work_order = suite["tasks"][0]["improvement_candidate"]["developer_patch_work_order"]
    target_ids = {target["target_id"] for target in work_order["study_quality_targets"]}

    assert work_order["study_quality_target_family"] == "obesity_registry_descriptive_phenotype_atlas"
    assert "obesity_registry_descriptive_first_draft_quality_contract" in work_order["required_patch_scopes"]
    assert "first_draft_quality_route_back_regression" in work_order["required_patch_scopes"]
    assert {
        "reference_integrity_25_to_40_citations",
        "main_text_3500_word_floor",
        "clinical_value_result_figure_gap",
        "figure_polish_skill_consistency",
        "tables_and_figures_volume_floor",
        "internal_report_style_language_purge",
        "administrative_declaration_sections_required",
        "registry_data_lock_enrollment_boundary",
        "diagnostic_provenance_caveat_required",
        "figure_caption_content_consistency",
        "pdf_nonblank_figure_export_qc",
        "journal_figure_numbering_normalization",
        "wide_table_supplement_or_landscape_routing",
        "descriptive_atlas_discussion_theme_compression",
        "supplementary_missingness_atlas_required",
        "adult_bmi_sensitivity_table_required",
        "methods_registry_cohort_completeness",
        "results_phenotype_clinical_interpretability",
        "discussion_claim_guardrails",
    }.issubset(target_ids)
    target_requirements = {
        target["target_id"]: target["requirement"]
        for target in work_order["study_quality_targets"]
    }
    assert "analytic/data-surface jargon" in target_requirements["internal_report_style_language_purge"]
    joined_refs = " ".join(suite["tasks"][0]["improvement_candidate"]["evidence_refs"])
    assert "reference-integrity-25-to-40-citations" in joined_refs
    assert "main-text-3500-word-floor" in joined_refs
    assert "clinical-value-result-figure-gap" in joined_refs
    assert "pdf-nonblank-figure-export-qc" in joined_refs
    assert "journal-figure-numbering-normalization" in joined_refs
    assert "wide-table-supplement-or-landscape-routing" in joined_refs
    assert "descriptive-atlas-discussion-theme-compression" in joined_refs
    assert "administrative-declaration-sections-required" in joined_refs
    assert "supplementary-missingness-atlas-required" in joined_refs
    assert "adult-bmi-sensitivity-table-required" in joined_refs
