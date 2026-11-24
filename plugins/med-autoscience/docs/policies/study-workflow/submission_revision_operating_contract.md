# Submission / Revision Operating Contract

Owner: `MedAutoScience`
Purpose: `canonical_artifact_submission_and_revision_contract`
State: `active_policy`
Machine boundary: artifact contracts、generation manifest、independent Review、currentness evaluation、owner receipts 与真实 workspace bytes 持有机器事实。

本文冻结 MAS 对 `manuscript/` 唯一编辑源、派生产物边界、同线修订、Revision Intake 与发表交付门禁的 authority 边界。它不授权新分析、新 claim、source readiness、外部投稿或将 OPL provider completion 视为 submission readiness。

## Canonical 编辑源与派生产物边界

- **唯一编辑源 vs 派生产物**：Workspace `manuscript/` 是 controller 授权的 canonical editable source；charter、analysis、evidence、claim 与 reference 材料在各自 canonical owner 下维护。DOCX/PDF、ZIP、`submission/` 与 `manuscript_source.md` 是派生产物或来源投影，不能反向成为编辑源或 quality authority；前台对派生文件作出的编辑只作 review overlay，必须先回到缺陷所属 Stage 的 canonical source（如 `manuscript/`）并重建，再重新评估受影响 review scope。
- **禁止浅层覆盖与旧路径**：Exporters 可将 canonical manuscript 复制到 `delivery/`、`manuscript/current_package/` 或 `submission/` 作 lineage，但 shallow publish 必须拒绝覆盖 canonical source。历史 `paper/` 路径仅作 provenance，新工作一律使用 `manuscript/`，不得创建别名。
- **元数据与交付物选择**：读者可见标题与导出元数据标题必须源自当前 canonical manuscript title；面向用户的 PDF/ZIP 按当前已发布 delivery manifest 的 artifact role、generation、路径、大小与 digest 选取，拒绝按目录名（即使含 `current`）直接浏览历史路径。`submission-package.v2` 内的 `audit/` 与 `reproducibility/` 仅提供来源和复现投影，不能取代医学、统计、引用或 publication verdict。
- **Owner 分工与原子切换**：MAS 持有 artifact mutation、quality/publication 与 memory authority；OPL Framework 提供通用 tree inventory、ZIP、hash、transport、retention 与原子 projection（[Runtime 边界](../../runtime/runtime_boundary.md)）。Final Handoff 仅封装 exact reviewed bytes，MAS owner receipt 绑定 `publication_generation`、status、evaluation、next-action 与 projection manifest 后，Framework 才通过 sibling staging 整树切换 `submission/`（见 [Stage / Route / Handoff](../../runtime/stage_route_handoff_standard.md)）；失败不得留下半填充 root，transport 成功也不提升领域 verdict。

## 发表门槛、同线修订与 Revision Intake

- **Publication Acceptance 边界**：Submission readiness 与 publication acceptance 必须消费当前研究 identity、完整 evidence/claim lineage、AI reviewer 支持的独立 Stage Review 与跨 Stage Meta Review、current per-scope epistemic dependency evaluations，以及与交付 generation 绑定的 exact bytes；产物存在、gate checklist 完整或运行成功不能签发 ready。普通质量缺口允许带质量债推进可消费 draft 并 route-back，弱结果必须降级 claim、调整路线或保留负结果；外部投稿仍须作者事实、期刊要求与明确 human authority。
- **未消费修订与 Scope 局部失效**：当存在尚未被当前 generation 消费的已接受或活跃 reviewer revision 时，即使旧 package 内部一致也非当前交付，finalize/publication handoff 必须 route-back 且不得声明 `milestone_delivered` 或 publication/submission authority。仅涉及 package、layout、checklist、receipt 或 projection 的变化，不自动使医疗、统计或引用审阅失效。
- **Revision Intake 唤醒边界**：已停止、交付暂停或暂停的 study 在收到明确审阅/用户修订意见后，必须通过持久 `reviewer_revision` intake（绑定修订清单、独立审阅包、首个 owning Stage 与允许范围）、OPL 原子物化 CAS reactivation receipt（[Study 生命周期控制](../../source/study_lifecycle_control.md)）与现有 `manuscript_authoring` Stage action（经 `user_intent`、`input_refs`、`route_context_refs`）恢复同线修订；不得新增 `revision_intake_wake` action、repo-local runner、queue 或状态壳。当 OPL 无法将当前持久 revision intake ref 绑定到现有 Stage action 时，输出 owner 为 `one-person-lab` 的 typed blocker `revision_intake_wake_host_binding_missing`。

## Incident Guards

平台须持续保持以下回归防护：禁止重复图注、平台包生成中的 study 硬编码、projection-as-authority 漂移、浅层 publish 覆盖 canonical manuscript、未消费新 reviewer revision 时接受旧一致包、可见标题与 PDF/DOCX 元数据标题不一致、在存在更新 manifest PDF 时直接选中旧 PDF、用户可见 ZIP 使用固定容器 epoch 而非冻结同代 finalization 时间、过期 epistemic 依赖或 package provenance，以及仅凭 package 存在错误声明 milestone。
