# Delivery 文档

Owner: `MedAutoScience`
Purpose: `medical_research_delivery_support`
State: `active_support`
Machine boundary: 人读索引。交付 authority 继续归 study workspaces、artifact/package contracts、generated submission material、source、runtime evidence 与 owner receipts。

本目录承接 MAS manuscript、package、submission/export、review/publication gate 与 delivery 支撑。通用 artifact lifecycle 已由 OPL Workspace `workspace artifact-lifecycle` 承担；MAS 只保留 delivery package / export authority、artifact body 与删除决策。

Delivery active board 只允许保存当前交付能力族的唯一 owner round、phase、下一步和退出条件。已吸收 round、外部 exemplar intake、旧 owner brief、长增量清单和 closeout proof 归 `docs/history/**` 或 delivery provenance，不在 active board 中累积。

本文是 delivery support 索引，不是 manuscript/package authority、submission-ready verdict、current-package freshness proof 或 active execution ledger。当前 delivery gap 和下一步回到 active owner docs；artifact/package 机器真相回到 study workspace、artifact contracts、generated submission material、runtime evidence、owner receipts 和 typed blockers；历史过程只作为 provenance 读取。

当前入口先看：

- [架构](../architecture.md)
- [当前状态](../status.md)
- [Runtime docs](../runtime/README.md)
- [Standard Domain Agent Skeleton](../runtime/contracts/standard_domain_agent_skeleton.md)
- [Inspection package 交付契约](inspection_package.md)

## Standard Agent Delivery Boundary

标准 OPL Domain Agent skeleton 只声明 delivery / artifact 相关 repo-source anchors 和 locator-only 边界。真实 manuscript、figure/table、submission package、`current_package`、publication eval、controller decisions、artifact mutation receipt 和 rebuild proof 仍归 MAS workspace / artifact authority surfaces，不进入 repo skeleton。

OPL generated / hosted surfaces 可以展示或运输 artifact locator refs、owner receipt refs、inspection-package pointer、retention candidate 和 typed blocker refs。它们不能授权 artifact mutation、package freshness、publication quality、submission readiness、delivery sync、cleanup / restore / retention apply 或 App release readiness。

## 外部证据与投稿资源

MAS 的 startup literature、medical literature audit、readiness authoring、Research Integrity 和 submission reference gap repair 若需要 provider transport，只消费 host 注入且带 exact ref 的 OPL Connect provider receipt；上游材料已经携带的静态 `provider_evidence` 仍可作为 Research Integrity 的纯输入，但不能伪装成 provider receipt 或 transport/currentness proof。MAS 根据 DOI、PMID、PMCID 等已知 identifier 解释医学文献证据，但不持有 provider HTTP、credential、retry、cache、receipt persistence 或关键词检索 transport；缺少需要联网补齐的证据时只返回 `opl_connect_reference_verification` request。广义文献发现仍由 literature specialist / OPL Connect search surface 承担，不能重新落成 MAS 私有 adapter。

投稿模板和引用样式同样不由 MAS 下载。Frontiers CSL 只接受 package-bundled 文件或 host 提供的 exact path，Word manuscript / supplementary templates 只接受 host-provisioned exact path；缺失时返回 `opl_pack_provision_submission_resource` request，禁止网络 fallback。机器边界分别以 `contracts/research-integrity-layer.json` 和 `contracts/submission-resource-requirements.json` 为准；receipt、模板存在或 package materialization 成功都不替代 publication quality、submission readiness 或 owner receipt。

若 delivery 文档、display pack 或 inspection package 只证明存在 derived artifact、blocked snapshot、review pointer 或 read-only projection，它只能作为 human inspection / evidence input；不能被写成 canonical artifact authority、source readiness verdict、publication gate closeout 或 `current_package` freshness proof。research evidence pack 的下一层目标是 read-model 可见、schema validation 可 fail closed、DM002 canary 可给出 evidence available 或 stable typed blocker；这些仍只是审计链证据，不替代真实 paper-line owner receipt、independent reviewer/auditor record、publication gate / human gate 或 artifact/memory/lifecycle authority。

Co-Scientist 启发的 hypothesis portfolio 可以帮助 delivery 前形成候选假设、证据包、negative / failed-path ledger、decision trace、claim-evidence map 和 reviewer briefing。它不能让 highest-ranked hypothesis、Elo winner、proximity representative 或 novelty score 直接进入 manuscript/package authority。进入 delivery 的最小口径仍是 MAS owner receipt、独立 reviewer/auditor record、publication gate / human gate、artifact lineage / reproducibility refs，或命名缺失 ref family 与 route-back owner 的 stable typed blocker。
