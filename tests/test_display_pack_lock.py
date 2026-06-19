from __future__ import annotations

from pathlib import Path
import json
import subprocess

from med_autoscience.display_pack_lock import build_display_pack_lock_payload


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_local_pack_config(repo_root: Path) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
version = "0.1.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_git_pack_config(repo_root: Path, *, relative_repo_path: str) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "display_packs.toml").write_text(
        f"""
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "git_repo"
pack_id = "fenggaolab.org.medical-display-core"
path = "{relative_repo_path}"
pack_subdir = "packs/core"
version = "0.2.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_pack_manifest(pack_root: Path, *, version: str) -> None:
    (pack_root / "templates" / "roc_curve_binary").mkdir(parents=True, exist_ok=True)
    (pack_root / "rlib" / "medicaldisplaycore").mkdir(parents=True, exist_ok=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                f'version = "{version}"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
                'summary = "test pack"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "renderer_migration_ledger.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (pack_root / "renderer_dependency_profile.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (pack_root / "rlib" / "medicaldisplaycore" / "evidence_renderer.R").write_text(
        "render_evidence_request <- function(request_path) {}\n",
        encoding="utf-8",
    )


def _write_template_manifest(template_root: Path) -> None:
    (template_root / "examples").mkdir(parents=True, exist_ok=True)
    (template_root / "goldens").mkdir(parents=True, exist_ok=True)
    (template_root / "exemplars").mkdir(parents=True, exist_ok=True)
    (template_root / "audit").mkdir(parents=True, exist_ok=True)
    (template_root / "render.R").write_text("message('render')\n", encoding="utf-8")
    (template_root / "render_candidate.R").write_text("message('candidate')\n", encoding="utf-8")
    (template_root / "examples" / "input.json").write_text("{}", encoding="utf-8")
    (template_root / "goldens" / "main.png").write_text("png", encoding="utf-8")
    (template_root / "exemplars" / "source.md").write_text("# exemplar", encoding="utf-8")
    (template_root / "audit" / "notes.md").write_text("# audit", encoding="utf-8")
    (template_root / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve (Binary Outcome)"',
                'paper_family_ids = ["A"]',
                'audit_family = "Prediction Performance"',
                'renderer_family = "r_ggplot2"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'required_exports = ["png", "pdf"]',
                'golden_case_paths = ["goldens/main.png"]',
                'exemplar_refs = ["Nature Medicine 2025 Figure 2"]',
                'execution_mode = "subprocess"',
                'entrypoint = "Rscript render.R --request {request_json}"',
                "paper_proven = false",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_publication_style_profile(paper_root: Path) -> None:
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "publication_style_profile.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "style_profile_id": "paper_neutral_clinical_v1",
                "journal_palette_ref": "large_journal_safe_lancet_like_v1",
                "palette": {
                    "primary": "#245A6B",
                    "secondary": "#B89A6D",
                    "neutral": "#6B7280",
                    "text": "#102A43",
                    "grid": "#D9E2EC",
                },
                "semantic_roles": {
                    "model_curve": "primary",
                    "comparator_curve": "secondary",
                    "reference_line": "neutral",
                    "text": "text",
                    "grid_line": "grid",
                },
                "typography": {
                    "font_family": "sans",
                    "base_size": 10.5,
                    "title_size": 12.0,
                    "axis_title_size": 10.8,
                    "tick_size": 9.5,
                    "legend_size": 9.2,
                    "panel_label_size": 10.8,
                },
                "stroke": {
                    "primary_linewidth": 2.0,
                    "secondary_linewidth": 1.6,
                    "reference_linewidth": 1.1,
                    "grid_linewidth": 0.35,
                    "marker_size": 4.2,
                },
                "grid": {
                    "major": True,
                    "minor": False,
                    "major_axis": "both",
                    "minor_axis": "none",
                    "color": "#D9E2EC",
                    "linetype": "solid",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_build_display_pack_lock_payload_captures_template_asset_inventory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_local_pack_config(repo_root)

    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    _write_pack_manifest(pack_root, version="0.1.0")
    _write_template_manifest(pack_root / "templates" / "roc_curve_binary")

    payload = build_display_pack_lock_payload(repo_root=repo_root)

    pack_entry = payload["enabled_packs"][0]
    template_entry = pack_entry["templates"][0]

    assert pack_entry["template_count"] == 1
    assert pack_entry["renderer_migration_ledger_path"].endswith("renderer_migration_ledger.json")
    assert len(pack_entry["renderer_migration_ledger_sha256"]) == 64
    assert pack_entry["renderer_dependency_profile_path"].endswith("renderer_dependency_profile.json")
    assert len(pack_entry["renderer_dependency_profile_sha256"]) == 64
    assert pack_entry["r_evidence_helper_path"].endswith("rlib/medicaldisplaycore/evidence_renderer.R")
    assert len(pack_entry["r_evidence_helper_sha256"]) == 64
    assert template_entry["template_id"] == "roc_curve_binary"
    assert template_entry["template_manifest_path"].endswith("templates/roc_curve_binary/template.toml")
    assert len(template_entry["template_manifest_sha256"]) == 64
    assert template_entry["renderer_family"] == "r_ggplot2"
    assert template_entry["execution_mode"] == "subprocess"
    assert template_entry["entrypoint"] == "Rscript render.R --request {request_json}"
    assert template_entry["render_script_path"].endswith("templates/roc_curve_binary/render.R")
    assert len(template_entry["render_script_sha256"]) == 64
    assert template_entry["candidate_render_script_path"].endswith("templates/roc_curve_binary/render_candidate.R")
    assert len(template_entry["candidate_render_script_sha256"]) == 64
    assert template_entry["candidate_entrypoint"] == "Rscript render_candidate.R --request {request_json}"
    assert template_entry["candidate_execution_mode"] == "subprocess"
    assert template_entry["golden_case_paths"] == ["goldens/main.png"]
    assert template_entry["exemplar_refs"] == ["Nature Medicine 2025 Figure 2"]
    assert template_entry["examples_dir"].endswith("templates/roc_curve_binary/examples")
    assert template_entry["examples_file_count"] == 1
    assert template_entry["goldens_dir"].endswith("templates/roc_curve_binary/goldens")
    assert template_entry["goldens_file_count"] == 1
    assert template_entry["exemplars_dir"].endswith("templates/roc_curve_binary/exemplars")
    assert template_entry["exemplars_file_count"] == 1
    assert template_entry["audit_dir"].endswith("templates/roc_curve_binary/audit")
    assert template_entry["audit_file_count"] == 1


def test_build_display_pack_lock_payload_locks_publication_style_profile(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    paper_root = tmp_path / "workspace" / "paper"
    repo_root.mkdir()
    _write_local_pack_config(repo_root)

    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    _write_pack_manifest(pack_root, version="0.1.0")
    _write_template_manifest(pack_root / "templates" / "roc_curve_binary")
    _write_publication_style_profile(paper_root)

    payload = build_display_pack_lock_payload(repo_root=repo_root, paper_root=paper_root)

    style_lock = payload["publication_style_profile"]
    assert style_lock["status"] == "present"
    assert style_lock["ref"] == "paper/publication_style_profile.json"
    assert len(style_lock["sha256"]) == 64
    assert style_lock["style_profile_id"] == "paper_neutral_clinical_v1"
    assert style_lock["journal_palette_ref"] == "large_journal_safe_lancet_like_v1"
    assert "primary" in style_lock["palette_keys"]
    assert style_lock["semantic_roles"]["model_curve"] == "primary"
    assert style_lock["typography"]["font_family"] == "sans"
    assert style_lock["stroke"]["grid_linewidth"] == 0.35
    assert style_lock["grid"]["color"] == "#D9E2EC"
    assert style_lock["payload"]["palette"]["primary"] == "#245A6B"
    assert payload["publication_figure_quality_refs"]["publication_style_profile"]["sha256"] == style_lock["sha256"]


def test_build_display_pack_lock_payload_captures_git_repo_source_provenance(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_repo_root = tmp_path / "display-core-git"
    git_repo_root.mkdir()
    _write_git_pack_config(repo_root, relative_repo_path="../display-core-git")

    pack_root = git_repo_root / "packs" / "core"
    _write_pack_manifest(pack_root, version="0.2.0")
    _write_template_manifest(pack_root / "templates" / "roc_curve_binary")

    _git(git_repo_root, "init", "-b", "main")
    _git(git_repo_root, "config", "user.name", "Test User")
    _git(git_repo_root, "config", "user.email", "test@example.com")
    _git(git_repo_root, "add", ".")
    _git(git_repo_root, "commit", "-m", "Initial display pack")
    expected_commit = _git(git_repo_root, "rev-parse", "HEAD")

    payload = build_display_pack_lock_payload(repo_root=repo_root)

    pack_entry = payload["enabled_packs"][0]

    assert pack_entry["source_kind"] == "git_repo"
    assert pack_entry["source_path"] == "../display-core-git"
    assert pack_entry["pack_subdir"] == "packs/core"
    assert pack_entry["git_commit"] == expected_commit
    assert pack_entry["git_is_dirty"] is False
    assert pack_entry["resolved_source_root"].endswith("display-core-git")


def test_build_display_pack_lock_payload_projects_canonical_default_renderers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    payload = build_display_pack_lock_payload(repo_root=repo_root)
    template_entries = {
        item["template_id"]: item
        for pack in payload["enabled_packs"]
        if pack["pack_id"] == "fenggaolab.org.medical-display-core"
        for item in pack["templates"]
    }
    r_ggplot2_default_templates = [
        item
        for item in template_entries.values()
        if item["renderer_family"] == "r_ggplot2"
        and item["execution_mode"] == "subprocess"
        and item["entrypoint"] == "Rscript render.R --request {request_json}"
        and item["render_script_path"].endswith(f"templates/{item['template_id']}/render.R")
    ]
    r_ggplot2_default_templates_with_candidate = [
        item
        for item in template_entries.values()
        if item["renderer_family"] == "r_ggplot2"
        and item["execution_mode"] == "subprocess"
        and item["entrypoint"] == "Rscript render.R --request {request_json}"
        and item["candidate_entrypoint"] == "Rscript render_candidate.R --request {request_json}"
    ]

    assert len(template_entries) == 19
    assert len(r_ggplot2_default_templates) == 16
    assert len(r_ggplot2_default_templates_with_candidate) == 11
    assert "time_to_event_risk_group_summary" not in template_entries
    assert "partial_dependence_ice_panel" not in template_entries
    assert "single_cell_atlas_overview_panel" not in template_entries
    assert "phenotype_gap_structure_figure" not in template_entries
    assert "shap_dependence_panel" in template_entries
    assert "shap_waterfall_local_explanation_panel" in template_entries
    assert "generalizability_subgroup_composite_panel" in template_entries
    assert not [
        item["template_id"]
        for item in template_entries.values()
        if item["kind"] == "evidence_figure" and item["renderer_family"] == "python"
    ]
    assert template_entries["time_to_event_discrimination_calibration_panel"]["renderer_family"] == "r_ggplot2"
    assert template_entries["time_to_event_discrimination_calibration_panel"]["execution_mode"] == "subprocess"
    assert template_entries["time_to_event_discrimination_calibration_panel"]["entrypoint"] == (
        "Rscript render.R --request {request_json}"
    )
    assert template_entries["time_to_event_discrimination_calibration_panel"]["render_script_path"].endswith(
        "templates/time_to_event_discrimination_calibration_panel/render.R"
    )
    assert len(template_entries["time_to_event_discrimination_calibration_panel"]["render_script_sha256"]) == 64
    assert template_entries["time_to_event_discrimination_calibration_panel"][
        "candidate_render_script_path"
    ].endswith(
        "templates/time_to_event_discrimination_calibration_panel/render_candidate.R"
    )
    assert template_entries["omics_volcano_panel"]["render_script_path"].endswith(
        "templates/omics_volcano_panel/render.R"
    )
    assert template_entries["shap_summary_beeswarm"]["render_script_path"].endswith(
        "templates/shap_summary_beeswarm/render.R"
    )
    assert template_entries["table1_baseline_characteristics"]["kind"] == "table_shell"
    assert template_entries["table1_baseline_characteristics"]["entrypoint"] == (
        "fenggaolab_org_medical_display_core.table_shells:render_table_shell"
    )
