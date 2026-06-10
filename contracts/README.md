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

- `contracts/domain_descriptor.json`, `contracts/pack_compiler_input.json`, `contracts/generated_surface_handoff.json`, `contracts/action_catalog.json`, `contracts/agent_tool_arsenal.json`, `contracts/stage_control_plane.json`, `contracts/golden_path_profile.json`, `contracts/stage_artifact_kernel_adoption.json`, `contracts/stage_run_kernel_profile.json`, `contracts/progress_first_safety_envelope.json`, `contracts/memory_descriptor.json`, `contracts/artifact_locator_contract.json`, `contracts/owner_receipt_contract.json`, `contracts/functional_privatization_audit.json`, and `contracts/private_functional_surface_policy.json`: OPL standard domain-agent pack inputs. OPL compiles these into generated interface descriptors; MAS local domain handler targets, owner receipts, controller authority functions, and necessary durable workspace diagnostics stay as domain targets and authority functions. `agent_tool_arsenal.json` indexes ToolArsenalIndex, ToolUseCard, CapabilityInvocationPlan, ToolResultEnvelope, and ToolAuditTrail metadata for OPL-generated tool discovery and invocation; it carries invocation metadata, refs, risk annotations, allowed/forbidden authority flags, and result envelope shapes, not MAS study truth, quality verdicts, owner receipt bodies, artifact authority, publication authority, or production-ready claims. `golden_path_profile.json` declares the single ordinary OPL default path and hidden-variant policy without claiming medical/domain readiness; `stage_artifact_kernel_adoption.json` is the root machine-readable declaration that MAS consumes the OPL Stage Folder + Manifest + Receipt + current pointer kernel while retaining MAS medical authority; `stage_run_kernel_profile.json` defines the minimal StageRun state shell and forbids provider completion, file presence, `latest.json`, read-model, or active run id from becoming transition authority; `progress_first_safety_envelope.json` fixes false-completion, pseudo-evidence, stale read-model, duplicate receipt, artifact-authority drift, external-learning adoption closure status, and Light/Co-Scientist/Evo advisory sidecar boundaries without adding live-path preflight friction.
- Source-defined contract builders under `src/med_autoscience/` may expose MAS-native intake surfaces such as reviewer issue/progress ledgers, display artifact manifests, and source/citation authority packs. They are machine contract sources only when covered by focused tests and linked from current docs; external projects such as ARK remain clean-room pattern sources, not runtime dependencies or authority surfaces.
- `contracts/display-pack-contract.v2.json`: Display Pack v2 descriptor and MAS/OPL Pack OS boundary contract. The validator in `src/med_autoscience/display_pack_v2_contract.py` enforces the required pack/template descriptor fields, authority boundaries, the OPL repo `mas-display-smoke` consumer evidence, external OPL Pack OS substrate refs, and the rule that generic OPL Pack OS is not MAS-owned.
- `contracts/publication_figure_quality_contract.json`: paper-level Display Pack v2 figure-quality surface index. The source-defined validators in `src/med_autoscience/publication_figure_quality_contract.py` enforce `figure_intent.json`, single-figure `figure_spec.json`, batch `figure_specs.json`, `figure_style_reference_bundle.json`, `figure_visual_audit_receipt.json`, and `ai_illustration_receipt.json`; `display_pack_lock.json` and submission manifests preserve refs, status, and hashes without turning visual audit into publication authority.
- `contracts/medical_figure_spec_contract.json`: declarative medical figure grammar surface. The validator in `src/med_autoscience/medical_figure_spec_contract.py` enforces `paper/figure_spec.json` and `paper/figure_specs.json` fields that bind `figure_intent`, Display Template, figure kind, medical semantics, and optional panel roles; it is not a Vega-Lite runtime, publication verdict, renderer, or data/statistics mutation surface.
- `contracts/figure_polish_lifecycle_contract.json`: paper-level AI/VLM polish lifecycle surface. The source-defined validator in `src/med_autoscience/figure_polish_lifecycle_contract.py` enforces the ordered state prefix from `draft_rendered` through `publication_manifested`, binds events to `figure_visual_audit_receipt` and `display_pack_lock.publication_figure_quality_refs`, and forbids AI/VLM quality-loop evidence from mutating data/statistics/evidence marks or carrying publication verdicts.
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

