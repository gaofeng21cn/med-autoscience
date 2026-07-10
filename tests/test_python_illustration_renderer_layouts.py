from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from med_autoscience.display_layout_qc import run_display_layout_qc
from med_autoscience.display_pack_gallery.assets import _image_size
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
                                "evidence_ref": "test:evidence/cohort",
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
                                "evidence_ref": "test:evidence/c-index",
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


def test_submission_graphical_abstract_clinical_storyline_uses_pack_renderer(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "shell_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "layout_style": "clinical_storyline",
        "title": "From patient profiles to risk-guided follow-up",
        "caption": "Illustrative non-quantitative renderer regression payload.",
        "scientific_claim_carried": False,
        "quality_floor_policy": "brief_first_reference_guided_ai_candidate_not_single_template_reuse",
        "panels": [
            {
                "panel_id": "study_population",
                "panel_label": "A",
                "visual_role": "population",
                "title": "Study population",
                "subtitle": "Clinical profiles define the population of interest",
                "rows": [
                    {
                        "cards": [
                            {"card_id": "population", "title": "Stage message", "value": "Patient profiles", "accent_role": "primary"}
                        ]
                    }
                ],
            },
            {
                "panel_id": "core_finding",
                "panel_label": "B",
                "visual_role": "model_signal",
                "title": "Core finding",
                "subtitle": "A reproducible signal organizes relative risk",
                "rows": [
                    {
                        "cards": [
                            {"card_id": "finding", "title": "Stage message", "value": "Risk gradient", "accent_role": "contrast"}
                        ]
                    }
                ],
            },
            {
                "panel_id": "clinical_meaning",
                "panel_label": "C",
                "visual_role": "clinical_use",
                "title": "Clinical meaning",
                "subtitle": "Follow-up intensity can be matched to need",
                "rows": [
                    {
                        "cards": [
                            {"card_id": "meaning", "title": "Stage message", "value": "Matched follow-up", "accent_role": "secondary"}
                        ]
                    }
                ],
            },
        ],
        "footer_pills": [],
    }

    layout_path = tmp_path / "ga.layout.json"
    output_png_path = tmp_path / "ga.png"
    render_illustration_shell(
        template_id="fenggaolab.org.medical-display-core::submission_graphical_abstract",
        shell_payload=payload,
        render_context=_style_context_for("submission_graphical_abstract"),
        output_svg_path=tmp_path / "ga.svg",
        output_png_path=output_png_path,
        output_layout_path=layout_path,
        payload_path=tmp_path / "ga.payload.json",
    )

    sidecar = json.loads(layout_path.read_text(encoding="utf-8"))
    panel_boxes = [box for box in sidecar["panel_boxes"] if box["box_type"] == "panel"]
    visual_glyphs = [box for box in sidecar["layout_boxes"] if box["box_type"] == "visual_glyph"]
    stage_callouts = [box for box in sidecar["layout_boxes"] if box["box_type"] == "stage_callout"]
    arrows = [box for box in sidecar["guide_boxes"] if box["box_type"] == "arrow_connector"]

    assert sidecar["metrics"]["layout_style"] == "clinical_storyline"
    assert sidecar["metrics"]["panel_count"] == 3
    assert sidecar["metrics"]["visual_roles"] == ["population", "signal", "action"]
    assert sidecar["metrics"]["source_renderer"] == "scholarskills_pack_graphical_abstract.v2"
    assert sidecar["metrics"]["canvas_size_px"] == [1800, 1000]
    assert sidecar["metrics"]["governance_metadata_visible_in_artwork"] is False
    assert set(sidecar["metrics"]["design_rules"]) >= {
        "continuous_left_to_right_clinical_story",
        "one_visual_glyph_per_stage",
        "central_signal_is_visual_hero",
        "no_nested_cards",
        "no_visible_governance_metadata",
        "editable_svg_source",
    }
    assert _image_size(output_png_path) == (1800, 1000)
    assert len(panel_boxes) == 3
    assert len(visual_glyphs) == 3
    assert len(stage_callouts) == 3
    assert len(arrows) == 2
    assert max(box["x1"] for box in panel_boxes) > 0.92
    assert min(box["x0"] for box in panel_boxes) <= 0.06
    assert not any(
        box["box_type"] in {"card_box", "footer_pill", "evidence_cue"}
        for box in sidecar["layout_boxes"]
    )

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
        "layout_style": "clinical_storyline",
        "title": "Population to signal to care",
        "caption": "Relative path rasterization regression payload.",
        "panels": [
            {
                "panel_id": "brief",
                "panel_label": "A",
                "visual_role": "population",
                "title": "Study population",
                "subtitle": "Clinical profiles define the population",
                "rows": [{"cards": [{"card_id": "brief", "title": "Stage message", "value": "Patient profiles"}]}],
            },
            {
                "panel_id": "core_finding",
                "panel_label": "B",
                "visual_role": "model_signal",
                "title": "Core finding",
                "subtitle": "A reproducible signal organizes risk",
                "rows": [{"cards": [{"card_id": "finding", "title": "Stage message", "value": "Risk gradient"}]}],
            },
            {
                "panel_id": "clinical_meaning",
                "panel_label": "C",
                "visual_role": "clinical_use",
                "title": "Clinical meaning",
                "subtitle": "Follow-up intensity can match need",
                "rows": [{"cards": [{"card_id": "meaning", "title": "Stage message", "value": "Matched follow-up"}]}],
            },
        ],
        "footer_pills": [],
    }
    relative_root = Path("relative-assets")
    output_png_path = relative_root / "ga.png"

    render_illustration_shell(
        template_id="fenggaolab.org.medical-display-core::submission_graphical_abstract",
        shell_payload=payload,
        render_context=_style_context_for("submission_graphical_abstract"),
        output_svg_path=relative_root / "ga.svg",
        output_png_path=output_png_path,
        output_layout_path=relative_root / "ga.layout.json",
        payload_path=relative_root / "ga.payload.json",
    )

    assert _image_size(output_png_path) == (1800, 1000)
    assert output_png_path.stat().st_size > 20_000


def test_submission_graphical_abstract_rejects_numeric_value_without_evidence_ref(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "shell_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "title": "Numeric evidence gate",
        "caption": "Regression payload.",
        "panels": [
            {
                "panel_id": "population",
                "panel_label": "A",
                "visual_role": "population",
                "title": "Population",
                "subtitle": "Evidence-bound count",
                "rows": [{"cards": [{"card_id": "count", "title": "Cohort", "value": "15,120"}]}],
            }
        ],
    }

    with pytest.raises(ValueError, match="must provide evidence_ref before a numeric value can be rendered"):
        render_illustration_shell(
            template_id="fenggaolab.org.medical-display-core::submission_graphical_abstract",
            shell_payload=payload,
            render_context=_style_context_for("submission_graphical_abstract"),
            output_svg_path=tmp_path / "ga.svg",
            output_png_path=tmp_path / "ga.png",
            output_layout_path=tmp_path / "ga.layout.json",
            payload_path=tmp_path / "ga.payload.json",
        )
