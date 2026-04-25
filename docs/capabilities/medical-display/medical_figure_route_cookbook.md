# Medical Figure Route Cookbook

这份 cookbook 学习 `DeepScientist` paper-plot refresh 的做法，但只吸收“图形路线要有可复用 cookbook、输入 contract 和审阅标准”的方法。

## 稳定医学图形路线

| Route | 用途 | 最小输入 | 审阅重点 |
| --- | --- | --- | --- |
| `baseline_table` | Table 1 / cohort baseline | cohort groups、变量字典、缺失率 | 单位、分组、缺失、临床可读性 |
| `forest_effect` | subgroup / interaction / sensitivity | effect estimate、CI、subgroup labels | CI、reference、multiplicity、方向一致性 |
| `kaplan_meier` | survival comparison | time、event、group、at-risk counts | censoring、at-risk table、time horizon |
| `calibration_curve` | prediction calibration | predicted risk、observed risk、bins | slope/intercept、置信区间、过拟合 |
| `decision_curve` | clinical utility | threshold、net benefit、treat-all/none | threshold range、临床解释、基线策略 |
| `shap_summary` | explainability | feature values、SHAP values、cohort scope | label、direction、clinical plausibility |
| `trajectory_panel` | longitudinal course | time axis、measurements、grouping | 时间定义、平滑、个体/群体区别 |

## Cookbook 规则

- 每条 figure route 都必须声明医学问题，而不是只声明 chart type。
- 每条 figure route 都必须绑定数据输入、claim、caption、reviewer concern 和 freshness status。
- display refresh 必须能回指 baseline refresh、bounded analysis 或 write repair 的 route outcome。
- 图形模板可以复用，但 caption 和 clinical interpretation 不能模板化偷懒。

## 不吸收范围

上游 AI benchmark 图模板不直接进入 MAS。只有能服务医学论文展示、reviewer concern 或 publication gate 的路线才进入 cookbook。
