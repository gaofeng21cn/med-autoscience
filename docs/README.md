# 文档索引

这个目录是 `Med Auto Science` 的技术阅读层。仓库首页继续作为医生、PI 和医学研究团队的默认入口。

## 先读这里

| 需求 | 入口 |
| --- | --- |
| 产品角色与边界 | [项目概览](./project.md) |
| 当前运行真相 | [当前状态](./status.md) |
| 当前执行地图 | [MAS 当前开发线路](./active/current-development-lines.md) |
| 架构与 owner 边界 | [架构](./architecture.md) |
| 不可变约束 | [不可变约束](./invariants.md) |
| 持久决策 | [关键决策](./decisions.md) |
| 文档生命周期规则 | [文档组合治理](./docs_portfolio_consolidation.md) |

## OPL 系列分层

OPL 系列项目的全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`。其中维护 OPL Framework 的全局目标、全局差距、通用能力上收边界、App/workbench 目标和跨仓开发顺序。

MAS 本仓只维护医学研究 domain agent 的目标、当前差距、study/publication/artifact authority、direct MAS app skill path、OPL-hosted sidecar/projection/receipt 边界，以及哪些通用 runtime、memory、artifact lifecycle、workbench 和 observability primitive 应上收到 OPL。MAS 理想目标态读 [MAS 理想目标态](./references/positioning/mas_ideal_state.md)，当前差距和完善计划读 [MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)。MAG、RCA、MDS 或 OPL-owned App/workbench 的并行 backlog 不在 MAS 文档中维护。

## Workspace / file lifecycle 边界

MAS 的 repo-source layout 按标准 domain agent 职责读取：`agent/` 持有医学研究 declarative pack，`contracts/` 持有机器合同和 schema/index，`runtime/authority_functions/` 只作为最小医学 authority function 的 runtime-facing descriptor/receipt-ref 边界，`src/` 持有 domain handler、authority adapter 与 native helper，`docs/` 持有人读治理说明。真实 study workspace state、runtime artifact、receipt instance、交付物、临时 build/cache/venv/pycache/pytest cache/install sync 副产物不进入开发 checkout；它们必须落到受控 study workspace/runtime artifact root 或用户级 runtime state。

MAS repo source 只保存 locator、index、schema、receipt ref、restore/retention policy 和 no-forbidden-write 证据。医学 study truth、publication/quality verdict、artifact authority、publication-route memory body accept/reject 与 owner receipt 仍归 MAS owner chain；OPL 只上收通用 workspace/file lifecycle primitive、scheduler/runner/session/workbench shell 和 projection。

## 目录地图

| 目录 | 用途 |
| --- | --- |
| [active](./active/README.md) | 当前执行、当前计划、当前差距与 active baton；旧 `program/` 内容由这里维护。 |
| [public](./public/README.md) | MAS 对外公开叙事和用户第一阅读层。 |
| [product](./product/README.md) | MAS app skill、direct product entry、operator/workbench-facing 指南。 |
| [runtime](./runtime/README.md) | 运行时合同、控制面、读模型、展示合同和活跃设计。 |
| [delivery](./delivery/README.md) | manuscript、package、submission/export 与医学研究交付 authority。 |
| [source](./source/README.md) | study workspace、source readiness、source truth consumption 与 external research intake。 |
| [policies](./policies/README.md) | 稳定内部规则和长期运行边界。 |
| [specs](./specs/README.md) | 当前仍有效的技术规格索引；旧 spec 需标清 active/history。 |
| [references](./references/README.md) | 支撑参考、定位、集成说明和 parity 材料；dated verification ledger 归 history。 |
| [history](./history/README.md) | dated snapshot、provenance、退役 board、归档计划和过程稿。 |

这张表采用 OPL-family canonical docs taxonomy。旧 `program/` 与
`capabilities/` 目录已物理退役；program-baton 内容进入 `active/`，
medical-display 能力族进入 `delivery/medical-display/`。

当前生命周期校准：`outer_loop_wakeup_and_decision_loop.md` 已从 active runtime/control 归档到 [history/runtime](./history/runtime/README.md)，只作 provenance。当前 control 语义从 [Study runtime control surface](./runtime/control/study_runtime_control_surface.md)、[Study runtime orchestration](./runtime/control/study_runtime_orchestration.md) 和 [Runtime event and outer-loop input contract](./runtime/contracts/runtime_event_and_outer_loop_input_contract.md) 读取。MAS local scheduler / LaunchAgent / legacy tick 已物理退役，只按 tombstone/provenance refs 理解，不写成 MAS 理想 runtime 常态。`Plan Completion Ledger`、real-study verification note 和 docs lifecycle audit 这类 dated proof 已归 [history/program](./history/program/README.md)，不再由 `references` 承载。本轮 docs 生命周期治理 closeout 见 [Docs lifecycle governance closeout 2026-05-20](./history/program/docs_lifecycle_governance_closeout_2026_05_20.md)。

## 阅读规则

先读核心文档，再进入对应子目录索引。详细文件清单由各子目录 README 承担，本页只保留短导航。

`docs/**` 是中文内部开发与维护参考。代码、测试、runtime status 和 contract 应依赖 schema、durable JSON、source path 或 `runtime:*`、`program:*`、`policy:*`、`human_doc:*` 等语义 ID，不应把 Markdown prose 文案钉成机器接口。
