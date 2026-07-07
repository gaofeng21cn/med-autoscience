from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_gallery.svg_primitives import (
    append_arrow,
    append_badge,
    append_circle,
    append_line,
    append_rect,
    append_text,
    normalized_box,
    relative_box,
    render_svg_to_png,
    svg_header,
)

CANVAS_WIDTH = 1800
CANVAS_HEIGHT = 1000
GA_LAYOUT_STYLE = "reference_guided_flow"
GA_RENDERER_SOURCE = "mas_reference_guided_svg_preview.v6"


def render_submission_graphical_abstract_gallery_preview(
    *,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
) -> None:
    width = CANVAS_WIDTH
    height = CANVAS_HEIGHT
    colors = _submission_colors(
        palette=dict(render_context.get("palette") or {}),
        style_roles=dict(render_context.get("style_roles") or {}),
    )
    panels = [dict(item) for item in list(shell_payload.get("panels") or [])[:3]]
    footer_pills = [dict(item) for item in list(shell_payload.get("footer_pills") or [])]
    title = str(shell_payload.get("title") or "Submission graphical abstract").strip()
    subtitle = str(shell_payload.get("caption") or "Reference-guided flow from source brief to review-ready candidate.").strip()

    layout_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    panel_boxes = _panel_boxes(width=width, height=height, count=max(1, len(panels)))
    svg_parts = [svg_header(width=width, height=height)]
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="{colors["background"]}"/>\n')
    _append_background(svg_parts, width=width, height=height, colors=colors)
    _append_header(svg_parts, layout_boxes, title=title, subtitle=subtitle, width=width, height=height, colors=colors)
    for index, panel in enumerate(panels):
        panel_box = panel_boxes[index]
        panel_id = str(panel.get("panel_id") or f"panel_{index + 1}").strip() or f"panel_{index + 1}"
        panel_box["box_id"] = f"panel_{panel_id}"
        panel_box["box_type"] = "panel"
        accent = _role_color(panel.get("visual_role") or panel.get("panel_id"), index=index, colors=colors)
        soft = _role_soft_color(panel.get("visual_role") or panel.get("panel_id"), index=index, colors=colors)
        _append_workflow_node(
            svg_parts,
            layout_boxes,
            panel=panel,
            panel_box=panel_box,
            panel_id=panel_id,
            index=index,
            accent=accent,
            soft=soft,
            colors=colors,
            width=width,
            height=height,
        )

    for index, (left, right) in enumerate(zip(panel_boxes, panel_boxes[1:], strict=False)):
        arrow_box = {
            "x0": left["x0"] + left["w"] + width * 0.014,
            "y0": left["y0"] + left["h"] * 0.520,
            "w": right["x0"] - (left["x0"] + left["w"]) - width * 0.028,
            "h": height * 0.040,
        }
        append_arrow(svg_parts, arrow_box, color=colors["neutral"])
        guide_boxes.append(
            normalized_box(
                arrow_box,
                width=width,
                height=height,
                box_id=f"arrow_connector_{index + 1}",
                box_type="arrow_connector",
            )
        )

    _append_quality_rail(svg_parts, layout_boxes, footer_pills=footer_pills, colors=colors, width=width, height=height)
    svg_parts.append("</svg>\n")
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    output_svg_path.write_text("".join(svg_parts), encoding="utf-8")
    render_svg_to_png(output_svg_path=output_svg_path, output_png_path=output_png_path, width=width, height=height)
    _write_layout(
        output_layout_path=output_layout_path,
        shell_payload={**shell_payload, "layout_style": GA_LAYOUT_STYLE},
        render_context=render_context,
        layout_boxes=layout_boxes,
        panel_boxes=[normalized_box(item, width=width, height=height, box_id=item["box_id"], box_type="panel") for item in panel_boxes],
        guide_boxes=guide_boxes,
    )


def _submission_colors(*, palette: dict[str, Any], style_roles: dict[str, Any]) -> dict[str, str]:
    def color(key: str, fallback: str) -> str:
        return str(style_roles.get(key) or palette.get(key) or fallback).strip() or fallback

    return {
        "background": color("background", "#FFFFFF"),
        "text": color("text", "#17222B"),
        "muted": color("muted", "#66717C"),
        "grid": color("grid", "#D7E0E7"),
        "neutral": color("neutral", "#17222B"),
        "light": color("light", "#F1F5F7"),
        "primary": color("primary", "#245A6B"),
        "secondary": color("secondary", "#8B3A3A"),
        "contrast": color("contrast", "#2166AC"),
        "primary_soft": color("primary_soft", "#DDECF0"),
        "secondary_soft": color("secondary_soft", "#F3DDDD"),
        "contrast_soft": color("contrast_soft", "#DCE9F5"),
        "neutral_soft": color("light", "#F1F5F7"),
        "paper": "#FBFDFE",
        "panel": "#FFFFFF",
        "ink_soft": "#EEF5F7",
        "warm": "#F7F1EA",
    }


