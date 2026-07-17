# 关键决策

Owner: `MedAutoScience`
Purpose: `current_decisions`
State: `active_current_truth`
Machine boundary: 本文只保留当前有效决策。完整历史与具体变更由 Git provenance、`docs/history/`、contracts 和 runtime receipts 持有。

## D-01 标准 OPL Agent 形态

MAS 的目标形态是 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal registry-bound authority functions`。不以已有 caller 为理由保留第二套平台。

## D-02 Identity

canonical agent/package id 固定为 `mas`；machine `domain_id` / `target_domain_id` 固定为 `medautoscience`。`med-autoscience` 是 repo/package/plugin locator。

## D-03 Generated surface owner

CLI、MCP、Skill、product-entry、status、workbench 与 functional harness 的 generated/default owner 是 OPL。MAS 提供 action catalog、schema、domain-handler target 和 authority refs/results。

## D-04 Runtime owner

StageRun、queue、attempt ledger、retry/dead-letter、StateIndex、lifecycle/storage、observability、hosted workbench 和环境准备归 OPL。MAS 不维护 local runtime/platform parity。

## D-05 Medical authority

MAS 的 declarative policy、ScholarSkills 与独立 Review 持有 study/source、quality、publication、artifact 与 memory 语义；三个 registry-bound authority functions 形成 owner receipt、route-back、quality debt、typed blocker 或 human gate。OPL 只传输和投影这些结果。

## D-06 Next-action authority

route owner 拆为 `semantic_route_decision_owner=decisive_codex_attempt` 与 `stage_transition_materialization_owner=opl_stage_run_controller`。旧 provider admission、current work unit、PaperRecovery 与 domain-action request producers 只保留 Git/history provenance，不再作为 current control plane。

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

默认 profile/workspace/project 身份、workspace binding、runtime registration ref、progress aliases 与 routing hints 由 MAS 在 `contracts/domain_descriptor.json#/standard_agent_interface` 按 `opl_standard_agent_interface.v1` 声明，由 OPL generic consumer 验证和消费。descriptor 不再声明 `entry_command_template`、`manifest_command_template` 或 `runtime.dispatch_command`；公开执行从六个 V2 Stage action 生成，内部最小 authority callable 只由 closed handler registry 绑定。OPL 不再从静态 registry 推断 MAS domain body，MAS 也不生成第二套 hosted surface。

## D-20 验证按证据类型去重

Canonical `scripts/verify.sh` 默认运行一次只读 tracked-path/no-resurrection hygiene 与完整 pytest collection。全套测试足够小，不再维护 `smoke`、`meta`、`regression` 子 lane 或手写 syntax sweep；结构分析统一交给 `opl quality details`。Table-driven case 必须保留可读稳定 id，且不得合并或削弱 authority、fail-closed 与 zero-write 断言。

## D-21 私有控制面物理退役

MAS active source 只保留 package init、candidate admission、paper mission、self-evolution closeout 三个 registry-bound authority handlers、共享纯校验 helper 与 CSL assets。CLI/MCP/Skill/default domain-handler wrapper、scheduler、runner、queue、session store、lifecycle/SQLite、StateIndex、status/workbench、provider/package transport、NextAction、PaperRecovery、stage terminalizer 和私有 quality validator 全部物理退役。Canonical primary skill 与 plugin carrier 是声明源/分发镜像；authority handlers 是领域裁决函数，均不构成第二控制面。

## D-19 Provider 与 dispatch transport

Reference provider invocation/retry/cache/receipt 归 OPL Connect；domain-handler transport receipt persistence 归 OPL Runway/Ledger。MAS 只保留医学 reference judgment、domain result、owner receipt/typed blocker signer 与 forbidden-write guard，不在 workspace 创建通用 dispatch receipt store。

## D-18 Stage prompt 自主性与专业依赖

六个 Stage prompt 采用目标/好结果/关键依赖/边界/handoff 形态，不再复制工具目录、固定 `search -> inspect -> sync` 或 specialist checklist。工具顺序由 Codex 在专业依赖内决定；科研预声明、failed-path 留痕、独立 review、内容 owner Stage 内的 canonical-source mutation -> rebuild -> fresh proof、human submission 等因果或 authority 顺序继续由 Stage policy、Skill、quality gate 与 contract 固定。Final Handoff 不拥有这条 mutation 链，只能机械封装 exact reviewed bytes；发现缺陷时 route-back。普通质量缺口允许 `completed_with_quality_debt`，ready claim 仍 fail closed。

## D-20 独立上下文 Stage Review

正式 Review 不是 producer thread 内自检。producer 同 thread 内只能做
`in_thread_refinement`；reviewer、repairer、re-reviewer 必须是同一 StageRun
下不同 StageAttempt 和 execution session，Review context 仅由 exact artifact、
source、rubric 与必要 lineage refs 组装。相同基座模型可以复用，但 session
identity 不得复用。`codex exec resume` 只可用于 typed closeout 协议补全，
不得被解释为 Review。

`review_and_quality_gate` 固定为独立 cross-Stage Meta Review，不继承任何
上游生成对话、不内联修复，只输出 defect-owner route。默认最多三轮语义
修订；provider/dispatch retry 与语义质量预算分账。机器真相是
`contracts/stage_quality_cycle_policy.json`。

路由判断不归 StageRun controller：primary-only StageRun 由 producer 返回
终局 decision；formal Review StageRun 由终局 reviewer / re-reviewer 返回
decision，且仅在这种 StageRun 内 producer、repairer 始终只能返回
recommendation。repair-required finding
可在当前 Stage 修复且预算尚存时，reviewer / re-reviewer 也只 recommendation；
若最窄 canonical owner 是另一个 declared Stage，则它可在预算耗尽前以
`repair_required + route_back` 成为终局 decisive Attempt，且不能选择其他终局
route。OPL 只拒绝越权角色、未声明 Stage target 或非法 shape，并保留
其余 artifact / finding / repair 进展。Meta Review producer 与 Final Handoff
producer 都属于 primary-only decisive Attempt，但前者负责跨 Stage 根因判断，
后者只运输 exact reviewed refs，不能借路由权扩张交付 authority。

每个 Stage 的 policy 必须完整满足 Framework `stage-quality-cycle-policy.v1`
shape，显式绑定 Stage prompt、四角色 prompt、rubric、risk/depth、预算与
Attempt boundary。四个产生开放判断或 canonical bytes 的 Stage 启用 formal
Review；Meta Review Stage 不递归 Review 自身，机械封装且保留下游 acceptance
的 Final Handoff 也不再重复 Review。旧 `triggered_meta_review` 只作为历史分类标签保留，active
机器术语统一为非权威 `strategy_retrospective`，不得与正式 Review 混用。

## 机器入口

- `contracts/domain_descriptor.json`
- `contracts/pack_compiler_input.json`
- `contracts/generated_surface_handoff.json`
- `contracts/action_catalog.json`
- `contracts/domain_handler_registry.json`
- `contracts/standard_agent_conformance_profile.json`
- `contracts/runtime_environment_requirements.json`
- `contracts/opl_agent_package_manifest.json`
