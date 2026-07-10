# 关键决策

Owner: `MedAutoScience`
Purpose: `current_decisions`
State: `active_current_truth`
Machine boundary: 本文只保留当前有效决策。完整历史与具体变更由 Git provenance、`docs/history/`、contracts 和 runtime receipts 持有。

## D-01 标准 OPL Agent 形态

MAS 的目标形态是 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`。不以已有 caller 为理由保留第二套平台。

## D-02 Identity

canonical id 固定为 `mas`。`med-autoscience` 是 repo/package/plugin locator。

## D-03 Generated surface owner

CLI、MCP、Skill、product-entry、status、workbench 与 functional harness 的 generated/default owner 是 OPL。MAS 提供 action catalog、schema、domain-handler target 和 authority refs/results。

## D-04 Runtime owner

StageRun、queue、attempt ledger、retry/dead-letter、StateIndex、lifecycle/storage、observability、hosted workbench 和环境准备归 OPL。MAS 不维护 local runtime/platform parity。

## D-05 Medical authority

MAS 保留 study/source truth、AI reviewer/publication quality、artifact/memory decision、owner receipt、typed blocker、human gate 与必要 domain-native helper。OPL 只传输和投影这些结果。

## D-06 Next-action authority

默认 next action 只有 `StageOutcome -> NextActionEnvelope`。旧 provider admission、current work unit、PaperRecovery 与 domain-action request producers 退役为 tombstone/provenance，不再作为 current control plane。

## D-07 Standard packaging

Python import 不改写 `sys.path`、package path 或 `sys.modules`。依赖由标准 packaging、`uv sync`、OPL workspace override 与 environment substrate 解决。

## D-08 Standard pytest collection

测试由 pytest 原生递归收集。wildcard aggregate/re-export、nested ignore 与 collection-hygiene 自证 plumbing 不恢复。

## D-09 Environment provisioning

MAS 声明 `analysis-display` requirement profile，并可保留不安装、不修复、不授权 ready 的 read-only environment inspection/projection。OPL `env prepare/run` 负责 Python/R/Bioconductor 环境；repo-local installer、workspace environment builder 与 plugin provisioning 不再是 current surface。

## D-10 Generated catalog and tool surface

Tool Arsenal、capability cards、CLI/MCP schema 与 package interface 从 action metadata 生成。派生 catalog 不手工维护，普通 tool invocation 不在 MAS 建第二套 gate/runtime。

## D-11 Runtime retirement

退役面只保留一个机器可读 no-authority/tombstone guard。live work-order、rollup、currentness、health 与 storage maintenance 归 OPL；不再建设“退役系统的退役系统”。

## D-12 Workbench

用户可见 workbench/status 归 OPL hosted surface。MAS 只输出 body-free refs、owner receipts、typed blockers 与 authority refs，不维护 repo-local markdown/HTML cockpit。

## D-13 Quality independence

执行与 review/audit 必须是独立 invocation、context/task record 与 receipt。程序只验证结构、证据引用和 forbidden writes，不替代 AI reviewer/auditor judgment。

## D-14 Live evidence 分账

repo/source/control-plane structural completion 与 live acceptance 分开。Live evidence 后置不阻塞物理退役，但 paper progress、runtime ready、publication ready、provider running 与 production ready 仍必须 fresh live/readback/artifact/receipt evidence。

## D-15 文档生命周期

核心 docs 只保留 current owner、purpose、state、machine boundary、有效决策和 open gate。dated proof、旧 checklist、receipt id 与过程流水归 Git 或 `docs/history/`，不在 active docs 累积。

## 机器入口

- `contracts/domain_descriptor.json`
- `contracts/pack_compiler_input.json`
- `contracts/generated_surface_handoff.json`
- `contracts/action_catalog.json`
- `contracts/authority_kernel_inventory.json`
- `contracts/runtime_environment_requirements.json`
- `contracts/paper_progress_transition_runtime_completion_audit.json`
