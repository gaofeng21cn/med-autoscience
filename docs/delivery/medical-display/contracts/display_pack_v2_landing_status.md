# Display Pack v2 落地状态

Owner: `MedAutoScience`
Purpose: `display_pack_v2_landing_status_and_e2e_path`
State: `active_delivery_contract_status`
Machine boundary: 人读落地状态与 E2E 使用路径。机器真相继续归 `contracts/display-pack-contract.v2.json`、`contracts/publication_figure_quality_contract.json`、`contracts/medical_figure_spec_contract.json`、`contracts/figure_polish_lifecycle_contract.json`、对应 source validators、`paper/build/display_pack_lock.json`、submission manifest、真实 paper artifact refs、visual-audit receipt、owner receipt 和 publication gate。

本文件回答三个问题：

- Display Pack v2 当前哪些能力已经在 MAS 内落地；
- 一篇真实 MAS paper 应如何从 display intent 走到 locked refs、visual audit、submission manifest；
- 哪些目标已由 OPL repo 的 Pack OS 承接，以及 MAS 如何保持 refs-only 边界。
- 下一层 `next ideal operating model / display agent OS` 当前处于什么 target 状态。

## 当前完成度

当前完成度是 `MAS Display Pack v2 runtime lane complete, P1 default R/ggplot2 renderer promotion landed, OPL Pack OS substrate landed externally, MAS refs-only boundary preserved`。

已落地的 MAS 域内能力：

