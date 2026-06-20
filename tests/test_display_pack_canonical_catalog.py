from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from med_autoscience.display_pack_canonical_catalog import load_canonical_template_catalog
from med_autoscience.display_pack_gallery_catalog import (
    ai_adaptation_policy,
    canonical_family_ontology,
    canonical_family_wording,
    gallery_display_records,
    gallery_template_family_ontology,
    non_visual_canonical_records,
    read_template_records,
    visual_gallery_records,
)
from med_autoscience.display_pack_gallery_parts.quality import build_quality_audit_markdown
from med_autoscience.display_pack_gallery_parts.payloads import _load_seed_r_payloads
from med_autoscience.display_pack_gallery_parts.status_writer import build_gallery_status_markdown
from med_autoscience.medical_figure_family_catalog import load_medical_figure_family_catalog
from med_autoscience.display_pack_loader import load_enabled_local_display_template_records


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "display-packs" / "fenggaolab.org.medical-display-core"
TEMPLATE_ROOT = PACK_ROOT / "templates"


def test_canonical_template_catalog_maps_full_template_inventory() -> None:
    catalog = load_canonical_template_catalog(PACK_ROOT)
    assert catalog is not None
    records = load_enabled_local_display_template_records(REPO_ROOT, inventory_scope="all")
    template_ids = {record.template_manifest.template_id for record in records}

    assert set(catalog.canonical_template_ids) == template_ids
    assert set(catalog.alias_template_ids).isdisjoint(template_ids)
    assert len(catalog.canonical_template_ids) == 31
    assert len(catalog.alias_template_ids) == 35
    assert len(catalog.entries_by_template_id) == 66
    responsibility_counts = {}
    for template_id in catalog.canonical_template_ids:
        entry = catalog.entries_by_template_id[template_id]
        responsibility_counts[entry.analysis_responsibility] = (
            responsibility_counts.get(entry.analysis_responsibility, 0) + 1
        )
    assert responsibility_counts == {
        "computed_in_template": 3,
        "illustration_shell": 2,
        "table_shell": 1,
        "validated_summary_required": 25,
    }
    for template_id in catalog.canonical_template_ids:
        entry = catalog.entries_by_template_id[template_id]
        profile = entry.publication_quality_profile
        assert entry.medical_family_ids
        assert profile["medical_family_ids"] == list(entry.medical_family_ids)
        assert profile["starter_recipe_ids"]
        assert profile["style_profile_ids"]
        assert profile["palette_token_ids"]
        assert profile["qa_gate_ids"]
        assert profile["starter_templates_are_floor_not_ceiling"] is True
        assert "layout" in profile["ai_may_change"]
        assert "source_data_and_statistics_refs" in profile["ai_must_preserve"]

    migrated_alias = catalog.entries_by_template_id["time_dependent_roc_comparison_panel"]
    assert migrated_alias.migration_status == "migrated_alias"
    assert migrated_alias.canonical_template_id == "time_dependent_roc_horizon"
    assert migrated_alias.default_visible is False
    assert migrated_alias.analysis_responsibility == "validated_summary_required"
    assert migrated_alias.medical_family_ids == ("discrimination_curve",)

    current_template = catalog.entries_by_template_id["time_dependent_roc_horizon"]
    assert current_template.migration_status == "canonical"
    assert current_template.default_visible is True
    assert current_template.analysis_input_state == "validated_display_payload"
    assert "time_dependent_roc_comparison_panel" in current_template.aliases


def test_gallery_family_ontology_exposes_canonical_wording_without_alias_noise() -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    ontology = gallery_template_family_ontology(records)
    visual_records = visual_gallery_records(records)
    evidence_gallery_records = gallery_display_records(records)
    non_visual_records = non_visual_canonical_records(records)

    assert len(ontology) == 28
    assert len(visual_records) == 28
    assert len(evidence_gallery_records) == 28
    assert {record.kind for record in evidence_gallery_records} == {"evidence_figure"}
    assert {record.renderer_family for record in evidence_gallery_records} == {"r_ggplot2"}
    assert [record.template_id for record in non_visual_records] == [
        "cohort_flow_figure",
        "submission_graphical_abstract",
        "table1_baseline_characteristics",
    ]
    assert {entry["canonical_template_id"] for entry in ontology}.issubset(
        {record.template_id for record in visual_records}
    )
    assert "time_dependent_roc_horizon" in {record.template_id for record in evidence_gallery_records}
    assert "time_dependent_roc_comparison_panel" not in {record.template_id for record in evidence_gallery_records}
    assert "table1_baseline_characteristics" not in {entry["canonical_template_id"] for entry in ontology}
    assert "single_cell_atlas_overview_panel" not in {entry["canonical_template_id"] for entry in ontology}
    assert "phenotype_gap_structure_figure" not in {entry["canonical_template_id"] for entry in ontology}
    assert not {record.template_id for record in visual_records if record.renderer_family == "python"}
    assert not [
        record.template_id
        for record in visual_records
        if record.kind == "evidence_figure" and record.renderer_family == "python"
    ]

    roc = next(record for record in records if record.template_id == "roc_curve_binary")
    wording = canonical_family_wording(roc)
    assert wording == (
        "ROC Curve (Prediction Performance): binary_discrimination_roc_curve"
    )
    assert "time_dependent_roc_horizon" not in wording