def _append_background(parts: list[str], *, width: int, height: int, colors: dict[str, str]) -> None:
    band = {"x0": width * 0.070, "y0": height * 0.355, "w": width * 0.860, "h": height * 0.235}
    append_rect(parts, band, fill=colors["ink_soft"], stroke="none", stroke_width=0, radius=band["h"] / 2.0)
    append_line(
        parts,
        x1=width * 0.120,
        y1=height * 0.475,
        x2=width * 0.880,
        y2=height * 0.475,
        color=colors["grid"],
        stroke_width=8,
    )


def _append_header(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    title: str,
    subtitle: str,
    width: int,
    height: int,
    colors: dict[str, str],
) -> None:
    append_text(
        parts,
        layout_boxes,
        text=title,
        x=width * 0.058,
        y=height * 0.088,
        max_width=width * 0.680,
        font_size=46,
        font_weight="700",
        color=colors["text"],
        box_id="title",
        box_type="title",
        width=width,
        height=height,
        max_lines=1,
    )
    append_text(
        parts,
        layout_boxes,
        text=subtitle,
        x=width * 0.060,
        y=height * 0.138,
        max_width=width * 0.660,
        font_size=20,
        font_weight="400",
        color=colors["muted"],
        box_id="subtitle",
        box_type="subtitle",
        width=width,
        height=height,
        max_lines=1,
    )
    append_text(
        parts,
        layout_boxes,
        text="Reference-guided GA",
        x=width * 0.762,
        y=height * 0.090,
        max_width=width * 0.190,
        font_size=20,
        font_weight="700",
        color=colors["secondary"],
        box_id="surface_label",
        box_type="surface_label",
        width=width,
        height=height,
        max_lines=1,
    )


def _panel_boxes(*, width: int, height: int, count: int) -> list[dict[str, float]]:
    margin_x = width * 0.060
    gap = width * 0.055
    top = height * 0.205
    panel_height = height * 0.555
    panel_width = (width - margin_x * 2.0 - gap * float(max(0, count - 1))) / float(count)
    return [
        {
            "x0": margin_x + index * (panel_width + gap),
            "y0": top,
            "w": panel_width,
            "h": panel_height,
        }
        for index in range(count)
    ]


def _footer_boxes(*, width: int, height: int, pills: list[dict[str, Any]]) -> list[dict[str, float]]:
    if not pills:
        return []
    margin_x = width * 0.060
    gap = width * 0.030
    pill_width = (width - margin_x * 2.0 - gap * float(len(pills) - 1)) / float(len(pills))
    y0 = height * 0.835
    return [
        {
            "x0": margin_x + index * (pill_width + gap),
            "y0": y0,
            "w": pill_width,
            "h": height * 0.055,
        }
        for index in range(len(pills))
    ]


def _first_card(panel: dict[str, Any]) -> dict[str, Any]:
    for row in list(panel.get("rows") or []):
        if not isinstance(row, dict):
            continue
        cards = list(row.get("cards") or [])
        if cards and isinstance(cards[0], dict):
            return dict(cards[0])
    return {"title": panel.get("title") or "", "value": "", "detail": ""}


def _role_color(role: object, *, index: int, colors: dict[str, str]) -> str:
    role_text = str(role or "").strip().lower()
    if role_text in {"population", "source_data", "cohort", "brief", "claim_evidence"}:
        return colors["primary"]
    if role_text in {"model_signal", "model", "algorithm", "mechanism", "reference_style", "style_brief"}:
        return colors["contrast"]
    if role_text in {"clinical_use", "decision", "action", "care_path", "critic_gate", "owner_gate"}:
        return colors["secondary"]
    return (colors["primary"], colors["contrast"], colors["secondary"])[index % 3]


