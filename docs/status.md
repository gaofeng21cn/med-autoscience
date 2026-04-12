# 当前状态

**更新时间：2026-04-12**

## 当前角色与边界

- 仓库角色：医学 `Research Ops` 的 domain gateway 与 `Domain Harness OS`
- 正式入口矩阵：默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`
- 当前产品主线：`Auto-only`
- 当前研究入口边界：`MedAutoScience` 是唯一研究入口；上游 `Hermes-Agent` 是目标 outer runtime substrate；当前真实执行仍落在受控 `MedDeepScientist` backend
- 当前入口真相：`operator entry` 与 `agent entry` 已存在；成熟的医学 `product entry` 仍未落地
- 当前协作模型：`Hermes-Agent` 负责产品级长期在线 runtime substrate / orchestration，`MedAutoScience` 负责 gateway / authority / outer-loop，`MedDeepScientist` 继续作为当前 research executor；单步执行器替换不是当前 tranche 的默认目标

## 当前基线（repo-verified）

- `P0 runtime native truth` 已完成，上游完成点为 `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a`。
- `P1 workspace canonical literature / knowledge truth` 已完成，workspace canonical literature、study reference context 与 quest materialization-only 边界已进入仓库主线。
- `P2 controlled cutover -> physical monorepo migration` 仍未完成；当前仓内已完成 repo-side real adapter cutover 与 future outer-runtime seam 清理，但这还不是上游 `Hermes-Agent` 已完成接管证明。

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
- `med_autoscience.runtime_transport.hermes` 已从 consumer-only alias 收紧为 profile/runtime-bound real adapter：先绑定 runtime home 下的 Hermes evidence，再对 external runtime readiness fail-closed，最后才委托 controlled `MedDeepScientist` backend 执行 quest control。
- `2026-04-12` 已在真实 workspace `dm-cvd-mortality-risk` 的 `002-dm-china-us-mortality-attribution` 上拿到一条完整 F3 证据链：`ensure-study-runtime` 把 quest 从 `waiting_for_user` 拉回 `running` 并拿到 `active_run_id = run-b5ed4887`；随后 `watch --apply --ensure-study-runtimes` 与两次短周期 `watch --loop` 连续刷新了 `runtime_watch/latest.json`、`runtime_supervision/latest.json` 和 `study-progress`。

## 长线目标（规划层）

- 让上游 `Hermes-Agent` 成为外层 runtime substrate owner。
- 让 `MedAutoScience` 继续保持唯一研究入口与 research gateway。
- 让 `MedDeepScientist` 从当前默认执行 substrate 收敛为受控 research backend，并逐步解构其中通用 runtime 能力。
- 在 external gate 真正清除前，不伪造“已完全 cutover”或“已完成 physical monorepo migration”。

## 当前真实 blocker 与独立支线

- 保持 `MedAutoScience` 对 `MedDeepScientist` native runtime truth 的消费不回退，不再让 controller 覆盖 quest-owned `runtime_events/*`。
- 保持 `runtime backend interface` 已冻结：`MedAutoScience` controller 只认 backend contract，不再把 `med-deepscientist` 模块名当作 managed runtime 判定真相。
- 保持上游 `Hermes-Agent` 作为目标 outer substrate owner 这条路线诚实成立，同时保留 external runtime repo / workspace / daemon truth 仍未进入本仓这一 blocker。
- `2026-04-12` 对真实外部环境运行 `doctor`、`hermes-runtime-check` 与 `hermes gateway status` 后已确认：`/Users/gaofeng/workspace/_external/hermes-agent`、其 `.venv` / launcher、`~/.hermes/state.db` 与 launchd gateway service 均已就绪；当前开发宿主上的 repo-side `F2 / real adapter cutover` 代码与回归也已落地。
- 同日对真实 study `002-dm-china-us-mortality-attribution` 运行 `ensure-study-runtime` 后，controller 已通过真实 Hermes adapter 把 quest 从 `waiting_for_user` 拉回 `running`，并通过 `autonomous_runtime_notice` 暴露 `browser_url = http://127.0.0.1:20999`、`quest_session_api_url` 与 `active_run_id = run-b5ed4887`。
- 同日对同一 runtime 运行 `watch --runtime-root ... --profile ... --ensure-study-runtimes --apply` 与 `watch --loop --interval-seconds 1 --max-ticks 2` 后，`runtime_watch/latest.json` 与 `runtime_supervision/latest.json` 已连续刷新，`study-progress` 也已从 `managed_runtime_supervision_gap` 恢复到 `publication_supervision`。
- 如果其他宿主机尚无 external `Hermes-Agent` runtime，本仓当前 adapter 会 fail-closed：可以检测掉线、请求恢复、升级告警与输出人话进度，但不能伪造成“独立 `Hermes-Agent` host 已脱离 `MedDeepScientist` 完整接管执行”。
- 维护 workspace canonical literature / reference-context contract，不让 quest-local literature surface 重新退回 authority root。
- 对当前开发宿主，external runtime dependency gate 已通过，F2 real adapter 与至少一条 F3 real study recovery/progress proof 也都已成立；当前 honest next step 已转为 `F4 / blocker 收口`，而不是回去继续做 seam-only 包装。
- 即便如此，当前仍不做 physical migration 或 cross-repo rewrite：研究执行依旧由 controlled `MedDeepScientist` backend 承担，其他宿主机与其他 workspace 仍可能因 external gate 或 human gate fail-closed。
- 医学展示 / 论文配图资产化是独立 owner line；不得与主线 runtime / gateway 迁移混写。
- `OPL -> Med Auto Science` handoff 与 lightweight product entry 目前只冻结到架构和合同语义；在 external gate 清除前，不得把它们写成已落地的独立产品前台。

## 下一阶段

1. 按 `docs/program/upstream_hermes_agent_fast_cutover_board.md` 从 `F3 real study soak / recovery proof` 进入 `F4 blocker 收口`：`001-dm-cvd-mortality-risk` 仍需显式 rerun 决策，`002-dm-china-us-mortality-attribution` 的 runtime owner gap 已清掉，当前 blocker 已回落到 publication surface / reporting contract。
2. 保持 display 线与 runtime 主线严格分离，避免资产化支线反向污染主线 truth。
3. 即使 F3 证据已成立，也不提前宣称 runtime owner 已完全切换完成；完整 upstream ownership、backend engine 替换与多宿主稳定性仍需继续验证。
4. 在不突破 external gate 的前提下，继续把 `Med Auto Science Product Entry` 与 `OPL` handoff 所需合同写清，但不偷跑到 physical migration 或 product overclaim。
