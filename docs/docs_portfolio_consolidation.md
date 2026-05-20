# MAS 文档组合治理

Status: `active_docs_governance`
Owner: `MedAutoScience`
Purpose: `docs_lifecycle_governance`
State: `active_support`
Machine boundary: 本文是人读治理入口。MAS 机器真相继续归 runtime/controller/schema/source/generated surfaces、CLI/MCP/API 行为、study workspace artifacts、domain manifests、owner receipts 和语义化 `human_doc:*` id。

## 当前结论

`docs/**` 是 MAS 的中文内部开发与维护参考，不维护 docs 层双语镜像。稳定路径优先使用无语言后缀 `.md` 承载中文 canonical 内容。历史文件可以保留旧双语、旧路径或 dated 过程描述作为 provenance，但 active/reference 索引必须指向当前无后缀路径。

MAS 采用 OPL-family canonical docs taxonomy：

`active/public/product/runtime/delivery/source/policies/specs/references/history`

这个目录集合按长期职责保留，不按当前文件数量决定。`product/public/source/specs` 当前可以较薄，但必须在 README 或 owner 文档中说明进入条件和不进入条件。

## 生命周期原则

- 主文档只记录最新情况：当前定位、当前边界、当前功能/结构差距、测试/证据差距、完善顺序和禁止误写口径。
- 历史演变、dated evidence、process follow-through、closeout 过程、旧 board、旧 activation package 和完整流水进入 `docs/history/**`。
- 如果历史文件仍含 current truth，先抽取当前结论进入当前 owner 文档，再保留原文件作为 provenance。
- 每份长期文档必须在开头或索引中明确 owner、purpose、state 和 machine boundary。`state=active_plan` 表示仍决定执行顺序；`state=active_support` 表示仍支撑当前 owner 但不自行排队；`support_reference` 表示参考材料；`history_only` / `history_provenance` 表示不能作为 current truth。
- 已落地基础文档只有在仍承担 guard、provenance 分类、source intake 规则或 drift 判断时才留在 `docs/active/`；纯过程、旧 lane table、旧 activation package、旧 full record 和 dated closeout 必须放入 `docs/history/**`。
- `docs/decisions.md` 保留决策日期日志；不要为了压缩过程流水而改写 decisions 的历史记录。
- dated specs、dated closeout 和历史 full record 不能直接作为 current truth；当前 truth 必须由核心五件套、当前 owner doc、machine-readable contract 或 runtime/controller surface 承载。
- `docs/status.md` 只维护当前状态摘要，不承载 dated follow-up ledger；执行顺序只在 `docs/active/current-development-lines.md` 维护；program 文档组合只在 `docs/active/program_portfolio_consolidation.md` 维护。2026-05-20 这轮收敛记录见 [Docs lifecycle governance closeout 2026-05-20](./history/program/docs_lifecycle_governance_closeout_2026_05_20.md)。

## 与 OPL 的分层

OPL 系列项目全局主参考由 OPL 仓维护。MAS 文档只维护医学研究 domain agent 的目标、差距、study/publication/artifact authority、direct MAS app skill path、OPL-hosted sidecar/projection/receipt 边界，以及 MAS-to-OPL 上收候选。

MAG、RCA、MDS 或 OPL-owned App/workbench 的并行 backlog 不写入 MAS active docs。

## 目录职责

| 目录 | 长期职责 | 当前 MAS 承载 |
| --- | --- | --- |
| `docs/` root | docs 入口、核心五件套、docs governance | `README.md`、核心五件套、本文件。 |
| `docs/active/` | 当前执行、当前差距、active baton、当前 owner plan | current development lines、program portfolio、ideal-state gap plan、paper autonomy / OPL workbench / Temporal retirement / stage standardization 等 active owner docs。 |
| `docs/public/` | repo home 之后的公开叙事 | 当前较薄，保持 public narrative index；不承载 study truth。 |
| `docs/product/` | MAS app skill、product-entry、operator/workbench-facing guidance | direct path / product entry / OPL App drilldown 指南。 |
| `docs/runtime/` | runtime contracts、control、projection、display、active designs | 当前核心技术承载之一。完成或退役计划进入 `docs/history/runtime/`。 |
| `docs/delivery/` | manuscript、package、submission/export、medical-display 等交付支撑 | `delivery/medical-display/` 已承载能力族；domain artifact authority 仍归 MAS runtime/artifact surfaces。 |
| `docs/source/` | study workspace、source readiness、external intake、source truth consumption | 承接 workspace/source intake 与 source truth 边界。 |
| `docs/policies/` | 长期规则 | quality、study-workflow、runtime-governance、repo-ops。 |
| `docs/specs/` | 当前有效技术规格索引 | 新增 active spec 前先确认是否更适合 runtime/policies/references 或 machine contract。 |
| `docs/references/` | 支撑参考、定位、integration、MDS parity、verification、workspace、med-deepscientist | target/support/reference，不承担 active owner。 |
| `docs/history/` | dated snapshot、provenance、retired board、process archive | 旧 `program/`、旧 `capabilities/`、runtime/OMX/superpowers history、过程性 closeout 摘要。 |