| 层级 | 当前状态 | 机器真相 |
| --- | --- | --- |
| Pack descriptor contract | `landed` | `contracts/display-pack-contract.v2.json` 要求 `display_pack.toml` 的 pack identity、version、source、owner、license、templates、style/QC/AI/golden/exemplar/provenance 和 `opl_handoff` 字段。 |
| Template descriptor contract | `landed` | `templates/<template_id>/template.toml` 要求 full template id、kind、paper/audit family、renderer、input schema、QC/style refs、exports、execution mode、entrypoint、goldens 和 exemplar refs。 |
| Template discovery / describe | `landed` | `medautosci publication display-pack-templates` 可按 kind、renderer family、audit family、paper family 和 query 列出当前启用模板；`medautosci publication display-pack-template` 返回 descriptor、runtime、source config、renderer assets、golden refs 和 forbidden-authority boundary。list/describe 只读，不执行 renderer、不写 artifact、不签 publication readiness。 |
| Agent-facing capability surface | `landed_orchestrate_first_adaptable_baseline` | `src/med_autoscience/display_pack_agent.py` 暴露 `display-pack-capability-discover`、`display-pack-orchestrate`、`display-pack-figure-plan`、`display-pack-preflight`、`display-pack-render`；同一能力进入 CLI grouped commands、`MedAutoScienceDomainEntry` command contract、`contracts/action_catalog.json`、`contracts/agent_tool_arsenal.json` 和 `domain-handler export.display_pack_agent_capability`。`orchestrate` 从 `current_owner_delta`、claim/data refs、paper target 和 intent 编译 `figure_intent` / `figure_request`，再返回推荐 plan、preflight、quality floor、typed repair routes 和下一步 callable。模板选择采用 `quality-floor baseline` 语义：exact match 直接用，接近匹配则输出 `adaptable_baseline_not_exact_contract`、adaptation hints、allowed/forbidden layers 和 minimum fit floor。Agent 默认走 orchestrate，不要求用户或 Agent 手工理解模板目录。 |
| Paper-level figure quality refs | `landed` | `contracts/publication_figure_quality_contract.json` 索引 `figure_intent`、单图 `figure_spec`、批量 `figure_specs`、style refs、visual audit receipt、figure polish lifecycle 和 AI illustration receipt。 |
| Publication style profile | `landed` | `paper/publication_style_profile.json` 是 paper-owned article-level style-token truth，字段覆盖 `style_profile_id`、`journal_palette_ref`、`palette`、`semantic_roles`、`typography`、`stroke` 和 `grid`。E2E runtime 把同一 profile hash 写入 render request、layout sidecar、每张 figure entry、`display_pack_lock.json` 和 publication manifest，以约束整篇论文的配色、字体、字号、线宽和网格。 |
| Medical figure grammar | `landed` | `contracts/medical_figure_spec_contract.json` / `paper/figure_spec.json` / `paper/figure_specs.json` 绑定 intent、Display Template、figure kind、medical semantics 和 panel roles。 |
| AI/VLM polish lifecycle | `landed` | `contracts/figure_polish_lifecycle_contract.json` / `paper/figure_polish_lifecycle.json` 固定每张图从 `draft_rendered` 到 `publication_manifested` 的有序前缀。 |
| Deterministic E2E path | `landed` | `medautosci publication display-pack-e2e` 从 paper intent/spec、style/overrides 和 Display Pack renderer 生成 artifacts、layout QC、visual-audit receipt、polish lifecycle、artifact manifest、display pack lock 和 publication manifest；runtime 支持 `python_plugin` 和 `subprocess`。 |
| One-shot scaffold render | `landed` | `medautosci publication display-pack-scaffold-render` 可用一个 template id 和 payload JSON 生成最小 paper scaffold，再走正式 E2E materialization 产出 render/QC/audit receipt/lifecycle/display lock/publication manifest。scaffold 只服务试跑和开发验收，不替代 paper intent authoring 或 publication gate。 |
| Golden lower-bound surface | `landed` | `medautosci publication display-pack-golden refresh/check` 通过 scaffold + 正式 E2E 生成 golden manifest。默认 strict match 覆盖 PNG、layout sidecar、deterministic QC status 和 publication style profile hash；PDF bytes 因设备元数据可能变化，只作为 observed-only artifact hash 记录。golden check 不能授权 publication readiness、数据/统计值 mutation 或 visual audit 替代。 |
| R/ggplot2 subprocess runtime protocol | `landed` | `execution_mode = "subprocess"` 的 template descriptor 可通过无 shell argv 执行 `Rscript render.R --request {request_json}` 等命令；runtime 写出 render request/stdout/stderr refs，并强制 PNG/PDF/layout sidecar 后再跑 QC。 |
| Core pack R/ggplot2 template migration | `landed_p0_p1_default` | 当前 55 个 evidence templates 已是默认 R/ggplot2 subprocess renderer：P0 22 个和 P1 promoted 33 个均使用 template-local `render.R`，entrypoint 固定为 `Rscript render.R --request {request_json}`。P1 的 Python 实现保留为 baseline / legacy comparison provenance，不再是默认 renderer。共享 R helper 位于 `display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/`，display lock 记录 `renderer_family`、`execution_mode`、`entrypoint` 和 `render_script_sha256`。P1/P2 分类见 core pack `renderer_migration_ledger.json` 与 [Display Pack Renderer 分层与 R/ggplot2 迁移评估](../plans/display_pack_renderer_migration_assessment.md)。 |
| P1 comparison receipt surface | `landed_legacy_comparison` | `medautosci publication display-pack-render-candidate` 保留为 P1 legacy comparison receipt，可对裸 `display_payload` 生成 request/stdout/stderr、PNG、PDF 和 layout sidecar；结果固定 `candidate_only=true`、`comparison_only=true`、`publication_readiness_verdict=false`，不能替代 promoted default renderer、publication manifest、artifact authority、visual-audit clear、owner receipt 或 publication gate。 |
| Multi-figure batch | `landed` | `paper/figure_specs.json` 可声明多个 figure spec；E2E 默认全量 materialize，`--figure-id` 可选择子集；visual audit、polish lifecycle、artifact manifest 和 publication manifest 均记录多图。 |
| Lock and submission handoff | `landed` | `paper/build/display_pack_lock.json#/publication_figure_quality_refs` 记录 surface path、present/missing 状态和 hash；submission manifest 保留同一 refs block。 |
| OPL Pack OS MAS consumer | `landed_in_opl_repo` | OPL repo 的 `opl pack os mas-display-smoke --contract <mas_repo>/contracts/display-pack-contract.v2.json --json` 可消费 MAS Display Pack v2 contract 并输出 generic pack lock/audit smoke receipt。 |
| OPL generic Pack OS substrate | `landed_in_opl_repo_outside_mas` | OPL repo 已落地 `opl pack os install/registry/cache/distribute/lock/validate/mas-display-smoke`；MAS 只记录外部 refs，不拥有 generic Pack OS，不签 publication authority。 |
| Next ideal operating model / Display Agent OS | `orchestrate_surface_landed_full_os_target_planned` | [Display Pack Agent OS 目标架构](./display_pack_agent_os_target.md) 描述 `current_owner_delta / claim refs / data refs -> figure_intent -> medical figure spec -> template resolver -> OPL pack lock -> render -> QC -> visual audit -> typed repair router -> publication manifest` 的目标链路。当前 MAS main code surface 已落地 agent-native orchestrate 编译、推荐、预检、quality floor 和 typed repair route hints；OPL-hosted pack lock integration、完整 typed repair router、ordinary-path resolver receipt 和 publication manifest handoff 仍是 planned/target。 |

