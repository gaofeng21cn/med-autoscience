# AI-first Quality Boundary Policy

本 policy 固定 MAS 质量判断面的 owner 边界。它来自 RCA AI-first 修复后的跨项目经验：结构化 pack、schema、gate 和 scorecard 只能传递约束、引用和机械状态；创作判断、科学审稿判断、论文质量判断必须由 AI reviewer / author artifact 持有。

## Owner boundary

- `publication_gate`、`medical_reporting_audit` 和类似 deterministic controller surface 只持有机械完整性、交付 gate、blocker 与 projection。
- 这些机械面 materialize 的 `publication_eval/latest.json` 必须标记为 `assessment_provenance.owner=mechanical_projection`，并设置 `ai_reviewer_required=true`。
- AI reviewer-backed `publication_eval/latest.json` 必须来自 AI reviewer 读取 manuscript、evidence ledger、review ledger 与 study charter 后写出的 artifact。
- AI reviewer-backed record 必须使用 `medical_publication_critique_v1`，并标记 `assessment_provenance.owner=ai_reviewer` 与 `ai_reviewer_required=false`。
- AI reviewer-backed record 还必须携带 `medical_publication_ai_reviewer_os_v1` 结构化审稿痕迹，包括输入 bundle、rubric scores、decision matrix、provenance checks 与 route-back decision；缺少该 trace 时不得写回质量权威。

## Downstream read rule

任何会输出 reviewer-first readiness、bundle-only remaining、finalize-ready、submission-facing 质量闭环或 study-quality ready 语义的 reader，都必须先检查 `assessment_provenance`。

缺少 provenance、provenance 损坏，或 owner 不是 `ai_reviewer` 时，下游只能输出：

- `review_required`
- `projection_only`
- AI reviewer required blocker
- 机械 gate/blocker/projection 摘要

不得输出：

- reviewer-first ready
- bundle-only remaining
- finalize-ready
- submission-facing quality closure
- study-quality ready verdict

## Implementation rule

