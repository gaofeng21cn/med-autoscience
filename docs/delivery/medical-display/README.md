# Medical Display 能力族

Owner: `MedAutoScience`
Purpose: `medical_display_delivery_index`
State: `active_delivery_support`
Machine boundary: 人读能力族索引。机器真相继续归 renderer contracts、template/schema source、layout QC、generated display artifacts、delivery manifests、runtime/controller receipt 和真实 workspace artifact refs。

这是医学展示能力族的活跃入口。

| 目录 | 角色 |
| --- | --- |
| [portfolio](./portfolio/) | Portfolio map 和长期 roadmap。 |
| [board](./board/) | 当前 active board 和下一轮可执行 display round。 |
| [contracts](./contracts/) | 平台主线、审计指南、视觉审计协议和 route contract。 |
| [catalogs](./catalogs/) | 模板目录、arsenal、backlog 和 route cookbook。Catalog 可以很长；它们是 inventory，不是叙事入口。 |
| [examples](./examples/) | 人读最小示例和 E2E 字段关系说明；不是 fixture 或机器真相。 |
| [plans](./plans/) | Template-pack active support design。已完成实施计划进入 history/provenance，不作为当前执行队列。 |
| [provenance](./provenance/) | 真实论文审计和能力 provenance。 |
| [history](../../history/capabilities/medical-display/README.md) | 退役 owner brief、baseline program、exemplar intake 和 exhausted exploration record。 |

## 主要入口

- [Portfolio consolidation](./portfolio/medical_display_portfolio_consolidation.md)
- [Active board](./board/medical_display_active_board.md)
- [Display Pack v2 landing status](./contracts/display_pack_v2_landing_status.md)
- [Display Pack renderer migration assessment](./plans/display_pack_renderer_migration_assessment.md)
- [Platform mainline](./contracts/medical_display_platform_mainline.md)
- [Audit guide](./contracts/medical_display_audit_guide.md)
- [Template catalog](./catalogs/medical_display_template_catalog.md)
- [Display Pack v2 E2E skeleton](./examples/display_pack_v2_e2e_skeleton.md)

历史 exemplar 和退役 brief 只保留 provenance；除非真实 MAS 论文需求通过 active board 重开，否则不作为当前 backlog。

`board/medical_display_active_board.md` 只维护当前唯一 active round 与下一轮 reroute 边界。已吸收 round 的 owner note、完整命令流水、exemplar intake 细节和历史 capability ledger 进入 history/provenance，不继续堆在 board 中。

## Delivery Authority 边界

Medical Display 文档和 template pack 可以定义 renderer family、input schema、layout QC、template catalog、route cookbook、display-to-claim 审计输入和生成型 display artifacts。它们不授权 source readiness、publication quality、submission readiness、artifact mutation、`current_package` freshness proof、delivery sync、paper closure、domain ready 或 production ready。

Display Pack v2 当前完成度按 [Display Pack v2 landing status](./contracts/display_pack_v2_landing_status.md) 读取：MAS 域内 pack/template descriptor、paper-level figure quality refs、article-level `paper/publication_style_profile.json` style-token lock、single/batch medical figure grammar、R/ggplot2-first subprocess runtime protocol、55 个 core evidence templates 的 `subprocess + render.R` 一等默认 R/ggplot2 入口、P2 Python plugin adapter、AI/VLM polish lifecycle、template discovery/describe CLI、agent-facing orchestrate/discovery/plan/preflight/render receipt surface、one-shot scaffold render、golden refresh/check lower-bound surface、deterministic E2E render/QC/publication manifest、display lock 和 submission refs preservation 已有 contract / validator / test 面；OPL repo 已落地 `opl pack os install/registry/cache/distribute/lock/validate/mas-display-smoke` surfaces。OPL surfaces 只消费和运输 refs，不表示 MAS 已拥有 generic Pack OS substrate。当前 core pack 的 renderer migration ledger 覆盖 84/84 evidence templates：P0 landed 22，P1 default R/ggplot2 promotion landed 33，P2 retained Python / later dual-stack 29。`display-pack-render-candidate` 只保留 legacy comparison receipt；`publication_style_profile`、`display_pack_lock.json`、golden match、visual-audit clear、polish lifecycle、agent orchestration/render receipt、comparison receipt 或 OPL smoke receipt 都不能代签 publication readiness、artifact authority 或 owner receipt。

## Agent 调用路径

Display Pack 是 MAS agent 使用的能力包，不要求用户理解每个模板。主路径是：

