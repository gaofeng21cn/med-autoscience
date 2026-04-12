# 当前状态

**更新时间：2026-04-12**

## 当前角色与边界

- 仓库角色：医学 `Research Ops` 的 domain gateway 与 `Domain Harness OS`
- 正式入口矩阵：默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`
- 当前产品主线：`Auto-only`
- 当前研究入口边界：`MedAutoScience` 是唯一研究入口；上游 `Hermes-Agent` 是目标 outer runtime substrate；当前真实执行仍落在受控 `MedDeepScientist` backend

## 当前基线（repo-verified）

- `P0 runtime native truth` 已完成，上游完成点为 `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a`。
- `P1 workspace canonical literature / knowledge truth` 已完成，workspace canonical literature、study reference context 与 quest materialization-only 边界已进入仓库主线。
- `P2 controlled cutover -> physical monorepo migration` 仍未完成；当前仓内完成的是 repo-side consumer-only 收敛与 future outer-runtime seam 清理，不是上游 `Hermes-Agent` 已接管。

## 当前 tranche

- 旧 `Codex-default host-agent runtime` 已明确退为迁移期对照面，不再作为长期产品方向。
- 当前 runtime / gateway / architecture 主线只推进上游 `Hermes-Agent` 目标 substrate、`MedAutoScience` gateway、`MedDeepScientist` controlled backend 这条迁移，不碰 display / paper-facing asset packaging 独立线。
- `runtime_binding.yaml`、`study_runtime_status`、`runtime_watch`、outer-loop controller action 已同步写入 future outer-runtime seam 与 `MedDeepScientist` research backend 的分层语义。
- `docs/program/med_deepscientist_deconstruction_map.md` 已冻结三类能力归属：迁入 `Hermes` substrate、暂留 backend、后续吸收/替换。
- `managed_runtime_transport` 已作为 repo-side controller / guard / publication stop surface 的通用 authority 名称落盘；`med_deepscientist_transport` 仅继续保留兼容别名。
- workspace onboarding 已把默认自动推进 wording 明确切到“上游 `Hermes-Agent` 目标 + repo-side managed runtime seam”，不再把 `med-deepscientist` 写成默认 outer runtime owner。
- `study_runtime_transport` 已接受 generic router shim 仅暴露 `managed_runtime_backend` 的收口形态；薄层 execution / outer-loop / topology 测试契约开始以 `managed_runtime_transport` 为主口径。
- `hermes-runtime-check` / `inspect_hermes_runtime_contract(...)` 已进入 repo-tracked contract surface，可结构化核对 external Hermes repo、launcher、`.venv`、`~/.hermes` state root、provider/model 配置与 gateway service 证据。
- `doctor` 与 workspace contract 已同步暴露 `external_runtime_contract`，不再只能靠人工口头描述“external runtime 可能缺什么”。

## 长线目标（规划层）

- 让上游 `Hermes-Agent` 成为外层 runtime substrate owner。
- 让 `MedAutoScience` 继续保持唯一研究入口与 research gateway。
- 让 `MedDeepScientist` 从当前默认执行 substrate 收敛为受控 research backend，并逐步解构其中通用 runtime 能力。
- 在 external gate 真正清除前，不伪造“已完全 cutover”或“已完成 physical monorepo migration”。

## 当前真实 blocker 与独立支线

- 保持 `MedAutoScience` 对 `MedDeepScientist` native runtime truth 的消费不回退，不再让 controller 覆盖 quest-owned `runtime_events/*`。
- 保持 `runtime backend interface` 已冻结：`MedAutoScience` controller 只认 backend contract，不再把 `med-deepscientist` 模块名当作 managed runtime 判定真相。
- 保持上游 `Hermes-Agent` 作为目标 outer substrate owner 这条路线诚实成立，同时保留 external runtime repo / workspace / daemon truth 仍未进入本仓这一 blocker。
- `2026-04-12` 对真实外部环境运行 `hermes-runtime-check` 后已确认：`/Users/gaofeng/workspace/_external/hermes-agent` 与 `~/.hermes/state.db` 存在，当前真实 blocker 已缩窄为 provider/model 未配置、gateway service 未加载，而不是 external repo 不存在。
- 如果宿主机尚无 external `Hermes-Agent` runtime，本仓当前仍只有 repo-side seam：可以检测掉线、请求恢复、升级告警与输出人话进度，但不能伪造成“独立 `Hermes-Agent` host 已脱离 `MedDeepScientist` 完整接管执行”。
- 维护 workspace canonical literature / reference-context contract，不让 quest-local literature surface 重新退回 authority root。
- `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB` 仍然成立；external runtime / workspace / human gate 未清除前，不做 physical migration 或 cross-repo rewrite。
- 医学展示 / 论文配图资产化是独立 owner line；不得与主线 runtime / gateway 迁移混写。

## 下一阶段

1. 按 `docs/program/upstream_hermes_agent_fast_cutover_board.md` 在 repo-side 继续推进真实 external `Hermes-Agent` 接入、future outer-runtime seam -> real adapter 切换、以及 backend-generic durable surface 与 cutover evidence 收口。
2. 保持 display 线与 runtime 主线严格分离，避免资产化支线反向污染主线 truth。
3. external gate 未清除前，只做 consumer-only convergence，不提前宣称 runtime owner 已切换完成。
