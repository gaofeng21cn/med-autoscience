# Display Pack Renderer 分层与 R/ggplot2 迁移评估

Owner: `MedAutoScience Medical Display`
Purpose: `display_pack_renderer_topology_and_migration_assessment`
State: `landed_r_first_current_pack`
Machine boundary: 本文是人读结构评估。机器真相继续归 `display-packs/**/display_pack.toml`、`display-packs/**/templates/*/template.toml`、renderer source、`renderer_migration_ledger.json`、E2E runtime、tests、真实 paper artifacts、visual-audit receipt、owner receipt 和 publication gate。

## 当前结论

`R/ggplot2-first` 已在 core pack 收口为当前默认路径：55 个 data evidence templates 全部是 `renderer_family = "r_ggplot2"`、`execution_mode = "subprocess"`、`entrypoint = "Rscript render.R --request {request_json}"`。Python evidence 不再作为隐藏库存、显式请求库存或 Gallery 对比图保留。

当前 `fenggaolab.org.medical-display-core` 的真实 inventory 是：

| 口径 | 数量 | 当前真实状态 |
| --- | ---: | --- |
| Evidence figure template descriptor | 55 | 已在 `templates/*/template.toml` 注册，均为当前 R evidence。 |
| `renderer_family = "r_ggplot2"` | 55 | 当前全部 evidence templates 的一等默认 renderer。 |
| `renderer_family = "python"` evidence | 0 | 当前 pack 不保留 Python evidence。 |
| `execution_mode = "subprocess"` evidence | 55 | 全部 evidence templates 均由 template-local `render.R` 调用。 |
| Python illustration shells | 4 | 仅用于 design / flow / graphical abstract composition，不承担统计证据 authority。 |
| Table shells | 7 | 由 table shell renderer 生成，不属于 evidence figure。 |

因此，现状应读作：**当前医学数据证据图只保留 R/ggplot2 版本；Python 只保留在设计/流程/graphical abstract shell 和 table-shell 支撑路径。**

## Python evidence re-entry 规则

Python evidence 不是“隐藏可选项”。未来只有同时满足以下条件，才允许作为新的当前模板进入 pack：

1. 明确证明 Python 版本相对 R/ggplot2 baseline 有实际优势，例如对应领域 Python 生态明显更成熟、R 模板无法可靠表达、或 paper-specific artifact 必须依赖 Python renderer。
2. 有 machine-readable template descriptor、renderer source、layout sidecar、display lock 和 visual audit 证据。
3. Gallery、agent discover、figure plan、renderer contract 和 tests 都把该模板作为当前受审计模板，而不是 legacy baseline 或 hidden inventory。
4. 不降低整篇论文的 palette、typography、guide placement 和 export discipline 一致性。

## 当前目标结构

```text
display-packs/fenggaolab.org.medical-display-core/
  display_pack.toml
  canonical_template_catalog.json
  renderer_migration_ledger.json
  templates/
    <template_id>/
      template.toml
      render.R                 # 当前 R/ggplot2 subprocess 一等入口
      example_input.json       # 可选，最小输入
      goldens/                 # 可选，template-local regression assets
  src/
    fenggaolab_org_medical_display_core/
      evidence_figures/r_renderer.py   # 旧 host materialization compatibility caller
      illustration_shells/             # design / flow composition shells
      table_shells.py                  # table shell renderer
  rlib/
    medicaldisplaycore/        # R shared helpers，不能替代 template-local entrypoint
```

模板 descriptor 规则：

| 模板类型 | `renderer_family` | `execution_mode` | `entrypoint` |
| --- | --- | --- | --- |
| 当前 evidence 模板 | `r_ggplot2` | `subprocess` | `Rscript render.R --request {request_json}` |
| 设计/流程 shell | `python` | `python_plugin` | `fenggaolab_org_medical_display_core.illustration_shells:render_illustration_shell` |
| Table shell | `n/a` | `python_plugin` | `fenggaolab_org_medical_display_core.table_shells:render_table_shell` |

新增或修改 evidence template 时，bootstrap、registry、canonical catalog、Gallery manifest、agent discover、figure renderer contract 和 focused tests 必须一起读回 current Python evidence count = `0`，除非该模板按 re-entry 规则正式进入当前 pack。

## R 生态证据

R/ggplot2 适合作为医学 evidence figure 默认路线，原因不是偏好，而是成熟生态覆盖面：

- `ggplot2` 官方定位就是基于 Grammar of Graphics 的声明式图形系统，能把 data、aesthetic、geom、scale、facet、theme 分层管理；其扩展生态也是长期稳定入口。[ggplot2](https://ggplot2.tidyverse.org/)
- 生存曲线和 risk table 有 `survminer::ggsurvplot()`，支持 stratified survival curves、facet/group/combine、risk table、p value、confidence interval 和 ggsci palette。[survminer ggsurvplot](https://rpkgs.datanovia.com/survminer/reference/ggsurvplot.html)
- ROC 有 `pROC::ggroc()`，可从 ROC object/list 初始化 ggplot object，并继续叠加 theme/layers。[pROC ggroc](https://search.r-project.org/CRAN/refmans/pROC/html/ggroc.html)
- Decision curve 有 `dcurves`，目标就是 model evaluation 的 decision curve analysis。[dcurves](https://www.danieldsjoberg.com/dcurves/)
- 复杂热图和多注释矩阵图有 Bioconductor `ComplexHeatmap`，适合多组学、annotation-rich heatmap 和 matrix pattern。[ComplexHeatmap](https://www.bioconductor.org/packages/release/bioc/html/ComplexHeatmap.html)
- 森林图有 `forestploter` 这类 R 包，支持多列 CI、分组和主题化编辑。[forestploter](https://adayim.r-universe.dev/forestploter)
- SHAP 可视化有 `shapviz`，覆盖 importance、beeswarm、dependence、interaction、waterfall 和 force plots。[shapviz](https://cran.r-project.org/package%3Dshapviz)
- 医学期刊和科学图配色有 `ggsci`，覆盖 NPG、NEJM、Lancet、JAMA、BMJ、JCO 等 palette。[ggsci](https://nanx.me/ggsci/)
- 文本避让可用 `ggrepel`；火山图可用 `EnhancedVolcano`；富集 dotplot 可用 `enrichplot`；肿瘤 oncoplot 可用 `maftools`。这些不必全部成为 runtime dependency，但足以证明很多 Python 手写模板可迁到成熟 R pattern。[ggrepel](https://ggrepel.slowkow.com/) [EnhancedVolcano](https://bioconductor.posit.co/packages/3.19/bioc/html/EnhancedVolcano.html) [enrichplot dotplot](https://rdrr.io/bioc/enrichplot/man/dotplot.html) [maftools oncoplot](https://rdrr.io/bioc/maftools/man/oncoplot.html)
