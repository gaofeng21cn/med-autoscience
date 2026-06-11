# Display Pack Agent OS 目标架构

Owner: `MedAutoScience`
Purpose: `agent_native_scientific_display_system_target_architecture`
State: `orchestrate_surface_landed_full_os_target_architecture`
Machine boundary: 本文是人读目标架构与 MAS/OPL handoff 文案。机器真相继续归 `contracts/display-pack-contract.v2.json`、`contracts/publication_figure_quality_contract.json`、`contracts/medical_figure_spec_contract.json`、`contracts/figure_polish_lifecycle_contract.json`、真实 paper artifact refs、display pack lock、visual-audit receipt、owner receipt、typed blocker、publication gate，以及 OPL repo 的 Pack OS 合同和 runtime surfaces。

本文描述下一层 Agent-native Scientific Display System。当前已在 MAS main code surface 落地的是 agent-native `display_pack_agent.orchestrate`：它从 `current_owner_delta`、claim refs、data refs、paper target 和 intent 编译 figure intent / figure request，并返回推荐 plan、preflight、quality floor、typed repair route hints 和下一步 callable。除已在 [Display Pack v2 落地状态](./display_pack_v2_landing_status.md) 标为 `landed`、`landed_orchestrate_first` 或 `landed_in_opl_repo` 的能力外，本文中的完整 Display Agent OS、完整 typed repair router、ordinary-path resolver receipt、OPL-hosted pack lock 接入和 publication manifest handoff 都是 `target` / `planned`，不能当作 production-ready、publication-ready 或 domain-ready 的证据。

## 目标

Display Pack Agent OS 的目标是让 autonomous research agent 从当前论文 owner delta 和证据 refs 出发，直接走到可审计的图表产物、质量反馈、修复路由和 publication manifest，而不是让人类或 agent 手工遍历模板目录、猜 renderer、拼 CLI 参数或把视觉审计结果写成散落评论。

模板在这条链路中的角色是 `quality-floor baseline`，不是要求论文需求逐字段精确命中的死合同。Agent resolver 应先保住硬边界，再在接近匹配时把现有模板作为可改造基线输出：`figure_kind` 和显式 `template_id` 是硬选择边界；audit family、paper family、renderer preference、input schema 和 query 是 fit score 与 adaptation hints。这样 Agent 可以在布局、panel 组合、标签、caption、axis/scale presentation、legend、style tokens、facet/split 和 evidence-ref-tied annotation 层做 paper-local customization；但数据值、统计估计、模型估计、claim 内容、evidence mark、source refs、owner receipt、visual audit 替代和 publication readiness 仍然禁止由 Display Pack resolver 改写或授权。

目标运行链路固定为：

```text
current_owner_delta / claim refs / data refs
  -> figure_intent
  -> medical figure spec
  -> template resolver
  -> OPL pack lock
  -> render
  -> QC
  -> visual audit
  -> typed repair router
  -> publication manifest
```

这条链路只定义 display work 的目标操作系统。它不改变 MAS study truth、source/data readiness、paper body、publication quality verdict、owner receipt 或 typed blocker 的 authority owner。

## 目标链路

| 阶段 | 目标输入 | 目标输出 | Owner | 状态 |
| --- | --- | --- | --- | --- |
| Owner delta intake | `current_owner_delta`、claim refs、data refs、paper context refs | display work intent seed | MAS | `landed_orchestrate_surface` |
| Figure intent authoring | claim/data refs、publication role、target figure family | compiled `figure_intent` / future `paper/figure_intent.json` entry | MAS | `landed_orchestrate_surface_persistent_authoring_planned` |
| Medical figure spec | figure intent、template constraints、medical semantics、panel roles | `paper/figure_spec.json` / `paper/figure_specs.json` | MAS | `landed_surface_target_integration_planned` |
| Template resolver | figure spec、style profile、paper family、audit family、pack registry refs | exact template candidate 或 adaptable baseline candidate + adaptation hints + forbidden-authority boundary | MAS intent, OPL registry substrate | `landed_adaptable_baseline_plan_surface_full_resolver_planned` |
| OPL pack lock | pack id/version/source、template refs、asset refs、provenance refs | OPL-owned generic pack lock + MAS refs-only display lock projection | OPL substrate, MAS publication refs | `planned_integration`; OPL generic substrate is `landed_in_opl_repo` |
| Render | locked template, renderer entrypoint, payload refs, style profile | PNG/PDF/layout sidecar/render receipt refs | MAS display runtime, OPL transport | `partly_landed`; agent-native lock integration is `planned` |
| QC | render refs、layout sidecar、QC profile | deterministic QC receipt | MAS display quality | `landed_surface_target_integration_planned` |
| Visual audit | rendered artifact refs、QC refs、journal constraints | visual-audit receipt with findings and impact | MAS quality loop | `landed_surface_target_integration_planned` |
| Typed repair router | QC/audit findings、renderer/template/style/data-boundary class | typed repair candidate, owner route, blocker, or human gate | MAS route authority, OPL transport | `landed_hint_surface_full_router_planned` |
| Publication manifest | cleared refs、lock refs、audit refs、owner receipt or blocker refs | display section in publication manifest / submission manifest refs | MAS publication authority | `partly_landed`; OS-level handoff is `planned` |

