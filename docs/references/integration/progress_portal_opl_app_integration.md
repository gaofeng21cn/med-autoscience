# Progress Portal OPL App Integration

Status: `support reference`
Owner: `MedAutoScience Product Projection + OPL integration boundary`
Purpose: `Support MAS integration and OPL handoff understanding.`
State: `support_reference`
Machine boundary: Human-readable integration reference only; callable and generated-surface truth remains in manifests, contracts, source, tests, OPL handoff contracts, and read-model output.

2026-05-10 更新：此前本文把 OPL App 的最优形态写成 family dashboard + 打开 MAS workspace-local Portal deep link。新的产品结论是，OPL App 应成为 MAS 人类运行工作台的主入口；workspace-local Portal / Live Console 继续作为 legacy_restore_import、evidence 和 no-App 环境入口。OPL App 仍然只消费 MAS read model / owner-route handoff refs / source refs，不接管 MAS study truth、publication quality、runtime owner 或 current package authority。

## 入口结论

MAS Progress Portal 与 OPL App 进度看板服务同一个用户目的：让医生、PI 和维护者快速知道研究线当前在哪里、下一步是什么、哪里需要人工判断、文件在哪里。最佳集成形态是 owner-preserving projection：

- `MAS` 持有 domain-owned progress portal payload、route/domain projection、runtime control receipt 和 workspace-local HTML legacy_restore_import；旧 conversation / Live Console / terminal attach read model 只作为 history/provenance。
- `OPL App` 持有 family-level dashboard、Runtime Workbench、workspace/session/progress/artifact 聚合视图、通知、approval transport 和 terminal UI shell。
- OPL 只消费 MAS read-model / payload refs，不重新解释 study truth。

这让本地 MAS workspace 保留固定 legacy_restore_import 入口，也让 OPL App 可以在一个工作台里显示多个 domain / workspace 的进度和单篇 MAS study 的运行细节，而不制造第二套医学研究状态机。

## MAS 侧职责

MAS 负责生成和维护：

```text
artifacts/runtime/progress_portal/latest.json
ops/mas/progress/index.html
```

`latest.json` 是展示 payload，不是 study truth。`index.html` 是 per-workspace fixed entrance，不依赖 OPL App 才能打开。payload 应包含 `generated_at`、freshness、source refs、study/workspace identity、user-visible state、next action、blockers、quality/publication projection、delivery/artifact locators 和 stale/missing/conflict 状态。OPL 只能消费这些 payload refs 与定位信息，不能把它们提升为 OPL-owned study truth、runtime authority、publication authority 或 package authority。

MAS payload 的输入只能来自 MAS durable surfaces，例如 `study_macro_state/latest.json`、`study_progress.user_visible_projection`、`workspace-cockpit`、`progress_projection`、`domain_health_diagnostic`、`publication_eval/latest.json`、`controller_decisions/latest.json`、delivery/package projection 和 runtime lifecycle read model。

`latest.json` 内固定包含 `opl_handoff`，作为 OPL family projection 的最小稳定 bundle：

```text
opl_handoff:
  handoff_kind: mas_progress_portal_opl_family_projection
  owner: mas
  role: family_level_projection
  authority: display_artifact_only
  opl_role: family_level_projection_consumer_only
  payload_refs:
    progress_portal: artifacts/runtime/progress_portal/latest.json
    source_payloads: <progress/cockpit/runtime/package summary>
  freshness: <same payload freshness object>
  source_refs: <same payload source refs>
  artifact_locators: <delivery/package refs>
  portal_path: ops/mas/progress/index.html
  portal_url: file://<workspace>/ops/mas/progress/index.html
  conditions:
    missing: [...]
    stale: [...]
    conflict: [...]
  deep_link: ops/mas/progress/index.html
```

这个 bundle 是 `latest.json` 的投影子结构，不引入第二套状态文件或第二套 status machine。

`browser_url` 与 Portal deep link 的边界必须保持稳定：`browser_url` 只用于 hosted/runtime monitoring URL，例如 Live Console 或可选本地只读 runtime monitor；`portal_path`、`portal_url` 与 `deep_link` 才是 MAS Progress Portal 的 workspace-local HTML/ref deep link。OPL App 可以展示二者，但不能把 hosted monitoring URL 当成 Progress Portal authority，也不能用任一 URL 写回 MAS truth。

