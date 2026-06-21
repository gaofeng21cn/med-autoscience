from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience import cli
from med_autoscience.display_pack_agent import (
    compile_display_figure_intent,
    display_pack_capability_discover,
    display_pack_figure_plan,
    display_pack_orchestrate,
    display_pack_preflight,
    display_pack_render,
)
from med_autoscience.publication_display_contract import seed_publication_display_contracts_if_missing


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_roc_payload(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_data_digest": "payload-digest",
                "title": "Primary ROC",
                "x_label": "1 - Specificity",
                "y_label": "Sensitivity",
                "series": [
                    {"label": "Model", "x": [0.0, 0.2, 1.0], "y": [0.0, 0.8, 1.0]},
                    {"label": "Comparator", "x": [0.0, 0.4, 1.0], "y": [0.0, 0.7, 1.0]},
                ],
                "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _styled_paper_root(tmp_path: Path) -> Path:
    paper_root = tmp_path / "paper"
    seed_publication_display_contracts_if_missing(paper_root=paper_root)
    return paper_root


def _write_prepared_dependency_environment(paper_root: Path) -> None:
    build_root = paper_root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    (build_root / "dependency_environment_lock.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "lock_id": "test-display-env-lock",
                "lock_sha256": "sha256:test-display-env-lock",
                "source_requirement_refs": [
                    "display-packs/fenggaolab.org.medical-display-core/renderer_dependency_profile.json"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (build_root / "dependency_run_context.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_context_id": "test-display-env-run-context",
                "execution_fingerprint": "sha256:test-display-env-run-context",
                "argv_prefix": [],
                "env_vars": {"MAS_TEST_DEPENDENCY_ENV": "prepared"},
                "binary_paths": {},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (build_root / "dependency_environment_receipt.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "prepared",
                "failure_class": "",
                "lock_ref": "paper/build/dependency_environment_lock.json",
                "lock_sha256": "sha256:test-display-env-lock",
                "environment_ref": "test-prepared-display-env",
                "cache_key": "test-display-env-cache",
                "target_platform": "test-platform",
                "binary_checks": [{"name": "Rscript", "status": "present"}],
                "package_checks": [{"name": "ggplot2", "status": "present"}],
                "system_requirement_checks": [],
                "run_context_ref": "paper/build/dependency_run_context.json",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_display_pack_capability_discover_exposes_agent_actions_and_inventory() -> None:
    payload = display_pack_capability_discover(repo_root=REPO_ROOT)

    assert payload["surface_kind"] == "display_pack_agent_capability"
    assert payload["status"] == "available"
    assert payload["inventory"]["template_count"] == 31
    assert payload["inventory"]["active_template_count"] == 31
    assert payload["inventory"]["canonical_family_count"] == 31
    assert payload["inventory"]["canonical_template_count"] == 31
    assert payload["inventory"]["legacy_alias_template_count"] == 0
    assert payload["inventory"]["kind_counts"]["evidence_figure"] >= 15
    assert payload["inventory"]["renderer_family_counts"]["r_ggplot2"] >= 10
    assert payload["inventory"]["analysis_responsibility_counts"] == {
        "computed_in_template": 3,
        "illustration_shell": 1,
        "table_shell": 1,
        "validated_summary_required": 26,
    }
    assert payload["inventory"]["kind_counts"]["illustration_shell"] == 2
    assert payload["inventory"]["renderer_policy_completion"]["default_python_evidence_template_count"] == 0
    assert payload["inventory"]["renderer_policy_completion"]["python_evidence_retained_count"] == 0
    assert payload["renderer_policy"]["data_evidence_first_class_renderer"] == "r_ggplot2"
    assert payload["figure_contract_policy"]["policy_id"] == "mas_nature_skills_informed_figure_contract.v1"
    assert "core_conclusion_before_plotting" in payload["figure_contract_policy"]["adopted_patterns"]
    assert "no_python_or_r_question_on_default_mas_evidence_path" in payload["figure_contract_policy"]["mas_adaptations"]
    assert payload["figure_contract_policy"]["publication_polish_policy"]["policy_id"] == (
        "mas_publication_polish_policy.v1"
    )
    assert payload["figure_contract_policy"]["publication_polish_policy"]["nonblocking_agent_policy"][
        "blocks_default_evidence_progress"
    ] is False
    assert payload["figure_contract_policy"]["figure_workflow_policy"]["policy_id"] == (
        "mas_nature_skills_figure_workflow_lifecycle.v1"
    )
    assert payload["composition_recipe_surface"]["policy"]["policy_id"] == (
        "mas_medical_figure_composition_recipes.v1"
    )
    assert payload["composition_recipe_surface"]["composition_recipe_count"] == 6
    assert payload["composition_recipe_surface"]["blocks_default_evidence_progress"] is False
    assert payload["figure_contract_policy"]["figure_workflow_policy"]["authority_boundary"][
        "can_authorize_publication_readiness"
    ] is False
    assert payload["expected_receipt_refs"]["figure_workflow_packet"] == "paper/figure_workflow_packet.json"
    assert {item["command"] for item in payload["callable_actions"]} == {
        "display-pack-capability-discover",
        "display-pack-orchestrate",
        "display-pack-figure-plan",
        "display-pack-preflight",
        "display-pack-render",
    }
    assert payload["authority_boundary"]["can_mutate_data_or_statistics"] is False
    assert payload["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert payload["expected_receipt_refs"]["figure_render_receipt"] == "paper/figure_render_receipt.json"


def test_display_pack_capability_discover_templates_defaults_to_canonical_surface() -> None:
    payload = display_pack_capability_discover(repo_root=REPO_ROOT, include_templates=True)

    assert payload["template_surface_policy"]["default_templates_are_canonical_only"] is True
    assert payload["template_surface_policy"]["active_inventory_is_canonical_only"] is True
    assert payload["template_surface_policy"]["evidence_figures_default_to_r_ggplot2"] is True
    assert payload["template_surface_policy"]["python_evidence_templates_not_retained_without_advantage_proof"] is True
    assert payload["template_surface_policy"]["composition_recipe_routing_required"] is True
    assert payload["template_surface_policy"]["template_analysis_responsibility_required"] is True
    assert payload["template_surface_policy"]["validated_summary_templates_fail_closed_on_raw_analysis_requests"] is True
    assert payload["template_surface_policy"]["migration_inventory_template_count"] == 66
    assert payload["template_surface_policy"]["returned_template_count"] == payload["inventory"]["template_count"]
    assert payload["templates"]
    assert len(payload["composition_recipe_surface"]["recipes"]) == 6
    assert {item["migration_status"] for item in payload["templates"]} == {"canonical"}
    assert all(item["default_visible"] is True for item in payload["templates"])
    assert not [
        item["template_id"]
        for item in payload["templates"]
        if item["kind"] == "evidence_figure" and item["renderer_family"] == "python"
    ]
    by_id = {item["template_id"]: item for item in payload["templates"]}
    assert by_id["roc_curve_binary"]["analysis_responsibility"] == "validated_summary_required"
    assert by_id["roc_curve_binary"]["analysis_input_state"] == "validated_display_payload"
    assert by_id["roc_curve_binary"]["medical_family_ids"] == ["discrimination_curve"]
    assert "roc_pr_curve" in by_id["roc_curve_binary"]["publication_quality_profile"]["starter_recipe_ids"]
    assert "categorical_accessible" in by_id["roc_curve_binary"]["publication_quality_profile"]["palette_token_ids"]
    assert "layout_readability" in by_id["roc_curve_binary"]["publication_quality_profile"]["qa_gate_ids"]
    assert by_id["umap_scatter_grouped"]["analysis_responsibility"] == "computed_in_template"
    assert by_id["umap_scatter_grouped"]["analysis_input_state"] == "raw_feature_matrix"
    assert by_id["umap_scatter_grouped"]["medical_family_ids"] == ["dimension_reduction_scatter"]
    assert "embedding_scatter" in by_id["umap_scatter_grouped"]["publication_quality_profile"][
        "starter_recipe_ids"
    ]


def test_display_pack_figure_plan_prefers_r_ggplot2_template_for_agent_request() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Prediction Performance",
            "preferred_renderer_family": "r_ggplot2",
            "query": "roc",
        },
        max_recommendations=3,
    )

    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["status"] == "display_plan_ready"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["recommended_template"]["renderer_family"] == "r_ggplot2"
    assert payload["recommended_template"]["migration_status"] == "canonical"
    assert payload["recommended_template"]["canonical_family_id"] == "roc_curve_binary"
    assert payload["recommended_template"]["analysis_responsibility"] == "validated_summary_required"
    assert payload["recommended_template"]["medical_family_ids"] == ["discrimination_curve"]
    assert payload["recommended_template"]["publication_quality_profile"]["starter_templates_are_floor_not_ceiling"] is True
    assert "palette" in payload["recommended_template"]["publication_quality_profile"]["ai_may_change"]
    assert "source_data_and_statistics_refs" in payload["recommended_template"]["publication_quality_profile"][
        "ai_must_preserve"
    ]
    assert payload["recommended_template"]["analysis_boundary"]["compatible_with_request"] is True
    assert payload["figure_intent"]["figure_contract"]["backend_policy"]["selected_backend"] == "r_ggplot2"
    assert payload["figure_intent"]["figure_contract"]["backend_policy"]["blocks_agent_progress"] is False
    assert payload["figure_intent"]["figure_contract"]["agent_progress_policy"][
        "backend_question_required_for_default_mas_evidence_path"
    ] is False
    workflow = payload["figure_workflow_packet"]
    assert workflow["policy_ref"] == "mas_nature_skills_figure_workflow_lifecycle.v1"
    assert workflow["nonblocking_progress_policy"]["blocks_default_evidence_progress"] is False
    assert workflow["figures"][0]["figure_brief"]["core_conclusion"]
    assert workflow["figures"][0]["storyboard"]["starter_template"]["template_id"] == "roc_curve_binary"
    composition = workflow["figures"][0]["storyboard"]["composition_recipe"]
    assert composition["recipe_id"] == "clinical_triptych_prediction"
    assert workflow["figures"][0]["storyboard"]["hero_panel"] == "primary_model_performance_summary"
    assert workflow["figures"][0]["storyboard"]["programmatic_evidence_required"] is True
    assert workflow["figures"][0]["storyboard"]["design_shell_allowed"] is False
    assert "shared" in workflow["figures"][0]["storyboard"]["guide_strategy"]
    assert workflow["figures"][0]["storyboard"]["panel_drop_policy"] == (
        "drop_or_merge_panels_without_unique_evidence"
    )
    assert "owner_or_publication_gate_receipt_present_for_claim_bearing_figures" in workflow["figures"][0][
        "paper_use_acceptance"
    ]["required_before_paper_use"]
    assert payload["template_surface_policy"]["default_recommendations_are_canonical_only"] is True
    assert payload["template_surface_policy"][
        "nature_skills_backend_question_not_used_on_default_mas_evidence_path"
    ] is True
    assert payload["template_surface_policy"]["medical_figure_family_mapping_required"] is True
    assert payload["template_surface_policy"]["starter_recipe_profile_required"] is True
    assert payload["template_surface_policy"]["style_palette_qa_profile_required"] is True
    assert payload["template_surface_policy"]["composition_recipe_routing_required"] is True
    assert payload["recommended_template"]["adaptation_required"] is False
    assert payload["next_callable"] == "display-pack-preflight"


def test_display_pack_figure_plan_blocks_raw_request_for_summary_only_roc() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={"query": "roc", "analysis_input_state": "labels_and_scores"},
    )

    assert payload["status"] == "blocked"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["recommended_template"]["analysis_responsibility"] == "validated_summary_required"
    assert payload["recommended_template"]["analysis_boundary"]["request_declares_raw_input"] is True
    assert payload["recommended_template"]["analysis_boundary"]["compatible_with_request"] is False
    assert payload["typed_blocker"]["blocked_reason"] == "analysis_summary_required_before_display_render"
    assert payload["typed_blocker"]["route_hint"] == (
        "materialize_validated_analysis_summary_before_display_render"
    )
    assert payload["next_callable"] == ""


def test_display_pack_figure_plan_allows_raw_feature_matrix_for_computed_umap() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={"query": "umap", "analysis_input_state": "raw_feature_matrix"},
    )

    assert payload["status"] == "display_plan_ready"
    assert payload["recommended_template"]["template_id"] == "umap_scatter_grouped"
    assert payload["recommended_template"]["analysis_responsibility"] == "computed_in_template"
    assert payload["recommended_template"]["analysis_input_state"] == "raw_feature_matrix"
    assert payload["recommended_template"]["analysis_boundary"]["compatible_with_request"] is True
    assert payload["figure_workflow_packet"]["figures"][0]["storyboard"]["composition_recipe"]["recipe_id"] == (
        "single_cell_atlas_storyboard"
    )
    assert payload["next_callable"] == "display-pack-preflight"


@pytest.mark.parametrize(
    ("query", "expected_recipe", "expected_hero"),
    [
        ("roc calibration decision curve clinical utility", "clinical_triptych_prediction", "primary_model_performance_summary"),
        ("genomic alteration heatmap pathway consequence", "asymmetric_genomics_figure", "dominant_molecular_pattern"),
        ("single cell UMAP marker dotplot cell type atlas", "single_cell_atlas_storyboard", "cell_state_geometry_or_spatial_context"),
        ("SHAP subgroup threshold model validation dashboard", "model_validation_dashboard", "validation_summary_or_generalizability"),
    ],
)
def test_display_pack_figure_plan_routes_to_page_level_composition_recipe(
    query: str,
    expected_recipe: str,
    expected_hero: str,
) -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={"query": query, "analysis_input_state": "validated_display_payload"},
        max_recommendations=5,
    )

    assert payload["status"] == "display_plan_ready"
    storyboard = payload["figure_workflow_packet"]["figures"][0]["storyboard"]
    assert storyboard["composition_recipe"]["recipe_id"] == expected_recipe
    assert storyboard["hero_panel"] == expected_hero
    assert storyboard["programmatic_evidence_required"] is True
    assert storyboard["composition_recipe"]["quality_floor_only"] is True
    assert "source_data_and_statistics_refs" in storyboard["composition_recipe"]["ai_must_preserve"]


def test_display_pack_figure_plan_allows_design_shell_composition_without_data_authority() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "illustration_shell",
            "query": "study workflow schematic graphical abstract with validation panel",
        },
        max_recommendations=5,
    )

    storyboard = payload["figure_workflow_packet"]["figures"][0]["storyboard"]
    assert storyboard["composition_recipe"]["recipe_id"] == "schematic_led_composite"
    assert storyboard["design_shell_allowed"] is True
    assert storyboard["programmatic_evidence_required"] is True
    assert "treat_imagegen_or_svg_schematic_as_data_evidence" in storyboard["composition_recipe"][
        "forbidden_authority"
    ]


