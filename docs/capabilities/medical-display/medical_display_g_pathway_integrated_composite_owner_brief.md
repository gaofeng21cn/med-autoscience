# Medical Display G Pathway-Integrated Genomic Composite Owner Brief

## 文档定位

这份 brief 是当前 `G` 家族 owner round 的唯一实现锚点。

它回答 5 个问题：

1. 这一轮到底要落成哪个模板；
2. 这张图要回答什么论文问题；
3. 最小 panel 结构和最小数据前提是什么；
4. 这一轮允许做什么，不允许做什么；
5. merge-back 前必须拿到哪些验证证据。

## 当前轮次身份

- Family：`G. 生物信息与组学证据`
- Capability cluster：`pathway-integrated genomic composite beyond the current landscape-plus-three-omics lower bound`
- 当前 owner branch：`codex/medical-display-g-pathway-integrated-composite-20260419T130417Z`
- 当前 owner worktree：`.worktrees/medical-display-g-pathway-integrated-composite-20260419T130417Z`

## 这轮要落成的模板

本轮收口为一个新的 audited evidence template：

- provisional template id：`genomic_alteration_pathway_integrated_composite_panel`

它是在当前 3 条已吸收能力之上继续上提一层：

1. `genomic_alteration_landscape_panel`
2. `genomic_alteration_multiomic_consequence_panel`
3. `pathway_enrichment_dotplot_panel`

目标是把“driver alteration 是否同时推动下游 omics 层后果与 pathway 层偏移”收成一张正文可直接使用的 bounded composite。

## 论文问题

当前模板必须稳定回答下面这个问题：

> 关键 driver alteration 在样本层是否形成明确的 mutation-plus-CNV landscape，并且这种 alteration 是否在 proteome / phosphoproteome / glycoproteome 三个层面同时表现出可解释的基因级 consequence 与 pathway-level enrichment 偏移。

换句话说，这张图服务的是：

- 左边给出 alteration 事实面；
- 右上给出 gene-level consequence 面；
- 右下给出 pathway-level integrated summary 面。

## exemplar 依据

这轮 brief 只吸收高价值、可复用的结构性信息：

1. `Nature Communications` `2025`
   - MuPPE 论文把 `proteome / phosphoproteome / glycoproteome` 作为固定三层，并对三层做共享 pathway 级比较。
   - 这一点支持我们把 pathway 面也固定成三层 shared-order contract，而不是临时增减 panel。
2. `Nature Cancer` `2024`
   - proteogenomic landscape 类论文持续把 genomic alteration、分子层 consequence 和 pathway/program 解释拉进同一条 manuscript-facing 叙事链。
   - 这一点支持我们继续沿“alteration -> consequence -> pathway”三段式收口，而不是退回分散的小图 gallery。

这一轮吸收的是结构，不是照抄版式。

## 最小 panel 结构

本轮新模板固定为 `1 + 3 + 3` 结构：

1. 左列 `A`
   - 沿用当前 genomic alteration landscape 主骨架：
   - burden
   - annotation tracks
   - alteration matrix
   - frequency sidebar
2. 右上 `B/C/D`
   - 固定三层 gene-level consequence panels：
   - `proteome`
   - `phosphoproteome`
   - `glycoproteome`
3. 右下 `E/F/G`
   - 固定三层 pathway-level panels：
   - `proteome`
   - `phosphoproteome`
   - `glycoproteome`

这里的关键不是“多放几块”，而是把 3 层 omics vocabulary 在 gene-level 与 pathway-level 两个层面都固定住。

## 最小数据前提

新模板至少要求：

1. alteration landscape 所需的全部字段
   - `gene_order`
   - `sample_order`
   - `annotation_tracks`
   - `alteration_records`
2. multiomic consequence 所需的全部字段
   - `driver_gene_order`
   - `consequence_panel_order`
   - `consequence_points`
   - `effect_threshold`
   - `significance_threshold`
3. pathway-integrated 所需新增字段
   - `pathway_order`
   - `pathway_x_label`
   - `pathway_y_label`
   - `pathway_effect_scale_label`
   - `pathway_size_scale_label`
   - `pathway_panel_order`
   - `pathway_points`

新增 pathway 层必须满足：

1. panel ids 与 consequence 层保持完全一致：
   - `proteome`
   - `phosphoproteome`
   - `glycoproteome`
2. 所有 panel 共用同一条 `pathway_order`
3. 每个 `panel_id x pathway_label` 坐标必须完整覆盖且唯一
4. `size_value` 非负
5. `x_value`、`effect_value` 有限

## 继承与复用规则

这轮必须复用已有 contract，而不是另起体系：

1. alteration landscape 左列直接继承 `genomic_alteration_multiomic_consequence_panel`
2. 右上三层 consequence 直接继承当前 multiomic consequence contract
3. 右下三层 pathway 继承 `pathway_enrichment_dotplot_panel` 的 shared-pathway grid 语义
4. palette、typography、panel-label、title policy 继续服从当前 audited display contract

## 这一轮明确不做的事

这一轮不进入下面这些方向：

1. pathway network graph
2. node-link / sankey / circos
3. 自动聚类、自动 pathway 压缩、自动布局避让
4. 超过三层的任意 omics 扩容
5. atlas / spatial / trajectory 混入
6. 论文现场自由拼装的“超大综合图”

## 审计与质控重点

这轮要锁住的 fail-closed lower bound 包括：

1. `A` 面板的 landscape panel 结构仍完整
2. `B/C/D` 与 `E/F/G` 的 panel ids 必须都固定为三层 omics vocabulary
3. consequence 层每个 panel 必须覆盖全部 driver genes
4. pathway 层每个 panel 必须覆盖全部 declared pathways
5. panel labels、panel titles、x/y axis titles、legend / colorbar / size legend 必须留在各自 blank zone 内
6. figure title 默认继续隐藏，只保留 panel titles

## 最低测试面

最少需要一起补齐：

1. `tests/test_display_registry.py`
2. `tests/test_display_schema_contract.py`
3. `tests/test_display_surface_materialization.py`
4. `tests/test_display_layout_qc.py`
5. `tests/test_display_deg_golden_regression.py`

## merge-back 前必须满足

1. 新模板正式注册
2. schema contract、source contract、materialization、renderer、QC、golden regression 一起闭环
3. `scripts/verify.sh` fresh 通过
4. `make test-meta` fresh 通过
5. 相关 docs/catalog/changelog fresh 对齐

## 当前推荐实现顺序

1. 先写 registry/schema/source failing tests
2. 再写 materialization / QC / DEG golden failing tests
3. 再补 renderer 与 sidecar
4. 最后回刷 catalog 与 docs

