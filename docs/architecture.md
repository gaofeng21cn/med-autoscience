# 架构概览

Owner: `MedAutoScience`
Purpose: `architecture_current_truth`
State: `active_current_truth`
Machine boundary: 本文是人读架构和 owner 边界概览。机器真相继续归 `agent/`、`contracts/`、源码、CLI/MCP/API 行为、product-entry/domain-handler payload、runtime/controller durable surfaces、真实 workspace artifact 与 owner receipts。

## 分层视图

当前架构按三层理解最清楚：

1. 产品层
   - 面向用户的对象是研究问题、工作区、进度反馈和文件交付。
   - `Med Auto Science` 在这一层以独立 medical research domain agent 身份组织同一条课题线，由单一 MAS app skill 承接稳定 callable surface。

2. 操作与集成层
   - `CLI`、`MCP`、`controller`、workspace commands / scripts / contracts 是当前可发现的操作与自动化接口；在 standard OPL Agent 目标形态下，它们只能作为 domain handler target、医学 authority function、owner receipt / typed blocker producer、diagnostic refs 或迁移输入保留。
   - 单一 MAS app skill 负责把这些当前接口承接到 direct path；OPL generated/default callers 接管后，repo-local generic wrapper 不作为长期 capability owner 保留。
   - `OPL`、`product-entry manifest` 和其他机器可读桥接属于上层整合与自动化消费面；对外第一主语继续是 MAS domain agent。
   - `OPL` 是完整智能体运行框架：它提供 stage attempt、queue、wakeup、approval/retry/dead-letter、trace/projection、generated/hosted surface 和 shared module/index 能力，可作为 MAS 外部依赖运行；医学研究 owner 留在 MAS。
   - 在 OPL stage-led family framework 中，MAS stage descriptor、handoff、receipt 和 projection 可以被 OPL 发现和托管；stage 内部的研究拆解、分析探索、写作、审核和路线判断由 repo-root `agent/` 下的 MAS semantic pack、AI reviewer、controller truth 和被选中的 Agent executor 执行，当前第一公民 executor 是 `Codex CLI`。
   - `OPL Runtime Manager` 是 OPL 侧的运行管理/投影层：它接收 MAS 暴露的 task registration、runtime-control projection、status/artifact locator 与 approval/wakeup 边界，再把这些信息挂到 OPL 的 profile、task、resume、doctor 与索引面。Temporal 是 production online runtime 的必需 substrate，也是 MAS hosted autonomous runtime 的默认 provider。MAS 侧通过 `medautosci domain-handler export|dispatch` 暴露受控桥接。高频文件/状态索引可由 OPL native helper 加速；研究真相来源继续是 MAS truth surface。

3. 运行时与持久真相层
   - `Med Auto Science` 持有课题与工作区权威语义、进度语义和发表判断，是唯一研究入口与 owner。
   - OPL provider-backed stage runtime 持有 generic runtime owner / substrate：durable attempt、queue、wakeup、retry/dead-letter、resume、worker residency、transition runner、provider transport 和 generic lifecycle/index。该 hosted autonomous runtime 对 MAS hosted path 默认启用；Codex App 不是外围持续驱动。
   - MAS domain runtime authority surface 持有医学研究 truth、paper-progress SLO 语义、owner receipt、typed blocker、safe action refs、no-forbidden-write evidence、runtime event refs、guarded apply 与 diagnostic refs。current product-entry / domain-handler / read-model 默认面只暴露 `standard_agent_purity` 和 domain refs/receipts/blockers。
   - `Stage` 是一次大型研究步骤；Agent executor 是 stage 内最小执行单位。OPL provider 负责唤醒、signal/query、delivery/approval transport、retry/dead-letter、resume 与 family queue tick；MAS study truth、publication judgment、quality gate 和 artifact authority 继续由 MAS 持有。
   - `MedDeepScientist` 的当前角色是 frozen source archive、historical fixture、explicit archive import / backend-audit reference 与 provenance reference。

历史 MAS-local scheduler、Hermes/MDS、runtime lifecycle/SQLite、workspace-local wrapper 与旧 alias 仅作为 `docs/history/**` provenance、explicit archive/import reference 或 parity oracle 读取；当前默认面是 OPL/Temporal hosted runtime + MAS domain authority refs、owner receipts、typed blockers 和 minimal authority functions。