def test_compile_display_figure_intent_emits_claim_first_contract_without_blocking_agent() -> None:
    payload = compile_display_figure_intent(
        intent="Show calibration and clinical utility for the final prediction model.",
        claim_ref="claim:model-calibration",
        data_ref="data:calibration-decision",
        paper_target="nature_medicine",
    )

    contract = payload["figure_contract"]
    assert contract["contract_id"] == "mas_display_figure_contract.v1"
    assert contract["core_conclusion"] == (
        "Show calibration and clinical utility for the final prediction model."
    )
    assert contract["evidence_chain"][0]["status"] == "present"
    assert contract["evidence_chain"][1]["status"] == "present"
    assert contract["panel_logic"]["hero_panel_preferred"] is True
    assert contract["backend_policy"]["selected_backend"] == "r_ggplot2"
    assert contract["backend_policy"]["backend_exclusivity_required"] is True
    assert contract["publication_polish_policy_ref"] == "mas_publication_polish_policy.v1"
    assert "semantic_palette_roles_resolved_from_article_style_profile" in contract[
        "publication_polish_required_before_paper_use"
    ]
    assert contract["agent_progress_policy"]["missing_refs_route_to_typed_repair"] is True
    assert contract["agent_progress_policy"]["manual_template_browsing_required"] is False
    assert payload["figure_workflow_packet"]["figures"][0]["figure_brief"]["core_conclusion"] == (
        "Show calibration and clinical utility for the final prediction model."
    )
    assert payload["figure_workflow_packet"]["figures"][0]["render_inspect_revise"]["inspect_at_final_size"] is True
    assert payload["figure_contract_policy"]["observed_head"] == "5d2ba1dee1c087be6de8f4a8aad4b27f04974be9"
    assert payload["compiled_figure_request"]["medical_figure_template_seed_ids"]