## OPL App 侧职责

OPL App / OPL Runtime Manager 可以消费 MAS 暴露的 refs：

- portal payload path
- portal HTML path
- freshness and generated time
- source refs
- artifact locators
- study/workspace identifiers
- user-facing state labels
- attention, blocker, running/recent and artifact locator fields
- workspace-local Portal deep link

OPL App 的最优 UI 是 App-native Runtime Workbench，而不是复制 MAS Portal 的静态 HTML。family-level dashboard 负责跨 workspace 的进度条目、attention queue、running/recent items 和交付物入口；用户需要深看 MAS 医学研究线时，在 OPL App 内进入 MAS study workbench。`ops/mas/progress/index.html` 与 `ops/mas/live-console/index.html` 保留为 legacy_restore_import / evidence / operator debug 入口。

OPL App 的 MAS study workbench 应直接消费以下 MAS read model 或它们的稳定 projection：

- `artifacts/runtime/progress_portal/latest.json`
- domain-handler / owner-route handoff refs under `artifacts/supervision/owner_route_handoff/` or the matching domain-handler dispatch evidence payload

terminal/log/provider drilldown 必须来自 OPL `current_control_state` 或 provider attempt projection。OPL App 可以提供 terminal UI shell，但 MAS 不提供 terminal attach owner gate；任何 UI 都不能直接写 per-run command queue、runtime state、runtime SQLite、publication eval、controller decisions 或 package authority。

## 禁止升级的边界

OPL App、OPL Runtime Manager、native helper、state indexer 或 dashboard 不得：

- 生成新的 MAS study truth。
- 生成 publication readiness、submission readiness、quality verdict 或 medical claim judgment。
- 重算 `study_macro_state`、`owner_route`、`publication_eval/latest.json` 或 `controller_decisions/latest.json`。
- 把 stale/missing/conflict payload 隐藏成 ready 状态。
- 把旧 MDS WebUI、OPL state cache 或 Markdown 文档当成 MAS progress authority。
- 写入或接管 MAS runtime、publication、package、artifact 或 evidence/review ledger authority。

OPL native helper 可以加速索引、freshness 检查、artifact path discovery 和 source ref 汇总；这些输出仍是 observability / projection，不是 authority。

## 集成合同

MAS implementation lane 应把 handoff payload 固定成 OPL 可消费的 reference bundle：

```text
progress_portal:
  payload_ref: artifacts/runtime/progress_portal/latest.json
  html_ref: ops/mas/progress/index.html
  portal_path: ops/mas/progress/index.html
  portal_url: file://<workspace>/ops/mas/progress/index.html
  deep_link: ops/mas/progress/index.html
  browser_url: <hosted/runtime monitoring url, optional>
  owner: mas
  role: domain_owned_progress_projection
  authority: display_artifact_only
```

OPL App 可以把该 bundle 映射到 family dashboard 和 App-native Runtime Workbench，但所有状态都应保留 MAS source refs 和 freshness。用户点击详情时，优先进 OPL App 的 MAS study workbench；workspace-local Portal 和 `browser_url` 对应的 hosted/runtime monitoring 面只作为 legacy_restore_import / debug / no-App 路径。两类入口都保持 projection/action-transport 边界，不进入 OPL 自己维护的研究状态机。

后续实现计划见 [OPL App MAS Runtime Workbench Program](../../active/opl_app_mas_runtime_workbench_program.md)。

## 验收口径

- 新 MAS workspace 有固定可打开入口 `ops/mas/progress/index.html`。
- MAS payload 与 `study-progress`、`workspace-cockpit` 和 runtime/publication durable refs 一致。
- OPL App 能读取 payload/html refs 并展示 family-level progress item。
- OPL dashboard 显示 freshness、source refs 和 stale/missing/conflict，不把缺口改写成 ready。
- OPL App 内 MAS study workbench 能显示进度、路线/决策、artifact refs、可用/不可用 action，并并列展示 OPL `current_control_state` 的 runtime drilldown refs。
- terminal/log/provider drilldown 来自 OPL projection；MAS 不接收 terminal input/resize/detach，也不显示 MAS gate reason。
- OPL 集成不写 MAS study truth、publication truth、runtime authority、evidence/review ledger 或 artifact authority。