def _role_soft_color(role: object, *, index: int, colors: dict[str, str]) -> str:
    role_text = str(role or "").strip().lower()
    if role_text in {"population", "source_data", "cohort", "brief", "claim_evidence"}:
        return colors["primary_soft"]
    if role_text in {"model_signal", "model", "algorithm", "mechanism", "reference_style", "style_brief"}:
        return colors["contrast_soft"]
    if role_text in {"clinical_use", "decision", "action", "care_path", "critic_gate", "owner_gate"}:
        return colors["secondary_soft"]
    return (colors["primary_soft"], colors["contrast_soft"], colors["secondary_soft"])[index % 3]


def _append_workflow_node(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    panel: dict[str, Any],
    panel_box: dict[str, float],
    panel_id: str,
    index: int,
    accent: str,
    soft: str,
    colors: dict[str, str],
    width: int,
    height: int,
) -> None:
    append_rect(parts, panel_box, fill=colors["paper"], stroke=accent, stroke_width=3, radius=28)
    append_badge(
        parts,
        layout_boxes,
        label=str(panel.get("panel_label") or chr(65 + index)),
        box=relative_box(panel_box, 0.050, 0.060, 0.158, 0.165),
        fill=accent,
        text_color="#FFFFFF",
        width=width,
        height=height,
        box_id=f"panel_label_{panel_id}",
        box_type="panel_label",
    )
    glyph_box = relative_box(panel_box, 0.180, 0.105, 0.820, 0.455)
    append_rect(parts, glyph_box, fill=soft, stroke=accent, stroke_width=2.5, radius=24)
    _append_glyph(parts, glyph_box, role=str(panel.get("visual_role") or ""), accent=accent, colors=colors)
    layout_boxes.append(normalized_box(glyph_box, width=width, height=height, box_id=f"visual_glyph_{panel_id}", box_type="visual_glyph"))
    append_text(
        parts,
        layout_boxes,
        text=str(panel.get("title") or ""),
        x=panel_box["x0"] + panel_box["w"] * 0.105,
        y=panel_box["y0"] + panel_box["h"] * 0.535,
        max_width=panel_box["w"] * 0.790,
        font_size=28,
        font_weight="700",
        color=colors["text"],
        box_id=f"panel_title_{panel_id}",
        box_type="panel_title",
        width=width,
        height=height,
        max_lines=1,
    )
    append_text(
        parts,
        layout_boxes,
        text=str(panel.get("subtitle") or ""),
        x=panel_box["x0"] + panel_box["w"] * 0.105,
        y=panel_box["y0"] + panel_box["h"] * 0.610,
        max_width=panel_box["w"] * 0.790,
        font_size=18,
        font_weight="400",
        color=colors["muted"],
        box_id=f"panel_subtitle_{panel_id}",
        box_type="panel_subtitle",
        width=width,
        height=height,
        max_lines=2,
    )
    _append_evidence_cue(parts, layout_boxes, panel=panel, panel_box=panel_box, panel_id=panel_id, accent=accent, colors=colors, width=width, height=height)
    _append_card(parts, layout_boxes, panel=panel, panel_box=panel_box, panel_id=panel_id, accent=accent, colors=colors, width=width, height=height)


def _append_evidence_cue(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    panel: dict[str, Any],
    panel_box: dict[str, float],
    panel_id: str,
    accent: str,
    colors: dict[str, str],
    width: int,
    height: int,
) -> None:
    cue_box = relative_box(panel_box, 0.105, 0.700, 0.895, 0.775)
    append_rect(parts, cue_box, fill=colors["ink_soft"], stroke=colors["grid"], stroke_width=1.5, radius=cue_box["h"] / 2.0)
    append_circle(
        parts,
        cx=cue_box["x0"] + cue_box["h"] * 0.50,
        cy=cue_box["y0"] + cue_box["h"] * 0.50,
        r=cue_box["h"] * 0.20,
        fill=accent,
    )
    cue = str(panel.get("evidence_cue") or panel.get("caption") or "Evidence refs locked").strip()
    append_text(
        parts,
        layout_boxes,
        text=cue,
        x=cue_box["x0"] + cue_box["h"] * 0.86,
        y=cue_box["y0"] + cue_box["h"] * 0.64,
        max_width=cue_box["w"] - cue_box["h"] * 1.04,
        font_size=15,
        font_weight="700",
        color=colors["text"],
        box_id=f"evidence_cue_{panel_id}",
        box_type="evidence_cue",
        width=width,
        height=height,
        max_lines=1,
    )