## MAS / OPL 边界

MAS 持有医学语义和 publication authority：

- `current_owner_delta` 对 display work 的 domain interpretation；
- claim refs、data refs、figure intent、medical figure grammar、panel semantics 和 paper role；
- source/data readiness、evidence mark boundary、scientific claim boundary 和 artifact mutation authorization；
- layout/readability QC policy、visual-audit finding interpretation、AI/VLM polish lifecycle 和 typed repair classification；
- publication gate、quality verdict、owner receipt、typed blocker、human gate、route-back evidence 和 submission readiness判断；
- `publication manifest` 中与医学论文图表相关的 refs preservation 和 authority boundary。

OPL 持有通用 Pack OS 和 runtime substrate：

- pack registry、pack install、version resolution、cache、distribution 和 provenance capture；
- generic pack lock、asset inventory、lock validation、Workbench display shell 和 cross-domain pack lifecycle；
- runtime adapter、queue / StageRun / attempt ledger、trace transport、observability 和 refs transport；
- OPL-hosted pack lock 与 MAS display refs 的展示、运输、索引和审计投影；
- generic repair task transport 和 workbench route presentation，但不拥有 MAS repair authority。

边界规则：

- OPL 可以运输和展示 MAS refs，不能写 MAS publication truth。
- OPL pack lock 可以证明 pack/version/source/provenance 被解析和固定，不能证明 figure scientific content 正确、visual audit clear、publication-ready 或 submission-ready。
- MAS 可以声明医学 display intent、quality gate 和 publication route，不能把 generic pack registry/install/cache/lock substrate 写成 MAS-owned platform。
- typed repair router 的分类和下一步 owner 由 MAS authority 决定；OPL 只承接可执行任务、trace、attempt、handoff 和 workbench transport。

## Handoff 合同文案

目标 OPL handoff 应采用 refs-only packet，而不是把 MAS 论文真相复制进 OPL Pack OS：

```text
handoff_kind: display_agent_os_pack_handoff
producer: MedAutoScience
consumer: OPL Pack OS
status: orchestrate_surface_landed_full_os_target_planned
input_refs:
  - current_owner_delta_ref
  - claim_refs
  - data_refs
  - figure_intent_ref
  - medical_figure_spec_ref
  - publication_style_profile_ref
requested_opl_capabilities:
  - pack_registry_resolve
  - pack_install_or_cache
  - pack_lock_project
  - renderer_runtime_adapter
  - trace_transport
  - workbench_display_projection
return_refs:
  - opl_pack_lock_ref
  - render_attempt_ref
  - trace_ref
  - workbench_projection_ref
forbidden_authority:
  - write_mas_publication_truth
  - mutate_claim_or_data_truth
  - sign_owner_receipt
  - issue_publication_quality_verdict
  - authorize_artifact_mutation
  - mark_submission_ready
```

MAS 消费 OPL 返回 refs 后，必须回到 MAS display quality loop：render/QC/visual-audit/typed repair/publication gate 继续由 MAS 判断。OPL 的 pack lock、render attempt 或 workbench trace 只能作为 evidence refs，不能升级为 MAS owner receipt、typed blocker 或 publication verdict。

## Typed Repair Router 目标

typed repair router 是 Display Agent OS 的关键未完整落地目标。当前 `orchestrate` / `preflight` 已返回 typed repair route hints，用来降低 Agent 发现和修复摩擦；完整 router 还需要把 QC 和 visual audit findings 转成可执行、可审计、可停止的 repair route，而不是散落的自然语言建议。

目标 repair classes：

