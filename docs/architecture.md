# 架构概览

Owner: `MedAutoScience`
Purpose: `architecture_current_truth`
State: `active_current_truth`
Machine boundary: 本文解释 owner split。机器边界以 `contracts/domain_descriptor.json`、`contracts/pack_compiler_input.json`、`contracts/generated_surface_handoff.json`、`contracts/action_catalog.json` 与源码为准。

## 目标形态

MAS 是标准 OPL domain agent，不是第二套平台：

```text
MAS declarative pack
  stages / prompts / knowledge / quality gates
  action catalog / schemas / environment requirements
                    |
                    v
OPL generated and hosted surfaces
  CLI / MCP / Skill / product entry / status / workbench
  runtime / StageRun / StateIndex / lifecycle / observability
                    |
                    v
MAS registry-bound authority functions
  medical truth / quality / publication / artifact / memory
  owner receipt / typed blocker / human gate / domain refs
```

canonical agent/package id 固定为 `mas`；machine `domain_id` / `target_domain_id` 固定为 `medautoscience`。`med-autoscience` 仅是 repo/package/plugin locator。生态顶层关系是：

```text
OPL Base        ~= R
OPL App         ~= RStudio / replaceable GUI and deployment carrier
OPL Package     ~= R Package
MAS             = OPL Package(kind=agent)
```

这不是把 MAS 绑定到某个 App 或 executor。OPL 自有并保持 executor-neutral 的边界包括 Package identity、capabilities、required/optional dependency identity、business work item、Temporal refs、用户偏好与 typed views。当前正式路径优先使用 Codex，以最低实现和维护成本获得成熟体验；Codex Plugin 只是首个 carrier projection，Codex CLI 只是首个 executor。替换 carrier 或 executor 不应改变 MAS identity、重装完整 Package，或丢失业务任务与 typed views。

Package、carrier 与 executor 分离：

- MAS owner 独立构建和发布完整 Package bytes 到自身 GHCR，并独立推进 `latest-stable`；共享 Release Set 不定义普通更新 currentness。
- Base 只提供薄 OCI 下载适配器并把 bytes 交给 Package 声明的 carrier/runtime adapter；实际 carrier 负责完整 runtime 的激活/readback，以及所需 Skill/Plugin/config/cache 投影。仅安装 Codex Plugin 不能证明完整 MAS Package 已安装。
- Framework 根据各实际 carrier 的 fresh readback 聚合状态；App 只消费并展示通用状态、Home shortcut、业务 Work Item 和 MAS-owned typed views。
- exact ref/digest 只绑定单次 release artifact、下载完整性或离线/Full/QA 快照，不进入普通 composition readiness。

这是目标边界，不是实现完成声明。当前机器合同、validator 和 readback 仍可能带有 version range、ABI、lock、payload、digest、atomic closure、receipt 或共享 Release Set 字段；在兼容迁移和 retained-consumer 清零前，它们只描述过渡实现，不能反向成为生态长期规则。

## Declarative Medical Research Pack

`agent/` 与机器 contracts 描述：

- 六个与 canonical Stage 一一对应的公开 action、两个无用户 surface 的内部 authority actions，以及各自 input/output schema；
- stage manifest、prompt、knowledge refs 和 quality gate；
- domain route/profile、projection 与 forbidden-write boundary；
- `analysis-display` 环境需求，包括 R/Bioconductor 依赖声明；
- primary skill 与 Codex plugin carrier 的受控镜像关系。

Pack 只声明需求和能力，不实现通用 transport、installer、workspace bootstrap、runtime shell 或 workbench。

`mas-scholar-skills` 是 MAS 的 required capability dependency（硬依赖），不是第六个 Agent。独立仓库形成开发、发布和 owner 边界。普通 composition 只要求 `mas-scholar-skills` identity 存在且 MAS 需要的能力可调用，不做跨包版本范围、ABI 或依赖图求解；缺失或不可调用时仅 MAS readiness fail-closed 并进入托管安装/修复，无关 Package 继续可用。该依赖不得降级为 optional。用户仍通过 `opl packages install/update/uninstall mas` 使用统一入口；MAS 不维护私有安装器或第二套 package lifecycle。

