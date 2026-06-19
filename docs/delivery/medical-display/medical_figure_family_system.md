# MAS 医学论文图型家族体系指南

Owner: `MedAutoScience`
Purpose: `medical_figure_family_taxonomy_and_operator_guide`
State: `active_delivery_support`
Machine boundary: 人读 taxonomy、维护指南和 operator 使用指南。机器真相归 `contracts/medical-figure-family-catalog/`、catalog loader、schema / validator tests、Display Pack template descriptors、renderer source、QC contract、generated artifacts、visual-audit receipt、display lock、publication manifest 和 MAS owner receipt。本文不能被脚本、测试、runtime 或 Gallery 当作机器接口。

## 结论

医学图型家族系统的核心规则是：

模板提供高质量下限，不是上限。AI 可以自由改造图的结构、布局、panel 编排、注释、legend、局部叙事和视觉表达，但必须保留 claim / data / statistics / evidence refs 的真实性，并通过确定性质量门、真实图像 visual audit、必要的独立 reviewer / owner gate。

这套体系用于指导实现和使用，不替代现有 Display Pack v2 合同，也不把文档写成第二真相源。family / variant / starter recipe 的机器入口是 `contracts/medical-figure-family-catalog/`、loader 和 tests；只改本文或 README 不能声明 family 已 landed。

## 适用对象

本文面向两类人：

- MAS maintainer：维护图型 taxonomy、Display Pack template、style token、QC / visual audit promotion 和 catalog loader。
- MAS operator / agent：从论文 claim、data refs 和 paper intent 出发，选择合适 family，拿 starter recipe 生成可审图的第一版，再通过 critique loop 把图推到投稿级表达。

不适用场景：

- 不用于签 publication-ready、submission-ready、artifact authority、owner receipt 或 paper closure。
- 不用于替代真实渲染图审阅、`paper/publication_style_profile.json`、`paper/figure_spec.json`、`paper/figure_visual_audit_receipt.json` 或 `paper/build/display_pack_lock.json`。
- 不用于把外部 Gallery、论文截图、公开模板页面或 link-only exemplar 直接升级成 MAS runtime dependency、template truth、golden truth 或质量结论。

## 分层模型

图型家族体系分五层读取，每层的职责不同。

| 层级 | 作用 | 例子 | 不能做什么 |
| --- | --- | --- | --- |
| `artifact_kind` | 区分证据图、说明图、表格 shell | `evidence_figure`、`illustration_shell`、`table_shell` | 不能表达医学问题本身。 |
| `family` | 表达论文问题和证据类型 | 预测性能、生存事件、效应量、队列设计 | 不能指定完整 renderer 实现。 |
| `variant` | 表达数据形态、统计语境和 panel grammar | binary ROC、time-dependent ROC、subgroup forest、multi-cohort heatmap | 不能绕过 input schema 或 claim/data refs。 |
| `starter_recipe` | 提供第一版可审图的最低可用 recipe | 推荐 template、input schema、style tokens、QC checklist、critic prompts | 不能限制 AI 只能照模板生成最终图。 |
| `paper_render_instance` | 真实论文中的一次图生成和审计实例 | `figure_intent`、rendered PNG/PDF、QC、visual audit、lock refs | 不能把一次局部取舍反向写成全局规则，除非经过 promotion。 |

### Family

`family` 回答“这张图在论文里解决什么问题”。它是维护者和 operator 共同使用的上层语言，应该稳定、少而清楚。

一个 family 至少需要说明：

- 论文问题；
- 典型 claim / data refs；
- 常见 display variants；
- 常见错误和 QA 风险；
- 可用的 Display Pack template anchors；
- 哪些情况需要 human / reviewer / owner decision。

### Variant

`variant` 回答“这个 family 在当前数据和统计语境下应该怎样表达”。它可以比 family 更细，也可以复用多个 family 的图形语言。

典型 variant 包括：

- binary prediction curve、time-dependent prediction curve、multicohort calibration；
- KM grouped curve、cumulative incidence、landmark summary；
- main-effect forest、subgroup forest、interaction effect panel；
- embedding scatter、trajectory storyboard、spatial niche panel；
- SHAP beeswarm、PDP / ICE、support-domain explanation。

Variant 必须绑定可验证输入形状。没有 schema、data refs 或统计输出 refs 时，只能生成缺口或 next-safe-action，不能让 renderer 猜数据。

### Starter Recipe

`starter_recipe` 是第一版图的启动配方，不是最终形态。它的职责是让 agent 快速生成一张不会低于质量下限的可审图。

