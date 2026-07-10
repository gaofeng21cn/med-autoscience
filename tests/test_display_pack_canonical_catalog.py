from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from med_autoscience.display_pack_canonical_catalog import load_canonical_template_catalog
from med_autoscience.display_pack_gallery_catalog import (
    ai_adaptation_policy,
    canonical_family_ontology,
    canonical_family_wording,
    design_gallery_records,
    gallery_display_records,
    gallery_visual_records,
    gallery_template_family_ontology,
    non_visual_canonical_records,
    reporting_flow_gallery_records,
    read_template_records,
    table_preview_gallery_records,
    visual_gallery_records,
)
from med_autoscience.display_pack_gallery.quality import build_quality_audit_markdown
from med_autoscience.display_pack_gallery.payloads import (
    GALLERY_R_DISPLAY_PAYLOADS,
    REGISTRY_GALLERY_CASES_FIXTURE_REF,
    _load_seed_r_payloads,
)
from med_autoscience.display_pack_gallery.rendering import _gallery_dependency_environment_for
from med_autoscience.display_pack_gallery.status_writer import build_gallery_status_markdown
from med_autoscience.display_pack_gallery.html import _render_html
from med_autoscience.medical_figure_family_catalog import load_medical_figure_family_catalog
from med_autoscience.display_pack_loader import load_enabled_local_display_template_records
from med_autoscience.display_pack_paths import core_medical_display_pack_root


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = core_medical_display_pack_root(REPO_ROOT)
TEMPLATE_ROOT = PACK_ROOT / "templates"


def _registry_gallery_fixture_payload() -> dict[str, object]:
    return json.loads((PACK_ROOT / REGISTRY_GALLERY_CASES_FIXTURE_REF).read_text(encoding="utf-8"))


