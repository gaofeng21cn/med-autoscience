# MAS 医学论文配图 Gallery

Owner: `MedAutoScience`
Purpose: `human_readable_gallery_for_builtin_mas_display_templates`
State: `active_support`
Machine boundary: 人读示例文档。机器真相继续归 display-pack template descriptor、renderer source、`paper/publication_style_profile.json`、layout sidecar、display lock、publication manifest、tests 和真实论文 artifacts。

- [PDF Gallery](./medical_display_gallery.pdf)：面向人阅读的主文档，用于直观判断 MAS 默认图页组织、非数据设计图起点、数据证据图起点和统一视觉风格。
- [生成状态](./display_pack_gallery_status.md)：从 manifest 生成的数量、路由和生成口径。
- [质量审计](./display_pack_gallery_quality_audit.md)：从质量门生成的模板入库状态、风险项和论文使用前检查项。

HTML、manifest、payload、layout sidecar、PNG/SVG/PDF 单图导出属于可再生成的本地输出，默认写入仓库忽略的 `outputs/display-pack-gallery/`。需要重建时运行：

```bash
./scripts/run-python-clean.sh scripts/build-display-pack-gallery.py --publish-docs
```

## 设计目的

MAS 的绘图模板库提供统一、可审计、可继续打磨的论文配图起点。默认流程是：

1. 先根据论文论点选择页面级图页方案。
2. 再为每个数据证据面板选择 R/ggplot2 证据图起点。
3. MAS 根据论文语义继续调整布局、标签、配色和面板结构。
4. 最终论文图件经过真实论文语境下的视觉审查和证据引用检查。

PDF 画册分为三部分：前部展示 6 类页面级图页方案，中部展示非数据设计/流程图起点，后部展示 28 个 R/ggplot2 数据证据图起点。未证明优于 R/ggplot2 的 Python 数据证据模板不进入默认画册。

## 数据证据图分类

| Category | Templates |
| --- | ---: |
| Prediction Performance | 3 |
| Clinical Utility | 2 |
| Time-to-Event | 5 |
| Effect Estimate | 2 |
| Generalizability | 1 |
| Data Geometry | 3 |
| Matrix Pattern | 2 |
| Model Explanation | 3 |
| Model Audit | 1 |

## 页面级图页方案

这些页面级方案用于组织多个数据证据面板。它们确定一张论文主图或关键扩展图的论点结构、主面板和辅助证据。

| Recipe | Hero panel | Supporting panels | Preview anchors |
| --- | --- | ---: | ---: |
| `clinical_triptych_prediction` | primary_model_performance_summary | 3 | 4 |
| `model_validation_dashboard` | validation_summary_or_generalizability | 3 | 4 |
| `schematic_led_composite` | schematic_or_process_hero | 3 | 1 |
| `image_plate_plus_quantification` | representative_image_plate | 3 | 3 |
| `asymmetric_genomics_figure` | dominant_molecular_pattern | 3 | 4 |
| `single_cell_atlas_storyboard` | cell_state_geometry_or_spatial_context | 3 | 4 |

## 非数据设计/流程图起点

这些图件用于 cohort flow、graphical abstract、研究流程或机制性说明。它们可以使用 SVG、Python composition 或 imagegen-assisted art direction；涉及真实结果数字时必须保留来源引用，不能替代程序化数据证据图。

| Template | Display name | Renderer | Render status |
| --- | --- | --- | --- |
| `cohort_flow_figure` | Cohort Flow Figure | python | rendered |
| `submission_graphical_abstract` | Submission Graphical Abstract | python | rendered |

## 当前默认风格与边界

- `style_profile_id`: `paper_neutral_clinical_v1`
- `journal_palette_ref`: `nature_informed_clinical_publication_v1`
- 当前数据证据图默认渲染器：`r_ggplot2=28`，`python=0`，`n/a=0`
- 当前 R/ggplot2 数据证据图起点：`28`
- 当前 Python 数据证据模板：`0`
- 当前非数据设计/流程图起点：`2`
- 已渲染 Gallery 可视示例：`30`
- 当前视觉证据图族：`28`
- 页面级图页方案：`6`
- 重复或旧 ID 只保留在生成状态和 manifest 的迁移索引中，不进入当前模板目录或画册卡片。
- 医学图族来源：`contracts/medical-figure-family-catalog/`
- 图族策略：`intent_first_current_template_surface`
- AI 改造策略：`canonical_family_baseline_then_paper_local_adaptation`
- Nature-Skills 学习版本：`5d2ba1dee1c087be6de8f4a8aad4b27f04974be9`
- 图件合同策略：`mas_nature_skills_informed_figure_contract.v1`

## 风格口径

MAS 默认风格是 `nature_informed_clinical_publication_v1`：白底、左下轴线、小字号、细轴线、弱网格、统一临床配色、连续/发散热图色板和横向 colorbar。数据分析产生的证据图以 R/ggplot2 为第一公民；未证明优于 R/ggplot2 的 Python 数据证据模板不进入当前 pack、隐藏库存或画册对比图。设计、流程和 graphical abstract shell 可以使用 SVG、Python composition 或 imagegen-assisted art direction，并作为非数据设计图起点进入 Gallery；它们不承担统计证据权威，也不混入 R/ggplot2 数据证据图分区。

Nature-Skills 的 `nature-figure` 已作为 clean-room 质量流程学习源吸收：MAS 要求图件先有核心结论、证据链、面板层级、期刊/导出合同和最终视觉审查记录。与上游不同的是，MAS 的默认数据证据路径直接走 R/ggplot2，同时保留 AI 对布局、面板、配色、标签、backend 和组合方式的论文级改造权限。
