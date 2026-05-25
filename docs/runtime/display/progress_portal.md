# MAS Progress Portal

Status: `landed read-model display surface; OPL App workbench cutover pending`
Owner: `MedAutoScience Product Projection + OPL App integration boundary`
Purpose: `progress_portal_display_contract`
State: `active_runtime_display_contract`
Machine boundary: 本文是人读展示合同。机器真相继续归 MAS controller/domain-authority refs surfaces、Progress Portal payload、product-entry manifest、sidecar receipt、generated HTML/artifact refs、owner receipts 和真实 workspace evidence；runtime drilldown / current-control-state 归 OPL。
Related runtime drilldown owner: `OPL current_control_state`
Related focused lane: `portal-route-decision-trail`

## 入口结论

`MAS Progress Portal` 是面向医生、PI 和研究团队的 workspace-local read-model / diagnostic / no-App 展示入口。它已经落成 MAS-owned payload、HTML materializer、workspace helper 和可选本地只读服务；这些 surface 仍是 `workbench_sidecar_status_cutover` 的 active source-purity tail。当前 `medautosci workspace progress-portal`、`--serve` 与 `ops/mas/bin/start-web` 仍是 active caller，因此 carrier 只能标记为 active diagnostic carrier delete-blocked；需要 OPL App default progress carrier、workspace helper no-active-caller proof 和 focused tests 同时成立后，才能继续收薄或删除。Portal 负责 progress / status / blocker / artifact pickup 的只读展示，不负责 terminal attach、日志流、执行器对话、runtime drilldown 或长期 workbench shell；这些运行观察能力归 OPL `current_control_state` / provider attempt projection / OPL App Runtime Workbench。旧 MDS WebUI 的实时 console 和历史 MAS 私有 Console 材料只保留为 history/provenance。Progress Portal 给每个 MAS workspace 一个稳定 no-App / evidence 位置：

```text
ops/mas/progress/index.html
```

用户应能直接打开这个入口，看到当前 workspace 与论文线做到了哪里、系统下一步准备做什么、为什么卡住、是否需要医生/PI 判断、交付文件在哪里。Portal 只消费 MAS 现有 truth / read-model surface，不创建第二套状态系统。

这个入口是 per-workspace local display entrance。无论从 Codex、浏览器、OPL App 还是 OPL Runtime Manager 打开，页面和 payload 的 domain owner 都保持为 MAS；但主用户运行工作台的长期 owner 是 OPL App，MAS local Portal 只保留 domain-owned read-model payload、HTML evidence、diagnostic/no-App path 和 action receipt handoff，不成为 MAS 长期 generic workbench。

新 workspace 中旧 `start-web` 目的的默认落点也固定到 MAS Progress Portal：`ops/mas/bin/start-web` 刷新并打开 `ops/mas/progress/index.html`。如果维护者需要外部 MDS WebUI，只能通过显式 explicit archive import reference / backend audit 路径启动；医生/PI 默认不再在旧 WebUI 与 MAS Portal 之间判断进度 truth。

Portal 现在是旧 MDS WebUI 进度可视化的 MAS-owned read-model 替代面。它不表示 MDS 被函数级 1:1 搬进 MAS，也不表示 MAS 长期持有 generic workbench；它表示日常研究进度、路线、阻塞、artifact pickup 和 OPL handoff 已能用 MAS refs-only payload / HTML evidence 展示。主用户工作台继续向 OPL App-native MAS study workbench 收敛；旧 MDS WebUI 的 terminal/log streaming 属于 OPL runtime drilldown 能力，不应继续混进 Portal 的完成口径。

“替代旧 MDS WebUI”的产品验收是能力等价，不是导入旧 WebUI 模块或历史代码。最低可用形态必须同时显示 workspace 级概览和 study 级详情：同一 workspace 内多篇论文线要能按 `study_id` 区分，并展示各自的 `active_run_id`、runtime health、supervisor freshness、paper/current stage 和下一步/焦点。legacy runtime 或已停驻 study 的诊断噪声不能覆盖当前 live study 的主状态；这类信息只能保留在 diagnostics / source refs 中供维护者核查。

2026-05-08 user-view parity 校准：当前 Portal 已有固定入口和 study rows，但用户体验仍偏 workspace overview，多篇论文线会在同一页叙事中混合。旧 MDS WebUI 的 per-project/per-quest 工作台更接近用户视角；后续 P0 是把 Portal 改成 workspace shell + per-study/per-paper detail/deep link，而不是继续扩大一个混合 overview。详细调研见 [MDS WebUI User Parity Gap Review](../../references/mds-parity/mds_webui_user_parity_gap_review.md)。

