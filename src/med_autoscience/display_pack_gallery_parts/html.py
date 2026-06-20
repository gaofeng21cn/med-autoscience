from __future__ import annotations

import html

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_gallery_catalog import (
    TemplateRecord,
    design_gallery_records,
    family_categories,
    gallery_display_records,
    reporting_flow_gallery_records,
)
from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset
from med_autoscience.display_pack_gallery_parts.composition_gallery import (
    build_composition_gallery_surface,
)
from med_autoscience.display_pack_gallery_parts.composition_html import (
    render_composition_gallery_html,
)
from med_autoscience.display_pack_gallery_parts.gallery_copy import (
    GALLERY_SCOPE,
    GALLERY_SUBTITLE,
    GALLERY_TITLE,
    GALLERY_WORKFLOW_STEPS,
    design_copy,
    evidence_category_copy,
    evidence_copy,
)
from med_autoscience.display_pack_gallery_parts.html_style import GALLERY_CSS
from med_autoscience.display_pack_gallery_parts.taxonomy import CATEGORY_ORDER
from med_autoscience.display_pack_agent_parts.composition_recipe_projection import (
    composition_recipe_discovery_payload,
)


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


def _workflow_html() -> str:
    cards = []
    for step, title, body in GALLERY_WORKFLOW_STEPS:
        cards.append(
            f"""
<div class="workflow-card">
  <div class="step">步骤 {html.escape(step)}</div>
  <h3>{html.escape(title)}</h3>
  <p>{html.escape(body)}</p>
</div>"""
        )
    return f"""
<section class="section" id="how-to-read">
  <div class="section-label">读法</div>
  <h2>从论文论点到可审计图件</h2>
  <p class="section-lead">MAS 的模板库不是限制 AI 创作的硬模板，而是提供结构清晰、风格统一、统计含义可追踪的起点。AI 可以在保留科学语义和数据引用的前提下继续重排、改写和打磨。</p>
  <div class="workflow">{''.join(cards)}</div>
</section>"""


def _metrics_html(
    *,
    visible_count: int,
    reporting_flow_count: int,
    design_count: int,
    composition_count: int,
    rendered_count: int,
    style_profile_id: str,
) -> str:
    metrics = (
        (str(composition_count), "页面级图页方案"),
        (str(reporting_flow_count), "数据驱动报告流程图"),
        (str(design_count), "非数据设计图起点"),
        (str(visible_count), "R/ggplot2 证据图起点"),
    )
    return "".join(
        f'<div class="metric"><strong>{html.escape(value)}</strong><span>{html.escape(label)}</span></div>'
        for value, label in metrics
    )


def _palette_html(palette: dict[str, str]) -> str:
    labels = (
        ("primary", "主色"),
        ("secondary", "辅助色"),
        ("tertiary", "强调色"),
        ("quaternary", "对比色"),
        ("neutral", "中性色"),
        ("heatmap_seq_high", "连续热图高值"),
        ("heatmap_high", "发散热图高值"),
    )
    return "".join(
        (
            f'<span class="swatch"><span class="box" style="background:{html.escape(palette[key])}"></span>'
            f'{html.escape(label)}</span>'
        )
        for key, label in labels
        if key in palette
    )


