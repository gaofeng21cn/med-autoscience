# 医学展示能力线

[English](./README.md) | **中文**

这个目录是 medical display 能力线的当前入口。
它只索引当前生命周期面，不把历史记录重新搬回 active 树。

## 生命周期地图

| 生命周期角色 | 入口 | 含义 |
| --- | --- | --- |
| active execution surface | [medical_display_active_board.md](./medical_display_active_board.md) | 当前 owner round 状态、phase、next baton，以及下一轮 display round 的打开规则。 |
| current inventory / reference | [medical_display_audit_guide.md](./medical_display_audit_guide.md)、[medical_display_template_catalog.md](./medical_display_template_catalog.md)、[medical_display_arsenal.md](./medical_display_arsenal.md) | 当前 strict audited inventory、生成式模板矩阵和人话版能力库存。 |
| roadmap / backlog | [medical_display_family_roadmap.md](./medical_display_family_roadmap.md)、[medical_display_template_backlog.md](./medical_display_template_backlog.md) | 长线论文家族方向，以及 inactive 或 candidate 扩容池；这些文件本身不构成 active blocker。 |
| implementation plan | [medical_display_template_pack_architecture.md](./medical_display_template_pack_architecture.md)、[medical_display_template_pack_implementation_plan.md](./medical_display_template_pack_implementation_plan.md)、[medical_display_platform_mainline.md](./medical_display_platform_mainline.md) | 模板包架构、实施计划和平台运行模型。 |
| review discipline and route references | [medical_display_visual_audit_protocol.md](./medical_display_visual_audit_protocol.md)、[medical_figure_route_cookbook.md](./medical_figure_route_cookbook.md)、[sidecar_figure_routes.md](./sidecar_figure_routes.md)、[medical_display_anchor_paper_audit.md](./medical_display_anchor_paper_audit.md) | 视觉审计协议、路线/cookbook 参考和真实论文审计参考。 |
| historical provenance | [历史归档](../../history/capabilities/medical-display/README.zh-CN.md) | 已退役 owner brief、baseline-completion provenance、exemplar intake 和扩库历史。 |

## 使用规则

当前执行状态以 [medical_display_active_board.md](./medical_display_active_board.md) 为准。

当前库存以 audit guide、template catalog 和 arsenal 为准。历史 exemplar、已退役 owner brief、已耗尽 intake ledger 只作为 provenance；只有真实 MAS paper demand 通过 active board 重新打开时，才进入新一轮执行。

需要 medical-display 子树的压缩组合地图时，读取 [medical_display_portfolio_consolidation.md](./medical_display_portfolio_consolidation.md)。