当前 Display Pack v2 不是“模板市场已完成”，也不是“所有 98 个 catalog 模板都有正式 checked-in golden”。它表示 MAS 已有 paper-facing display pack descriptor、paper-level quality refs、article-level style profile lock、R/ggplot2-first subprocess runtime 协议、55 个 core evidence templates 的一等默认 R/ggplot2 subprocess renderer、P1 Python baseline / legacy comparison provenance、P2 Python plugin 兼容 renderer、可发现/可描述/可 scaffold 试跑的 CLI surface、agent-facing orchestrate/discovery/plan/preflight/render receipt surface、adaptable-template baseline resolver、可 refresh/check 的 deterministic lower-bound golden surface、multi-figure deterministic E2E render/QC/publication-manifest path、visual audit / polish lifecycle 和 submission refs preservation 的可验证下界；OPL 侧已有通用 Pack OS install、registry、cache、distribution、lock、validation 和 MAS consumer smoke，MAS 合同只保留外部 substrate refs 和 forbidden-authority 边界。P1 renderer promotion 已落地，但 style profile lock、renderer promotion、display lock、golden match、visual-audit clear、agent orchestration/render receipt 或 comparison receipt 仍不能代签 publication readiness、artifact authority、owner receipt 或 publication gate。

## 目标态

目标态分两层：

1. MAS 持有医学展示 domain authority：模板包 descriptor、医学 figure grammar、paper-level display quality refs、visual-audit / AI/VLM polish lifecycle、figure/table generated artifact refs、publication quality owner receipt 和 forbidden authority boundary。
2. OPL 持有通用 Pack OS substrate：generic pack install、registry、version resolution、lock projection、asset inventory、Workbench display shell、跨 domain pack 分发和 lifecycle transport。

MAS 只把 `opl_handoff` 暴露成 refs-only handoff boundary。OPL repo 已经有带测试的 `mas-display-smoke` consumer projection，可以读取 MAS contract 并生成 generic pack lock/audit smoke receipt；OPL repo 同时已落地通用 install / registry / cache / distribution / lock / validation surfaces。MAS 不能把这些外部基座写成 MAS-owned substrate。

## Next ideal operating model / Display Agent OS

下一层目标运行模型是 Agent-native Scientific Display System。目标链路是：

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

当前状态是 `orchestrate_surface_landed_adaptable_baseline_full_os_target_planned`。它继承已落地的 Display Pack v2 descriptor、paper-level figure-quality refs、medical figure spec、style profile lock、E2E render/QC/manifest path、visual-audit receipt、polish lifecycle 和 OPL repo 外部 Pack OS substrate；MAS main code surface 已提供 `display_pack_agent.orchestrate`，能从 current owner delta 与 claim/data refs 编译 figure intent、推荐 exact template 或 adaptable baseline、预检 paper/style/runtime/QC/golden 下界、返回 typed repair route hints 与下一步 callable。但 OS-level OPL-hosted pack lock integration、完整 resolver receipt、完整 typed repair router 和 publication manifest handoff 还没有完整落地。