@pytest.mark.parametrize(
    ("query", "template_id", "audit_family"),
    [
        ("km plot", "kaplan_meier_grouped", "Time-to-Event"),
        ("heatmap", "heatmap_group_comparison", "Matrix Pattern"),
        ("shap beeswarm", "shap_summary_beeswarm", "Model Explanation"),
        ("shap dependence", "shap_dependence_panel", "Model Explanation"),
        ("umap", "umap_scatter_grouped", "Data Geometry"),
        ("roc", "roc_curve_binary", "Prediction Performance"),
    ],
)
def test_display_pack_figure_plan_routes_query_only_through_medical_family_catalog(
    query: str,
    template_id: str,
    audit_family: str,
) -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={"query": query},
        max_recommendations=5,
    )

    assert payload["status"] == "display_plan_ready"
    assert payload["recommended_template"]["template_id"] == template_id
    assert payload["recommended_template"]["audit_family"] == audit_family
    assert payload["figure_request"]["medical_figure_template_seed_ids"]
    assert "medical_figure_family_route" in payload["recommended_template"]["recommendation_reasons"]


def test_display_pack_figure_plan_migrates_explicit_legacy_alias_to_canonical_template() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "evidence_figure",
            "template_id": "time_dependent_roc_comparison_panel",
            "query": "time dependent roc",
        },
        max_recommendations=3,
    )

    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["status"] == "display_plan_ready"
    assert payload["recommended_template"]["template_id"] == "time_dependent_roc_horizon"
    assert payload["recommended_template"]["migration_status"] == "canonical"
    assert payload["requested_template_migration"]["status"] == "migrated_alias_to_canonical"
    assert payload["requested_template_migration"]["requested_template_id"] == "time_dependent_roc_comparison_panel"
    assert payload["requested_template_migration"]["canonical_template_id"] == "time_dependent_roc_horizon"


