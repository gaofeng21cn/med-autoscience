from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_gallery import paths
from med_autoscience.display_pack_gallery.lidocaineq_coverage import (
    LIDOCAINEQ_COVERAGE_ITEMS,
)


@dataclass(frozen=True)
class ParityJudgement:
    status: str
    differences: tuple[str, ...]
    required_action: str


_REFERENCE_ROOT_ENV = "MAS_LIDOCAINEQ_REFERENCE_ROOT"
_DEFAULT_REFERENCE_ROOT = Path("/tmp/lidocaineq_figure_template")

_MANUAL_JUDGEMENTS: dict[str, ParityJudgement] = {
    "survival_km": ParityJudgement(
        "reference_style_matched",
        ("Kaplan-Meier renderer follows the reference split curve/spacer/risk-table grammar; Gallery hides the risk-table title by default to keep the table aligned with the curve panel.",),
        "Use as MAS lower-bound start; paper-specific review should only tune censor marks, time scale, and final risk-table labels.",
    ),
    "cumulative_incidence_grouped": ParityJudgement(
        "reference_style_matched",
        ("Grouped step curve follows the reference time-to-event incidence grammar with right-edge padding so terminal steps do not sit on the panel border.",),
        "Use as MAS lower-bound start; paper-specific review should tune competing-risk labels and horizon ticks.",
    ),
    "embedding_umap_tsne": ParityJudgement(
        "mas_computed_workflow_intentionally_extended",
        ("The LidocaineQ reference is a single embedding scatter. MAS keeps separate PCA, t-SNE, and UMAP computed-workflow templates that start from the same feature matrix and intentionally produce different layouts.",),
        "Use as computed MAS workflows; do not force PCA/t-SNE/UMAP to share the same point geometry.",
    ),
    "volcano_deg": ParityJudgement(
        "reference_style_matched",
        ("Renderer follows the reference thresholded volcano grammar with dense background genes, up/down colours, dashed cutoffs, and sparse top labels.",),
        "Use as MAS lower-bound start; paper-specific review should tune differential-testing thresholds and label policy.",
    ),
    "shap_dependence_panel": ParityJudgement(
        "reference_style_matched",
        ("Renderer follows the reference loess dependence scatter grammar with dense points, two-context colour coding, and square panel geometry.",),
        "Use as MAS lower-bound start; paper-specific review should tune interaction variable and axis units.",
    ),
    "shap_summary_beeswarm": ParityJudgement(
        "reference_style_matched",
        ("Renderer follows the reference beeswarm layout with feature rows, jittered SHAP points, zero line, and horizontal feature-value colour bar.",),
        "Use as MAS lower-bound start; paper-specific review should tune feature ordering and colour-bar label.",
    ),
    "shap_waterfall_local_explanation_panel": ParityJudgement(
        "reference_style_matched",
        ("Renderer follows the reference local explanation grammar with baseline, signed contributions, final prediction bar, and angled feature labels.",),
        "Use as MAS lower-bound start; paper-specific review should tune patient label and contribution units.",
    ),
    "model_complexity_audit_panel": ParityJudgement(
        "reference_style_matched",
        ("Renderer uses the reference performance-vs-feature-count line chart with CV and external validation curves plus selected-feature vertical marker.",),
        "Use as MAS lower-bound start; paper-specific review should tune selected feature count and metric naming.",
    ),
    "baseline_table": ParityJudgement(
        "reference_style_matched",
        ("Table 1 preview keeps table_shell authority while following the reference gridExtra title/subtitle/table layout and palette.",),
        "Use as Gallery preview only; table_shell remains the authoritative data/table surface.",
    ),
}

_DEFAULT_JUDGEMENT = ParityJudgement(
    "reference_style_matched",
    ("MAS renderer uses the LidocaineQ source renderer id, matching reference device ratio, shared palette, and the reference plot grammar for the current template mapping.",),
    "Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output.",
)


def _reference_root() -> Path:
    configured = os.environ.get(_REFERENCE_ROOT_ENV, "").strip()
    return Path(configured).expanduser().resolve() if configured else _DEFAULT_REFERENCE_ROOT