MAS / OPL 边界固定为：

- MAS 管医学语义、claim/data refs、figure intent、medical figure grammar、QC/audit policy、typed repair classification、publication gate、quality verdict、owner receipt、typed blocker、human gate 和 publication manifest authority。
- OPL 管 pack registry、install、version resolution、cache、distribution、generic pack lock、provenance、runtime adapter、Workbench display shell、trace transport、StageRun / attempt ledger 和 refs transport。
- OPL 可以返回 pack lock、render attempt、trace 和 workbench projection refs；这些 refs 不能写 MAS publication truth，不能修改 claim/data/statistics truth，不能签 owner receipt，不能授权 artifact mutation、publication-ready 或 submission-ready。

目标文案和晋级门见 [Display Pack Agent OS 目标架构](./display_pack_agent_os_target.md)。后续只有当 source-defined builder、合同、resolver、typed repair router、OPL refs-only lock projection、focused tests 和真实 paper/scaffold evidence 同时覆盖 allowed writes 与 forbidden authority 时，才可以把完整 OS 对应条目从 `target_planned` 晋级为 `landed`。

## E2E 使用路径

一篇 MAS paper 的 Display Pack v2 路径按下面顺序读取。Agent 不需要遍历模板目录；它先消费 `display_pack_agent_capability`，再把 `current_owner_delta`、claim/data refs、paper target 和 intent 交给 orchestrate，获得结构化 `figure_intent`、`figure_request`、推荐 plan、preflight、quality floor、typed repair routes 和下一步 callable。render 仍由同一 capability 的 render mode 执行：

```bash
medautosci publication display-pack-agent-discover --repo-root <mas_repo>
medautosci publication display-pack-agent-orchestrate --repo-root <mas_repo> --paper-root <paper_root> --current-owner-delta-json '<current_owner_delta_json>' --claim-ref <claim_ref> --data-ref <data_ref> --paper-target <journal_or_profile> --intent '<display_intent>'
medautosci publication display-pack-agent-plan --repo-root <mas_repo> --figure-request-json '<figure_request_json>'
medautosci publication display-pack-agent-preflight --repo-root <mas_repo> --paper-root <paper_root> --figure-request-json '<figure_request_json>'
medautosci publication display-pack-agent-render --repo-root <mas_repo> --paper-root <paper_root> --figure-request-json '<figure_request_json>'
```

同一能力也通过 `MedAutoScienceDomainEntry` 暴露给 OPL generated/hosted surfaces。`domain-handler export` 会给出 `display_pack_agent_capability`，`contracts/action_catalog.json` 会把 `display_pack_capability_discover`、`display_pack_orchestrate`、`display_pack_figure_plan`、`display_pack_preflight`、`display_pack_render` 映射到同一个 MCP runtime tool `display_pack_agent`，由 `mode=discover|orchestrate|plan|preflight|render` 选择底层 action surface。CLI 仍是 debug/资产管理入口；MCP `display_pack_agent`、domain entry 和 action catalog 是 agent consumption 的稳定合同面。

模板 resolver 的当前规则是：`figure_kind` 和显式 `template_id` 仍是硬边界；audit family、paper family、preferred renderer、input schema 和 query 参与 fit score 与 adaptation hints。输出为 `exact_descriptor_match` 时可直接进入 preflight；输出为 `adaptable_baseline_not_exact_contract` 时，Agent 可以把该模板作为下限基线继续推进，并在 layout、panel arrangement、label/caption、axis/scale presentation、legend、style tokens、facet/split、evidence-ref-tied annotations 或 display payload mapping 层做 paper-local customization。禁止层固定为 data values、statistical/model estimates、claim content、evidence marks、source refs、owner receipt、visual-audit replacement 和 publication readiness verdict。重复出现的 customization 应 promotion 到 pack contract、style profile、QC 或 golden regression。

