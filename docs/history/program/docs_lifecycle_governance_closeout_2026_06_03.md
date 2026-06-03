# Docs lifecycle governance closeout 2026-06-03

Owner: `MedAutoScience`
Purpose: `docs_lifecycle_governance_closeout`
State: `history_provenance`
Machine boundary: 本文是人读 docs lifecycle closeout 记录。当前 docs truth 继续归 `docs/README.md`、核心五件套、`docs/docs_portfolio_consolidation.md`、`docs/active/mas-ideal-state-gap-plan.md`、contracts、source、runtime/controller surfaces 和 owner receipts。

## Scope

本轮按 MAS 理想目标态、当前 gap plan、docs lifecycle governance 和 repo machine facts 审计 `README*` 与 `docs/**/*.md`。写入范围限制为 Markdown 文档；未修改源码、contracts 或 tests。

本轮只做 docs lifecycle 收敛，不重新判断 live study runtime 是否已推进。DM002/DM003 或其他 study 的当前状态必须 fresh 读取 live `study_progress`、workspace artifacts、controller decisions、publication eval、OPL current-control 和 owner receipts。

## Inventory

本轮文档库存：

| Area | 文件数 |
| --- | ---: |
| README | 2 |
| `docs/` root | 7 |
| `docs/active/` | 10 |
| `docs/delivery/` | 16 |
| `docs/history/` | 132 |
| `docs/policies/` | 27 |
| `docs/product/` | 2 |
| `docs/public/` | 1 |
| `docs/references/` | 33 |
| `docs/runtime/` | 32 |
| `docs/source/` | 1 |
| `docs/specs/` | 1 |

总计：`264` 个 Markdown 入口，其中 `docs/**/*.md` 为 `262` 个。

## Lifecycle Roles

本轮确认的唯一职责：

| Role | Owner docs | Rule |
| --- | --- | --- |
| active truth | `docs/status.md`、核心五件套 | 只保存当前状态摘要、owner 边界、最近一次已记录 live audit 的 compact conclusion；不保存 receipt/worklist ledger。 |
| active plan | `docs/active/mas-ideal-state-gap-plan.md` | 唯一 gap / completion plan；维护功能/结构 gap、production evidence tail、近期完善顺序和禁止误写口径。 |
| active map | `docs/active/current-development-lines.md` | 内容线索引；不承担第二 backlog。 |
| support reference | `docs/runtime/**`、`docs/delivery/**`、`docs/source/**`、`docs/product/**`、`docs/references/**`、`docs/policies/**` | 支撑当前 owner、contract、policy 或 background；不得拥有 current study truth 或 dated verification ledger。 |
| history/tombstone | `docs/history/**` | 保存 dated closeout、attempt/receipt id、命令流水、旧 phase checklist、旧 activation package、legacy MDS/Hermes/OMX/Gateway/frontdoor/federation/compatibility 语境。 |

## Changes

本轮清理：

- 压缩 `docs/status.md`：从 dated follow-through ledger 改为 current-state summary，保留当前角色、最近一次已记录 DM002/DM003 runtime truth、机器事实、功能/结构状态、evidence tail、源码形态收口和禁止误写口径。
- 压缩 `docs/active/mas-ideal-state-gap-plan.md`：从长 closeout / receipt / worklist 流水改为 single Active Truth plan，明确结构 gap 当前为 0，剩余项全部归 production evidence tail。
- 更新 `docs/docs_portfolio_consolidation.md`：新增 2026-06-03 lifecycle 规则，明确 status/gap/current-development-lines 的唯一职责和 dated proof 的归档规则。
- 更新 `docs/README.md`、`docs/active/README.md`、`docs/history/program/README.md`：把本轮 closeout 和新归档规则接入索引。

## Retired From Active Layer

以下内容从 active/core 入口清理或压缩为 compact rule：

- Dated OPL worklist item count、domain-dispatch receipt count、stage replay missing receipt count、framework readiness count。
- Stage attempt id、receipt URL、same-day record/verify chain 和 follow-through tranche。
- Source/test morphology 的逐文件拆分流水。
- 已关闭 gate 的 checklist chronology。
- 已退役 MDS / DeepScientist / Hermes / local scheduler / `runtime_transport` / `mas_runtime_core*` / compat alias / fallback 路线作为 current owner 的歧义表述。

保留方式：

- 当前有效规则折回 `docs/status.md`、`docs/active/mas-ideal-state-gap-plan.md`、核心五件套、runtime docs、policies 或 machine-readable contracts。
- 纯历史过程保留在本文件、既有 `docs/history/program/**`、runtime ledger、真实 workspace receipt 或提交历史。

## Source Of Truth Checked

本轮读取并用于判断的事实面：

- `AGENTS.md`
- `TASTE.md`
- `docs/README.md`
- `docs/status.md`
- `docs/active/mas-ideal-state-gap-plan.md`
- `docs/docs_portfolio_consolidation.md`
- 核心五件套：`docs/project.md`、`docs/architecture.md`、`docs/invariants.md`、`docs/decisions.md`、`docs/status.md`
- 文档索引：各 canonical area README
- Machine facts spot-check：`contracts/functional_privatization_audit.json`、`contracts/generated_surface_handoff.json`、`contracts/production_acceptance/mas-production-acceptance.json`、`contracts/foundry_agent_series.json`
- Test/code fact spot-check：functional gap count、standard Agent purity、production acceptance 和 boundary fitness 相关测试/源码引用

## Verification Scope

本轮预期最小验证：

- `rtk git diff --check`
- `rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs README.md README.zh-CN.md`
- docs inventory/header/path spot-check

未运行 full tests。原因：本轮是 docs-only lifecycle rewrite，未修改 source、contracts、tests 或 runtime semantics。

## Remaining Risk

- `docs/decisions.md` 仍是大体量日期决策日志；按现有治理规则它保留历史记录，不在本轮压缩。
- `docs/delivery/medical-display/**` 和部分 runtime/policy/reference 文档仍较长；本轮只按 role 分类和入口治理收敛，没有逐篇重写内容。
- Active/support 文档仍可能保留 legacy 词面，但只要同时声明当前 owner 或处在 parity/provenance/reference 语境，就不是本轮 blocking issue。
- `docs/status.md` 中最近一次已记录 DM002/DM003 状态可能随 live runtime 改变；任何状态答复必须重新读取 live surfaces。
