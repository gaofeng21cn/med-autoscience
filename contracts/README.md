# Contracts

Owner: `MedAutoScience`
Purpose: `machine_contract_index`
State: `current_index`
Machine boundary: 本目录是 machine-readable contracts。本文只做索引，不复制 contract 字段为第二真相源。

## 标准 OPL Agent 输入

| Contract | 用途 |
| --- | --- |
| `domain_descriptor.json` | canonical id、package role、refs-only work-item inventory mapping、generated surface owner 与 authority boundary |
| `pack_compiler_input.json` | OPL pack compiler 输入与 MAS runtime role |
| `action_catalog.json` | 22-action catalog、handler targets、schema refs |
| `schemas/v1/mas-action.input.schema.json` | action input schemas |
| `schemas/v1/mas-action.output.schema.json` | action output schemas |
| `generated_surface_handoff.json` | CLI/MCP/Skill/product/status/workbench/environment owner handoff |
| `runtime_environment_requirements.json` | MAS environment requirement profile |
| `domain_route_profile.json` | domain route identity、task kind 与 handler mapping |
| `domain_projection_profile.json` | OPL-consumable refs-only projection |

## Authority contracts

| Contract | 用途 |
| --- | --- |
| `authority_kernel_inventory.json` | retained minimal authority function inventory |
| `private_functional_surface_policy.json` | private surface forbidden/allowed boundary |
| `functional_privatization_audit.json` | generated/hosted handoff 与 no-private-platform guard |
| `next_action_envelope_contract.json` | canonical next-action shape |
| `agent/stages/manifest.json` | canonical stage policy source; OPL generates the stage control plane |

## Contract 规则

- 普通 interface 从 action metadata/schema 生成；不在 contracts 中复制 CLI/MCP/workbench implementation。
- MAS contract 只声明 domain requirement、authority、handler target、refs 与 forbidden writes。
- OPL-owned runtime、StateIndex、environment、lifecycle、observability 和 hosted surface通过 stable handoff/ref 引用，不在 MAS 复制实现合同。
- Tombstone/no-resurrection contract 可以保留旧 identity，不得让旧 path 重新成为 current caller。
- 叙述性 docs 不是机器接口；机器消费者不得解析 Markdown 文案或章节。

## Ready 边界

Contract/schema valid、descriptor ready、action count 与 generated interface resolution 只证明 repo structural currentness。它们不证明 provider running、paper progress、quality/publication ready、artifact mutation authorization 或 production ready。

## 维护方式

1. 新增/修改 action：改 catalog、input/output schema 与 domain handler target。
2. 新增 environment requirement：改 requirement profile，由 OPL substrate 实现 prepare/run。
3. 新增 retained authority function：更新 authority inventory 与 forbidden-write boundary。
4. 通用 platform capability：改 OPL contract/implementation，MAS 只保留消费 ref。
5. 已退役 surface：删除 active caller，保留最小 tombstone/no-resurrection evidence。

## 人读入口

- [Project](../docs/project.md)
- [Architecture](../docs/architecture.md)
- [Invariants](../docs/invariants.md)
- [Active plan](../docs/active/mas-ideal-state-gap-plan.md)
