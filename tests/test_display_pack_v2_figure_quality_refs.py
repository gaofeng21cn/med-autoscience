from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.display_pack_lock import build_display_pack_lock_payload


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_pack(repo_root: Path) -> None:
    (repo_root / "config").mkdir(parents=True)
    (repo_root / "config" / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
version = "0.2.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    template_root = pack_root / "templates" / "roc_curve_binary"
    template_root.mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                'version = "0.2.0"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
                'summary = "test pack"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve"',
                'paper_family_ids = ["A"]',
                'audit_family = "Prediction Performance"',
                'renderer_family = "r_ggplot2"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "pkg.module:render"',
                "paper_proven = false",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_display_pack_lock_payload_includes_figure_quality_refs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_pack(repo_root)
    paper_root = tmp_path / "workspace" / "paper"
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "claim_ref": "claim:primary",
                    "data_ref": "paper/data/frozen/primary.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_visual_audit_receipt.json",
        {
            "schema_version": 1,
            "receipt_id": "visual-audit-20260610",
            "audit_mode": "vlm_visual_verification",
            "inspected_artifacts": [
                {
                    "figure_id": "F1",
                    "artifact_path": "paper/figures/generated/F1.png",
                    "artifact_sha256": "a" * 64,
                }
            ],
            "findings": [],
            "reviewer": {"provider": "openai", "model": "gpt-5-vlm", "prompt_hash": "b" * 64},
            "final_status": "clear",
        },
    )
    _write_json(
        paper_root / "figure_render_receipt.json",
        {
            "schema_version": 1,
            "receipt_id": "render-receipt-20260618",
            "source_project": "nature-skills",
            "source_commit": "1cb9070fdd94929d5f267ce6585ac87e2cba60b3",
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "selected_backend": "r_ggplot2",
                    "execution_mode": "python_plugin",
                    "backend_exclusivity_proof": {
                        "selected_backend": "r_ggplot2",
                        "observed_renderer_family": "r_ggplot2",
                        "cross_backend_visual_fallback_used": False,
                        "non_selected_backend_rendered_artifacts": [],
                    },
                    "export_formats": ["png", "pdf"],
                    "editable_text_required": True,
                    "editable_text_check_ref": "paper/figures/generated/F1.pdf",
                    "source_data_refs": ["paper/data/frozen/primary.json"],
                    "source_data_digests": {"paper/data/frozen/primary.json": "data-digest"},
                    "statistics_refs": ["analysis/statistics/auc_primary"],
                    "rendered_artifact_refs": ["paper/figures/generated/F1.png", "paper/figures/generated/F1.pdf"],
                    "visual_qa_ref": "paper/figure_visual_audit_receipt.json",
                    "authority_boundary": {
                        "can_authorize_publication_readiness": False,
                        "can_authorize_quality_verdict": False,
                        "can_mutate_data_or_statistics": False,
                    },
                }
            ],
            "authority_boundary": {
                "can_authorize_publication_readiness": False,
                "can_authorize_quality_verdict": False,
                "can_mutate_data_or_statistics": False,
            },
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
        {
            "schema_version": 1,
            "figure_id": "F1",
            "intent_ref": "paper/figure_intent.json#/figures/F1",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/derivation",
                "endpoint_ref": "endpoint:mace",
                "claim_role": "primary_evidence",
            },
        },
    )
    _write_json(
        paper_root / "figure_polish_lifecycle.json",
        {
            "schema_version": 1,
            "lifecycle_id": "fig-F1-polish",
            "relationship_refs": {
                "figure_visual_audit_receipt": "paper/figure_visual_audit_receipt.json",
                "display_pack_lock_publication_figure_quality_refs": (
                    "paper/build/display_pack_lock.json#/publication_figure_quality_refs"
                ),
            },
            "events": [
                {
                    "state": "draft_rendered",
                    "figure_id": "F1",
                    "artifact_ref": "paper/figures/generated/F1.png",
                    "actor": "display_pack_builder",
                    "evidence_ref": "paper/build/display_pack_lock.json",
                },
                {
                    "state": "deterministic_qc_clear",
                    "figure_id": "F1",
                    "artifact_ref": "paper/figures/generated/F1.png",
                    "actor": "deterministic_qc",
                    "evidence_ref": "paper/qc/F1.layout.json",
                },
            ],
        },
    )

    payload = build_display_pack_lock_payload(repo_root=repo_root, paper_root=paper_root)

    refs = payload["publication_figure_quality_refs"]
    assert refs["figure_intent"]["status"] == "present"
    assert refs["medical_figure_spec"]["status"] == "present"
    assert refs["figure_visual_audit_receipt"]["status"] == "present"
    assert refs["figure_render_receipt"]["status"] == "present"
    assert refs["figure_polish_lifecycle"]["status"] == "present"
    assert refs["ai_illustration_receipt"]["status"] == "missing"
