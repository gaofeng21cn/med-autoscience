# MAS 单项目 MDS 吸收

Status: `retired_active_guard_history`
Date: `2026-05-16`
Owner: `MedAutoScience`
Purpose: `mds_provenance_archive_parity_guard`
State: `history_provenance`
Machine boundary: 本文是人读历史 guard / provenance record。当前 MDS / DeepScientist owner boundary 归 `docs/policies/runtime-governance/mas_mds_owner_boundary_contract.md`、核心五件套、active gap plan、contracts、source、tests、runtime/controller surfaces、owner receipts 和 typed blockers。

完整历史记录见 [2026-05-10 MAS/MDS absorb full record](./mas_single_project_mds_absorb_program_2026_05_10_full_record.md)。

## Active-path retirement closeout 2026-06-07

Retired surface:

- `docs/active/mas_single_project_mds_absorb_program.md`

Replacement owners:

- `docs/policies/runtime-governance/mas_mds_owner_boundary_contract.md` 持有当前 MAS/MDS owner boundary policy。
- `docs/active/mas-ideal-state-gap-plan.md` 和 `docs/active/current-development-lines.md` 持有当前 active truth / execution map。
- `docs/runtime/domain_authority_refs_index_guard.md` 持有 domain authority refs / restore / archive drift guard。
- 本文件和 `docs/history/program/mas_single_project_mds_absorb_program_2026_05_10_full_record.md` 只保留 history / provenance。

Reviewed refs:

- Active/support references were updated in `docs/active/README.md`, `docs/active/current-development-lines.md`, `docs/active/program_portfolio_consolidation.md`, `docs/active/ai_first_paper_autonomy_closure_program.md`, `docs/docs_portfolio_consolidation.md`, `docs/history/program/README.md`, and `docs/references/med-deepscientist/deepscientist_latest_update_learning_protocol.md`.
- No `src/`, `tests/`, `contracts/`, or `agent/` caller referenced the retired active path during this tranche.
- Remaining literal mentions of `docs/active/mas_single_project_mds_absorb_program.md` live only in older history / coverage ledgers and are preserved as historical evidence, not current entrypoints.

Next-scope:

- Keep MDS / DeepScientist wording in active docs constrained to source provenance, historical fixture, explicit archive import, backend audit, upstream learning, and parity oracle reference.
- If future active caller evidence appears for this retired path, migrate that caller to the policy / active gap plan / domain authority refs owner surface rather than adding a compatibility redirect.

## 当前定位

本文是已从 `docs/active/` 退役的 P3 landed foundation guard，不是活跃 implementation queue，也不是当前 owner doc。它只保存 MAS monolith closeout 后的 owner 边界、MDS / DeepScientist retained role、archive/import 规则、parity oracle 规则和后续 source intake 分类口径的历史 guard 版本；当前维护入口回到 MAS/MDS owner boundary policy、核心 docs 和 active gap plan。

当前结论：

- MAS 是日常唯一 repo、用户入口、app skill、CLI/MCP/product-entry surface、医学 quality owner 和 artifact/publication authority。
- 外部 `med-deepscientist` / `DeepScientist` 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。
- MAS daily operation 不依赖外部 MDS repo、MDS daemon、MDS WebUI、MDS workspace-local service 或 MDS Git runtime lifecycle。
- MAS default independence 已落地；本文不声明旧 MDS daemon/WebUI 每个交互都已完整等价。

## 当前 owner split

| 关注面 | 当前 owner | P3 处置 |
| --- | --- | --- |
| Study truth / next owner | MAS controller / study truth surfaces | 留在 MAS。 |
| Publication / quality verdict | MAS AI reviewer、publication gate、evidence/review ledgers | 留在 MAS。 |
| Runtime health / recovery | OPL current control state、MAS owner receipt / typed blocker refs、local retired diagnostics | MAS 持有 domain truth 与 blocker/receipt 语义；provider hosting、attempt、recovery 和 worker liveness 归 P2 / OPL。 |
| Artifact / package authority | MAS Artifact OS、canonical rebuild proof | 留在 MAS。 |
| 旧 MDS code/history | external archive / provenance reference | 只允许 no-history import / explicit archive reference。 |
| 旧 MDS capability signal | parity fixture / backend audit oracle | 不能授权 quality 或 submission readiness。 |
| 旧 MDS path | explicit archive/import 或 provenance reader | 不新增 default writer。 |

## 保留角色分类

后续任何文档或代码引用 MDS / DeepScientist，必须先归入以下分类之一：

| classification | 允许用途 |
| --- | --- |
| `source_provenance` | 说明 source ref、hash、license 和 no-history 来源。 |
| `historical_fixture` | 保留冻结样例用于 regression / parity。 |
| `explicit_archive_import` | 由 operator 显式恢复或检查旧 workspace/archive。 |
| `backend_audit` | 对比行为，不让 MDS 成为 default backend。 |
| `upstream_learning` | 学习 upstream ideas，再由 MAS 或 OPL 重新持有采纳模式。 |
| `parity_oracle_reference` | 比较 retained capability semantics，不授予 authority。 |

禁止用途：

- 把外部 MDS 写成默认 runtime、默认 diagnostic、default runner、WebUI dependency 或 hidden runnable substitute；
- 用旧 MDS paper/package/coverage signal 授权 MAS quality、submission readiness 或 package authority；
- 把 MDS history / upstream authors 导入 MAS default-branch contributor graph；
- 在新功能中恢复 MDS-first names、paths、CLI alias、wrapper 或 facade。

## 与其他层的关系

P3 支撑其他 owner 文档，但不接管它们：

- P0 paper autonomy 依赖 MAS-owned quality、route、repair 和 artifact authority。
- P1 OPL App Runtime Workbench 消费 MAS projections，不咨询旧 MDS UI 或 workspace service。
- P2 OPL framework 通过 sidecar/receipt 托管 MAS，不复活 MDS daemon semantics。
- P3a domain authority refs guard 防止 root/quest Git、旧 `.ds` payload 和旧 active path 回流为默认 state surface。

新增 runtime/product 实现不写入本文。论文闭环写 P0，App/workbench 写 P1，OPL provider/framework 写 P2，domain authority refs / restore / archive drift 写 P3a。

## 验证口径

P3 claim 只能通过 source provenance、author audit、retained capability / behavior parity fixture、MAS controller/domain-authority refs/product-entry/Progress Portal contract test、explicit archive/import test 或具体 live workspace evidence 验证。文档本身不是 paper line 进展证明。
