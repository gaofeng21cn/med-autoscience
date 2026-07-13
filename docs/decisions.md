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

## D-07 Framework Python carrier

MAS 不把 OPL Framework 当作自身 Python dependency。OPL module workflow 维护 `src/opl_framework` carrier，MAS 只通过该 namespace 消费；import 不改写 `sys.path`、package path 或 `sys.modules`，构建配置只收集 `med_autoscience*`，不把 carrier vendoring 进 MAS wheel。

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

## D-16 Foundry consumer contract

Foundry 系列 canonical policy 只存在于 OPL Framework。MAS 不声明或安装 Framework policy carrier，只以 `contracts/foundry_agent_series.json` 保存 canonical refs、policy fingerprint、MAS domain delta 和完整 false-authority envelope。

## D-17 ScholarSkills 硬依赖

`mas-scholar-skills` 与 MAS 是产品级一对一硬依赖：MAS 是唯一获得运行兼容性承诺的 required consumer；其他智能体可以只读发现或评估其 refs，但不能据此获得通用 runtime dependency 承诺。代码仓保持独立，package lifecycle 统一走 `opl packages`。OPL 按依赖闭包原子安装、锁定、更新、回滚并保护卸载；MAS 只声明 consumer ABI 和消费 OPL status，不拥有第二套安装器。

## D-18 Standard Agent interface descriptor

默认 profile/workspace/project 身份、workspace binding、direct-entry command template、runtime registration ref、progress aliases 与 routing hints 由 MAS 在 `contracts/domain_descriptor.json#/standard_agent_interface` 按 `opl_standard_agent_interface.v1` 声明，由 OPL generic consumer 验证和消费。OPL 不再从静态 registry 推断 MAS domain body，MAS 也不生成第二套 hosted surface。

## D-20 验证按证据类型去重

Canonical `scripts/verify.sh` 默认只执行一次 line-budget，并把 fast pytest 选集收集一次；smoke/fast Make target 不重复全仓结构扫描。Family boundary case 在同一隔离 pytest invocation 中执行。Table-driven case 必须保留可读稳定 id，且不得合并或削弱 authority、fail-closed 与 zero-write 断言。

## D-19 Provider 与 dispatch transport

Reference provider invocation/retry/cache/receipt 归 OPL Connect；domain-handler transport receipt persistence 归 OPL Runway/Ledger。MAS 只保留医学 reference judgment、domain result、owner receipt/typed blocker signer 与 forbidden-write guard，不在 workspace 创建通用 dispatch receipt store。

## D-18 Stage prompt 自主性与专业依赖

六个 Stage prompt 采用目标/好结果/关键依赖/边界/handoff 形态，不再复制工具目录、固定 `search -> inspect -> sync` 或 specialist checklist。工具顺序由 Codex 在专业依赖内决定；科研预声明、failed-path 留痕、独立 review、canonical-source mutation -> rebuild -> fresh proof、human submission 等因果或 authority 顺序继续由 Stage policy、Skill、quality gate 与 contract 固定。普通质量缺口允许 `completed_with_quality_debt`，ready claim 仍 fail closed。

## 机器入口

- `contracts/domain_descriptor.json`
- `contracts/pack_compiler_input.json`
- `contracts/generated_surface_handoff.json`
- `contracts/action_catalog.json`
- `contracts/authority_kernel_inventory.json`
- `contracts/runtime_environment_requirements.json`
- `contracts/opl_agent_package_manifest.json`