`contracts/foundry-agent-os-domain-kernel-manifest.json` 是 MAS 对 Foundry Agent OS W4 domain authority kernel 的机器边界。架构层读取它来区分 retained Medical Authority Kernel 与 OPL upcollect surfaces：OPL/Vault/Console/Runway/Pack/Capability Registry 只能承运 refs、generated/hosted surface 和 `current_owner_delta` 投影，不能写 study truth、签 MAS owner receipt、创建 MAS typed blocker 或授权 quality/publication/review verdict。

当前论文推进 SSOT 是 `PaperMissionRun`。`paper-mission inspect|start|resume|consume-candidate`、product-entry `paper_mission/start_or_resume`、domain-handler `paper_mission/start_or_resume` 和 `artifact_first_mission_summary.paper_mission_run` 都只投影同一份 mission contract：`current_mission`、artifact refs / delta ledger、source refs、authority touchpoints、`next_owner`、`required_output`、`consume_candidate_status`、terminal owner answer 或 stable blocker。DM002 / DM003 的旧 truth 通过 `legacy_truth_import_pack` 冻结进 mission input；旧 blocker 只保留为 `legacy_constraints`、`decision_constraints`、`source_refs`、audit trail 和 non-degradation evidence，不能再作为 `current_work_unit.default_execution_state` 或默认 executor 主状态。

OPL 对 `PaperMissionRun` 的职责只到 runtime envelope、StageRun / attempt / queue / provider lifecycle、`current_owner_delta` 投影和 App/workbench drilldown。OPL 可以消费 mission refs、调度 hosted attempt、记录 provider observation、投影 next owner 或把 owner answer refs 折回 `current_owner_delta`；它不能改写 MAS mission truth、物化 MAS owner receipt / typed blocker / human gate、写 `publication_eval/latest.json` / `controller_decisions/latest.json` / current package，也不能把 provider completion、queue 状态、domain diagnostic clean 或 read-model clean 升级成 paper progress、publication-ready 或 submission-ready。

Stage outcome 之后的下一步控制面目标收敛为 [Next Action Control Plane](./runtime/control/next_action_control_plane.md)：`StageOutcome -> NextActionEnvelope`。`NextActionEnvelope` 是 MAS-owned 单一 next action envelope，绑定 exact work-unit identity、owner boundary、target surface 和 forbidden-write boundary；OPL TransitionReceipt 只证明 generic transition transport / closeout，是 MAS owner-consumption input，不能参与选择默认 next action，也不能替代 MAS owner receipt、typed blocker、human gate、paper progress 或 readiness evidence。

## 当前主链路

当前仓库的能力表达继续遵循 `policy -> controller -> overlay -> adapter` 这条主链路。
这条链路服务两个目标：

- 把研究治理、进度判断和交付语义固定在仓库跟踪真相上。
- 把研究执行、运行时底座和上层整合入口分层表达，避免混成一个黑盒运行时。

## 当前用户关心的对象

从用户角度，当前系统围绕四个对象组织：

- 研究问题
- 工作区语境
- 人话进度
- 文件交付

## 当前操作与自动化接口

当前操作路径继续由 `product-entry-status`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 这一组接口组成。

`family_action_catalog` 是 callable action 的 MAS-owned metadata 单一声明面；repo-root OPL standard pack 现在以 `agent/` 作为 canonical repo-source semantic pack，其中 `agent/stages/` + `agent/prompts/` 是标准 OPL Agent stage 主提示词与策略的 canonical source。它把 stage prompt、stage policy、skill policy、knowledge refs、quality gate refs、action catalog、memory/artifact/receipt contract 和 authority boundary 一起声明为 OPL pack compiler 输入。OPL 从该 pack 生成统一 CLI / MCP / Skill / product-entry / tool descriptor bundle，用于 stage-runtime discovery/export/parity；MAS 现有 CLI、MCP、single app skill、product-entry、domain-handler 和 controller 是 generated descriptors 指向的 action target / authority function。MAS action execution、study truth、runtime controller truth、AI reviewer judgment、publication gate 和 artifact authority 留在 MAS。

