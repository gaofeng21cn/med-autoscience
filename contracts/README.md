# Contracts

Owner: `MedAutoScience`
Purpose: `machine_contract_index`
State: `current_index`
Machine boundary: 本目录是 machine-readable contracts。本文只做索引，不复制 contract 字段为第二真相源。

## 标准 OPL Agent 输入

| Contract | 用途 |
| --- | --- |
| `domain_descriptor.json` | canonical agent/package id、machine domain id、package role、refs-only work-item inventory mapping、generated surface owner 与 authority boundary |
| `pack_compiler_input.json` | OPL pack compiler 输入与 MAS runtime role |
| `action_catalog.json` | V2 closed catalog：六个公开 Stage action + 一个内部 authority action |
| `domain_handler_registry.json` | closed minimal-authority callable binding；不提供用户 surface |
| `schemas/v2/mas-stage-action.input.schema.json` | 六个公开 Stage action 的 closed input schema |
| `schemas/v2/mas-stage-action.output.schema.json` | 六个公开 Stage action 的 closed output schema |
| `research_trajectory_contract.json` | MAS 科研假设、验证、证据解释、路线调整、固定存储位置、接受门与医学化投影边界 |
| `schemas/v2/mas-research-trajectory-event.schema.json` | candidate/accepted 科研轨迹事件；运行结果、证据判断与路线决定相互独立 |
| `schemas/v2/mas-research-trajectory-snapshot.schema.json` | 从 accepted event set 确定性重建的科研路线图 snapshot |
| `schemas/v2/mas-medical-narrative.schema.json` | 面向医生、教授和科研人员的医学论文式人读叙事字段 |
| `schemas/v2/mas-paper-mission-authority.input.schema.json` | 内部 authority callable 的 closed input schema |
| `schemas/v2/mas-paper-mission-authority.output.schema.json` | 内部 authority callable 的 closed output schema |
| `source_closure_audit.json` | OPL source-closure owner 写回的 typed decision ledger；空表不代表 closure |
| `generated_surface_handoff.json` | CLI/MCP/Skill/product/status/workbench/environment owner handoff |
| `runtime_environment_requirements.json` | MAS environment requirement profile |
| `submission-resource-requirements.json` | submission 资源的 package bundled / host exact-path 需求、request-only 缺失输出与 OPL Pack receipt consumer |
| `domain_route_profile.json` | domain route identity、task kind 与 handler mapping |
| `domain_projection_profile.json` | OPL-consumable refs-only projection |

## Authority contracts

| Contract | 用途 |
| --- | --- |
| `private_functional_surface_policy.json` | private surface forbidden/allowed boundary |
| `functional_privatization_audit.json` | generated/hosted handoff 与 no-private-platform guard |
| `domain_handler_registry.json` | retained authority handler binding |
| `agent/stages/manifest.json` | canonical stage policy source; OPL generates the stage control plane |

## Contract 规则

- 普通 interface 从 V2 Stage action metadata/schema 生成；内部 authority callable 只从 closed registry 解析，不在 contracts 中复制 CLI/MCP/workbench implementation。
- MAS contract 只声明 domain requirement、authority、handler target、refs 与 forbidden writes。
- OPL-owned runtime、StateIndex、environment、lifecycle、observability 和 hosted surface通过 stable handoff/ref 引用，不在 MAS 复制实现合同。
- 旧私有控制面只保留在 `docs/history/` 与 Git provenance；active contracts 不保留其路径、validator、wrapper 或 compatibility shape。
- 叙述性 docs 不是机器接口；机器消费者不得解析 Markdown 文案或章节。

## Ready 边界

Contract/schema valid、descriptor ready、action count 与 generated interface resolution 只证明 repo structural currentness。它们不证明 provider running、paper progress、quality/publication ready、artifact mutation authorization 或 production ready。

## 维护方式

1. 新增/修改公开 action：改 catalog、Stage manifest 与 V2 input/output schema；新增 retained authority callable 时同时改 closed registry 与 authority inventory。
2. 新增 environment requirement：改 requirement profile，由 OPL substrate 实现 prepare/run。
3. 新增 retained authority function：更新 authority inventory 与 forbidden-write boundary。
4. 通用 platform capability：改 OPL contract/implementation，MAS 只保留消费 ref。
5. 已退役 surface：删除 active caller，保留最小 tombstone/no-resurrection evidence。

## 人读入口

- [Project](../docs/project.md)
- [Architecture](../docs/architecture.md)
- [Invariants](../docs/invariants.md)
- [Active plan](../docs/active/mas-ideal-state-gap-plan.md)