def test_default_gallery_r_templates_have_runtime_seed_payloads_without_generic_fallback() -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    gallery_records = gallery_display_records(records)
    seed_payloads = _load_seed_r_payloads(records)

    assert len(gallery_records) == 28
    assert {
        "calibration_curve_binary",
        "cumulative_incidence_grouped",
        "forest_effect_main",
        "heatmap_group_comparison",
        "pr_curve_binary",
        "roc_curve_binary",
        "time_dependent_roc_horizon",
    } <= set(seed_payloads)
    assert {
        record.template_id
        for record in gallery_records
        if seed_payloads[record.template_id].get("caption")
        == "Synthetic gallery preview payload for local visual inspection only."
    } == set()


def test_gallery_manifest_dry_readback_reserves_family_policy_metadata() -> None:
    module_path = REPO_ROOT / "scripts" / "build-display-pack-gallery.py"
    spec = importlib.util.spec_from_file_location("build_display_pack_gallery", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    rendered = {
        record.template_id: module.RenderedAsset(status="not_rendered", reason="dry_readback")
        for record in records
    }
    manifest = module._build_manifest(
        records=records,
        rendered=rendered,
        baseline_rendered={},
        publish_docs=False,
    )

    figure_family_policy = manifest["figure_family_policy"]
    assert figure_family_policy == {
        "policy_version": 2,
        "current_metadata_source": "medical_figure_family_catalog",
        "core_catalog_ref": "contracts/medical-figure-family-catalog/",
        "gallery_template_metadata_source": "display_pack_canonical_template_catalog",
        "core_catalog_dependency": "loaded_via_medical_figure_family_catalog_loader",
        "default_gallery_surface": "canonical_current_r_ggplot2_evidence_templates",
        "alias_handling": "retired_duplicate_template_ids_are_migration_index_entries_not_gallery_cards",
        "non_visual_handling": "design_flow_shells_and_table_shells_preserved_in_manifest_without_entering_ggplot2_evidence_gallery",
        "analysis_responsibility_source": "display_pack_canonical_template_catalog",
        "analysis_responsibility_required": True,
        "raw_analysis_input_policy": "raw_analysis_inputs_must_route_to_computed_in_template_workflows_or_upstream_analysis_materialization",
        "medical_figure_family_mapping_required": True,
        "starter_recipe_profile_required": True,
        "style_palette_qa_profile_required": True,
        "renderer_policy": {
            "policy_version": 1,
            "data_evidence_first_class_renderer": "r_ggplot2",
            "data_evidence_default_rule": (
                "current evidence_figure templates are retained only when their renderer is R/ggplot2; "
                "a Python evidence template can re-enter only as a current audited template with documented "
                "advantage over the R/ggplot2 baseline"
            ),
            "python_evidence_default_allowed": False,
            "python_evidence_retention_rule": (
                "not retained in the current pack without documented advantage proof and visual audit"
            ),
            "python_evidence_allowed_roles": [],
            "design_flow_renderer_rule": (
                "illustration_shell templates may use SVG, Python composition, or imagegen-assisted "
                "art direction because they do not act as statistical evidence authority"
            ),
            "programmatic_precision_required_for": ["evidence_figure"],
            "composition_expression_allowed_for": ["illustration_shell"],
        },
        "machine_boundary": "core_catalog_and_gallery_metadata_only_not_source_truth_statistical_truth_or_publication_readiness_authority",
    }
    core_catalog = load_medical_figure_family_catalog()
    assert manifest["schema_version"] == 9
    assert manifest["ai_adaptation_policy"] == ai_adaptation_policy()
    assert manifest["figure_contract_policy"]["policy_id"] == "mas_nature_skills_informed_figure_contract.v1"
    assert manifest["publication_polish_policy"]["policy_id"] == "mas_publication_polish_policy.v1"
    assert manifest["publication_polish_policy"]["palette_scale_policy"]["per_plot_palette_drift_allowed"] is False
    assert manifest["publication_quality_profile_coverage"] == {
        "schema_version": 1,
        "current_template_count": 31,
        "complete_profile_template_count": 31,
        "complete_profile_percent": 100,
        "medical_family_missing_template_ids": [],
        "starter_recipe_missing_template_ids": [],
        "style_profile_missing_template_ids": [],
        "palette_token_missing_template_ids": [],
        "qa_gate_missing_template_ids": [],
    }
    assert manifest["analysis_responsibility_counts"] == {
        "computed_in_template": 3,
        "illustration_shell": 2,
        "table_shell": 1,
        "validated_summary_required": 25,
    }
    assert manifest["analysis_responsibility_policy"]["raw_request_fail_closed"] is True
    assert manifest["template_surface_policy"]["template_analysis_responsibility_required"] is True
    assert manifest["template_surface_policy"][
        "validated_summary_templates_fail_closed_on_raw_analysis_requests"
    ] is True
    assert manifest["template_surface_policy"]["composition_recipe_routing_required"] is True
    assert manifest["template_surface_policy"]["composition_recipes_are_page_level_not_gallery_cards"] is True
    assert manifest["composition_recipe_surface"]["policy"]["policy_id"] == (
        "mas_medical_figure_composition_recipes.v1"
    )
    assert manifest["composition_recipe_surface"]["composition_recipe_count"] == 6
    assert {
        item["recipe_id"] for item in manifest["composition_recipe_surface"]["recipes"]
    } == {
        "clinical_triptych_prediction",
        "schematic_led_composite",
        "asymmetric_genomics_figure",
        "image_plate_plus_quantification",
        "single_cell_atlas_storyboard",
        "model_validation_dashboard",
    }
    assert "matrix_heatmap" in {
        item["family"] for item in manifest["publication_polish_policy"]["high_risk_family_checks"]
    }
    assert manifest["figure_contract_policy"]["observed_head"] == "5d2ba1dee1c087be6de8f4a8aad4b27f04974be9"
    assert "query_resolves_through_medical_figure_family_catalog_before_template_scoring" in manifest[
        "figure_contract_policy"
    ]["mas_adaptations"]
    assert manifest["canonical_family_count"] == len(manifest["canonical_family_ontology"]) == core_catalog.family_count
    assert manifest["gallery_template_family_count"] == len(manifest["gallery_template_family_ontology"]) == 28
    assert manifest["canonical_representative_template_count"] == 28
    assert manifest["active_template_count"] == len(manifest["templates"]) == 28
    assert manifest["evidence_gallery_template_count"] == 28
    assert manifest["current_template_count"] == 31
    assert manifest["retired_alias_template_count"] == 35
    assert manifest["non_visual_canonical_template_count"] == len(manifest["non_visual_inventory"]) == 3
    assert manifest["catalog_default_visible_template_count"] == 31
    assert manifest["default_visible_template_count"] == 31
    assert len(manifest["canonical_category_ontology"]) == 12
    assert "discrimination_curve" in {item["family_id"] for item in manifest["canonical_family_ontology"]}
    assert {item["kind"] for item in manifest["templates"]} == {"evidence_figure"}
    assert {item["renderer_family"] for item in manifest["templates"]} == {"r_ggplot2"}
    assert all(item["migration_status"] == "canonical" for item in manifest["templates"])
    assert all(item["visual_gallery_visible"] is True for item in manifest["templates"])
    template_by_id = {item["template_id"]: item for item in manifest["templates"]}
    assert template_by_id["umap_scatter_grouped"]["analysis_responsibility"] == "computed_in_template"
    assert template_by_id["umap_scatter_grouped"]["analysis_input_state"] == "raw_feature_matrix"
    assert template_by_id["umap_scatter_grouped"]["medical_family_ids"] == ["dimension_reduction_scatter"]
    assert "embedding_scatter" in template_by_id["umap_scatter_grouped"]["publication_quality_profile"][
        "starter_recipe_ids"
    ]
    assert template_by_id["roc_curve_binary"]["analysis_responsibility"] == "validated_summary_required"
    assert template_by_id["roc_curve_binary"]["medical_family_ids"] == ["discrimination_curve"]
    assert "roc_pr_curve" in template_by_id["roc_curve_binary"]["publication_quality_profile"][
        "starter_recipe_ids"
    ]
    assert {item["template_id"] for item in manifest["non_visual_inventory"]} == {
        "cohort_flow_figure",
        "submission_graphical_abstract",
        "table1_baseline_characteristics",
    }
    assert all(item["visual_gallery_visible"] is False for item in manifest["non_visual_inventory"])
    assert "time_dependent_roc_horizon" in {item["template_id"] for item in manifest["templates"]}
    assert "time_dependent_roc_comparison_panel" in {
        item["template_id"] for item in manifest["retired_alias_index"]
    }
    assert not [
        item["template_id"]
        for item in manifest["templates"]
        if item["kind"] == "evidence_figure" and item["renderer_family"] == "python"
    ]
    assert manifest["renderer_policy_completion"]["default_python_evidence_template_count"] == 0
    assert manifest["renderer_policy_completion"]["default_r_ggplot2_evidence_template_count"] == 28
    assert manifest["renderer_policy_completion"]["all_r_ggplot2_evidence_template_count"] == 28
    assert manifest["renderer_policy_completion"]["python_evidence_retained_count"] == 0
    assert manifest["renderer_policy_completion"]["default_illustration_shell_count"] == 2
    assert manifest["layout_sidecar_readback"]["rendered_layout_sidecar_count"] == 0
    assert manifest["layout_sidecar_readback"]["missing_renderer_metrics"] == []
    assert manifest["layout_sidecar_readback"]["missing_style_profile"] == []
    assert manifest["palette_policy"]["matrix_heatmap_uses_shared_palette_roles"] is True
    assert manifest["palette_policy"]["heatmap_sequential_roles"] == [
        "heatmap_seq_low",
        "heatmap_seq_mid",
        "heatmap_seq_high",
    ]
    assert manifest["quality_audit"]["completion_by_category"]
    assert manifest["templates"][0]["canonical_family_wording"]
    assert manifest["quality_audit"]["overall_status"] == "not_publication_ready"
    assert manifest["quality_audit"]["publication_ready_claim_authorized"] is False
    assert manifest["quality_audit"]["blocked_template_count"] == 28
    assert manifest["quality_audit"]["publication_quality_profile_coverage"][
        "complete_profile_percent"
    ] == 100
    assert manifest["quality_audit"]["figure_contract_policy"]["policy_id"] == (
        "mas_nature_skills_informed_figure_contract.v1"
    )
    assert manifest["quality_audit"]["publication_polish_policy"]["policy_id"] == (
        "mas_publication_polish_policy.v1"
    )
    assert manifest["quality_audit"]["figure_workflow_policy"]["policy_id"] == (
        "mas_nature_skills_figure_workflow_lifecycle.v1"
    )
    assert manifest["quality_audit"]["composition_recipe_surface"]["composition_recipe_count"] == 6
    assert manifest["quality_audit"]["quality_policy"]["ai_authority"] == (
        "ai_may_freely_modify_template_structure_layout_palette_labels_and_composition_for_paper_specific_claim"
    )
    assert manifest["quality_audit"]["quality_policy"]["composition_recipe_policy"] == (
        "page_level_recipes_organize_primitives_without_becoming_duplicate_gallery_cards"
    )
    assert "core_conclusion_and_evidence_chain_locked" in manifest["quality_audit"]["quality_policy"][
        "required_before_paper_use"
    ]
    assert "storyboard_panel_hierarchy_declared" in manifest["quality_audit"]["quality_policy"][
        "required_workflow_before_paper_use"
    ]

    status_markdown = build_gallery_status_markdown(manifest)
    assert "Gallery evidence figures | 28" in status_markdown
    assert "Current canonical templates | 31" in status_markdown
    assert "Retired alias / duplicate ids | 35" in status_markdown
    assert "Current Python evidence templates | 0" in status_markdown
    assert "publication-ready claim authorized: `false`" in status_markdown
    assert "publication quality profile coverage: `31/31` (100%)" in status_markdown
    assert "publication polish policy: `mas_publication_polish_policy.v1`" in status_markdown
    assert "figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`" in status_markdown
    assert "Page-level composition recipes | 6" in status_markdown
    assert "composition recipe policy: `mas_medical_figure_composition_recipes.v1`" in status_markdown
    assert "| `clinical_triptych_prediction` | Clinical Prediction Triptych | primary_model_performance_summary |" in status_markdown
    assert "- `storyboard_panel_hierarchy_declared`" in status_markdown
    assert "| `computed_in_template` | 3 |" in status_markdown
    assert "| `validated_summary_required` | 25 |" in status_markdown

    quality_markdown = build_quality_audit_markdown(manifest["quality_audit"])
    assert "figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`" in quality_markdown
    assert "composition recipe policy: `mas_medical_figure_composition_recipes.v1`" in quality_markdown
    assert "| `single_cell_atlas_storyboard` | Single-cell or Spatial Atlas Storyboard | cell_state_geometry_or_spatial_context |" in quality_markdown
    assert "- `guide_legend_colorbar_overlap_checked_after_render`" in quality_markdown