| 步骤 | Surface | 完成信号 | 不授权内容 |
| --- | --- | --- | --- |
| 1 | `config/display_packs.toml` / `paper/display_packs.toml` | 论文声明启用 pack、source 和 exact version。 | 不授权图已生成或 publication-ready。 |
| 2 | `display_pack.toml` / `templates/<template_id>/template.toml` | pack/template descriptor 通过 contract，template 绑定 renderer、schema、QC 和 style refs；可用 `medautosci publication display-pack-templates` 搜索，用 `medautosci publication display-pack-template` 查看 runtime 与 assets。 | 不替代 source/data/statistics truth，不执行 renderer。 |
| 3 | `paper/figure_intent.json` | 每个 paper display 绑定 claim ref、data ref、template id 和 kind。 | 不修改 claim、data 或 artifact authority。 |
| 4 | `paper/publication_style_profile.json` | 文章级视觉 token 固定 palette / semantic roles / typography / stroke / grid；E2E render context、R sidecar、display lock 和 publication manifest 记录同一 hash。 | 不是数据、统计值、artifact mutation、publication verdict 或 submission readiness。 |
| 5 | `paper/figure_spec.json` / `paper/figure_specs.json` | MAS-native grammar 绑定 intent、template、figure kind 和医学语义；`figure_specs.json` 支持一次物化多张图。 | 不是 Vega-Lite runtime、renderer 或 publication verdict。 |
| 6 | deterministic render + QC | `medautosci publication display-pack-e2e` 生成 figure refs、PDF/PNG/layout sidecar、layout QC、artifact manifest 和 display pack lock；template 可用 `python_plugin` 或 `subprocess`。 | gate clear 只是下界，不等于视觉完成。 |
| 7 | `paper/figure_visual_audit_receipt.json` | VLM/human/hybrid 审阅真实渲染图，记录 findings、impact、layer、promotion decision 和 verification plan。 | 不签 publication quality，也不授权 artifact mutation。 |
| 8 | `paper/figure_polish_lifecycle.json` | lifecycle 以有序前缀记录 draft、QC、visual audit、revision、audit clear、manifested。AI/VLM event 必须带 `model_ref` 或 `reviewer_ref`。 | AI/VLM event 不能 `mutates_data=true`，不能 `carries_publication_verdict=true`。 |
| 9 | `paper/build/display_pack_lock.json` | lock 保存 pack source/version/hash、`publication_style_profile` lock block 和 `publication_figure_quality_refs` 的 path/status/hash。 | lock 不是 publication verdict、source readiness 或 artifact authority。 |
| 10 | `paper/build/display_pack_publication_manifest.json` / `paper/submission_minimal/submission_manifest.json` | publication manifest 和 submission manifest 保留 lock 中的 figure-quality refs block、style profile lock、audit refs 和 artifact refs。 | refs preservation 不等于 submission-ready。 |
| 11 | MAS owner receipt / publication gate | 独立 reviewer/auditor、publication gate、owner receipt、typed blocker 或 human gate 给出下一步。 | Display Pack surface 不能代签 MAS owner authority。 |

开发或模板验收时，可先用 one-shot scaffold 路径试跑单个模板：

```bash
medautosci publication display-pack-scaffold-render \
  --repo-root <mas_repo> \
  --paper-root <tmp_paper_root> \
  --template-id roc_curve_binary \
  --data-payload-file <payload.json>
```

需要固定 deterministic lower bound 时，使用同一 payload 刷新并检查 golden：

```bash
medautosci publication display-pack-golden refresh \
  --repo-root <mas_repo> \
  --paper-root <tmp_paper_root> \
  --template-id roc_curve_binary \
  --data-payload-file <payload.json> \
  --golden-root <golden_root>

medautosci publication display-pack-golden check \
  --repo-root <mas_repo> \
  --paper-root <tmp_paper_root> \
  --template-id roc_curve_binary \
  --data-payload-file <payload.json> \
  --golden-root <golden_root>
```

## 最小示例