- 新增质量 read-model 时，先决定它消费的是 AI reviewer judgment 还是 mechanical projection。
- 如果消费 AI reviewer judgment，入口必须 fail-closed 检查 `assessment_provenance.owner=ai_reviewer` 和 `ai_reviewer_required=false`。
- 如果入口会投影 `finalize`、`bundle-only remaining`、`human-review ready` 或 `submission-facing closure`，还必须确认 `quality_assessment.medical_journal_prose_quality.status=ready`。缺失、`underdefined`、`partial` 或 `blocked` 都表示 AI reviewer 主观稿件质量尚未闭合，只能 route back 到同一论文线的 `review` / AI reviewer workflow。
- 如果消费 mechanical projection，输出文案必须明确它只是 projection，不得写成科学审稿结论。
- MAS private authority surface 必须声明 `judgment_mode`。`ai_first_stage_gate` 和 `ai_first_record_validator` 必须消费独立 reviewer/auditor record；`mechanical_guard` 和 `domain_authority_refs` 不得输出医学 ready/pass、publication readiness、source readiness、route acceptance 或 artifact quality verdict。
- 对 `*_verdict`、`*_decision`、`*_authorization` 这类 surface，缺少独立 reviewer/auditor invocation、task/context record、receipt、AI reviewer record 或 quality-pack refs 时，只能 typed blocker / route-back。
- 医学论文文体、reader flow、段落论证节奏、是否像工作汇报、claim restraint、讨论克制性等主观质量，只能由 AI reviewer-backed `medical_prose_review` 或 AI reviewer-backed `publication_eval/latest.json` 判定。
- `是否像高质量医学论文` 可以作为 OPL Agent Lab 的自进化目标，但只能以 MAS refs-only suite 暴露 scorecard ref、evidence refs、review refs 和 improvement candidate refs。Agent Lab 不能把自身评分、脚本检查、completion summary 或 provider success 投影成 `medical_journal_prose_quality=ready`、submission readiness 或 publication quality closure。
- Agent Lab / OPL meta-agent 的 developer patch work order 必须显式声明 `ai_native_expert_judgment_first`：AI reviewer 原生专家判断优先，contract、rubric、schema 和 deterministic guard 只定义下限、route-back 和 typed blocker，不能作为质量上限或 ready 授权。
- 交付物反馈进入自进化 suite 时，必须跨 `review`、`analysis-campaign`、`write`、`figure-polish` 与 `publication-gate` 扫描漏洞，防止 reviewer feedback 在 stage 之间丢失、方法学 blocker 被降格为 prose repair、机械 gate 覆盖 AI reviewer 判断，或 delivery/package 状态抢跑质量 route-back。
- 交付物反馈进入自进化 suite 时，developer work order 必须带 study-family-specific quality targets。预测模型外部验证论文可以暴露 HDL harmonization、NHANES framing、calibration/risk-collapse 等目标；observational phenotype / treatment-gap 论文必须暴露 phenotype derivation transparency、recorded treatment-gap terminology、BP/data-quality assessment、baseline characteristics table、formal figures/tables、numeric abstract、restrained prose、reference style、claim-evidence alignment 和 method/data-error route-back 目标。错误 family target 泄漏属于 MAS Agent Lab suite defect，不能交给 OMA 或 OPL 用宽松兼容去吸收。
- internal error、debug history、runtime incident 和 provider/executor trace 只能作为 diagnostics、incident learning 或 mechanism patch evidence refs。它们不得进入论文 main story，不得支撑医学 claim，也不得替代 evidence ledger、review ledger 或 AI reviewer quality verdict。
- 外部大模型人工评估、导师意见或审稿意见可以作为 `reviewer_revision` / task intake / reviewer feedback ref 进入该 scorecard，但它们必须回到 MAS AI reviewer workflow 和 owner route 后才能关闭质量判断；不得直接改写 `publication_eval/latest.json` 或 current package。
- Regex / pattern / deterministic scanner 可以保留为 `mechanical_safety_flags`、evidence snippets 或内部术语泄漏安全护栏；它们不得单独触发或清除 `medical_journal_prose_style_not_met` 这类主观文体 blocker。
- deterministic gate 可以继续阻断可验证事实缺口，例如缺文件、schema 不完整、claim-evidence 缺失、submission 包 stale、内部控制术语泄漏或 provenance 损坏。
- internal methodology repair provenance 泄漏属于可验证安全护栏：当修正路线被写成摘要、结果、结论、贡献或图注故事时，mechanical flag 可以阻止 AI reviewer clear verdict 被物化；它仍然不能给 ready，后续修改必须回到 write / AI reviewer owner chain。
- literature hygiene 的 key / provenance 检查只能证明 citation key、ledger provenance、重复项和基本同步关系没有机械漂移。它不能授权 reference style、医学引用充分性、文献选择合理性或 publication-quality bibliography。
- rendered bibliography audit 可以阻断已渲染参考文献中的可验证样式缺陷，例如 initials-first 作者缩写、明显不规范的期刊名大小写或缺少可用 DOI/URL 的提示；它是 publication-quality 输入和 safety flag，不替代 AI reviewer、医学质量 owner 或投稿前人工/作者判断。
- 003 暴露的初稿质量缺陷必须按 MAS 层边界修复：机械 hygiene 负责发现可重放的 citation/rendered-reference 缺陷，AI reviewer 负责审稿式质量判断，study / publication owner 负责最终路线和质量裁决。任何一层都不得把自己的 projection 写成完整医学质量结论。
- 不得用 hidden templates、heuristic-only reviewer verdict、scorecard-only ready verdict 或程序化正文/论文质量判断替代 AI reviewer artifact。
- 需要新增可调用面时，优先挂在现有 controller / publication-eval surface 下，不新增第二前台入口。
- 外部 skill/workflow 材料只能作为 clean-room 学习背景。reviewer response、data、Figure/display、source-grounded deliverable patterns 必须吸收到 MAS stage quality pack、AI reviewer、evidence/review ledgers、publication gate、controller decisions、Stage Deliverable Review Page / Index 或 Portal read model；不得把 vendor prompt、runtime、HTML exporter、citation UI、skill runner 或 checklist 写成质量 owner、publication authority、default skill source 或外部 runtime dependency。nature-skills clean-room 学习已经落到可用的 `stage_quality_pack_contract`、stage prompts / quality gate、product-entry / descriptor refs 和 focused tests；剩余验收是 live paper-line evidence tail，而不是再引入外部 runner 或 authority。当前 closeout 见 [Nature-skills Learning Intake](../../references/mainline/nature_skills_learning_intake.md)。