2026-05-10 route/conversation visibility correction：此前 repo contract 已有单篇工作台、路线/决策和执行器对话 read model，但真实 workspace 页面仍可能看不到研究路线变化或真实对话回合。根因是物化单篇页时部分路径只从 workspace study row 合成 progress payload，丢掉 canonical `study_progress.intervention_lane` / controller refs；同时执行器对话面板按原始 timeline 前 12 条展示，容易被 runtime lifecycle event 噪音挤掉 user message 和 turn receipt。Portal 现在在生成单篇页时优先读取 canonical study-progress，路线/决策面板会把 `intervention_lane` 投影成可读 route node、当前路线、采用路线、依据和切换理由；执行器对话面板按用户消息、执行回合、最近回合、控制/阻塞引用优先抽样，再展示运行事件。该修正只改变只读展示投影，不写 study truth、controller decisions、publication gate、runtime SQLite 或 paper/package。页面可见文案默认中文，机器字段名和 source refs 仍保留英文 token 以便审计。

2026-05-10 route map visual landing：单篇论文页现在在文字路线/决策面板前增加 `研究路线地图`。该地图来自 `mas_progress_portal_route_map` 只读 payload，把当前阶段、路线节点、路线决策、阻塞、产物和执行回合投影为 SVG 节点与边，并保留 node/edge 的 source refs、artifact refs 和 conversation refs。缺少真实 route lineage、route source refs 或 route nodes 时，地图 fail-closed 显示“缺少研究路线来源”，不会从阶段文案、文件名或产物路径猜测路线。执行器对话面板同步升级为 timeline 视图，按 study scope 展示用户消息、执行回合、运行控制、动作/阻塞和工具引用；它仍然是只读 runtime conversation projection，不能发送 terminal input 或执行 controller action。

2026-05-09 paper progress degradation closeout：Portal 现在还承担“这是否真的影响论文产出”的解释层。它消费 `mas_production_blocker_impact_projection`，在单篇论文视图中展示 `affects_output`、`next_owner`、`why_not_running`、`same_fingerprint_or_handoff`、`will_start_llm`、safe reconcile command、route 和 source refs。这个投影只说明自动推进链路的生产影响，不执行 relaunch，不裁决医学质量，不写 publication gate，也不把 `current_package` / `submission_minimal` 当作当前写作 authority。若真实 workspace blocker 是 human gate、publication gate、parked handoff、profile unreadable 或 route/source refs 缺失，Portal 必须显示 blocker 和下一 owner，不能因为 repo capability 已 landed 就显示“论文自治稳定已完成”。

2026-05-10 workspace 首页 IA 刷新：`ops/mas/progress/index.html` 的首屏目标是医生/PI 能直接判断“哪些论文要注意、整体是否在推进、下一步由谁负责”。首页上半部分固定为大盘告警、关键指标和论文任务列表；系统字段、来源引用、底层诊断和修复命令统一放在页面底部折叠区，默认不抢占医生/PI 的主视图。该 IA 只改变展示优先级，不改变 Portal 的只读 projection 身份。

2026-05-12 stage review landing：单篇论文页现在把 `Stage Deliverable Index` 与 `One-Page Paper Review` 接入 `Stage 交付审阅` 表。人工审阅者不需要在 JSON、ledger 与 package proof 之间拼图；页面直接显示当前 stage、最新审阅页、deliverable index、freshness 红黄绿、论文资产变化、claim 影响、人工审阅注释、下一 owner、阻塞与是否可继续。这个表只消费显式 review/index/source refs，缺少 refs 时 fail-closed 显示“缺少 Stage Review Page / Deliverable Index 显式引用”，不会从文件名、产物路径或 stage 文案猜测审阅结论。它是人读审阅入口和 OPL locator，不写 MAS truth，不授权 quality verdict、submission readiness、publication readiness 或 artifact authority；人工注释默认也不阻塞自动推进，只有 MAS owner surface 判定 human-gate boundary 命中时才会阻塞。

2026-05-12 stage review workspace proof：Stage review 现在不仅是 contract / UI 字段。MAS repo-level materialization 能把 closeout 后的一页式 review page 和 paper-line Stage Deliverable Index 写入 workspace artifact locator；单篇 Portal payload 能只读追到 evidence ledger、review ledger、publication eval、controller decision、artifact freshness 和 package proof refs，并把跨阶段 claim impact、论文资产变化、freshness 和人工注释汇总成 paper-line summary。OPL Workbench 只消费这些 refs 和状态，不接收人工判断写回，不写 MAS truth，不授权 quality / submission / publication ready。该 proof 仍不是 production provider-hosted live apply 完成；真实 provider attempt 长时自动生成这些 locator 仍属于 provider soak 边界。

