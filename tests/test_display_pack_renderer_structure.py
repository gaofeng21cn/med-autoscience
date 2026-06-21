from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import json
import subprocess
import tempfile
import tomllib

from med_autoscience.display_pack_gallery_parts.lidocaineq_coverage import (
    LIDOCAINEQ_COVERAGE_ITEMS,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PACK_MODULE_ROOT = (
    REPO_ROOT
    / "display-packs"
    / "fenggaolab.org.medical-display-core"
    / "src"
    / "fenggaolab_org_medical_display_core"
)
CORE_PACK_SRC_ROOT = CORE_PACK_MODULE_ROOT.parent
CORE_PACK_ROOT = REPO_ROOT / "display-packs" / "fenggaolab.org.medical-display-core"


def _candidate_request(
    *,
    template_id: str,
    payload: dict[str, object],
    output_dir: Path,
) -> Path:
    request_path = output_dir / f"{template_id}.request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "execution_mode": "subprocess",
                "renderer_family": "r_ggplot2",
                "figure_id": f"candidate-{template_id}",
                "template_id": f"fenggaolab.org.medical-display-core::{template_id}",
                "short_template_id": template_id,
                "display_payload": payload,
                "output_png_path": str(output_dir / f"{template_id}.png"),
                "output_pdf_path": str(output_dir / f"{template_id}.pdf"),
                "layout_sidecar_path": str(output_dir / f"{template_id}.layout.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return request_path


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


def test_cohort_flow_checked_in_renderer_uses_ggconsort_without_installing_packages() -> None:
    manifest_path = CORE_PACK_ROOT / "templates" / "cohort_flow_figure" / "template.toml"
    render_path = CORE_PACK_ROOT / "templates" / "cohort_flow_figure" / "render.R"
    payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    source = render_path.read_text(encoding="utf-8")

    assert payload["renderer_family"] == "r_ggplot2"
    assert payload["execution_mode"] == "subprocess"
    assert payload["entrypoint"] == "Rscript render.R --request {request_json}"
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
    alluvial_packages = {item["name"]: item for item in alluvial_profile["language_packages"]["r"]}
    assert alluvial_profile["template_ids"] == [
        "alluvial_transition",
        "fenggaolab.org.medical-display-core::alluvial_transition",
    ]
    assert alluvial_profile["surface_role"] == "ggalluvial_capable_state_transition_dependency_intent"
    assert alluvial_packages["ggalluvial"]["required"] is True
    assert alluvial_profile["render_contract"]["checked_in_renderer_uses_ggalluvial"] is True
    assert alluvial_profile["render_contract"]["prepared_dependency_receipt_required_before_render"] is True
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
    assert embedding_item.required_mas_template_ids == ("umap_scatter_grouped", "tsne_scatter_grouped")
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
    assert embedding_item["mas_template_ids"] == ["umap_scatter_grouped", "tsne_scatter_grouped"]
    assert embedding_item["covered_mas_template_ids"] == ["umap_scatter_grouped", "tsne_scatter_grouped"]
    assert embedding_item["missing_or_downgraded_mas_template_ids"] == []
    assert embedding_item["actual_source_renderers"] == {
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


def test_gallery_builder_fails_closed_without_opl_dependency_run_context(tmp_path: Path) -> None:
    script_path = REPO_ROOT / "scripts" / "build-display-pack-gallery.py"
    env = dict(os.environ)
    env.pop("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_PATH", None)
    env.pop("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_REF", None)
    env.pop("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_FINGERPRINT", None)
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--force-render",
            "--output-root",
            str(tmp_path / "gallery-output"),
        ],
        cwd=REPO_ROOT,
        env={**env, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode != 0
    assert "requires OPL-prepared dependency run-context" in result.stderr


def test_gallery_r_renderers_apply_opl_dependency_run_context(monkeypatch, tmp_path: Path) -> None:
    from med_autoscience.display_pack_gallery_catalog import TemplateRecord
    from med_autoscience.display_pack_gallery_parts import paths
    from med_autoscience.display_pack_gallery_parts import rendering

    paths.configure_output_paths(tmp_path / "gallery")
    run_context_path = tmp_path / "dependency_run_context.json"
    run_context_path.write_text(
        json.dumps(
                {
                    "surface_kind": "opl_runtime_environment_dependency_run_context",
                    "status": "prepared",
                    "selected_requirement_profile_ids": [
                        "r_ggplot2_evidence_subprocess_v1",
                        "r_ggplot2_alluvial_transition_v1",
                    ],
                    "binary_paths": {"Rscript": "/opt/opl/bin/Rscript"},
                    "env_vars": {
                    "OPL_RUNTIME_ENVIRONMENT_STATUS": "prepared",
                    "R_LIBS_USER": str(tmp_path / "opl-managed-r-lib"),
                },
                "execution_fingerprint": "sha256:test-opl-run-context",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_PATH", str(run_context_path))
    monkeypatch.setenv("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_FINGERPRINT", "sha256:test-opl-run-context")
    monkeypatch.setattr(
        rendering,
        "_load_r_gallery_payload",
        lambda template_id, seed_payloads: {"title": template_id},
    )
    monkeypatch.setattr(
        "med_autoscience.display_pack_gallery_parts.dependency_run_context._missing_required_r_packages",
        lambda **kwargs: [],
    )

    record = TemplateRecord(
        template_id="alluvial_transition",
        full_template_id="fenggaolab.org.medical-display-core::alluvial_transition",
        display_name="Alluvial Transition",
        kind="evidence_figure",
        audit_family="Publication",
        renderer_family="r_ggplot2",
        execution_mode="subprocess",
        entrypoint="Rscript render.R --request {request_json}",
        paper_proven=False,
        required_exports=("png", "pdf"),
        template_dir=CORE_PACK_ROOT / "templates" / "alluvial_transition",
        canonical_family_id="",
        canonical_family_title="",
        canonical_family_category="",
        canonical_template_id="alluvial_transition",
        figure_archetype="",
        migration_status="canonical",
        default_visible=True,
        migrated_alias_template_ids=(),
        migration_reason="",
        analysis_responsibility="",
        analysis_input_state="",
        medical_family_ids=(),
        publication_quality_profile={},
    )
    preview_record = TemplateRecord(
        template_id="table1_baseline_characteristics",
        full_template_id="fenggaolab.org.medical-display-core::table1_baseline_characteristics",
        display_name="Table 1 Baseline Characteristics",
        kind="table_shell",
        audit_family="Publication Shells and Tables",
        renderer_family="n/a",
        execution_mode="python_plugin",
        entrypoint="fenggaolab_org_medical_display_core.table_shells:render_table_shell",
        paper_proven=False,
        required_exports=("csv", "md"),
        template_dir=CORE_PACK_ROOT / "templates" / "table1_baseline_characteristics",
        canonical_family_id="",
        canonical_family_title="",
        canonical_family_category="",
        canonical_template_id="table1_baseline_characteristics",
        figure_archetype="",
        migration_status="canonical",
        default_visible=True,
        migrated_alias_template_ids=(),
        migration_reason="",
        analysis_responsibility="",
        analysis_input_state="",
        medical_family_ids=(),
        publication_quality_profile={},
    )
    calls: list[dict[str, object]] = []
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00"
        b"\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    def fake_run(argv, *, cwd, capture_output, text, check, timeout, env):
        request_path = Path(argv[-1])
        request_payload = json.loads(request_path.read_text(encoding="utf-8"))
        calls.append(
            {
                "argv": list(argv),
                "env": dict(env),
                "request": request_payload,
                "cwd": Path(cwd),
            }
        )
        Path(request_payload["output_png_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(request_payload["output_png_path"]).write_bytes(png_bytes)
        Path(request_payload["output_pdf_path"]).write_bytes(b"%PDF-1.4\n")
        Path(request_payload["layout_sidecar_path"]).write_text(
            json.dumps({"template_id": request_payload["short_template_id"]}) + "\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rendering.subprocess, "run", fake_run)

    rendering._render_r_template(record, {}, force_render=True)
    rendering._render_r_gallery_preview(preview_record, {}, force_render=True)

    assert len(calls) == 2
    assert {call["request"]["short_template_id"] for call in calls} == {
        "alluvial_transition",
        "table1_baseline_characteristics",
    }
    for call in calls:
        assert call["argv"][0] == "/opt/opl/bin/Rscript"
        assert call["env"]["R_LIBS_USER"] == str(tmp_path / "opl-managed-r-lib")
        assert call["env"]["OPL_RUNTIME_ENVIRONMENT_STATUS"] == "prepared"
        assert call["request"]["dependency_environment"] == {
            "status": "prepared",
            "run_context_ref": str(run_context_path),
            "run_context_fingerprint": "sha256:test-opl-run-context",
            "required_profile_ids": (
                "r_ggplot2_alluvial_transition_v1"
                if call["request"]["short_template_id"] == "alluvial_transition"
                else "r_ggplot2_evidence_subprocess_v1"
            ),
        }
        assert call["request"]["dependency_cache_context"] == {
            "status": "prepared",
            "run_context_ref": str(run_context_path),
            "run_context_fingerprint": "sha256:test-opl-run-context",
            "required_profile_ids": (
                "r_ggplot2_alluvial_transition_v1"
                if call["request"]["short_template_id"] == "alluvial_transition"
                else "r_ggplot2_evidence_subprocess_v1"
            ),
            "rscript_path": "/opt/opl/bin/Rscript",
            "r_libs_user": str(tmp_path / "opl-managed-r-lib"),
        }


def test_gallery_builder_packages_cached_assets_by_default(monkeypatch, tmp_path: Path, capsys) -> None:
    from med_autoscience.display_pack_gallery_parts import cli as gallery_cli

    calls: dict[str, object] = {
        "clean_assets": 0,
        "force_render_values": [],
    }

    def fake_manifest(
        *,
        records,
        rendered,
        baseline_rendered,
        publish_docs,
        render_cache_summary,
        force_render,
        package_only,
    ):
        return {
            "quality_audit": {
                "overall_status": "not_publication_ready",
                "publication_ready_claim_authorized": False,
            },
            "design_gallery_template_count": 0,
            "non_visual_canonical_template_count": 0,
            "rendered_image_template_count": 0,
            "internal_rendered_image_template_count": 0,
            "lidocaineq_reference_coverage": {
                "reference_template_count": 0,
                "covered_reference_template_count": 0,
                "coverage_complete": True,
                "missing_or_downgraded_reference_template_ids": [],
                "replacement_template_count": 0,
                "do_not_restore_legacy_alias_count": 0,
            },
            "quality_overall_status": "not_publication_ready",
            "force_render": force_render,
            "package_only": package_only,
            "render_cache_summary": render_cache_summary,
        }

    def fake_render_records(records, *, force_render, package_only):
        calls["force_render_values"].append((force_render, package_only))
        return {}, {}

    def fake_clean_assets() -> None:
        calls["clean_assets"] = int(calls["clean_assets"]) + 1

    def fake_write_reference(records, rendered, baseline_rendered, *, reference_path: Path) -> None:
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.write_text("reference\n", encoding="utf-8")

    monkeypatch.setattr(gallery_cli.shutil, "which", lambda name: "/usr/bin/Rscript" if name == "Rscript" else None)
    monkeypatch.setattr(gallery_cli, "read_template_records", lambda *_: [])
    monkeypatch.setattr(gallery_cli, "_render_records", fake_render_records)
    monkeypatch.setattr(gallery_cli, "_clean_assets", fake_clean_assets)
    monkeypatch.setattr(gallery_cli, "_render_html", lambda *_: "<html></html>")
    monkeypatch.setattr(gallery_cli, "_write_reference", fake_write_reference)
    monkeypatch.setattr(gallery_cli, "build_manifest", fake_manifest)
    monkeypatch.setattr(gallery_cli, "build_quality_audit_markdown", lambda *_: "quality\n")
    monkeypatch.setattr(gallery_cli, "build_gallery_status_markdown", lambda *_: "status\n")
    monkeypatch.setattr(gallery_cli, "_export_pdf", lambda: None)

    assert gallery_cli.main(["--output-root", str(tmp_path / "default")]) == 0
    default_stdout = json.loads(capsys.readouterr().out)
    assert default_stdout["force_render"] is False
    assert calls["force_render_values"] == [(False, False)]
    assert calls["clean_assets"] == 0

    assert gallery_cli.main(["--output-root", str(tmp_path / "force"), "--force-render"]) == 0
    force_stdout = json.loads(capsys.readouterr().out)
    assert force_stdout["force_render"] is True
    assert calls["force_render_values"] == [(False, False), (True, False)]
    assert calls["clean_assets"] == 1


def test_gallery_builder_package_only_skips_renderer_preflight(monkeypatch, tmp_path: Path, capsys) -> None:
    from med_autoscience.display_pack_gallery_parts import cli as gallery_cli

    calls: dict[str, object] = {
        "which": [],
        "render_records": [],
    }

    def fake_manifest(
        *,
        records,
        rendered,
        baseline_rendered,
        publish_docs,
        render_cache_summary,
        force_render,
        package_only,
    ):
        return {
            "quality_audit": {
                "overall_status": "not_publication_ready",
                "publication_ready_claim_authorized": False,
            },
            "design_gallery_template_count": 0,
            "non_visual_canonical_template_count": 0,
            "rendered_image_template_count": 0,
            "internal_rendered_image_template_count": 0,
            "lidocaineq_reference_coverage": {
                "reference_template_count": 0,
                "covered_reference_template_count": 0,
                "coverage_complete": True,
                "missing_or_downgraded_reference_template_ids": [],
                "replacement_template_count": 0,
                "do_not_restore_legacy_alias_count": 0,
            },
            "force_render": force_render,
            "package_only": package_only,
            "render_cache_summary": render_cache_summary,
        }

    def fake_render_records(records, *, force_render, package_only):
        calls["render_records"].append((force_render, package_only))
        return {}, {}

    def fake_which(name: str) -> None:
        calls["which"].append(name)
        return None

    def fake_write_reference(records, rendered, baseline_rendered, *, reference_path: Path) -> None:
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.write_text("reference\n", encoding="utf-8")

    monkeypatch.setattr(gallery_cli.shutil, "which", fake_which)
    monkeypatch.setattr(gallery_cli, "read_template_records", lambda *_: [])
    monkeypatch.setattr(gallery_cli, "_render_records", fake_render_records)
    monkeypatch.setattr(gallery_cli, "_render_html", lambda *_: "<html></html>")
    monkeypatch.setattr(gallery_cli, "_write_reference", fake_write_reference)
    monkeypatch.setattr(gallery_cli, "build_manifest", fake_manifest)
    monkeypatch.setattr(gallery_cli, "build_quality_audit_markdown", lambda *_: "quality\n")
    monkeypatch.setattr(gallery_cli, "build_gallery_status_markdown", lambda *_: "status\n")
    monkeypatch.setattr(gallery_cli, "_export_pdf", lambda: None)

    assert gallery_cli.main(["--output-root", str(tmp_path / "package-only"), "--package-only"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["package_only"] is True
    assert calls["which"] == []
    assert calls["render_records"] == [(False, True)]


def test_embedding_templates_use_feature_matrix_workflow_schema() -> None:
    expected = {
        "pca_scatter_grouped": "dimensionality_reduction_inputs_v1",
        "tsne_scatter_grouped": "dimensionality_reduction_inputs_v1",
        "umap_scatter_grouped": "dimensionality_reduction_inputs_v1",
    }

    for template_id, expected_schema in expected.items():
        payload = tomllib.loads((CORE_PACK_ROOT / "templates" / template_id / "template.toml").read_text(encoding="utf-8"))
        assert payload["input_schema_ref"] == expected_schema


def test_r_embedding_renderer_computes_pca_from_feature_matrix_without_reusing_points() -> None:
    r_script = r"""
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/evidence_renderer.R")
payload <- list(
  title = "PCA probe",
  x_label = "PC1",
  y_label = "PC2",
  embedding_input_mode = "feature_matrix",
  source_feature_matrix_digest = "test-matrix",
  feature_matrix = list(
    list(sample_id = "S1", group = "A", features = list(f1 = -1.2, f2 = 0.6, f3 = -0.4)),
    list(sample_id = "S2", group = "A", features = list(f1 = -0.9, f2 = 0.4, f3 = -0.3)),
    list(sample_id = "S3", group = "B", features = list(f1 = 0.8, f2 = -0.5, f3 = 0.5)),
    list(sample_id = "S4", group = "B", features = list(f1 = 1.1, f2 = -0.7, f3 = 0.7))
  ),
  points = list(
    list(sample_id = "S1", x = 100, y = 100, group = "A"),
    list(sample_id = "S2", x = 100, y = 100, group = "A"),
    list(sample_id = "S3", x = 100, y = 100, group = "B"),
    list(sample_id = "S4", x = 100, y = 100, group = "B")
  )
)
plot <- build_evidence_plot("pca_scatter_grouped", payload)
built <- ggplot2::ggplot_build(plot)
stopifnot(!all(abs(built$data[[1]]$x - 100) < 1e-9))
metrics <- build_dimensionality_reduction_metrics(
  "pca_scatter_grouped",
  payload,
  list(x0 = 0.1, y0 = 0.1, x1 = 0.9, y1 = 0.9)
)
stopifnot(identical(metrics$embedding_method, "pca"))
stopifnot(identical(metrics$embedding_backend, "stats::prcomp"))
stopifnot(identical(metrics$embedding_input_mode, "feature_matrix"))
stopifnot(identical(metrics$source_feature_matrix_digest, "test-matrix"))
stopifnot(identical(metrics$analysis_provenance$sample_count, 4L))
stopifnot(identical(metrics$analysis_provenance$feature_count, 3L))
"""

    result = subprocess.run(
        ["Rscript", "-e", r_script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr


def test_r_embedding_renderer_requires_real_tsne_and_umap_backends() -> None:
    r_script = r"""
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/evidence_renderer.R")
payload <- list(
  title = "Embedding probe",
  x_label = "x",
  y_label = "y",
  embedding_input_mode = "feature_matrix",
  feature_matrix = list(
    list(sample_id = "S1", group = "A", features = list(f1 = -1.2, f2 = 0.6, f3 = -0.4)),
    list(sample_id = "S2", group = "A", features = list(f1 = -0.9, f2 = 0.4, f3 = -0.3)),
    list(sample_id = "S3", group = "B", features = list(f1 = 0.8, f2 = -0.5, f3 = 0.5)),
    list(sample_id = "S4", group = "B", features = list(f1 = 1.1, f2 = -0.7, f3 = 0.7))
  )
)
if (!requireNamespace("Rtsne", quietly = TRUE)) {
  err <- tryCatch({ build_evidence_plot("tsne_scatter_grouped", payload); "" }, error = function(e) conditionMessage(e))
  stopifnot(grepl("Rtsne", err, fixed = TRUE))
}
if (!requireNamespace("uwot", quietly = TRUE)) {
  err <- tryCatch({ build_evidence_plot("umap_scatter_grouped", payload); "" }, error = function(e) conditionMessage(e))
  stopifnot(grepl("uwot", err, fixed = TRUE))
}
"""

    result = subprocess.run(
        ["Rscript", "-e", r_script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr


def test_publication_embedding_gallery_payload_drives_distinct_reduction_workflows() -> None:
    from med_autoscience.display_pack_gallery_parts.publication_payloads import PUBLICATION_R_DISPLAY_PAYLOADS

    payloads = {
        key: PUBLICATION_R_DISPLAY_PAYLOADS[key]
        for key in ("pca_scatter_grouped", "tsne_scatter_grouped", "umap_scatter_grouped")
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        payload_path = Path(tmpdir) / "embedding_payloads.json"
        payload_path.write_text(json.dumps(payloads), encoding="utf-8")
        r_script = """
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/evidence_renderer.R")
med_autoscience_payloads <- jsonlite::fromJSON("__PAYLOAD_PATH__", simplifyVector = FALSE)
pca_payload <- med_autoscience_payloads$pca_scatter_grouped
tsne_payload <- med_autoscience_payloads$tsne_scatter_grouped
umap_payload <- med_autoscience_payloads$umap_scatter_grouped
stopifnot(is.null(pca_payload$points))
stopifnot(is.null(tsne_payload$points))
stopifnot(is.null(umap_payload$points))
stopifnot(identical(pca_payload$source_feature_matrix_digest, tsne_payload$source_feature_matrix_digest))
stopifnot(identical(pca_payload$source_feature_matrix_digest, umap_payload$source_feature_matrix_digest))
stopifnot(length(pca_payload$feature_matrix) == length(tsne_payload$feature_matrix))
stopifnot(length(pca_payload$feature_matrix) == length(umap_payload$feature_matrix))

if (requireNamespace("Rtsne", quietly = TRUE) && requireNamespace("uwot", quietly = TRUE)) {
  pca <- compute_embedding_result("pca_scatter_grouped", pca_payload)
  tsne <- compute_embedding_result("tsne_scatter_grouped", tsne_payload)
  umap <- compute_embedding_result("umap_scatter_grouped", umap_payload)
  stopifnot(identical(pca$provenance$backend, "stats::prcomp"))
  stopifnot(identical(tsne$provenance$backend, "Rtsne::Rtsne"))
  stopifnot(identical(umap$provenance$backend, "uwot::umap"))
  pca_xy <- round(as.matrix(pca$points[, c("x", "y")]), 6)
  tsne_xy <- round(as.matrix(tsne$points[, c("x", "y")]), 6)
  umap_xy <- round(as.matrix(umap$points[, c("x", "y")]), 6)
  stopifnot(!identical(pca_xy, tsne_xy))
  stopifnot(!identical(pca_xy, umap_xy))
  stopifnot(!identical(tsne_xy, umap_xy))
}
""".replace("__PAYLOAD_PATH__", payload_path.as_posix())

        result = subprocess.run(
            ["Rscript", "-e", r_script],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )

    assert result.returncode == 0, result.stderr


def test_embedding_layout_sidecar_preserves_nonzero_panel_and_point_positions() -> None:
    from med_autoscience.display_pack_gallery_parts.publication_payloads import PUBLICATION_R_DISPLAY_PAYLOADS

    payload = PUBLICATION_R_DISPLAY_PAYLOADS["pca_scatter_grouped"]
    with tempfile.TemporaryDirectory() as tmpdir:
        payload_path = Path(tmpdir) / "pca_payload.json"
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        r_script = """
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/evidence_renderer.R")
payload <- jsonlite::fromJSON("__PAYLOAD_PATH__", simplifyVector = FALSE)
plot <- build_evidence_plot("pca_scatter_grouped", payload)
sidecar <- build_layout_sidecar(plot, "pca_scatter_grouped", payload)
panel <- sidecar$panel_boxes[[1]]
stopifnot((panel$x1 - panel$x0) > 0.5)
stopifnot((panel$y1 - panel$y0) > 0.5)
point_keys <- vapply(
  sidecar$metrics$points,
  function(point) paste(round(point$x, 4), round(point$y, 4)),
  character(1)
)
stopifnot(length(unique(point_keys)) == length(point_keys))
""".replace("__PAYLOAD_PATH__", payload_path.as_posix())

        result = subprocess.run(
            ["Rscript", "-e", r_script],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )

    assert result.returncode == 0, result.stderr


def test_core_pack_representative_lidocaineq_default_renderers_render_with_r_subprocess() -> None:
    source_renderers_by_template = {
        "risk_layering_monotonic_bars": "LidocaineQ/Figure_Template::risk_layering_monotonic_bars",
        "omics_volcano_panel": "LidocaineQ/Figure_Template::volcano_deg",
        "shap_summary_beeswarm": "LidocaineQ/Figure_Template::shap_summary_beeswarm",
    }
    default_payloads: dict[str, dict[str, object]] = {
        "risk_layering_monotonic_bars": {
            "title": "Risk group summary",
            "x_label": "Risk group",
            "y_label": "Five-year risk",
            "risk_group_summaries": [
                {"label": "Low", "mean_predicted_risk_5y": 0.08, "observed_km_risk_5y": 0.07, "events_5y": 12},
                {"label": "High", "mean_predicted_risk_5y": 0.26, "observed_km_risk_5y": 0.29, "events_5y": 44},
            ],
        },
        "omics_volcano_panel": {
            "title": "Volcano candidate",
            "x_label": "log2 fold change",
            "y_label": "-log10 FDR",
            "effect_threshold": 1.0,
            "significance_threshold": 1.3,
            "points": [
                {
                    "panel_id": "A",
                    "feature_label": "IFNG",
                    "effect_value": 1.4,
                    "significance_value": 3.2,
                    "regulation_class": "upregulated",
                },
                {
                    "panel_id": "A",
                    "feature_label": "MKI67",
                    "effect_value": -1.2,
                    "significance_value": 2.7,
                    "regulation_class": "downregulated",
                },
            ],
        },
        "shap_summary_beeswarm": {
            "title": "SHAP candidate",
            "x_label": "SHAP value",
            "rows": [
                {
                    "feature": "Age",
                    "points": [
                        {"shap_value": -0.12, "feature_value": 0.20},
                        {"shap_value": 0.23, "feature_value": 0.85},
                    ],
                },
                {
                    "feature": "Ki-67",
                    "points": [
                        {"shap_value": -0.08, "feature_value": 0.35},
                        {"shap_value": 0.18, "feature_value": 0.72},
                    ],
                },
            ],
        },
    }
    with tempfile.TemporaryDirectory(prefix="mas-display-lidocaineq-r-") as tmpdir:
        output_dir = Path(tmpdir)
        for template_id, payload in default_payloads.items():
            request_path = _candidate_request(template_id=template_id, payload=payload, output_dir=output_dir)
            completed = subprocess.run(
                ["Rscript", "render.R", "--request", str(request_path)],
                cwd=CORE_PACK_ROOT / "templates" / template_id,
                capture_output=True,
                text=True,
                check=False,
            )
            assert completed.returncode == 0, completed.stderr
            assert (output_dir / f"{template_id}.png").is_file()
            assert (output_dir / f"{template_id}.pdf").is_file()
            sidecar = json.loads((output_dir / f"{template_id}.layout.json").read_text(encoding="utf-8"))
            assert sidecar["template_id"] == template_id
            assert sidecar["metrics"]["renderer"] == "r_ggplot2_evidence_subprocess_v1"
            assert sidecar["metrics"]["renderer_role"] == "default"
            assert sidecar["metrics"]["source_renderer"] == source_renderers_by_template[template_id]


def test_cli_display_pack_render_candidate_runs_legacy_comparison_surface(tmp_path: Path, capsys) -> None:
    from med_autoscience import cli

    payload_path = tmp_path / "payload.json"
    output_dir = tmp_path / "candidate-output"
    payload_path.write_text(
        json.dumps(
            {
                "title": "Risk group summary",
                "x_label": "Risk group",
                "y_label": "Five-year risk",
                "risk_group_summaries": [
                    {"label": "Low", "mean_predicted_risk_5y": 0.08, "observed_km_risk_5y": 0.07, "events_5y": 12},
                    {"label": "High", "mean_predicted_risk_5y": 0.26, "observed_km_risk_5y": 0.29, "events_5y": 44},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "display-pack-render-candidate",
            "--repo-root",
            str(REPO_ROOT),
            "--template-id",
            "risk_layering_monotonic_bars",
            "--display-payload-file",
            str(payload_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["status"] == "rendered"
    assert result["candidate_only"] is True
    assert result["comparison_only"] is True
    assert result["publication_readiness_verdict"] is False
    assert result["template_id"] == "fenggaolab.org.medical-display-core::risk_layering_monotonic_bars"
    assert result["candidate_entrypoint"] == "Rscript render_candidate.R --request {request_json}"
    assert result["authority_boundary"]["candidate_can_authorize_publication_readiness"] is False
    assert result["authority_boundary"]["candidate_can_mutate_data_or_statistics"] is False
    assert result["authority_boundary"]["candidate_can_replace_default_renderer"] is False
    assert result["authority_boundary"]["comparison_receipt_can_replace_default_renderer"] is False
    assert result["authority_boundary"]["default_renderer_promotion_already_landed"] is True
    assert result["default_renderer"]["renderer_family"] == "r_ggplot2"
    assert result["default_renderer"]["execution_mode"] == "subprocess"
    assert result["default_renderer"]["entrypoint"] == "Rscript render.R --request {request_json}"
    assert result["render_result"]["status"] == "rendered"
    assert Path(result["rendered_artifacts"]["png_path"]).is_file()
    assert Path(result["rendered_artifacts"]["pdf_path"]).is_file()
    assert Path(result["rendered_artifacts"]["layout_sidecar_path"]).is_file()
    assert Path(result["render_result"]["request_path"]).is_file()
    assert Path(result["render_result"]["stdout_path"]).is_file()
    assert Path(result["render_result"]["stderr_path"]).is_file()
    render_request = json.loads(Path(result["render_result"]["request_path"]).read_text(encoding="utf-8"))
    assert render_request["candidate_only"] is True
    assert render_request["comparison_only"] is True
    sidecar = json.loads(Path(result["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    assert sidecar["metrics"]["renderer"] == "r_ggplot2_comparison_subprocess_v1"
    assert sidecar["metrics"]["renderer_role"] == "comparison"