`study_state_matrix` 是 `family_action_catalog` 中的 read-only materialization action：它把 MAS-owned domain transition table 投影成 `family_transition_spec` 与 `family_transition_matrix_cases`，供 OPL generic `family-transition-runner` 消费。该 action 是 transition read model / materializer，不是 MAS-owned generic state-machine runner；它不写 study truth、不执行 domain action、不签 owner receipt、不授权 publication quality、artifact authority 或 submission readiness。

`family_stage_control_plane` 是 OPL 标准可发现 stage descriptor；`family_stage_control_plane_descriptor` 是 Stage-Led Autonomy 的 MAS-owned 深度 descriptor projection。二者都从 `agent/stages/stage_route_contract.yaml`、`agent/prompts/*.md`、`agent/stages/*.policy.md`、`agent/skills/*.md`、`agent/quality_gates/*.md`、`agent/knowledge/*.md` 和 `stage_knowledge_plane_contract` 派生 route snapshot、stage packets、memory closeout/router/recall、evidence/review/controller/publication refs 与 `authority_boundary`。`src/med_autoscience/overlay/templates/*.SKILL.md` 与运行时 `.codex/skills/medical-research-*` 只是 Codex 自动发现/兼容投影，不是 stage prompt source，也不是 professional specialist skill source。OPL 可以读取这些 canonical source 和 projection 做 OPL stage-runtime indexing、display、freshness check、admission proof 和 MAS-exported task discovery；route、study truth、evidence promotion 和 publication quality / submission readiness 继续由 MAS owner surfaces 授权。

`medautosci domain-handler export|dispatch` 是 OPL family runtime provider 到 MAS owner surface 的受控桥接：export 投影 MAS domain runtime/status/source refs 与 pending family tasks，dispatch 接收 allowlisted task 并回到 OPL-dispatched MAS controller/domain owner chain 产出 receipt。`MCP`、action catalog、skill command projection、plugin manifest 与 product-entry manifest 都是 entry/projection surface；study truth、publication quality、quality gate、artifact authority、paper package、`progress_projection` 和 `domain_diagnostic_report` 由 MAS authority / diagnostic surfaces 持有。

`stage_outcome_authority` 与 `paper_repair_executor` 是 retained MAS authority boundary，不是 repo-local attempt loop、queue consumer 或 private retry runner。任何 `apply=True` 的 owner action / paper repair 执行都必须携带 OPL provider attempt、lease 或 receipt proof；缺失时 MAS fail-closed，产出 `opl_execution_authorization_required` typed blocker，并保留医学 domain authority、artifact mutation authorization、owner receipt / typed blocker 签发边界。OPL provider completion、lease 或 receipt proof 只授权进入 MAS owner surface，不等于 publication quality、paper closure、artifact mutation authorization 或 `current_package` 更新。

`medautosci domain-handler export` 同时暴露 `opl_substrate_adapter`，把 MAS 现有 workspace/source/artifact/memory 数据管理面薄化为 OPL generic substrate 可消费的 opaque/index-only refs。该 adapter 只声明 `workspace_refs`、`source_refs`、`artifact_refs`、`memory_refs`、locator/lifecycle/projection policy 与 authority boundary；不输出 memory body、evidence/review ledger body、publication verdict 或 artifact blob。OPL 可以基于这些 refs 做 locator、index、lifecycle 和 projection；MAS 继续持有 study truth、memory body、evidence ledger、review ledger、publication authority 和 artifact authority。

MAS 在 stage-led OPL framework 下的可调用路线保持 direct skill 等价：直接通过 MAS app skill 调用，或通过 OPL stage/queue/handoff 调用，最终都回到同一套 MAS-owned stage entry、controller、ledger、review、route decision 与 artifact surface。OPL 持有 framework-level attempt/receipt/projection metadata；医学 research memory、evidence ledger、review ledger、publication verdict 和 current package authority 留在 MAS。

