# AI-first Quality Boundary Policy

本 policy 固定 MAS 质量判断面的 owner 边界。它来自 RCA AI-first 修复后的跨项目经验：结构化 pack、schema、gate 和 scorecard 只能传递约束、引用和机械状态；创作判断、科学审稿判断、论文质量判断必须由 AI reviewer / author artifact 持有。

## Owner boundary

- `publication_gate`、`medical_reporting_audit` 和类似 deterministic controller surface 只持有机械完整性、交付 gate、blocker 与 projection。
- 这些机械面 materialize 的 `publication_eval/latest.json` 必须标记为 `assessment_provenance.owner=mechanical_projection`，并设置 `ai_reviewer_required=true`。
- AI reviewer-backed `publication_eval/latest.json` 必须来自 AI reviewer 读取 manuscript、evidence ledger、review ledger 与 study charter 后写出的 artifact。
- AI reviewer-backed record 必须使用 `medical_publication_critique_v1`，并标记 `assessment_provenance.owner=ai_reviewer` 与 `ai_reviewer_required=false`。

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
- 不得用 hidden templates、heuristic-only reviewer verdict、scorecard-only ready verdict 或程序化正文/论文质量判断替代 AI reviewer artifact。
- 需要新增可调用面时，优先挂在现有 controller / publication-eval surface 下，不新增第二前台入口。

## Verification

后续涉及论文质量、publication eval、study quality 或 finalize readiness 的改动，至少检查：

- `tests/test_ai_first_quality_boundary.py`
- `tests/test_publication_eval_latest.py`
- `tests/test_study_quality.py`
- `tests/test_evaluation_summary.py`
- `make test-meta`
- `scripts/verify.sh`