def test_display_pack_figure_plan_uses_close_template_as_adaptable_baseline() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Custom Mortality Discrimination",
            "paper_family": "custom_journal_family",
            "preferred_renderer_family": "r_ggplot2",
            "input_schema_ref": "schemas/custom_roc_payload.schema.json",
            "query": "roc",
        },
        max_recommendations=3,
    )

    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["status"] == "display_plan_ready"
    assert payload["agent_manual_template_selection_required"] is False
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["recommended_template"]["renderer_family"] == "r_ggplot2"
    assert payload["recommended_template"]["template_fit_policy"] == (
        "adaptable_baseline_not_exact_contract"
    )
    assert payload["recommended_template"]["adaptation_required"] is True
    assert {
        hint["code"]
        for hint in payload["recommended_template"]["adaptation_hints"]
    } >= {
        "audit_family_adaptation_required",
        "paper_family_adaptation_required",
        "input_schema_adaptation_required",
    }
    assert set(payload["recommended_template"]["adaptation_boundary"]["allowed_layers"]) >= {
        "layout",
        "labels_and_caption",
        "style_tokens",
    }
    assert "data_values" in payload["recommended_template"]["adaptation_boundary"]["forbidden_layers"]
    assert "statistical_estimates" in payload["recommended_template"]["adaptation_boundary"]["forbidden_layers"]
    assert set(payload["minimum_fit_floor"]["hard_constraints"]) >= {
        "figure_kind_compatible",
        "explicit_template_id_match_when_requested",
    }
    assert payload["publication_readiness_verdict"] is False