2026-05-15 study projection isolation / bounded conversation read：workspace cockpit 和 Progress Portal 物化路径现在必须把单个 study 的 `study_progress` projection error 限定在该 study 行/详情页内。错误 study 显示 `projection_blocked`、`progress_freshness.status=invalid`、`projection_error.handled_as=study_progress_projection_error` 和受控 inspect command；其他 study 页面继续生成并可监督。这个降级只适用于 read-model/display surface，不把旧配置兼容成有效配置，也不授权质量、投稿或 runtime action。执行器对话 read model 读取 JSONL 时必须使用 bounded tail：大文件只读尾部固定窗口并最多保留固定数量对象，同时在 source refs 标注 `truncated`、`size_bytes`、`bytes_read`、`items_truncated` 与 `max_items`。Portal 不得为展示一个静态页全量读取长期 runtime 历史日志，也不得因为无关 study 的历史日志过大而阻塞当前论文页。

## 形态决策

Progress Portal 采用双层形态：

1. 默认层：静态快照 HTML
   - 由 MAS CLI / controller-authorized refresh 生成 `ops/mas/progress/index.html`。
   - 不需要长期服务进程，不依赖外部 MDS checkout。
   - 适合医生直接打开、转发、归档或在断网/服务未启动时查看。
   - 页面必须显示 `generated_at`、`freshness`、`source_refs` 和 stale/missing 状态。
   - 通过 `file://` 打开的静态页面只能展示已生成快照，不能执行命令、发起 runtime 控制、安装 scheduler 或写 action receipt。

2. 可选层：本地只读实时服务
   - 由 `medautosci workspace progress-portal --serve --profile <profile>` 或同等 workspace helper 启动。
   - 服务只读取本地 MAS durable surfaces 和 portal payload；可以轮询刷新或使用文件变更通知。
   - 不写 study truth、publication truth、runtime authority、package authority 或 SQLite runtime lifecycle authority。
   - 实时体验应显示“最近刷新时间”和“下一次刷新/监听状态”，让用户知道页面是否仍在更新。
   - 这是 no-App / diagnostic / evidence 体验，不是 MAS-owned long-running workbench shell；长期 App-native workbench、notification、approval transport、terminal UI shell 和 provider drilldown 归 OPL App / OPL Runtime Manager。

因此，Portal 不是二选一的静态网页或动态网站。默认必须有稳定静态入口；实时体验作为同一 read-model 的本地只读增强层实现。

## OPL App 集成结论

同一目的集成到 OPL App 进度看板的最优形态是分层消费，而不是把 MAS Portal 搬进 OPL 重新解释。本文只固定 MAS-owned Progress Portal projection contract、workspace-local HTML evidence 和 no-App diagnostic path；OPL App 的 product/workbench 细节和主用户运行面归 [Progress Portal OPL App Integration](../../references/integration/progress_portal_opl_app_integration.md) 和 [OPL App MAS Runtime Workbench Program](../../active/opl_app_mas_runtime_workbench_program.md) 持有：

- `MAS` 负责 domain-owned progress portal payload 和 HTML，生成 `artifacts/runtime/progress_portal/latest.json` 与 `ops/mas/progress/index.html`。
- `MAS` 还负责 hosted packaging manifest，生成 `artifacts/runtime/progress_portal/hosted_package.json`。这个 manifest 只打包 MAS-owned workspace truth packaging，不消费 MDS WebUI，也不写任何 authority surface。
- 本地 MAS Portal 是每个 workspace 的 no-App / evidence / diagnostic 入口，适合医生、PI 或维护者直接打开查看同一条研究线；长期主用户工作台是 OPL App-native MAS study workbench。
- `OPL App` / `OPL Runtime Manager` 只消费 MAS read-model / payload refs，把它们汇总到 family-level dashboard、attention queue、running/recent item 和 artifact locator。
- `latest.json` 固定暴露 `opl_handoff`：包含 payload refs、freshness、source refs、artifact locators、workspace-local Portal deep link 和 forbidden authority 列表，供 OPL family projection 直接索引。OPL 只能消费这些引用，不重新解释 study truth，不写 MAS truth，也不接管 runtime、publication 或 package authority。
- OPL 展示层可以打开或深链到 `ops/mas/progress/index.html`，也可以读取 `latest.json` 做跨 workspace 概览；它不能把 payload 文案升级成 OPL-owned readiness、submission-ready、publication verdict、quality verdict 或新的 study truth。
- OPL native helper 或 state indexer 只能加速文件发现、freshness、artifact index 和 source ref 汇总；它不能重算 MAS 的 study 状态、publication judgment、evidence ledger 或 controller next action。
- `browser_url` 只表示 hosted/runtime monitoring URL，用于 OPL runtime drilldown 或可选本地只读服务的浏览器入口；Progress Portal 的 OPL handoff 使用 workspace-local HTML/ref deep link，例如 `portal_path` / `portal_url` / `deep_link` 指向 `ops/mas/progress/index.html` 或其本地文件 URL，不把 hosted monitoring URL 写成 Portal authority。