Foundry 系列 policy 只由唯一 OPL Framework 持有。MAS 的 `contracts/foundry_agent_series.json` 是 refs-only consumer contract，只记录 canonical contract refs、policy fingerprint、MAS domain delta 与 false-authority envelope；MAS 不复制 OPL policy body，也不声明本地 Framework 依赖。

Framework Python helper 同样由 OPL 持有。OPL module workflow 在 MAS checkout 维护 `src/opl_framework` carrier；MAS 通过该 namespace 消费，不在 `pyproject.toml` 或 `uv.lock` 声明、安装或锁定 OPL implementation。

`contracts/domain_descriptor.json#/standard_agent_interface` 是 OPL generic consumer 的 MAS-owned machine input。它以 `opl_standard_agent_interface.v1` 声明默认 profile/workspace/project 身份、workspace locator fields、可选 work-item inventory projection、runtime registration ref、progress aliases 与 routing hints；不声明 `entry_command_template`、`manifest_command_template` 或 `runtime.dispatch_command`，也不承载 package lock、provider state、domain truth 或 artifact authority。

### Work-item inventory 边界

MAS 通过 `standard_agent_interface.inventory_projection` 声明病种 workspace 根目录下的 `workspace_index.json#/studies`。该声明只是只读字段映射：`study_id`、canonical study root、MAS 业务状态、当前 Stage 摘要、投稿包状态和 lifecycle/control refs 继续由 MAS workspace truth 生成；OPL 可以读取并与自己的运行账本关联，但不能回写或根据 Temporal attempt 改写这些字段。

Inventory、execution 与 telemetry 是三个独立事实面：

- `workspace_index.json` 回答“这个项目有哪些论文、MAS 当前如何描述它们”；
- OPL execution ledger 回答“当前或历史上有哪些 Stage/Attempt 在运行”；
- OPL usage/telemetry ledger 回答“哪些执行用量已经被观测并可靠归属”。

缺少 execution 或 telemetry 不会让论文从 inventory 消失，也不能把 MAS 业务状态改成运行失败。`inventory_projection` 使用 workspace-relative JSON source，OPL 无需调用或恢复 MAS 已退役的私有 runtime wrapper；`STUDY_STATUS.md` 只作为 lifecycle 人读 ref 传递，机器字段必须直接读取 JSON，不得解析 Markdown 文案。

## OPL 平台职责

OPL 是 generated/default owner：

- 从 V2 Stage action catalog 生成 CLI、MCP、Skill、product-entry 与 harness，并从 closed handler registry 托管最小 authority callable；
- 托管 status、workbench、runtime lifecycle、queue、attempt ledger、retry/dead-letter 与 observability；
- 提供 StageRun、StateIndex、storage/lifecycle 与环境准备；
- 传输 human gate、owner answer、receipt/blocker refs；
- 不写 MAS study truth、quality verdict、publication authority、artifact body 或 memory body。

MAS 的 runtime 边界是单向的：MAS 生成 typed domain-route request / handoff，OPL host 负责 attempt submission、Temporal admission、查询与进程生命周期；MAS 只消费 host 注入的 canonical runtime payload，并按 study、route identity 与 owner authority fail-closed 校验。MAS 不解析 OPL binary、不启动 CLI、不做 live probe，也不把缺失 host receipt 写成已提交或运行中。

Reference provider transport 同样单向：MAS 通过 OPL Framework carrier 调用 `opl connect references verify`，消费 OPL Connect 的 read-only provider receipt；reference authenticity、claim support、publication gate 与 owner consumption 仍归 MAS。

`Codex CLI` 是 stage 内第一公民 executor；其他 executor adapter 必须显式接入，且不承诺质量等价。Temporal 是 hosted durable runtime 的 substrate，属于 OPL 平台边界。

## Stage 内质量循环与 Meta Review

