# PaperPlotHub Exemplar Exhaustion Ledger

Owner: `MedAutoScience`
Purpose: `medical_display_history_record`
State: `history_provenance`
Machine boundary: 人读医学展示能力历史/provenance 记录。当前 medical-display 能力真相继续归 `docs/delivery/medical-display/`、template/renderer source、contracts、generated artifacts、tests 和 audit receipts。

## Scope

本账本记录 `2026-04-30` 第二轮 PaperPlotHub 学习结果。目标是回答一个问题：在不复制外部脚本、截图、PNG、论文图，不把 PaperPlotHub 变成 runtime dependency 或 display-pack source 的前提下，当前公开 gallery 还有没有可以继续吸收进 MAS medical display 的内容。

结论：当前公开 PaperPlotHub gallery 的可吸收内容已经耗尽到治理边界。已经完成的吸收面是：

- `27` 条公开 gallery metadata 全量进入 [paperplothub_exemplar_intake.md](./paperplothub_exemplar_intake.md)；
- 高价值且语义可对齐的样例已作为 link-only `exemplar_refs` 绑定到既有 audited 模板；
- 剩余 `18` 条 `candidate_gap` 已按 cluster 完成 promotion decision；
- `visual_style_only` 与 `reject_for_medical_display` 条目已明确不进入正式模板队列；
- 当前没有 PaperPlotHub 驱动的 formal owner template round。

本账本只记录当前学习边界。它不创建新模板，不变更 strict audited inventory，不替代真实 MAS paper demand。

## Current Status

| landing status | count | second-pass decision |
| --- | ---: | --- |
| `mapped_existing_template` | `3` | 已吸收为 link-only exemplar refs；当前不需要新模板 |
| `visual_style_only` | `3` | 只保留视觉处理启发；不作为 medical-display capability gap |
| `candidate_gap` | `18` | 已聚类并冻结 promotion gate；需真实论文 demand 才能继续 |
| `reject_for_medical_display` | `3` | 当前不进入 MAS medical-display 路线 |

## Candidate-Gap Decision Matrix

| cluster | intake slugs | learned signal | current MAS boundary | promotion evidence required | current decision |
| --- | --- | --- | --- | --- | --- |
| generic performance bar families | `average_scores_across_warmup_steps`, `phybench_model_perf`, `ttrl_main_results`, `prerl_behavior_bars`, `bar_spice`, `bar_memevolve` | paired bars, grouped bars, delta arrows, reference lines, hatching, value labels | MAS 当前 performance / clinical-impact lower bound 更强调医学结局、校准、ROC/PR、DCA、confusion matrix 与可审计表面；通用 AI benchmark bar chart 不足以单独成为医学模板 | 真实 MAS paper 需要跨模型或跨队列的 manuscript-facing performance bar，并且现有 `performance_summary_table_generic`、ROC/PR/calibration/clinical-impact/confusion family 无法稳定表达 | `exhausted_current_public_surface`; keep as candidate evidence only |
| metric trajectory families | `opengame_debug_iters`, `kronos_test_time_scaling`, `prerl_passk_qwen4b`, `prerl_behavior_panels`, `line_selfdistill_scale`, `line_selfdistill_train`, `line_aime` | training curves, scaling curves, small multiples, confidence bands, breakpoints, log axes | MAS 已有 time-dependent ROC / longitudinal and curve families，但这些 PaperPlotHub 条目多为 AI training-process metrics；医学语义、input schema 与 QC profile 不能从图形外观直接推出 | 真实 MAS paper 需要模型随时间、训练轮次、随访窗或外部验证批次变化的正式曲线，并明确 y-axis 医学意义、interval semantics、panel role 与 submission sidecar | `exhausted_current_public_surface`; no template until paper demand proves a medical curve contract |
| distribution panels | `paperespresso_swarm`, `prerl_grad_metrics_hist` | swarm / strip distributions, histogram panels, median or stats annotation boxes | MAS 当前没有把通用 distribution diagnostics 作为独立 medical-display owner target；需要先明确统计对象、分布比较目的和误用风险 | 真实 MAS paper 需要 distribution panel 支持 cohort characteristics、model diagnostics、feature shift 或 robustness evidence，且现有 table / forest / heatmap / calibration family 不足 | `exhausted_current_public_surface`; candidate only |
| temporal composition | `aievol_diversification` | stacked area category evolution over time | 该图面主要表达 AI architecture category composition；医学 display promotion 需要 cohort、treatment、center、phenotype 或 endpoint composition 语义 | 真实 MAS paper 需要时间分层组成变化，并给出 category definition、denominator、stacking rule、missingness handling 与 QC profile | `exhausted_current_public_surface`; candidate only |
| heat-shaded performance tables | `classwise_iou` | table cells with heat shading and compact row comparisons | MAS 已有 table shell 与 heatmap family；该条还是 community plot-from-image provenance，不能凭截图反推可复用 contract | 真实 MAS paper 需要 classwise / subgroup / endpoint performance table，且必须定义 cell scale、color semantics、metric family、uncertainty treatment 与 export sidecar | `exhausted_current_public_surface`; candidate only with stronger provenance and demand |
| tradeoff scatter / Pareto views | `scatter_break` | Pareto frontier, multi-marker scatter, broken axis | Broken axis 与 Pareto framing 在医学论文里有高误导风险；当前不能仅凭外观提升为模板 | 真实 MAS paper 需要 model tradeoff / resource tradeoff / fairness tradeoff scatter，并通过 explicit axis break policy、frontier definition、label density rule 与 QC review | `exhausted_current_public_surface`; candidate only, high review burden |

