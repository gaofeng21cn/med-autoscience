# Integration Harness Activation Package

这份文档把 `real-study relaunch and verify` 已 absorbed 到 `main` 之后，`Phase 6 / Integration Harness And Cutover Readiness` 当前允许打开的 **最小 repo-tracked activation package** 固定下来。

状态更新：截至 `2026-04-10`，这条 activation package 已完成并 absorbed 到 `main`。当前 repo-side 正式停车终态是：

- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`

它不是：

- `end-to-end study harness` 已开启的声明
- `runtime cutover` 已放行的声明
- `behavior-equivalence` 已通过的声明
- 对 `med-deepscientist` 写入、cross-repo write、external workspace writer widening 的授权

## 1. 当前 absorbed 起点

截至 `2026-04-10`，当前已确认并 absorbed 到 `main` 的 committed position 为：

1. `P0 outer-loop durable decision loop` 已完成
2. `P1 formal stop semantics + rerun policy + canonical spec bridge` 已完成
3. `P2 delivery plane contract map and artifact-surface freeze` 已完成
4. `real-study relaunch and verify` 已在真实 anchor 完成验证并 absorbed 到 `main`

当前 authoritative repo 起点应拆成 tranche start baseline 与 absorbed closeout：

- tranche start baseline commit：`f5e909b0f6db64489f63aa70f6e1bfe38ec362a6`
- absorbed closeout commit：`70dc19fe4001b6eddda14e9b7a00e79a30d79ab1`
- real-study verification note：[`docs/real_study_relaunch_verification.md`](./real_study_relaunch_verification.md)

因此，这份文档当前承担的是“已完成 activation package 的 repo-tracked closeout truth”，而不是“尚未 absorb 的 active tranche 说明”。

此前 repo-side 的下一棒是：

- 把 `controller -> runtime -> eval -> delivery` chain 与 `cutover readiness` 收敛成稳定、repo-tracked、可审计的 activation package

而截至当前状态，这一棒已经完成并 absorbed。

## 2. 当前冻结的 controller-authorized chain

当前最小正式链路固定为：

```text
study_runtime_status / ensure_study_runtime
  -> launch_report
  -> runtime_escalation_record
  -> publication_eval
  -> study_outer_loop_tick
  -> study_decision_record
  -> runtime_watch
  -> publication_gate
  -> study_delivery_sync