def _append_card(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    panel: dict[str, Any],
    panel_box: dict[str, float],
    panel_id: str,
    accent: str,
    colors: dict[str, str],
    width: int,
    height: int,
) -> None:
    card = _first_card(panel)
    card_box = relative_box(panel_box, 0.105, 0.795, 0.895, 0.955)
    append_rect(parts, card_box, fill="#FFFFFF", stroke=colors["grid"], stroke_width=2, radius=18)
    layout_boxes.append(normalized_box(card_box, width=width, height=height, box_id=f"card_{panel_id}", box_type="card_box"))
    append_text(
        parts,
        layout_boxes,
        text=str(card.get("title") or ""),
        x=card_box["x0"] + card_box["w"] * 0.060,
        y=card_box["y0"] + card_box["h"] * 0.420,
        max_width=card_box["w"] * 0.370,
        font_size=16,
        font_weight="400",
        color=colors["muted"],
        box_id=f"card_title_{panel_id}",
        box_type="card_title",
        width=width,
        height=height,
        max_lines=1,
    )
    append_text(
        parts,
        layout_boxes,
        text=str(card.get("value") or ""),
        x=card_box["x0"] + card_box["w"] * 0.500,
        y=card_box["y0"] + card_box["h"] * 0.440,
        max_width=card_box["w"] * 0.390,
        font_size=28,
        font_weight="700",
        color=accent,
        box_id=f"card_value_{panel_id}",
        box_type="card_value",
        width=width,
        height=height,
        max_lines=1,
    )
    append_text(
        parts,
        layout_boxes,
        text=str(card.get("detail") or ""),
        x=card_box["x0"] + card_box["w"] * 0.500,
        y=card_box["y0"] + card_box["h"] * 0.785,
        max_width=card_box["w"] * 0.390,
        font_size=14,
        font_weight="400",
        color=colors["muted"],
        box_id=f"card_detail_{panel_id}",
        box_type="card_detail",
        width=width,
        height=height,
        max_lines=1,
    )


def _append_quality_rail(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    footer_pills: list[dict[str, Any]],
    colors: dict[str, str],
    width: int,
    height: int,
) -> None:
    band = {"x0": width * 0.050, "y0": height * 0.803, "w": width * 0.900, "h": height * 0.115}
    append_rect(parts, band, fill=colors["light"], stroke=colors["grid"], stroke_width=2, radius=22)
    append_text(
        parts,
        layout_boxes,
        text="Quality band",
        x=band["x0"] + band["w"] * 0.025,
        y=band["y0"] + band["h"] * 0.390,
        max_width=band["w"] * 0.145,
        font_size=18,
        font_weight="700",
        color=colors["text"],
        box_id="quality_band_label",
        box_type="quality_band_label",
        width=width,
        height=height,
        max_lines=1,
    )
    footer_boxes = _footer_boxes(width=width, height=height, pills=footer_pills)
    for pill, pill_box in zip(footer_pills, footer_boxes, strict=False):
        pill_id = str(pill.get("pill_id") or "").strip() or f"pill_{len(layout_boxes) + 1}"
        style_role = str(pill.get("style_role") or "neutral").strip().lower()
        fill = colors.get(f"{style_role}_soft", colors["neutral_soft"])
        stroke = colors.get(style_role, colors["neutral"])
        append_rect(parts, pill_box, fill=fill, stroke=stroke, stroke_width=2, radius=18)
        layout_boxes.append(normalized_box(pill_box, width=width, height=height, box_id=f"footer_pill_{pill_id}", box_type="footer_pill"))
        append_text(
            parts,
            layout_boxes,
            text=str(pill.get("label") or ""),
            x=pill_box["x0"] + pill_box["w"] * 0.070,
            y=pill_box["y0"] + pill_box["h"] * 0.620,
            max_width=pill_box["w"] * 0.850,
            font_size=17,
            font_weight="700",
            color=colors["text"],
            box_id=f"footer_pill_text_{pill_id}",
            box_type="footer_pill_text",
            width=width,
            height=height,
            max_lines=1,
        )


