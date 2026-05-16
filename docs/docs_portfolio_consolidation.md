# MAS 文档组合治理

Status: `active_docs_governance`
Owner: `MedAutoScience`
Purpose: `docs_lifecycle_governance`
State: `active_support`
Machine boundary: 本文是人读治理入口。MAS 机器真相继续归 runtime/controller/schema/source/generated surfaces、CLI/MCP/API 行为、study workspace artifacts、domain manifests、owner receipts 和语义化 `human_doc:*` id。

## 当前结论

`docs/**` 是 MAS 的中文内部开发与维护参考，不再维护 docs 层双语镜像。稳定路径优先使用无语言后缀 `.md` 承载中文 canonical 内容。历史文件可以保留旧双语或旧路径描述作为 provenance，但 active/reference 索引必须指向当前无后缀路径。

MAS 采用 OPL-family canonical docs taxonomy：

`active/public/product/runtime/delivery/source/policies/specs/references/history`

这个目录集合按长期职责保留，不按当前文件数量决定。`product/public/source/specs` 当前可以较薄，但必须在 README 或 owner 文档中说明进入条件和不进入条件。

## 与 OPL 的分层

OPL 系列项目全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`。它持有全局 framework 目标、跨仓差距顺序、shared primitive 上收、App/workbench 目标和同名 docs taxonomy。

MAS 文档只维护医学研究 domain agent 的目标、差距、study/publication/artifact authority、direct MAS app skill path、OPL-hosted sidecar/projection/receipt 边界，以及 MAS-to-OPL 上收候选。MAG、RCA、MDS 或 OPL-owned App/workbench 的并行 backlog 不写入 MAS active docs。

## 目录职责

| 目录 | 长期职责 | 当前 MAS 承载 |
| --- | --- | --- |
| `docs/` root | docs 入口、核心五件套、docs governance | `README.md`、核心五件套、本文件。 |
| `docs/active/` | 当前执行、当前差距、active baton、program lifecycle portfolio、closeout evidence | current development lines、program portfolio、paper autonomy / OPL workbench / Temporal retirement / stage standardization 等 active owner docs。 |
| `docs/public/` | repo home 之后的公开叙事 | 当前较薄，保持 public narrative index；不承载 study truth。 |
| `docs/product/` | MAS app skill、product-entry、operator/workbench-facing guidance | 当前较薄，承接 direct path / product entry / OPL App drilldown 指南。 |
| `docs/runtime/` | runtime contracts、control、projection、display、active designs | 当前核心技术承载之一。完成或退役计划进入 `docs/history/runtime/`。 |
| `docs/delivery/` | manuscript、package、submission/export、medical-display 等交付支撑 | `delivery/medical-display/` 已真实承载能力族；domain artifact authority 仍归 MAS runtime/artifact surfaces。 |
| `docs/source/` | study workspace、source readiness、external intake、source truth consumption | 当前较薄，后续承接 workspace/source intake 与 source truth 边界。 |
| `docs/policies/` | 长期规则 | quality、study-workflow、runtime-governance、repo-ops。 |
| `docs/specs/` | 当前有效技术规格索引 | 当前较薄；新增 active spec 前先确认是否更适合 runtime/policies/references 或 machine contract。 |
| `docs/references/` | 支撑参考、定位、integration、MDS parity、verification、workspace、med-deepscientist | target/support/reference，不承担 active owner。 |
| `docs/history/` | dated snapshot、provenance、retired board、process archive | 旧 `program/`、旧 `capabilities/`、runtime/OMX/superpowers history。 |

## 非 canonical 目录

旧 `docs/program/` 和 `docs/capabilities/` active 目录已物理退役：

- 当前 program-baton 材料进入 `docs/active/`。
- medical-display 能力族进入 `docs/delivery/medical-display/`。
- 历史 program/capability 材料只保留在 `docs/history/`，不得继续作为 recurring material 落点。

如果历史文件仍含 current truth，先抽取内容进入当前 owner 文档，再保留原文件作为 provenance。

## 2026-05-16 生命周期审阅结论

本轮以 [MAS 理想目标态](./references/positioning/mas_ideal_state.md)、[MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)、OPL family 主参考和核心五件套为依据，逐类审阅 `docs/**` 中除主参考和核心五件套外的长期文档。当前处置如下：

| 文档族 | lifecycle | 处置 |
| --- | --- | --- |
| `docs/active/` | `current_plan/support` | 保留为 MAS 当前执行、差距和 closeout evidence 入口；旧 program 物理目录不复活，`program_id` 只作为语义 ID。 |
| `docs/runtime/control/study_runtime_control_surface.md` / `study_runtime_orchestration.md` / `runtime_supervision_loop.md` | `current_runtime_support` | 保留当前控制面、orchestration 和 domain supervision 解释；通用 queue/attempt/provider/state-machine runner 继续归 OPL。 |
| `docs/runtime/control/supervision_scheduler_contract.md` | `current_residue_migration_bridge` | 保留为 MAS 活代码中的 direct/local diagnostic scheduler 残留说明；不能写成 MAS 理想终态，后续有 replacement proof 后迁移或退役。 |
| `docs/runtime/control/outer_loop_wakeup_and_decision_loop.md` | `history_provenance` | 已归档到 `docs/history/runtime/outer_loop_wakeup_and_decision_loop.md`；active control 入口改读 `study_runtime_control_surface` 与 `runtime_event_and_outer_loop_input_contract`。 |
| `docs/delivery/medical-display/` | `current_delivery_support` | 保持为 medical-display 能力族活跃位置；旧 `docs/capabilities/medical-display/` 只保留历史/provenance，不作为 backlog。 |
| `docs/history/program/` / `docs/history/capabilities/` / `docs/history/positioning/` | `history_only` | 只作 dated snapshot、tombstone、旧定位和 provenance；Domain Harness OS、Open Harness OS、Hermes-first、MDS default dependency 不能从这里回写到 active/current。 |
| `docs/product/` / `docs/public/` / `docs/source/` / `docs/specs/` | `thin_current_index` | 目录按 OPL-family taxonomy 保留；只承接本目录职责，不扩成第二计划、第二 runtime 或第二 truth source。 |

## 内容级整合规则

1. 当前 factual truth 合入核心五件套、runtime/controller/schema/source 或当前 owner doc。
2. 当前执行、差距、program baton 和 closeout evidence 留在 `docs/active/`。
3. Runtime/control/projection/display 进入 `docs/runtime/`；完成或退役计划进入 `docs/history/runtime/`。
4. Medical display 和 delivery authority support 进入 `docs/delivery/`；真实 artifact authority 仍归 MAS runtime/artifact surfaces。
5. Source/workspace/intake 支撑进入 `docs/source/`；generic shell 候选记录为 MAS-to-OPL 上收边界。
6. 稳定规则进入 `docs/policies/`；一次性计划不得放入 policies。
7. MDS/DeepScientist 只作为 historical fixture、explicit archive import、backend audit、upstream intake、source provenance 或 parity oracle reference。

## Direct Retirement

当旧模块、旧接口、旧 CLI alias、旧 wrapper、旧 facade、旧测试入口或旧文档入口已被当前 owner surface 替代时，默认直接退役。迁移 active caller 后删除旧面；需要来龙去脉时只保留 history/tombstone/provenance，不新增 compatibility shim、别名或聚合测试。

直接退役的判断顺序固定为：

1. 证明没有 default CLI/MCP/product-entry/app-skill/OPL active caller。
2. 证明没有 public surface、fixture 或 provenance 必须依赖该旧入口。
3. 证明 replacement owner surface、history link 或 tombstone contract 已存在。
4. 删除旧源码、命令 wrapper、alias、facade 和对应兼容测试；测试改断言当前 machine-readable contract、schema、CLI/API、manifest 或 generated artifact。

满足上述条件后，不保留旧名兼容层，不新增聚合兼容测试，也不把旧文档路径当成稳定机器接口。
