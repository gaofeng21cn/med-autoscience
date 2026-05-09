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
- 如果消费 mechanical projection，输出文案必须明确它只是 projection，不得写成科学审稿结论。
- 医学论文文体、reader flow、段落论证节奏、是否像工作汇报、claim restraint、讨论克制性等主观质量，只能由 AI reviewer-backed `medical_prose_review` 或 AI reviewer-backed `publication_eval/latest.json` 判定。
- Regex / pattern / deterministic scanner 可以保留为 `mechanical_safety_flags`、evidence snippets 或内部术语泄漏安全护栏；它们不得单独触发或清除 `medical_journal_prose_style_not_met` 这类主观文体 blocker。
- deterministic gate 可以继续阻断可验证事实缺口，例如缺文件、schema 不完整、claim-evidence 缺失、submission 包 stale、内部控制术语泄漏或 provenance 损坏。
- 不得用 hidden templates、heuristic-only reviewer verdict、scorecard-only ready verdict 或程序化正文/论文质量判断替代 AI reviewer artifact。
- 需要新增可调用面时，优先挂在现有 controller / publication-eval surface 下，不新增第二前台入口。

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