用户可见进度展示归 OPL hosted workbench / App shell 承载。MAS 不再维护 repo-local Progress Portal materializer、静态 HTML 入口、HTTP service、action endpoint 或运行控制面；MAS 只输出 `study-progress`、`paper-mission`、current-control handoff refs、owner receipt / typed blocker refs 和 body-free projection JSON。OPL App 需要统一进度看板、长期托管、跨域唤醒或统一状态面时，消费这些 MAS refs 并索引为 OPL stage-runtime dashboard / runtime status；study truth、publication judgment 和 evidence ledger 继续由 MAS 持有。

## Foundry Agent series profile

MAS 的 OPL series design profile 固化在 `contracts/foundry_agent_series.json#/series_design_profile`。该字段现在是 OPL Foundry Agent 系列的 canonical 机器签名，和 MAG、RCA、OMA 完全同形：共享 domain material intake、domain pack interpretation、stage-led execution、independent gate / owner review、owner receipt / typed blocker closeout、artifact / deliverable handoff 与 OPL refs-only projection / recovery。医学研究差异写在 `contracts/foundry_agent_series.json#/domain_specific_profile` 和 MAS-owned stage/action/authority refs 中：MAS 输入是医学研究问题、workspace/study truth refs、source readiness、evidence/review/claim boundary、publication-route memory 与 human/PI decision refs；输出是 research evidence pack、manuscript/display delta、AI reviewer/auditor record、publication gate/route-back、artifact lineage/package refs 与 owner receipt 或 stable typed blocker。

`contracts/foundry_agent_series.json#/workspace_topology_profile` 绑定 OPL-owned workspace topology envelope：MAS workspace mode 是 `portfolio`，project collection path 是 `studies`，stage-native 默认输出根是 `artifacts/stage_outputs`。该字段只声明 OPL 如何读取 workspace group / project unit / stage artifact unit 和 refs-only projection 边界；真实 study truth、artifact body、product view、owner receipt、typed blocker、quality/export verdict 仍由 MAS domain-owned surfaces 持有。

这个 profile 不改变 owner split。OPL 持有 refs projection、runtime lifecycle、generated/hosted surfaces 和 App/workbench shell；MAS 持有 study truth、publication quality、artifact authority、publication-route memory authority、source readiness 和 owner receipt。OPL 可以读取和投影 refs、调度 stage attempt、承载 wakeup/retry/resume，但不能写 study truth、声明 publication quality、授权 artifact mutation 或接受/拒绝 memory body。

## Workspace / file lifecycle 结构

MAS repo-source 目录按标准 domain agent 职责分层：

- `agent/`：医学研究 declarative pack；`agent/stages/` + `agent/prompts/` 持有 stage 主提示词/策略 canonical source，`agent/skills/`、knowledge refs 与 quality gate refs 提供 app-skill / projection / gate 输入。
- `contracts/`：机器合同、schema、descriptor、locator/index contract、receipt ref contract 与 restore/retention policy。
- `runtime/authority_functions/`：最小医学 authority function 的 runtime-facing anchor；只暴露 action metadata、owner receipt refs、typed blocker refs、no-regression refs 或 guarded apply refs，不承载 runtime artifact root。
- `src/`：MAS domain handler、AI-first authority adapter、receipt signer、typed blocker materializer 与 native helper implementation；不能扩展成 generic runner、queue、session store 或 workbench。
- `docs/`：人读治理、当前状态、边界说明和 provenance，不作为机器接口。

真实 workspace/file lifecycle 由 OPL generic lifecycle primitive 与 MAS owner authority 分层完成。OPL 持有通用 locator/index、runner/session/workbench shell、retention/restore orchestration 与 projection；MAS repo source 只持有 refs、policy、schema 和 proof。真实 paper/manuscript/package、runtime artifact、receipt instance、workspace state、restore archive、cache、venv、pycache、pytest cache 和 install sync 副产物必须落在受控 study workspace/runtime artifact root 或用户级 runtime state，不能写回开发 checkout。

MAS 的 authority 边界不因 refs-only lifecycle 上收而外移：study truth、publication/quality verdict、AI reviewer judgment、artifact mutation authority、publication-route memory body accept/reject 和 owner receipt 继续由 MAS owner surface 决定；OPL 只能消费 locator、receipt ref、typed blocker 或 no-regression evidence。