```

### 2.1 Artifact / controller surface map

| 对象 | 当前 owner | 正式作用 | 当前 tranche 中的地位 |
| --- | --- | --- | --- |
| `launch_report` | runtime orchestration | durable 回显最近一次 runtime dispatch / daemon result | 作为 controller -> runtime handoff proof 起点 |
| `runtime_escalation_record` | runtime-owned event artifact | 表达 quest 已超出本地自治 envelope | outer-loop durable loop 的上游输入 |
| `publication_eval` | eval-owned verdict artifact | 表达 publishability verdict / gaps / recommended actions | outer-loop decision 的正式 eval 输入 |
| `study_decision_record` | controller-owned durable decision artifact | 把 escalation / eval 收口成 next controller action | current outer-loop authority 证明面 |
| `runtime_watch` | controller-owned poll/report shell | 聚合 controller reports 与 managed-study action | 当前 `runtime -> eval / delivery report surface` 的最小 integration shell |
| `publication_gate` | controller-owned delivery guard | 对 `paper/` 与 medical publication surface fail-closed | 当前 delivery guard baseline proof 面 |
| `study_delivery_sync` | controller-owned delivery materializer | 将 controller-authorized `paper/` package 投影到 `manuscript/` | 当前 delivery plane projection baseline proof 面 |

### 2.2 当前 stable bridge

当前链路的正式 repo-tracked bridge 继续由这些文档共同裁定：

- [`docs/study_runtime_orchestration.md`](./study_runtime_orchestration.md)
- [`docs/study_runtime_control_surface.md`](./study_runtime_control_surface.md)
- [`docs/outer_loop_wakeup_and_decision_loop.md`](./outer_loop_wakeup_and_decision_loop.md)
- [`docs/delivery_plane_contract_map.md`](./delivery_plane_contract_map.md)

本文件只负责补齐：

1. `real-study` absorbed 之后的下一棒 activation package
2. `runtime_watch -> publication_gate -> study_delivery_sync` 作为最小 `runtime-eval/delivery` baseline 的地位
3. `cutover readiness` 仍然受哪些 gate 约束
4. 哪些部分已经是 repo-side baseline，哪些仍明确依赖 external surface

## 3. 当前 tranche 真正打开的最小 baseline

当前允许打开、并且已具备 repo-native proof surface 的最小 baseline 是：

1. `runtime_watch`
2. `publication_gate`
3. `study_delivery_sync`
4. 这些 controller 与 `study_runtime_status / ensure_study_runtime / launch_report` 之间的文档化 handoff
5. 对上述 bridge 的 repo-native preflight / audit / regression

当前 tranche 的最小 proof surface 固定为：

- `tests/test_runtime_watch.py`
- `tests/test_study_delivery_sync.py`
- `tests/test_publication_gate.py`
- `tests/test_integration_harness_activation_package.py`
- `tests/test_dev_preflight_contract.py`
- `tests/test_dev_preflight.py`

其中：

- `runtime_watch` 继续只是 **poll/report shell**
- `publication_gate` 继续只消费 controller-authorized delivery source
- `study_delivery_sync` 继续只做 authority-preserving projection
- 当前不把 `runtime_watch` 升格成新的 authority root
- 当前不把 `manuscript/`、zip、mirror 反向抬升成 authority root

## 4. 当前仍明确关闭的面

下面这些面当前继续 fail-closed，不得被 activation package 偷渡打开：

1. `end-to-end study harness`
2. `runtime cutover`
3. `behavior-equivalence claim`
4. `med-deepscientist` 写入
5. cross-repo write
6. external workspace writer widening
7. `eval_hygiene` 本体与 broader downstream authority implementation

当前 tranche 的意义是：

- 先把 repo 内已经存在、已经被 P0/P1/P2 + real-study 验证的链路压成稳定 bridge
- 而不是假装更大的 harness / cutover 已经成熟

## 5. Cutover readiness 仍然需要的 gate

当前 `real-study relaunch` 已提供了重要前置证据，但它 **不是** `runtime cutover gate` 的替代品。

继续走到更大 cutover readiness 前，仍然至少需要：

1. controlled fork 已固定
2. external runtime `behavior_equivalence_gate` 放行
3. 至少一个真实 workspace 的受控热身验证持续稳定
4. external workspace-side paper truth gap 被独立处理，不再阻塞当前 repo-side baseline

相关 cutover 约束继续由：

- [`docs/merge_and_cutover_gates.md`](./merge_and_cutover_gates.md)

裁定。

## 6. 当前 residual risks

截至本轮，当前 residual risks 只允许被诚实表述为：

1. `integration harness` 还没有打开 `end-to-end study harness`
2. `runtime cutover` 仍受 external runtime surface 与 behavior-equivalence gate 约束
3. `DM001` 真实课题仍有 external workspace-side blocker：
   - `Methods` 结构不完整
   - `endpoint_provenance_note.md` 缺失
   - pending human interaction
4. `display-pack` 独立线仍然独立存在，当前 runtime 主线不得把它混入当前 tranche

## 7. 继续推进所需的 external surface

如果要从当前 baseline 再往前推进，真正需要 external surface 的部分是：

1. `med-deepscientist` controlled fork / runtime cutover gate
2. external workspace / quest paper writer
3. pending human interaction 的显式清除
4. 任何 cross-repo contract 扩大

因此，当前 repo 内的正确动作是：

1. 承认这条 activation package / baseline 已 absorb 到 `main`
2. 把后续更大推进诚实地停在 external dependency gate 前
3. 通过 [`docs/external_runtime_dependency_gate.md`](./external_runtime_dependency_gate.md) 把 blocker 固定为 repo-tracked canonical audit package
4. 不在 repo 内伪造新的 same-repo tranche 来代替 external readiness 清理
