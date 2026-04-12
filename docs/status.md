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
- `init-workspace` 现在会优先跟随 `ops/medautoscience/config.env` 中实际生效的 `MED_AUTOSCIENCE_PROFILE`，并允许通过显式 `--hermes-agent-repo-root / --hermes-home-root` 对 legacy workspace 的 active profile 原位补齐 Hermes-era contract 字段，而不是只在旁边新写一个 `.local.toml`。
- `2026-04-12` 已在真实 workspace `dm-cvd-mortality-risk` 的 `002-dm-china-us-mortality-attribution` 上拿到一条完整 F3 证据链：`ensure-study-runtime` 把 quest 从 `waiting_for_user` 拉回 `running` 并拿到 `active_run_id = run-b5ed4887`；随后 `watch --apply --ensure-study-runtimes` 与两次短周期 `watch --loop` 连续刷新了 `runtime_watch/latest.json`、`runtime_supervision/latest.json` 和 `study-progress`。
- 同日继续在同一 study 上完成了一次真实续跑 proof：再次执行 `ensure-study-runtime` 与短周期 `watch --loop` 后，`002-dm-china-us-mortality-attribution` 已重新回到 live managed runtime，`study-progress` 暴露的当前监督入口变为 `browser_url = http://127.0.0.1:20999`、`active_run_id = run-bed9deed`，`runtime_supervision/latest.json` 也已明确写成 `health_status = live`。
- 同日又拿到一条 workspace-level 常驻监管 proof：对 legacy `dm-cvd-mortality-risk` workspace 重跑 `init-workspace` 后，controller 在不加 `--force` 的前提下安全升级了 `_shared.sh`、`watch-runtime`、`install-watch-runtime-service`；随后 launchd `watch-runtime` service 成功常驻在线，`001-dm-cvd-mortality-risk` 从 `managed_runtime_supervision_gap` 恢复为 `runtime_blocked`，`002-dm-china-us-mortality-attribution` 恢复为 `publication_supervision`，两者的 `supervisor_tick_audit.status` 均回到 `fresh`。
- 同日继续对真实 workspace `NF-PitNET` 完成了一条 F4 workspace compatibility proof：`init-workspace` 已把 active `nfpitnet.workspace.toml` 原位升级到 Hermes-era profile，并补齐 `watch-runtime-service-runner / install-watch-runtime-service / watch-runtime-service-status / uninstall-watch-runtime-service`；随后 `doctor` 已转为 `external_runtime_contract.ready = true`，workspace-local `med-deepscientist` daemon 也已重新拉起，`watch --apply --ensure-study-runtimes` 成功写出新的 `runtime_supervision/latest.json` 与 `runtime_watch/latest.json`。
- 同日又收口了一条 legacy service upgrade gap：`NF-PitNET` 的 `_shared.sh` 仍停在“直接调用裸 `uv`”的旧骨架时，launchd `watch-runtime` service 会稳定报 `exit 127`；repo-side `init-workspace` 升级判定现已补齐这类 bare-`uv` legacy 入口，重新执行 `init-workspace` 并安装 service 后，`ai.medautoscience.nfpitnet.watch-runtime` 已恢复常驻在线。
- 同日继续收口了一条 host-env compatibility gap：`med-deepscientist` launcher `ds.js` 在 launchd 最小 `PATH` 下会因 `#!/usr/bin/env node` 报 `env: node: No such file or directory`；repo-side `init-workspace` 现在会把 `MED_AUTOSCIENCE_NODE_BIN` 合并进 workspace `ops/medautoscience/config.env`，升级 `_shared.sh / install-watch-runtime-service`，并让 `runtime_transport.med_deepscientist` 显式消费同一份 Node contract。对真实 `DM` / `NF` workspace 回灌并重装 service 后，两边 launchd supervisor 都已显式持有 `MED_AUTOSCIENCE_UV_BIN`、`MED_AUTOSCIENCE_RSCRIPT_BIN` 与 `MED_AUTOSCIENCE_NODE_BIN`。
- 上述 `NF-PitNET` proof 之后，`002-early-residual-risk`、`003-endocrine-burden-followup`、`004-invasive-architecture` 已不再因为 `hermes adapter binding requires hermes_agent_repo_root` fail-closed；当前阻塞已回落为各自的 study truth：
  - `002-early-residual-risk`：study completion contract 漂移已修正，当前只剩 publication gate 未放行
  - `003-endocrine-burden-followup`：`Rscript` / `node` host gap 已在真实 workspace 收口；`2026-04-12` fresh `ensure-study-runtime` 已不再报 launcher contract 失败，而是前移到 `quest_parked_on_unchanged_finalize_state` 与题名页/投稿声明最终元数据等待用户决策
  - `004-invasive-architecture`：已重新进入 live managed runtime；`2026-04-12` fresh `study-progress` 暴露 `browser_url = http://127.0.0.1:21001`、`active_run_id = run-bc987174`，当前阻塞回落为 publication surface / submission package truth

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
- 同日对 `002-dm-china-us-mortality-attribution` 的后续续跑也已证明这不是一次性恢复：再次 `ensure-study-runtime` 后，当前 live `active_run_id` 已更新到 `run-bed9deed`，DM workspace 的 launchd supervisor service 继续保持 `supervisor_tick_audit.status = fresh`。
- 同日对同一 workspace 追加验证 `ops/medautoscience/bin/install-watch-runtime-service` 后，launchd service 已稳定持有 `MED_AUTOSCIENCE_UV_BIN`、`MED_AUTOSCIENCE_RSCRIPT_BIN` 与 `MED_AUTOSCIENCE_NODE_BIN` 并持续刷新 supervisor tick；因此当前真实 blocker 不再是“MAS 外环没有常驻入口”或 “launcher 在最小 PATH 下起不来”，而是各个 study 的诚实内容/决策阻塞。
- `001-dm-cvd-mortality-risk` 已通过 `study.yaml.manual_finish` 正式转成 `manual_finishing / compatibility_guard_only`；它仍保留 publication surface blocker，但不再被投影成默认应自动续跑的活跃 runtime blocker。
- `002-dm-china-us-mortality-attribution` 的 current fresh truth 也已重新收口：历史上的 live `run-bed9deed` recovery proof 继续保留为 F3 成立证据，但 `2026-04-12` fresh supervisor tick 现在把它投影为 `quest_marked_running_but_no_live_session`。当前 `ensure_managed_daemon(...)` 对 DM runtime 已返回 `healthy=true / identity_match=true / url=http://127.0.0.1:20999`，因此剩余 gap 已从 host/env 兼容问题前移到 study-local recovery / publication surface，而不是 Hermes adapter 或 node launcher contract。
- `002-early-residual-risk` 的 completion evidence 路径漂移也已在真实 workspace 收口：`study_completion_contract.ready` 现已回到 `true`，剩余阻塞不再是 contract 缺件，而是 publication gate 仍未放行。
- `003-endocrine-burden-followup` 的 fresh truth 也已从 host blocker 前移：`analysis_bundle.ready=true` 与 Node contract 修复后，`last_launch_report.json` 不再出现 `env: node: No such file or directory`，当前阻塞回落为 publication gate / 用户最终元数据决策。
- `004-invasive-architecture` 已通过 `ensure-study-runtime --allow-stopped-relaunch` 加短周期 `watch --loop` 回到 live managed runtime；当前 `study-progress` 已暴露 `browser_url = http://127.0.0.1:21001` 与 `active_run_id = run-bc987174`，说明 rerun/relaunch 决策点已经跨过。
- 如果其他宿主机尚无 external `Hermes-Agent` runtime，本仓当前 adapter 会 fail-closed：可以检测掉线、请求恢复、升级告警与输出人话进度，但不能伪造成“独立 `Hermes-Agent` host 已脱离 `MedDeepScientist` 完整接管执行”。
- 维护 workspace canonical literature / reference-context contract，不让 quest-local literature surface 重新退回 authority root。
- 对当前开发宿主，external runtime dependency gate 已通过，F2 real adapter 与至少一条 F3 real study recovery/progress proof 也都已成立；当前 honest next step 已转为 `F4 / blocker 收口`，而不是回去继续做 seam-only 包装。
- 即便如此，当前仍不做 physical migration 或 cross-repo rewrite：研究执行依旧由 controlled `MedDeepScientist` backend 承担，其他宿主机与其他 workspace 仍可能因 external gate 或 human gate fail-closed。
- 医学展示 / 论文配图资产化是独立 owner line；不得与主线 runtime / gateway 迁移混写。
- `OPL -> Med Auto Science` handoff 与 lightweight product entry 目前只冻结到架构和合同语义；在 external gate 清除前，不得把它们写成已落地的独立产品前台。

## 下一阶段

1. 按 `docs/program/upstream_hermes_agent_fast_cutover_board.md` 从 `F3 real study soak / recovery proof` 进入 `F4 blocker 收口`：DM 与 NF 的 workspace/runtime host compatibility gap（`uv` / `Rscript` / `node`）已清掉，后续主线只继续收口各篇 active study 的 publication / completion / rerun truth。
2. 保持 display 线与 runtime 主线严格分离，避免资产化支线反向污染主线 truth。
3. 即使 F3 证据已成立，也不提前宣称 runtime owner 已完全切换完成；完整 upstream ownership、backend engine 替换与多宿主稳定性仍需继续验证。
4. 在不突破 external gate 的前提下，继续把 `Med Auto Science Product Entry` 与 `OPL` handoff 所需合同写清，但不偷跑到 physical migration 或 product overclaim。
