# Docs lifecycle governance closeout 2026-06-05

Owner: `MedAutoScience`
Purpose: `docs_lifecycle_governance_closeout`
State: `history_provenance`
Machine boundary: 本文是人读 docs lifecycle closeout 记录。当前 docs truth 继续归 `docs/README.md`、核心五件套、`docs/docs_portfolio_consolidation.md`、`docs/active/mas-ideal-state-gap-plan.md`、contracts、source、runtime/controller surfaces、OPL current-control / provider attempt refs 和 MAS owner receipts。

## Scope

本轮只清理 docs lifecycle 和 active/support 叙事边界。写入范围为 `docs/**`；未修改源码、contracts 或 tests。目标是让 MAS active docs 继续按标准 OPL Agent 目标态读取，不把 dated ledger、旧 runtime/Hermes/MDS/local scheduler 叙事、receipt/task id 或旧 Phase history 写成 current truth。

## Changes

- `docs/docs_portfolio_consolidation.md`：把逐日 coverage ledger 长清单折叠为 `docs/history/docs-portfolio-coverage-ledger/` 指针，并固定 active governance 不再追加 dated part list。
- `docs/status.md`：保留 current-state summary、recent audit compact conclusion、owner boundary、machine facts 和 evidence tail；把 2026-06-04 storage/index/stage-folder/DM002/DM003 follow-through 细节折回 `docs/runtime/domain_authority_refs_index_guard.md`。
- `docs/runtime/contracts/agent_runtime_interface.md`：从 active contract 主体移除旧 Phase、Hermes/MDS/local scheduler、workspace service 和数据资产流程长叙事，收敛为当前 agent runtime entry、owner boundary、stable entries、usage rules、product projection contract、forbidden statements 和 history pointers。
- `docs/history/program/README.md`：把本 closeout 接入 history 索引。

## Current Disposition

| 内容类型 | 当前归位 |
| --- | --- |
| Current status / owner boundary | `docs/status.md`、核心五件套、live MAS/OPL outputs |
| Active gap / completion plan | `docs/active/mas-ideal-state-gap-plan.md` |
| Docs lifecycle rule | `docs/docs_portfolio_consolidation.md` |
| Runtime entry / agent-facing contract | `docs/runtime/contracts/agent_runtime_interface.md` |
| Runtime storage / stage-folder closeout evidence | `docs/runtime/domain_authority_refs_index_guard.md` |
| Dated coverage ledger | `docs/history/docs-portfolio-coverage-ledger/` |
| Old Hermes/MDS/local scheduler/Phase process | `docs/history/**`、MDS references、runtime-governance references |

## Verification Scope

Docs-only verification for this closeout:

- `rtk git diff --check`
- `rtk find docs -maxdepth 3 -type f | sort`
- conflict marker scan over `docs` and `README.md`

未运行 full tests。原因：本轮未修改 source、contracts、tests 或 runtime semantics。

## Remaining Risk

- 本轮没有逐篇压缩所有 runtime/control/projection/display 长文档；仍可能存在 support 层的长历史段落，后续按具体 owner doc 分批处理。
- `docs/status.md` 中最近一次已记录 live audit 仍可能随 runtime 变化而过期；任何状态答复必须重新读取 live surfaces。
- History/provenance 文档保留 Hermes/MDS/legacy wording 是预期行为；它们不能作为 current truth。