def test_display_pack_figure_plan_explicit_template_id_remains_hard_selection() -> None:
    payload = display_pack_figure_plan(
        repo_root=REPO_ROOT,
        figure_request={
            "figure_kind": "evidence_figure",
            "template_id": "not-a-real-template",
            "query": "roc",
        },
    )

    assert payload["status"] == "blocked"
    assert payload["recommended_template"] is None
    assert payload["typed_blocker"]["blocked_reason"] == "display_template_not_found"
    assert payload["typed_blocker"]["requested_template_id"] == "not-a-real-template"
    assert payload["agent_manual_template_selection_required"] is False


def test_display_pack_orchestrate_compiles_current_owner_delta_into_render_next_step(tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)
    _write_prepared_dependency_environment(paper_root)
    payload = display_pack_orchestrate(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        current_owner_delta={
            "action_type": "artifact_display_surface_materialization_required",
            "owner": "publication_display",
            "work_unit_id": "figure-roc",
            "work_unit_fingerprint": "sha256:display",
            "display_intent": "Generate a primary ROC figure for prediction performance.",
        },
        claim_ref="claim:primary-model-discrimination",
        data_ref="data:analysis/roc_payload.json",
        paper_target="jama",
        check_runtime_dependencies=False,
    )

    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "ready_to_render"
    assert payload["figure_intent"]["planning_root"] == "current_owner_delta"
    assert payload["figure_request"]["claim_ref"] == "claim:primary-model-discrimination"
    assert payload["figure_request"]["data_ref"] == "data:analysis/roc_payload.json"
    assert payload["figure_request"]["audit_family"] == "Prediction Performance"
    assert payload["figure_request"]["preferred_renderer_family"] == "r_ggplot2"
    assert payload["plan"]["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["preflight"]["status"] == "ready"
    assert payload["preflight"]["dependency_environment"]["status"] == "prepared"
    assert payload["preflight"]["dependency_environment"]["requirement_profile_ref"] == (
        "display-packs/fenggaolab.org.medical-display-core/renderer_dependency_profile.json"
    )
    assert payload["preflight"]["dependency_environment"]["lock_ref"] == (
        "paper/build/dependency_environment_lock.json"
    )
    assert payload["preflight"]["dependency_environment"]["receipt_ref"] == (
        "paper/build/dependency_environment_receipt.json"
    )
    assert payload["preflight"]["dependency_environment"]["run_context_ref"] == (
        "paper/build/dependency_run_context.json"
    )
    assert payload["preflight"]["dependency_environment"]["doctor_status"] == "pass"
    assert payload["preflight"]["dependency_environment"]["forbidden_claims"][
        "dependency_environment_receipt_means_publication_ready"
    ] is False
    assert payload["quality_floor"]["checks"]["template_selected"] is True
    assert payload["agent_manual_template_selection_required"] is False
    assert payload["publication_readiness_verdict"] is False
    assert payload["next_callable"] == "display-pack-render"


def test_display_pack_orchestrate_routes_missing_claim_and_data_refs() -> None:
    payload = display_pack_orchestrate(
        repo_root=REPO_ROOT,
        intent="Need a ROC figure for prediction performance.",
        check_runtime_dependencies=False,
    )

    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "needs_repair"
    assert payload["next_callable"] == "display-pack-repair"
    assert {item["code"] for item in payload["typed_repair_routes"]} >= {
        "claim_ref_missing",
        "data_ref_missing",
    }


def test_display_pack_preflight_reports_missing_paper_style_profile(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    paper_root.mkdir()

    payload = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="roc_curve_binary",
        check_runtime_dependencies=False,
    )

    assert payload["surface_kind"] == "display_pack_agent_preflight"
    assert payload["status"] == "blocked"
    assert payload["style_profile"]["status"] == "missing"
    assert payload["dependency_environment"]["status"] == "missing_prepared_receipt"
    assert payload["dependency_environment"]["doctor_status"] == "planned_missing"
    assert {item["code"] for item in payload["blocking_findings"]} >= {
        "publication_style_profile_missing",
    }
    assert "dependency_environment_not_prepared" not in {item["code"] for item in payload["blocking_findings"]}


def test_display_pack_preflight_blocks_missing_dependency_environment_by_default(tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)

    payload = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="roc_curve_binary",
        check_runtime_dependencies=True,
    )

    assert payload["surface_kind"] == "display_pack_agent_preflight"
    assert payload["status"] == "blocked"
    assert payload["dependency_environment"]["status"] == "missing_prepared_receipt"
    assert payload["dependency_environment"]["requirement_profile_ref"] == (
        "display-packs/fenggaolab.org.medical-display-core/renderer_dependency_profile.json"
    )
    assert payload["dependency_environment"]["lock_ref"] == "paper/build/dependency_environment_lock.json"
    assert payload["dependency_environment"]["receipt_ref"] == "paper/build/dependency_environment_receipt.json"
    assert payload["dependency_environment"]["run_context_ref"] == "paper/build/dependency_run_context.json"
    assert payload["dependency_environment"]["doctor_status"] == "planned_missing"
    assert payload["dependency_environment"]["authority_boundary"]["canonical_substrate_owner"] == "OPL Framework"
    assert payload["dependency_environment"]["forbidden_claims"][
        "dependency_environment_lock_means_visual_audit_clear"
    ] is False
    assert {item["code"] for item in payload["blocking_findings"]} >= {
        "dependency_environment_not_prepared",
    }
    dependency_route = next(
        item for item in payload["typed_repair_routes"] if item["code"] == "dependency_environment_not_prepared"
    )
    assert dependency_route["repair_owner"] == "OPL Framework"
    assert dependency_route["layer"] == "dependency_environment"