一个 starter recipe 至少包含：

- 推荐 `family_id` 和 `variant_id`；
- 推荐或允许的 Display Pack template anchors；
- 输入 schema / required refs；
- 默认 panel grammar；
- 必须继承的 `publication_style_profile` tokens；
- deterministic QC profile；
- visual-audit checklist；
- 允许 AI 改造的层；
- 禁止 AI 改造的层；
- 失败后 typed repair route 或 next-safe-action。

Starter recipe 的成功标准不是“看起来像模板”，而是“真实渲染图能进入 critique loop，并且所有科学含义可追溯”。

## Canonical Category 清单

当前机器 catalog 已落地为 12 个 category、70 个 figure family。本文只展示人读索引；完整 family、variant、loose-match terms、style / palette / QA refs 和 external refs 以 `contracts/medical-figure-family-catalog/` 为准。后续若要增删或重命名，必须先更新机器 catalog、loader 和 tests，再同步本文。

| Category ID | 中文名 | 论文问题 | 常见 family / artifact |
| --- | --- | --- | --- |
| `study_design_and_flow` | 研究设计与样本流程 | 研究对象从哪里来，如何纳排、分组、筛选、随访和分析 | CONSORT flow、STROBE cohort flow、PRISMA flow、STARD flow、eligibility waterfall、timeline |
| `population_and_baseline` | 人群基线与分布 | 队列结构、基线差异、缺失、中心覆盖和数据质量如何 | Table 1 companion、SMD love plot、missingness matrix、center coverage、distribution comparison |
| `effect_estimation` | 效应量与统计关联 | 主效应多大，方向是否稳定，亚组或交互是否可信 | effect forest、subgroup forest、dose-response spline、coefficient path、interaction panel |
| `survival_and_time_to_event` | 生存与时间事件 | 风险随时间如何变化，事件差异和固定时间点表现如何 | KM with risk table、competing-risk incidence、hazard over time、landmark survival、RMST |
| `diagnosis_and_prediction` | 诊断、预测与决策 | 模型表现、校准、阈值和临床可用性如何 | ROC / PR / time-dependent ROC、calibration、decision curve、confusion matrix、risk stratification |
| `trial_response_and_safety` | 试验反应与安全性 | 干预反应、终点、安全事件和个体变化如何表达 | response waterfall、swimmer plot、AE summary、endpoint bar / curve、patient-level trajectory |
| `meta_analysis` | 证据综合与 Meta 分析 | 跨研究证据、异质性、发表偏倚和稳健性如何 | meta forest、funnel、influence、leave-one-out、GRADE / evidence map |
| `omics_and_molecular` | 组学与分子证据 | 差异表达、通路、突变格局、分子分型和多组学关系如何 | volcano、annotated heatmap、embedding、enrichment dotplot、GSEA、oncoplot、CNV / circos |
| `single_cell_and_spatial` | 单细胞、空间与轨迹 | 细胞状态、空间定位、trajectory 和 atlas bridge 如何 | UMAP / PHATE、marker dotplot、spatial niche、trajectory storyboard、cell-cell communication |
| `ml_explainability_and_causal` | 机器学习解释与因果 | 模型依赖、局部解释、响应曲线、DAG 和因果平衡如何 | SHAP、waterfall、PDP / ICE / ALE、causal DAG、love plot、threshold governance |
| `longitudinal_and_patient_trajectory` | 纵向与个体轨迹 | 随访指标、治疗路径、事件时间线和个体变化如何 | spaghetti、event-aligned trajectory、slope graph、episode timeline、state transition |
| `publication_shells` | 投稿复合壳与说明图 | 多 panel story、graphical abstract、机制图和 source-data companion 如何组织 | multipanel storyboard、graphical abstract、mechanism schematic、source-data companion、supplement panel |

读取规则：

- category 是维护边界，family 是图型选择边界，variant 是数据与统计语境边界。
- 同一个真实论文图可以组合多个 family；AI 可在保留统计语义和 source refs 的前提下改选相邻 family 或组合成 multipanel storyboard。
- Gallery 默认展示 canonical family 的代表图，重复 ROC/KM/heatmap/forest 变体作为 alias / variant 收敛，不作为默认候选噪声。
- `illustration_shell` family 只能承载说明性图。它不能携带 scientific claim，不能替代 evidence figure 的 deterministic renderer / data / QC / visual audit 路径。

## AI 自由改造权

AI 的目标不是机械选择最接近的模板，而是在可审计边界内生成更适合论文叙事的图。