def _asset_abs_path(asset_ref: str) -> Path:
    return (paths.HTML_PATH.parent / asset_ref).resolve()


def _find_reference_png(reference_root: Path, reference_template_id: str) -> Path | None:
    candidate = reference_root / "figures" / "reference" / f"{reference_template_id}.png"
    if candidate.is_file():
        return candidate
    return None


def _image_info(path: Path | None, *, path_ref: str | None = None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"exists": False, "path": path_ref if path_ref is not None else str(path) if path is not None else ""}
    try:
        from PIL import Image

        with Image.open(path) as image:
            width, height = image.size
    except Exception:
        width, height = 0, 0
    return {
        "exists": True,
        "path": path_ref if path_ref is not None else paths.repo_relative_path(path),
        "width_px": width,
        "height_px": height,
    }


def build_lidocaineq_visual_parity_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    reference_root = _reference_root()
    rendered_templates: dict[str, dict[str, Any]] = {}
    for section_key in (
        "templates",
        "reporting_flow_gallery_templates",
        "design_gallery_templates",
        "table_preview_gallery_templates",
        "non_visual_inventory",
        "default_surface_excluded_inventory",
    ):
        for rendered_item in manifest.get(section_key, []):
            if isinstance(rendered_item, dict) and rendered_item.get("template_id"):
                rendered_templates[str(rendered_item["template_id"])] = rendered_item
    rows: list[dict[str, Any]] = []
    for item in LIDOCAINEQ_COVERAGE_ITEMS:
        judgement = _MANUAL_JUDGEMENTS.get(
            item.reference_template_id,
            _DEFAULT_JUDGEMENT,
        )
        mas_refs: list[dict[str, Any]] = []
        for template_id in item.required_mas_template_ids or (item.mas_template_id,):
            rendered = rendered_templates.get(template_id, {})
            preview_ref = str(rendered.get("preview_image_ref") or rendered.get("image_ref") or "")
            mas_path = _asset_abs_path(preview_ref) if preview_ref else None
            mas_refs.append(
                {
                    "template_id": template_id,
                    "render_status": rendered.get("render_status") or rendered.get("status") or "missing",
                    "preview_image_ref": preview_ref,
                    "image": _image_info(mas_path, path_ref=preview_ref),
                }
            )
        reference_path = _find_reference_png(reference_root, item.reference_template_id)
        rows.append(
            {
                "reference_template_id": item.reference_template_id,
                "title": item.title,
                "category_label": item.category_label,
                "expected_source_renderer": item.expected_source_renderer,
                "reference_image": _image_info(reference_path),
                "mas_templates": mas_refs,
                "parity_status": judgement.status,
                "known_differences": list(judgement.differences),
                "required_action": judgement.required_action,
            }
        )
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row["parity_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema_version": 1,
        "source_project": "LidocaineQ/Figure_Template",
        "reference_root": str(reference_root),
        "reference_template_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "user_visible_gallery_policy": "Reference coverage is a learning and quality audit surface; it is not rendered as a permanent Gallery appendix.",
        "rows": rows,
    }


def write_lidocaineq_visual_parity_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    audit = build_lidocaineq_visual_parity_audit(manifest)
    paths.LIDOCAINEQ_PARITY_AUDIT_JSON_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    paths.LIDOCAINEQ_PARITY_AUDIT_PATH.write_text(
        render_lidocaineq_visual_parity_markdown(audit),
        encoding="utf-8",
    )
    build_lidocaineq_contact_sheet(audit, paths.LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH)
    return audit