MAS 的六个 canonical Stage 通过
Framework registry 绑定的
`contracts/opl-framework/official-knowledge-deliverable-quality-profile.json`
进入 OPL quality-cycle ABI；MAS 的 `contracts/stage_quality_cycle_policy.json`
只持有各 Stage 的角色、rubric、风险深度与预算扩展。同一
producer thread 内的写后检查只叫 `in_thread_refinement`，不产生 Review
receipt。正式 Stage Review 在同一 StageRun 下创建新的 reviewer
StageAttempt 和 execution session；repairer、re-reviewer 也分别使用新的
Attempt/session，且只消费 exact artifact/source/rubric/lineage refs，不继承
producer conversation。

每个 `stage_quality_cycle_policy_ref` 都解析到严格的 per-Stage policy：Stage
prompt、四角色 prompt、quality rubric、risk/depth、预算和 Attempt boundary
均显式声明，role overlay 只能收窄而不能改写 Stage goal、scope 或 authority。
四个产生开放领域判断或 canonical artifact bytes 的 Stage 要求 formal Review。
`review_and_quality_gate` 本身已经是独立 Meta Review StageRun，因此不递归
再创建一层 formal Review；`finalize_and_publication_handoff` 只对已经完成
Stage Review 与 Meta Review 的 exact bytes 做确定性 inspection packaging，也不
冻结 canonical bytes 或签发 quality/export/publication/ready claim，因此只有
primary Attempt。发现内容缺陷时必须 route-back 到最早 owner Stage，变化后的
bytes 重新完成 fresh Stage Review 与 Meta Review 后才能回到 Handoff。

Handoff 的 `publication_generation` 同时绑定 exact package bytes、
`submission/STATUS.json`、`artifacts/publication_eval/latest.json`、
`control/next_action.json` 和 submission projection manifest。MAS owner receipt 只在
这些成员与六域 review currentness 属于同一 generation 时输出
`artifact_projection_transport` authorization。OPL Pack 随后通过
`opl_pack_materialize_artifact_projection` 在 sibling staging 中校验完整树并整树
切换 `submission/`；禁止先创建 preferred root 再逐文件填充。该 transport 只证明
owner-prepared exact bytes 已被原子搬运，不能生成或提升 MAS status、quality、
publication、submission 或 next-action authority。

跨 Stage 路由仍由 Codex 的领域判断产生，但终局 owner 随 StageRun 形态固定：
primary-only StageRun 的 producer 作决定；启用 formal Review 时，只有终局
reviewer 或 re-reviewer 作决定。在 formal Review StageRun 内，producer、repairer
始终只能给 recommendation；primary-only StageRun 的 producer不受此限制。
仍有 repair budget 且缺陷可在当前 Stage 修复时，`repair_required` reviewer 也只给
recommendation并继续本 Stage 质量循环；若 required finding 的最窄 canonical
owner 是另一个 declared Stage，则 reviewer / re-reviewer 可在预算耗尽前以
`repair_required + route_back` 成为终局 decisive Attempt，这也是预算耗尽前唯一
允许的终局 `repair_required` 路由。预算耗尽且已有可消费 artifact 时，该
reviewer / re-reviewer 同样是终局 decisive Attempt，必须给出 route decision，由 controller 投影
`completed_with_quality_debt`。机器输出统一为
`route_impact.stage_route_decision` / `stage_route_recommendation`；OPL 只校验
Attempt 资格与目标是否为 manifest declared Stage，不解释或改写医学语义。
Reviewer 与 re-reviewer 的质量结果统一写入
`route_impact.stage_quality_cycle.outcome`，取值仅为 `pass`、
`repair_required`、`quality_debt`、`blocked` 或 `human_gate`。Attempt 不输出
receipt `verdict`，也不把 `hard_stop` 当作 outcome；StageRun controller 根据
Attempt identity、独立 session 与 exact reviewed hashes 生成正式
`opl_stage_review_receipt`，其中前三个 outcome 直接映射，`blocked` 与
`human_gate` 仅在 receipt 中映射为 `hard_stop`。

启用 formal Review 的 Stage 默认质量预算是初稿之后最多三轮
`repairer + re_reviewer`。provider retry、
protocol closeout resume 和 owner-callable dispatch retry 不消耗该预算。预算
耗尽但已有可消费产物时以 `completed_with_quality_debt` 推进；质量债继续
阻止 publication、export、submission 或 ready 声明。

