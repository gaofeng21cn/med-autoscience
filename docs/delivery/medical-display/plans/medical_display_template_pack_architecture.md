# 医学绘图模板包架构设计

Owner: `MedAutoScience`
Purpose: `Record the current target boundary for medical-display template packs.`
State: `active_support`
Machine boundary: 本文只解释 owner split 与迁移方向。机器真相归 `contracts/display-pack-contract.v2.json`、`contracts/opl_agent_package_manifest.json`、V2 action catalog/Stage manifest、ScholarSkills provider manifest、paper-local artifact refs、quality receipts 与 MAS owner receipts。

## 结论

医学绘图模板不再由 MAS 私有宿主平台管理。目标形态是：

`ScholarSkills display source -> OPL package lifecycle / Stage Tool Affordance Boundary / Runway -> candidate display refs -> MAS medical quality and artifact authority`

三方 owner 固定为：

- ScholarSkills/display pack source 持有模板、renderer code、examples、goldens、gallery、专业 Skill 与版本化 source truth。
- OPL Pack / Atlas / Stagecraft / Runway / Ledger / Console 持有 package dependency closure、安装更新卸载、descriptor discovery、prepared environment、StageRun、renderer transport、refs/receipt transport 与 hosted workbench。
- MAS 持有 figure intent、claim/data/statistics refs、医学语义、visual/claim quality gate、artifact mutation、publication/submission authority 与 owner receipt。

任何 MAS repo-local installer、registry service、scheduler、renderer runner、CLI/MCP、workbench 或 package lifecycle 都是迁移输入，不是长期架构。

## Public execution

Display 不形成独立 public action family。普通调用只经过六个 OPL-hosted Stage actions，其中 display 的主要消费点是：

- `manuscript_authoring`：形成 figure intent/spec，选择 display capability，执行受控 render 并返回 candidate refs。
- `review_and_quality_gate`：运行 deterministic QC、independent visual/medical review 与 claim-display consistency check。
- `finalize_and_publication_handoff`：绑定 final display refs、submission package refs、quality evidence 与 MAS owner authority。

模板 discovery、figure planning、preflight、render、composition 和 gallery lookup 都是 Stage Tool Affordance Boundary 内的工具选择。旧 `display_pack_capability_discover`、`display_pack_figure_plan`、`display_pack_orchestrate`、`display_pack_preflight` 和 `display_pack_render` 已退出 V2 public/default catalog；仍有 caller 的 handler/source 只能作为 internal residue，待 replacement parity 和 no-active-caller 成立后物理删除。

## Package lifecycle

用户只管理 canonical package `mas`：

```bash
opl packages install mas
opl packages update mas
opl packages uninstall mas
```

OPL 在同一 lifecycle transaction 内解析并物化必需的 `mas-scholar-skills` dependency closure，记录 manifest/content digest、ABI、core exports、physical surface、lifecycle receipt、卸载保护、更新回滚与 currentness。MAS 不暴露内部 activation/status/repair 命令，也不维护 display-specific installer 或 lock authority。

模板 source 可以来自 provider 声明允许的本地目录、Git source 或 package distribution，但 source acquisition、cache、lock、rollback 与 execution environment 都归 OPL。MAS 只消费 SHA-bound descriptor、lock、execution receipt 与 artifact refs。

## Domain artifact contract

MAS 仍需要保留以下医学与论文对象：

- `paper/figure_intent.json`：绑定 `claim_ref`、`data_ref`、`template_id` 与 `figure_kind`。
- `paper/figure_spec.json` / `paper/figure_specs.json`：表达 cohort、endpoint、model、risk horizon、panel role 等医学语义。
- `paper/publication_style_profile.json`：本篇文章实际采用的 style token。
- `paper/figure_style_reference_bundle.json`：link-only 采用/拒绝参考。
- `paper/figure_visual_audit_receipt.json`：独立视觉审阅证据。
- `paper/figure_polish_lifecycle.json`：从 draft 到 manifested 的有序 evidence prefix。
- `paper/build/display_pack_lock.json`、artifact manifest 与 submission manifest refs：绑定输入、renderer、版本、hash、QC 与 provenance。

这些对象是 MAS domain contract 或 paper-local artifact refs，不是 OPL package/runtime truth。文件存在、hash 一致、render 成功或 golden match 不能替代 owner acceptance。

## Renderer boundary

模板包可以携带 R、Python 或显式 adapter code，但执行必须经过 OPL prepared environment 与 Runway/StageRun transport。Renderer 必须：

- 只消费声明的 claim/data/analysis-summary refs；
- 记录 template/version/lock、environment、input/output hash、stdout/stderr 与 layout sidecar refs；
- 不拟合未授权模型、不重算未声明统计量、不静默修补数据；
- 不写 study truth、owner receipt、typed blocker、publication verdict、current package 或 runtime queue；
- 对 summary-only 模板收到 raw analysis input 时 fail closed 到 blocker candidate，由 MAS owner 决定正式 route。

模板是质量下限，不是最终裁决。AI executor 可以在 Stage 授权范围内调整 family、variant、layout、panel、palette、legend、scale 或 backend，但必须保留 claim/data/statistics refs、estimand、source traceability、visual audit 与 authority boundary。

## Source and gallery

ScholarSkills 是专业 Skill、模板、gallery 与 module catalog 的单一 source of truth。MAS 可以保留 link-only exemplar refs 和 paper-local selected template refs，但不能复制 provider catalog、gallery inventory、optional specialist list 或专业 Skill 正文。

Gallery 用于人类快速检查审美下限、覆盖范围与 known limitations。它不证明：

- external package 已安装或 current；
- renderer 在目标环境可运行；
- 当前 paper 的 claim/data/spec 合法；
- visual audit clear；
- artifact mutation、publication ready 或 submission ready。

## Authority and failure

OPL package receipt、environment receipt、StageRun completion、renderer success、layout QC、golden match 与 hosted workbench projection都是输入证据。它们不能：

- 修改医学 claim/data/statistics truth；
- 签 MAS owner receipt、typed blocker 或 human gate；
- 授权 artifact mutation；
- 关闭 publication/submission gate；
- 把 platform repair 或 render success 计作 paper progress。

MAS visual/publication owner 消费同一 work-unit 的 current refs 后，才可以接受、拒绝、route back、签 typed blocker/human gate 或授权 artifact/package 变化。

## Migration closeout

物理删除 legacy display implementation 需要同时满足：

1. V2 Stage public/default caller 已关闭；
2. OPL Stage affordance 覆盖 descriptor discovery、environment、render transport 与 receipt return；
3. MAS figure/quality/authority output replacement parity 成立；
4. legacy caller inventory 为零，或 caller 已明确迁移；
5. source-closure、default-callers、residue-decisions 与 focused display tests fresh green；
6. tombstone/provenance 保留，但不恢复 alias、wrapper 或 command template。

在这些条件全部成立前，只能声明 public/default cutover，不能声明 private implementation 已完全退役。

## 相关入口

- [Medical display](../README.md)
- [Display Pack v2 status](../contracts/display_pack_v2_landing_status.md)
- [Display Agent OS target](../contracts/display_pack_agent_os_target.md)
- [Visual audit protocol](../contracts/medical_display_visual_audit_protocol.md)
- [E2E skeleton](../examples/display_pack_v2_e2e_skeleton.md)
- [Active ideal-state gap plan](../../../active/mas-ideal-state-gap-plan.md)
- [Historical implementation plan](../../../history/capabilities/medical-display/medical_display_template_pack_implementation_plan_2026_04.md)
