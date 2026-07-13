# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读完成度矩阵。机器事实归 contracts、source、tests、OPL generated/readback surfaces、workspace artifacts 与 owner receipts。
Date: `2026-07-12`

## 目标态

MAS 的 repo 目标形态固定为：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`

canonical id 是 `mas`。OPL 从 MAS pack、action catalog 与 schemas 生成或托管通用 interface/runtime；MAS 只保留 domain-handler targets 和医学 authority functions。

## 完成度口径

- `done`：repo/source/control-plane 结构目标已经落地，并有当前 machine surface 或 no-active-caller/retirement guard。
- `partial`：结构 closeout acceptance 尚未完成；不反向恢复已退役的 MAS-local platform。Live/runtime/owner evidence 另列为 `partial_deferred`，不与结构状态混算。
- 本矩阵不把 docs、tests、descriptor ready、queue empty、projection clean、dry-run 或 candidate package写成 live ready。

## OE-01 至 OE-12

| ID | 原过度设计 | 当前处理 | 状态 | 当前证据入口 |
| --- | --- | --- | --- | --- |
| OE-01 | 无调用代码与空导出 | 删除无生产 caller 的 ports/policy 与无效 export | `done` | source caller scan、retirement diff |
| OE-02 | 未消费的打包/生成资产 | 删除未消费 block 与 repo-tracked generated display catalog；MAS whitepaper builder 已删除，OPL generic runner 消费 domain profile | `done` | package inventory、OPL runner、最终 whitepaper bytes/render fingerprint |
| OE-03 | MAS-local StateIndex pilot | 持久化已上收到 OPL；MAS 仍有 ref normalize/hash active caller，等待 OPL public normalizer | `partial` | `opl_domain_pack.state_index_source_refs`、OPL StateIndex readback |
| OE-04 | import-time editable bootstrap | 已删除 `sitecustomize.py` 与旧 runtime/editable clean runner；回归标准 Python packaging、`uv` native isolated no-project execution 与 OPL workspace override。`scripts/run-build-clean.sh` 继续作为正式 build-isolation runner | `done` | `pyproject.toml`、native `uv` checkout-zero-cache proof、bootstrap absence guard |
| OE-05 | pytest wildcard 聚合收集 | 恢复 pytest 原生递归收集，删除 re-export plumbing | `done` | pytest collection、test-lane manifest |
| OE-06 | 本地环境/installer/plugin provisioning | MAS 只声明 requirement profile并保留不安装、不修复、不授权 ready 的只读环境检查；overlay installer 已删除，OPL `env prepare/run` 与 Connect 负责 Python/R/Bioconductor 和 skill sync | `done` | `contracts/runtime_environment_requirements.json`、OPL Connect receipt、no-provisioning guard |
| OE-07 | “退役系统的退役系统” | 收为最小 no-authority/tombstone guard；compact functional audit 由 OPL 动态消费，旧生成链已删除 | `done` | compact audit contract、runtime retirement inventory、legacy tombstones |
| OE-08 | repo-local Workbench/cockpit | 删除本地 UI/render shell与 compatibility caller；OPL hosted workbench 只消费 body-free refs | `done` | `contracts/domain_descriptor.json`、generated surface handoff、caller scan |
| OE-09 | Tool Arsenal/Capability Runtime | action metadata 成为单一输入，由 OPL 生成 tool/interface surface | `done` | `contracts/action_catalog.json`、pack compiler input |
| OE-10 | 手写 CLI/MCP glue | OPL 从六个公开 Stage action 生成 CLI/MCP/Skill/product-entry，并从 closed registry 托管内部 authority callable；V2 default target 不再指向旧 domain entry | `done` | domain descriptor、V2 action catalog、handler registry、OPL generated stage plane |
| OE-11 | MAS runtime health/lifecycle/storage | provider/readiness builder 与 dispatch persistence 已退役；current-control 聚合、workspace/status materialization、Display transport、gate DAG 仍待迁 OPL public carrier | `partial` | standard interface descriptor、OPL carrier imports、active-caller scan |
| OE-12 | 旧 next-action 控制面族 | 默认 authority 收敛到 `Codex CLI selected stage -> nonbinding route context`；旧 producer 物理退役或 tombstone-only | `done` | next-action contract、runtime completion audit、legacy tombstones |

OE-01 至 OE-12 中 OE-03、OE-11 当前为 `partial`；此前 12/12 `done` 的结论已由 2026-07-12 active-caller 复审核正。已有历史 L1-L5 closeout 仍作为当时证据保留，但不能覆盖本轮发现的真实调用链残留。

## 2026-07-12 标准智能体边界 tranche

| ID | 迁移项 | 状态 | Fresh evidence |
| --- | --- | --- | --- |
| B1 | `standard_agent_interface` descriptor + package manifest ref | `done` | machine contract + focused consumer tests |
| B2 | OPL Framework public contract builders | `done` | `opl_framework.family_entry_contracts` active imports |
| B3 | domain-handler transport receipt persistence | `done` | private store deleted；result declares OPL transport owner |
| B4 | provider/Temporal/readiness export bundle | `done` | 5 adapter modules deleted；export only emits runtime handoff refs/intent |
| B5 | scientific provider transport | `done` | MAS HTTP adapters deleted；OPL Connect canonical receipt consumed |
| B6 | current-control/StageAttempt readback | `partial` | OPL canonical Python readback/identity carrier prerequisite |
| B7 | Workspace/Stage Folder/status + Display transport | `partial` | OPL Workspace/Stagecraft/Runway Python/generated carrier prerequisite |
| B8 | gate-clearing DAG + StateIndex normalizer | `partial` | OPL Stagecraft/Ledger public interface prerequisite |

上述结构状态只覆盖 repo/source/control-plane；不表示 runtime、paper line、publication、submission 或 production ready。

## 2026-07-13 hosted authority tranche

| ID | 迁移项 | 状态 | Fresh evidence |
| --- | --- | --- | --- |
| H1 | `paper_mission` / `mainline_*` / private transport active behavior inventory 与 parity machine contract | `done` | `contracts/paper_mission_authority_handler_parity.json` |
| H2 | 纯 MAS-owned `paper_mission` authority callable、strict input/output schemas、closed registry binding | `done` | `src/med_autoscience/authority_handlers/paper_mission.py`、`contracts/domain_handler_registry.json`、focused terminal/no-effect tests |
| H3 | OPL v2 hosted callable execution、SHA-bound input、contained exact-result commit、refs-only ledger | `partial` | registry/ABI 与 callable closure 已通过；等待 hosted terminal smoke、exact-result commit 与 readback |
| H4 | V2 public/default caller cutover；退役 public V1 `source_command` 与 `domain_handler_export/dispatch`、`mainline_status/phase` actions | `done` | `family-action-catalog.v2`、六个 Stage binding、closed registry、无 private command template 的 descriptor |
| H5 | 迁移遗留内部 callers，并物理删除旧 discovery/readback/persistence、status/read-model、queue/daemon、module healthcheck/bootstrap 与 domain-entry transport | `partial` | fresh source-closure：callable 可达 effect 为 0，但 534 个不可达 legacy generic effects、27 条 unresolved edges、534 条 audit mismatch 仍阻断 verified-zero 与 physical-delete authorization |

H2/H4 证明 MAS V2 registry 与 public/default surface 已切换，不证明 hosted runtime 已完成，也不证明旧源码物理清零。旧 transport 与医学行为在 H3/H5 关闭前继续作为迁移 residue；新 callable 不拥有 profile/path discovery、通用 I/O、queue/session/DAG、spawn、OPL/Codex 调用或 runtime ledger。

冻结 `MAS@bb8c5ed97cd8e7f2a9c82d7dc087e6b471af7d05` / `OPL@64fbe809f8ea958410bce0f7c0a9de305ef5c5e5` 的 fresh readback 已证明 interfaces ready、scaffold passed、8/8 generated default surfaces ready、8/8 retirement gates closed，且 residue decision item 为 0。由于 source-closure 尚未 verified zero，residue 状态仍是 `not_verified_zero`，这些结构 readback 不授权删除、不替代 hosted smoke，也不构成 domain/production ready claim。

## 当前结构 tranche

| ID | 当前范围 | 状态 | 验收证据 |
| --- | --- | --- | --- |
| L1 | compact functional audit 与 OPL generic whitepaper runner receiver | `done` | compact contract 动态消费、MAS builder 删除、最终 whitepaper bytes/render fingerprint |
| L2 | static stage control plane 到 OPL generated plane | `done` | 6-stage semantic parity、旧 Python/static producer caller 为零 |
| L3 | overlay、installer、sitecustomize 与旧 runtime/editable clean runner cutover | `done` | OPL Connect receipt、native `uv` checkout-zero-cache proof、旧路径 caller 为零；`scripts/run-build-clean.sh` 保留为正式 build-isolation runner |
| L4 | runtime protocol substrate 迁移 | `partial` | `runtime_control/**`、`runtime_protocol/**` 已退役；遗留 `domain_entry/mainline/read-model/queue` 内部 caller 与通用 effect 仍待 source-closure 和物理删除 |
| L5 | V2 双仓最终验证与 closeout | `partial` | frozen-baseline interfaces/source-closure/conformance/default-callers/residue/scaffold readback 已完成；等待 source retirement、MAS candidate 吸收、push/readback 与 worktree cleanup |

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