def test_display_pack_preflight_blocks_cohort_flow_without_ggconsort_capable_receipt(tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)

    payload = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="cohort_flow_figure",
        check_runtime_dependencies=True,
    )

    requirements = payload["dependency_environment"]["dependency_requirements"]
    requirement = next(item for item in requirements if item["profile_id"] == "r_ggplot2_ggconsort_reporting_flow_v1")
    packages = {item["name"]: item for item in requirement["language_package_requirements"]}

    assert payload["status"] == "blocked"
    assert payload["dependency_environment"]["status"] == "missing_prepared_receipt"
    assert requirement["surface_role"] == "ggconsort_capable_reporting_flow_dependency_intent"
    assert requirement["mature_dependency_intent"]["preferred_package"] == "ggconsort"
    assert requirement["mature_dependency_intent"]["fallback_generated_renderer_claims_ggconsort"] is False
    assert requirement["render_contract"]["checked_in_renderer_family"] == "python"
    assert requirement["render_contract"]["checked_in_renderer_uses_ggconsort"] is False
    assert packages["ggconsort"]["required"] is True
    assert {item["code"] for item in payload["blocking_findings"]} >= {"dependency_environment_not_prepared"}
    assert payload["repair_owner"] == "OPL Framework"


def test_display_pack_preflight_reports_cohort_flow_prepared_ggconsort_capable_profile(tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)
    _write_prepared_dependency_environment(paper_root)

    payload = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="cohort_flow_figure",
        check_runtime_dependencies=True,
    )

    requirement = next(
        item
        for item in payload["dependency_environment"]["dependency_requirements"]
        if item["profile_id"] == "r_ggplot2_ggconsort_reporting_flow_v1"
    )

    assert payload["status"] == "ready"
    assert payload["dependency_environment"]["status"] == "prepared"
    assert payload["r_runtime"]["required"] is True
    assert payload["r_runtime"]["status"] == "delegated_to_opl_dependency_environment"
    assert requirement["mature_dependency_intent"]["family"] == "ggconsort_capable_reporting_flow"
    assert requirement["render_contract"]["checked_in_renderer_is_generated_fallback"] is True
    assert payload["templates"][0]["dependency_requirements"][0]["profile_id"] == (
        "r_ggplot2_ggconsort_reporting_flow_v1"
    )


