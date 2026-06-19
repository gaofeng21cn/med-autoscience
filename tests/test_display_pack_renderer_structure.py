from __future__ import annotations

import importlib
import sys
from pathlib import Path
import json
import subprocess
import tempfile
import tomllib


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


def test_core_pack_evidence_renderer_keeps_stable_python_entrypoint() -> None:
    sys.path.insert(0, str(CORE_PACK_SRC_ROOT))
    module = importlib.import_module("fenggaolab_org_medical_display_core.evidence_figures")

    assert callable(module.render_python_evidence_figure)


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

    assert len(r_templates) == 51


def test_core_pack_renderer_migration_ledger_covers_all_evidence_templates() -> None:
    ledger = json.loads((CORE_PACK_ROOT / "renderer_migration_ledger.json").read_text(encoding="utf-8"))
    records = ledger["records"]
    manifest_ids = []
    for manifest_path in sorted((CORE_PACK_ROOT / "templates").glob("*/template.toml")):
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        if payload["kind"] == "evidence_figure":
            manifest_ids.append(payload["template_id"])

    records_by_template = {item["template_id"]: item for item in records}
    lane_counts = {
        lane: sum(1 for item in records if item["migration_lane"] == lane)
        for lane in ("P0", "P1", "P2")
    }

    assert sorted(records_by_template) == sorted(manifest_ids)
    assert ledger["summary"]["evidence_template_count"] == 84
    assert ledger["summary"]["p0_landed_r_ggplot2_subprocess"] == 22
    assert ledger["summary"]["p1_promoted_to_default_r_ggplot2_subprocess"] == 29
    assert ledger["summary"]["p2_retained_python_or_dual_stack_later"] == 33
    assert ledger["summary"]["unclassified"] == 0
    assert lane_counts == {"P0": 22, "P1": 29, "P2": 33}
    assert records_by_template["risk_layering_monotonic_bars"]["migration_lane"] == "P2"
    assert records_by_template["time_to_event_landmark_performance_panel"]["migration_lane"] == "P2"
    assert records_by_template["time_to_event_multihorizon_calibration_panel"]["migration_lane"] == "P2"
    assert records_by_template["time_to_event_threshold_governance_panel"]["migration_lane"] == "P2"
    assert records_by_template["celltype_signature_heatmap"]["migration_lane"] == "P1"
    assert records_by_template["multicenter_generalizability_overview"]["migration_lane"] == "P2"
    assert records_by_template["center_transportability_governance_summary_panel"]["migration_lane"] == "P2"


def test_core_pack_p1_renderers_are_promoted_r_subprocess_defaults() -> None:
    ledger = json.loads((CORE_PACK_ROOT / "renderer_migration_ledger.json").read_text(encoding="utf-8"))
    p1_records = [item for item in ledger["records"] if item["migration_lane"] == "P1"]

    assert len(p1_records) == 29
    for record in p1_records:
        template_root = CORE_PACK_ROOT / "templates" / record["template_id"]
        render_path = template_root / "render.R"
        comparison_path = template_root / "render_candidate.R"
        assert render_path.is_file(), record["template_id"]
        assert comparison_path.is_file(), record["template_id"]
        assert record["renderer_family"] == "r_ggplot2"
        assert record["execution_mode"] == "subprocess"
        assert record["entrypoint"] == "Rscript render.R --request {request_json}"
        assert record["render_script_path"] == "render.R"
        assert record["migration_status"] == "promoted_to_default_r_ggplot2_subprocess"
        assert record["previous_renderer_family"] == "python"
        assert record["previous_execution_mode"] == "python_plugin"
        wrapper_source = render_path.read_text(encoding="utf-8")
        assert f'expected_template_id = "{record["template_id"]}"' in wrapper_source


def test_core_pack_renderer_dependency_profile_declares_r_subprocess_runtime() -> None:
    profile = json.loads((CORE_PACK_ROOT / "renderer_dependency_profile.json").read_text(encoding="utf-8"))
    r_profile = next(item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_evidence_subprocess_v1")
    candidate_profile = next(
        item for item in profile["profiles"] if item["profile_id"] == "r_ggplot2_p1_comparison_subprocess_v1"
    )
    package_names = {item["name"] for item in r_profile["r_packages"]}

    assert r_profile["renderer_family"] == "r_ggplot2"
    assert r_profile["execution_mode"] == "subprocess"
    assert r_profile["entrypoint_pattern"] == "Rscript render.R --request {request_json}"
    assert {"jsonlite", "ggplot2", "ggsci", "grid"} <= package_names
    assert r_profile["shared_helper_ref"] == "rlib/medicaldisplaycore/evidence_renderer.R"
    assert r_profile["template_wrapper_ref"] == "templates/<template_id>/render.R"
    assert candidate_profile["renderer_family"] == "r_ggplot2"
    assert candidate_profile["execution_mode"] == "subprocess"
    assert candidate_profile["entrypoint_pattern"] == "Rscript render_candidate.R --request {request_json}"
    assert candidate_profile["shared_helper_ref"] == "rlib/medicaldisplaycore/evidence_renderer.R"
    assert candidate_profile["candidate_helper_ref"] == "rlib/medicaldisplaycore/candidate_renderer.R"
    assert candidate_profile["template_wrapper_ref"] == "templates/<template_id>/render_candidate.R"
    assert candidate_profile["surface_role"] == "legacy_comparison_receipt"
    assert candidate_profile["default_renderer_profile_ref"] == "r_ggplot2_evidence_subprocess_v1"
    assert candidate_profile["publication_readiness_verdict"] is False


def test_core_pack_representative_p1_default_renderers_render_with_r_subprocess() -> None:
    promoted_payloads: dict[str, dict[str, object]] = {
        "time_to_event_risk_group_summary": {
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
    with tempfile.TemporaryDirectory(prefix="mas-display-promoted-r-") as tmpdir:
        output_dir = Path(tmpdir)
        for template_id, payload in promoted_payloads.items():
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
            assert sidecar["metrics"]["renderer"] == "r_ggplot2_promoted_subprocess_v1"
            assert sidecar["metrics"]["renderer_role"] == "default"


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
            "time_to_event_risk_group_summary",
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
    assert result["template_id"] == "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"
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
