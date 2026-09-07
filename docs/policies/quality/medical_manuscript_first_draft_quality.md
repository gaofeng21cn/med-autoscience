# Medical Manuscript First-Draft Quality Policy

Owner: `MedAutoScience`
Purpose: `first_draft_medical_content_quality`
State: `active_policy`
Machine boundary: 本页提供医学写作与审阅标准；它不实现 pre-draft runtime、validator 或 publication materializer。

## 目标与规范

初稿按临床问题、设计、证据、结果和解释组织，不能写成执行日志、修复历史或
投稿清单。ICMJE 提供医学原著结构，EQUATOR 帮助选择报告规范；按研究类型
使用 STROBE、TRIPOD/TRIPOD+AI、CONSORT、PRISMA 或 RECORD。
这些是领域审阅输入，不是固定章节扫描器。

写作前明确 clinical question、population、timepoint、outcome、analysis、
claim/evidence 和 display-to-claim 关系。缺失内容需记录 owner、研究影响和
route-back；质量债不禁止起草可消费的局部稿件，不能将其宣称完整或 ready。

## 初稿生成门槛

Before a first full draft is accepted as complete:

- reporting-guideline family must be resolved;
- section-level contract must be available to the writer;
- clinical question, target population, timepoint, outcome horizon, analysis plan, and display-to-claim map must be available before main text generation;
- claim-evidence mapping and display-to-claim mapping must be closed before Results prose is generated;
- controller checklists, run logs, progress prose, generic completion checklists, and packaging metadata cannot authorize manuscript-body quality;
- if verified evidence surfaces support a stronger paper shape, MAS routes back to bounded analysis or an analysis campaign instead of writing a light descriptive first draft;
- results narrative must answer clinical findings directly, then cite figures/tables as support;
- limitations must be written as clinical interpretation, not as claim-boundary/controller language;
- registry and observational manuscripts should state denominator, source, causal, prognostic, and treatment-response boundaries in compact clinical language; they must not repeat long defensive disclaimer lists across Abstract, Methods, Results, Discussion, and legends;
- objective facts available to the author, institution, data owner, or
  submission owner use a minimum local `[AUTHOR INPUT: ...]` annotation at the
  exact manuscript location where the final fact belongs; all such annotations
  are registered once and projected into the submission To-Do list;
- scientific evidence gaps must never be disguised as author-input annotations;
  they route back, constrain the claim, become a scientific limitation, or are
  omitted;
- terms such as `analytic surface` and `data surface` should be rewritten as analytic cohort, analytic dataset, registry dataset, measured fields, or available measurements;
- figure legends must explain the display for readers, not describe what reviewers can identify or what the figure itself "defines".
- internal correction provenance, debug history, and preprocessing repair history must not become the title, objective, Results, Discussion opening, conclusion, novelty claim, or figure-legend story. Corrected preprocessing definitions belong in Methods or table notes only when needed for reproducibility; the article body should report the final analysis estimates as the clean scientific story.

### 描述性表型 / treatment-gap 初稿门槛

这类稿件不能只写成“分成若干组并报告各组比例”。完整初稿验收前必须回答描述性 atlas 的医学发现问题：这些表型是否揭示了可审计的临床负担、记录用药覆盖、轨迹或服务差异模式。

以下内容缺失时，默认 route back 到 bounded analysis-campaign、figure/table repair、write 或 decision，而不是生成轻描述初稿：

