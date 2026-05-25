# Artifact Inventory Projection

Owner: `MedAutoScience`
Purpose: `Explain MAS runtime projection and read-model semantics for human maintainers.`
State: `active_runtime_support`
Machine boundary: Human-readable projection support only; projection truth remains in source, tests, CLI/read-model output, runtime artifacts, ledgers, and owner receipts.

这份 contract 学习 `DeepScientist` 的 attachment preview、workspace file links 和 inspectable workspace，但在 `MAS` 中落为 study-level artifact inventory。

## 目标

用户不应只看到“研究在运行”。用户应能看到当前 study 的可接管文件清单：论文、图表、数据、日志、ledger、publication gate、delivery package 和恢复点。

## Inventory fields

每个 artifact inventory item 至少包含：

- `artifact_id`
- `artifact_type`
- `title`
- `path`
- `owner_surface`
- `freshness_status`
- `stage_ref`
- `resume_relevance`
- `handoff_note`

生命周期投影还会使用 `role`、`lifecycle`、`cleanup_candidate_action` 与 `cleanup_blockers`。稳定角色包括 `canonical_source`、`runtime_ephemeral`、`derived_projection`、`human_handoff_mirror`、`data_release`、`cold_archive`、`audit_log` 与 `cache`。这些字段只是 retention plan 的输入，不把 inventory 提升为 artifact authority。

## artifact_type

稳定类型包括：

- `manuscript`
- `table`
- `figure`
- `data_manifest`
- `evidence_ledger`
- `review_ledger`
- `publication_eval`
- `controller_decision`
- `runtime_log`
- `delivery_package`

`delivery_package` 使用 `submission-package.v2` 时，inventory 应把 package root、`audit/` 和 `reproducibility/` 分开投影：根目录是人读投稿文件，`audit/` 是审计追踪材料，`reproducibility/` 是来源签名和复现索引。三者仍然都是 projection，不是新的 authority root。

## delivery_package layout status

Inventory 对 delivery package 统一投影三类 layout status：

- `v2`：package root 下有 `audit/` 或 `reproducibility/`。用户打开投稿文件时看 package root 里的 `manuscript.docx`、`paper.pdf`、`references.bib`、`figures/`、`tables/`；核查 audit/ 时看 `submission_manifest.json`、`evidence_ledger.json`、`review_ledger.json`、`study_charter.json`；核查 reproducibility/ 时看 `source_signature.json`、`source_relative_paths.json` 和可选 `analysis_manifest.json`。
- `legacy`：审计文件仍在 package root、`review/` 或 `controller/` 等旧位置。用户可以打开根目录投稿文件，但 audit/reproducibility 核查应先按 legacy root audit files 标记读取，并进入只读回填计划。
- `unknown`：只发现 DOCX/PDF/ZIP 等生成输出，无法确认 package root、audit/ 或 reproducibility/ 边界。用户可以直接打开该文件检查内容，但必须把 layout 当作未分类投影处理，等待 controller 从 canonical sources 重新生成 v2 package。

所有三类 delivery package 文件都不是 edit source。稿件修改、审稿意见吸收、质量关闭和投稿授权必须回到 controller-authorized `paper/` sources、evidence/review ledger、publication gate 与 controller decision，再重新生成 projection。

## Projection 规则

- `study-progress` 应优先展示当前 blocker / next action 相关 artifact。
- `product-entry` 应展示可接管、可审阅、可下载或可继续运行的 artifact inventory。
- stale artifact 必须标注 freshness，不得和最新 truth surface 混在一起。
- inventory 是 projection，不是 authority；authority 仍在对应 ledger、publication eval、controller decision 或 paper surface。

## 与上游关系

上游 UI 的 attachment preview 和 file-link 能力说明：inspectability 是长期研究伙伴的核心能力。

`MAS` 吸收的是信息架构：所有关键研究文件都要能被前台投影、审阅、接管和恢复。