详细评估记录见 [Progress Portal OPL App Integration](../../references/integration/progress_portal_opl_app_integration.md)。

## Runtime Drilldown Boundary

Progress Portal 与 OPL runtime drilldown 分工如下：

- Progress Portal 负责 workspace/study overview、progress、blocker、artifact pickup、quality/publication projection 和 OPL handoff。
- OPL `current_control_state` / provider attempt projection 负责 runtime session、run、terminal tail、log tail、runtime health、supervision freshness、artifact delta 和 event stream。
- Progress Portal 不暴露 MAS 私有 console link/ref，也不解释 runtime run state。
- Progress Portal 可以展示 OPL handoff 或 safe action receipt；本仓 active Portal 不提供 pause / resume / stop apply endpoint。
- 两个层级都不得修改 paper/package、publication gate、controller decisions 或 study truth；runtime mutation 归 OPL runtime owner。

## 用户体验合同

Portal 首屏必须先回答医生/PI 的判断问题：

- 当前论文线状态：自动运行、排队处理、质量修复、人工 gate、投稿包已交付、停驻、终止或异常。
- 当前正在做什么：一句医生/PI 能看懂的研究或论文动作。
- 下一步是什么：补文献、补统计、降级 claim、回到 AI reviewer、等待外部投稿信息、重建投稿包等。
- 为什么卡住：当前 blocker、owner、是否需要用户动作。
- 最近一次可见进展：带时间戳的人话事件。
- 质量/投稿状态：AI reviewer、publication gate、claim/statistics/writing readiness 的 projection。
- 文件与交付入口：draft、figures/tables、current package、review record、rebuild proof。
- 可信来源：默认折叠显示 durable refs，供维护者核查。

页面文案必须先讲研究含义，再讲技术细节。`quest`、`projection`、`fingerprint`、`runtime reentry`、legacy MDS path 等内部术语不能成为医生视图主句。

workspace 首页 IA：

- 顶部大盘告警：只放影响医生/PI 判断的事项，例如需要人工判断、论文产出停滞、投稿包缺口、质量门禁阻塞、workspace 监管缺失或快照过期。每条告警必须带影响范围和下一 owner；纯系统诊断不能混入这里。
- 关键指标条：显示 workspace 级 live study 数、需要注意的 study 数、最近可见进展时间、整体 freshness、监管状态和交付/包状态摘要。指标是 read-model projection，只解释当前快照，不写入或刷新 truth surface。
- 论文任务列表：首屏主体是 `workspace.studies` / workspace attention queue，每行展示 `study_id`、研究标题或短名、当前用户面状态、下一步、owner、最近进展、质量/投稿投影、artifact 入口和 per-study deep link。
- 行内动作区：默认只允许打开 per-study 页面、打开 artifact、打开 OPL runtime drilldown ref 或复制受控命令。暂停、恢复、停止等动作只有在本机服务显式 `--serve --enable-actions` 时才能显示为可执行按钮。
- 底部折叠区：系统字段、完整 source refs、payload refs、diagnostics、adapter 信息、repair command、forbidden writes 和低信息诊断默认折叠；维护者展开后才能看到。展开区仍只展示来源与建议，不自动执行修复。

多论文 workspace 的默认 IA 目标：

- workspace 首屏只负责 study list / attention queue / running-recent，不把所有论文线解释成同一条状态叙事。
- 选择一个 `study_id` 后，主视图必须只解释这一篇论文，并提供概览、路线/决策、路径/阶段、运行状态摘要、产物和来源分区；执行器对话、终端/日志 drilldown 由 OPL runtime/workbench surface 承接。
- 单篇论文页必须提供 `Stage 交付审阅` 表：每行至少显示 current stage、latest review page、deliverable index ref、freshness signal、paper asset delta、claim impact、human review annotation、next owner 和 blockers/continue state。该表面向论文人工判断，允许自然语言摘要；机器可读 truth 仍来自 MAS contract、ledger、controller、publication gate 和 artifact locator。
- 路线/决策必须从 controller decisions、intervention lane、evidence/review ledgers、runtime lifecycle lineage/canvas 和 source refs 只读生成，展示 route node、decision rationale、blocked reason、superseded path、active/winning path；Portal 不得据此重新裁决医学质量或 publication readiness。
- 从 Portal 进入 OPL runtime drilldown 时应携带 study scope；profile-level runtime workbench 只作为维护者总览。
- 当前实现若只能生成 workspace overview，应显式显示这是概览页，并提供下一步 per-study deep link / refresh 计划。

当前优先级：