def _append_glyph(parts: list[str], box: dict[str, float], *, role: str, accent: str, colors: dict[str, str]) -> None:
    role_text = str(role or "").strip().lower()
    if role_text in {"brief", "claim_evidence"}:
        _append_brief_glyph(parts, box, accent=accent)
    elif role_text in {"reference_style", "style_brief"}:
        _append_reference_glyph(parts, box, accent=accent, colors=colors)
    elif role_text in {"clinical_use", "decision", "action", "care_path"}:
        _append_care_action_glyph(parts, box, accent=accent, colors=colors)
    elif role_text in {"critic_gate", "owner_gate"}:
        _append_gate_glyph(parts, box, accent=accent)
    elif role_text in {"population", "source_data", "cohort"}:
        _append_population_glyph(parts, box, accent=accent)
    elif role_text in {"model_signal", "model", "algorithm", "mechanism"}:
        _append_model_glyph(parts, box, accent=accent)
    else:
        center = relative_box(box, 0.320, 0.300, 0.680, 0.460)
        append_rect(parts, center, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=10)
        _center_text(parts, center, label="Signal", color=accent, font_size=box["h"] * 0.060)


def _append_brief_glyph(parts: list[str], box: dict[str, float], *, accent: str) -> None:
    for offset, label in ((0.18, "Claim"), (0.42, "Evidence"), (0.66, "Refs")):
        node = relative_box(box, 0.230, offset, 0.770, offset + 0.135)
        append_rect(parts, node, fill="#FFFFFF", stroke=accent, stroke_width=2.2, radius=10)
        _center_text(parts, node, label=label, color=accent, font_size=box["h"] * 0.060)
    append_line(parts, x1=box["x0"] + box["w"] * 0.50, y1=box["y0"] + box["h"] * 0.320, x2=box["x0"] + box["w"] * 0.50, y2=box["y0"] + box["h"] * 0.420, color=accent, stroke_width=3)
    append_line(parts, x1=box["x0"] + box["w"] * 0.50, y1=box["y0"] + box["h"] * 0.555, x2=box["x0"] + box["w"] * 0.50, y2=box["y0"] + box["h"] * 0.660, color=accent, stroke_width=3)


def _append_reference_glyph(parts: list[str], box: dict[str, float], *, accent: str, colors: dict[str, str]) -> None:
    for cx, cy in ((0.33, 0.28), (0.58, 0.24), (0.48, 0.52)):
        card = {"x0": box["x0"] + box["w"] * cx - box["w"] * 0.150, "y0": box["y0"] + box["h"] * cy - box["h"] * 0.105, "w": box["w"] * 0.300, "h": box["h"] * 0.210}
        append_rect(parts, card, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=8)
        append_line(parts, x1=card["x0"] + card["w"] * 0.20, y1=card["y0"] + card["h"] * 0.38, x2=card["x0"] + card["w"] * 0.82, y2=card["y0"] + card["h"] * 0.38, color=accent, stroke_width=3.5)
        append_line(parts, x1=card["x0"] + card["w"] * 0.20, y1=card["y0"] + card["h"] * 0.64, x2=card["x0"] + card["w"] * 0.70, y2=card["y0"] + card["h"] * 0.64, color=colors["muted"], stroke_width=3.0)
    parts.append(
        f'<path d="M{box["x0"] + box["w"] * 0.24:.2f},{box["y0"] + box["h"] * 0.795:.2f} C{box["x0"] + box["w"] * 0.39:.2f},{box["y0"] + box["h"] * 0.690:.2f} '
        f'{box["x0"] + box["w"] * 0.61:.2f},{box["y0"] + box["h"] * 0.690:.2f} {box["x0"] + box["w"] * 0.760:.2f},{box["y0"] + box["h"] * 0.795:.2f}" '
        f'fill="none" stroke="{escape(accent)}" stroke-width="5" stroke-linecap="round"/>\n'
    )


def _append_gate_glyph(parts: list[str], box: dict[str, float], *, accent: str) -> None:
    center = relative_box(box, 0.285, 0.170, 0.715, 0.320)
    append_rect(parts, center, fill="#FFFFFF", stroke=accent, stroke_width=2.2, radius=10)
    _center_text(parts, center, label="Critic", color=accent, font_size=box["h"] * 0.064)
    append_line(parts, x1=box["x0"] + box["w"] * 0.50, y1=box["y0"] + box["h"] * 0.330, x2=box["x0"] + box["w"] * 0.34, y2=box["y0"] + box["h"] * 0.590, color=accent, stroke_width=3)
    append_line(parts, x1=box["x0"] + box["w"] * 0.50, y1=box["y0"] + box["h"] * 0.330, x2=box["x0"] + box["w"] * 0.66, y2=box["y0"] + box["h"] * 0.590, color=accent, stroke_width=3)
    for cx, label in ((0.32, "Pass"), (0.68, "Revise")):
        target = {"x0": box["x0"] + box["w"] * cx - box["w"] * 0.125, "y0": box["y0"] + box["h"] * 0.595, "w": box["w"] * 0.250, "h": box["h"] * 0.135}
        append_rect(parts, target, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=9)
        _center_text(parts, target, label=label, color=accent, font_size=box["h"] * 0.048)


