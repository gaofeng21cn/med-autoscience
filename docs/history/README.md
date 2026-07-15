# 历史归档

Owner: `MedAutoScience`
Purpose: `history_archive_index`
State: `history_index`
Machine boundary: 本目录是人读历史/provenance 索引。当前机器真相继续归 `agent/`、`contracts/`、源码、CLI/MCP/API 行为、runtime/controller durable surfaces、真实 workspace artifact、owner receipts 和当前 owner docs。

本目录保存 repo-tracked 历史材料：dated snapshot、provenance、退役 board、归档 implementation plan 和过程稿。

History 是只读语境，不拥有 active backlog、runtime truth、controller decision、publication readiness、artifact authority 或 policy truth。

NextAction supersession notice：history 中出现的 `current_executable_owner_action`、PaperRecovery、domain transition、provider admission、OPL queue / attempt、current-work-unit 或 current-execution-envelope 只能按 historical provenance、diagnostic、migration input 或 no-resurrection guard 读取。当前默认 next action authority 是 [Next Action Control Plane](../runtime/control/next_action_control_plane.md) 的 `StageOutcome -> NextActionEnvelope`；`OPL TransitionReceipt` 只作 transport receipt-only evidence 和 MAS owner-consumption input。缺 canonical envelope 时不得从历史 surface 补一个隐式 next action。

MAS monolith closeout 之后，旧 MDS / DeepScientist / Hermes-first / 外部 runtime cutover / WebUI / daemon 文档若没有明确 active owner，只能在本目录或 `docs/references/` 中作为 provenance、parity、explicit archive import、backend audit 或历史决策材料保留。读者需要当前状态时，应回到 `docs/status.md`、`docs/architecture.md`、`docs/decisions.md`、`docs/active/program_portfolio_consolidation.md` 和 durable runtime/controller surfaces。

| archive | contents |
| --- | --- |
| [program](./program/README.md) | Closeout、activation package、退役 board 和 dated intake snapshot。 |
| [runtime](./runtime/README.md) | 已完成 runtime implementation plan 和 legacy runtime boundary 记录。 |
| [positioning](./positioning/README.md) | 旧 Domain Harness OS / Open Harness OS / Research Foundry 定位材料；只作历史参考。 |
| [capabilities](./capabilities/README.md) | 能力族历史和退役 medical-display 记录。 |
| [omx](./omx/README.md) | OMX worktree 启动/收尾历史。 |

当前真相从 [文档索引](../README.md)、核心五件套、runtime contracts、policies、`docs/active/` 和 durable runtime/controller surfaces 开始。