最小结构示例见 [Display Pack v2 E2E Skeleton](../examples/display_pack_v2_e2e_skeleton.md)。该示例只说明字段关系和 authority boundary，不作为 fixture、golden、真实论文证据或测试输入。

## Renderer 执行策略

医学论文 evidence figure 的默认推荐路线是 R/ggplot2-first subprocess renderer，因为医学论文图形社区里高质量模板、期刊风格和统计图实践主要沉淀在 R/ggplot2 生态。`python_plugin` 没有被提升为唯一路线；它只是 host-native renderer、测试 fixture 和部分内部 materializer 的兼容 adapter。

当前 core pack 的 renderer inventory 应分开读：

- 84 个 evidence template descriptor 已注册；
- 55 个 template 标为 `renderer_family = "r_ggplot2"`，并已使用默认 `execution_mode = "subprocess"`；
- 29 个 template 是 `renderer_family = "python"`，均为 P2 retained Python / later dual-stack；
- 55 个 core template 目录已有默认 `render.R`；
- 33 个 P1 template 目录保留 `render_candidate.R` legacy comparison wrapper，可通过 `display-pack-render-candidate` 单独触发 comparison receipt；
- `renderer_migration_ledger.json` 覆盖 84/84 evidence templates：P0 landed 22，P1 default R/ggplot2 promotion landed 33，P2 retained Python / later dual-stack 29，unclassified 0。

P0 迁移已经完成；P1 default R/ggplot2 renderer promotion 也已经完成。后续目标是对 P1 promoted renderer 继续积累 golden diff、visual audit 和 baseline comparison evidence，对 P2 模板继续保留 Python 或按真实论文需求做局部双栈。结构评估和迁移清单见 [Display Pack Renderer 分层与 R/ggplot2 迁移评估](../plans/display_pack_renderer_migration_assessment.md)。

`subprocess` 执行规则：

- template descriptor 写 `execution_mode = "subprocess"` 和 `entrypoint = "Rscript render.R --request {request_json}"` 这类命令；
- runtime 使用 `shlex` 解析 argv，不通过 shell 执行；
- `{request_json}`、`{output_png}`、`{output_pdf}`、`{layout_sidecar}`、`{paper_root}`、`{template_root}`、`{pack_root}` 是固定占位符；
- render request 中包含 `display_payload`、输出路径、template id、figure id 和 renderer family；
- runtime 记录 request/stdout/stderr refs，返回 render_result，并要求 PNG、PDF、layout sidecar 三件套存在后才进入 deterministic QC。

P1 legacy comparison receipt 触发规则：

- CLI/API 入口是 `medautosci publication display-pack-render-candidate --repo-root <repo> --template-id <template> --display-payload-file <payload.json> --output-dir <dir>`；
- template 必须存在 promoted default `render.R` 和 legacy comparison `render_candidate.R`；
- comparison 输出 JSON 固定 `candidate_only=true`、`comparison_only=true`、`publication_readiness_verdict=false`，并记录 request/stdout/stderr、PNG、PDF 和 layout sidecar；
- comparison receipt 不能替代 promoted default renderer、publication manifest、artifact authority、visual-audit clear、owner receipt 或 publication gate。

## MAS / OPL 边界

MAS 保留：

- paper display intent、medical figure grammar、visual audit receipt、AI/VLM polish lifecycle 和 AI illustration hard boundary；
- figure/table generated artifact refs、layout/readability QC refs、display pack lock refs 和 submission manifest refs preservation；
- publication quality、artifact mutation、source readiness、owner receipt、typed blocker、human gate 和 route-back authority。

OPL 可以承接：

- generic pack install / registry / version resolution / cache / distribution；
- lock projection、asset inventory、workbench display 和 lifecycle transport；
- refs-only handoff、owner receipt refs、typed blocker refs、pack/version refs 和 audit refs 的展示或运输。
- 已落地的 `mas-display-smoke` consumer 可以读取 MAS Display Pack v2 contract，输出 generic pack lock/audit smoke receipt。