允许 AI 改造的层：

- panel 拆分、合并、排序、facet 和布局；
- label、legend、annotation、callout、caption-facing emphasis；
- 坐标轴显示方式、scale presentation、参考线呈现和空白区使用；
- 图例位置、panel header、figure rhythm 和局部视觉层级；
- paper-local display overrides；
- article-level style token 的合理应用；
- 在同一 family 或相邻 family 内改选更合适的 variant；
- 将一个 starter recipe 扩展成多 panel composite，只要每个 panel 的 evidence refs 可追溯。

禁止 AI 改造的层：

- data values、统计估计、模型输出、置信区间、p 值、事件数和分母；
- claim content、evidence mark、source refs、frozen payload refs；
- owner receipt、typed blocker、human gate、publication verdict；
- schema validation、QC、visual audit、display lock 或 submission refs preservation；
- 把 AI illustration 当作 evidence figure；
- 把外部 gallery 图片、论文截图或风格示例当作 runtime asset、golden truth 或 source truth。

AI 改造后的图必须通过质量门。越过模板不等于越过质量门；结构更自由意味着更需要清楚的 refs、QC 和 visual audit evidence。

## Style / Palette Tokens

医学论文图不应每张图各自发明风格。文章级视觉真相应由 `paper/publication_style_profile.json` 表达，family / variant / starter recipe 只引用和解释 token，不复制 token 真相。

建议 token 分组：

| Token 组 | 作用 | 典型字段 |
| --- | --- | --- |
| `palette` | 定义颜色集合和色盲安全约束 | primary、secondary、neutral、warning、reference、missing |
| `semantic_roles` | 把颜色绑定到医学语义 | treatment、control、event、censored、threshold、high_risk、low_risk、external_validation |
| `typography` | 控制字号和层级 | base_size、axis_size、legend_size、panel_label_size、caption_size |
| `stroke` | 控制线条和 marker | line_width、reference_line_width、marker_size、errorbar_width |
| `grid` | 控制网格和背景 | grid_visibility、grid_axis、grid_color、panel_spacing |
| `accessibility` | 控制可读性和投稿约束 | colorblind_safe、monochrome_safe、min_label_size、contrast_floor |

维护规则：

- Family 可以声明“需要哪些语义角色”，不能写死文章级配色。
- Variant 可以声明“哪些角色不能共用颜色”，例如 event / censored、treatment / control、observed / predicted。
- Starter recipe 可以给出默认 token 使用方式，但 paper-level style profile 优先。
- 真实论文中反复出现的 style 修正，应 promotion 到 style profile、display override schema、QC 或 golden regression，而不是留在一次性 prompt 里。

## QA / Critic Loop

Operator 使用 family system 时按下面顺序推进：

1. 从 paper intent 读取 claim refs、data refs、target journal、正文语境和 figure role。
2. 选择 `family_id`，再选择最贴近的 `variant_id`。
3. 用 starter recipe 生成第一版 `figure_request`，不要让 agent 手工拼 raw template 细节。
4. 通过 Display Pack render / E2E path 生成真实 PNG/PDF/layout sidecar。
5. 运行 deterministic QC，检查 schema、layout、readability、style profile hash、required exports 和 lock refs。
6. 对真实图像运行 visual audit，记录具体 finding，而不是只读 manifest。
7. 让 critic 按科学真实性、医学语义、可读性、视觉层级、style coherence、accessibility、journal fit 和 packaging consistency 分类问题。
8. 修正最窄正确层：paper input、display override、style profile、renderer contract、QC、golden regression 或 family / variant catalog。
9. 重新 render、QC 和 audit，直到 finding resolved 或 human explicitly accepted。
10. 进入 display lock、publication manifest 和后续 MAS owner / reviewer / publication gate。

Critic finding 必须具体到可执行修复。推荐字段与 `paper/figure_visual_audit_receipt.json` 对齐：

- `artifact`
- `observed_issue`
- `paper_facing_impact`
- `suspected_layer`
- `proposed_action`
- `promotion_decision`
- `verification_plan`

不能接受的 critique：

- “更好看一点”；
- “像高分论文风格”；
- “模板不够高级”；
- “大概通过”；
- “测试绿，所以可投稿”。

## 与 Display Pack 的关系

Family system 是选择和治理语言；Display Pack 是可执行能力面。