- `template_contract_repair`：模板 descriptor、input schema、required exports、renderer entrypoint 或 pack asset 缺口；
- `renderer_output_repair`：PNG/PDF/layout sidecar、font、label、legend、scale、panel composition 或 device 输出缺陷；
- `style_profile_repair`：publication style profile、semantic roles、typography、stroke、grid 或 journal palette drift；
- `medical_semantic_repair`：figure kind、panel role、clinical grouping、endpoint naming 或 claim/data binding 语义问题；
- `data_boundary_blocker`：发现数据、统计值、evidence mark 或 claim truth 需要 owner authority，Display OS 必须停止并返回 typed blocker；
- `human_gate_required`：需要人工审稿、期刊格式判断、不可逆 artifact mutation 或 publication route decision；
- `opl_pack_substrate_issue`：pack registry/cache/install/lock/provenance/runtime adapter 问题，路由给 OPL substrate owner。

router 输出必须包含 finding refs、repair class、owner、allowed writes、forbidden authority、expected receipt shape、idempotency key 和 stop condition。缺这些字段时，只能输出 diagnostic finding，不能进入 ordinary repair execution。

## Adaptable Template Resolver

当前 MAS 已落地的 resolver surface 输出 `template_fit_policy`、`adaptation_required`、`adaptation_hints`、`adaptation_boundary` 和 `minimum_fit_floor`。这些字段的读法是：

- `exact_descriptor_match`：请求的主要 descriptor hint 与模板一致，Agent 可直接进入 preflight/render；
- `adaptable_baseline_not_exact_contract`：模板不是逐字段精确匹配，但满足 hard fit floor，可作为 paper-local customization 的质量下限；
- `adaptation_hints`：指出 audit family、paper family、input schema、renderer preference 或 composition/query 的差异应在哪个层修；
- `adaptation_boundary.allowed_layers`：只允许 presentation / display-payload mapping 层的改造；
- `adaptation_boundary.forbidden_layers`：数据值、统计估计、claim、evidence mark、source refs、owner receipt、visual audit 替代和 publication verdict 均禁止；
- `minimum_fit_floor`：仍要求 figure kind 兼容、显式 template id 命中、确定性 renderer contract 存在、descriptor 有效、forbidden authority boundary 保留。

这让模板成为 Agent 的 low-friction starting point：匹配不完全时仍能推进到 preflight、QC、visual audit 和 typed repair，而不是要求人类理解模板目录后手工选型。重复出现的 paper-local customization 应通过 promotion 进入 pack-level contract、style token、QC 或 golden regression，而不是长期散落在单篇论文 override。

## Landing Gates

本文目标架构要从 `planned` 晋级，至少需要以下 repo-native 证据：

- 机器合同或 source-defined builder 能表达 Display Agent OS handoff packet、resolver receipt、typed repair route 和 publication manifest refs；
- `current_owner_delta` ordinary path 能调用 display capability，并保留 claim/data refs 与 owner identity；
- template resolver 能消费 MAS figure spec 和 OPL pack registry/lock refs，能区分 exact match 与 adaptable baseline，且 fail closed 保留 forbidden authority；
- OPL pack lock refs 能被 MAS display lock / publication manifest 以 refs-only 方式保存；
- render/QC/visual-audit findings 能进入 typed repair router，并产出 owner receipt、typed blocker、human gate、route-back evidence 或 OPL substrate issue；
- focused tests 覆盖 allowed writes、forbidden authority、no publication verdict、no claim/data mutation 和 stale ref rejection；
- 至少一条真实 paper line 或 deterministic scaffold line 给出 render、QC、visual audit、typed repair/publication manifest 的可审计证据链。

未满足这些 gates 前，文档、状态表和决策日志只能写 `planned`、`target`、`target_integration` 或 `landed_surface_target_integration_planned`。

## 不得声明

- 不得把本文当作完整 Display Agent OS 已落地、production-ready、publication-ready 或 domain-ready 的证据；已落地范围限于 agent-native orchestrate surface 与底层 Display Pack v2 能力。
- 不得把 OPL generic Pack OS 的外部落地写成 MAS repo 内部已拥有 generic Pack OS。
- 不得把 OPL pack lock、render attempt、trace、cache hit、workbench projection 或 smoke receipt 写成 MAS publication authority。
- 不得让 visual audit、AI/VLM finding、style drift 或 template score 改写 claim/data/statistics truth。
- 不得用 typed repair router 自动修复需要 owner receipt、human gate、publication gate 或 artifact mutation authorization 的问题。
