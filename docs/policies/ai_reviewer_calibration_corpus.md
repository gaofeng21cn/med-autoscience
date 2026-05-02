# AI Reviewer Calibration Corpus

本 policy 把历史高成本论文修复转化为稳定回归语料。目标是让 MAS 在写作前和 finalize 前自动识别同类问题，而不是把返工推到投稿包阶段。

## Authority

- owner：MedAutoScience Quality OS。
- 机械 projection 只能提供证据和阻塞摘要。
- 主观医学质量、可发表性、写作质量与 submission-facing readiness 必须由 AI reviewer artifact 持有。
- calibration 不能停留在 prompt-only 提醒；语料、provenance 要求、route-back 规则和 fail-closed 条件必须是 repo-tracked contract。

## Initial Case Families

- mechanical ready without AI reviewer provenance。
- thin first draft despite richer data asset。
- coverage complete but quality unreviewed。
- medical prose review route-back。
- claim strength exceeds evidence。
- reviewer trace missing。

## Pre-draft Materialization

`paper/pre_draft_writing_readiness.json` 是正式写作前 surface。它必须读取 study charter、evidence ledger、review ledger、canonical medical manuscript blueprint 与 AI reviewer-backed publication eval。reporting checklist、artifact inventory 和 claim-evidence map 只作为 supporting mechanical inputs。

readiness verdict 必须绑定 `assessment_provenance.owner=ai_reviewer`、`assessment_provenance.ai_reviewer_required=false`、`assessment_provenance.policy_id=medical_publication_critique_v1` 与 `reviewer_operating_system` trace。缺少 AI reviewer provenance 时，该 surface fail-closed 到 `review_required` 或 `route_back_required`，不能授权 full manuscript drafting。

机械输入只能是 evidence-only：它们可以证明 checklist、coverage、inventory 或 claim map 的事实状态，不能生成 ready verdict，不能关闭质量 gate，不能替代 reviewer provenance。

## Drift Audit

`ai_first_drift_audit` 必须检查 calibration corpus 与 pre-draft materialization contract 的代码 surface。验收点包括：六类历史返工模式仍在 corpus 中，prompt-only calibration 被禁止，AI reviewer provenance 字段仍是结构化要求，pre-draft readiness 缺 provenance 时 fail-closed，mechanical supporting inputs 只能提供 evidence-only。