- P0 landed repo contract：`portal-study-scoped-ia`，`ops/mas/progress/index.html` 作为 workspace shell，并物化 `ops/mas/progress/studies/<study_id>/index.html` 这类 per-study 页面。
- P0 landed read-only contract：`portal-route-decision-trail`，把研究路线、分支、失败/阻塞原因、转向理由、superseded path、active/winning path 和对应 source refs 放到单篇论文视图。
- P0 landed visualization：`portal-route-map-visualization`，把路线/决策 read model 投影成单篇论文的 SVG 研究路线地图，展示阶段、路线、决策、阻塞、产物和执行回合节点，以及推进、阻塞、改道/替代和产物边。
- P0 landed repo contract：`portal-stage-artifact-path`，把 stage history、evidence/review/proof、draft/package/files 放到单篇论文视图。
- P1 runtime drilldown：执行器消息、turn/run receipt、tool/action refs、停驻原因、下一步和 terminal/log tail 由 OPL current-control-state / provider attempt projection 承接；MAS Portal 只暴露 handoff refs。
- P1 study scope handoff：Portal 深链应携带 study scope；profile-level OPL runtime workbench 继续作为 operator 总览。

Portal 主 UI 标签默认使用中文。顶部必须同时显示本机时区时间和 UTC `generated_at`；本机时间要带 IANA timezone，例如 `Asia/Shanghai`，避免跨时区排障时把 stale / fresh 误判成时钟问题。

workspace overview 模式是多论文线入口，不是某一篇论文的详情页。该模式必须把 `workspace.studies` 作为首屏主体，显示每条 study 的 `study_id`、运行健康、监管心跳、进度新鲜度、论文阶段和下一步；不得把缺少单篇 `publication_eval` 或 `current_package` 的缺省文案渲染成 workspace 级问题。单篇质量门禁和交付包结论只在具体 study 视图中展示。

workspace alerts 必须保留解释层。每条可见告警或降级诊断都要说明：

- 来源：例如 `workspace_cockpit.workspace_alerts`、`workspace_supervision.service.summary`、`product_entry_preflight.medical_overlay_ready`。
- 用途：这条信息用来提醒运行、进度、质量还是诊断缺口。
- 当前输出：原始 read-model 当前给出的文本或状态。
- 期望输出：恢复后应该看到的具体状态或更具体 blocker。
- 修复/查看命令：如果已有受控 CLI，例如 `domain-health-diagnostic`、`owner-route-reconcile` 或 `doctor --profile`，应显示命令；没有命令时保持为空。

`Supervisor scheduler 尚未注册。`、`MAS local scheduler 已物理退役；仅保留 tombstone/provenance refs。` 这类旧 local scheduler 文案只应作为 tombstone/provenance 诊断展示，不得指向可执行 `--manager local` 命令；默认 scheduler owner 是 OPL provider/runtime manager。诊断必须同时显示当前 `adapter_id`（默认 `opl_family_runtime_provider`，显式 Hermes 为 `hermes_gateway_cron`），不能把 Hermes-hosted 或 local LaunchAgent 文案当成默认架构事实。`状态需要检查。` 这类泛化旧文案应标为低信息诊断，由具体 study 行和 runtime health blocker 取代。

Portal 只读投影，不自动安装或修复 scheduler。默认 runtime 状态由 OPL `current_control_state` / provider attempt ledger 投影；MAS 只显示 domain refs、owner receipt、typed blocker、safe action refs 和 tombstone/provenance refs。发现 legacy local scheduler 缺失或漂移时，Portal 必须展示 `workspace_supervision.service.summary`、用途、期望状态和 tombstone/provenance refs，不输出 local cleanup command。

如果 OPL `current_control_state` / provider attempt ledger 显示 runtime handoff 新鲜且具体 study 行已经给出 runtime health blocker，Portal 不应继续把 “supervision 尚未注册” 当作当前问题展示。若旧 Hermes-hosted 文案仍从 `workspace_cockpit.workspace_alerts` 传入，只能落入诊断表并携带来源/修复命令；若现场 supervision 已在线且具体 study 行已经给出 runtime health blocker，`状态需要检查。` 应完全隐藏，避免医生/PI 把低信息历史诊断误认为待处理任务。

当前 UI 采用简洁的 operational dashboard 形态：状态用 chip/tag 呈现，表格负责多 study 区分，告警表负责来源/用途/期望/命令。设计参考原则来自 `awesome-design-md` / GetDesign.md 一类 design-context-first 方法，以及 Material / Carbon / Atlassian 的状态 chip、tag、lozenge 和 data-table 模式：少装饰、强对齐、可扫描、状态含义不只靠颜色表达。

## 数据与 Authority 边界

Portal 的输入来自现有 MAS surface：

