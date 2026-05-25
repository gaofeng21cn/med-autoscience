# PaperPlotHub Exemplar Intake

Owner: `MedAutoScience`
Purpose: `medical_display_history_record`
State: `history_provenance`
Machine boundary: 人读医学展示能力历史/provenance 记录。当前 medical-display 能力真相继续归 `docs/delivery/medical-display/`、template/renderer source、contracts、generated artifacts、tests 和 audit receipts。

## Scope

本文记录 `2026-04-30` 对 PaperPlotHub 当前公开 gallery 的一次只读 intake。

来源面：

- PaperPlotHub homepage: <https://paperplothub.tech/>
- PaperPlotHub detail pages: `https://paperplothub.tech/p/<slug>`
- PaperPlotHub about / repository license surface: <https://paperplothub.tech/about>, <https://github.com/Trae1ounG/PaperPlotHub>

当前公开首页统计：

- `approved=27`
- `papers=21`
- `types=14`

本文只保存 metadata 和链接。未复制外部脚本、截图、PNG、论文图或论文正文。

## Intake Rules

`landing status` 只使用下面四个值：

- `mapped_existing_template`: 图面语义和现有 MAS medical-display 模板有明确可审计映射。
- `visual_style_only`: 仅吸收视觉或排版风格，当前不作为 medical-display 模板缺口。
- `candidate_gap`: 可作为后续候选缺口证据，但不等于 active board 工作项。
- `reject_for_medical_display`: 当前不适合作为 medical-display 模板方向。

`existing template mapping` 使用短模板名；如无特别说明，均指 `fenggaolab.org.medical-display-core::<template_id>`。`none` 表示当前 strict catalog 没有合适语义模板。

`license/provenance note` 只说明本次 intake 的来源与处理方式。PaperPlotHub 站点页脚和公开仓库显示 `MIT`；本 intake 不重新分发脚本或外部论文图，也不把上传者脚本许可推断为 MAS 内部许可。

## Gallery Enumeration