- discovery contract：一句话写清 phenotype atlas 揭示的医学/服务复核模式，而不是只列 class count；
- hierarchy rationale：说明规则层级顺序的医学复核依据、未单列领域的处理依据、new-patient assignment 规则和 prespecification 状态；
- burden-medication discordance：至少有一个 phenotype x burden x recorded medication-coverage matrix，或明确 waiver；
- exact gap definitions：每个 gap 指标必须有 numerator、denominator、eligibility、time/index window、medication source、class mapping 和 non-causal interpretation label；
- medication-record sensitivity：当 medication record 不完整时，必须规划或完成 medication-field-present / any-recorded-medication sensitivity；否则只能写 documentation-sensitive review signal；
- diagnostic ascertainment：当 uncontrolled disease、hypertension、dyslipidemia、complication burden 或 phenotype assignment 来自结构化字段时，必须物化诊断/测量变量 ascertainment table；
- variable quality atlas：phenotype-defining variables 的 missingness、plausibility、semantic field checks 和 claim impact 必须进入 table 或 supplement；
- site/trajectory robustness：如果稿件要有“医学发现感”，优先检查 site-level variation、transition category、calendar-year / threshold / adult-known-age / age sensitivity；不要用 p-value pile-up 替代稳健性；
- unsupported evidence gap：calendar-year、repeated-visit、site variance 或中心差异没有当前证据时，必须成为 analysis-campaign gap 或 typed waiver，不能写成 Results 发现；
- service-priority contrast：gap 结果必须区分 rate、count 和 service-priority burden，避免把高比例小人群与低比例大人群混成同一结论；
- figure argument：cohort flow、phenotype/gap matrix、transition/site display 和 gap rate/count display 必须服务中心医学论点，rate 和 count 不得混成一个不可解释图；
- figure/table terminology and retention：Figure/Table、main/supplementary、rate/count、gap/coverage/review-signal 等术语必须一致；补充表图不能因主文压缩被静默丢弃，应保留在 supplement 或记录 typed blocker；
- terminology guardrail：没有 guideline-specific eligibility、contraindication、age/eGFR target 和 citation contract 时，不得把 recorded gap 写成 guideline nonadherence；优先用 recorded medication-coverage gap、treatment-review signal、burden-medication discordance。

### 预测模型外部验证初稿门槛

这类稿件不能只是一组 C-index / calibration 指标摘要。first full draft 的独立审阅必须核对以下 evidence 或明确的质量债：

- source model：模型来源、完整公式或系数表、变量编码、单位转换、5 年 baseline survival / absolute-risk extraction；
- validation cohort：数据年份、纳排、疾病定义、结局随访、5 年状态构建、删失/KM/IPCW 或二分类处理依据、缺失与 complete-case 策略；
- survey policy：NHANES 等复杂抽样数据必须写清 unweighted 边界，并在需要时规划 survey-weighted sensitivity；
- tables：Table 1 队列对比、Table 2 性能指标、按风险组/十分位的 grouped calibration table 必须有明确 shell、denominator、uncertainty 和 source refs；
- figures：development risk-bin occupancy 与 validation self-quantile calibration 不得混画；若 validation cohort 全落入 development low-risk bin，必须把 occupancy collapse 和 within-validation ranking 分开展示；
- calibration interpretation：极端 calibration slope、窄预测风险范围、O:E mismatch 必须解释为 risk-scale compression / baseline-risk mismatch / support mismatch 等受限解释，不能写成可部署绝对风险；
- decision curve：没有 verified threshold range、net-benefit calculation、calibration basis 和 clinical action scenario 时，不得保留主图 DCA，也不得在 Methods/Results 外包装成 clinical utility。


## 审阅与交付

独立 reviewer 检查稿件是否具有可复现 Methods、numeric Results/uncertainty、
正式医学图表、含关键结果的 Abstract、结果驱动 Discussion 和受证据约束的结论。
Objective author facts 按 [Submission Revision](../study-workflow/submission_revision_operating_contract.md)
保留最小局部 annotation 与唯一 registry；科学证据缺口不能伪装为 author input。

Review 不在自身会话内修正文稿；缺陷回到 authoring 或更早的 evidence/analysis owner。
变化后的 source 重新完成相应 Stage Review 与 Meta Review。
Final Handoff 的 exact bytes、generation 和 publication acceptance 由
[Stage Standard](../../runtime/stage_route_handoff_standard.md) 与
[Canonical Artifact](../../runtime/contracts/canonical_artifact_contract.md) 持有。