`review_and_quality_gate` 是独立 cross-Stage Meta Review StageRun。它不在
reviewer thread 内修稿，而是输出 defect-owner matrix，route-back 到最早能
关闭根因的 canonical Stage，再等待新 generation 和 fresh Review。六个
canonical Stage 与既有八个 paper-study physical Stage 的唯一映射也由该
合同持有；旧 route id 只作 runtime/migration 输入，不形成第二套 Stage 真相。
循环停损、重复失败、human gate、claim-boundary drift 或预算耗尽后的非权威
学习机制统一叫 `strategy_retrospective`，不能产生 Review receipt，也不能
替代 Stage Review 或 cross-Stage Meta Review。

## MAS 保留职责

MAS 的专业能力由 declarative pack、ScholarSkills 与独立 Review 承载；仅保留三个
registry-bound 最小 domain authority functions：candidate admission、paper-mission
evaluation 与 Agent Lab mechanism target-owner closeout：

- study/source readiness 与医学研究语义；
- AI reviewer/auditor 质量记录与 publication gate；
- canonical paper、evidence、artifact mutation 与 memory accept/reject；
- owner receipt、typed blocker、human gate 与 route-back decision；
- exact host-input validation 与医学 owner answer materialization，且不得获得通用 runtime authority。

Retained surface 的机器入口是 closed handler registry、standard conformance profile 与
functional privatization audit；重复 inventory presence 不构成 live-ready 证据。

## Progress control

stage-route owner 固定拆分为：

- `semantic_route_decision_owner=decisive_codex_attempt`
- `stage_transition_materialization_owner=opl_stage_run_controller`

OPL controller 只校验和物化 decisive Attempt 的 route decision，不获得医学语义批准权。MAS owner consumption 解释医学结果。旧 provider admission、current work unit、PaperRecovery、domain-action request 和 repo-local controller shell 只存在于 Git/history provenance，不得重新成为 authority 或 active diagnostic implementation。

## Generated surface handoff

`contracts/generated_surface_handoff.json` 固定以下 ownership：

| Generated/hosted surface | Owner |
| --- | --- |
| CLI / MCP / Skill / product-entry manifest | OPL |
| status read model / workbench drilldown | OPL |
| runtime environment prepare/run | OPL |
| registry-bound minimal authority callable / medical authority result | MAS |

MAS 不再维护 repo-local wrapper parity。新增公开能力时优先绑定 canonical Stage 并更新 catalog/schema；只有无法声明化的医学 authority 才能进入 closed handler registry。OPL 重新生成/托管 surface；MAS 不新增 parser、JSON-RPC transport、installer 或 workbench renderer。

## Live evidence 边界

结构完成与 live acceptance 分账。contracts、tests、descriptor ready、projection clean、queue empty 与 docs 只能证明 repo/source/control-plane。Runtime ready、paper progress、publication ready、provider running 与 production ready 必须有 fresh live/readback/artifact/receipt evidence。

## 相关入口

- [项目概览](./project.md)
- [不可变约束](./invariants.md)
- [Runtime boundary](./runtime/contracts/runtime_boundary.md)
- [Stage outcome runbook](./runtime/control/progress_first_stage_outcome.md)
- [理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md)

## Agent Lab 自进化 owner closeout

MAS 通过 `contracts/agent_lab_self_evolution_policy.json` 提供 OMA fresh Agent
Lab re-evaluation 所需的声明式、SHA 绑定投影。该投影指回
`agent/stages/stage_native_semantic_pack.yaml` 中 canonical `write` Stage
completion policy，定义 high-risk、mechanism-only promotion gate，并声明
target-owner hook command。

`mas.agent-lab-self-evolution-closeout` 是 registry-bound 最小 authority
function。它在 patch 已吸收、验证、清理且完成 fresh re-evaluation 后消费 OPL
work-order execution receipt draft，只返回一个 refs-only outcome：
`domain_receipt`、`no_regression_evidence` 或 `typed_blocker`。该 receipt 只覆盖
target-agent mechanism change；它不改变医学 scorecard，也不能授权 domain、
publication、submission、quality 或 export ready。
