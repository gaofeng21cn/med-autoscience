# Delivery 文档

Owner: `MedAutoScience`
Purpose: `delivery_support_index`
State: `active_index`
Machine boundary: 本页导航；真实交付 authority 归当前 artifact、Review 与 MAS owner receipt。

| 目的 | 入口 |
| --- | --- |
| canonical source、派生包与重建 | [Canonical Artifact](../runtime/contracts/canonical_artifact_contract.md) |
| 同线修订、作者事实和投稿包 | [Submission Revision](../policies/study-workflow/submission_revision_operating_contract.md) |
| 医学图表 | [Medical Display](./medical-display/README.md) |
| Exact Review 与 Final Handoff | [Stage Standard](../runtime/stage_route_handoff_standard.md) |
| 文献与来源完整性 | [Research Integrity](../runtime/contracts/research_integrity_layer.md) |
| inspection package 用户边界 | [Product](../product/README.md) |
| artifact 保留与恢复 | [Retention](../runtime/contracts/artifact_retention_operations_contract.md) |

交付资源由 Package bundled 或 host-provisioned exact path 提供；
缺失时按 `contracts/submission-resource-requirements.json` 返回资源 request。
MAS 不自行下载模板或建立 fallback transport。资源存在或 materialization 成功
不能证明 publication/submission ready。
