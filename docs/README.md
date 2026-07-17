# 文档索引

Owner: `MedAutoScience`
Purpose: `docs_entrypoint`
State: `active_index`
Machine boundary: 本文是人读导航。机器真相归 `agent/`、`contracts/`、MAS domain-handler/authority results、OPL generated/readback surfaces、workspace artifacts 与 owner receipts。

## 核心五件套

| 需求 | 入口 |
| --- | --- |
| 项目角色 | [项目概览](./project.md) |
| 架构与 owner split | [架构](./architecture.md) |
| 不可变约束 | [不可变约束](./invariants.md) |
| 当前有效决策 | [关键决策](./decisions.md) |
| 当前状态 | [当前状态](./status.md) |

## 面向用户

- [MAS 白皮书（在线阅读）](https://gaofeng21cn.github.io/med-autoscience/latest/whitepapers/mas-whitepaper.html)：解释 MAS 的设计理念、研究线、证据链、独立审阅与人机边界。
- [MAS 白皮书（PDF）](https://gaofeng21cn.github.io/med-autoscience/latest/whitepapers/mas-whitepaper.pdf)：适合离线阅读与转发。

## 当前计划

[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md) 是唯一 Active Truth owner，持有当前结构摘要、开放差距与下一轮 Agent prompt。当前机器形态是 declarative pack、OPL generated/hosted surfaces 与三个 registry-bound minimal authority functions；Live evidence 独立后置。

## 当前架构入口

- [Product surfaces](./product/README.md)：OPL generated/hosted interface 与 MAS authority boundary。
- [Runtime boundary](./runtime/contracts/runtime_boundary.md)：OPL runtime 与 MAS domain owner split。
- [Controllers](./runtime/control/controllers.md)：MAS controller 只处理医学 policy/authority。
- [Stage outcome](./runtime/control/progress_first_stage_outcome.md)：`Codex CLI selected stage -> nonbinding route context`。
- [Study Truth Kernel](./runtime/projections/study_truth_kernel.md)：domain reducer/read-model 边界。
- [Medical Display](./delivery/medical-display/README.md)：display action、OPL pack/runtime 与 MAS quality authority。
- [External runtime gate](./policies/runtime-governance/external_runtime_dependency_gate.md)：非默认 executor/backend/provenance 边界。

## OPL 系列分层

MAS 的 canonical agent id 是 `mas`，machine domain id 是 `medautoscience`，长期形态是：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`

`agent/` 持有 declarative pack，`contracts/` 持有 action/schema/authority/handoff contracts，`src/` 只保留 domain-handler targets 与 minimal authority helpers。CLI、MCP、Skill、product-entry、status、workbench、runtime lifecycle、StateIndex、storage/health 与环境 provisioning归 OPL。

## 目录地图

| 目录 | 用途 |
| --- | --- |
| [active](./active/README.md) | 当前计划、owner gate 与 active support index |
| [public](./public/README.md) | 对外叙事 |
| [product](./product/README.md) | Product/inspection boundary |
| [runtime](./runtime/README.md) | Runtime contracts、control、projections 与 active designs |
| [delivery](./delivery/README.md) | Manuscript、display、package 与 submission support |
| [source](./source/README.md) | Source readiness、workspace refs 与 external intake |
| [policies](./policies/README.md) | 稳定治理规则 |
| [specs](./specs/README.md) | 当前有效技术规格索引 |
| [references](./references/README.md) | 背景、对照、provenance 与非 active 参考 |
| [history](./history/README.md) | dated proof、旧计划、tombstone 与过程归档 |

## 阅读规则

- 先读核心五件套，再进入 owner 子目录。
- Active docs 只保留 current owner、state、machine boundary 与 open gate；dated proof/receipt/命令流水归 Git或 history。
- `docs/**` 不是机器接口。代码和测试依赖 JSON/schema/source/semantic id，不解析 Markdown措辞。
- History 中的 provider admission、current work unit、PaperRecovery、repo-local CLI/MCP/workbench/runtime 只能按 provenance/tombstone读取。
- Runtime/paper/publication/production ready 必须 fresh live/readback/artifact/receipt evidence；docs、tests、descriptor和 projection 不替代。

## 文档治理

新增、更新、归档或 tombstone 前读 [MAS 文档组合治理](./docs_portfolio_consolidation.md)。
