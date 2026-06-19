from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from med_autoscience.display_pack_canonical_catalog import load_canonical_template_catalog
from med_autoscience.display_pack_gallery_catalog import (
    ai_adaptation_policy,
    canonical_family_ontology,
    canonical_family_wording,
    gallery_template_family_ontology,
    non_visual_canonical_records,
    read_template_records,
    visual_gallery_records,
)
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

    assert set(catalog.canonical_template_ids).issubset(template_ids)
    assert set(catalog.alias_template_ids).issubset(template_ids)
    assert len(catalog.canonical_template_ids) >= 20
    assert len(catalog.alias_template_ids) >= 50
    assert len(catalog.entries_by_template_id) == len(template_ids)

    roc_alias = catalog.entries_by_template_id["time_dependent_roc_horizon"]
    assert roc_alias.migration_status == "migrated_alias"
    assert roc_alias.canonical_template_id == "roc_curve_binary"
    assert roc_alias.default_visible is False

    roc_canonical = catalog.entries_by_template_id["roc_curve_binary"]
    assert roc_canonical.migration_status == "canonical"
    assert roc_canonical.default_visible is True
    assert "time_dependent_roc_horizon" in roc_canonical.aliases


def test_gallery_family_ontology_exposes_canonical_wording_without_alias_noise() -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    ontology = gallery_template_family_ontology(records)
    visual_records = visual_gallery_records(records)
    non_visual_records = non_visual_canonical_records(records)

    assert len(ontology) == 18
    assert len(visual_records) == 18
    assert [record.template_id for record in non_visual_records] == ["table1_baseline_characteristics"]
    assert {entry["canonical_template_id"] for entry in ontology}.issubset(
        {record.template_id for record in visual_records}
    )
    assert "time_dependent_roc_horizon" not in {entry["canonical_template_id"] for entry in ontology}
    assert "table1_baseline_characteristics" not in {entry["canonical_template_id"] for entry in ontology}
    assert "single_cell_atlas_overview_panel" not in {entry["canonical_template_id"] for entry in ontology}
    assert "phenotype_gap_structure_figure" not in {entry["canonical_template_id"] for entry in ontology}
    assert {record.template_id for record in visual_records if record.renderer_family == "python"} == {
        "cohort_flow_figure",
        "submission_graphical_abstract",
    }
    assert not [
        record.template_id
        for record in visual_records
        if record.kind == "evidence_figure" and record.renderer_family == "python"
    ]

    roc = next(record for record in records if record.template_id == "roc_curve_binary")
    wording = canonical_family_wording(roc)
    assert wording == (
        "Prediction Curves (Prediction Performance): "
        "roc_pr_calibration_or_time_dependent_discrimination_curve"
    )
    assert "time_dependent_roc_horizon" not in wording


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
        "default_gallery_surface": "r_first_evidence_canonical_families_plus_design_shells",
        "alias_handling": "hidden_from_gallery_cards_preserved_in_migration_index",
        "non_visual_handling": "kept_in_manifest_inventory_hidden_from_image_gallery_cards",
        "renderer_policy": {
            "policy_version": 1,
            "data_evidence_first_class_renderer": "r_ggplot2",
            "data_evidence_default_rule": (
                "evidence_figure templates are default-visible only when the default renderer is "
                "R/ggplot2, unless a future catalog entry carries explicit Python advantage proof"
            ),
            "python_evidence_default_allowed": False,
            "python_evidence_allowed_roles": [
                "legacy_comparison",
                "migration_input",
                "paper_specific_explicit_request",
                "future_documented_advantage_with_visual_audit",
            ],
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
    assert manifest["schema_version"] == 7
    assert manifest["ai_adaptation_policy"] == ai_adaptation_policy()
    assert manifest["canonical_family_count"] == len(manifest["canonical_family_ontology"]) == core_catalog.family_count
    assert manifest["gallery_template_family_count"] == len(manifest["gallery_template_family_ontology"]) == 18
    assert manifest["active_template_count"] == len(manifest["templates"]) == 18
    assert manifest["non_visual_canonical_template_count"] == len(manifest["non_visual_inventory"]) == 1
    assert manifest["catalog_default_visible_template_count"] == 19
    assert manifest["default_visible_template_count"] == 19
    assert len(manifest["canonical_category_ontology"]) == 12
    assert "discrimination_curve" in {item["family_id"] for item in manifest["canonical_family_ontology"]}
    assert all(item["migration_status"] == "canonical" for item in manifest["templates"])
    assert all(item["default_visible"] is True for item in manifest["templates"])
    assert all(item["visual_gallery_visible"] is True for item in manifest["templates"])
    assert manifest["non_visual_inventory"][0]["template_id"] == "table1_baseline_characteristics"
    assert manifest["non_visual_inventory"][0]["visual_gallery_visible"] is False
    assert "time_dependent_roc_horizon" not in {item["template_id"] for item in manifest["templates"]}
    assert "time_dependent_roc_horizon" in {item["template_id"] for item in manifest["migration_index"]}
    assert not [
        item["template_id"]
        for item in manifest["templates"]
        if item["kind"] == "evidence_figure" and item["renderer_family"] == "python"
    ]
    assert manifest["renderer_policy_completion"]["default_python_evidence_template_count"] == 0
    assert manifest["renderer_policy_completion"]["default_r_ggplot2_evidence_template_count"] == 16
    assert manifest["renderer_policy_completion"]["default_illustration_shell_count"] == 2
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
    assert manifest["quality_audit"]["quality_policy"]["ai_authority"] == (
        "ai_may_freely_modify_template_structure_layout_palette_labels_and_composition_for_paper_specific_claim"
    )
