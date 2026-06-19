from __future__ import annotations

import json
from pathlib import Path

from med_autoscience import cli
from med_autoscience.display_layout_qc.router import QC_PROFILE_RUNNERS
from med_autoscience.display_pack_loader import load_enabled_local_display_template_records


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_cli_display_pack_list_templates_supports_filtering(capsys) -> None:
    exit_code = cli.main(
        [
            "publication",
            "display-pack-templates",
            "--repo-root",
            str(REPO_ROOT),
            "--kind",
            "evidence_figure",
            "--renderer-family",
            "r_ggplot2",
            "--audit-family",
            "Prediction Performance",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["schema_version"] == 1
    assert result["total_count"] >= 1
    assert result["template_surface_policy"]["default_templates_are_canonical_only"] is True
    assert result["template_surface_policy"]["active_inventory_is_canonical_only"] is True
    assert result["filters"] == {
        "kind": "evidence_figure",
        "renderer_family": "r_ggplot2",
        "audit_family": "Prediction Performance",
        "paper_family": "",
        "query": "",
    }
    template_ids = {entry["template_id"] for entry in result["templates"]}
    assert "roc_curve_binary" in template_ids
    assert "time_dependent_roc_horizon" not in template_ids
    assert {entry["migration_status"] for entry in result["templates"]} == {"canonical"}
    assert all(entry["renderer_family"] == "r_ggplot2" for entry in result["templates"])
    assert all(entry["kind"] == "evidence_figure" for entry in result["templates"])


def test_cli_display_pack_describe_template_reports_runtime_and_assets(capsys) -> None:
    exit_code = cli.main(
        [
            "publication",
            "display-pack-template",
            "--repo-root",
            str(REPO_ROOT),
            "--template-id",
            "roc_curve_binary",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["schema_version"] == 1
    assert result["template"]["template_id"] == "roc_curve_binary"
    assert result["template"]["full_template_id"] == "fenggaolab.org.medical-display-core::roc_curve_binary"
    assert result["runtime"]["execution_mode"] == "subprocess"
    assert result["runtime"]["entrypoint"] == "Rscript render.R --request {request_json}"
    assert result["assets"]["render_r"]["status"] == "present"
    assert result["assets"]["golden_case_count"] == 0
    assert result["authority_boundary"]["describe_can_authorize_publication_readiness"] is False


def test_cli_display_pack_scaffold_render_materializes_minimal_paper(tmp_path: Path, capsys) -> None:
    paper_root = tmp_path / "paper"
    data_path = tmp_path / "payload.json"
    data_path.write_text(
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

    exit_code = cli.main(
        [
            "publication",
            "display-pack-scaffold-render",
            "--repo-root",
            str(REPO_ROOT),
            "--paper-root",
            str(paper_root),
            "--template-id",
            "roc_curve_binary",
            "--data-payload-file",
            str(data_path),
            "--figure-id",
            "F1",
            "--claim-ref",
            "claim:primary",
            "--cohort-ref",
            "cohort:demo",
            "--endpoint-ref",
            "endpoint:mortality",
            "--risk-horizon",
            "5y",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["status"] == "publication_manifested"
    assert result["scaffold"]["created"] is True
    assert result["scaffold"]["paper_root"] == str(paper_root.resolve())
    assert result["figures"][0]["template_id"] == "fenggaolab.org.medical-display-core::roc_curve_binary"
    assert Path(result["figures"][0]["rendered_artifacts"]["png_path"]).is_file()
    assert (paper_root / "figure_intent.json").is_file()
    assert (paper_root / "figure_specs.json").is_file()
    assert (paper_root / "publication_style_profile.json").is_file()


def test_cli_display_pack_golden_refresh_and_check_roundtrip(tmp_path: Path, capsys) -> None:
    paper_root = tmp_path / "paper"
    golden_root = tmp_path / "goldens"
    data_path = tmp_path / "payload.json"
    data_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_data_digest": "payload-digest",
                "series": [{"label": "Model", "x": [0.0, 1.0], "y": [0.0, 1.0]}],
                "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    refresh_exit_code = cli.main(
        [
            "publication",
            "display-pack-golden",
            "refresh",
            "--repo-root",
            str(REPO_ROOT),
            "--paper-root",
            str(paper_root),
            "--template-id",
            "roc_curve_binary",
            "--data-payload-file",
            str(data_path),
            "--golden-root",
            str(golden_root),
        ]
    )
    refresh_result = json.loads(capsys.readouterr().out)
    assert refresh_exit_code == 0
    assert refresh_result["status"] == "golden_refreshed"
    manifest_path = Path(refresh_result["golden_manifest_path"])
    assert manifest_path.is_file()
    manifest_payload = _read_json(manifest_path)
    assert manifest_payload["template_id"] == "fenggaolab.org.medical-display-core::roc_curve_binary"
    assert manifest_payload["artifacts"]["png"]["sha256"]

    check_exit_code = cli.main(
        [
            "publication",
            "display-pack-golden",
            "check",
            "--repo-root",
            str(REPO_ROOT),
            "--paper-root",
            str(paper_root),
            "--template-id",
            "roc_curve_binary",
            "--data-payload-file",
            str(data_path),
            "--golden-root",
            str(golden_root),
        ]
    )
    check_result = json.loads(capsys.readouterr().out)
    assert check_exit_code == 0
    assert check_result["status"] == "golden_match"
    assert check_result["comparison"]["png"]["match"] is True
    assert check_result["comparison"]["pdf"]["required_match"] is False
    assert check_result["comparison"]["layout_sidecar"]["match"] is True
    assert check_result["contract_comparison"]["deterministic_qc_status"]["match"] is True
    assert check_result["contract_comparison"]["publication_style_profile_sha256"]["match"] is True
    assert check_result["authority_boundary"]["golden_check_can_authorize_publication_readiness"] is False


def test_all_enabled_display_pack_templates_reference_supported_qc_profiles() -> None:
    records = load_enabled_local_display_template_records(REPO_ROOT, inventory_scope="all")
    missing = sorted(
        {
            record.template_manifest.qc_profile_ref
            for record in records
            if record.template_manifest.qc_profile_ref not in QC_PROFILE_RUNNERS
        }
    )

    assert missing == []
