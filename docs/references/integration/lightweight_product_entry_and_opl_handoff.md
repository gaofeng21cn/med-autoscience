# Med Auto Science 集成参考：产品入口载荷与 OPL Handoff

## 1. 这份参考记录什么

这份文档记录 `Med Auto Science` 的产品入口载荷和 `OPL` handoff 之间的集成合同。

对外第一主语仍然是独立 medical research domain agent 和单一 MAS app skill；这里记录的是桥接载荷如何保持一致，而不是把桥接载荷写成前台产品主线。

repo 内已经把一层 shared-envelope shell 落成 machine-readable surface：

- `build-product-entry`
  - 基于已有 durable study task intake 输出共用 envelope
  - 继续只覆盖 research 主线，不碰 display 支线
  - 当缺少 durable intake 或 selector 不成立时保持 fail-closed

## 2. 目标形态

这个仓对外主语固定为“独立 medical research domain agent”和“单一 MAS app skill”，因此目标形态只记录两类集成路径：

- direct path：
  `User/Agent -> Med Auto Science -> single MAS app skill -> runtime/session surfaces`

- OPL integration handoff：
  `User/Agent -> OPL Entry -> OPL session/runtime/projection orchestration -> MAS handoff envelope -> Med Auto Science`

`gateway / harness` 术语继续保留为内部架构边界语言，不作为 MAS 的对外第一身份。

这意味着：

- `Med Auto Science` 是独立 medical research domain agent，可直连调用。
- `OPL` 负责 family-level session/runtime/projection 编排与 shared modules/contracts/indexes，不承担研究 owner。
- 两条集成路径共享同一套 `study semantics`、authority boundary 与 return surface contract。

## 3. 为什么这一层只保留为参考

`Med Auto Science` 和别的业务仓不同，它当前还有真实 external runtime gate：

- repo-side seam 已经成立
- outer-loop / watch / supervision / durable surface 已经成立
- 真实长时执行仍经由受控 `MedDeepScientist` backend
- external `Hermes-Agent` host 还没有彻底变成稳定 owner

所以这份文档当前冻结的是：

- 入口语义
- handoff 语义
- 未来 product entry / handoff 的边界

而不是宣称它已经落成一个成熟的 direct product entry。

## 4. 共享 handoff envelope

`OPL -> Med Auto Science` 至少共享下面这组最小字段：

- `target_domain_id`
- `task_intent`
- `entry_mode`
- `workspace_locator`
- `runtime_session_contract`
- `return_surface_contract`

在这层公共 envelope 之上，医学研究域继续补充：

- `study_id`
- `journal_target`
- `evidence_boundary`

## 5. 与 runtime 主线、display 支线的关系

这份产品入口文档只属于 runtime 主线，不属于 display 独立支线；其中 `gateway / harness` 仅用于内部架构边界说明。

必须同时保持：

- runtime 主线继续朝 external `Hermes-Agent` 切换推进
- display / 论文配图资产化继续独立演进
- 两条线不互相改写对方的真相

## 6. 当前不应过度宣称的事

- 不能把 `Med Auto Science Product Entry` 写成已经成熟落地
- 不能把 `OPL -> Med Auto Science` handoff 写成已经具备独立用户前台
- 不能把 repo-side seam 写成“上游 `Hermes-Agent` 已经完整接管”
- 不能因为补入口合同，就偷跑 physical migration 或 cross-repo rewrite

## 7. 下一步落地方向

1. 继续保持 `CLI / MCP / controller` 的入口语义稳定。
2. 在 external gate 不突破的前提下，先把 product-entry shell 与 OPL handoff contract 写清；当前 repo 内已经把 `workspace-cockpit` 收成用户 inbox，`build-product-entry` 也已把共用 envelope 收成 machine-readable shell，但这仍然只是 shell，不是成熟前台。
3. 等 external runtime gate 真正清除后，再把 product entry、runtime session、resume、watch、study progression 接成更完整的 direct path。