| slug | PaperPlotHub URL | script URL | paper/arXiv | chart type | tags | MAS family | existing template mapping | landing status | license/provenance note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `average_scores_across_warmup_steps` | <https://paperplothub.tech/p/average_scores_across_warmup_steps> | <https://paperplothub.tech/files/cmofi5ibk3xfqbmpo/script.py> | arXiv:2604.14142 | Bar Chart | `gradient`, `value-labels`, `serif` | `A` | none, generic performance bar absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `paperespresso_hype` | <https://paperplothub.tech/p/paperespresso_hype> | <https://paperplothub.tech/files/cmofgw75zaiqt3ocs/script.py> | arXiv:2604.04562 | Other | `hype-cycle`, `annotated-curve`, `phase-coloring` | none | none | `visual_style_only` | PPH MIT surface; link-only metadata; no script or image copied |
| `paperespresso_swarm` | <https://paperplothub.tech/p/paperespresso_swarm> | <https://paperplothub.tech/files/cmofgw75o13dw9esr/script.py> | arXiv:2604.04562 | Box / Violin | `strip-plot`, `jittered-scatter`, `median-annotation` | `C/H` | none, distribution strip or swarm panel absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `aievol_diversification` | <https://paperplothub.tech/p/aievol_diversification> | <https://paperplothub.tech/files/cmofgw755o80nlbud/script.py> | arXiv:2604.10571 | Area / Stack | `stacked-area`, `time-series`, `category-stack` | `H` | none, temporal composition stack absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `llmoptim_forest` | <https://paperplothub.tech/p/llmoptim_forest> | <https://paperplothub.tech/files/cmofgw74p6ep1ke0y/script.py> | arXiv:2604.19440 | Error Bar | `forest-plot`, `confidence-interval`, `significance-stars` | `C` | `forest_effect_main`, `multivariable_forest` | `mapped_existing_template` | PPH MIT surface; link-only metadata; no script or image copied |
| `predictscale_3dloss` | <https://paperplothub.tech/p/predictscale_3dloss> | <https://paperplothub.tech/files/cmofgw7496brm2vrb/script.py> | arXiv:2503.04715 | 3D Plot | `3d-surface`, `loss-landscape`, `twin-panel` | none | none | `reject_for_medical_display` | PPH MIT surface; link-only metadata; no script or image copied |
| `predictscale_contour` | <https://paperplothub.tech/p/predictscale_contour> | <https://paperplothub.tech/files/cmofgw73vnz85f0sn/script.py> | arXiv:2503.04715 | Contour | `contour`, `log-log-axes`, `optimum-overlay` | `F` | `partial_dependence_interaction_contour_panel`, geometry only | `visual_style_only` | PPH MIT surface; link-only metadata; no script or image copied |
| `aiscientist_heatmap` | <https://paperplothub.tech/p/aiscientist_heatmap> | <https://paperplothub.tech/files/cmofgw73hxyhhlu36/script.py> | arXiv:2604.18805 | Heatmap | `heatmap`, `marginal-bars`, `category-groups` | `E` | `heatmap_group_comparison`, `performance_heatmap` | `mapped_existing_template` | PPH MIT surface; link-only metadata; no script or image copied |
| `opengame_debug_iters` | <https://paperplothub.tech/p/opengame_debug_iters> | <https://paperplothub.tech/files/cmofgw733el0aer5q/script.py> | arXiv:2604.18394 | Line Chart | `training-curve`, `marker-styles`, `monotonic-improvement` | `A/F` | none, generic metric trajectory absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `genericagent_tool_donut` | <https://paperplothub.tech/p/genericagent_tool_donut> | <https://paperplothub.tech/files/cmofgw72l1b93o6j4/script.py> | arXiv:2604.17091 | Pie / Donut | `donut`, `leader-callout`, `small-multiples` | none | none | `reject_for_medical_display` | PPH MIT surface; link-only metadata; no script or image copied |
| `kronos_test_time_scaling` | <https://paperplothub.tech/p/kronos_test_time_scaling> | <https://paperplothub.tech/files/cmofgw7243dl02wn3/script.py> | arXiv:2508.02739 | Line Chart | `test-time-scaling`, `log-x`, `confidence-band` | `A/F` | none, generic metric trajectory with interval absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `phybench_model_perf` | <https://paperplothub.tech/p/phybench_model_perf> | <https://paperplothub.tech/files/cmofgw71pc3lygg0m/script.py> | arXiv:2504.16074 | Bar Chart | `paired-bar`, `category-colours`, `reference-line` | `A` | none, paired performance bar absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `ttrl_main_results` | <https://paperplothub.tech/p/ttrl_main_results> | <https://paperplothub.tech/files/cmofgw718os3p6yhk/script.py> | arXiv:2504.16084 | Bar Chart | `paired-bar`, `delta-arrow`, `percent-gain` | `A` | none, paired delta performance bar absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `prerl_behavior_bars` | <https://paperplothub.tech/p/prerl_behavior_bars> | <https://paperplothub.tech/files/cmofgw70s9c9jmmlu/script.py> | arXiv:2602.02488 | Bar Chart | `hatch-fill`, `multiplier-annotation`, `per-panel-color` | `A/F` | none, small-multiple comparative bar absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `prerl_passk_qwen4b` | <https://paperplothub.tech/p/prerl_passk_qwen4b> | <https://paperplothub.tech/files/cmofgw70irg0m7uy2/script.py> | arXiv:2602.02488 | Line Chart | `small-multiples`, `log-axis`, `pass-at-k` | `A/F` | none, small-multiple metric curve absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `prerl_behavior_panels` | <https://paperplothub.tech/p/prerl_behavior_panels> | <https://paperplothub.tech/files/cmofgw708r0hmjz8b/script.py> | arXiv:2602.02488 | Line Chart | `small-multiples`, `training-curve`, `per-panel-y-scale` | `A/F` | none, small-multiple metric trajectory absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `prerl_grad_metrics_hist` | <https://paperplothub.tech/p/prerl_grad_metrics_hist> | <https://paperplothub.tech/files/cmofgw6zxgdulnkdm/script.py> | arXiv:2602.02488 | Histogram | `histogram`, `stats-box`, `three-panel` | `H/F` | none, audited histogram or distribution QC panel absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `classwise_iou` | <https://paperplothub.tech/p/classwise_iou> | <https://paperplothub.tech/files/cmofgw6zdye9xaa4z/script.py> | no arXiv, community plot-from-image | Table | `table`, `heat-cell`, `plot-from-image` | `A/E` | `performance_summary_table_generic`, partial table-only fit | `candidate_gap` | PPH MIT surface; community plot-from-image provenance; link-only metadata; no script or image copied |
| `scatter_tsne` | <https://paperplothub.tech/p/scatter_tsne> | <https://paperplothub.tech/files/cmofgw6yrygl0f7w9/script.py> | arXiv:2509.24704 | Scatter Plot | `t-sne`, `annotation-box`, `latex` | `D` | `tsne_scatter_grouped` | `mapped_existing_template` | PPH MIT surface; link-only metadata; no script or image copied |
| `scatter_break` | <https://paperplothub.tech/p/scatter_break> | <https://paperplothub.tech/files/cmofgw6yb81usnnfi/script.py> | arXiv:2603.28052 | Scatter Plot | `broken-axis`, `pareto-frontier`, `multi-marker` | `A/H` | none, generic tradeoff scatter absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `radar_dora` | <https://paperplothub.tech/p/radar_dora> | <https://paperplothub.tech/files/cmofgw6xnmkj9teq4/script.py> | arXiv:2402.09353 | Radar / Polar | `radar`, `octagonal-grid`, `dual-series` | none | none | `reject_for_medical_display` | PPH MIT surface; link-only metadata; no script or image copied |
| `line_selfdistill_scale` | <https://paperplothub.tech/p/line_selfdistill_scale> | <https://paperplothub.tech/files/cmofgw6x6anvi8uvw/script.py> | arXiv:2601.20802 | Line Chart | `scaling-curve`, `confidence-band`, `latex` | `A/F` | none, generic scaling curve with interval absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `line_selfdistill_train` | <https://paperplothub.tech/p/line_selfdistill_train> | <https://paperplothub.tech/files/cmofgw6wtenggloby/script.py> | arXiv:2601.20802 | Line Chart | `confidence-band`, `ema-smoothing`, `latex` | `A/F` | none, smoothed training curve with interval absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `line_loss_inset` | <https://paperplothub.tech/p/line_loss_inset> | <https://paperplothub.tech/files/cmofgw6wa0pwpnwau/script.py> | arXiv:2602.08064 | Line Chart | `loss-curve`, `axis-arrows`, `L-spine` | `A/F` | none, inset and axis treatment only | `visual_style_only` | PPH MIT surface; link-only metadata; no script or image copied |
| `line_aime` | <https://paperplothub.tech/p/line_aime> | <https://paperplothub.tech/files/cmofgw6vtigmgelz1/script.py> | arXiv:2503.14476 | Line Chart | `training-curve`, `vertical-breakpoint`, `horizontal-reference` | `A/F` | none, annotated metric trajectory absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `bar_spice` | <https://paperplothub.tech/p/bar_spice> | <https://paperplothub.tech/files/cmofgw6v3sq6fscyw/script.py> | arXiv:2510.24684 | Bar Chart | `grouped-bars`, `hatch-fill`, `latex` | `A` | none, grouped performance bar absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |
| `bar_memevolve` | <https://paperplothub.tech/p/bar_memevolve> | <https://paperplothub.tech/files/cmofgw6u9fyt9ycnw/script.py> | arXiv:2512.18746 | Bar Chart | `paired-bars`, `delta-annotation`, `serif` | `A` | none, paired delta performance bar absent | `candidate_gap` | PPH MIT surface; link-only metadata; no script or image copied |

## Intake Summary

Landing status counts:

- `mapped_existing_template`: `3`
- `visual_style_only`: `3`
- `candidate_gap`: `18`
- `reject_for_medical_display`: `3`

Candidate gaps cluster into six repeatable intake lanes:

- generic performance bar families: paired bars, grouped bars, reference-line bars, delta-arrow bars;
- metric trajectory families: training curves, scaling curves, small-multiple metric curves, confidence bands, vertical breakpoints;
- distribution panels: strip/swarm plots and histogram panels with explicit statistics boxes;
- temporal composition: stacked area category evolution;
- heat-shaded performance tables beyond table-shell-only summaries;
- tradeoff scatter/Pareto views, with broken-axis handling requiring strict review before any promotion.

This intake does not promote any item into the active display board. Promotion would require a real MAS paper demand, an explicit input schema, deterministic QC boundaries, and a renderer path that does not depend on post-hoc layout repair.

Second-pass learning status is recorded in [paperplothub_exemplar_exhaustion_ledger.md](./paperplothub_exemplar_exhaustion_ledger.md). Current public PaperPlotHub learning is exhausted until a new public gallery item, a material metadata change, or a real MAS paper demand reopens one of the candidate-gap clusters through the promotion gate.
