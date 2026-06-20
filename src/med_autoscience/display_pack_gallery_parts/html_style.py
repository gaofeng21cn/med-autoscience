from __future__ import annotations


GALLERY_CSS = """
:root{
  --ink:#222426;
  --muted:#5f6670;
  --soft:#f5f6f8;
  --line:#dfe3e8;
  --rule:#bfc6cf;
  --card:#ffffff;
  --accent:#1f5f8f;
  --accent-soft:#e8f1f7;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans CJK SC','Microsoft YaHei',Arial,sans-serif;
  color:var(--ink);
  background:#ffffff;
  line-height:1.55;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.page{
  display:grid;
  grid-template-columns:248px minmax(0,1fr);
  gap:28px;
  max-width:1320px;
  margin:0 auto;
  padding:26px 30px 42px;
}
.nav{
  position:sticky;
  top:20px;
  align-self:start;
  border-right:1px solid var(--line);
  padding:8px 18px 0 0;
}
.nav-title{font-size:13px;font-weight:700;margin:0 0 10px;color:#333}
.nav a{
  display:flex;
  justify-content:space-between;
  gap:12px;
  padding:8px 0;
  border-top:1px solid #edf0f3;
  color:#30343a;
  font-size:13px;
}
.nav a:first-of-type{border-top:0}
.nav strong{color:var(--muted);font-weight:600}
.hero{
  padding:22px 0 24px;
  border-bottom:2px solid var(--ink);
  margin-bottom:24px;
}
.eyebrow{
  color:var(--accent);
  font-size:12px;
  font-weight:700;
  letter-spacing:.08em;
  text-transform:uppercase;
  margin-bottom:8px;
}
h1{
  margin:0 0 10px;
  font-size:34px;
  line-height:1.15;
  letter-spacing:0;
  font-weight:760;
}
.subtitle{
  max-width:880px;
  font-size:16px;
  color:#33383d;
  margin:0 0 10px;
}
.scope{
  max-width:980px;
  font-size:13px;
  color:var(--muted);
  margin:0;
}
.metrics{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:10px;
  margin-top:18px;
}
.metric{
  border-top:1px solid var(--rule);
  padding-top:8px;
}
.metric strong{display:block;font-size:24px;line-height:1.1}
.metric span{display:block;font-size:12px;color:var(--muted);margin-top:3px}
.section{margin:0 0 34px}
.section-label{
  font-size:12px;
  font-weight:700;
  color:var(--accent);
  margin:0 0 5px;
}
.section h2{
  margin:0 0 8px;
  font-size:23px;
  line-height:1.25;
}
.section h2 span{font-size:13px;color:var(--muted);font-weight:500}
.section-lead{
  max-width:920px;
  color:var(--muted);
  font-size:14px;
  margin:0 0 16px;
}
.workflow{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px;
}
.workflow-card{
  border-top:2px solid var(--ink);
  background:var(--soft);
  padding:12px;
  min-height:126px;
}
.workflow-card .step{font-size:12px;font-weight:700;color:var(--accent);margin-bottom:7px}
.workflow-card h3{margin:0 0 6px;font-size:15px}
.workflow-card p{margin:0;font-size:12px;color:var(--muted)}
.composition-cards{display:grid;grid-template-columns:1fr;gap:22px}
.composition-card{
  break-inside:avoid;
  page-break-inside:avoid;
  border-top:2px solid var(--ink);
  padding-top:12px;
}
.composition-kicker{
  color:var(--accent);
  font-size:12px;
  font-weight:700;
  margin-bottom:4px;
}
.composition-card h3{margin:0 0 9px;font-size:22px;line-height:1.25}
.composition-summary{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
  margin-bottom:12px;
}
.composition-summary p{
  margin:0;
  font-size:13px;
  color:#3a3f45;
}
.storyboard{
  display:grid;
  grid-template-columns:1.35fr 1fr 1fr 1fr;
  gap:8px;
  margin:10px 0 13px;
}
.story-panel{
  position:relative;
  border:1px solid var(--line);
  background:#fff;
  min-width:0;
  overflow:hidden;
}
.story-panel.hero{grid-row:span 2}
.panel-letter{
  position:absolute;
  top:7px;
  left:7px;
  width:22px;
  height:22px;
  border-radius:50%;
  background:rgba(34,36,38,.9);
  color:#fff;
  font-size:12px;
  font-weight:700;
  display:flex;
  align-items:center;
  justify-content:center;
  z-index:1;
}
.story-image{
  background:linear-gradient(180deg,#fbfcfd,#f4f6f8);
  height:136px;
  display:flex;
  align-items:center;
  justify-content:center;
  border-bottom:1px solid #edf0f3;
}
.story-panel.hero .story-image{height:283px}
.story-placeholder{
  width:78%;
  min-height:58%;
  border:1px solid #c9d0d8;
  border-top:3px solid var(--accent);
  background:#fff;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:12px;
  text-align:center;
  color:#31363b;
  font-weight:700;
  font-size:13px;
  line-height:1.25;
}
.story-meta{padding:7px 8px;font-size:11px;color:var(--muted)}
.story-meta strong{
  display:block;
  color:#30343a;
  font-size:12px;
  line-height:1.25;
  margin-bottom:3px;
}
.story-meta span{display:block;overflow-wrap:anywhere}
.composition-bottom{
  display:grid;
  grid-template-columns:1.4fr 1fr;
  gap:18px;
  border-top:1px solid var(--line);
  padding-top:11px;
}
.composition-bottom h4{margin:0 0 6px;font-size:13px}
.composition-bottom ol{margin:0;padding-left:19px;color:#3a3f45;font-size:12px}
.composition-bottom p{margin:0 0 6px;font-size:12px;color:#3a3f45}
.fine-print{color:var(--muted)!important}
.category-block{margin-bottom:28px}
.category-head{
  display:flex;
  justify-content:space-between;
  gap:16px;
  align-items:flex-end;
  border-bottom:1px solid var(--ink);
  padding-bottom:7px;
  margin-bottom:12px;
}
.category-head h3{margin:0;font-size:20px}
.category-head p{margin:4px 0 0;color:var(--muted);font-size:13px;max-width:820px}
.category-count{font-size:13px;color:var(--muted);white-space:nowrap}
.cards{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:14px;
}
.card{
  border:1px solid var(--line);
  background:var(--card);
  break-inside:avoid;
  page-break-inside:avoid;
}
.figure-pane{background:#fff;border-bottom:1px solid var(--line)}
.pane-label{
  display:flex;
  justify-content:space-between;
  gap:8px;
  padding:7px 9px;
  font-size:11px;
  color:#4b535c;
  background:#f7f8fa;
  border-bottom:1px solid #edf0f3;
}
.image-link{display:block;background:#fff}
.image-link img{
  display:block;
  width:100%;
  aspect-ratio:1/1;
  object-fit:contain;
  background:#fff;
}
.asset-links{
  padding:6px 9px;
  font-size:10px;
  color:var(--muted);
  border-top:1px solid #edf0f3;
}
.placeholder{
  height:240px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:7px;
  padding:18px;
  text-align:center;
  color:var(--muted);
}
.placeholder strong{color:#333}
.placeholder span,.placeholder em{font-size:12px}
.card-body{padding:10px 11px 12px}
.card h4{margin:0 0 7px;font-size:15px;line-height:1.28}
.card p{margin:6px 0;font-size:12px;color:#4a5057}
.callout{
  margin-top:8px;
  padding-top:7px;
  border-top:1px solid #edf0f3;
  font-size:11px;
  color:var(--muted);
}
.template-id{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.palette-row{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:14px;
}
.swatch{
  display:inline-flex;
  align-items:center;
  gap:7px;
  border:1px solid var(--line);
  background:#fff;
  padding:5px 8px;
  font-size:11px;
  color:#4a5057;
}
.box{width:18px;height:14px;border:1px solid rgba(0,0,0,.12)}
@media(max-width:980px){
  .page{display:block;padding:18px}
  .nav{position:static;border-right:0;border-bottom:1px solid var(--line);padding:0 0 12px;margin-bottom:18px}
  .metrics,.workflow,.composition-summary,.composition-bottom,.cards{grid-template-columns:1fr}
  .storyboard{grid-template-columns:1fr 1fr}
  .story-panel.hero{grid-column:1/-1}
}
@media print{
  @page{size:A4;margin:10mm}
  body{background:#fff}
  .page{display:block;max-width:none;padding:0}
  .nav{display:none}
  .hero{padding-top:0;margin-bottom:16px}
  h1{font-size:28px}
  .subtitle{font-size:13px}
  .scope{font-size:10px}
  .metrics{grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}
  .metric strong{font-size:18px}
  .metric span{font-size:9px}
  .section{margin-bottom:20px}
  #evidence-primitives{break-before:page;page-break-before:always}
  .section h2{font-size:18px}
  .section-lead{font-size:10px;margin-bottom:10px}
  .workflow{grid-template-columns:repeat(4,1fr);gap:7px}
  .workflow-card{padding:7px;min-height:82px}
  .workflow-card h3{font-size:10px;margin-bottom:3px}
  .workflow-card p,.workflow-card .step{font-size:8px}
  .composition-card{padding-top:8px;margin-bottom:16px}
  .composition-card h3{font-size:17px;margin-bottom:6px}
  .composition-kicker{font-size:9px}
  .composition-summary{grid-template-columns:1fr 1fr;gap:8px;margin-bottom:7px}
  .composition-summary p{font-size:9px}
  .storyboard{grid-template-columns:repeat(4,1fr);gap:5px;margin:6px 0 8px}
  .story-panel.hero{grid-row:auto}
  .story-panel{break-inside:avoid;page-break-inside:avoid}
  .story-image{height:98px}
  .story-panel.hero .story-image{height:98px}
  .story-placeholder{width:82%;min-height:58%;font-size:8px;padding:6px;border-top-width:2px}
  .panel-letter{top:4px;left:4px;width:16px;height:16px;font-size:9px}
  .story-meta{padding:4px;font-size:7px}
  .story-meta strong{font-size:8px}
  .composition-bottom{grid-template-columns:1.35fr 1fr;gap:10px;padding-top:7px}
  .composition-bottom h4{font-size:9px;margin-bottom:3px}
  .composition-bottom ol,.composition-bottom p{font-size:8px}
  .category-block{margin-bottom:14px}
  .category-head{padding-bottom:5px;margin-bottom:8px}
  .category-head{break-after:avoid;page-break-after:avoid}
  .category-head h3{font-size:15px}
  .category-head p,.category-count{font-size:9px}
  .cards{grid-template-columns:repeat(2,1fr);gap:8px}
  .pane-label{font-size:8px;padding:4px 6px}
  .asset-links{display:none}
  .card-body{padding:7px}
  .card h4{font-size:10px;margin-bottom:4px}
  .card p{font-size:8px;margin:3px 0}
  .callout{font-size:7px;margin-top:5px;padding-top:4px}
  .palette-row{display:none}
}
"""
