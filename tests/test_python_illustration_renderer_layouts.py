from __future__ import annotations

import json
from pathlib import Path
import sys

from med_autoscience.display_layout_qc import run_display_layout_qc
from med_autoscience.display_pack_gallery_parts.payloads import _style_context_for
from med_autoscience.display_pack_paths import core_medical_display_pack_python_src_root

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_SRC = core_medical_display_pack_python_src_root(REPO_ROOT)
sys.path.insert(0, str(PACK_SRC))

from fenggaolab_org_medical_display_core.illustration_shells import render_illustration_shell


def test_submission_graphical_abstract_two_panel_payload_uses_full_width(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "shell_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "title": "Two-panel graphical abstract layout check",
        "caption": "Synthetic renderer regression payload.",
        "panels": [
            {
                "panel_id": "population",
                "panel_label": "A",
                "title": "Population",
                "subtitle": "Locked cohort",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "cohort",
                                "title": "Analytic cohort",
                                "value": "15,120",
                                "detail": "patients",
                                "accent_role": "primary",
                            }
                        ]
                    }
                ],
            },
            {
                "panel_id": "result",
                "panel_label": "B",
                "title": "Result",
                "subtitle": "Primary endpoint",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "estimate",
                                "title": "Validation C-index",
                                "value": "0.86",
                                "detail": "temporal holdout",
                                "accent_role": "contrast",
                            }
                        ]
                    }
                ],
            },
        ],
        "footer_pills": [
            {"pill_id": "p1", "panel_id": "population", "label": "Cohort lock", "style_role": "primary"},
            {"pill_id": "p2", "panel_id": "result", "label": "Model evidence", "style_role": "contrast"},
        ],
    }

    layout_path = tmp_path / "ga.layout.json"
    render_illustration_shell(
        template_id="fenggaolab.org.medical-display-core::submission_graphical_abstract",
        shell_payload=payload,
        render_context=_style_context_for("submission_graphical_abstract"),
        output_svg_path=tmp_path / "ga.svg",
        output_png_path=tmp_path / "ga.png",
        output_layout_path=layout_path,
        payload_path=tmp_path / "ga.payload.json",
    )

    sidecar = json.loads(layout_path.read_text(encoding="utf-8"))
    panel_boxes = [box for box in sidecar["panel_boxes"] if box["box_type"] == "panel"]

    assert sidecar["metrics"]["panel_count"] == 2
    assert len(panel_boxes) == 2
    assert min(box["x0"] for box in panel_boxes) < 0.04
    assert max(box["x1"] for box in panel_boxes) > 0.96


def test_submission_graphical_abstract_square_storyline_uses_square_canvas(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "shell_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "layout_style": "square_storyline",
        "title": "Cohort to risk-stratified care",
        "caption": "Synthetic renderer regression payload.",
        "panels": [
            {
                "panel_id": "population",
                "panel_label": "A",
                "visual_role": "population",
                "title": "Population",
                "subtitle": "Cohort locked before modeling",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "cohort",
                                "title": "Analytic cohort",
                                "value": "15,120",
                                "detail": "auditable outcomes",
                                "accent_role": "primary",
                            }
                        ]
                    }
                ],
            },
            {
                "panel_id": "model_signal",
                "panel_label": "B",
                "visual_role": "model_signal",
                "title": "Model signal",
                "subtitle": "Primary endpoint risk ranking",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "c_index",
                                "title": "Validation C-index",
                                "value": "0.86",
                                "detail": "temporal holdout",
                                "accent_role": "contrast",
                            }
                        ]
                    }
                ],
            },
            {
                "panel_id": "clinical_use",
                "panel_label": "C",
                "visual_role": "clinical_use",
                "title": "Clinical use",
                "subtitle": "Risk-stratified follow-up",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "risk_group",
                                "title": "High-risk group",
                                "value": "3.4x",
                                "detail": "event enrichment",
                                "accent_role": "secondary",
                            }
                        ]
                    }
                ],
            },
        ],
        "footer_pills": [
            {"pill_id": "p1", "panel_id": "population", "label": "Cohort lock", "style_role": "primary"},
            {"pill_id": "p2", "panel_id": "model_signal", "label": "Model evidence", "style_role": "contrast"},
            {"pill_id": "p3", "panel_id": "clinical_use", "label": "Clinical message", "style_role": "secondary"},
        ],
    }

    layout_path = tmp_path / "ga-square.layout.json"
    render_illustration_shell(
        template_id="fenggaolab.org.medical-display-core::submission_graphical_abstract",
        shell_payload=payload,
        render_context=_style_context_for("submission_graphical_abstract"),
        output_svg_path=tmp_path / "ga-square.svg",
        output_png_path=tmp_path / "ga-square.png",
        output_layout_path=layout_path,
        payload_path=tmp_path / "ga-square.payload.json",
    )

    sidecar = json.loads(layout_path.read_text(encoding="utf-8"))
    panel_boxes = [box for box in sidecar["panel_boxes"] if box["box_type"] == "panel"]
    visual_glyphs = [box for box in sidecar["layout_boxes"] if box["box_type"] == "visual_glyph"]
    arrows = [box for box in sidecar["guide_boxes"] if box["box_type"] == "arrow_connector"]

    assert sidecar["metrics"]["layout_style"] == "square_storyline"
    assert sidecar["metrics"]["panel_count"] == 3
    assert sidecar["metrics"]["visual_roles"] == ["population", "model_signal", "clinical_use"]
    assert len(panel_boxes) == 3
    assert len(visual_glyphs) == 3
    assert len(arrows) == 2
    assert max(box["x1"] for box in panel_boxes) > 0.94
    assert min(box["x0"] for box in panel_boxes) < 0.06
    assert min(box["y0"] for box in panel_boxes) > 0.12

    qc_result = run_display_layout_qc(
        qc_profile="submission_graphical_abstract",
        layout_sidecar=sidecar,
    )
    assert qc_result["status"] == "pass"
    assert qc_result["issues"] == []
