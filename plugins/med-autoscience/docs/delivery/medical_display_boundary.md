# MAS Medical Display 交付与审计边界

Owner: `MedAutoScience`
Purpose: `medical_display_delivery_audit_and_env_ssot`
State: `active_current_truth`
Machine boundary: 可执行真相归 V2 Stage action catalog/manifest、Tool Affordance Boundary、`contracts/capability_map.json`、`contracts/runtime_environment_requirements.json`、`mas-scholar-skills/packs/medical-display-core/` 模板描述符与布局 sidecar、Stage Review receipts 与 MAS owner receipts。

## Owner 分工与 Stage 流程

Medical display 遵循标准 OPL Agent 边界，MAS 不维护 repo-local display CLI、catalog generator、installer、renderer 副本或单图 gallery 示例：

- **MAS**：持有医学 figure intent、claim/data refs、visual audit、quality gate 与 artifact/publication authority。
- **OPL Framework**：持有通用 Package discovery/activation 聚合、environment prepare/run、renderer transport、StageRun 与 hosted workbench（实际 carrier 持有安装生命周期）。
- **ScholarSkills (`medical-display-core`)**：持有版本化模板包（`packs/medical-display-core/templates/*/template.toml` 与生成的 `canonical_template_catalog.json`）、共享 R helpers、dependency requirement profiles 与人审 compact gallery（`mas-scholar-skills/gallery/medical-display/`）。

Display 通过六个公开 Stage action 消费：`manuscript_authoring` 形成 figure intent/spec 并按需调用模板与 renderer，`review_and_quality_gate` 消费 layout/visual/claim QC 与 independent review refs，`finalize_and_publication_handoff` 绑定 final display refs、package refs 与 owner authority。

## 研究图族与 Paper-Facing 路由 Cookbook

论文图形按“回答什么临床/研究问题”组织，最终模板与渲染能力从已安装 ScholarSkills canonical catalog 读取（历史模板名或外部示例不证明当前可用性）：

- **八类医学研究图族**：Prediction and decision（区分度/校准/决策曲线）、Survival and time-to-event（KM/累积发生率/at-risk）、Effects and heterogeneity（效应量/置信区间/亚组交互）、Representation and geometry（降维/聚类/纵向轨迹）、Matrix patterns（缺失率/相关性/组间热图）、Model explanation（SHAP/特征贡献/支撑域）、Biology and omics（通路/变异/多组学 provenance）、Cohort and study design（人群流程/基线平衡/跨中心覆盖）。

| Paper-facing route family | 用途 | 最小输入 | 审阅重点 |
| --- | --- | --- | --- |
| `baseline_table` | Table 1 / cohort baseline | cohort groups、变量字典、缺失率 | 单位、分组、缺失、临床可读性 |
| `forest_effect` | subgroup / interaction / sensitivity | effect estimate、CI、subgroup labels | CI、reference、multiplicity、方向一致性 |
| `kaplan_meier` | survival comparison | time、event、group、at-risk counts | censoring、at-risk table、time horizon |
| `calibration_curve` | prediction calibration | predicted risk、observed risk、bins | slope/intercept、置信区间、过拟合 |
| `decision_curve` | clinical utility | threshold、net benefit、treat-all/none | threshold range、临床解释、基线策略 |
| `shap_summary` | explainability | feature values、SHAP values、cohort scope | label、direction、clinical plausibility |
| `trajectory_panel` | longitudinal course | time axis、measurements、grouping | 时间定义、平滑、个体/群体区别 |

Cookbook 规则：每条路线必须声明医学问题并绑定数据输入、claim、caption、reviewer concern 与 freshness status；display refresh 须回指 source/analysis/write owner route，caption 与临床解释不得模板化偷懒；上游 AI benchmark 图模板不直接进入 MAS，只有服务医学论证的路线才纳入。

## Renderer 政策与审计门槛

| 图面类型 | Renderer 政策 | Authority 边界 |
| --- | --- | --- |
| Evidence figures | R/ggplot2 优先；当前 pack 无 Python evidence 模板 | 仅基于结构化 payload 与 renderer/QC 合同展示统计证据 |
| Illustration shells | 允许 Python/SVG/composition | 表达机制、队列流程或图形摘要，不能承载统计证据 authority |
| Table shells | 结构化表格 renderer | 物化表格交付物，不能签 publication readiness |

未来仅当证明相对 R/ggplot2 基线具备明确优势并补齐当前描述符、layout/QC/audit 证据与测试后，才可重新纳入 Python evidence 模板。`--package-only` 仅证明文档打包或由现有资产重生成 PDF，不证明 renderer、依赖环境或真实数据已被重新渲染；外部图库/论文示例仅作只读学习参考，须经完整描述符、renderer、QC、catalog 与测试落地后才算可用能力。

医学图表交付必须保留 exact artifact/source/data refs、生成参数、content hash、panel/legend/label 语义与 visual-audit evidence。`medical-figure-design`、`medical-figure-style` 与 `medical-figure-composer` 只提供设计与 QA 候选；正式通过、修复、质量债或 hard gate 必须由独立 reviewer/re-reviewer 基于真实图像、layout sidecar 与 rubric 给出，再由 MAS owner receipt 关闭（template resolved、render success、golden match、layout QC、Gallery 生成或 OPL smoke receipt 均不授权 publication/submission readiness）。

## 依赖与环境边界

MAS 的 `analysis-display` 默认只绑定 Rscript；具体分析显式声明外部包。ScholarSkills 持有专业模板的 `requirement_profile_ids` 与依赖配置，MAS 读取选中模板配置的完整并集交给 OPL `env prepare/run`（普通图不连带安装热图、降维等专用包；MAS 不维护安装器或 renderer transport）。

任务内脚本合并、批量绘图一致性准入、结果绑定及失败边界由 [执行策略](../../agent/skills/medical_research_execution.md#task-environment-routing) 定义：对于同任务、已准备环境下的多张独立图，当已安装 ScholarSkills provider 暴露 `--batch <request.json>` 且经其 `packs/medical-display-core/tests/benchmark_render_batch.py` 验证一致性、失败隔离、状态恢复及较逐图渲染至少 20% 总耗时收益时，默认采用批量入口；若实现或运行时变化使资格失效，回退单图路径直至重新验证通过。批量执行不改变单图医学与视觉审阅义务。

环境调用与本地验证见 [Bootstrap](../../bootstrap/README.md)，整体架构见 [架构概览](../architecture.md)，Runtime 分工见 [Runtime 边界](../runtime/runtime_boundary.md)。