## Already-Mapped Learning

`mapped_existing_template` 条目已完成吸收，不再打开新模板：

- `llmoptim_forest`：现有 forest / multivariable forest 模板已经承接 effect estimate + CI 的医学表达；
- `aiscientist_heatmap`：现有 grouped heatmap / performance heatmap 模板已经承接 matrix pattern 与 marginal grouping style；
- `scatter_tsne`：现有 grouped t-SNE scatter 模板已经承接 embedding scatter 的医学表达。

另有 `prerl_passk_qwen4b` 被用作 `time_dependent_roc_comparison_panel` 的 link-only visual exemplar，因为它的 small-multiple curve treatment 对现有曲线模板有排版参考价值；它在 intake 中仍保持 `candidate_gap`，不被解释为语义完整的 medical curve mapping。

## Visual-Only Learning

这些条目只保留为视觉启发，不进入模板 promotion：

- `paperespresso_hype`：hype-cycle 叙事曲线不属于当前 medical-display evidence family；
- `predictscale_contour`：contour geometry 已有现有 partial-dependence / interaction contour 模板承接，超参数语义不迁入 MAS；
- `line_loss_inset`：axis styling 与 inset treatment 不构成独立医学模板。

## Rejected Learning

这些条目当前不适合作为 MAS medical-display 学习源：

- `predictscale_3dloss`：3D loss landscape 不适合当前 submission-facing medical display；
- `genericagent_tool_donut`：donut tool-call distribution 不符合当前 evidence-display 方向；
- `radar_dora`：radar chart 在医学证据比较里解释风险高，不进入当前路线。

## Promotion Gate

PaperPlotHub 条目只有同时满足下面条件，才允许从本账本重新进入 active owner round：

1. 有真实 MAS paper demand 指向同一医学问题，而不是单纯看到外观相似；
2. 能写成显式 input schema，包括单位、分母、分组、uncertainty、missingness 和 panel role；
3. 有 deterministic renderer path，不依赖 post-hoc layout repair、文本避让或人工修图；
4. 有明确 QC profile 或值得新增一个审计边界清晰的 profile；
5. 能进入 catalog / lock / submission sidecar 的全链路验证；
6. provenance 保持 link-only，除非外部脚本和图像许可经过单独审计并明确允许仓内再分发。

## No More Current Learning Criteria

当前 PaperPlotHub 学习视为耗尽，直到满足以下任一触发条件：

- PaperPlotHub public gallery 出现新条目或公开 metadata 发生实质变化；
- MAS 真实论文线提出现有 display pack 无法表达的图面需求；
- 现有 candidate-gap cluster 获得更强医学证据，足以通过上面的 promotion gate；
- display pack schema / renderer / QC / submission surface 已经具备承接某个 cluster 的正式 owner round 条件。

在这些触发条件出现前，继续浏览同一批 PaperPlotHub `27` 条公开条目不会产生新的可落地 MAS 资产。
