# Medical Figure Route Cookbook

Owner: `MedAutoScience`
Purpose: `Maintain the human-readable paper-facing figure route cookbook for MAS delivery work.`
State: `active_support`
Machine boundary: Human-readable delivery route taxonomy only. Dispatchable figure-route truth remains in `src/med_autoscience/figure_routes.py`, domain-handler figure-route contracts, renderer/template source, tests, contracts, generated artifacts, and audit receipts.

这份 cookbook 学习 `DeepScientist` paper-plot refresh 的做法，但只吸收“图形路线要有可复用 cookbook、输入 contract 和审阅标准”的方法。

这里的 `route` 指 paper-facing display route family，不是 MAS domain-handler 或 OPL dispatcher route id。当前可解析的 figure-route metadata 只允许 `figure_script_fix:<figure-id>` 和 `figure_illustration_program:<figure-id>`；旧 `sidecar:<figure-id>`、autofigure 或外部绘图 route 已退役并 fail closed。若需要判断 dispatchable route、renderer family 或 artifact-authority 边界，读 [Domain Handler Figure Routes](../contracts/domain_handler_figure_routes.md)、`src/med_autoscience/figure_routes.py` 和 focused tests。

## 稳定医学图形路线

| Paper-facing route family | 用途 | 最小输入 | 审阅重点 |
| --- | --- | --- | --- |
| `baseline_table` | Table 1 / cohort baseline | cohort groups、变量字典、缺失率 | 单位、分组、缺失、临床可读性 |
| `forest_effect` | subgroup / interaction / sensitivity | effect estimate、CI、subgroup labels | CI、reference、multiplicity、方向一致性 |
| `kaplan_meier` | survival comparison | time、event、group、at-risk counts | censoring、at-risk table、time horizon |
| `calibration_curve` | prediction calibration | predicted risk、observed risk、bins | slope/intercept、置信区间、过拟合 |
| `decision_curve` | clinical utility | threshold、net benefit、treat-all/none | threshold range、临床解释、基线策略 |
| `shap_summary` | explainability | feature values、SHAP values、cohort scope | label、direction、clinical plausibility |
| `trajectory_panel` | longitudinal course | time axis、measurements、grouping | 时间定义、平滑、个体/群体区别 |

## Cookbook 规则

- 每条 cookbook route family 都必须声明医学问题，而不是只声明 chart type。
- 每条 cookbook route family 都必须绑定数据输入、claim、caption、reviewer concern 和 freshness status。
- display refresh 必须能回指 source / analysis / write owner route 的 evidence refs、typed blocker 或 receipt；仅有 route metadata 不构成 paper closure。
- 图形模板可以复用，但 caption 和 clinical interpretation 不能模板化偷懒。
- Cookbook route family 可以帮助选择 display contract，但不能授权 source readiness、publication quality、submission readiness、artifact mutation、`current_package` freshness、paper closure、domain ready 或 production ready。

## 不吸收范围

上游 AI benchmark 图模板不直接进入 MAS。只有能服务医学论文展示、reviewer concern 或 audited display contract 的路线才进入 cookbook；进入 cookbook 也只表示概念族可追踪，不表示当前模板已实现、已通过 quality gate 或可提交。
