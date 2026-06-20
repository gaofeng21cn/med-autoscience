from __future__ import annotations

import html
from typing import Any

from med_autoscience.display_pack_gallery_parts.gallery_copy import composition_copy


def _ordered_list(values: tuple[str, ...]) -> str:
    return "".join(f"<li>{html.escape(value)}</li>" for value in values)


def _panel_html(panel: dict[str, Any], *, index: int) -> str:
    template_id = str(panel.get("template_id") or "")
    kind = str(panel.get("panel_kind") or "")
    family_id = str(panel.get("evidence_primitive_family_id") or "")
    title = str(panel.get("canonical_family_title") or family_id or "storyboard placeholder")
    label = chr(ord("A") + index)
    return f"""
<div class="story-panel {html.escape(kind)}">
  <div class="panel-letter">{html.escape(label)}</div>
  <div class="story-image">
    <div class="story-placeholder">
      <span>{html.escape(title)}</span>
    </div>
  </div>
  <div class="story-meta">
    <span>证据图起点：{html.escape(template_id or family_id)}</span>
  </div>
</div>"""


def render_composition_gallery_html(
    composition_gallery: dict[str, Any],
    rendered: dict[str, object],
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
            _panel_html(panel, index=index)
            for index, panel in enumerate(panels)
            if isinstance(panel, dict)
        ) if isinstance(panels, list) else ""
        recipe_id = str(item.get("recipe_id", ""))
        copy = composition_copy(recipe_id, str(item.get("title", "")))
        cards.append(
            f"""
<article class="composition-card" id="composition-{html.escape(recipe_id)}">
  <div class="composition-kicker">页面级图页方案</div>
  <h3>{html.escape(copy.title)}</h3>
  <div class="composition-summary">
    <p><strong>适用场景：</strong>{html.escape(copy.use_case)}</p>
    <p><strong>核心表达：</strong>{html.escape(copy.central_message)}</p>
  </div>
  <div class="storyboard">{panel_html}</div>
  <div class="composition-bottom">
    <div>
      <h4>推荐面板组织</h4>
      <ol>{_ordered_list(copy.panel_plan)}</ol>
    </div>
    <div>
      <h4>证据边界</h4>
      <p>{html.escape(copy.evidence_note)}</p>
      <p class="fine-print">本页为图页组织示例，使用合成数据或示意性面板，不代表真实论文数据结果。</p>
    </div>
  </div>
</article>"""
        )
    return f"""
<section class="section composition-section" id="composition-recipes">
  <div class="section-label">第一部分</div>
  <h2>页面级图页方案 <span>{len(cards)} 类</span></h2>
  <p class="section-lead">页面级方案用于组织一张医学论文主图或关键扩展图。它定义论点、主面板、辅助证据和风格边界，不替代真实数据分析。</p>
  <div class="composition-cards">{''.join(cards)}
  </div>
</section>"""