def test_display_pack_preflight_blocks_direct_raw_input_for_summary_only_template(tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)

    payload = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="roc_curve_binary",
        figure_request={"analysis_input_state": "labels_and_scores"},
        check_runtime_dependencies=False,
    )

    assert payload["status"] == "blocked"
    assert payload["blocking_findings"][0]["code"] == "analysis_summary_required_before_display_render"
    assert payload["next_callable"] == "materialize_validated_analysis_summary_before_display_render"
    assert payload["typed_repair_routes"][0]["layer"] == "analysis_materialization"


def test_display_pack_preflight_checks_embedding_backend_dependencies_only_for_matching_templates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from med_autoscience import display_pack_agent as agent

    paper_root = _styled_paper_root(tmp_path)
    observed_exprs: list[str] = []

    class _Completed:
        returncode = 0
        stdout = "ggplot2 TRUE\nggsci TRUE\ngrid TRUE\njsonlite TRUE\nRtsne FALSE\nuwot FALSE\n"
        stderr = ""

    def _fake_run(argv, *, capture_output, text, check, timeout):  # noqa: ANN001
        observed_exprs.append(argv[2])
        return _Completed()

    monkeypatch.setattr(agent.shutil, "which", lambda name: "/usr/bin/Rscript" if name == "Rscript" else None)
    monkeypatch.setattr(agent.subprocess, "run", _fake_run)

    roc = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="roc_curve_binary",
        check_runtime_dependencies=True,
    )
    tsne = display_pack_preflight(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        template_id="tsne_scatter_grouped",
        check_runtime_dependencies=True,
    )

    assert roc["r_runtime"]["packages"] == {
        "ggplot2": True,
        "ggsci": True,
        "grid": True,
        "jsonlite": True,
    }
    assert roc["r_runtime"]["status"] == "present"
    assert tsne["r_runtime"]["packages"]["Rtsne"] is False
    assert tsne["r_runtime"]["status"] == "missing_dependency"
    assert "uwot" not in tsne["r_runtime"]["packages"]
    assert "requireNamespace(\"Rtsne\"" in observed_exprs[-1]
    assert "requireNamespace(\"uwot\"" not in observed_exprs[-1]