- `study_macro_state/latest.json`
- `study_progress.user_visible_projection`
- `study_progress.opl_current_control_state_refs`
- `study_progress.domain_authority_refs`
- `study_progress.runtime_reconcile_trigger`
- `study.runtime_continuity`
- `workspace-cockpit`
- `progress_projection`
- `domain_health_diagnostic`
- `runtime_supervision/latest.json`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- delivery / package currentness projection
- Stage Deliverable Index / One-Page Paper Review 显式 locator
- `artifacts/runtime/domain_authority_refs.sqlite` 里的 owner receipt / typed blocker / locator refs

Stage review 表在 Portal 中只做一页式人工审阅投影。它可以展示：

- 最新审阅页和 deliverable index 的显式引用；
- stage 输入、输出、ledger、quality gate、package/artifact delta 和 next owner；
- 论文资产变化类型，例如 manuscript、table、figure、supplement、reference、response letter、analysis record、review record、package/delivery 或 no paper asset body delta；
- claim trace 影响，例如 strengthened、weakened、rewritten、removed、unsupported、newly_blocked 或 no_claim_change；
- freshness 红黄绿和对应 source refs；
- 人工审阅注释：可进入下一阶段、需修改、退回前一阶段、停止/转向、需要人工 gate。
- paper-line workspace proof：evidence ledger、review ledger、publication eval、controller decision、artifact freshness 和 package proof 的 locator refs；页面只显示 refs，不嵌入正文或包内容。

这些字段都不能提升为 MAS 质量结论、投稿结论或 artifact authority。OPL 只能索引这些 refs 与状态，不能接受 memory writeback、写 evidence/review ledger、替换 controller decision，或把人工注释转成 publication-ready。

路线/决策的机器合同在 `contracts/test-lane-manifest.json` 的 `focused_lanes.portal-route-decision-trail`。该 lane 固定：

- surface kind：`mas_progress_portal_route_decision_trail`。
- visual surface kind：`mas_progress_portal_route_map`。
- required inputs：`controller_decisions`、`evidence_or_review_ledgers`、`runtime_lifecycle_lineage_or_canvas`、`source_refs`。
- required display fields：`route_map`、`route_map_node`、`route_map_edge`、`route_node`、`decision_rationale`、`blocked_reason`、`pivot_rationale`、`superseded_path`、`active_path`、`winning_path`、`source_refs`。
- 页面展示：单篇论文的路线/决策面板必须把 route source refs 直接列出，方便用户从路线节点跳回 controller/evidence/runtime lineage 证据；缺 source refs 时显示 missing，不用文件名或 stage 文案补推。
- 地图展示：单篇论文的研究路线地图必须用节点/边表达路线演进，而不是只列文字。节点至少区分阶段、路线、决策、阻塞、产物和执行回合；边至少区分推进、阻塞、改道/替代和产物关系。节点详情必须保留 source refs，并可关联 artifact refs 或 conversation refs。
- authority boundary：`read_only_route_decision_projection`。
- fail-closed：缺输入时显示 missing 条件，不从文件名、stage 摘要或 artifact path 推断研究路线。
- forbidden writes：不得写 `study_truth`、`publication_eval/latest.json`、`controller_decisions/latest.json`、OPL runtime state、retired `runtime_lifecycle.sqlite`、`paper/current_package` 或 `manuscript/current_package`。

执行器对话和 runtime event drilldown 已从 MAS active Portal 合同中物理退役。Portal 只展示 MAS study progress、route/decision、owner receipt、typed blocker 和 artifact/source refs；用户消息、turn receipt、runtime event、terminal/log tail 的可视化由 OPL `current_control_state` / provider attempt projection 承接。MAS Portal 不读取或生成私有 conversation read model，不把 user message queue 当 interactive terminal input，不写 controller decisions、publication eval、paper/package 或任何 runtime owner state。

Runtime continuity 在 Portal 中只负责解释 OPL current-control-state refs 与 MAS owner receipt / typed blocker refs，不负责执行动作。页面可以显示 OPL attempt state、last seen、freshness、blocked reason、next owner、typed blocker，以及是否存在 OPL next action；它不能直接重启 worker，不能修改 `current_package`，不能写 `publication_eval/latest.json` 或 `controller_decisions/latest.json`。

Outer supervision SLA 在 Portal 中只负责解释 OPL 外环监管是否新鲜。页面应显示 `outer_supervision_slo.state`、最新 OPL tick/reconcile 时间、监管年龄、blocked/missing reason，以及 canonical OPL/MAS handoff 推荐命令。`due` 或 `stale` 表示可以请求 OPL 重新 reconcile；它不表示 Portal 拥有 runtime relaunch 权限。重复刷新必须通过 dedupe fingerprint 和 OPL current-control-state 去重，不能制造重复恢复动作。

