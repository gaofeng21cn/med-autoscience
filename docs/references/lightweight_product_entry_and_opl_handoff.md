# Med Auto Science 轻量产品入口与 OPL Handoff

## 1. 当前真相

`Med Auto Science` 现在已经有稳定的：

- `operator entry`
  - workspace 准备、调试、检查、人工治理
- `agent entry`
  - `CLI` / `MCP`，由 `Codex` 或其他 host-agent 调用

但还没有成熟的用户级 `product entry`。

因此，当前最诚实的用户路径仍然是：

- 用户把医学研究目标、数据和约束交给自己的 agent
- agent 再调用 `Med Auto Science`

而不是已经存在一个完整稳定的医疗研究产品前台。
不过现在 repo 内已经把一层 shared-envelope shell 落成 machine-readable surface：

- `build-product-entry`
  - 基于已有 durable study task intake 输出 `direct` / `opl-handoff` 共用 envelope
  - 继续只覆盖 research 主线，不碰 display 支线
  - 当缺少 durable intake 或 selector 不成立时保持 fail-closed

## 2. 目标形态

这个仓理想中的 domain 级产品链路应是：

`User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`

在 `OPL` 家族级入口下，则应兼容：

`User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`

这意味着：

- `OPL` 是 family-level 总入口
- `Med Auto Science` 是 medical research domain 自己的 lightweight direct entry
- 两者同时存在，但作用域不同

## 3. 为什么这一层现在只能冻结到合同

`Med Auto Science` 和别的业务仓不同，它当前还有真实 external runtime gate：

- repo-side seam 已经成立
- outer-loop / watch / supervision / durable surface 已经成立
- 真实长时执行仍经由受控 `MedDeepScientist` backend
- external `Hermes-Agent` host 还没有彻底变成稳定 owner

所以这份文档当前冻结的是：

- 入口语义
- handoff 语义
- 未来 product entry 的边界

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

这份产品入口文档只属于 runtime / gateway 主线，不属于 display 独立支线。

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
2. 在 external gate 不突破的前提下，先把 product-entry shell 与 OPL handoff contract 写清；当前 repo 内已经把 `workspace-cockpit` 收成用户 inbox，`build-product-entry` 也已把 direct / `OPL` handoff envelope 收成 machine-readable shell，但这仍然只是 shell，不是成熟 direct entry。
3. 等 external runtime gate 真正清除后，再把 product entry、runtime session、resume、watch、study progression 接成真实 direct entry。
