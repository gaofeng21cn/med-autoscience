# References

本目录保存仍有价值、但不属于 active development-plan、runtime contract 或 execution gate 层的技术上下文。

这里用于理解背景、集成形态、parity 证据、定位和验证历史。当前执行 gate 仍在
`docs/program/`，runtime authority 仍在 `docs/runtime/`，active truth 从核心文档进入：

- [文档索引](../README.zh-CN.md)
- [项目概览](../project.md)
- [当前状态](../status.md)
- [架构](../architecture.md)
- [不可变约束](../invariants.md)
- [关键决策](../decisions.md)
- [Program portfolio consolidation](../program/program_portfolio_consolidation.md)

## Current Mainline References

- [MAS 单项目质量与自治主线](./mas_single_project_quality_and_autonomy_mainline.md)
- [AI-first research OS architecture](./ai_first_research_os_architecture.md)
- [项目修复优先级图](./project_repair_priority_map.md)
- [Series doc governance checklist](./series-doc-governance-checklist.md)

## Workspace And Integration References

- [Disease workspace quickstart](./disease_workspace_quickstart.md)
- [Workspace architecture](./workspace_architecture.md)
- [Lightweight product entry and OPL handoff](./lightweight_product_entry_and_opl_handoff.md)
- [Codex plugin](./codex_plugin.md)
- [Codex plugin release](./codex_plugin_release.md)
- [Domain gateway harness OS](./domain_gateway_harness_os.md)
- [OPL family contract adoption](./opl_family_contract_adoption.md)
- [OPL-managed runtime three-layer contract](./opl_managed_runtime_three_layer_contract.md)

## MDS Learning And Intake References

- [MedDeepScientist references](./med-deepscientist/README.zh-CN.md)

`med-deepscientist/` 包含 DeepScientist recurring learning 的 active policy/protocol。
dated intake 记录保存在 `docs/history/program/`，作为已完成轮次的快照。

## Positioning And Architecture References

- [Domain Harness OS positioning](./domain-harness-os-positioning.md)
- [Open Harness OS architecture](./open_harness_os_architecture.md)
- [Research Foundry positioning](./research_foundry_positioning.md)
- [Research Foundry medical phase ladder](./research_foundry_medical_phase_ladder.md)
- [Research Foundry 与 Med Auto Science 仓库分工](./repo_split_between_research_foundry_and_med_autoscience.md)

## Ledgers, Parity, And Verification References

- [Plan completion ledger](./plan_completion_ledger.md)
- [MDS capability parity matrix](./mds_capability_parity_matrix.md)
- [真实 study relaunch 验证](./real_study_relaunch_verification.md)

## 分组规则

新增 reference 文件应先进入上面的一个分组，再扩大 root-level 文件列表：

- Mainline references：长期有效的 MAS quality、autonomy、repair priority 或 docs governance 背景。
- Workspace and integration references：workspace setup、plugin、handoff、gateway 和 family-contract 背景。
- MDS learning and intake references：standing learning policy/protocol；dated intake snapshot 应进入 history。
- Positioning and architecture references：repo 定位、外部模型比较和架构 rationale。
- Ledgers, parity, and verification references：evidence ledger、parity matrix 和 verification narrative。

如果新 reference 无法归入现有分组，先判断它是否其实属于 active program、runtime contract、policy、capability-family doc 或 history snapshot。只有某个类别会反复出现并容纳多个文件时，才新增 references 分组。否则应从最近的 owner README 链接它，避免 root-level loose reference files 继续扩张。

## Lifecycle Rule

references 是支持材料。它可以保存 rationale、comparison、integration notes 和 evidence
history，但不认证当前 runtime state、publication readiness、controller authority 或 active
execution gate。若 reference 与当前真相冲突，以核心文档、runtime contracts、policy docs、
durable JSON/schema surfaces 和 active program board 为准。

OPL family lifecycle governance 只是文档管理输入。文件放在 `docs/references/` 不代表 MAS 继承 OPL owner route；MAS domain truth 仍由 MAS-owned contracts、controllers、generated catalogs、schemas 和 durable workspace surfaces 决定。
