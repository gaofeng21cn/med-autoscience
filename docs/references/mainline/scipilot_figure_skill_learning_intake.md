# SciPilot Figure Skill Learning Intake

Owner: `MedAutoScience`
Purpose: `scipilot_figure_pattern_provenance`
State: `support_reference`
Machine boundary: 本页保留来源和视觉方法，不声明私有 advisor、lint 或 sidecar 已实现。

## 来源

历史检查的 `scipilot-figure-skill` snapshot 为
`43098ddb9e6a6d142218540c114f9ed38922fc42`，许可证 MIT；
当时临时 checkout 为 `/tmp/scipilot-figure-skill`，它不是长期资源 locator。

本轮检查了：

- `SKILL.md` 与 `README.md`：定位为 scientific data visualization advisor，强调先数据剖析、论证目标和图型选择，再绘图。
- `references/chart_selection.md`：用变量类型、论证意图和样本量三轴选择图型。
- `references/data_profiling.md`：把列类型、分组样本量、偏度、缺失、异常和相关性转成画图决策。
- `references/viz_pitfalls.md`：主动拦截均值柱、双 Y 轴、饼图、Y 轴截断、rainbow 色图、一图多论点、乱码、裁切和子图编号错位等高频错误。
- `references/journal_specs.md` 与 `references/publication_checklist.md`：记录最终尺寸、字体、矢量优先、色盲安全、误差说明和投稿前机器检查。
- `references/visual_review.md`：提出 PNG preview -> deterministic layout audit -> AI 读图 -> 回改重渲的视觉自检闭环。
- `references/plot_recipes.md`、`scripts/*.py`、`requirements.txt`：实现基于 matplotlib / seaborn / plotly / pandas / scipy 的 Python 绘图工具链，包含 profile、style、export、layout、visual QA 和 check scripts。
- `LICENSE`：MIT。


## 保留的方法

先确认 claim、变量类型、比较目标、样本量、分布、缺失和 grouping，再选择图型。
均值柱掩盖分布、双 Y 轴、截断坐标、rainbow 色图或一图多论点应成为审阅线索，
不能仅凭关键词自动拒绝一幅图。

按最终投稿尺寸检查字体、误差说明、色盲/灰度可读性和导出格式。
程序布局检查后仍要读取真实 PNG/PDF，修改 canonical source 并重渲。
这些专业方法由 ScholarSkills figure 能力和 MAS
[Visual Audit](../../delivery/medical-display/contracts/medical_display_visual_audit_protocol.md)
持有，Stage Review 消费 exact artifact evidence。

SciPilot Python scripts、requirements 和 Skill 正文不作为 MAS 运行依赖。
旧 figure-advisor/export-lint projection builder 和学习完成百分比不再作为当前能力证据；
render/lint 成功不能签 MAS quality、publication、submission 或 owner receipt。