def test_display_pack_render_returns_agent_receipt_around_scaffold_render(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    _write_prepared_dependency_environment(paper_root)
    payload_path = tmp_path / "roc-payload.json"
    _write_roc_payload(payload_path)

    payload = display_pack_render(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Prediction Performance",
            "preferred_renderer_family": "r_ggplot2",
            "query": "roc",
            "data_payload_file": str(payload_path),
            "figure_id": "F1",
            "claim_ref": "claim:primary",
            "cohort_ref": "cohort:demo",
            "endpoint_ref": "endpoint:mortality",
            "risk_horizon": "5y",
        },
    )

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "publication_manifested"
    assert payload["dependency_environment"]["status"] == "prepared"
    assert payload["publication_readiness_verdict"] is False
    assert payload["render_result"]["figures"][0]["template_id"] == (
        "fenggaolab.org.medical-display-core::roc_curve_binary"
    )
    assert (paper_root / "build" / "display_pack_publication_manifest.json").is_file()
    assert (paper_root / "build" / "display_pack_lock.json").is_file()
    assert (paper_root / "figure_visual_audit_receipt.json").is_file()
    assert (paper_root / "figure_render_receipt.json").is_file()
    assert payload["receipt_refs"]["figure_render_receipt"] == "paper/figure_render_receipt.json"
    assert payload["receipt_refs"]["dependency_environment_receipt"] == (
        "paper/build/dependency_environment_receipt.json"
    )
    assert payload["receipt_refs"]["figure_workflow_packet"] == "paper/figure_workflow_packet.json"
    figure_receipt = json.loads((paper_root / "figure_render_receipt.json").read_text(encoding="utf-8"))
    assert figure_receipt["dependency_environment"]["receipt_ref"] == (
        "paper/build/dependency_environment_receipt.json"
    )
    assert figure_receipt["figures"][0]["dependency_environment"]["run_context_fingerprint"] == (
        "sha256:test-display-env-run-context"
    )
    assert figure_receipt["authority_boundary"][
        "dependency_environment_can_authorize_publication_readiness"
    ] is False
    manifest = json.loads((paper_root / "build" / "display_pack_publication_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dependency_environment"]["run_context_ref"] == "paper/build/dependency_run_context.json"
    assert manifest["authority_boundary"]["renderer_code_must_not_install_packages"] is True
    assert (paper_root / "figure_workflow_packet.json").is_file()
    workflow_packet = json.loads((paper_root / "figure_workflow_packet.json").read_text(encoding="utf-8"))
    assert workflow_packet["workflow_status"] == "audit_clear"
    assert workflow_packet["figures"][0]["render_inspect_revise"]["visual_audit_final_status"] == "clear"
    assert payload["render_result"]["figure_workflow_packet"]["workflow_status"] == "audit_clear"


def test_display_pack_render_fail_closes_missing_dependency_environment(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    payload_path = tmp_path / "roc-payload.json"
    _write_roc_payload(payload_path)

    payload = display_pack_render(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        figure_request={
            "figure_kind": "evidence_figure",
            "audit_family": "Prediction Performance",
            "preferred_renderer_family": "r_ggplot2",
            "query": "roc",
            "data_payload_file": str(payload_path),
            "figure_id": "F1",
        },
    )

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "blocked"
    assert payload["dependency_environment"]["status"] == "missing_prepared_receipt"
    assert payload["typed_blocker"]["code"] == "dependency_environment_not_prepared"
    assert payload["typed_blocker"]["repair_owner"] == "OPL Framework"
    assert payload["publication_readiness_verdict"] is False
    assert not (paper_root / "figure_render_receipt.json").exists()


def test_display_pack_render_fail_closes_cohort_flow_missing_ggconsort_capable_receipt(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    payload_path = tmp_path / "cohort-flow-payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "shell_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
                "display_id": "cohort_flow_figure",
                "title": "Participant flow",
                "layout_mode": "participant_flow",
                "steps": [{"step_id": "screened", "label": "Screened", "n": 100}],
                "exclusions": [],
                "endpoint_inventory": [],
                "design_panels": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = display_pack_render(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        figure_request={
            "template_id": "cohort_flow_figure",
            "data_payload_file": str(payload_path),
            "figure_id": "F1",
        },
    )

    requirement = payload["dependency_environment"]["dependency_requirements"][0]

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "blocked"
    assert payload["dependency_environment"]["status"] == "missing_prepared_receipt"
    assert requirement["profile_id"] == "r_ggplot2_ggconsort_reporting_flow_v1"
    assert requirement["render_contract"]["checked_in_renderer_uses_ggconsort"] is False
    assert payload["typed_blocker"]["code"] == "dependency_environment_not_prepared"
    assert payload["typed_blocker"]["repair_owner"] == "OPL Framework"
    assert not (paper_root / "figure_render_receipt.json").exists()


def test_display_pack_render_blocks_raw_input_when_direct_template_id_is_summary_only(tmp_path: Path) -> None:
    paper_root = tmp_path / "paper"
    payload_path = tmp_path / "roc-payload.json"
    _write_roc_payload(payload_path)

    payload = display_pack_render(
        repo_root=REPO_ROOT,
        paper_root=paper_root,
        figure_request={
            "template_id": "roc_curve_binary",
            "data_payload_file": str(payload_path),
            "analysis_input_state": "labels_and_scores",
        },
    )

    assert payload["surface_kind"] == "display_pack_agent_render_receipt"
    assert payload["status"] == "blocked"
    assert payload["typed_blocker"]["blocked_reason"] == "analysis_summary_required_before_display_render"
    assert payload["typed_blocker"]["route_hint"] == (
        "materialize_validated_analysis_summary_before_display_render"
    )
    assert payload["next_callable"] == "display-pack-repair"


def test_cli_display_pack_agent_plan_loads_figure_request_json(capsys) -> None:
    exit_code = cli.main(
        [
            "publication",
            "display-pack-agent-plan",
            "--repo-root",
            str(REPO_ROOT),
            "--figure-request-json",
            json.dumps(
                {
                    "figure_kind": "evidence_figure",
                    "audit_family": "Prediction Performance",
                    "preferred_renderer_family": "r_ggplot2",
                    "query": "roc",
                }
            ),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"


def test_cli_display_pack_agent_orchestrate_accepts_current_owner_delta_json(capsys, tmp_path: Path) -> None:
    paper_root = _styled_paper_root(tmp_path)
    exit_code = cli.main(
        [
            "publication",
            "display-pack-agent-orchestrate",
            "--repo-root",
            str(REPO_ROOT),
            "--paper-root",
            str(paper_root),
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "display_pack_orchestrate",
                    "display_intent": "Create ROC figure for model discrimination.",
                }
            ),
            "--claim-ref",
            "claim:roc",
            "--data-ref",
            "data:roc",
            "--skip-runtime-dependency-check",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "ready_to_render"
    assert payload["plan"]["recommended_template"]["template_id"] == "roc_curve_binary"