科研 lifecycle 审计链不随旧 runtime UX 退役而降级。OPL 可以持有 attempt ledger、file lifecycle shell、generic artifact/memory transport、restore/retention orchestration 和 workbench drilldown；MAS 必须在 reviewer / writer sprint、analysis campaign、publication gate 或 artifact handoff 后留下研究 evidence pack refs、negative / failed-path ledger refs、decision trace refs、artifact lineage / reproducibility refs，或返回命名缺失 ref family 与 route-back owner 的 stable typed blocker。缺这条链时，transport 成功、queue 完成、package 存在或 UI 可见都不能关闭医学研究 authority。

Co-Scientist 论文启发进入 MAS 时，架构落点是 `hypothesis portfolio -> evidence pack -> independent reviewer / human gate -> owner receipt or stable typed blocker`，不是外部 runtime、外部 authority 或 ranking owner。MAS 持有候选假设的医学语义、source readiness、证据包质量、claim restraint、AI reviewer / auditor judgment、publication gate、human/PI decision 和 artifact authority；OPL 只能托管 stage attempt、queue、attempt ledger、refs-only projection、generated/default callers 和 App/workbench shell。Elo、pairwise ranking、proximity cluster、novelty 或 coverage score 只作为 advisory selection / review briefing signal，最多影响探索顺序和候选聚类；缺 MAS owner receipt、独立 reviewer/auditor record、human gate 或 publication gate 时，不能把最高分候选写成 ready、publication-ready、artifact-authorized 或 source-ready。

## 当前自治与质量合同主线

- `study charter` 冻结方向锁定后的自治边界与论文质量合同。
- `evidence_ledger`、`review_ledger`、`publication_eval/latest.json` 负责把证据闭环、审阅闭环和投稿前判断投影成可审计真相。
- `publication_gate` 与 `medical_reporting_audit` 持有机械完整性、交付状态和 reporting blocker 判断；科学质量、审稿 readiness 与 submission-facing 闭环判断由 AI reviewer workflow 持有。
- 主观医学论文文体质量由 AI reviewer workflow 持有：`medical_prose_review` 与 AI reviewer-backed `publication_eval/latest.json` 负责判断医学期刊声音、reader flow、论证节奏、claim restraint 和工作汇报残留；regex / pattern 只作为 `mechanical_safety_flags` 或 reviewer evidence snippets，不单独决定 `medical_journal_prose_style_not_met`。
- AI reviewer-backed `publication_eval/latest.json` 必须回指 manuscript、evidence ledger、review ledger 与 study charter，并使用 `medical_publication_critique_v1` policy；缺少该 provenance 时，下游只能输出 `review_required` / `projection_only`。
- `Research Integrity Layer` 是投稿前 integrity gate input 层：review / publication gate 的 stage hook 先请求 OPL/provider lookup 拉取 Crossref / PubMed / OpenAlex / Semantic Scholar / publisher / Crossmark evidence，MAS gate 再消费 evidence，输出 `reference_verification_attestation`、`claim_citation_support_matrix_v2`、`manuscript_consistency_meta_review` 与 `research_integrity_gate_input_bundle`。它不是独立专业 skill；provider lookup 属 OPL / connector substrate，MAS thin provider client 只可作为 first slice。当前达标条件是每条 reference 至少一个 provider verified，或明确标成 unresolved / needs_review / contradicted / retracted。该层通过 `research-integrity-gate-input`、`research-integrity-reference-verification`、`research-integrity-review-publication-gate-stage-hook` domain entry 以及对应 action catalog read-only descriptor 暴露；MAS 持有医学解释、publication quality consumption、owner receipt、typed blocker、human gate 与 artifact / submission authority。该层只产出 evidence / gate input / blocker candidate，不能写 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、owner receipt、typed blocker、human gate、runtime queue、provider attempt，或声明 publication-ready / submission-ready。
- 初稿质量属于 pre-draft runtime 关注点：写作前应能看到研究问题、数据资产支撑、reporting guideline、display-to-claim map 和 manuscript-native prose 约束；文档只说明这条可运行质量线，不新增 wording gate。
- 产物证明采用 canonical-source-first：manuscript、figures、tables 与 submission package 必须能从 canonical source 重建，artifact rebuild proof 才能支撑交付判断。
- `controller_decisions/latest.json`、`progress_projection`、`domain_diagnostic_report` 负责把运行状态和控制动作沉成可回放记录。