1. agent 从 `contracts/agent_tool_arsenal.json` 或 MCP `agent_tool_arsenal mode=resolve` 发现 `display_pack_*` candidates；缺 `paper_root` / `claim_ref` / `data_ref` 只进入 `missing_refs` 和 `next_safe_actions`，不把 Display Pack 候选过滤掉；
2. agent 调 MCP `display_pack_agent`，用 `mode=orchestrate` 和 `current_owner_delta` / claim refs / data refs / intent 编译 `figure_intent`、结构化 `figure_request`、推荐 plan、preflight、quality floor、typed repair routes 和下一步 callable；
3. agent 只在需要诊断或分步执行时调 `mode=plan` / `mode=preflight`；`adaptable_baseline_not_exact_contract` 只表示可作为 quality-floor baseline，不表示 publication readiness、artifact authority、owner receipt 或 visual-audit replacement；
4. agent 调 MCP `display_pack_agent` 的 `mode=render` 物化 display artifacts、visual-audit receipt、polish lifecycle、display_pack_lock 和 publication manifest refs；
5. visual audit finding、owner receipt、publication gate 继续由 MAS authority 决定，不由 Display Pack 自签。

稳定机器入口：

```bash
MCP tool: agent_tool_arsenal mode=index|card|resolve|plan|result_envelope_schema
MCP tool: display_pack_agent mode=discover|orchestrate|plan|preflight|render
medautosci domain-handler export --profile <profile> --format json
medautosci domain-handler dispatch --task <task.json> --format json
```

Domain entry commands：

```json
{
  "command": "display-pack-orchestrate",
  "repo_root": "<mas_repo>",
  "paper_root": "<paper_root>",
  "current_owner_delta": {
    "stage_id": "paper_autonomy/display",
    "work_unit_id": "figure-2-roc"
  },
  "claim_ref": "claim:primary-discrimination",
  "data_ref": "analysis:roc-input-v1",
  "paper_target": "jama",
  "intent": "Create a primary ROC curve evidence figure for the mortality risk model.",
  "figure_request": {
    "preferred_renderer_family": "r_ggplot2"
  }
}
```

CLI 是 agent/debug/资产管理面，不是让用户手工选模板的主路径：

```bash
medautosci publication display-pack-agent-discover --repo-root <mas_repo>
medautosci publication display-pack-agent-orchestrate --repo-root <mas_repo> --paper-root <paper_root> --current-owner-delta-json '<current_owner_delta_json>' --claim-ref <claim_ref> --data-ref <data_ref> --paper-target <journal_or_profile> --intent '<display_intent>'
medautosci publication display-pack-agent-plan --repo-root <mas_repo> --figure-request-json '<figure_request_json>'
medautosci publication display-pack-agent-preflight --repo-root <mas_repo> --paper-root <paper_root> --figure-request-json '<figure_request_json>'
medautosci publication display-pack-agent-render --repo-root <mas_repo> --paper-root <paper_root> --figure-request-json '<figure_request_json>'
medautosci publication display-pack-templates --repo-root <mas_repo> --kind evidence_figure --renderer-family r_ggplot2
medautosci publication display-pack-template --repo-root <mas_repo> --template-id roc_curve_binary
medautosci publication display-pack-scaffold-render --repo-root <mas_repo> --paper-root <paper_root> --template-id roc_curve_binary --data-payload-file <payload.json>
medautosci publication display-pack-golden refresh --repo-root <mas_repo> --paper-root <paper_root> --template-id roc_curve_binary --data-payload-file <payload.json> --golden-root <golden_root>
medautosci publication display-pack-golden check --repo-root <mas_repo> --paper-root <paper_root> --template-id roc_curve_binary --data-payload-file <payload.json> --golden-root <golden_root>
```

`display-pack-agent-*` 是 MAS agent 的结构化能力面；`display-pack-templates` / `display-pack-template` 是只读资产发现面；`display-pack-scaffold-render` 和 `display-pack-golden` 会物化试跑用 paper scaffold 并走正式 E2E render/QC/audit receipt/lifecycle/lock/manifest。它们方便模板开发与资产验收，但不替代真实 paper intent authoring、独立 visual audit、MAS owner receipt 或 publication gate。

证据型图修复必须保留 frozen data / script / statistics refs 与 MAS artifact authority refs 的直接关系。说明性图可以走程序化 illustration route，但不能承载结果证据、修改 claim、替换 source truth 或绕过 MAS owner receipt / typed blocker。OPL generated / hosted surfaces 只能展示或运输 display locator refs、owner receipt refs、typed blocker refs、pack/version refs 和 audit refs。

## Memory 边界

医学展示有两层复用内容：

- 已审计模板、input schema、renderer family、layout QC profile、shell contract、生成型 catalog 和 packaging manifest 是强 display contract；
- 论文为什么选某类图、视觉审计中反复出现的可读性失败、文章级风格取舍、图表路线选择 caveat，适合作为自然语言经验记忆。

第一层归属本能力树和 source/contract surface。第二层可以被 MAS stage knowledge packet 和 publication route memory 引用，但不能替代实际渲染图审阅、模板合同或 QC 合同。
