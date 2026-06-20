from __future__ import annotations

import html
from typing import Any

from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset


def _asset_image_ref(template_id: str, rendered: dict[str, RenderedAsset]) -> str:
    asset = rendered.get(template_id)
    if asset is None or asset.status != "rendered":
        return ""
    return asset.preview_image_ref or asset.image_ref


def _tag_list(values: list[str], *, limit: int = 5) -> str:
    shown = values[:limit]
    tags = "".join(f'<span class="tag">{html.escape(value)}</span>' for value in shown)
    if len(values) > limit:
        tags += f'<span class="tag">+{len(values) - limit}</span>'
    return tags


def _panel_html(panel: dict[str, Any], rendered: dict[str, RenderedAsset]) -> str:
    template_id = str(panel.get("template_id") or "")
    image_ref = _asset_image_ref(template_id, rendered)
    role = str(panel.get("panel_role") or "")
    kind = str(panel.get("panel_kind") or "")
    family_id = str(panel.get("evidence_primitive_family_id") or "")
    title = str(panel.get("canonical_family_title") or family_id or "storyboard placeholder")
    proxy = panel.get("uses_gallery_proxy") is True
    image = (
        f'<img src="{html.escape(image_ref)}" alt="{html.escape(title)}">'
        if image_ref
        else '<div class="panel-placeholder">storyboard<br>placeholder</div>'
    )
    proxy_label = '<span class="mini-note">proxy</span>' if proxy else ""
    return f"""
<div class="story-panel {html.escape(kind)}">
  <div class="story-image">{image}</div>
  <div class="story-meta">
    <strong>{html.escape(role)}</strong>
    <span>{html.escape(title)}{proxy_label}</span>
    <code>{html.escape(template_id or family_id)}</code>
  </div>
</div>"""


def render_composition_gallery_html(
    composition_gallery: dict[str, Any],
    rendered: dict[str, RenderedAsset],
) -> str:
    recipes = composition_gallery.get("recipes", [])
    if not isinstance(recipes, list) or not recipes:
        return ""
    cards: list[str] = []
    for item in recipes:
        if not isinstance(item, dict):
            continue
        panels = item.get("storyboard_panels")
        panel_html = "".join(
            _panel_html(panel, rendered)
            for panel in panels
            if isinstance(panel, dict)
        ) if isinstance(panels, list) else ""
        supporting = _tag_list([str(value) for value in item.get("supporting_panel_roles", [])])
        starters = _tag_list([str(value) for value in item.get("recommended_starter_recipe_ids", [])])
        palettes = _tag_list([str(value) for value in item.get("palette_tokens", [])], limit=4)
        cards.append(
            f"""
<article class="composition-card" id="composition-{html.escape(str(item.get('recipe_id', '')))}">
  <div class="composition-head">
    <h3>{html.escape(str(item.get('title', '')))}</h3>
    <code>{html.escape(str(item.get('recipe_id', '')))}</code>
  </div>
  <p>{html.escape(str(item.get('intent', '')))}</p>
  <div class="storyboard">{panel_html}</div>
  <div class="composition-grid">
    <div><strong>Layout</strong><span>{html.escape(str(item.get('default_layout', '')))}</span></div>
    <div><strong>Hero</strong><span>{html.escape(str(item.get('hero_panel_role', '')))}</span></div>
    <div><strong>Supporting</strong><div class="tags">{supporting}</div></div>
    <div><strong>Starter recipes</strong><div class="tags">{starters}</div></div>
    <div><strong>Guide strategy</strong><span>{html.escape(str(item.get('guide_strategy', '')))}</span></div>
    <div><strong>Label strategy</strong><span>{html.escape(str(item.get('label_strategy', '')))}</span></div>
    <div><strong>Palette tokens</strong><div class="tags">{palettes}</div></div>
    <div><strong>Boundary</strong><span>mock storyboard; not real data; not publication-ready</span></div>
  </div>
</article>"""
        )
    return f"""
<section class="section composition-section" id="composition-recipes">
  <h2>Composition Recipe Gallery <span>{len(cards)}</span></h2>
  <div class="composition-intro">
    页面级 recipe 展示如何把多个 evidence primitives 组织成论文图页。这里是可视 storyboard，不是真实论文数据、不签 publication-ready。
  </div>
  <div class="composition-cards">{''.join(cards)}
  </div>
</section>"""
