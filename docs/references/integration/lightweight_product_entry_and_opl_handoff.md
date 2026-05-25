# Med Auto Science 集成参考：产品入口载荷与 OPL Handoff

Owner: `MedAutoScience`
Purpose: `Support MAS integration and OPL handoff understanding.`
State: `support_reference`
Machine boundary: Human-readable integration reference only; callable and generated-surface truth remains in manifests, contracts, source, tests, OPL handoff contracts, and read-model output.

## 1. 这份参考记录什么

这份文档记录 `Med Auto Science` 的产品入口载荷和 `OPL` handoff 之间的集成合同。

对外第一主语仍然是独立 medical research domain agent 和单一 MAS app skill；这里记录的是桥接载荷如何保持一致，而不是把桥接载荷写成前台产品主线。

repo 内已经把 service-safe domain entry、product-entry builder 与 shared handoff envelope 落成 machine-readable surface：

- `MedAutoScienceDomainEntry`
  - 给 direct MAS skill、CLI 和 OPL generated / hosted surface 复用同一个 structured entry adapter。
  - command catalog 以 `product-entry-status`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress`、`progress-projection`、`product-entry-manifest` 和 `build-product-entry` 为当前 service-safe 入口集合。
- `build-product-entry`
  - CLI 入口是 `medautosci product build-entry --profile <profile> --study-id <study_id> --entry-mode direct|opl-handoff`；内部 service-safe command id 保持 `build-product-entry`。
  - 基于已有 durable study task intake 输出共用 envelope；缺少 durable intake 或 study selector 不成立时保持 fail-closed。
  - 输出 `domain_authority_handoff_contract`、`managed_runtime_contract`、`return_surface_contract`、`domain_entry_contract` 和 `user_interaction_contract`，供 direct path 与 OPL-handoff path 共享。

## 2. 目标形态

这个仓对外主语固定为“独立 medical research domain agent”和“单一 MAS app skill”，因此目标形态只记录两类集成路径：

- direct path：
  `User/Agent -> Med Auto Science -> single MAS app skill -> runtime/session surfaces`

- OPL stage handoff：
  `User/Agent -> OPL stage runtime -> stage attempt / queue / receipt / projection -> MAS handoff envelope -> Med Auto Science`

这意味着：

- `Med Auto Science` 是独立 medical research domain agent，可直连调用。
- `OPL` 负责 family-level stage attempt、queue/wakeup、receipt、projection 与 shared modules/contracts/indexes，不承担研究 owner。
- 两条集成路径共享同一套 `study semantics`、authority boundary 与 return surface contract。

## 3. 为什么这一层只保留为参考

这份文档只保留为参考，是因为当前 callable truth 已经由 contracts、source、CLI/read-model、product-entry manifest 与 OPL handoff contracts 承担；本文只解释这些机器面之间的 owner split。

当前冻结的是：

- direct MAS app skill、CLI 和 OPL generated / hosted surfaces 共享同一个 MAS domain entry adapter。
- OPL/Temporal 是 hosted autonomous runtime 的默认 owner；MAS 不再把 external `MedDeepScientist` backend、Hermes host 或 local LaunchAgent 写成默认 runtime gate。
- product-entry / status / workbench / sidecar shell 仍是 strict source-purity tail：它们可以作为 direct handler、domain target 或 diagnostic bridge 活跃存在，但长期 generated/default caller owner 归 OPL，不能写成 MAS 自有 generic product runtime。
- `MedDeepScientist` 只保留为 source provenance、historical fixture、explicit archive import、backend audit、upstream intake 或 parity oracle reference；`Hermes-Agent` 只作为显式非默认 executor/proof lane 或历史 provenance。

## 4. 共享 handoff envelope

`OPL -> Med Auto Science` 至少共享下面这组最小字段：

- `target_domain_id`
- `task_intent`
- `entry_mode`
- `workspace_locator`
- `domain_authority_handoff_contract`
- `managed_runtime_contract`
- `return_surface_contract`
- `domain_entry_contract`
- `user_interaction_contract`

在这层公共 envelope 之上，医学研究域继续补充：

- `study_id`
- `journal_target`
- `evidence_boundary`

## 5. 与 runtime 主线、display 支线的关系

这份产品入口文档只解释 product-entry / OPL handoff 集成，不持有 Progress Portal、submission package、artifact authority 或 quality verdict 的当前真相；其中 OPL 表示 stage-led framework handoff、generated/default caller owner 和 hosted runtime owner，不表示 MAS 的对外第一身份。

必须同时保持：

- runtime 主线继续以 OPL/Temporal hosted autonomy 为默认 owner，MAS 只输出 domain authority refs、owner receipt、typed blocker 和 safe action refs。
- display / Progress Portal / OPL App workbench 继续作为 projection / operator surface 独立演进。
- 两条线不互相改写对方的真相

## 6. 当前不应过度宣称的事

- 不能把 product-entry / workbench shell 写成 MAS 长期自有 generic product runtime；它们当前仍是 OPL generated/default caller cutover 前的 active migration surface。
- 不能把 `OPL -> Med Auto Science` handoff 写成 MAS study truth、publication quality、artifact authority、memory body、`current_package` freshness proof 或 domain-ready verdict。
- 不能把 repo-side seam 写成“上游 `Hermes-Agent` 已经完整接管”或“external runtime gate 仍阻塞当前默认 runtime”；当前默认 hosted runtime owner 是 OPL/Temporal。
- 不能因为补入口合同，就偷跑 physical migration 或 cross-repo rewrite

## 7. 下一步落地方向

1. 继续保持 `CLI / MCP / controller` 的入口语义稳定。
2. 继续把 `product-entry-status`、`workspace-cockpit`、`build-product-entry`、`sidecar export|dispatch` 和 domain entry contract 对齐到同一套 `agent/` pack、contracts、owner receipt、typed blocker 和 no-forbidden-write boundary。
3. 当 OPL generated/default caller parity、active-caller proof、MAS owner receipt parity 和 focused tests 成立后，直接收薄或删除 repo-local product/status/workbench/sidecar shell；需要来龙去脉只保留 history/provenance，不新增 compatibility alias。
