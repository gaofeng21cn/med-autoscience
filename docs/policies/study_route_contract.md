# Study Route Contract

本 policy 固定 `MedAutoScience` 的研究阶段 route 合同边界。
canonical source 位于 `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml` 的 `route_contracts`。
`modes` 只回答某个 entry mode 当前允许走哪些 route，正式 route 定义统一以 `route_contracts` 为准。

## 固定字段

每个 route 必须稳定提供以下字段：

- `goal`
- `key_question`
- `enter_conditions`
- `hard_success_gate`
- `durable_outputs_minimum`
- `human_gate_boundary`
- `next_routes`
- `route_back_triggers`

字段语义固定如下：

- `goal`：当前 route 唯一要完成的阶段目标
- `key_question`：当前 route 唯一回答的高层研究问题，必须可供 agent 直接判断 route 边界，不暴露底层函数或实现细节
- `enter_conditions`：进入该阶段前必须已经满足的前置条件
- `hard_success_gate`：什么状态算当前阶段正式过线
- `durable_outputs_minimum`：离开当前阶段前至少要留下的 durable surface 或可引用产物
- `human_gate_boundary`：该 route 何时必须进入 human gate 或停止自动推进
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

## Stage Packet 规则

从 `DeepScientist` stage operational packet 学到的规则，在 `MAS` 中统一表达为医学化 stage packet：

- 进入阶段前，必须能恢复 `study_id`、`active_route`、`quest_id`、study charter 边界、objective contract、ledger refs 与当前 blocker。
- 离开阶段前，必须留下 route outcome、evidence refs、reviewer-first concern 状态、failed paths、winning path、resume point 与 next route。
- `idea`、`analysis-campaign`、`write`、`finalize`、`decision` 都应引用 overlay 中的 `medical-research-stage-packet.block.md`，避免每个 stage 各写一套不可比较的 prose。
- stage packet 是 route truth 的最小可接力单元；它可以被 `study-progress`、controller、publication gate 或人工接管读取。

## 维护规则

- route 合同统一维护在 canonical YAML，不在每个 mode 内重复定义。
- route 名称必须稳定、短、可长期复用。
- 每个 route 只回答一个 `key_question`；新增或调整 route 时必须先确认这个问题与已有 route 不重叠。
- route 之间的前进、回退、治理边界应通过 `next_routes` 与 `route_back_triggers` 表达，不把阶段跳转藏在 prose 里。
- route 产物要求以 durable surface、artifact、ledger、decision record 这类可引用对象表述。
- 任何写作、补充分析、最终交付动作都要能回指当前 route 合同与 study charter 边界。

## 吸收规则

- 变更 route 合同时，先改 canonical YAML，再同步 `docs/runtime/agent_entry_modes.md` 与模板输出。
- 变更 route 合同属于 contract surface 变更，至少补跑 `tests/test_agent_entry_assets.py` 与 `make test-meta`。