OPL 不能写 MAS publication truth，MAS 也不把外部 Pack OS substrate 写成 MAS repo 内部能力。

## AI/VLM Audit Lifecycle

AI/VLM 只进入 display quality loop：

1. deterministic render 后，VLM/human/hybrid 审阅真实图像；
2. `figure_visual_audit_receipt` 记录具体 finding；
3. `figure_polish_lifecycle` 把 finding、revision 和 audit-clear 事件绑定到 artifact refs 与 display-pack lock refs；
4. 可复用缺陷向 renderer contract、layout/readability QC、style profile 或 golden regression 下沉；
5. publication verdict 继续由 MAS independent reviewer / publication gate / owner receipt / typed blocker 承接。

AI-generated illustration 只允许 `illustration_shell` 候选，并且 `scientific_claim_carried=false` 是硬边界。证据型 figure 必须走 deterministic renderer/template/data/QC 路径和 visual audit，不用 AI illustration 承载科学 claim。

## 外部项目吸收顺序

外部 display / visualization / paper-figure 项目只能按以下顺序吸收：

1. `link_only_exemplar`：记录公开论文图面或 gallery 的 link-only 参考，不复制脚本、图片、截图或运行时。
2. `style_or_audit_hint`：把可复用的风格、可读性或审计问题写入 style notes、visual-audit guide 或 promotion decision。
3. `template_gap_candidate`：只有真实 MAS paper demand 证明现有 template/QC 不足时，才进入 active board / backlog。
4. `display_pack_descriptor_candidate`：新模板必须有 pack/template descriptor、input schema、renderer family、QC/style refs、golden/exemplar refs 和 authority boundary。
5. `landed_template_or_pack`：只有通过 descriptor validation、materialization、QC、visual audit、lock、submission manifest preservation 和 repo-native verification，才写成 landed。
6. `opl_pack_os_handoff`：OPL `mas-display-smoke` consumer 与 generic install/registry/cache/distribution/lock/validation surfaces 已可消费 MAS refs；这些只能作为 OPL-owned substrate refs，不能在 MAS 文档中写成 MAS 已拥有。

外部项目不能直接成为 MAS runtime、publication owner、quality gate、artifact authority、data/statistics source、claim truth 或 dispatch blocker。

## 不得声明

- 不得声明 Display Pack v2 lock、visual audit clear 或 polish lifecycle 等于 publication-ready、submission-ready、paper closure、domain-ready 或 production-ready。
- 不得声明 `figure_spec.json` 是 renderer、Vega-Lite runtime、data/statistics mutation surface 或 publication verdict。
- 不得声明 AI/VLM audit、style reference 或 illustration receipt 能携带科学 claim、修改 evidence mark 或替代 independent reviewer/auditor。
- 不得声明 OPL Pack OS substrate 已由 MAS repo 落地；当前是 OPL repo 外部落地，MAS 只保留 refs-only handoff 和 forbidden-authority 边界。
- 不得声明完整 Display Agent OS、完整 typed repair router、OPL-hosted pack lock integration 或 publication manifest handoff 已在 MAS main code surface 落地；当前已落地的是 agent-native orchestrate 编译/推荐/预检/typed route hint surface 和底层可复用能力。
- 不得把 link-only external exemplar 写成 MAS template、golden、runtime dependency 或 copied asset。

## 验证口径

修改 Display Pack v2 机器合同或 validators 时，最小验证为：

```bash
rtk ./scripts/run-pytest-clean.sh tests/test_display_pack_v2_contract.py tests/test_display_pack_v2_figure_quality_refs.py tests/test_figure_polish_lifecycle_contract.py tests/test_medical_figure_spec_contract.py tests/test_publication_figure_quality_contract.py -q
rtk make test-meta
rtk ./scripts/verify.sh
rtk git diff --check
```

纯文档状态或示例说明变更可按 `documentation_review_only` 处理，但仍应运行 `rtk git diff --check`；若改动触及合同名、测试名或完成度声明，应至少跑上述 focused pytest 以确认引用没有漂移。