Paper progress degradation 在 Portal 中只负责解释自动论文推进是否被阻塞。页面可以显示 same fingerprint loop、read churn、stale truth surface、OPL retry/dead-letter blocker、owner handoff、publication gate recheck 和 AI reviewer / writer next owner；它不能把这些 read model 结果提升为 quality ready、publication ready 或 submission ready。safe reconcile command 应保持 dry-run 优先；任何 apply 仍由 OPL stage runtime 调度并回到 MAS owner receipt / typed blocker surface。

Portal 只能生成 read-model payload 和展示文件，例如：

```text
artifacts/runtime/progress_portal/latest.json
artifacts/runtime/progress_portal/hosted_package.json
ops/mas/progress/index.html
```

这些文件是展示产物，不是 study truth。任何启动、恢复、暂停、写作、质量裁决、投稿授权、交付重建或 runtime lifecycle 写入仍回到 OPL current control state 与 MAS owner receipt / typed blocker / authority surface。

`opl_handoff` 是同一 payload 内的 family-level projection，不是额外 truth surface。它只能引用本 payload、源 payload 摘要、freshness、source refs、artifact locators 与 workspace-local Portal deep link；OPL 侧只能把它作为 family-level projection consumer 输入，不能据此生成新的 study truth、publication judgment、quality verdict、runtime authority、publication authority、package authority 或 artifact authority。若 payload 同时暴露 hosted monitoring `browser_url` 与 Portal `portal_path` / `portal_url` / `deep_link`，OPL 应把 `browser_url` 视为 runtime monitoring 入口，把 Portal 字段视为本地 HTML/ref deep link。

## 静态快照合同

静态 HTML 应满足：

- 单文件可打开，默认不需要 Node、Python server 或前端构建链。
- 使用稳定 MAS branding：`Med Auto Science`。
- 顶部主标题显示 workspace name；当前选择的 `study_id` 作为元信息显示，不能覆盖 workspace 级入口身份。
- 顶部时间同时显示本机本地时区时间和 UTC `generated_at`，避免跨时区排障时误判 freshness。
- 对 stale/missing/conflict 必须 fail-closed 显示，而不是隐藏。
- 页面内引用路径应来自 payload refs，不硬编码 docs prose path。
- 页面可以内联 CSS 和少量 JS 负责折叠、筛选、自动滚动到当前 blocker；不能依赖远程 CDN。

静态快照的刷新时机可以是：

- 用户手动运行 refresh 命令。
- controller-authorized sync / runtime watch tick 后刷新。
- 本地只读 serve 进程轮询刷新。
- workspace helper 被外部 scheduler 调用。

## 本地实时服务合同

实时服务应保持 lightweight：

- 绑定本机地址，默认 `127.0.0.1`。
- 只读本地文件与 SQLite read model。
- 不持有长期 workflow state；重启后可从 durable surfaces 重建。
- 不使用外部 MDS WebUI、外部 MDS runtime root 或 upstream DeepScientist UI state 作为默认输入。
- 如果 refresh 失败，页面显示上一版快照和明确错误，不写入 misleading current 状态。
- 适合后续接入 Codex App、OPL Runtime Manager 或浏览器自动打开，但这些集成不能成为 Portal 的 authority。

实时服务的价值是让用户看到页面持续更新，减少“是不是还在跑”的不确定感；工程上它只是 read-model refresh loop。

如果 read-model 给出 `runtime_reconcile_trigger.safe_to_request=true`，实时服务或页面刷新只能展示推荐命令或调用现有 controller/supervisor safe surface；重复刷新必须依赖 dedupe fingerprint，不能制造重复 relaunch。已 parked、completed、human gate、publication gate missing 或 retry exhausted 的 study 必须显示 blocked reason，而不是提示恢复。

## Authorized Action Endpoint

Progress Portal 默认仍是只读静态快照。只有本机 loopback 服务显式启用 `--enable-actions` 时，`POST /actions` 才接受受控 action request：

- allowlist：`inspect`、`reconcile-dry-run`、`pause`、`resume`、`stop`。
- 静态 `file://` 页面和未启用 `--enable-actions` 的 `--serve` 页面不得执行 action；它们只能显示命令文本、deep link、artifact link 或 disabled 状态。
- `inspect` 与 `reconcile-dry-run` 只写 dry-run receipt，不执行 runtime mutation。
- `pause`、`resume`、`stop` 在 `--enable-actions` 下只写 `runtime_owner_route_request` receipt，必须带 `study_id` 或 `quest_id`，并把 runtime action handoff 给 `queue_owner=one-person-lab`；Portal 不直接调用 MAS backend 的 `pause_quest`、`resume_quest`、`stop_quest`。
- idempotency：同一 key 已有 receipt 时直接返回旧 receipt，不重复创建 runtime owner handoff。
- audit：receipt 记录 `action`、`study_id`、`quest_id`、`mode`、`apply_status`、`runtime_control_operation=opl_runtime_owner_route`、runtime owner handoff、`audit_ref` 和 forbidden writes。
- fail-closed：未启用 `--enable-actions` 返回 disabled；action 不在 allowlist、idempotency key 非法或缺 `quest_id/study_id` 时拒绝。

