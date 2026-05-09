# Canonical Artifact Contract

Artifact OS 的目标是让 manuscript、figures、tables 和 submission package 全部从 canonical sources 与 AI reviewer quality decision 重建。派生产物可以交付给人看，但不能反向成为 edit source 或 quality authority。

## Layers

1. canonical sources：study charter、evidence ledger、analysis outputs、AI reviewer quality decision、canonical blueprint。
2. derived manuscript：从 canonical sources 与 AI reviewer quality decision 生成 manuscript、tables、figures。
3. submission package：controller-authorized delivery projection。
4. human handoff mirror：给人工审阅或提交使用的只读镜像。

## Rule

`manuscript/current_package/`、`artifacts/final/`、`current_package.zip`、`submission_minimal/` 都不是 edit source，也不是 quality authority。任何 revision 或 reviewer feedback 必须回到 canonical sources 和 MAS quality/runtime chain，由 AI reviewer quality decision 重新授权后再生成派生产物。

在 `submission-package.v2` layout 下，`audit/*` 与 `reproducibility/*` 是交付包内的 traceability projection，用于核查来源、审计和复现索引；它们不把交付包提升为 edit source、quality authority 或 dispatch authority。

## Rebuild Requirements

- manuscript 必须从 canonical sources + AI reviewer quality decision 重建。
- figures 必须从 canonical sources + AI reviewer quality decision 重建。
- tables 必须从 canonical sources + AI reviewer quality decision 重建。
- submission package 必须从 canonical sources + AI reviewer quality decision 重建。

派生 projection 可以作为人读 handoff、提交镜像或 traceability output 使用；不能作为后续编辑、质量关闭、投稿授权的根。

`artifact_rebuild_integrity_contract` 固定每类生成产物的 rebuild proof：`source_refs`、`fingerprint_refs`、`quality_decision_ref`、`controller_decision_ref` 和 `generated_artifact_role` 必须同时存在。缺任何一项只能说明 rebuild proof 不完整，不能把当前包、DOCX/PDF、zip 或 `submission_minimal/` 提升成质量或投稿 authority。

终局止损后的文件精简不改变这条 authority 规则。即使 `study_macro_state` 已进入不可重开 `TerminalAbandon`，canonical source、data release、audit log 与 human handoff mirror 仍保持在线；runtime ephemeral 只能在 manifest、sha256、restore index 与 restore proof 成立后进入后续 archive/compact apply。派生 projection 的移除也必须先证明 canonical source 可重建。