## 非 canonical 目录

旧 `docs/program/` 和 `docs/capabilities/` active 目录已物理退役：

- 当前 program-baton 材料进入 `docs/active/`。
- medical-display 能力族进入 `docs/delivery/medical-display/`。
- 历史 program/capability 材料只保留在 `docs/history/`，不得继续作为 recurring material 落点。

## 内容级整合规则

1. 当前 factual truth 合入核心五件套、runtime/controller/schema/source、machine-readable contract 或当前 owner doc。
2. 当前执行、差距、program baton 和仍决定下一步顺序的 owner plan 留在 `docs/active/`。
3. Runtime/control/projection/display 进入 `docs/runtime/`；完成或退役计划进入 `docs/history/runtime/`。
4. Medical display 和 delivery authority support 进入 `docs/delivery/`；真实 artifact authority 仍归 MAS runtime/artifact surfaces。
5. Source/workspace/intake 支撑进入 `docs/source/`；generic shell 候选记录为 MAS-to-OPL 上收边界。
6. 稳定规则进入 `docs/policies/`；一次性计划不得放入 policies。
7. MDS/DeepScientist 只作为 historical fixture、explicit archive import、backend audit、upstream intake、source provenance 或 parity oracle reference。
8. dated evidence、follow-through、过程流水和 closeout 摘要进入 `docs/history/program/` 或相应 `docs/history/<area>/`。

## Direct Retirement

当旧模块、旧接口、旧 CLI alias、旧 wrapper、旧 facade、旧测试入口或旧文档入口已被当前 owner surface 替代时，默认直接退役。迁移 active caller 后删除旧面；需要来龙去脉时只保留 history/tombstone/provenance，不新增 compatibility shim、别名或聚合测试。

直接退役的判断顺序固定为：

1. 证明没有 default CLI/MCP/product-entry/app-skill/OPL active caller。
2. 证明没有 public surface、fixture 或 provenance 必须依赖该旧入口。
3. 证明 replacement owner surface、history link 或 tombstone contract 已存在。
4. 删除旧源码、命令 wrapper、alias、facade 和对应兼容测试；测试改断言当前 machine-readable contract、schema、CLI/API、manifest 或 generated artifact。

满足上述条件后，不保留旧名兼容层，不新增聚合兼容测试，也不把旧文档路径当成稳定机器接口。

## Path-Stable Active 文档收敛

少数 `docs/active/*.md` 仍被 `human_doc:*`、contract、source projection 或测试 manifest 指向。它们可以暂留原路径，但必须收窄为单一职责：

- `mas-ideal-state-gap-plan.md` 是唯一当前 gap / 完善计划。
- `current-development-lines.md` 是唯一当前执行内容地图。
- `program_portfolio_consolidation.md` 只解释旧 program 文档组合与生命周期，不维护第二 backlog。
- `ai_first_paper_autonomy_closure_program.md` 只定义论文自治验收合同。
- `opl_temporal_mas_runtime_retirement_program.md` 只维护 MAS 侧 OPL handoff / legacy retirement 支撑，不定义 OPL framework 总计划。
- `stage_surface_standardization_program.md` 只维护 stage pack 形态。
- `opl_app_mas_runtime_workbench_program.md` 只维护 MAS refs-only projection 到 OPL App/workbench 的边界。
- `mas_single_project_mds_absorb_program.md` 与 `runtime_lifecycle_sqlite_migration_program.md` 只保留 landed foundation guard、provenance 和 drift 判断。

这些路径暂留不是兼容承诺。若后续 machine/human_doc caller 迁出，且当前结论已吸收到 gap plan、runtime/source/delivery/policy 或 history，文档应直接移动到 `docs/history/**` 或 tombstone；不新增重定向文档、兼容 alias 或平行索引。
