# Contracts Root

Owner: `MedAutoScience Contract Surface`
Purpose: `machine_contract_index`
State: `active_support`
Machine boundary: This README is a human index for the `contracts/` root. Machine truth stays in the structured contract payloads, schemas, source, tests, generated descriptors, CLI/product-entry behavior, owner receipts, typed blockers, and runtime/controller durable surfaces. This README must not become a second source of truth for contract fields, readiness claims, quality verdicts, artifact authority, publication authority, or runtime ownership.

`contracts/` is the repo root for machine-readable governance contracts.

Keep structured payloads here when other agents, CLIs, tests, or runtime entry
surfaces must consume the contract directly. Narrative design notes belong under
`docs/`; retired runtime explanations belong under `docs/history/`.

MAS is published as a medical research Foundry Agent and an OPL-compatible
package built on OPL Framework. Machine-readable product positioning lives in
the product-entry manifest, while this directory keeps the contract families
that let OPL discover, index, and validate MAS package metadata without owning
MAS medical research truth, quality verdicts, runtime owner surfaces, artifact
authority, or publication authority.

AI-first quality contracts assume separate agent tasks for execution and
review/audit. Executor receipts and reviewer/auditor receipts must come from
independent invocations with separate task/context records; self-review by the
same execution agent is not valid quality-gate evidence.

Current contract families:

- `contracts/domain_descriptor.json`, `contracts/pack_compiler_input.json`, `contracts/generated_surface_handoff.json`, `contracts/action_catalog.json`, `contracts/stage_control_plane.json`, `contracts/memory_descriptor.json`, `contracts/artifact_locator_contract.json`, `contracts/owner_receipt_contract.json`, `contracts/functional_privatization_audit.json`, and `contracts/private_functional_surface_policy.json`: OPL standard domain-agent pack inputs. OPL compiles these into generated interface descriptors; MAS local domain handler targets, owner receipts, controller authority functions, and necessary durable workspace diagnostics stay as domain targets and authority functions.
- `contracts/production_acceptance/`: production-acceptance and evidence-tail snapshots. These payloads may record body-free owner receipt refs, typed blocker refs, no-forbidden-write refs, and provenance hashes; they do not carry paper bodies, memory bodies, artifact bodies, quality verdict bodies, or production-ready claims.
- `contracts/modules/`: module boundary contracts for controller, runtime, and eval hygiene ownership.
- `contracts/opl-framework/`: OPL Framework projection, compatible-package, and helper-consumption contracts.
- `contracts/schemas/`: JSON schemas for stable product-entry surfaces.

This README is the index exception for humans and agents. It must not become a
second source of truth for contract fields.

## 中文

`contracts/` 是仓库根部的机器可读 governance contract 入口。

需要被 agent、CLI、测试或 runtime 入口直接消费的结构化 payload 放在这里。叙述性设计说明进入
`docs/`；已退休的 runtime 边界说明进入 `docs/history/`。

MAS 对外发布为医学研究 Foundry Agent，也是 built on OPL Framework 的
OPL-compatible package。机器可读产品定位由 product-entry manifest 持有；本目录只保存
OPL 发现、索引和验证 MAS package metadata 所需的 contract 家族，不让 OPL 持有 MAS 的
medical research truth、quality verdict、runtime owner surface、artifact authority 或
publication authority。

AI-first quality contract 默认要求执行与审阅/审计是独立 agent task。executor receipt 与
reviewer/auditor receipt 必须来自独立 invocation，并有分开的 task/context record；同一个
执行 agent 的自审不能作为关闭 quality gate 的证据。

当前 contract 家族：

- `contracts/domain_descriptor.json`、`contracts/pack_compiler_input.json`、`contracts/generated_surface_handoff.json`、`contracts/action_catalog.json`、`contracts/stage_control_plane.json`、`contracts/memory_descriptor.json`、`contracts/artifact_locator_contract.json`、`contracts/owner_receipt_contract.json`、`contracts/functional_privatization_audit.json`、`contracts/private_functional_surface_policy.json`：OPL standard domain-agent pack 输入。OPL 用它们生成统一接口 descriptor；MAS 本地 domain handler target、owner receipt、controller authority function 与必要 durable workspace diagnostic 继续作为 domain target 与 authority function。
- `contracts/production_acceptance/`：production acceptance 与 evidence tail snapshot。这里可以记录 body-free owner receipt refs、typed blocker refs、no-forbidden-write refs 和 provenance hash；不承载 paper body、memory body、artifact body、quality verdict body 或 production-ready claim。
- `contracts/modules/`：controller、runtime、eval hygiene ownership 的模块边界 contract。
- `contracts/opl-framework/`：OPL Framework projection、compatible-package 与 helper-consumption contract。
- `contracts/schemas/`：稳定 product-entry surface 的 JSON schema。

本 README 只是给人和 agent 的索引例外，不承载 contract 字段真相。