def _write_registry_gallery_fixture(pack_root: Path, payload: dict[str, object]) -> None:
    fixture_path = pack_root / REGISTRY_GALLERY_CASES_FIXTURE_REF
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_canonical_template_catalog_maps_full_template_inventory() -> None:
    catalog = load_canonical_template_catalog(PACK_ROOT)
    assert catalog is not None
    records = load_enabled_local_display_template_records(REPO_ROOT, inventory_scope="all")
    template_ids = {record.template_manifest.template_id for record in records}

    assert set(catalog.canonical_template_ids) == template_ids
    assert set(catalog.alias_template_ids).isdisjoint(template_ids)
    assert len(catalog.canonical_template_ids) == 54
    assert len(catalog.alias_template_ids) == 40
    assert len(catalog.entries_by_template_id) == 94
    responsibility_counts = {}
    for template_id in catalog.canonical_template_ids:
        entry = catalog.entries_by_template_id[template_id]
        responsibility_counts[entry.analysis_responsibility] = (
            responsibility_counts.get(entry.analysis_responsibility, 0) + 1
        )
    assert responsibility_counts == {
        "computed_in_template": 3,
        "illustration_shell": 1,
        "table_shell": 9,
        "validated_summary_required": 41,
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


def test_table_preview_gallery_only_exposes_table_shells_with_preview_renderers() -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    non_visual_records = non_visual_canonical_records(records)
    table_preview_records = table_preview_gallery_records(records)

    assert len(records) == 54
    assert len(non_visual_records) == 9
    assert {record.kind for record in non_visual_records} == {"table_shell"}
    assert [record.template_id for record in table_preview_records] == [
        "table1_baseline_characteristics",
    ]


def test_gallery_family_ontology_exposes_canonical_wording_without_alias_noise() -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    ontology = gallery_template_family_ontology(records)
    visual_records = visual_gallery_records(records)
    evidence_gallery_records = gallery_display_records(records)
    reporting_flow_records = reporting_flow_gallery_records(records)
    design_records = design_gallery_records(records)
    table_preview_records = table_preview_gallery_records(records)
    all_gallery_visual_records = gallery_visual_records(records)
    non_visual_records = non_visual_canonical_records(records)

    assert len(ontology) == 43
    assert len(visual_records) == 43
    assert len(evidence_gallery_records) == 43
    assert len(reporting_flow_records) == 1
    assert len(design_records) == 1
    assert len(table_preview_records) == 1
    assert len(all_gallery_visual_records) == 46
    assert {record.kind for record in evidence_gallery_records} == {"evidence_figure"}
    assert {record.renderer_family for record in evidence_gallery_records} == {"r_ggplot2"}
    assert {record.kind for record in design_records} == {"illustration_shell"}
    assert {record.renderer_family for record in design_records} == {"python"}
    assert [record.template_id for record in reporting_flow_records] == ["cohort_flow_figure"]
    assert [record.template_id for record in design_records] == ["submission_graphical_abstract"]
    assert [record.template_id for record in table_preview_records] == [
        "table1_baseline_characteristics",
    ]
    assert [record.template_id for record in non_visual_records] == [
        "supplementary_adult_sensitivity",
        "supplementary_missingness_atlas",
        "supplementary_variable_ascertainment",
        "table1_baseline_characteristics",
        "table2_phenotype_gap_summary",
        "table3_transition_site_support_summary",
        "table4_adult_multidimensional_phenotype",
        "table5_xiangya_psychometabolic_profile",
        "table6_adult_bmi_waist_central_adiposity",
    ]
    assert {entry["canonical_template_id"] for entry in ontology}.issubset(
        {record.template_id for record in visual_records}
    )
    assert "time_dependent_roc_horizon" in {record.template_id for record in evidence_gallery_records}
    assert "time_dependent_roc_comparison_panel" not in {record.template_id for record in evidence_gallery_records}
    assert "table1_baseline_characteristics" not in {entry["canonical_template_id"] for entry in ontology}
    assert "single_cell_atlas_overview_panel" not in {entry["canonical_template_id"] for entry in ontology}
    assert "phenotype_gap_structure_figure" in {entry["canonical_template_id"] for entry in ontology}
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
    seed_payloads = _load_seed_r_payloads(records, pack_root=PACK_ROOT)
    fixture = _registry_gallery_fixture_payload()
    fixture_cases = fixture["cases"]
    assert isinstance(fixture_cases, dict)
    fixture_payloads = {
        template_id: case["payload"]
        for template_id, case in fixture_cases.items()
    }

    assert len(gallery_records) == 43
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
    assert len(fixture_payloads) == 5
    assert set(fixture_payloads).isdisjoint(GALLERY_R_DISPLAY_PAYLOADS)
    for template_id, payload in fixture_payloads.items():
        assert seed_payloads[template_id] == payload
        assert payload["source_data_digest"] == "gallery-synthetic-preview"
        assert payload["preview_only"] is True
        assert payload["authority"] is False
        assert payload["publication_ready"] is False


def test_registry_gallery_fixture_is_required_from_bound_pack(tmp_path: Path) -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)

    with pytest.raises(FileNotFoundError, match="missing required Gallery fixture"):
        _load_seed_r_payloads(records, pack_root=tmp_path)


def test_registry_gallery_fixture_case_inventory_must_match_payload_gaps(tmp_path: Path) -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    fixture = _registry_gallery_fixture_payload()
    cases = fixture["cases"]
    assert isinstance(cases, dict)
    cases.pop(sorted(cases)[0])
    _write_registry_gallery_fixture(tmp_path, fixture)

    with pytest.raises(ValueError, match="case ids must exactly match"):
        _load_seed_r_payloads(records, pack_root=tmp_path)


def test_registry_gallery_fixture_rejects_authority_drift(tmp_path: Path) -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    fixture = _registry_gallery_fixture_payload()
    cases = fixture["cases"]
    assert isinstance(cases, dict)
    first_case = cases[sorted(cases)[0]]
    assert isinstance(first_case, dict)
    payload = first_case["payload"]
    assert isinstance(payload, dict)
    payload["authority"] = True
    _write_registry_gallery_fixture(tmp_path, fixture)

    with pytest.raises(ValueError, match="payload.authority must be False"):
        _load_seed_r_payloads(records, pack_root=tmp_path)


def test_registry_gallery_fixture_rejects_invalid_json(tmp_path: Path) -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    fixture_path = tmp_path / REGISTRY_GALLERY_CASES_FIXTURE_REF
    fixture_path.parent.mkdir(parents=True)
    fixture_path.write_text("{\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain valid JSON"):
        _load_seed_r_payloads(records, pack_root=tmp_path)


