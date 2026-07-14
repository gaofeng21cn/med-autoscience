# 活跃文档

Owner: `MedAutoScience`
Purpose: `active_execution_and_gap_index`
State: `active_support`
Machine boundary: 人读索引。机器真相归 declarative pack、contracts、唯一 authority function、OPL runtime ledgers、study workspaces、publication artifacts 与 owner receipts。

本目录只承接当前执行、当前差距与仍有效的验收边界。唯一结构完成度 owner 是
[MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)。旧 migration、
private-control-plane、runtime implementation 和 dated proof 流水归 Git 或
`docs/history/**`，不得从 active 文档恢复实现。

## 当前入口

- [MAS 理想目标态差距与完善计划](./mas-ideal-state-gap-plan.md)：唯一结构完成度矩阵与 Live Evidence tail。
- [MAS Current Development Lines](./current-development-lines.md)：只列当前维护线，不维护第二 backlog。
- [MAS Executor-First 重构边界](./mas_executor_first_rearchitecture_program.md)：完成后的 no-resurrection guard。
- [MAS Stage Surface Standardization](./stage_surface_standardization_program.md)：declarative Stage/Review/route 形态。
- [AI-first Paper Autonomy Closure](./ai_first_paper_autonomy_closure_program.md)：真实论文线验收合同。
- [OPL App MAS Workbench Boundary](./opl_app_mas_runtime_workbench_program.md)：OPL-owned App 只读投影边界。
- [Program Portfolio Consolidation](./program_portfolio_consolidation.md)：这些稳定路径的唯一职责。

## 当前层次

| 层次 | Owner | 当前作用 |
| --- | --- | --- |
| Repo/source 结构 | MAS maintainers | 保持 declarative pack + one authority function，阻止 private runtime/wrapper 复活 |
| Generated/runtime platform | OPL | CLI/MCP/Skill/status/workbench、StageRun/Attempt、StateIndex、lifecycle、provider/package transport |
| Domain authority | MAS | 医学 truth、quality/publication/artifact/memory 判断与 owner answer |
| Live Evidence | MAS + OPL owner surfaces | 真实 StageRun、paper artifact、independent Review、publication/release readback |

## 放置规则

- 当前结构差距与验收顺序只写入 `mas-ideal-state-gap-plan.md`。
- Stage/Review/route 的稳定声明边界写入 stage support 文档和 machine contracts。
- App/workbench 只记录 OPL-owned projection boundary，不维护 MAS-local UI/runtime实现。
- dated receipts、worktree、commit、命令流水与旧实现说明进入 history/Git。
- Live Evidence 必须写回 runtime/owner/release surface，不用 docs、tests 或 read model代替。
