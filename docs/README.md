# 文档索引与生命周期

Owner: `MedAutoScience`
Purpose: `docs_entrypoint_and_lifecycle`
State: `active_index`
Machine boundary: 文档导航与维护约定不生成机器状态、医学结论或运行证据；机器事实以 `contracts/`、源码、workspace artifacts 和 fresh owner receipts 为准。

## 按主题导航

| 阅读目的 | 唯一人读入口 |
| --- | --- |
| 产品定位与长期研究目标 | [项目定位](./project.md) |
| 组件边界、OPL 合同映射与产品表面 | [架构概览](./architecture.md) |
| 必须保持的硬约束与退役边界 | [不可变约束](./invariants.md) |
| 当前有效设计理由与控制面退役记录 | [关键决策](./decisions.md) |
| 源码事实 vs 必须现场读取的证据 | [当前验证边界](./status.md) |
| 尚待证明的外部验收差距 | [开放差距计划](./active/mas-ideal-state-gap-plan.md) |
| 公开技术接口与机器合同 | [Contracts](../contracts/README.md) |
| Study 与 Workspace 目录职责及接入 | [Workspace 职责与接入](./source/study_workspace_target_state.md) |
| Study 四态生命周期与唤醒门禁 | [Study 生命周期控制](./source/study_lifecycle_control.md) |
| 医学数据资产 4-Plane 与保留分账 | [数据资产目标模型](./source/medical_data_asset_target_operating_model.md) |
| MAS/OPL Runtime 边界、Handler 与保留分工 | [Runtime 边界](./runtime/runtime_boundary.md) |
| 六 Stage、Decisive Attempt 路由与质量循环 | [Stage / Route / Handoff](./runtime/stage_route_handoff_standard.md) |
| Review Scope Currentness v2 与修订消费绑定 | [质量循环与 Currentness](./runtime/progress_first_quality_loop.md) |
| 文献/引用完整性与投稿资源边界 | [Research Integrity Layer](./runtime/research_integrity_layer.md) |
| Comparator 与 Baseline 显式刷新 | [Baseline Refresh 合同](./runtime/baseline_refresh_contract.md) |
| Markdown-First 知识作用域与来源绑定 | [知识与记忆政策](./policies/domain_memory_markdown_first_policy.md) |
| 出版策略记忆与写回规则 | [策略记忆政策](./policies/study-workflow/publication_route_memory_policy.md) |
| 七类医学研究路线锚点 | [Study Archetypes](./policies/study-workflow/study_archetypes.md) |
| 阶段研究自治、人机分工与候选板规则 | [研究自治与 Frontier](./policies/study-workflow/stage_led_research_autonomy.md) |
| `manuscript/` 同线修订与投稿交付合同 | [修订与投稿合同](./policies/study-workflow/submission_revision_operating_contract.md) |
| AI-First 质量边界、校准与发表验收 | [AI-First 质量边界](./policies/quality/ai_first_quality_boundary.md) |
| 医学论文初稿质量门槛 | [初稿质量门槛](./policies/quality/medical_manuscript_first_draft_quality.md) |
| CI Preflight、主线集成、切换与外部运行来源 | [仓库与运行治理](./policies/repo_and_runtime_operations.md) |
| 医学图表边界、审阅、路由与批量环境 | [医学图表交付边界](./delivery/medical_display_boundary.md) |
| App `runtime.detail` 贡献与审阅交接 | [Runtime Detail Contribution](./references/integration/mas-runtime-detail-contribution.md) |
| Codex Plugin Carrier 与 OPL Handoff | [Codex Plugin 与 Handoff](./references/integration/codex_plugin.md) |
| 白皮书构建边界与正文源 | [白皮书](./whitepapers/README.md) · [MAS 白皮书](./whitepapers/mas-whitepaper.md) |

## 文档生命周期

[`one-person-lab`](https://github.com/gaofeng21cn/one-person-lab/blob/main/docs/policies/docs-lifecycle-policy.md) 持有 OPL 家族通用文档生命周期规则；MAS 按以下原则维护本目录：

- **单一职责与引用同步**：每个主题只有一个当前正文 owner，上层文档只导航或保留独特上下文，不复制阶段状态、合同字段或能力库存。代码、合同、调用者或验证入口变化时，同一次修改更新对应正文及全部入链。
- **退役与清理**：已完成计划、过时模块、旧接口兼容叙事和重复流水直接删除并修复入链，不留重定向页、空目录索引或覆盖台账，历史交由 Git 保存；只有仍解释当前边界或机器 provenance 的内容才保留在 [关键决策](./decisions.md) 或显式元数据（如 [MDS 来源记录](./references/med-deepscientist/source_provenance.json)）。
- **验证边界**：纯文档改动检查语义准确性、相对链接/锚点、资源存在性与 `git diff --check`；涉及合同、源码、清单或测试时重跑 `scripts/verify.sh`（full lane 含 `opl pack inspect`）。不使用关键词、标题数量或静态快照证明文档正确，文档通过也不能替代真实论文、安装或运行证据。
