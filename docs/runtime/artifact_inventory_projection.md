# Artifact Inventory Projection

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

## Projection 规则

- `study-progress` 应优先展示当前 blocker / next action 相关 artifact。
- `product-entry` 应展示可接管、可审阅、可下载或可继续运行的 artifact inventory。
- stale artifact 必须标注 freshness，不得和最新 truth surface 混在一起。
- inventory 是 projection，不是 authority；authority 仍在对应 ledger、publication eval、controller decision 或 paper surface。

## 与上游关系

上游 UI 的 attachment preview 和 file-link 能力说明：inspectability 是长期研究伙伴的核心能力。

`MAS` 吸收的是信息架构：所有关键研究文件都要能被前台投影、审阅、接管和恢复。
