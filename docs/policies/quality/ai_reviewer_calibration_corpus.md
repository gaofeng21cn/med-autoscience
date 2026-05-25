# AI Reviewer Calibration Corpus

Owner: `MedAutoScience`
Purpose: `Define stable MAS quality, publication, evidence, and reviewer policy boundaries.`
State: `active_policy`
Machine boundary: Human-readable policy only; quality verdicts, publication truth, evidence state, and reviewer receipts remain in MAS authority functions, contracts, artifacts, ledgers, and owner receipts.

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
- thin first draft。
- overstrong claim。
- missing reviewer trace。
- coverage as quality。
- mechanical gate as quality。

## Target Journal Writing Layer

`target_journal_writing_layer` 是 AI reviewer operating system 的质量上下文，不是新入口。它必须覆盖 target journal family、near-neighbor style corpus、section plan、claim-to-paragraph map、display-to-claim map 与 restrained language strategy。

near-neighbor corpus 只能作为 style and structure calibration，不能供应 claim，不能覆盖 evidence ledger。restrained language strategy 必须绑定 claim-evidence alignment，且禁止从风格样例推出更强医学结论。

## Real-study Soak Matrix

`real_study_soak_matrix` 是 calibration corpus 内的 soak proof surface，用来证明真实 study 能穿过 literature scout、line selection、main analysis、bounded analysis、route-back、stop-loss、revision reopen、runtime recovery、finalize rebuild 与 final pre-submission audit。

soak matrix 只提供质量回归与 route-back 证据。它要求 AI reviewer provenance、route-back trace 与 quality regression projection，但 mechanical gate 仍只能作为 evidence-only 输入，不能授权 publication quality。

## Pre-draft Materialization

`paper/pre_draft_writing_readiness.json` 是正式写作前 surface。它必须读取 study charter、evidence ledger、review ledger、canonical medical manuscript blueprint 与 AI reviewer-backed publication eval。reporting checklist、artifact inventory 和 claim-evidence map 只作为 supporting mechanical inputs。

readiness verdict 必须绑定 `assessment_provenance.owner=ai_reviewer`、`assessment_provenance.ai_reviewer_required=false`、`assessment_provenance.policy_id=medical_publication_critique_v1` 与 `reviewer_operating_system` trace。缺少 AI reviewer provenance 时，该 surface fail-closed 到 `review_required` 或 `route_back_required`，不能授权 full manuscript drafting。

机械输入只能是 evidence-only：它们可以证明 checklist、coverage、inventory 或 claim map 的事实状态，不能生成 ready verdict，不能关闭质量 gate，不能替代 reviewer provenance。

## AI Reviewer Currentness Contract

AI reviewer 的主观医学质量判断必须绑定它实际审阅的输入快照。`medical_prose_review` 的 provenance 必须记录 `request_ref`、`request_digest`、`manuscript_ref` 与 `manuscript_digest`；`publication_eval/latest.json` 的 `reviewer_operating_system` 必须记录 `currentness_checks.medical_prose_review`。如果最新 request digest、manuscript digest 或 reviewer trace 不一致，MAS 必须 fail-closed 回到 `ai_reviewer` / `write` / `review` owner，不能把旧 prose review 重新包装成 ready。

AI reviewer 的 clear verdict 还必须包含 IMRAD 关键段落的 section-level diagnosis 和 representative rewrite evidence。空泛的 “looks formal enough” 或只给概括性 ready 的回答不能关闭 `medical_journal_prose_quality`。

质量闭合不等于交付投影已刷新。bundle-stage 或 human-facing package 需要继续绑定 `current_package_freshness` proof；该 proof 的 `source_eval_id` 必须匹配当前 AI reviewer publication eval。旧 package freshness、旧 zip、旧 DOCX 或旧 `manuscript/current_package` 不能因为新的 `publication_eval` ready 标签而被视为最新论文。

## Owner-Route Regression Contract

DM002/DM003 暴露的 stale reviewer record、pending reviewer request、medical prose write route-back、unit harmonization rerun、package freshness 和 typed closeout 问题必须进入 owner-route protocol regression。每个质量 blocker 需要在 MAS registry 中声明 owner、allowed action、required output、forbidden surfaces 和 regression refs；未注册 reason 不得生成 ready dispatch。

Agent Lab / opl-meta-agent 可以消费这些 refs 生成 developer work order，但不能消费 study truth body、AI reviewer verdict body、paper body 或 package body，也不能把 suite pass 写成 publication-ready。回归 suite 的成功标准是 owner route、request lifecycle、dispatch blocker、typed closeout contract 和 no-forbidden-write proof 正确投影；医学质量闭合仍必须由当前 AI reviewer-backed `publication_eval/latest.json`、publication gate、owner receipt 或 typed blocker 决定。

## Drift Audit

`ai_first_drift_audit` 必须检查 calibration corpus 与 pre-draft materialization contract 的代码 surface。验收点包括：六类历史返工模式仍在 corpus 中，prompt-only calibration 被禁止，AI reviewer provenance 字段仍是结构化要求，pre-draft readiness 缺 provenance 时 fail-closed，mechanical supporting inputs 只能提供 evidence-only。