def test_gallery_dependency_environment_requires_explicit_prepared_run_context(
    monkeypatch,
) -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    cohort_flow = next(record for record in records if record.template_id == "cohort_flow_figure")
    roc = next(record for record in records if record.template_id == "roc_curve_binary")

    assert _gallery_dependency_environment_for(roc) == {}
    try:
        _gallery_dependency_environment_for(cohort_flow)
    except RuntimeError as exc:
        assert "requires OPL-prepared dependency run-context" in str(exc)
    else:
        raise AssertionError("cohort_flow_figure should fail closed without OPL run-context")

    monkeypatch.setenv("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_REF", "paper/build/dependency_run_context.json")
    monkeypatch.setenv("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_FINGERPRINT", "sha256:gallery")


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
        "current_template_count": 54,
        "complete_profile_template_count": 54,
        "complete_profile_percent": 100,
        "medical_family_missing_template_ids": [],
        "starter_recipe_missing_template_ids": [],
        "style_profile_missing_template_ids": [],
        "palette_token_missing_template_ids": [],
        "qa_gate_missing_template_ids": [],
    }
    assert manifest["analysis_responsibility_counts"] == {
        "computed_in_template": 3,
        "illustration_shell": 1,
        "table_shell": 9,
        "validated_summary_required": 41,
    }
    assert manifest["analysis_responsibility_policy"]["raw_request_fail_closed"] is True
    assert manifest["template_surface_policy"]["template_analysis_responsibility_required"] is True
    assert manifest["template_surface_policy"][
        "validated_summary_templates_fail_closed_on_raw_analysis_requests"
    ] is True
    assert manifest["template_surface_policy"]["composition_recipe_routing_required"] is True
    assert manifest["template_surface_policy"]["composition_recipes_are_page_level_not_gallery_cards"] is True
    assert manifest["template_surface_policy"][
        "composition_recipes_are_visible_in_gallery_storyboard_section"
    ] is True
    assert manifest["template_surface_policy"]["reporting_flow_dependency_profile"] == (
        "r_ggplot2_ggconsort_reporting_flow_v1"
    )
    assert manifest["template_surface_policy"]["reporting_flow_requires_ggconsort_capable_prepared_environment"] is True
    assert manifest["template_surface_policy"]["reporting_flow_generated_fallback_claims_ggconsort"] is False
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
    assert manifest["composition_recipe_gallery_count"] == 6
    assert manifest["composition_gallery_surface"]["surface_kind"] == "display_pack_composition_recipe_gallery"
    assert manifest["composition_gallery_surface"]["included_in_html_pdf"] is True
    assert manifest["composition_gallery_surface"]["composition_recipe_count"] == 6
    composition_by_id = {
        item["recipe_id"]: item
        for item in manifest["composition_gallery_surface"]["recipes"]
    }
    assert set(composition_by_id) == {
        "clinical_triptych_prediction",
        "schematic_led_composite",
        "asymmetric_genomics_figure",
        "image_plate_plus_quantification",
        "single_cell_atlas_storyboard",
        "model_validation_dashboard",
    }
    clinical_triptych = composition_by_id["clinical_triptych_prediction"]
    assert clinical_triptych["hero_panel_role"] == "primary_model_performance_summary"
    assert len(clinical_triptych["supporting_panel_roles"]) == 3
    assert {"discrimination_curve", "calibration_panel", "decision_curve_analysis"} <= set(
        clinical_triptych["evidence_primitive_family_ids"]
    )
    assert {"roc_curve_binary", "calibration_curve_binary", "decision_curve_binary"} <= set(
        clinical_triptych["preview_template_ids"]
    )
    assert clinical_triptych["programmatic_evidence_required"] is True
    assert clinical_triptych["design_shell_allowed"] is False
    assert clinical_triptych["quality_floor_only"] is True
    assert clinical_triptych["not_publication_ready"] is True
    for recipe in composition_by_id.values():
        assert recipe["supporting_panel_roles"]
        assert recipe["evidence_primitive_family_ids"]
        assert recipe["recommended_starter_recipe_ids"]
        assert recipe["default_layout"]
        assert recipe["guide_strategy"]
        assert recipe["label_strategy"]
        assert recipe["palette_tokens"]
        assert recipe["qa_gate_ids"]
        assert recipe["storyboard_panels"]
    assert "matrix_heatmap" in {
        item["family"] for item in manifest["publication_polish_policy"]["high_risk_family_checks"]
    }
    assert manifest["figure_contract_policy"]["observed_head"] == "5d2ba1dee1c087be6de8f4a8aad4b27f04974be9"
    assert "query_resolves_through_medical_figure_family_catalog_before_template_scoring" in manifest[
        "figure_contract_policy"
    ]["mas_adaptations"]
    assert manifest["canonical_family_count"] == len(manifest["canonical_family_ontology"]) == core_catalog.family_count
    assert manifest["gallery_template_family_count"] == len(manifest["gallery_template_family_ontology"]) == 43
    assert manifest["canonical_representative_template_count"] == 43
    assert manifest["active_template_count"] == len(manifest["templates"]) == 43
    assert manifest["evidence_gallery_template_count"] == 43
    assert manifest["reporting_flow_gallery_template_count"] == len(manifest["reporting_flow_gallery_templates"]) == 1
    assert manifest["design_gallery_template_count"] == len(manifest["design_gallery_templates"]) == 1
    assert manifest["table_preview_gallery_template_count"] == len(manifest["table_preview_gallery_templates"]) == 1
    assert manifest["visual_gallery_template_count"] == 46
    assert manifest["template_count"] == 46
    assert manifest["current_template_count"] == 54
    assert manifest["retired_alias_template_count"] == 40
    assert manifest["non_visual_canonical_template_count"] == len(manifest["non_visual_inventory"]) == 9
    assert manifest["catalog_default_visible_template_count"] == 54
    assert manifest["default_visible_template_count"] == 54
    assert len(manifest["canonical_category_ontology"]) == 13
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
        "supplementary_adult_sensitivity",
        "supplementary_missingness_atlas",
        "supplementary_variable_ascertainment",
        "table1_baseline_characteristics",
        "table2_phenotype_gap_summary",
        "table3_transition_site_support_summary",
        "table4_adult_multidimensional_phenotype",
        "table5_xiangya_psychometabolic_profile",
        "table6_adult_bmi_waist_central_adiposity",
    }
    design_inventory = {
        item["template_id"]: item
        for item in manifest["design_gallery_templates"]
    }
    reporting_flow_inventory = {
        item["template_id"]: item
        for item in manifest["reporting_flow_gallery_templates"]
    }
    table_preview_inventory = {
        item["template_id"]: item
        for item in manifest["table_preview_gallery_templates"]
    }
    assert set(reporting_flow_inventory) == {"cohort_flow_figure"}
    cohort_flow_dependency = reporting_flow_inventory["cohort_flow_figure"]["dependency_requirements"][0]
    assert cohort_flow_dependency["profile_id"] == "r_ggplot2_ggconsort_reporting_flow_v1"
    assert cohort_flow_dependency["mature_dependency_intent"]["preferred_package"] == "ggconsort"
    assert cohort_flow_dependency["mature_dependency_intent"]["fallback_generated_renderer_claims_ggconsort"] is False
    assert cohort_flow_dependency["render_contract"]["checked_in_renderer_family"] == "r_ggplot2"
    assert cohort_flow_dependency["render_contract"]["checked_in_renderer_is_generated_fallback"] is False
    assert cohort_flow_dependency["render_contract"]["checked_in_renderer_uses_ggconsort"] is True
    assert cohort_flow_dependency["render_contract"]["checked_in_renderer_ref"] == (
        "rlib/medicaldisplaycore/cohort_flow_renderer.R"
    )
    assert set(design_inventory) == {"submission_graphical_abstract"}
    assert set(table_preview_inventory) == {"table1_baseline_characteristics"}
    assert all(item["visual_gallery_visible"] is True for item in reporting_flow_inventory.values())
    assert all(item["visual_gallery_visible"] is True for item in design_inventory.values())
    assert all(item["visual_gallery_visible"] is True for item in table_preview_inventory.values())
    assert {
        item["template_id"]
        for item in manifest["non_visual_inventory"]
        if item["visual_gallery_visible"] is True
    } == {"table1_baseline_characteristics"}
    assert {
        item["template_id"]
        for item in manifest["non_visual_inventory"]
        if item["visual_gallery_visible"] is False
    } == {
        "supplementary_adult_sensitivity",
        "supplementary_missingness_atlas",
        "supplementary_variable_ascertainment",
        "table2_phenotype_gap_summary",
        "table3_transition_site_support_summary",
        "table4_adult_multidimensional_phenotype",
        "table5_xiangya_psychometabolic_profile",
        "table6_adult_bmi_waist_central_adiposity",
    }
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
    assert manifest["renderer_policy_completion"]["default_r_ggplot2_evidence_template_count"] == 43
    assert manifest["renderer_policy_completion"]["all_r_ggplot2_evidence_template_count"] == 43
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
    assert manifest["quality_audit"]["blocked_template_count"] == 43
    assert manifest["quality_audit"]["gallery_visual_blocked_template_count"] == 46
    assert manifest["quality_audit"]["gallery_lower_bound_admission_status"] == "gallery_lower_bound_blocked"
    assert manifest["quality_audit"]["reporting_flow_visual_template_count"] == 1
    assert manifest["quality_audit"]["design_visual_template_count"] == 1
    assert manifest["quality_audit"]["table_preview_visual_template_count"] == 1
    assert manifest["quality_audit"]["total_gallery_visual_template_count"] == 46
    assert {item["template_id"] for item in manifest["quality_audit"]["design_gallery_templates"]} == {
        "submission_graphical_abstract",
    }
    assert {item["template_id"] for item in manifest["quality_audit"]["reporting_flow_gallery_templates"]} == {
        "cohort_flow_figure",
    }
    assert {item["template_id"] for item in manifest["quality_audit"]["table_preview_gallery_templates"]} == {
        "table1_baseline_characteristics",
    }
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
    assert manifest["quality_audit"]["composition_gallery_surface"]["composition_recipe_count"] == 6
    assert manifest["quality_audit"]["quality_policy"]["ai_authority"] == (
        "ai_may_freely_modify_template_structure_layout_palette_labels_and_composition_for_paper_specific_claim"
    )
    assert manifest["quality_audit"]["quality_policy"]["composition_recipe_policy"] == (
        "page_level_recipes_organize_primitives_without_becoming_duplicate_gallery_cards"
    )
    scientific_floor = manifest["quality_audit"]["quality_policy"]["scientific_figure_quality_floor_policy"]
    assert scientific_floor["policy_id"] == "mas_scientific_figure_quality_floor.v1"
    assert scientific_floor["graphical_abstract_strategy"] == (
        "brief_first_reference_guided_ai_candidate_not_single_template_reuse"
    )
    assert scientific_floor["template_library_role"] == (
        "quality_floor_and_reviewable_starting_point_not_ceiling_or_publication_ready_authority"
    )
    assert "figure_brief_before_plotting" in scientific_floor["learned_scientific_figure_patterns"]
    assert "reference_selection_and_style_brief" in scientific_floor["learned_scientific_figure_patterns"]
    assert "reference_target_preserve_list" in scientific_floor["learned_scientific_figure_patterns"]
    assert "candidate_generation_before_owner_gate" in scientific_floor["learned_scientific_figure_patterns"]
    assert "critic_review_or_route_back" in scientific_floor["learned_scientific_figure_patterns"]
    assert "vector_export_when_possible" in scientific_floor["learned_scientific_figure_patterns"]
    assert "source_data_statistics_and_claim_refs_preserved" in scientific_floor[
        "learned_scientific_figure_patterns"
    ]
    assert "figure_brief_ref" in scientific_floor["required_before_gallery_or_paper_use"]
    assert "preserve_list_ref" in scientific_floor["required_before_gallery_or_paper_use"]
    assert "critic_review_ref" in scientific_floor["required_before_gallery_or_paper_use"]
    assert "owner_gate_ref" in scientific_floor["required_before_gallery_or_paper_use"]
    assert "publication_ready" in scientific_floor["forbidden_claims"]
    assert scientific_floor["rebuild_boundary"]["design_shell_graphical_abstract_reporting_flow"] == (
        "may_be_rebuilt_into_stronger_visual_systems_when_the_figure_brief_and_owner_gate_require_it"
    )
    assert scientific_floor["rebuild_boundary"]["r_ggplot2_evidence_figures"] == (
        "raise_quality_through_theme_size_qc_critic_gate_references_and_source_preservation_not_wholesale_manual_redraw"
    )
    assert "K-Dense-AI/scientific-agent-skills" in scientific_floor["external_learning_sources"]
    assert "google-research/papervizagent" in scientific_floor["external_learning_sources"]
    assert "VILA-Lab/FigMirror" in scientific_floor["external_learning_sources"]
    assert "keros68/abstract-fig" in scientific_floor["external_learning_sources"]
    assert "IyatomiLab/SciGA" in scientific_floor["external_learning_sources"]
    reference_learning = {item["source_id"]: item for item in scientific_floor["reference_learning_sources"]}
    assert reference_learning["abstract_fig_editable_source"]["url"] == "https://github.com/keros68/abstract-fig"
    assert "editable" in reference_learning["abstract_fig_editable_source"]["lesson"]
    assert reference_learning["sciga_graphical_abstract_dataset"]["url"] == "https://github.com/IyatomiLab/SciGA"
    assert "core_conclusion_and_evidence_chain_locked" in manifest["quality_audit"]["quality_policy"][
        "required_before_paper_use"
    ]
    assert "storyboard_panel_hierarchy_declared" in manifest["quality_audit"]["quality_policy"][
        "required_workflow_before_paper_use"
    ]

    status_markdown = build_gallery_status_markdown(manifest)
    assert "Gallery evidence figures | 43" in status_markdown
    assert "Gallery reporting flow figures | 1" in status_markdown
    assert "Gallery design figures | 1" in status_markdown
    assert "Gallery table preview figures | 1" in status_markdown
    assert "Gallery visual templates | 46" in status_markdown
    assert "Current canonical templates | 54" in status_markdown
    assert "Retired alias / duplicate ids | 40" in status_markdown
    assert "Current Python evidence templates | 0" in status_markdown
    assert "publication-ready claim authorized: `false`" in status_markdown
    assert "publication quality profile coverage: `54/54` (100%)" in status_markdown
    assert "blocked evidence templates after current render: `43`" in status_markdown
    assert "blocked gallery visual templates after current render: `46`" in status_markdown
    assert "publication polish policy: `mas_publication_polish_policy.v1`" in status_markdown
    assert "figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`" in status_markdown
    assert "Page-level composition recipes | 6" in status_markdown
    assert "Composition storyboard gallery pages | 6" in status_markdown
    assert "Python illustration shells visible as design cards: `true`" in status_markdown
    assert "| `cohort_flow_figure` | Cohort Flow Figure | r_ggplot2 | not_rendered |" in status_markdown
    assert "| `submission_graphical_abstract` | Submission Graphical Abstract | python | not_rendered |" in status_markdown
    assert "| `table1_baseline_characteristics` | Table 1 Baseline Characteristics | n/a | not_rendered |" in status_markdown
    assert "`table2_phenotype_gap_summary`" in status_markdown
    assert "`table3_transition_site_support_summary`" in status_markdown
    assert "composition recipe policy: `mas_medical_figure_composition_recipes.v1`" in status_markdown
    assert "| `clinical_triptych_prediction` | Clinical Prediction Triptych | primary_model_performance_summary | 3 |" in status_markdown
    assert "- `storyboard_panel_hierarchy_declared`" in status_markdown
    assert "| `computed_in_template` | 3 |" in status_markdown
    assert "| `illustration_shell` | 1 |" in status_markdown
    assert "| `validated_summary_required` | 41 |" in status_markdown

    quality_markdown = build_quality_audit_markdown(manifest["quality_audit"])
    assert "figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`" in quality_markdown
    assert "composition recipe policy: `mas_medical_figure_composition_recipes.v1`" in quality_markdown
    assert "composition storyboard gallery pages: `6`" in quality_markdown
    assert "通用科研做图 Quality Floor" in quality_markdown
    assert "policy: `mas_scientific_figure_quality_floor.v1`" in quality_markdown
    assert "AI executor freedom:" in quality_markdown
    assert "publication ready claim authorized: `false`" in quality_markdown
    assert "- `reference_target_preserve_list`" in quality_markdown
    assert "- `critic_review_ref`" in quality_markdown
    assert "- `design_shell_graphical_abstract_reporting_flow`:" in quality_markdown
    assert "- `google-research/papervizagent`" in quality_markdown
    assert "[abstract_fig_editable_source](https://github.com/keros68/abstract-fig)" in quality_markdown
    assert "[sciga_graphical_abstract_dataset](https://github.com/IyatomiLab/SciGA)" in quality_markdown
    assert "reporting flow visual template count: `1`" in quality_markdown
    assert "design visual template count: `1`" in quality_markdown
    assert "table preview visual template count: `1`" in quality_markdown
    assert "total Gallery visual template count: `46`" in quality_markdown
    assert "blocked evidence templates: `43`" in quality_markdown
    assert "blocked gallery visual templates: `46`" in quality_markdown
    assert "| `cohort_flow_figure` | Publication Shells and Tables | r_ggplot2 | `not_publication_ready` |" in quality_markdown
    assert "| `table1_baseline_characteristics` | Publication Shells and Tables | n/a | `not_publication_ready` |" in quality_markdown
    assert "| `table2_phenotype_gap_summary` |" not in quality_markdown
    assert "| `single_cell_atlas_storyboard` | Single-cell or Spatial Atlas Storyboard | cell_state_geometry_or_spatial_context | 3 |" in quality_markdown
    assert "- `guide_legend_colorbar_overlap_checked_after_render`" in quality_markdown


