# Publication Gate Policy

`MedAutoScience` 对 paper-required quests 默认执行三层发表门槛：

1. scout 后 gate
2. 首个 main result 后 gate
3. write 前 gate

核心原则：

- 不在弱结果上空转
- outline 也属于 write，不得绕 gate
- 若临床效用证据不足，不继续做论文式包装

## 当前主线的 gate 收紧方式

当 display template / materialization / QC 已经通过后，paper-required quest 不能直接视为可交付；还必须继续通过 reporting 与 publication 两层合同面。

### Reporting audit gate

`medical-reporting-audit` 负责检查 paper root 是否已经具备正式 reporting contract 所需的最低骨架。当前控制器会明确核对：

- `paper/medical_reporting_contract.json`
- `paper/display_registry.json`
- contract 中声明的 figure/table shell 文件
- 必需 display stub（例如 `cohort_flow.json`、`baseline_characteristics_schema.json`）
- `paper/reporting_guideline_checklist.json`

这里的 gate 重点不是“图画出来没有”，而是 reporting 所需的结构化审计面有没有正式落盘。

### Publication surface gate

`medical-publication-surface` 负责检查 manuscript-facing 语义合同是否已经闭合。当前正式必需项包括：

- `paper/methods_implementation_manifest.json`
- `paper/results_narrative_map.json`
- `paper/figure_semantics_manifest.json`
- `paper/derived_analysis_manifest.json`
- `paper/manuscript_safe_reproducibility_supplement.json`
- `paper/endpoint_provenance_note.md`

除此之外，publication surface 还会继续检查：

- figure / table catalog 与 narrative / semantics 覆盖是否一致
- manuscript-facing 文本里是否仍残留 forbidden manuscript terms
- endpoint caveat 是否真正应用到 manuscript-facing surface，而不只是“文件存在”

### 自动化边界

当前主线应明确区分两类 blocker：

1. **可由正式 controller / contract 自动吸收的 blocker**
   - 文件缺失
   - JSON 结构不完整
   - catalog / narrative / semantics 覆盖不一致
2. **必须回到真实 study / paper truth source 才能闭合的 blocker**
   - manuscript-safe wording
   - endpoint provenance 是否真的 applied
   - 结果叙事、方法说明、图注语义是否忠实对应真实 paper truth

因此，gate tighten 不是“补几个占位文件”就算完成；凡是 manuscript-facing truth 仍依赖真实 paper root 的项，都必须回到权威来源收口。

## 当前固定优先级

按当前 program 状态，固定顺序应为：

1. 先清 `003` 的 reporting / publication gate blocker
2. 再把 `001` 的 `submission_graphical_abstract` / `submission_companion` contract 缺口正式化
3. 最后回到 `002`，把 `Phase C / Phase D` 提升进真实课题 controller 主线

换言之，`003` 当前已经不再是 display 几何或模板缺口问题，而是 reporting / publication 合同面问题；`001` 与 `002` 则分别作为下一条 contract tighten 与真实课题 promotion 线。
