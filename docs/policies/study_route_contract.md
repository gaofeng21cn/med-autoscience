# Study Route Contract

本 policy 固定 `MedAutoScience` 的研究阶段 route 合同边界。
canonical source 位于 `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml` 的 `route_contracts`。
`modes` 只回答某个 entry mode 当前允许走哪些 route，正式 route 定义统一以 `route_contracts` 为准。

## 固定字段

每个 route 必须稳定提供以下字段：

- `goal`
- `enter_conditions`
- `hard_success_gate`
- `durable_outputs_minimum`
- `next_routes`
- `route_back_triggers`

字段语义固定如下：

- `goal`：当前 route 唯一要完成的阶段目标
- `enter_conditions`：进入该阶段前必须已经满足的前置条件
- `hard_success_gate`：什么状态算当前阶段正式过线
- `durable_outputs_minimum`：离开当前阶段前至少要留下的 durable surface 或可引用产物
- `next_routes`：当前阶段过线后的正式去向
- `route_back_triggers`：发现缺口时应回退的触发条件

## Canonical Routes

当前 canonical route 主线至少覆盖：

- `scout`
- `baseline`
- `analysis-campaign`
- `write`
- `finalize`
- `decision`

这些 route 是 MAS 当前研究阶段纪律的最小稳定集合。
新增 route 可以扩展在同一张 `route_contracts` 表里，已有 route 的字段语义保持稳定。

## 维护规则

- route 合同统一维护在 canonical YAML，不在每个 mode 内重复定义。
- route 名称必须稳定、短、可长期复用。
- route 之间的前进、回退、治理边界应通过 `next_routes` 与 `route_back_triggers` 表达，不把阶段跳转藏在 prose 里。
- route 产物要求以 durable surface、artifact、ledger、decision record 这类可引用对象表述。
- 任何写作、补充分析、最终交付动作都要能回指当前 route 合同与 study charter 边界。

## 吸收规则

- 变更 route 合同时，先改 canonical YAML，再同步 `docs/runtime/agent_entry_modes.md` 与模板输出。
- 变更 route 合同属于 contract surface 变更，至少补跑 `tests/test_agent_entry_assets.py` 与 `make test-meta`。