## MAS AI-first Research OS 长线目标

长线目标固定为 `MAS AI-first Research OS`。它是 owner、authority、contract 与验收口径的目标架构，再按可运行能力逐步吸收和替换。

- 当前 target operating architecture 入口是 [MAS / OPL Agent OS 目标运行架构与重构计划](./runtime/designs/mas_opl_agent_os_target_operating_architecture.md)。该计划把目标态明确为 `OPL Agent OS + MAS Declarative Medical Research Pack + MAS Minimal Authority Kernel + Scientific Capability Registry`，并把后续重构拆成 Lane 0 文档/合同入口 + Pack Compiler / generated surface、OPL StageRun durable execution、`current_owner_delta` 默认读面、MAS authority function 收薄、evidence lineage、AI-first Quality OS、Agent Tool Arsenal / Scientific Capability Registry、Workbench UX 和 production evidence soak。它不改变本文 owner boundary：OPL 持有通用 runtime substrate、generated surfaces、Tool Arsenal 和 capability invocation；MAS 持有医学研究 truth 和 authority verdict。
- `MAS Core` 是目标 owner 层：study truth、quality truth、publication truth、artifact truth 与用户可见 truth 都应归 MAS。
- `Progress Runtime Spine` 的顶层目标态见 [MAS / OPL 进度运行时理想蓝图](./runtime/designs/mas_opl_progress_runtime_ideal_blueprint.md)：ordinary progress 必须沿 `DomainIntent -> OPL Command -> OPL Event -> OPL Transactional Outbox -> StageRun / ToolInvocation -> MAS OwnerAnswer -> Derived Projection` 前进。OPL 是 command/event/outbox/fixed-point/StageRun/human gate/state index owner；MAS 是 medical policy、owner answer、quality/artifact/memory/source authority owner；所有 domain diagnostic、Portal、Workbench、trace 和 lineage 都是 derived projection。当前完成口径见 `contracts/paper_progress_transition_runtime_completion_audit.json#/blueprint_l0_l7_functional_acceptance`：L0-L7 的 repo/source/control-plane 功能面已落地为源码、合同、schema/readback shape、tests/replay fixtures、authority=false projection、legacy retirement/rebuild surfaces 和 live-claim harness；live runtime / paper-line acceptance 仍是 deferred evidence，不属于架构层完成声明。
- 顶层“一步到位”验收矩阵由 [MAS 理想目标态差距与完善计划](./active/mas-ideal-state-gap-plan.md) 维护。架构层只固定归属：OPL 基座优化对应 `TransitionRuntime`、`Outbox`、`StageRunKernel`、`StateIndex`、`Tool Arsenal`、`Workbench`；MAS 程序面只保留 `Declarative Medical Research Pack` 和 `Medical Authority Kernel`。完成度百分比必须分成 `repo/source/control-plane` 与 `live acceptance`，结构账的 100% 不能升级为 runtime ready、paper progress、publication-ready、submission-ready 或 production-ready。
- 2026-06-30 readback tail 更新后，`repo:med-autoscience@10d17340d4d374d7eae56b302c09a8ad2ee12b78` 只证明 study-progress receipt consumption 已进入 main，`repo:med-autoscience@37be1f4a88b271fddb78dcd3e43c65535fdaa1ea` 只证明 legacy next-action authority retirement tail 已被 main 吸收。这两项关闭的是 repo/control-plane readback tail；它们不能替代 OPL/Temporal StageRun live readback、MAS owner receipt、stable typed blocker、human gate、route-back evidence、paper/gate/artifact semantic delta、provider running proof 或 live acceptance。
- `Quality OS` 的当前落点是 pre-draft quality runtime、evidence ledger、review ledger 与 AI reviewer-backed `publication_eval/latest.json` 的闭环；真实论文 soak 仍需继续积累。
- `Runtime OS` 的当前落点是 OPL-owned stage/runtime control plane 加 MAS domain authority refs。OPL 持有 attempt、queue、wakeup、provider query、typed closeout、retry/dead-letter、worker residency、human gate transport、current-control-state 和 lifecycle/index；MAS 只持有 DomainIntent / owner route、owner receipt、typed blocker、artifact/source/quality refs、guarded apply receipt、paper-progress SLO 解释与 diagnostic explanation。
- `Agent Tool Arsenal` 是 Runtime OS 与 Capability Registry 之间已落地的 agent-facing invocation ABI。`contracts/agent_tool_arsenal.json` 从 action catalog、MCP tools、owner callable、stage skills、sidecar 和 native helpers 汇总 `ToolArsenalIndex`、`ToolUseCard`、`CapabilityInvocationPlan`、`ToolResultEnvelope` 和 audit trail 的机器边界；MCP 只读 `agent_tool_arsenal` 工具让 autonomous agent 从 `current_owner_delta` 读取 index、card、plan、result schema 或 completeness diagnostic，实际成功工具调用的 `structuredContent` 已统一为 `mas_tool_result_envelope`。OPL 消费该 ABI 做发现、延迟加载、调用和审计；MAS 继续持有医学 truth、authority verdict、owner receipt 和 typed blocker。OPL 品牌模块 taxonomy 归 OPL 持有，MAS 文档中的 tool/card/count 只表示 invocation ABI，不表示新增或复制 OPL brand module owner truth。
- `Capability Module OS` 的目标模型见 [MAS / OPL 外挂能力模块运行模型](./runtime/designs/mas_opl_capability_module_operating_model.md)。MAS 保持医学论文/研究总控和 authority kernel；发表级绘图、数据管理、文献管理、统计分析、组学 workflow、表格、写作辅助、质量审阅和投稿打包等重能力作为 OPL 管理的 capability modules 独立升级。模块必须暴露 descriptor、dependency profile、run-context contract、artifact refs、execution receipt 和 authority false flags；MAS 通过 `current_owner_delta -> capability catalog -> OPL prepare/run -> module receipt -> MAS owner gate` 调用。该能力体系不是 OPL 第 11 个品牌模块，而是 Atlas、Pack、Stagecraft、Runway、Vault、Console、Connect、Workspace、Foundry Lab 和 Charter 共同承载的跨 agent capability substrate。
- `medical-manuscript-writing`、`medical-manuscript-review`、`medical-figure-design`、`medical-figure-style`、`medical-figure-composer`、`medical-research-lit`、`medical-statistical-review`、`medical-table-design`、`medical-submission-prep` 和 `medical-data-governance` 属于 `mas-scholar-skills` professional specialist skill 增强包；`medical-figure-style` / `medical-figure-composer` 是 Display module 下的 dedicated 子 Skill，不新增 MAS active module。它们和工具/connector 默认只产出 candidate refs、execution receipt 或 owner-gate request，不能写 MAS truth、clinical data body、source readiness verdict、owner receipt、typed blocker、human gate、publication eval、controller decision 或 current package。
- `Artifact OS` 固定 canonical-source-first：manuscript、figures、tables、submission package 都从 canonical source 重建，并通过 artifact rebuild proof 支撑交付判断。
- Artifact / lifecycle owner split 固定为：OPL 持有 generic locator/index、retention/restore shell、lifecycle report 和 App/workbench 展示；MAS 持有 artifact mutation authorization、canonical-source rebuild proof、publication-route memory decision、package freshness interpretation 和 current package authority。OPL lifecycle receipt 可以作为 evidence ref 被 MAS 消费，不能直接授权 cleanup apply、artifact mutation、publication readiness 或 submission readiness。
- `Evaluation OS` 的目标是把历史返工转为 AI reviewer calibration corpus、quality regression 与 AI-first drift audit；这些目标项按证据逐步关闭。
- `Observability OS` 面向维护者暴露 drift、trace、route-back、cache freshness、artifact stale 和 runtime recovery，但不成为 authority。

