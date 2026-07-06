from __future__ import annotations

import json
from pathlib import Path

from tests.test_display_pack_e2e_runtime import (
    _build_workspace,
    _visual_audit_review,
    _write_json,
    _write_subprocess_renderable_template,
)


def test_materialize_display_pack_publication_manifest_runs_subprocess_renderer(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    repo_root, paper_root = _build_workspace(tmp_path)
    _write_subprocess_renderable_template(repo_root)
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F2",
                    "claim_ref": "claim:secondary-discrimination",
                    "data_ref": "paper/data/frozen/primary_curve.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
                    "figure_kind": "evidence_figure",
                    "statistical_value_refs": ["analysis/statistics/auc_secondary"],
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
        {
            "schema_version": 1,
            "figure_id": "F2",
            "intent_ref": "paper/figure_intent.json#/figures/F2",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/validation",
                "endpoint_ref": "endpoint:mace",
                "model_ref": "model:cox-secondary",
                "risk_horizon": "5y",
                "effect_estimate_ref": "analysis/statistics/auc_secondary",
                "claim_role": "secondary_evidence",
            },
            "panels": [{"panel_id": "A", "data_role": "discrimination", "mark_role": "roc_curve"}],
        },
    )

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
    )

    figure = result["figures"][0]
    assert figure["figure_id"] == "F2"
    assert figure["render_result"]["execution_mode"] == "subprocess"
    assert figure["render_result"]["renderer_family"] == "r_ggplot2"
    assert figure["render_result"]["returncode"] == 0
    assert Path(figure["render_result"]["request_path"]).exists()
    assert Path(figure["render_result"]["stdout_path"]).read_text(encoding="utf-8").strip()
    assert Path(figure["rendered_artifacts"]["png_path"]).read_text(encoding="utf-8").startswith("PNG:subprocess:")
    request_payload = json.loads(Path(figure["render_result"]["request_path"]).read_text(encoding="utf-8"))
    render_context = request_payload["display_payload"]["render_context"]
    assert render_context["palette"]["secondary"] == "#B89A6D"
    assert render_context["semantic_roles"]["comparator_curve"] == "secondary"
    assert render_context["style_roles"]["comparator_curve"] == "#B89A6D"
    assert render_context["typography"]["base_size"] == 10.5
    assert render_context["stroke"]["reference_linewidth"] == 1.1
    assert render_context["grid"]["major_axis"] == "both"