## AI-first drift audit

`ai_first_drift_audit` 是 doctor / meta test 可消费的稳定回归审计面。它扫描的不是单篇 study 产物，而是 repo-level contract 是否再次漂回“机械 gate 判断质量”的实现方式。

固定审计类别包括：

- `ready_wording_without_ai_provenance`：任何 ready / finalize / bundle-only / submission-facing 语义缺少 AI reviewer provenance 前置检查。
- `mechanical_projection_as_quality`：publication gate、reporting audit、coverage 或 scorecard 把机械 projection 写成质量权威。
- `pattern_only_subjective_blockers`：regex / pattern / scanner 直接触发或清除医学文体、reader flow、claim restraint 等主观 blocker。
- `mechanical_stop_loss`：stop-loss 由 marker、字符串或 gate status 直接决定，而不是由 AI reviewer-owned publishability decision 决定。
- `mechanical_blueprint_as_canonical`：机械汇总越权写入 canonical `paper/medical_manuscript_blueprint.json`。
- `coverage_as_quality` / `coverage-as-quality`：MDS manuscript coverage 被解释为 quality-ready 或 submission-ready。
- `stale_ai_cache`：paper contract health cache 没有纳入 AI review、blueprint、publication eval、style corpus、review ledger 等 AI-first surfaces。
- `prompt_only_gates`：质量边界只写在 prompt / skill 文案里，没有结构化 contract 或测试保护。
- `ai_reviewer_os_trace_missing`：AI reviewer 只输出结论或自然语言审稿意见，缺少结构化输入、rubric、decision matrix 与 provenance trace。

## DM002 质量路由事故复盘

DM002 暴露的顶层缺陷不是英文润色能力不足，也不是缺少一条程序化 manuscript scanner。真实问题是 owner chain：`publication_gate` 已 clear，`current_required_action=continue_bundle_stage`，但 AI reviewer 的 `medical_journal_prose_quality` 仍是 `underdefined`；下游 action 决策却继续把线路推进到 `finalize` / human-facing bundle。这等于让交付 gate 覆盖了主观医学论文质量 owner。

修复口径：

- `medical_prose_review_status` 缺失时按 `underdefined` 处理。
- clear bundle-stage gate 只有在 `medical_journal_prose_quality.status=ready` 时才能进入 `finalize`。
- 未 ready 时推荐动作必须是同线 `route_back_same_line`，`route_target=review`，由 AI reviewer / prose review workflow 关闭稿件质量维度。
- 机械检查、pattern scan 和 completeness projection 只能提供 evidence、blocker 或 safety flag，不能授权初稿质量、人工审阅 readiness、定稿或投稿面 closure。

DM002 后续的高质量医学论文目标应进入 MAS/Agent Lab 自进化闭环：HDL 单位和敏感性分析、模型可复现信息、Table 1 / Table 2、统计不确定性、校准图和风险分布图、NHANES unweighted framing、内部质量控制语言泄漏等问题可以作为 improvement candidate refs 暴露给 Agent Lab；但最终是否达到高质量医学论文口径，仍必须由独立 AI reviewer 读取当前稿件和 evidence refs 后给出 current verdict。

外部工程依据：

- NIST AI RMF：把质量 owner、测量、治理和管理闭环显式化，避免高风险判断藏在单个 gate 输出中。
- EQUATOR：医学报告规范必须前置进入写作合同，而不是在投稿包阶段才做机械补救。
- G-Eval：LLM reviewer 适合在结构化 rubric、source provenance 和可审计 response contract 下给 judgment；不应把隐式分数或字符串 marker 当质量判断。
- Google SRE toil elimination：重复人工论文修复是可靠性 toil，应通过系统设计消除，而不是用更快的机械判定把返工推到后面。

## Verification

后续涉及论文质量、publication eval、study quality 或 finalize readiness 的改动，至少检查：

- `tests/test_ai_first_drift_audit.py`
- `tests/test_ai_first_quality_boundary.py`
- `tests/test_publication_eval_latest.py`
- `tests/test_study_quality.py`
- `tests/test_evaluation_summary.py`
- `make test-meta`
- `scripts/verify.sh`