def _non_evidence_gallery_html(
    *,
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    section_id: str,
    section_label: str,
    title: str,
    lead: str,
    pane_label: str,
    card_class: str,
) -> str:
    if not records:
        return ""
    cards: list[str] = []
    for record in records:
        asset = rendered[record.template_id]
        copy = design_copy(record)
        panes = _asset_html(asset, label=pane_label)
        if asset.status != "rendered":
            panes = f'<div class="placeholder"><strong>{html.escape(record.display_name)}</strong><span>{html.escape(record.kind)} · {html.escape(record.renderer_family)}</span><em>{html.escape(asset.reason or "no renderer output")}</em></div>'
        cards.append(
            f"""
<article class="card {html.escape(card_class)}" id="template-{html.escape(record.template_id)}">
  {panes}
  <div class="card-body">
    <h4>{html.escape(record.display_name)}</h4>
    <p><strong>表达目的：</strong>{html.escape(copy.purpose)}</p>
    <p><strong>输入要求：</strong>{html.escape(copy.input_requirement)}</p>
    <p><strong>适用场景：</strong>{html.escape(copy.use_when)}</p>
    <p><strong>证据边界：</strong>{html.escape(copy.evidence_boundary)}</p>
    <div class="callout">调用入口：<span class="template-id">{html.escape(record.template_id)}</span></div>
  </div>
</article>"""
        )
    return f"""
<section class="section" id="{html.escape(section_id)}">
  <div class="section-label">{html.escape(section_label)}</div>
  <h2>{html.escape(title)} <span>{len(records)} 个</span></h2>
  <p class="section-lead">{html.escape(lead)}</p>
  <div class="cards design-cards">{''.join(cards)}
  </div>
</section>"""


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
    visible_records = gallery_display_records(records)
    reporting_flow_records = reporting_flow_gallery_records(records)
    design_records = design_gallery_records(records)
    composition_surface = composition_recipe_discovery_payload(include_recipes=True)
    composition_gallery = build_composition_gallery_surface(composition_surface, records)
    rendered_count = sum(
        1
        for record in [*visible_records, *reporting_flow_records, *design_records]
        if rendered[record.template_id].status == "rendered"
    )
    nav = "\n".join(
        [
            (
                f'<a href="#how-to-read"><span>读法</span><strong>4</strong></a>'
                f'<a href="#composition-recipes"><span>图页方案</span>'
                f'<strong>{composition_gallery["composition_recipe_count"]}</strong></a>'
                f'<a href="#reporting-flows"><span>报告流程图</span><strong>{len(reporting_flow_records)}</strong></a>'
                f'<a href="#design-shells"><span>设计图</span><strong>{len(design_records)}</strong></a>'
            )
        ]
        + [
            f'<a href="#family-{_html_id(category)}"><span>{html.escape(evidence_category_copy(category)[0])}</span><strong>{len(categories[category])}</strong></a>'
            for category in ordered_categories
        ]
    )
    sections: list[str] = []
    for category in ordered_categories:
        cards: list[str] = []
        for record in sorted(categories[category], key=lambda item: (item.kind, item.canonical_family_id)):
            asset = rendered[record.template_id]
            copy = evidence_copy(record)
            panes = _asset_html(asset, label="R/ggplot2 数据证据图")
            if asset.status != "rendered":
                panes = f'<div class="placeholder"><strong>{html.escape(record.display_name)}</strong><span>{html.escape(record.kind)} · {html.escape(record.renderer_family)}</span><em>{html.escape(asset.reason or "no renderer output")}</em></div>'
            cards.append(
                f"""
<article class="card" id="template-{html.escape(record.template_id)}">
  {panes}
  <div class="card-body">
    <h4>{html.escape(record.display_name)}</h4>
    <p><strong>表达目的：</strong>{html.escape(copy.purpose)}</p>
    <p><strong>数据要求：</strong>{html.escape(copy.data_requirement)}</p>
    <p><strong>适用场景：</strong>{html.escape(copy.use_when)}</p>
    <div class="callout">调用入口：<span class="template-id">{html.escape(record.template_id)}</span></div>
  </div>
</article>"""
            )
        category_title, category_lead = evidence_category_copy(category)
        sections.append(
            f"""
<section class="category-block" id="family-{_html_id(category)}">
  <div class="category-head">
    <div>
      <h3>{html.escape(category_title)}</h3>
      <p>{html.escape(category_lead)}</p>
    </div>
    <div class="category-count">{len(categories[category])} 个模板</div>
  </div>
  <div class="cards">{''.join(cards)}
  </div>
</section>"""
        )

    composition_section = render_composition_gallery_html(composition_gallery, rendered)
    reporting_flow_section = _non_evidence_gallery_html(
        records=reporting_flow_records,
        rendered=rendered,
        section_id="reporting-flows",
        section_label="第二部分",
        title="数据驱动报告流程图起点",
        lead=(
            "这些图件用于 cohort disposition、CONSORT/STROBE 式筛选流程、排除原因和分析集说明。"
            "它们必须由结构化人数、节点关系和来源引用驱动；renderer 负责稳定版式，不负责发明统计事实。"
        ),
        pane_label="数据驱动报告流程图",
        card_class="reporting-flow-card",
    )
    design_section = _non_evidence_gallery_html(
        records=design_records,
        rendered=rendered,
        section_id="design-shells",
        section_label="第三部分",
        title="非数据设计图起点",
        lead=(
            "这些图件用于 graphical abstract、机制说明和编辑部视觉摘要。"
            "它们允许 SVG、Python composition 或 imagegen-assisted art direction，以表达力和期刊风格为优先；"
            "真实结果数字必须来自已审计证据引用。"
        ),
        pane_label="非数据设计图",
        card_class="design-card",
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(GALLERY_TITLE)}</title>
<style>{GALLERY_CSS}</style>
</head>
<body>
<div class="page">
<nav class="nav"><div class="nav-title">目录</div>{nav}</nav>
<main>
  <section class="hero">
    <div class="eyebrow">MedAutoScience Display Pack</div>
    <h1>{html.escape(GALLERY_TITLE)}</h1>
    <p class="subtitle">{html.escape(GALLERY_SUBTITLE)}</p>
    <p class="scope">{html.escape(GALLERY_SCOPE)}</p>
    <div class="metrics">{_metrics_html(visible_count=len(visible_records), reporting_flow_count=len(reporting_flow_records), design_count=len(design_records), composition_count=composition_gallery["composition_recipe_count"], rendered_count=rendered_count, style_profile_id=str(default_style["style_profile_id"]))}</div>
    <div class="palette-row">{_palette_html(palette)}</div>
  </section>
  {_workflow_html()}
  {composition_section}
  {reporting_flow_section}
  {design_section}
  <section class="section" id="evidence-primitives">
    <div class="section-label">第四部分</div>
    <h2>R/ggplot2 数据证据图起点 <span>{len(visible_records)} 个</span></h2>
    <p class="section-lead">这些证据图起点是 MAS 默认数据证据图入口。它们按医学表达目的组织，强调输入数据、统计语义、统一风格和可审计导出；AI 可在论文级语义约束下继续调整图形结构。</p>
    {''.join(sections)}
  </section>
</main>
</div>
</body>
</html>
"""