def test_gallery_html_exposes_composition_recipe_storyboards_without_counting_them_as_templates() -> None:
    records = read_template_records(PACK_ROOT, TEMPLATE_ROOT)
    rendered = {
        record.template_id: type(
            "Asset",
            (),
            {
                "status": "rendered",
                "preview_image_ref": f"assets/{record.template_id}.gallery.png",
                "image_ref": f"assets/{record.template_id}.png",
                "payload_ref": f"assets/{record.template_id}.payload.json",
                "layout_ref": f"assets/{record.template_id}.layout.json",
                "pdf_ref": f"assets/{record.template_id}.pdf",
                "svg_ref": "",
                "reason": "",
            },
        )()
        for record in records
    }

    html = _render_html(records, rendered, {})

    assert "<title>MAS 医学论文配图 Gallery</title>" in html
    assert "从论文论点到可审计图件" in html
    assert "页面级图页方案" in html
    assert "数据驱动报告流程图起点" in html
    assert "非数据设计图起点" in html
    assert html.count('class="composition-card"') == 6
    assert html.count('class="story-panel-image"') >= 20
    assert html.count('id="template-') == 46
    assert 'id="template-cohort_flow_figure"' in html
    assert 'id="template-submission_graphical_abstract"' in html
    assert 'id="template-table1_baseline_characteristics"' in html
    assert 'id="template-table2_phenotype_gap_summary"' not in html
    assert 'src="assets/cohort_flow_figure.gallery.png"' in html
    assert 'src="assets/submission_graphical_abstract.gallery.png"' in html
    assert "临床预测模型主图" in html
    assert "核心表达" in html
    assert "推荐面板组织" in html
    assert "证据边界" in html
    assert "R/ggplot2 数据证据图起点" in html
    assert "表达目的" in html
    assert "数据要求" in html
    assert "适用场景" in html
    assert "decision_curve_binary" in html
    assert "组学景观与功能后果图页" in html
    assert 'src="assets/roc_curve_binary.gallery.png"' in html
    assert 'src="assets/calibration_curve_binary.gallery.png"' in html
    assert 'src="assets/decision_curve_binary.gallery.png"' in html
    assert "storyboard 占位" in html
    assert "本页为图页组织示例，使用合成数据或示意性面板" in html
    assert "Python evidence: 0" not in html
    assert "默认 Python 数据证据模板" not in html


def test_mas_docs_gallery_review_package_is_externalized_to_scholarskills() -> None:
    docs_manifest_path = REPO_ROOT / "docs" / "delivery" / "medical-display" / "examples" / "gallery_manifest.json"
    docs_asset_root = docs_manifest_path.parent / "medical_display_gallery_assets"
    readme_path = docs_manifest_path.parent / "README.md"

    assert not docs_manifest_path.exists()
    assert not docs_asset_root.exists()
    assert readme_path.is_file()
    readme = readme_path.read_text(encoding="utf-8")
    assert "/Users/gaofeng/workspace/mas-scholar-skills/gallery/medical-display/" in readme
    assert "MAS 不在本目录维护 Display Pack gallery 发布包" in readme
    assert "gallery PDF / status / quality-audit mirror" in readme
