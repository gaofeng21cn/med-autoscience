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
| [plans](./plans/) | 活跃 implementation plan 和 template-pack 设计。 |
| [provenance](./provenance/) | 真实论文审计和能力 provenance。 |
| [history](../../history/capabilities/medical-display/README.md) | 退役 owner brief、baseline program、exemplar intake 和 exhausted exploration record。 |

## 主要入口

- [Portfolio consolidation](./portfolio/medical_display_portfolio_consolidation.md)
- [Active board](./board/medical_display_active_board.md)
- [Platform mainline](./contracts/medical_display_platform_mainline.md)
- [Audit guide](./contracts/medical_display_audit_guide.md)
- [Template catalog](./catalogs/medical_display_template_catalog.md)

历史 exemplar 和退役 brief 只保留 provenance；除非真实 MAS 论文需求通过 active board 重开，否则不作为当前 backlog。

`board/medical_display_active_board.md` 只维护当前唯一 active round 与下一轮 reroute 边界。已吸收 round 的 owner note、完整命令流水、exemplar intake 细节和历史 capability ledger 进入 history/provenance，不继续堆在 board 中。

## Memory 边界

医学展示有两层复用内容：

- 已审计模板、input schema、renderer family、layout QC profile、shell contract、生成型 catalog 和 packaging manifest 是强 display contract；
- 论文为什么选某类图、视觉审计中反复出现的可读性失败、文章级风格取舍、图表路线选择 caveat，适合作为自然语言经验记忆。

第一层归属本能力树和 source/contract surface。第二层可以被 MAS stage knowledge packet 和 publication route memory 引用，但不能替代实际渲染图审阅、模板合同或 QC 合同。