- `contracts/domain_descriptor.json`、`contracts/pack_compiler_input.json`、`contracts/generated_surface_handoff.json`、`contracts/action_catalog.json`、`contracts/agent_tool_arsenal.json`、`contracts/stage_control_plane.json`、`contracts/golden_path_profile.json`、`contracts/stage_artifact_kernel_adoption.json`、`contracts/stage_run_kernel_profile.json`、`contracts/progress_first_safety_envelope.json`、`contracts/memory_descriptor.json`、`contracts/artifact_locator_contract.json`、`contracts/owner_receipt_contract.json`、`contracts/functional_privatization_audit.json`、`contracts/private_functional_surface_policy.json`：OPL standard domain-agent pack 输入。OPL 用它们生成统一接口 descriptor；MAS 本地 domain handler target、owner receipt、controller authority function 与必要 durable workspace diagnostic 继续作为 domain target 与 authority function。`agent_tool_arsenal.json` 索引 ToolArsenalIndex、ToolUseCard、CapabilityInvocationPlan、ToolResultEnvelope 和 ToolAuditTrail metadata，供 OPL generated tool discovery / invocation 消费；它只承载调用 metadata、refs、risk annotations、allowed/forbidden authority flags 和 result envelope shape，不承载 MAS study truth、quality verdict、owner receipt body、artifact authority、publication authority 或 production-ready claim。`golden_path_profile.json` 声明单一 OPL ordinary default path 与 hidden-variant policy，不声明医学/domain readiness；`stage_artifact_kernel_adoption.json` 是根层机器声明：MAS 接入 OPL Stage Folder + Manifest + Receipt + current pointer kernel，但 MAS medical authority 仍归 MAS；`stage_run_kernel_profile.json` 定义最小 StageRun 状态壳，并禁止 provider completion、file presence、`latest.json`、read-model 或 active run id 成为 transition authority；`progress_first_safety_envelope.json` 固定错误完成、伪证据、旧 read-model、重复 receipt、artifact authority 漂移、external-learning adoption closure status 和 Light/Co-Scientist/Evo advisory sidecar 边界，同时不增加 live path preflight 摩擦。
- `src/med_autoscience/` 下的 source-defined contract builder 可以暴露 MAS-native intake surface，例如 reviewer issue/progress ledger、display artifact manifest 和 source/citation authority pack。只有在 focused tests 覆盖并由当前 docs 索引后，它们才作为机器 contract source 读取；ARK 这类外部项目始终只是 clean-room pattern source，不是 runtime dependency 或 authority surface。
- `contracts/display-pack-contract.v2.json`：Display Pack v2 descriptor 与 MAS/OPL Pack OS 边界合同。`src/med_autoscience/display_pack_v2_contract.py` 中的 validator 校验 pack/template descriptor 必备字段、authority boundary、OPL repo `mas-display-smoke` consumer evidence、外部 OPL Pack OS substrate refs，以及 generic OPL Pack OS 不是 MAS-owned 通用基座。
- `contracts/publication_figure_quality_contract.json`：paper-level Display Pack v2 图质量 surface 索引。`src/med_autoscience/publication_figure_quality_contract.py` 中的 source-defined validator 强制校验 `figure_intent.json`、单图 `figure_spec.json`、批量 `figure_specs.json`、`figure_style_reference_bundle.json`、`figure_visual_audit_receipt.json` 和 `ai_illustration_receipt.json`；`display_pack_lock.json` 与 submission manifest 只保留 refs、status 和 hash，不把视觉审计变成 publication authority。
- `contracts/medical_figure_spec_contract.json`：声明式医学 figure grammar surface。`src/med_autoscience/medical_figure_spec_contract.py` 中的 validator 强制校验 `paper/figure_spec.json` 和 `paper/figure_specs.json`，用于绑定 `figure_intent`、Display Template、figure kind、医学语义与可选 panel role；它不是 Vega-Lite runtime、publication verdict、renderer 或数据/统计改写面。
- `contracts/figure_polish_lifecycle_contract.json`：paper-level AI/VLM polish lifecycle surface。`src/med_autoscience/figure_polish_lifecycle_contract.py` 中的 source-defined validator 强制校验从 `draft_rendered` 到 `publication_manifested` 的有序状态前缀，把 event 绑定到 `figure_visual_audit_receipt` 与 `display_pack_lock.publication_figure_quality_refs`，并禁止 AI/VLM 质量循环证据改动 data/statistics/evidence mark 或携带 publication verdict。
- `contracts/production_acceptance/`：production acceptance 与 evidence tail snapshot。这里可以记录 body-free owner receipt refs、typed blocker refs、no-forbidden-write refs 和 provenance hash；不承载 paper body、memory body、artifact body、quality verdict body 或 production-ready claim。
- `contracts/modules/`：controller、runtime、eval hygiene ownership 的模块边界 contract。
- `contracts/opl-framework/`：OPL Framework projection、compatible-package 与 helper-consumption contract。
- `contracts/schemas/`：稳定 product-entry surface 的 JSON schema。

本 README 只是给人和 agent 的索引例外，不承载 contract 字段真相。
