from __future__ import annotations

import html

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_gallery_catalog import (
    TemplateRecord,
    canonical_family_wording,
    family_categories,
    visual_gallery_records,
)
from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset
from med_autoscience.display_pack_gallery_parts.taxonomy import CATEGORY_ORDER

def _html_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-")


def _asset_html(asset: RenderedAsset, *, label: str) -> str:
    if asset.status != "rendered":
        return ""
    display_image_ref = asset.preview_image_ref or asset.image_ref
    links = [f'<a href="{html.escape(asset.payload_ref)}">payload</a>', f'<a href="{html.escape(asset.layout_ref)}">layout</a>']
    if asset.preview_image_ref and asset.preview_image_ref != asset.image_ref:
        links.append(f'<a href="{html.escape(asset.image_ref)}">raw PNG</a>')
    if asset.pdf_ref:
        links.append(f'<a href="{html.escape(asset.pdf_ref)}">PDF</a>')
    if asset.svg_ref:
        links.append(f'<a href="{html.escape(asset.svg_ref)}">SVG</a>')
    return f"""
<div class="figure-pane">
  <div class="pane-label">{html.escape(label)}</div>
  <a class="image-link" href="{html.escape(display_image_ref)}">
    <img src="{html.escape(display_image_ref)}" alt="{html.escape(label)}">
  </a>
  <div class="asset-links">{' · '.join(links)}</div>
</div>"""