该 endpoint 不是旧 MDS daemon/UI control 的恢复。它只把 action intent 写成 MAS receipt 与 OPL runtime-owner handoff，继续禁止写 paper/package、publication gate、controller decisions、study truth 和 provider runtime state。Terminal attach/input/resize/detach 归 OPL terminal transport；不能复用这个 action endpoint 或 `chat_quest` 伪装实现。

## Portal / Runtime Drilldown Evidence

真实 workspace 上的 Portal 可用性由 `workspace progress-portal`、OPL workbench/current-control-state evidence 和 product-entry refs 分别验证。MAS 不再提供 Portal/Console combined soak runner；历史 soak 只作为已退役 provenance 读取。当前 active 检查重点是：

- Portal 是否能刷新并写出 payload / HTML；
- 单篇论文页是否有 `mas_progress_portal_route_map`、SVG 研究路线地图、route/decision 节点、路线边和 source refs；
- 单篇论文页是否把 OPL runtime handoff、owner receipt 和 typed blocker refs 清楚暴露；
- source refs 是否没有把旧 MDS 路径冒充 truth；
- 页面是否保持 `Med Auto Science` identity，不把旧 MDS WebUI 作为产品入口。

Portal 刷新只允许写 display/read-model evidence：`artifacts/runtime/progress_portal/*` 与 `ops/mas/progress/index.html`。它禁止写 paper/package、publication gate、controller decision、provider runtime state 或 restore archive。检查失败时应输出 blocker，不得伪造页面可用或 paper autonomy landed。

## 旧 MDS WebUI 关系

旧 MDS WebUI 的可吸收价值是“可视化状态、进度和路线”，不是品牌、代码历史或产品入口身份。

迁移原则：

- 旧 `start-web` 语义应转向 MAS Progress Portal 或明确 explicit archive import reference。
- `DeepScientist`、`MDS`、`DS` 只允许出现在折叠的 explicit archive import reference / provenance / oracle 区域。
- 默认医生视图不得展示 MDS/DS 路径作为 workspace truth。
- 不把上游 WebUI 历史、contributor footprint 或 product semantics 导入 MAS main。

如果外部 MDS 仍因 backend audit、oracle fixture 或 upstream intake 被显式运行，MDS WebUI 也只能服务维护者诊断。它不能再作为医生默认进度面，也不能和 `ops/mas/progress/index.html` 并列解释同一个 study truth。

## Landed Implementation Surface

当前实现写集：

- `src/med_autoscience/controllers/progress_portal.py`
- `medautosci workspace progress-portal`
- `artifacts/runtime/progress_portal/hosted_package.json` MAS-owned hosted packaging manifest
- workspace init 生成 `ops/mas/progress/index.html` placeholder 和 `ops/medautoscience/bin/progress-portal`
- workspace init 生成 `ops/mas/bin/start-web`，默认刷新并打开 MAS Progress Portal
- `tests/test_progress_portal.py`
- `tests/test_cli_cases/progress_portal_commands.py`
- workspace init / README / architecture / status / OPL handoff docs

CLI 形态：

```bash
medautosci workspace progress-portal --profile <profile>
medautosci workspace progress-portal --profile <profile> --open
medautosci workspace progress-portal --profile <profile> --serve
```

`--serve` 不应是默认必需路径；默认命令应能生成可打开的静态快照。

实现时的最小合同：

- payload builder 从现有 MAS durable surfaces 组装 read-model，不从 Markdown 文档、OPL state cache 或旧 MDS WebUI 路径推导状态。
- HTML materializer 只渲染 payload，并把 stale/missing/conflict 显示成可见状态。
- workspace init 只需要提供固定入口位置和可刷新路径；不能把 OPL App、长期服务进程或外部 runtime substrate 变成 Portal 的必需依赖。
- OPL handoff 只暴露 payload refs、HTML path/deep link、freshness、source refs 和 artifact locators，供 family dashboard 消费。

## 验收标准

- 新 workspace 有明确固定入口：`ops/mas/progress/index.html`。
- Portal payload 与 `study-progress`、`workspace-cockpit`、`product-entry-status` 对同一 study 的状态一致。
- Portal 不写 authority surface，只写 read-model / display artifact。
- 默认页面不出现 MDS/DeepScientist 产品语义。
- stale/missing/conflict 有明确可见状态。
- 本地实时服务可刷新页面，但停止服务后静态快照仍可打开。
- MCP/CLI/controller payload shape 不因 Portal 改动而破坏。