这套目标架构的人工可读 contract 由 `docs/references/mainline/ai_first_research_os_architecture.md` 与 controller surface `ai_first_research_os_architecture_contract` 表达；外部工程依据固定为 ISO/IEC/IEEE 42010、NIST AI RMF、EQUATOR、FAIR、durable execution、OpenTelemetry、G-Eval 与 SRE toil elimination。它不授权新增文档 wording gate。

## Owner Boundary Fitness

MAS 的模块数量已经足够大，单靠文档描述 owner 容易漂移。因此当前架构使用 `mas_mds_architecture_owner_boundary_report`、`module_boundary_audit` 与 architecture fitness functions 防护四类重复 authority 风险：entry projection 越权解释下一步、external oracle 被读成医学质量 owner、observability 输出直接驱动 control、runtime liveness 被多处局部重算。

该 surface 的规则是：

- `mas_core`、`quality_os`、`domain_authority_refs` 才能持有 study truth、quality truth、runtime-domain refs 和 user-visible next action；generic runtime current-control-state 归 OPL。
- `study_progress`、`workspace-cockpit`、`product-entry-status`、product-entry manifest 与 MCP 做 projection；authority 继续在 MAS owner surface。
- `Observability OS` 只提供 evidence、calibration、analytics 和 replay proof，不直接授权 finalize、submission 或 publication readiness。
- External backend / oracle 只保留 explicit backend audit、explicit archive import reference、upstream intake、parity oracle 四类角色。