def _render_html(
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
) -> str:
    categories = family_categories(records)
    ordered_categories = [item for item in CATEGORY_ORDER if item in categories]
    ordered_categories.extend(sorted(set(categories) - set(ordered_categories)))

    default_style = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD
    palette = default_style["palette"]
    visible_records = visual_gallery_records(records)
    rendered_count = sum(1 for record in visible_records if rendered[record.template_id].status == "rendered")
    r_evidence_count = sum(
        1
        for record in visible_records
        if record.kind == "evidence_figure" and record.renderer_family == "r_ggplot2"
    )
    python_evidence_count = sum(
        1
        for record in visible_records
        if record.kind == "evidence_figure" and record.renderer_family == "python"
    )
    illustration_count = sum(1 for record in visible_records if record.kind == "illustration_shell")
    baseline_count = sum(
        1
        for record in visible_records
        if baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")).status == "rendered"
    )
    meta = (
        f'<span class="pill">style_profile_id: {html.escape(default_style["style_profile_id"])}</span>'
        f'<span class="pill">journal_palette_ref: {html.escape(default_style["journal_palette_ref"])}</span>'
        f'<span class="pill">gallery cards: {len(visible_records)}</span>'
        f'<span class="pill">family policy: R-first evidence + design shells</span>'
        f'<span class="pill">R/ggplot2 evidence: {r_evidence_count}</span>'
        f'<span class="pill">Python evidence: {python_evidence_count}</span>'
        f'<span class="pill">Python design shells: {illustration_count}</span>'
        f'<span class="pill">rendered images: {rendered_count}</span>'
        f'<span class="pill">Python comparisons: {baseline_count}</span>'
    )
    swatches = "".join(
        (
            f'<span class="swatch"><span class="box" style="background:{html.escape(palette[key])}"></span>'
            f'<code>{html.escape(key)}</code></span>'
        )
        for key in ("primary", "secondary", "tertiary", "quaternary", "violet", "neutral", "heatmap_seq_high", "heatmap_high")
        if key in palette
    )
    nav = "\n".join(
        f'<a href="#family-{_html_id(category)}"><span>{html.escape(category)}</span><strong>{len(categories[category])}</strong></a>'
        for category in ordered_categories
    )
    sections: list[str] = []
    for category in ordered_categories:
        cards: list[str] = []
        for record in sorted(categories[category], key=lambda item: (item.kind, item.canonical_family_id)):
            asset = rendered[record.template_id]
            baseline = baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable"))
            tags = "".join(
                f'<span class="tag">{html.escape(tag)}</span>'
                for tag in (
                    record.canonical_family_id,
                    record.kind,
                    record.renderer_family,
                    "canonical",
                )
            )
            family_wording = canonical_family_wording(record)
            if record.kind == "illustration_shell":
                pane_label = "Python / SVG composition shell"
            else:
                pane_label = "R / ggplot2 evidence" if record.renderer_family == "r_ggplot2" else "Python evidence"
            panes = _asset_html(asset, label=pane_label)
            if baseline.status == "rendered":
                panes += _asset_html(baseline, label="Legacy Python baseline")
            if asset.status != "rendered":
                panes = f'<div class="placeholder"><strong>{html.escape(record.canonical_family_title)}</strong><span>{html.escape(record.kind)} · {html.escape(record.renderer_family)}</span><em>{html.escape(asset.reason or "no renderer output")}</em></div>'
            cards.append(
                f"""
<article class="card" id="template-{html.escape(record.template_id)}">
  <div class="panes{' compare' if baseline.status == 'rendered' else ''}">{panes}</div>
  <div class="card-body">
    <h3>{html.escape(record.canonical_family_title)}</h3>
    <p><code>{html.escape(record.template_id)}</code></p>
    <p>{html.escape(family_wording)}</p>
    <div class="tags">{tags}</div>
  </div>
</article>"""
            )
        sections.append(
            f"""
<section class="section" id="family-{_html_id(category)}">
  <h2>{html.escape(category)} <span>{len(categories[category])}</span></h2>
  <div class="cards">{''.join(cards)}
  </div>
</section>"""
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MAS Display Pack Canonical Gallery</title>
<style>
:root{{--ink:#272727;--muted:#666;--line:#e4e7eb;--bg:#f7f8fa;--card:#fff;}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.42}}
a{{color:#0f4d92;text-decoration:none}}a:hover{{text-decoration:underline}}
header{{padding:22px 30px 16px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}}
h1{{margin:0 0 8px;font-size:25px;letter-spacing:0}}
.sub{{max-width:1080px;color:var(--muted);font-size:14px}}
.meta,.palette{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.pill,.swatch{{border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 10px;font-size:12px;color:#333}}
.swatch{{display:inline-flex;align-items:center;gap:7px}}
.box{{width:16px;height:16px;border-radius:50%;border:1px solid rgba(0,0,0,.14)}}
.layout{{display:grid;grid-template-columns:260px minmax(0,1fr);gap:20px;padding:22px 28px 40px}}
.nav{{position:sticky;top:118px;align-self:start;background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px}}
.nav h2{{font-size:13px;margin:0 0 8px;color:#555}}
.nav a{{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid #eef1f4;font-size:13px;color:#333}}
.nav a:first-of-type{{border-top:0}}
.section{{margin:0 0 28px}}
.section h2{{margin:0 0 12px;font-size:21px}}.section h2 span{{font-size:13px;color:var(--muted);font-weight:500}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;break-inside:avoid}}
.panes{{display:grid;grid-template-columns:1fr;background:#fff;border-bottom:1px solid var(--line)}}
.panes.compare{{grid-template-columns:1fr 1fr}}
.figure-pane{{min-width:0;border-right:1px solid var(--line)}}
.figure-pane:last-child{{border-right:0}}
.pane-label{{font-size:11px;color:#555;padding:7px 9px;border-bottom:1px solid #eef1f4;background:#fbfcfd}}
.image-link{{display:block;background:#fff}}
.image-link img{{display:block;width:100%;aspect-ratio:1/1;object-fit:contain;background:#fff}}
.asset-links{{font-size:11px;color:#555;padding:7px 9px;border-top:1px solid #eef1f4}}
.placeholder{{height:260px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:18px;text-align:center;background:#fff;border-bottom:1px solid var(--line);color:#555}}
.placeholder strong{{color:#333}}.placeholder span,.placeholder em{{font-size:12px}}
.card-body{{padding:11px 12px}}
.card h3{{margin:0 0 5px;font-size:15px;line-height:1.28}}
.card p{{margin:5px 0;font-size:12px;color:#555}}
.tags{{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}}
.tag{{font-size:11px;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:#fbfcfd;color:#555}}
@media(max-width:900px){{header{{position:static}}.layout{{display:block;padding:16px}}.nav{{position:static;margin-bottom:18px}}.cards{{grid-template-columns:1fr}}.panes.compare{{grid-template-columns:1fr}}.figure-pane{{border-right:0;border-bottom:1px solid var(--line)}}}}
@media print{{@page{{size:A4;margin:10mm}}header{{position:static}}.layout{{display:block;padding:0}}.nav{{display:none}}.cards{{grid-template-columns:repeat(2,1fr);gap:10px}}body{{background:#fff}}.card{{break-inside:avoid}}}}
</style>
</head>
<body>
<header>
  <h1>MAS Display Pack Canonical Gallery</h1>
  <div class="sub">默认展示 R/ggplot2 数据证据图和设计/流程类 composition shell；Python evidence 模板保留为迁移库存或显式请求，不作为默认图卡。</div>
  <div class="meta">{meta}</div>
  <div class="palette">{swatches}</div>
</header>
<div class="layout">
<nav class="nav"><h2>索引</h2>{nav}</nav>
<main>{''.join(sections)}</main>
</div>
</body>
</html>
"""