def _append_care_action_glyph(parts: list[str], box: dict[str, float], *, accent: str, colors: dict[str, str]) -> None:
    _append_callout_stack(
        parts,
        box,
        accent=accent,
        eyebrow="ACTION",
        headline="HIGH RISK",
        summary="FOLLOW-UP",
        footnote="OWNER REVIEW",
    )


def _append_population_glyph(parts: list[str], box: dict[str, float], *, accent: str) -> None:
    _append_callout_stack(
        parts,
        box,
        accent=accent,
        eyebrow="COHORT",
        headline="15,120",
        summary="ENDPOINT LOCKED",
        footnote="REFS READY",
    )


def _append_model_glyph(parts: list[str], box: dict[str, float], *, accent: str) -> None:
    _append_callout_stack(
        parts,
        box,
        accent=accent,
        eyebrow="VALIDATION",
        headline="C=0.86",
        summary="LOW -> HIGH RISK",
        footnote="STRATA SEPARATED",
    )


def _append_callout_stack(
    parts: list[str],
    box: dict[str, float],
    *,
    accent: str,
    eyebrow: str,
    headline: str,
    summary: str,
    footnote: str,
) -> None:
    card = relative_box(box, 0.105, 0.120, 0.895, 0.880)
    append_rect(parts, card, fill="#FFFFFF", stroke=accent, stroke_width=2.4, radius=18)
    append_line(parts, x1=card["x0"] + card["w"] * 0.075, y1=card["y0"] + card["h"] * 0.270, x2=card["x0"] + card["w"] * 0.925, y2=card["y0"] + card["h"] * 0.270, color=accent, stroke_width=3)
    _center_text(parts, relative_box(card, 0.070, 0.030, 0.930, 0.240), label=eyebrow, color=accent, font_size=box["h"] * 0.072)
    _center_text(parts, relative_box(card, 0.070, 0.280, 0.930, 0.545), label=headline, color=accent, font_size=box["h"] * 0.128)
    _center_text(parts, relative_box(card, 0.075, 0.600, 0.925, 0.755), label=summary, color="#17222B", font_size=box["h"] * 0.068)
    _center_text(parts, relative_box(card, 0.075, 0.805, 0.925, 0.945), label=footnote, color=accent, font_size=box["h"] * 0.054)


def _center_text(parts: list[str], box: dict[str, float], *, label: str, color: str, font_size: float) -> None:
    parts.append(
        f'<text x="{box["x0"] + box["w"] * 0.50:.2f}" y="{box["y0"] + box["h"] * 0.66:.2f}" '
        f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.2f}" '
        f'font-weight="700" fill="{escape(color)}" text-anchor="middle">{escape(label)}</text>\n'
    )


def _write_layout(
    *,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    layout_boxes: list[dict[str, Any]],
    panel_boxes: list[dict[str, Any]],
    guide_boxes: list[dict[str, Any]],
) -> None:
    output_layout_path.parent.mkdir(parents=True, exist_ok=True)
    panels = list(shell_payload.get("panels") or [])
    output_layout_path.write_text(
        json.dumps(
            {
                "template_id": "submission_graphical_abstract",
                "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
                "layout_boxes": layout_boxes,
                "panel_boxes": panel_boxes,
                "guide_boxes": guide_boxes,
                "metrics": {
                    "layout_style": str(shell_payload.get("layout_style") or GA_LAYOUT_STYLE),
                    "panel_count": len(panels),
                    "panels": panels,
                    "footer_pills": list(shell_payload.get("footer_pills") or []),
                    "visual_roles": [str(panel.get("visual_role") or "").strip() for panel in panels],
                    "source_renderer": GA_RENDERER_SOURCE,
                    "canvas_size_px": [CANVAS_WIDTH, CANVAS_HEIGHT],
                    "design_rules": [
                        "three_panel_full_width",
                        "left_to_right_reading_order",
                        "stable_panel_boundaries",
                        "semantic_panel_glyphs",
                        "text_first_semantic_callouts",
                        "evidence_cue_per_panel",
                        "separate_quality_band",
                    ],
                },
                "render_context": render_context,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