当前状态一致性合同已经收敛为一条执行链：`StudyTruthKernel/RuntimeHealthKernel -> study_macro_state -> owner_route -> consumer latest -> executor -> rescan`。`study_macro_state` 给出短枚举用户状态，细节进入 `details`；`owner_route` 持有当前可执行 owner、allowed action 和 idempotency key；consumer 和 executor 传播或执行这张票据。下一轮收薄目标是把稳定控制面明确压到 `macro_state + owner_route + receipt_or_blocker + evidence_refs`：细分 runtime reason、supersession reason、publication supervisor phase 和 workbench 文案只能作为 diagnostic / read-model detail，不再扩展成跨入口执行 contract。Artifact lifecycle 属 Artifact OS / maintainability，生成 retention plan、terminal lifecycle dry-run、checksum 与 restore-proof gate；study truth 和论文 authority 留在对应 owner surface。

## Boundary Governance 与自然边界

全仓 `_parts` 目录已经成为当前结构治理的主要观察面。它们表达自然职责边界：controller 薄入口、read-model/projection、publication gate、artifact lifecycle、display contract、CLI parser/command、test case family 等。`boundary_fitness` 把 hard blocking 与 advisory governance 分开：机械 `part/chunk/split` 编号仍是阻断；nested `_parts`、膨胀的 `shared_base.py`、接近 1000 行的单个 part、`exec(compile(...))` 拼接加载先作为 advisory 报告，服务后续自然边界拆分计划。

这组治理信号保持当前 authority API / contract / generated descriptor 稳定：`CLI`、`MCP`、controller callable surface、product-entry payload、manifest/schema 与当前测试入口按 owner 边界维护。已退役 import facade、compat alias、legacy wrapper 和旧聚合入口只保留 history / tombstone / provenance 语境，不作为 public contract 继续保护。后续 lane 若处理 advisory，在对应 owner 边界内把内部实现迁到更清晰的 importable module、case module 或 shared helper family；study truth、publication truth、runtime truth、artifact authority 和用户可见 next action 继续由对应 authority 持有。

live artifacts 不属于本治理面的写集。`publication_eval/latest.json`、`controller_decisions/latest.json`、`progress_projection`、`domain_diagnostic_report`、`current_package`、submission package、restore archives 与真实 workspace 产物都继续由 stable runtime / controller / canonical artifact flow 持有。Boundary governance 只报告 repo-tracked source/test/docs 的维护风险，不触碰或重生成 live study artifact。

## 当前架构明确保留的边界

- `Med Auto Science` 负责研究工作线，并保持唯一入口与 owner 身份。
- `OPL` 负责 OPL stage-runtime session/runtime/projection、generated/hosted surfaces 与 shared modules/contracts/indexes 的上层整合。
- `OPL` 的 stage-led framework 语义取代旧 gateway / federation 定位；对外第一身份是 `Med Auto Science` domain agent。
- `MedDeepScientist` 只保留 frozen source archive / historical fixture / explicit archive import reference / provenance reference 角色。
- 运行时底座、后端执行和产品入口继续分层表达。
- 迁移、解构、切换和历史推进记录继续留在 `docs/history/**`；当前架构页只承载当前 owner 边界。