| Surface | 角色 |
| --- | --- |
| `contracts/medical-figure-family-catalog/` | family / variant / starter recipe、loose matching、style / palette / QA / external refs 的机器 catalog。 |
| Display Pack template descriptors | 具体模板、renderer、schema、QC 和 exports。 |
| `paper/figure_intent.json` | paper-local figure 目标、claim refs 和 data refs。 |
| `paper/figure_spec.json` / `paper/figure_specs.json` | MAS-native 医学 figure grammar。 |
| `paper/publication_style_profile.json` | 文章级 style / palette token 真相。 |
| `paper/display_overrides.json` | 论文局部结构化展示调整。 |
| `paper/figure_visual_audit_receipt.json` | 真实图像 visual audit findings。 |
| `paper/figure_polish_lifecycle.json` | AI/VLM polish lifecycle。 |
| `paper/build/display_pack_lock.json` | pack、style、figure-quality refs 和 artifact refs 锁定。 |

Display Pack 可以提供 starter recipe 的 template anchors 和 deterministic lower bound，但它不能替代 family-level paper question，也不能签 publication verdict。Family system 可以推荐 Display Pack 路径，但不能自己物化图、改数据、改 claim 或签 owner authority。

## 与 Gallery / Exemplar 的关系

Gallery 和 exemplar 是人读参考，不是机器真相。

允许：

- 用 Gallery 查看当前 pack 的可视输出下限；
- 用 link-only exemplar 记录外部高质量图面的风格和问题；
- 把可复用观察写成 style / audit hint、template gap candidate 或 starter recipe 改进建议；
- 在真实 paper demand 证明缺口后，把候选推进到 active board / catalog / contract / tests。

禁止：

- 复制外部脚本、PNG、截图、论文图或 gallery runtime 进 MAS template truth；
- 把 Gallery 中的图直接当作 golden regression，除非它由 MAS render path 生成并进入正式 golden / lock / audit surface；
- 把 style score、外部示例或 AI 偏好当作 publication gate；
- 把 link-only exemplar 写成已 landed template。

## 维护协议

新增或提升一个 family / variant / starter recipe 时，按下面顺序执行：

1. 先确认真实 paper demand 或重复 visual-audit finding。
2. 在 active board 或对应 planning surface 记录 owner、目标、allowed writes、forbidden authority 和 verification path。
3. 更新 `contracts/medical-figure-family-catalog/`，声明 family、variant、starter recipe、required refs、allowed AI customization、forbidden layers、style token needs、QA checklist 和 Display Pack anchors。
4. 更新 catalog loader 和 schema / validator tests，确保缺 required refs 时 fail closed。
5. 如需新增 template，更新 Display Pack descriptor、renderer、input schema、QC profile 和 golden / scaffold evidence。
6. 跑 repo-native verification。机器合同或 loader 变更至少覆盖 focused tests、`make test-meta` 和 `scripts/verify.sh`；docs-only 可按文档变更处理，但不能声明 machine landed。
7. 将使用指南同步到本文、README 或相关 roadmap，但不要让 narrative docs 成为 runtime source。

退役或合并一个 family / variant 时也必须走机器 catalog。只从本文删掉条目，不表示 runtime、template 或 Gallery 已退役。

## Operator 快速读法

生成医学论文图时，operator 只需要记住下面的路径：

```text
paper claim / data refs
  -> family
  -> variant
  -> starter recipe
  -> Display Pack render
  -> deterministic QC
  -> visual audit / critic loop
  -> display lock / publication manifest
  -> MAS owner / reviewer / publication gate
```

若 family 无 exact template：

- 不要让 agent 停在“没有模板”；
- 选择最接近的 starter recipe 作为质量下限；
- 明确输出 `adaptable_baseline_not_exact_contract`；
- 只在允许层改造表达；
- 把缺口写成 template gap、style/QC gap 或 next-safe-action；
- 重复出现的缺口再 promotion 到 machine catalog / Display Pack。

若 visual audit 指出模板下限不足：

- 不做隐藏后处理；
- 不在最终图片上手工修补；
- 不用 prompt 记忆代替合同；
- 修正 paper input、display override、style profile、renderer、QC 或 starter recipe；
- 重新 render 并复审真实图像。

## 完成口径

本文落地后只能声明：

- family / variant / starter recipe 的人读维护指南已存在；
- operator 有清晰路径理解“模板是下限，AI 可拔高上限”；
- 机器 catalog、loader 和 tests 已提供 family system 的 durable 下限。

本文不能声明：

- 新 family 已进入 runtime；
- Display Agent OS 已完整落地；
- Gallery 已成为 machine catalog；
- 任一真实 paper figure 已 publication-ready、submission-ready 或 owner-accepted。
