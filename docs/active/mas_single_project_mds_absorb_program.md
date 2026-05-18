# MAS 单项目 MDS 吸收

Status: `landed_foundation_owner_doc`
Date: `2026-05-16`
Owner: `MedAutoScience`
Purpose: `mds_provenance_archive_parity_guard`
State: `active_support`
Machine boundary: 本文是人读 owner / provenance guard。机器真相继续归 MAS runtime/controller/quality/artifact surfaces、source provenance records、parity fixtures、explicit archive/import readers、archive/import ledgers 和 live workspace evidence。

完整历史记录见 [2026-05-10 MAS/MDS absorb full record](../history/program/mas_single_project_mds_absorb_program_2026_05_10_full_record.md)。

## 当前定位

本文是 P3 landed foundation owner，不是活跃 implementation queue。它只保存 MAS monolith closeout 后的当前 owner 边界、MDS / DeepScientist retained role、archive/import 规则、parity oracle 规则和后续 source intake 分类口径。

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
| Runtime health / recovery | MAS Runtime OS、owner-route dispatch、local diagnostics | MAS 持有 domain truth；provider hosting 归 P2 / OPL。 |
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
- P3a runtime lifecycle guard 防止 root/quest Git、旧 `.ds` payload 和旧 active path 回流为默认 state surface。

新增 runtime/product 实现不写入本文。论文闭环写 P0，App/workbench 写 P1，OPL provider/framework 写 P2，runtime lifecycle / restore / archive drift 写 P3a。

## 验证口径

P3 claim 只能通过 source provenance、author audit、retained capability / behavior parity fixture、MAS runtime/controller/product-entry/Progress Portal contract test、explicit archive/import test 或具体 live workspace evidence 验证。文档本身不是 paper line 进展证明。
