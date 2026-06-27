from __future__ import annotations

from .common import (
    CORE_PACK_MODULE_ROOT,
    CORE_PACK_ROOT,
    CORE_PACK_SRC_ROOT,
    REPO_ROOT,
    SimpleNamespace,
    _candidate_request,
    importlib,
    json,
    os,
    subprocess,
    sys,
    tempfile,
    tomllib,
    Path,
)
from med_autoscience.display_pack_gallery_parts.lidocaineq_coverage import (
    LIDOCAINEQ_COVERAGE_ITEMS,
)


def test_core_pack_evidence_renderer_is_split_into_maintainable_modules() -> None:
    legacy_single_file = CORE_PACK_MODULE_ROOT / "evidence_figures.py"
    evidence_package = CORE_PACK_MODULE_ROOT / "evidence_figures"

    assert not legacy_single_file.exists()
    assert (evidence_package / "__init__.py").exists()

    module_line_counts = {
        path.relative_to(CORE_PACK_MODULE_ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for path in evidence_package.rglob("*.py")
    }

    assert module_line_counts
    assert module_line_counts["evidence_figures/__init__.py"] <= 220
    assert max(module_line_counts.values()) <= 1500


def test_core_pack_illustration_shells_are_split_into_maintainable_modules() -> None:
    legacy_single_file = CORE_PACK_MODULE_ROOT / "illustration_shells.py"
    illustration_package = CORE_PACK_MODULE_ROOT / "illustration_shells"

    assert not legacy_single_file.exists()
    assert (illustration_package / "__init__.py").exists()

    module_line_counts = {
        path.relative_to(CORE_PACK_MODULE_ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for path in illustration_package.rglob("*.py")
    }

    assert module_line_counts
    assert module_line_counts["illustration_shells/__init__.py"] <= 80
    assert max(module_line_counts.values()) <= 1500


def test_core_pack_evidence_renderer_exports_only_r_entrypoint() -> None:
    sys.path.insert(0, str(CORE_PACK_SRC_ROOT))
    module = importlib.import_module("fenggaolab_org_medical_display_core.evidence_figures")

    assert callable(module.render_r_evidence_figure)
    assert not hasattr(module, "render_python_evidence_figure")


def test_core_pack_r_ggplot2_templates_do_not_reference_python_bridge() -> None:
    r_templates = []
    for manifest_path in sorted((CORE_PACK_ROOT / "templates").glob("*/template.toml")):
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        if payload["kind"] == "evidence_figure" and payload["renderer_family"] == "r_ggplot2":
            r_templates.append(payload["template_id"])
            assert payload["execution_mode"] == "subprocess"
            assert payload["entrypoint"] == "Rscript render.R --request {request_json}"
            assert "render_r_evidence_figure" not in payload["entrypoint"]
            assert (manifest_path.parent / "render.R").is_file()

    assert len(r_templates) == 34


def test_cohort_flow_materialization_manifest_uses_pack_local_ggconsort_subprocess() -> None:
    manifest_path = CORE_PACK_ROOT / "templates" / "cohort_flow_figure" / "template.toml"
    payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["kind"] == "illustration_shell"
    assert payload["renderer_family"] == "r_ggplot2"
    assert payload["execution_mode"] == "subprocess"
    assert payload["entrypoint"] == "Rscript render.R --request {request_json}"


def test_cohort_flow_checked_in_ggconsort_renderer_asset_does_not_install_packages() -> None:
    render_path = CORE_PACK_ROOT / "templates" / "cohort_flow_figure" / "render.R"
    source = render_path.read_text(encoding="utf-8")

    assert render_path.is_file()
    assert 'requireNamespace("ggconsort", quietly = TRUE)' in source
    assert "library(dplyr)" in source
    assert "install.packages" not in source
    assert "pak::" not in source
    assert "renv::install" not in source
    assert "remotes::install" not in source
    assert "BiocManager::install" not in source
    for call in (
        "ggconsort::cohort_start",
        "ggconsort::cohort_label",
        "ggconsort::consort_box_add",
        "ggconsort::consort_arrow_add",
        "ggconsort::geom_consort",
        "ggconsort::theme_consort",
    ):
        assert call in source


def test_alluvial_transition_checked_in_renderer_uses_ggalluvial_without_fallback_or_installs() -> None:
    manifest_path = CORE_PACK_ROOT / "templates" / "alluvial_transition" / "template.toml"
    render_path = CORE_PACK_ROOT / "templates" / "alluvial_transition" / "render.R"
    renderer_source = (
        CORE_PACK_ROOT
        / "rlib"
        / "medicaldisplaycore"
        / "lidocaineq_publication_renderers.R"
    ).read_text(encoding="utf-8")
    payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["renderer_family"] == "r_ggplot2"
    assert payload["execution_mode"] == "subprocess"
    assert payload["entrypoint"] == "Rscript render.R --request {request_json}"
    assert render_path.is_file()
    assert 'requireNamespace("ggalluvial", quietly = TRUE)' in renderer_source
    assert "ggalluvial::geom_alluvium" in renderer_source
    assert "ggalluvial::geom_stratum" in renderer_source
    assert "ggalluvial::stat_stratum" in renderer_source
    assert "build_alluvial_segment_dataframe" not in renderer_source
    for forbidden in (
        "install.packages",
        "pak::",
        "renv::install",
        "remotes::install",
        "BiocManager::install",
    ):
        assert forbidden not in renderer_source


def test_lidocaineq_specialized_renderers_use_mature_packages_without_installing_packages() -> None:
    ml_omics_source = (
        CORE_PACK_ROOT
        / "rlib"
        / "medicaldisplaycore"
        / "lidocaineq_ml_omics_renderers.R"
    ).read_text(encoding="utf-8")
    publication_source = (
        CORE_PACK_ROOT
        / "rlib"
        / "medicaldisplaycore"
        / "lidocaineq_publication_renderers.R"
    ).read_text(encoding="utf-8")

    assert 'requireNamespace("maftools", quietly = TRUE)' in ml_omics_source
    assert "maftools::read.maf" in ml_omics_source
    assert "maftools::oncoplot" in ml_omics_source
    assert '"lidocaine_base_graphics_plot"' in ml_omics_source
    assert "ComplexHeatmap::oncoPrint" not in ml_omics_source
    assert 'requireNamespace("ggradar", quietly = TRUE)' in publication_source
    assert "ggradar::ggradar" in publication_source

    for source in (ml_omics_source, publication_source):
        for forbidden in (
            "install.packages",
            "pak::",
            "renv::install",
            "remotes::install",
            "BiocManager::install",
        ):
            assert forbidden not in source


def test_core_pack_renderer_migration_ledger_covers_all_evidence_templates() -> None:
    ledger = json.loads((CORE_PACK_ROOT / "renderer_migration_ledger.json").read_text(encoding="utf-8"))
    records = ledger["records"]
    manifest_ids = []
    for manifest_path in sorted((CORE_PACK_ROOT / "templates").glob("*/template.toml")):
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_ids.append(payload["template_id"])

    records_by_template = {item["template_id"]: item for item in records}
    assert sorted(records_by_template) == sorted(manifest_ids)
    assert ledger["summary"]["current_template_count"] == 37
    assert ledger["summary"]["current_evidence_template_count"] == 34
    assert ledger["summary"]["current_r_ggplot2_subprocess_evidence_count"] == 34
    assert ledger["summary"]["retired_alias_template_count"] == 42
    assert ledger["summary"]["python_evidence_retained_count"] == 0
    assert "retired_python_evidence_template_count" not in ledger["summary"]
    assert "retired_python_evidence_template_ids" not in ledger
    assert {item["migration_lane"] for item in records} == {"CANONICAL_CURRENT"}
    assert {item["migration_status"] for item in records} == {"current_canonical_template"}
    assert "retired_aliases" in ledger
    assert {item["template_id"] for item in ledger["retired_aliases"]}.isdisjoint(records_by_template)
    assert records_by_template["risk_layering_monotonic_bars"]["migration_status"] == "current_canonical_template"
    assert records_by_template["time_dependent_roc_horizon"]["migration_status"] == "current_canonical_template"
    assert records_by_template["time_to_event_multihorizon_calibration_panel"]["migration_status"] == "current_canonical_template"
    assert records_by_template["time_to_event_decision_curve"]["migration_status"] == "current_canonical_template"


def test_core_pack_current_evidence_renderers_are_r_subprocess_defaults() -> None:
    ledger = json.loads((CORE_PACK_ROOT / "renderer_migration_ledger.json").read_text(encoding="utf-8"))
    current_records = [
        item
        for item in ledger["records"]
        if item["kind"] == "evidence_figure"
        and item["renderer_family"] == "r_ggplot2"
    ]

    assert len(current_records) == 34
    for record in current_records:
        template_root = CORE_PACK_ROOT / "templates" / record["template_id"]
        render_path = template_root / "render.R"
        assert render_path.is_file(), record["template_id"]
        assert record["renderer_family"] == "r_ggplot2"
        assert record["execution_mode"] == "subprocess"
        assert record["entrypoint"] == "Rscript render.R --request {request_json}"
        assert record["render_script_path"] == "render.R"
        assert record["migration_lane"] == "CANONICAL_CURRENT"
        assert record["migration_status"] == "current_canonical_template"
        wrapper_source = render_path.read_text(encoding="utf-8")
        assert f'expected_template_id = "{record["template_id"]}"' in wrapper_source


def test_core_pack_renderer_dependency_profile_declares_r_subprocess_runtime() -> None:
    profile = json.loads((CORE_PACK_ROOT / "renderer_dependency_profile.json").read_text(encoding="utf-8"))
    r_profile = next(item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_evidence_subprocess_v1")
    reporting_flow_profile = next(
        item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_ggconsort_reporting_flow_v1"
    )
    alluvial_profile = next(
        item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_alluvial_transition_v1"
    )
    maftools_profile = next(
        item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_maftools_oncoplot_v1"
    )
    ggradar_profile = next(
        item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_ggradar_profile_v1"
    )
    candidate_profile = next(
        item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_p1_comparison_subprocess_v1"
    )
    r_packages = r_profile["language_packages"]["r"]
    package_names = {item["name"] for item in r_packages}
    packages_by_name = {item["name"]: item for item in r_packages}
    reporting_flow_packages = {item["name"]: item for item in reporting_flow_profile["language_packages"]["r"]}

    assert r_profile["renderer_family"] == "r_ggplot2"
    assert r_profile["execution_mode"] == "subprocess"
    assert r_profile["entrypoint_pattern"] == "Rscript render.R --request {request_json}"
    assert {"jsonlite", "ggplot2", "ggsci", "grid", "patchwork", "gridExtra"} <= package_names
    assert packages_by_name["patchwork"]["template_ids"] == ["kaplan_meier_grouped"]
    assert packages_by_name["patchwork"]["required"] is True
    assert packages_by_name["gridExtra"]["template_ids"] == ["table1_baseline_characteristics"]
    assert packages_by_name["gridExtra"]["required"] is True
    assert "ggalluvial" not in package_names
    assert "maftools" not in package_names
    assert "ggradar" not in package_names
    alluvial_packages = {item["name"]: item for item in alluvial_profile["language_packages"]["r"]}
    maftools_packages = {item["name"]: item for item in maftools_profile["language_packages"]["r"]}
    ggradar_packages = {item["name"]: item for item in ggradar_profile["language_packages"]["r"]}
    assert alluvial_profile["template_ids"] == [
        "alluvial_transition",
        "fenggaolab.org.medical-display-core::alluvial_transition",
    ]
    assert alluvial_profile["surface_role"] == "ggalluvial_capable_state_transition_dependency_intent"
    assert alluvial_packages["ggalluvial"]["required"] is True
    assert alluvial_profile["render_contract"]["checked_in_renderer_uses_ggalluvial"] is True
    assert alluvial_profile["render_contract"]["prepared_dependency_receipt_required_before_render"] is True
    assert maftools_profile["template_ids"] == [
        "genomic_alteration_landscape_panel",
        "fenggaolab.org.medical-display-core::genomic_alteration_landscape_panel",
    ]
    assert maftools_profile["surface_role"] == "maftools_oncoplot_mutation_landscape_dependency_intent"
    assert {"jsonlite", "ggplot2", "ggsci", "grid", "maftools"} <= set(maftools_packages)
    assert maftools_packages["maftools"]["required"] is True
    assert maftools_packages["maftools"]["source"] == {
        "type": "github",
        "repo": "PoisonAlien/maftools",
        "upstream_package_manager": "BiocManager",
    }
    assert maftools_profile["render_contract"]["checked_in_renderer_uses_maftools"] is True
    assert maftools_profile["render_contract"]["checked_in_renderer_uses_base_graphics_device"] is True
    assert maftools_profile["render_contract"]["prepared_dependency_receipt_required_before_render"] is True
    assert ggradar_profile["template_ids"] == [
        "radar_profile",
        "fenggaolab.org.medical-display-core::radar_profile",
    ]
    assert ggradar_profile["surface_role"] == "ggradar_radial_profile_dependency_intent"
    assert {"jsonlite", "ggplot2", "ggsci", "grid", "ggradar"} <= set(ggradar_packages)
    assert ggradar_packages["ggradar"]["required"] is True
    assert ggradar_packages["ggradar"]["source"] == {"type": "github", "repo": "ricardo-bion/ggradar"}
    assert ggradar_profile["render_contract"]["checked_in_renderer_uses_ggradar"] is True
    assert ggradar_profile["render_contract"]["prepared_dependency_receipt_required_before_render"] is True
    assert packages_by_name["Rtsne"]["template_ids"] == ["tsne_scatter_grouped"]
    assert packages_by_name["uwot"]["template_ids"] == ["umap_scatter_grouped"]
    assert r_profile["shared_helper_ref"] == "rlib/medicaldisplaycore/evidence_renderer.R"
    assert r_profile["template_wrapper_ref"] == "templates/<template_id>/render.R"
    assert reporting_flow_profile["renderer_family"] == "r_ggplot2"
    assert reporting_flow_profile["execution_mode"] == "subprocess"
    assert reporting_flow_profile["surface_role"] == "ggconsort_capable_reporting_flow_dependency_intent"
    assert reporting_flow_profile["template_ids"] == [
        "cohort_flow_figure",
        "fenggaolab.org.medical-display-core::cohort_flow_figure",
    ]
    assert reporting_flow_packages["dplyr"]["required"] is True
    assert reporting_flow_packages["ggconsort"]["required"] is True
    assert reporting_flow_profile["mature_dependency_intent"]["preferred_package"] == "ggconsort"
    assert reporting_flow_profile["mature_dependency_intent"]["fallback_generated_renderer_claims_ggconsort"] is False
    assert reporting_flow_profile["render_contract"]["checked_in_renderer_family"] == "r_ggplot2"
    assert reporting_flow_profile["render_contract"]["checked_in_execution_mode"] == "subprocess"
    assert reporting_flow_profile["render_contract"]["checked_in_renderer_is_generated_fallback"] is False
    assert reporting_flow_profile["render_contract"]["checked_in_renderer_uses_ggconsort"] is True
    assert reporting_flow_profile["render_contract"]["checked_in_renderer_ref"] == (
        "templates/cohort_flow_figure/render.R"
    )
    assert reporting_flow_profile["render_contract"]["prepared_dependency_receipt_required_before_render"] is True
    assert candidate_profile["renderer_family"] == "r_ggplot2"
    assert candidate_profile["execution_mode"] == "subprocess"
    assert candidate_profile["entrypoint_pattern"] == "Rscript render_candidate.R --request {request_json}"
    assert candidate_profile["shared_helper_ref"] == "rlib/medicaldisplaycore/evidence_renderer.R"
    assert candidate_profile["candidate_helper_ref"] == "rlib/medicaldisplaycore/candidate_renderer.R"
    assert candidate_profile["template_wrapper_ref"] == "templates/<template_id>/render_candidate.R"
    assert candidate_profile["surface_role"] == "legacy_comparison_receipt"
    assert candidate_profile["default_renderer_profile_ref"] == "r_ggplot2_evidence_subprocess_v1"
    assert candidate_profile["publication_readiness_verdict"] is False


def test_lidocaineq_reference_coverage_contract_lists_all_33_reference_items() -> None:
    assert len(LIDOCAINEQ_COVERAGE_ITEMS) == 33
    reference_ids = [item.reference_template_id for item in LIDOCAINEQ_COVERAGE_ITEMS]
    assert len(reference_ids) == len(set(reference_ids))
    assert "baseline_table" in reference_ids
    assert "embedding_umap_tsne" in reference_ids
    embedding_item = next(item for item in LIDOCAINEQ_COVERAGE_ITEMS if item.reference_template_id == "embedding_umap_tsne")
    assert embedding_item.mas_template_id == "umap_scatter_grouped"
    assert embedding_item.required_mas_template_ids == (
        "pca_scatter_grouped",
        "tsne_scatter_grouped",
        "umap_scatter_grouped",
    )
    assert {item.mas_template_id for item in LIDOCAINEQ_COVERAGE_ITEMS} <= {
        path.parent.name
        for path in (CORE_PACK_ROOT / "templates").glob("*/template.toml")
    }
    assert set(embedding_item.required_mas_template_ids) <= {
        path.parent.name
        for path in (CORE_PACK_ROOT / "templates").glob("*/template.toml")
    }


def test_docs_gallery_manifest_reports_complete_lidocaineq_coverage_when_built() -> None:
    manifest_path = REPO_ROOT / "docs" / "delivery" / "medical-display" / "examples" / "gallery_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    coverage = manifest["lidocaineq_reference_coverage"]

    assert coverage["reference_template_count"] == 33
    assert coverage["covered_reference_template_count"] == 33
    assert coverage["coverage_complete"] is True
    assert coverage["missing_or_downgraded_reference_template_ids"] == []
    assert coverage["mapping_relation_counts"] == {
        "direct_current_template": 18,
        "renamed_current_template": 9,
        "retired_alias_to_current_template": 6,
    }
    assert coverage["replacement_template_count"] == 15
    assert coverage["retired_alias_reference_template_count"] == 6
    assert coverage["do_not_restore_legacy_alias_count"] == 6
    assert {item["reference_template_id"] for item in coverage["items"]} == {
        item.reference_template_id for item in LIDOCAINEQ_COVERAGE_ITEMS
    }
    embedding_item = next(item for item in coverage["items"] if item["reference_template_id"] == "embedding_umap_tsne")
    assert embedding_item["mas_template_ids"] == [
        "pca_scatter_grouped",
        "tsne_scatter_grouped",
        "umap_scatter_grouped",
    ]
    assert embedding_item["covered_mas_template_ids"] == [
        "pca_scatter_grouped",
        "tsne_scatter_grouped",
        "umap_scatter_grouped",
    ]
    assert embedding_item["missing_or_downgraded_mas_template_ids"] == []
    assert embedding_item["actual_source_renderers"] == {
        "pca_scatter_grouped": "LidocaineQ/Figure_Template::embedding_umap_tsne",
        "umap_scatter_grouped": "LidocaineQ/Figure_Template::embedding_umap_tsne",
        "tsne_scatter_grouped": "LidocaineQ/Figure_Template::embedding_umap_tsne",
    }
    retired_alias_items = {
        item["reference_template_id"]: item
        for item in coverage["items"]
        if item["mapping_relation"] == "retired_alias_to_current_template"
    }
    assert set(retired_alias_items) == {
        "violin_box",
        "bar_stacked",
        "scatter_correlation",
        "waterfall",
        "sankey_alluvial",
        "radar",
    }
    assert all(item["do_not_restore_legacy_alias"] is True for item in retired_alias_items.values())
    assert {item["legacy_alias_status"] for item in retired_alias_items.values()} == {"retired_do_not_restore"}
    assert manifest["surface_kind"] == "display_pack_gallery_docs_manifest"
    assert manifest["asset_ref_base"] == "docs/delivery/medical-display/examples"
    assert manifest["asset_ref_docs_mirror"] == "docs/delivery/medical-display/examples"
    assert manifest["source_manifest_schema_version"] == 9
    assert manifest["quality_summary"]["gallery_lower_bound_admission_status"] == (
        "gallery_lower_bound_passed_requires_paper_audit"
    )
