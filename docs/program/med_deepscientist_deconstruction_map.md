# MedDeepScientist Deconstruction Map

这份文档把 `MedDeepScientist` 在新主线 runtime topology 下的解构路线冻结为 repo-tracked truth。

当前固定边界是：

- `MedAutoScience`：唯一研究入口、research gateway、study / workspace / outer-loop authority owner
- `Hermes`：新的外层 runtime substrate owner，负责 backend-generic transport、runtime handle、durable surface 与 substrate-level contract
- `MedDeepScientist`：受控 research backend，只保留当前仍需由 research runtime 承担的 backend 能力
- 旧 `Codex-default host-agent runtime`：只保留为迁移期对照面与 regression oracle，不再是长期产品方向
- display / paper-facing asset packaging：明确排除在本线之外

## 1. 分类规则

每一项能力只允许落到下面三类之一：

1. 应迁入 `Hermes` substrate 的通用 runtime 能力
2. 暂时保留为 controlled research backend 的能力
3. 后续可进一步吸收或替换的能力

promotion 规则固定为：

- 没有 repo-tracked contract、代码入口、测试 proof surface，不得把能力声称为“已迁出”
- 不允许通过 hidden fallback、silent downgrade、synthetic truth rewrite 来伪造迁移完成
- 任何能力迁出 `MedDeepScientist` 前，都必须先在 `MedAutoScience` / `Hermes` 拓扑里获得明确 owner、artifact surface 与 fail-closed gate semantics

## 2. A 类：应迁入 Hermes substrate 的通用 runtime 能力

| 能力 | 当前 proof surface | 为什么属于 substrate | 当前 repo-side 动作 |
| --- | --- | --- | --- |
| backend registry / backend selection / fail-closed contract | `src/med_autoscience/runtime_backend.py`、`tests/test_runtime_backend.py` | 这是 controller-facing substrate contract，不应继续由单一 research backend 名称充当 authority | 已冻结为 backend-generic contract，默认 outer substrate owner 已切到 `Hermes` |
| runtime layout / runtime handle / runtime binding metadata | `src/med_autoscience/runtime_protocol/layout.py`、`src/med_autoscience/runtime_protocol/study_runtime.py`、`tests/test_runtime_protocol_layout.py`、`tests/test_runtime_protocol_study_runtime.py` | `program_id / study_id / quest_id / active_run_id` 与 `runtime_binding.yaml` 属于 substrate-level durable surface | 已写入 `runtime_backend_id / runtime_engine_id / research_backend_id / research_engine_id` |
| quest session / live-runtime inspection / transport seam | `src/med_autoscience/controllers/study_runtime_transport.py`、`src/med_autoscience/runtime_transport/hermes.py`、`tests/test_runtime_transport_hermes.py` | 这些是 outer runtime 调 backend 的标准动作，不应由 `MedDeepScientist` 名称直接支配 | 已通过 `Hermes` adapter 暴露 controller-facing contract |
| outer-loop wakeup / runtime watch / study runtime status loop | `src/med_autoscience/controllers/study_runtime_router.py`、`src/med_autoscience/controllers/study_outer_loop.py`、`src/med_autoscience/controllers/runtime_watch.py` | 这是 gateway/substrate 的控制闭环，不是 research backend 的自治真相 | 已要求全链只认 backend-generic contract |
| runtime durable surface normalization | `docs/runtime/runtime_handle_and_durable_surface_contract.md`、`docs/runtime/runtime_backend_interface_contract.md`、`tests/test_runtime_contract_docs.py` | durable surface 是产品主线 truth，不应继续挂在单一 backend 品牌名下 | 当前 repo-side 已冻结 Hermes-backed outer runtime wording |

## 3. B 类：暂时保留为 controlled research backend 的能力

| 能力 | 当前 proof surface | 为什么暂留在 backend |
| --- | --- | --- |
| quest inner-loop / daemon turn worker / bash session execution | `src/med_autoscience/runtime_transport/med_deepscientist.py`、`tests/test_runtime_transport_med_deepscientist.py` | 当前真实长时运行仍发生在 research runtime 内部，repo 内没有更高置信度替代物 |
| runtime-owned startup subset / quest-local snapshot echo | `docs/runtime/study_runtime_orchestration.md`、`src/med_autoscience/controllers/study_runtime_startup.py` | 仍然依赖 quest runtime 对启动投影的 durable persistence 与 roundtrip |
| quest-local logs / memory / config / paper worktree execution | `docs/references/workspace_architecture.md`、`src/med_autoscience/runtime_transport/med_deepscientist.py` | 这些仍绑定当前 research backend 的真实执行面与 worktree layout |
| typed quest completion / interaction artifact writer | `artifact_complete_quest(...)`、`artifact_interact(...)`、相关 controller tests | 目前仍通过 backend 生成 quest-owned interaction / completion durable state |

## 4. C 类：后续可进一步吸收或替换的能力

| 能力 | 当前 proof surface | 后续方向 |
| --- | --- | --- |
| startup-context patch / baseline attach metadata | `update_quest_startup_context(...)`、`requested_baseline_ref` roundtrip tests | 先保持 backend contract，可在 Hermes substrate 获得更稳定 owner 后再上收 |
| pending-user-interaction relay / approval mediation | `study_runtime_decision.py`、`study_outer_loop.py` | 当前仍需读 quest artifact；后续可向 outer substrate 的统一 interaction bridge 收敛 |
| runtime-owned memory / review-followup / manuscript-edit side effects | `MedDeepScientist` external runtime truth、`docs/program/external_runtime_dependency_gate.md` | 这些能力要么迁入更通用 substrate，要么被更受控的上层产品替换 |

## 5. 验证面

这张解构地图当前至少由下面这些 surface 共同约束：

- `tests/test_runtime_backend.py`
- `tests/test_runtime_transport_hermes.py`
- `tests/test_runtime_protocol_layout.py`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_study_runtime_router.py`
- `docs/runtime/runtime_backend_interface_contract.md`
- `docs/program/hermes_backend_continuation_board.md`

## 6. 真实 blocker

当前仍然不能把 `MedDeepScientist` 写成“已完全退场”，因为下面这些 blocker 仍在：

1. external `Hermes` runtime repo / workspace / daemon truth 还不在当前仓内
2. `MedDeepScientist` controlled fork 与 `behavior_equivalence_gate` 仍是外部 gate
3. external workspace / paper truth gap / human-required interaction 仍未清除
4. physical migration 仍需等待 external runtime / workspace / human gate 真正放行
