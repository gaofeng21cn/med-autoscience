from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_gallery_parts.svg_primitives import (
    append_arrow,
    append_badge,
    append_rect,
    append_text,
    normalized_box,
    relative_box,
    render_svg_to_png,
    svg_header,
)


def render_submission_graphical_abstract_gallery_preview(
    *,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
) -> None:
    width = 1800
    height = 1000
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    colors = _submission_colors(palette=palette, style_roles=style_roles)
    panels = [dict(item) for item in list(shell_payload.get("panels") or [])[:3]]
    footer_pills = [dict(item) for item in list(shell_payload.get("footer_pills") or [])]
    title = str(shell_payload.get("title") or "Submission graphical abstract").strip()
    subtitle = str(shell_payload.get("caption") or "Reference-guided flow from source brief to review-ready candidate.").strip()

    panel_boxes = _panel_boxes(width=width, height=height, count=max(1, len(panels)))
    layout_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    svg_parts = [svg_header(width=width, height=height)]
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="{colors["background"]}"/>\n')
    _append_flow_backbone(svg_parts, width=width, height=height, colors=colors)
    append_text(
        svg_parts,
        layout_boxes,
        text=title,
        x=width * 0.058,
        y=height * 0.088,
        max_width=width * 0.68,
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
        svg_parts,
        layout_boxes,
        text=subtitle,
        x=width * 0.060,
        y=height * 0.138,
        max_width=width * 0.66,
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
        svg_parts,
        layout_boxes,
        text="Reference-guided GA",
        x=width * 0.762,
        y=height * 0.090,
        max_width=width * 0.19,
        font_size=20,
        font_weight="700",
        color=colors["secondary"],
        box_id="surface_label",
        box_type="surface_label",
        width=width,
        height=height,
        max_lines=1,
    )

    for index, panel in enumerate(panels):
        panel_box = panel_boxes[index]
        accent = _role_color(panel.get("visual_role") or panel.get("panel_id"), index=index, colors=colors)
        panel_id = str(panel.get("panel_id") or f"panel_{index + 1}").strip() or f"panel_{index + 1}"
        panel_box["box_id"] = f"panel_{panel_id}"
        panel_box["box_type"] = "panel"
        _append_process_panel(
            svg_parts,
            layout_boxes,
            panel=panel,
            panel_box=panel_box,
            panel_id=panel_id,
            index=index,
            accent=accent,
            colors=colors,
            width=width,
            height=height,
        )

    for index, (left, right) in enumerate(zip(panel_boxes, panel_boxes[1:], strict=False)):
        arrow_box = {
            "x0": left["x0"] + left["w"] + width * 0.012,
            "y0": left["y0"] + left["h"] * 0.500,
            "w": right["x0"] - (left["x0"] + left["w"]) - width * 0.024,
            "h": height * 0.030,
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

    _append_quality_band(svg_parts, layout_boxes, footer_pills=footer_pills, colors=colors, width=width, height=height)
    svg_parts.append("</svg>\n")
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    output_svg_path.write_text("".join(svg_parts), encoding="utf-8")
    render_svg_to_png(output_svg_path=output_svg_path, output_png_path=output_png_path, width=width, height=height)
    _write_layout(
        output_layout_path=output_layout_path,
        shell_payload={**shell_payload, "layout_style": "reference_guided_flow"},
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
        "text": color("text", "#13293D"),
        "muted": color("muted", "#64748B"),
        "grid": color("grid", "#D9E5EA"),
        "neutral": color("neutral", "#13293D"),
        "light": color("light", "#EEF4F7"),
        "primary": color("primary", "#245A6B"),
        "secondary": color("secondary", "#8B3A3A"),
        "contrast": color("contrast", "#2166AC"),
        "primary_soft": color("primary_soft", "#DCEBF0"),
        "secondary_soft": color("secondary_soft", "#F1DADA"),
        "contrast_soft": color("contrast_soft", "#DCE8F4"),
        "neutral_soft": color("light", "#EEF4F7"),
        "paper": "#FBFDFE",
        "ink_soft": "#EFF5F7",
    }


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


def _append_flow_backbone(parts: list[str], *, width: int, height: int, colors: dict[str, str]) -> None:
    band = {"x0": width * 0.070, "y0": height * 0.355, "w": width * 0.860, "h": height * 0.235}
    parts.append(
        f'<rect x="{band["x0"]:.2f}" y="{band["y0"]:.2f}" width="{band["w"]:.2f}" height="{band["h"]:.2f}" '
        f'rx="{band["h"] / 2.0:.2f}" fill="{escape(colors["ink_soft"])}" stroke="none"/>\n'
    )
    parts.append(
        f'<line x1="{width * 0.120:.2f}" y1="{height * 0.475:.2f}" x2="{width * 0.880:.2f}" y2="{height * 0.475:.2f}" '
        f'stroke="{escape(colors["grid"])}" stroke-width="8" stroke-linecap="round"/>\n'
    )


def _append_process_panel(
    parts: list[str],
    layout_boxes: list[dict[str, Any]],
    *,
    panel: dict[str, Any],
    panel_box: dict[str, float],
    panel_id: str,
    index: int,
    accent: str,
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
    glyph_box = relative_box(panel_box, 0.230, 0.115, 0.770, 0.445)
    append_rect(parts, glyph_box, fill=_role_soft_color(panel.get("visual_role") or panel.get("panel_id"), index=index, colors=colors), stroke=accent, stroke_width=2.5, radius=24)
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
    parts.append(
        f'<circle cx="{cue_box["x0"] + cue_box["h"] * 0.50:.2f}" cy="{cue_box["y0"] + cue_box["h"] * 0.50:.2f}" '
        f'r="{cue_box["h"] * 0.20:.2f}" fill="{escape(accent)}"/>\n'
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


def _append_quality_band(
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


def _append_glyph(
    parts: list[str],
    box: dict[str, float],
    *,
    role: str,
    accent: str,
    colors: dict[str, str],
) -> None:
    role_text = str(role or "").strip().lower()
    x0 = box["x0"]
    y0 = box["y0"]
    w = box["w"]
    h = box["h"]
    if role_text in {"brief", "claim_evidence"}:
        for offset, label in ((0.20, "Claim"), (0.43, "Evidence"), (0.66, "Refs")):
            node = {"x0": x0 + w * 0.23, "y0": y0 + h * offset, "w": w * 0.54, "h": h * 0.135}
            append_rect(parts, node, fill="#FFFFFF", stroke=accent, stroke_width=2.2, radius=10)
            parts.append(
                f'<text x="{x0 + w * 0.50:.2f}" y="{node["y0"] + node["h"] * 0.67:.2f}" '
                f'font-family="Arial, Helvetica, sans-serif" font-size="{h * 0.060:.2f}" '
                f'font-weight="700" fill="{escape(accent)}" text-anchor="middle">{label}</text>\n'
            )
        parts.append(
            f'<path d="M{x0 + w * 0.50:.2f},{y0 + h * 0.335:.2f} L{x0 + w * 0.50:.2f},{y0 + h * 0.425:.2f} '
            f'M{x0 + w * 0.50:.2f},{y0 + h * 0.565:.2f} L{x0 + w * 0.50:.2f},{y0 + h * 0.655:.2f}" '
            f'stroke="{escape(accent)}" stroke-width="3" stroke-linecap="round"/>\n'
        )
    elif role_text in {"reference_style", "style_brief"}:
        for cx, cy in ((0.33, 0.31), (0.57, 0.23), (0.50, 0.55)):
            card = {"x0": x0 + w * cx - w * 0.145, "y0": y0 + h * cy - h * 0.105, "w": w * 0.290, "h": h * 0.210}
            append_rect(parts, card, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=8)
            parts.append(
                f'<line x1="{card["x0"] + card["w"] * 0.20:.2f}" y1="{card["y0"] + card["h"] * 0.38:.2f}" '
                f'x2="{card["x0"] + card["w"] * 0.82:.2f}" y2="{card["y0"] + card["h"] * 0.38:.2f}" '
                f'stroke="{escape(accent)}" stroke-width="3.5" stroke-linecap="round"/>\n'
            )
            parts.append(
                f'<line x1="{card["x0"] + card["w"] * 0.20:.2f}" y1="{card["y0"] + card["h"] * 0.64:.2f}" '
                f'x2="{card["x0"] + card["w"] * 0.70:.2f}" y2="{card["y0"] + card["h"] * 0.64:.2f}" '
                f'stroke="{escape(accent)}" stroke-width="3.5" stroke-linecap="round"/>\n'
            )
        parts.append(
            f'<path d="M{x0 + w * 0.26:.2f},{y0 + h * 0.80:.2f} C{x0 + w * 0.39:.2f},{y0 + h * 0.70:.2f} '
            f'{x0 + w * 0.61:.2f},{y0 + h * 0.70:.2f} {x0 + w * 0.74:.2f},{y0 + h * 0.80:.2f}" '
            f'fill="none" stroke="{escape(accent)}" stroke-width="5" stroke-linecap="round"/>\n'
        )
    elif role_text in {"critic_gate", "owner_gate"}:
        center = {"x0": x0 + w * 0.28, "y0": y0 + h * 0.18, "w": w * 0.44, "h": h * 0.145}
        append_rect(parts, center, fill="#FFFFFF", stroke=accent, stroke_width=2.2, radius=10)
        parts.append(
            f'<text x="{x0 + w * 0.50:.2f}" y="{center["y0"] + center["h"] * 0.68:.2f}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{h * 0.065:.2f}" '
            f'font-weight="700" fill="{escape(accent)}" text-anchor="middle">Critic</text>\n'
        )
        for cx, label in ((0.33, "Pass"), (0.67, "Revise")):
            target = {"x0": x0 + w * cx - w * 0.125, "y0": y0 + h * 0.585, "w": w * 0.250, "h": h * 0.135}
            append_rect(parts, target, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=9)
            parts.append(
                f'<text x="{x0 + w * cx:.2f}" y="{target["y0"] + target["h"] * 0.65:.2f}" '
                f'font-family="Arial, Helvetica, sans-serif" font-size="{h * 0.048:.2f}" '
                f'font-weight="700" fill="{escape(accent)}" text-anchor="middle">{label}</text>\n'
            )
    elif role_text in {"population", "source_data", "cohort"}:
        for cx, cy in ((0.30, 0.38), (0.46, 0.31), (0.62, 0.38), (0.38, 0.58), (0.56, 0.60)):
            parts.append(f'<circle cx="{x0 + w * cx:.2f}" cy="{y0 + h * cy:.2f}" r="{h * 0.050:.2f}" fill="{escape(accent)}"/>\n')
            parts.append(
                f'<line x1="{x0 + w * cx:.2f}" y1="{y0 + h * (cy + 0.065):.2f}" '
                f'x2="{x0 + w * cx:.2f}" y2="{y0 + h * (cy + 0.180):.2f}" '
                f'stroke="{escape(accent)}" stroke-width="4" stroke-linecap="round"/>\n'
            )
    elif role_text in {"model_signal", "model", "algorithm", "mechanism"}:
        parts.append(
            f'<polyline points="{x0 + w * 0.18:.2f},{y0 + h * 0.68:.2f} {x0 + w * 0.40:.2f},{y0 + h * 0.54:.2f} '
            f'{x0 + w * 0.60:.2f},{y0 + h * 0.38:.2f} {x0 + w * 0.82:.2f},{y0 + h * 0.25:.2f}" '
            f'fill="none" stroke="{escape(accent)}" stroke-width="5" stroke-linecap="round"/>\n'
        )
        for cx, label in ((0.25, "X"), (0.50, "f"), (0.75, "Y")):
            node = {"x0": x0 + w * cx - w * 0.055, "y0": y0 + h * 0.66, "w": w * 0.110, "h": h * 0.105}
            append_rect(parts, node, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=8)
            parts.append(
                f'<text x="{x0 + w * cx:.2f}" y="{node["y0"] + node["h"] * 0.68:.2f}" '
                f'font-family="Arial, Helvetica, sans-serif" font-size="{h * 0.055:.2f}" '
                f'font-weight="700" fill="{escape(accent)}" text-anchor="middle">{label}</text>\n'
            )
    else:
        center = {"x0": x0 + w * 0.32, "y0": y0 + h * 0.30, "w": w * 0.36, "h": h * 0.160}
        append_rect(parts, center, fill="#FFFFFF", stroke=accent, stroke_width=2, radius=10)
        parts.append(
            f'<text x="{x0 + w * 0.50:.2f}" y="{center["y0"] + center["h"] * 0.67:.2f}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{h * 0.060:.2f}" '
            f'font-weight="700" fill="{escape(accent)}" text-anchor="middle">Signal</text>\n'
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
                    "layout_style": str(shell_payload.get("layout_style") or "reference_guided_flow"),
                    "panel_count": len(panels),
                    "panels": panels,
                    "footer_pills": list(shell_payload.get("footer_pills") or []),
                    "visual_roles": [str(panel.get("visual_role") or "").strip() for panel in panels],
                    "source_renderer": "mas_reference_guided_svg_preview",
                    "canvas_size_px": [1800, 1000],
                },
                "render_context": render_context,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
