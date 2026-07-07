from __future__ import annotations

import json
from pathlib import Path
import sys

from med_autoscience.display_layout_qc import run_display_layout_qc
from med_autoscience.display_pack_gallery.assets import _image_size
from med_autoscience.display_pack_gallery.design_svg_renderer import (
    render_submission_graphical_abstract_gallery_preview,
)
from med_autoscience.display_pack_gallery.payloads import _style_context_for
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


def test_submission_graphical_abstract_reference_guided_flow_uses_wide_canvas(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "shell_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "layout_style": "reference_guided_flow",
        "title": "Question to claim-ready figure",
        "caption": "Synthetic renderer regression payload.",
        "quality_floor_policy": "brief_first_reference_guided_ai_candidate_not_single_template_reuse",
        "panels": [
            {
                "panel_id": "cohort",
                "panel_label": "A",
                "visual_role": "population",
                "evidence_cue": "Locked cohort and endpoint refs",
                "title": "Study cohort",
                "subtitle": "Registry records mapped to auditable outcomes",
                "rows": [
                    {
                        "cards": [
                            {"card_id": "cohort", "title": "Analytic set", "value": "15,120", "detail": "patients", "accent_role": "primary"}
                        ]
                    }
                ],
            },
            {
                "panel_id": "model_signal",
                "panel_label": "B",
                "visual_role": "model_signal",
                "evidence_cue": "Validation statistic preserved",
                "title": "Risk signal",
                "subtitle": "Model separates low- and high-risk strata",
                "rows": [
                    {
                        "cards": [
                            {"card_id": "model", "title": "Validation", "value": "C=0.86", "detail": "holdout", "accent_role": "contrast"}
                        ]
                    }
                ],
            },
            {
                "panel_id": "clinical_action",
                "panel_label": "C",
                "visual_role": "clinical_use",
                "evidence_cue": "Owner gate before paper use",
                "title": "Care action",
                "subtitle": "High-risk group routed to closer follow-up",
                "rows": [
                    {
                        "cards": [
                            {"card_id": "action", "title": "Owner gate", "value": "Review", "detail": "refs", "accent_role": "secondary"}
                        ]
                    }
                ],
            },
        ],
        "footer_pills": [
            {"pill_id": "p1", "panel_id": "cohort", "label": "Cohort + endpoint", "style_role": "primary"},
            {"pill_id": "p2", "panel_id": "model_signal", "label": "Signal + validation", "style_role": "contrast"},
            {"pill_id": "p3", "panel_id": "clinical_action", "label": "Decision + owner gate", "style_role": "secondary"},
        ],
    }

    layout_path = tmp_path / "ga-square.layout.json"
    output_png_path = tmp_path / "ga-square.png"
    render_submission_graphical_abstract_gallery_preview(
        shell_payload=payload,
        render_context=_style_context_for("submission_graphical_abstract"),
        output_svg_path=tmp_path / "ga-square.svg",
        output_png_path=output_png_path,
        output_layout_path=layout_path,
    )

    sidecar = json.loads(layout_path.read_text(encoding="utf-8"))
    panel_boxes = [box for box in sidecar["panel_boxes"] if box["box_type"] == "panel"]
    visual_glyphs = [box for box in sidecar["layout_boxes"] if box["box_type"] == "visual_glyph"]
    evidence_cues = [box for box in sidecar["layout_boxes"] if box["box_type"] == "evidence_cue"]
    arrows = [box for box in sidecar["guide_boxes"] if box["box_type"] == "arrow_connector"]

    assert sidecar["metrics"]["layout_style"] == "reference_guided_flow"
    assert sidecar["metrics"]["panel_count"] == 3
    assert sidecar["metrics"]["visual_roles"] == ["population", "model_signal", "clinical_use"]
    assert sidecar["metrics"]["source_renderer"] == "mas_reference_guided_svg_preview.v6"
    assert sidecar["metrics"]["canvas_size_px"] == [1800, 1000]
    assert set(sidecar["metrics"]["design_rules"]) >= {
        "three_panel_full_width",
        "left_to_right_reading_order",
        "stable_panel_boundaries",
        "semantic_panel_glyphs",
        "text_first_semantic_callouts",
        "evidence_cue_per_panel",
        "separate_quality_band",
    }
    assert _image_size(output_png_path) == (1800, 1000)
    assert len(panel_boxes) == 3
    assert len(visual_glyphs) == 3
    assert len(evidence_cues) == 3
    assert len(arrows) == 2
    assert max(box["x1"] for box in panel_boxes) > 0.92
    assert min(box["x0"] for box in panel_boxes) <= 0.06
    assert min(box["y0"] for box in panel_boxes) > 0.18
    assert max(box["y1"] for box in panel_boxes) < 0.77

    qc_result = run_display_layout_qc(
        qc_profile="submission_graphical_abstract",
        layout_sidecar=sidecar,
    )
    assert qc_result["status"] == "pass"
    assert qc_result["issues"] == []


def test_submission_graphical_abstract_rasterizes_relative_svg_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    payload = {
        "schema_version": 1,
        "shell_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "layout_style": "reference_guided_flow",
        "title": "Question to claim-ready figure",
        "caption": "Relative path rasterization regression payload.",
        "panels": [
            {
                "panel_id": "brief",
                "panel_label": "A",
                "visual_role": "brief",
                "evidence_cue": "Claim + evidence refs locked",
                "title": "Figure brief",
                "subtitle": "Core claim and evidence chain first",
                "rows": [{"cards": [{"card_id": "brief", "title": "Locked inputs", "value": "Brief", "detail": "refs"}]}],
            },
            {
                "panel_id": "reference_style",
                "panel_label": "B",
                "visual_role": "reference_style",
                "evidence_cue": "Reference style + preserve list",
                "title": "Reference style",
                "subtitle": "Journal family and preserve list",
                "rows": [{"cards": [{"card_id": "reference", "title": "Style brief", "value": "Target", "detail": "style"}]}],
            },
            {
                "panel_id": "critic_gate",
                "panel_label": "C",
                "visual_role": "critic_gate",
                "evidence_cue": "Visual critic before owner use",
                "title": "Candidate gate",
                "subtitle": "Visual critic before owner use",
                "rows": [{"cards": [{"card_id": "gate", "title": "Required refs", "value": "Review", "detail": "gate"}]}],
            },
        ],
        "footer_pills": [
            {"pill_id": "p1", "label": "Claim + evidence", "style_role": "primary"},
            {"pill_id": "p2", "label": "Style + preserve", "style_role": "contrast"},
            {"pill_id": "p3", "label": "Critic + owner gate", "style_role": "secondary"},
        ],
    }
    relative_root = Path("relative-assets")
    output_png_path = relative_root / "ga.png"

    render_submission_graphical_abstract_gallery_preview(
        shell_payload=payload,
        render_context=_style_context_for("submission_graphical_abstract"),
        output_svg_path=relative_root / "ga.svg",
        output_png_path=output_png_path,
        output_layout_path=relative_root / "ga.layout.json",
    )

    assert _image_size(output_png_path) == (1800, 1000)
    assert output_png_path.stat().st_size > 20_000