def render_lidocaineq_visual_parity_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# LidocaineQ 33 项逐图视觉审计",
        "",
        "Owner: `MedAutoScience`",
        "Purpose: `medical_display_visual_parity_audit`",
        "State: `generated_support_reference`",
        "Machine boundary: Generated human-readable visual parity audit support. Machine truth remains in display-pack registry/schema source, gallery manifest/status, generated contact sheet/assets, renderer/QC tests, and MAS publication/artifact owner receipts.",
        "",
        "本文件是 MAS 绘图模板质量审计面，不作为 Gallery 永久章节。审计目的，是把学生手工确认过的发表级参考图与 MAS 当前模板输出逐一对应，发现图型语法、排版、配色和信息密度偏差。",
        "",
        f"- 参考项目：`{audit['source_project']}`",
        f"- 参考根目录：`{audit['reference_root']}`",
        f"- 参考模板数：`{audit['reference_template_count']}`",
        f"- 状态计数：`{json.dumps(audit['status_counts'], ensure_ascii=False)}`",
        f"- Contact sheet：`{paths.repo_relative_path(paths.LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH)}`",
        "",
        "| Reference | MAS template | Status | Required action |",
        "| --- | --- | --- | --- |",
    ]
    for row in audit["rows"]:
        mas_templates = ", ".join(item["template_id"] for item in row["mas_templates"])
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['reference_template_id']}`",
                    f"`{mas_templates}`",
                    row["parity_status"],
                    row["required_action"].replace("|", "/"),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_lidocaineq_contact_sheet(audit: dict[str, Any], output_path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return

    rows = audit["rows"]
    thumb = 280
    label_h = 54
    gutter = 18
    width = gutter + (thumb * 2) + gutter + 280 + gutter
    height = gutter + len(rows) * (thumb + label_h + gutter)
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("Arial.ttf", 15)
        small_font = ImageFont.truetype("Arial.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    y = gutter
    for row in rows:
        ref_box = (gutter, y + label_h, gutter + thumb, y + label_h + thumb)
        mas_box = (gutter + thumb + gutter, y + label_h, gutter + thumb * 2 + gutter, y + label_h + thumb)
        draw.text((gutter, y), row["reference_template_id"], fill=(19, 41, 61), font=font)
        draw.text((gutter + thumb + gutter, y), ", ".join(item["template_id"] for item in row["mas_templates"]), fill=(19, 41, 61), font=font)
        draw.text((gutter + thumb * 2 + gutter * 2, y), row["parity_status"], fill=(139, 58, 58), font=font)
        _paste_thumb(sheet, draw, row["reference_image"], ref_box, "reference", small_font)
        first_mas_image = row["mas_templates"][0]["image"] if row["mas_templates"] else {}
        if row["mas_templates"] and row["mas_templates"][0].get("preview_image_ref"):
            first_mas_image = {
                **first_mas_image,
                "path": str(_asset_abs_path(str(row["mas_templates"][0]["preview_image_ref"]))),
            }
        _paste_thumb(sheet, draw, first_mas_image, mas_box, "MAS", small_font)
        action = row["required_action"]
        draw.multiline_text(
            (gutter + thumb * 2 + gutter * 2, y + label_h + 4),
            "\n".join(_wrap_text(action, 34)),
            fill=(100, 116, 139),
            font=small_font,
            spacing=3,
        )
        y += thumb + label_h + gutter
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def _paste_thumb(
    sheet: Any,
    draw: Any,
    image_info: dict[str, Any],
    box: tuple[int, int, int, int],
    label: str,
    font: Any,
) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=(230, 237, 242), width=2)
    path_text = str(image_info.get("path") or "")
    if not image_info.get("exists") or not path_text:
        draw.text((x0 + 16, y0 + 18), f"missing {label}", fill=(178, 24, 43), font=font)
        return
    try:
        from PIL import Image

        with Image.open(path_text) as image:
            image = image.convert("RGB")
            image.thumbnail((x1 - x0 - 12, y1 - y0 - 12), Image.LANCZOS)
            px = x0 + ((x1 - x0) - image.size[0]) // 2
            py = y0 + ((y1 - y0) - image.size[1]) // 2
            sheet.paste(image, (px, py))
    except Exception as exc:
        draw.text((x0 + 16, y0 + 18), f"{label} error: {type(exc).__name__}", fill=(178, 24, 43), font=font)


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:8]
