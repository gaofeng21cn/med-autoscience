# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读完成度矩阵。机器事实归 contracts、source、tests、OPL generated/readback surfaces、workspace artifacts 与 owner receipts。
Date: `2026-07-11`

## 目标态

MAS 的 repo 目标形态固定为：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`

canonical id 是 `mas`。OPL 从 MAS pack、action catalog 与 schemas 生成或托管通用 interface/runtime；MAS 只保留 domain-handler targets 和医学 authority functions。

## 完成度口径

- `done`：repo/source/control-plane 结构目标已经落地，并有当前 machine surface 或 no-active-caller/retirement guard。
- `partial`：只有 live/runtime/owner evidence 未关闭；不反向恢复已退役的 MAS-local platform。
- 本矩阵不把 docs、tests、descriptor ready、queue empty、projection clean、dry-run 或 candidate package写成 live ready。

## OE-01 至 OE-12

| ID | 原过度设计 | 当前处理 | 状态 | 当前证据入口 |
| --- | --- | --- | --- | --- |
| OE-01 | 无调用代码与空导出 | 删除无生产 caller 的 ports/policy 与无效 export | `done` | source caller scan、retirement diff |
| OE-02 | 未消费的打包/生成资产 | 删除未被 installer 消费的 block 与 repo-tracked generated display catalog | `done` | package inventory、docs link gate |
| OE-03 | MAS-local StateIndex pilot | 上收到 OPL StateIndex；MAS 只保留 body-free source refs | `done` | `contracts/generated_surface_handoff.json`、runtime tombstones |
| OE-04 | import-time editable bootstrap | 回归标准 Python packaging、`uv sync` 与 OPL workspace override | `done` | `pyproject.toml`、bootstrap absence guard |
| OE-05 | pytest wildcard 聚合收集 | 恢复 pytest 原生递归收集，删除 re-export plumbing | `done` | pytest collection、test-lane manifest |
| OE-06 | 本地环境/installer/plugin provisioning | MAS 只声明 requirement profile并保留不安装、不修复、不授权 ready 的只读环境检查；OPL `env prepare/run` 负责 Python/R/Bioconductor 与 plugin sync | `done` | `contracts/runtime_environment_requirements.json`、`contracts/generated_surface_handoff.json`、`study_runtime_analysis_bundle.py` / `workspace_python_environment.py` 的 no-provisioning guard |
| OE-07 | “退役系统的退役系统” | 收为 no-authority/tombstone guard；work-order/rollup/currentness 归 OPL | `done` | runtime retirement inventory、legacy tombstones |
| OE-08 | repo-local Workbench/cockpit | 删除本地 UI/render shell；OPL hosted workbench 消费 body-free refs | `done` | `contracts/domain_descriptor.json`、generated surface handoff |
| OE-09 | Tool Arsenal/Capability Runtime | action metadata 成为单一输入，由 OPL 生成 tool/interface surface | `done` | `contracts/action_catalog.json`、pack compiler input |
| OE-10 | 手写 CLI/MCP glue | OPL 生成 CLI/MCP/Skill/product-entry；MAS 保留 handler targets | `done` | domain descriptor、22-action catalog、schemas |
| OE-11 | MAS runtime health/lifecycle/storage | 上收到 OPL Observability/Lifecycle/StateIndex；MAS 留医学 blocker 与 mutation gate | `done` | generated surface handoff、authority inventory、runtime tombstones |
| OE-12 | 旧 next-action 控制面族 | 默认 authority 收敛到 `StageOutcome -> NextActionEnvelope`；旧 producer 物理退役或 tombstone-only | `done` | next-action contract、runtime completion audit、legacy tombstones |

结构目标完成度：`12/12 done (100%)`。

这个百分比仅覆盖 repo/source/control-plane；不表示 runtime、paper line、publication、submission 或 production ready。

## 保留面

以下不是过度设计删除目标：

- canonical primary skill 与 Codex plugin carrier mirror；
- packaged stage/route/prompt/knowledge/quality-gate declarations；
- owner receipt、typed blocker、human gate；
- AI reviewer/auditor 与 publication gate；
- source readiness、artifact mutation、memory accept/reject；
- minimal domain-native authority helper。

新增保留面必须进入 `contracts/authority_kernel_inventory.json`，写清 active caller、allowed/forbidden writes、不能上收原因与 retirement gate。

## Live evidence tail

State: `partial_deferred`

Live evidence 单独后置，不再作为 repo cleanup backlog。以下 claim 只有 fresh evidence 才能关闭：

| Claim | 必需证据 |
| --- | --- |
| OPL runtime ready | same-identity command/event/outbox/StageRun readback、provider running 与 lifecycle evidence |
| Paper progress | MAS owner receipt、stable typed blocker、human gate、route-back 或 paper/artifact semantic delta |
| Quality/publication ready | independent reviewer/auditor receipt、publication owner verdict 与 current artifact refs |
| Submission/current package ready | submission authority、fresh manifest/package receipt 与 owner readback |
| Production ready | live runtime/readback、restart/retry/dead-letter/long-soak 与 no-forbidden-write proof |

## 后续维护规则

1. 普通 action 只改 catalog/schema/handler target，由 OPL 生成 interface。
2. 通用 runtime、index、lifecycle、environment、observability 和 workbench需求直接路由 OPL，不在 MAS 新建 wrapper。
3. 旧路径只保留机器 tombstone/no-resurrection guard，不新增兼容入口或专测体系。
4. Docs 只维护 current owner、状态与证据边界；dated proof 和 closeout 流水归 Git/history。
5. Live evidence 到来时写回对应 runtime/owner receipt surface，不把它混入结构完成度。

## 相关入口

- [当前状态](../status.md)
- [架构](../architecture.md)
- [不可变约束](../invariants.md)
- [Runtime boundary](../runtime/contracts/runtime_boundary.md)
- [Current development lines](./current-development-lines.md)
- [历史完成台账](../history/program/plan_completion_ledger.md)
