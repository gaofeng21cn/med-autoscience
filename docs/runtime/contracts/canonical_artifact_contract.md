# Canonical Artifact Contract

Owner: `MedAutoScience`
Purpose: `canonical_source_and_derived_artifact_boundary`
State: `active_runtime_support`
Machine boundary: artifact contracts、generation manifest、owner receipts 与真实 workspace bytes 持有机器事实。

## 编辑源与交付物

`manuscript/` 持有可编辑论文 source；charter、analysis、evidence、claim 和 reference
材料各自在 canonical owner 下维护。DOCX/PDF、ZIP 和 `submission/` 是派生产物，
不能反向成为编辑源或 quality authority。修订先回到缺陷所属 Stage 的 canonical source，
重建后重新评估受影响 review scope。

`submission-package.v2` 内的 `audit/` 与 `reproducibility/` 仅提供来源和复现投影。
source signature、source path/hash inventory、analysis/software manifest 和 lineage
graph 帮助定位与重建，不能取代医学、统计、引用或 publication verdict。

## Owner 与发布投影

MAS 持有 artifact mutation、quality/publication 与 memory authority。
OPL Framework 提供通用 tree inventory、ZIP、hash、transport、retention 和原子 projection；
它不能决定医学质量或签发 submission readiness。

Final Handoff 仅封装 exact reviewed bytes。MAS owner receipt 绑定 publication generation、
status、evaluation、next-action 与 projection manifest 后，Framework 才运输授权的完整树。
失败不能留下半填充的 preferred submission root；transport 成功也不提升领域 verdict。

## 重建与保留

每次 artifact 变化记录 source、analysis/environment、evidence/claim、review 与 generation
lineage；缺失证明时显式记录质量债、route-back 或真实 authority blocker。
研究进展不等于 publication/submission acceptance。

论文关闭后的返修依照 [Submission Revision](../../policies/study-workflow/submission_revision_operating_contract.md)
和 [Lifecycle](../../source/study_lifecycle_control.md) 进入受控新 revision。
数据保留和清理依照 [Artifact Retention](./artifact_retention_operations_contract.md)；
删除派生产物前证明 canonical source 可重建，保留独立的 restore/retention 证据。
