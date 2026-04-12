# Upstream Hermes-Agent Fast Cutover Board

状态锚点：`2026-04-12`

## 文档目的

这份文档用于冻结 `MedAutoScience` 当前**最快可落地**的理想形态切换路径。

重点不是“理论上最纯粹的最终架构”，而是：

- 哪条路能最快把产品 runtime 真正切到上游 `Hermes-Agent`
- 同时不破坏当前已经可运行的医学自动研究主线

## 一句话结论

对 `MedAutoScience` 来说，最快的诚实路径不是“先完全解构 `MedDeepScientist`”，而是：

- 先让上游 `Hermes-Agent` 真正接管 outer runtime substrate
- 同时保留 `MedDeepScientist` 作为 controlled research backend
- 等 outer runtime ownership、长跑稳定性、外部证据都成立后，再继续解构 backend

## 目标形态

本线完成后，目标应变成：

- `MedAutoScience`：唯一研究入口、study/workspace authority owner、publication gate / outer-loop judgment owner
- upstream `Hermes-Agent`：outer runtime substrate owner、session / run / watch / recovery / scheduling / interruption owner
- `MedDeepScientist`：controlled research backend，暂时继续承担研究执行 engine

## 为什么不先完整解构 MedDeepScientist

因为那不是最快路径。

如果现在直接要求一边真实接上游 `Hermes-Agent`，一边把 `MedDeepScientist` 里仍在工作的研究执行能力全部拆出来，结果大概率是：

- runtime cutover 迟迟落不下真实证据
- 长跑稳定性下降
- 文档和实现重新漂移

因此，这条 fast cutover board 固定采用：

- 第一阶段：`Hermes-Agent` 真正接 outer runtime
- 第二阶段：在此基础上继续解构 backend

## 成功条件

只有同时满足下面几项，才可以把这条线写成完成：

1. external `Hermes-Agent` runtime 真实存在。
2. 当前 `consumer-only seam` 变成真实 adapter。
3. `MedDeepScientist` 仍被诚实保留为 controlled research backend。
4. 至少一条真实 study / harness 路径证明：session / run / watch / recovery 归 `Hermes-Agent`，研究执行仍可经由受控 backend 完成。
5. display / paper-figure 资产化独立线完全不被污染。

## 明确排除范围

本线不做：

- display / paper-facing assetization 独立线
- physical monorepo migration
- cross-repo 大重构
- 把 `MedDeepScientist` 一次性完全拆空
- 在 external gate 未清除前伪造“已 fully cutover”

## 固定阶段顺序

### F1. External Hermes runtime 真实落地

先拿到真实外部运行证据：

- 安装方式
- runtime root / profile
- process / gateway evidence
- 与当前 repo-side contract 的连接证据

### F2. Repo-side seam 变成真实 outer-runtime adapter

把当前 repo-side seam 从 consumer-only 收紧成真实 adapter：

- `ensure_study_runtime`
- pause / resume / stop / relaunch
- runtime watch / supervision
- session / run identity binding

### F3. 真实 study soak / recovery proof

至少对真实 study 路径做长跑与恢复证明：

- 掉线检测
- 恢复请求
- runtime escalation
- publication gate 与 controller decision
- study-progress 人话汇报

### F4. 缩窄 external blocker

在完成上面三步后，重新收口：

- 哪些 blocker 已从 repo-side 变成已解决
- 哪些 blocker 仍然需要外部 workspace / human gate
- 哪些才是下一轮 backend deconstruction board 的正式输入

## 当前落点（2026-04-12）

- F1 的 repo-side 证据面已落成可验证 contract：`hermes-runtime-check`、`inspect_hermes_runtime_contract(...)`、`doctor.external_runtime_contract`
- 对当前开发宿主执行检查后，已确认 external Hermes repo、launcher、managed `.venv`、`~/.hermes/state.db`、logs/sessions root、provider 配置与 launchd gateway service 均已就绪
- `med_autoscience.runtime_transport.hermes` 已从 consumer-only seam 收紧为 profile/runtime-bound real adapter：会先绑定 external Hermes runtime evidence，fail-closed 校验 readiness，再把 quest control 委托给 controlled backend
- `2026-04-12` 已对真实 workspace `dm-cvd-mortality-risk` 的 `002-dm-china-us-mortality-attribution` 跑出一条完整 F3 证据链：
  - `ensure-study-runtime` 把 quest 从 `waiting_for_user` 拉回 `running`
  - live run 句柄变成 `active_run_id = run-b5ed4887`
  - `autonomous_runtime_notice` 暴露 `browser_url = http://127.0.0.1:20999` 与 `quest_session_api_url`
  - `watch --runtime-root ... --profile ... --ensure-study-runtimes --apply` 刷新了 `runtime_watch/latest.json` 与 `runtime_supervision/latest.json`
  - `watch --loop --interval-seconds 1 --max-ticks 2` 又连续写出两次新的 supervisor tick，证明这不是一次性手动补写
  - `study-progress` 已从 `managed_runtime_supervision_gap` 恢复为 `publication_supervision`
- 同日对同一 workspace 又完成了一条 F4 收口 proof：
  - legacy workspace 重新执行 `init-workspace` 时，controller 已能在不加 `--force` 的前提下，自动升级 `_shared.sh`、`watch-runtime`、`install-watch-runtime-service` 这些 service-critical managed entry scripts
  - `init-workspace` 现在还会优先跟随 `ops/medautoscience/config.env` 中实际生效的 `MED_AUTOSCIENCE_PROFILE`，并可用显式 `--hermes-agent-repo-root / --hermes-home-root` 原位升级 active profile
  - `ops/medautoscience/bin/install-watch-runtime-service` 安装出的 launchd service 已显式携带 `MED_AUTOSCIENCE_UV_BIN`
  - service 常驻后，`001-dm-cvd-mortality-risk` 先从 `managed_runtime_supervision_gap` 恢复为 `runtime_blocked`，随后在写入正式 `manual_finish / compatibility_guard_only` contract 后投影为 `manual_finishing`
  - service 常驻后，`002-dm-china-us-mortality-attribution` 从 `managed_runtime_supervision_gap` 恢复为 `publication_supervision`
  - 同日继续续跑后，`002-dm-china-us-mortality-attribution` 又重新回到 live managed runtime，当前 `active_run_id = run-bed9deed`
- 同日又在真实 workspace `NF-PitNET` 上拿到一条 workspace compatibility proof：
  - legacy `nfpitnet.workspace.toml` 已被原位补齐 Hermes binding，不再停在 `hermes adapter binding requires hermes_agent_repo_root`
  - `watch-runtime-service-runner / install-watch-runtime-service / watch-runtime-service-status / uninstall-watch-runtime-service` 已补齐到 workspace 本地入口
  - `doctor` 已转为 `external_runtime_contract.ready = true`
  - 重新拉起 workspace-local `med-deepscientist` daemon 并执行 `watch --apply --ensure-study-runtimes` 后，`runtime_supervision/latest.json` 与 `runtime_watch/latest.json` 已重新刷新
  - `002-early-residual-risk`、`003-endocrine-burden-followup`、`004-invasive-architecture` 现在都能进入诚实的 study-progress 投影，而不是在 adapter binding 上 fail-closed
  - 同日又补上了一条 legacy host-service fix：repo-side `init-workspace` 现在会升级仍在直接调用裸 `uv` 的 `_shared.sh`；对 `NF-PitNET` 重跑升级并重新安装 launchd service 后，`ai.medautoscience.nfpitnet.watch-runtime` 已从 `exit 127` 恢复为常驻在线
  - 同日继续补上了一条更深一层的 host-env fix：`med-deepscientist` launcher `ds.js` 在 launchd 最小 `PATH` 下会因为 `#!/usr/bin/env node` 失败；repo-side `init-workspace`、workspace `config.env` 与 `runtime_transport.med_deepscientist` 现在都已显式消费 `MED_AUTOSCIENCE_NODE_BIN`。对真实 DM / NF workspace 回灌并重装 service 后，两边 launchd supervisor 都已显式持有 `MED_AUTOSCIENCE_UV_BIN / MED_AUTOSCIENCE_RSCRIPT_BIN / MED_AUTOSCIENCE_NODE_BIN`
  - 之后 `002-early-residual-risk` 的 completion contract 漂移也已被修正，不再卡在缺失 final evidence path；当前 blocker 已回落为 publication gate
  - 之后 `003-endocrine-burden-followup` 又拿到一条新的 fresh proof：`ensure-study-runtime` 不再报 `env: node: No such file or directory`，当前 fresh blocker 已从 launcher host gap 前移到 `quest_parked_on_unchanged_finalize_state` 与题名页/投稿声明最终元数据等待用户决策
  - 之后 `004-invasive-architecture` 已通过 `ensure-study-runtime --allow-stopped-relaunch` 加 `watch --loop` 回到 live managed runtime，当前 `active_run_id = run-bc987174`
- 因此当前开发宿主上的 honest next step 已从 `F3 / real study soak / recovery proof` 转为 `F4 / blocker 收口`
- 但 repo-side 仍不能伪装成“已经完成 Hermes 接管”：研究执行仍经由 controlled backend，当前 blocker 已明确回落为各 study 自身 truth，而不是 repo-side adapter gap
  - `001-dm-cvd-mortality-risk`：manual finishing / compatibility-only + publication surface blocker
  - `002-dm-china-us-mortality-attribution`：historical live recovery proof 已成立，但 `2026-04-12` fresh truth 已转为 `quest_marked_running_but_no_live_session`；当前 `ensure_managed_daemon(...)` 仍返回 `healthy=true / identity_match=true / url=http://127.0.0.1:20999`，说明 blocker 已前移到 study-local recovery / publication surface，而不是 Hermes adapter 或 node host contract
  - `002-early-residual-risk`：publication gate / scientific anchor blocker
  - `003-endocrine-burden-followup`：publication surface blocker + 最终元数据用户决策；`Rscript / node` host gap 已清掉
  - `004-invasive-architecture`：publication surface / submission package blocker（runtime 已重新 live）

## 默认验证

- `scripts/verify.sh meta`
- 必要的 runtime / topology / transport / outer-loop regression
- 真实 external `Hermes-Agent` runtime proof
- 至少一条真实 study soak / recovery proof

## 长线 Codex 提示词

> 你现在负责 `MedAutoScience` 的 `upstream Hermes-Agent fast cutover` 主线。先完整读取并遵守：`AGENTS.md`、`README.md`、`docs/project.md`、`docs/status.md`、`docs/architecture.md`、`docs/program/external_runtime_dependency_gate.md`、`docs/program/med_deepscientist_deconstruction_map.md`、`docs/runtime/agent_runtime_interface.md`、`docs/program/upstream_hermes_agent_fast_cutover_board.md`。你的目标不是继续打磨 repo-side consumer-only seam，也不是直接完全解构 `MedDeepScientist`。你的目标是以最快速度把真实 external `Hermes-Agent` 接成 outer runtime substrate owner，同时继续把 `MedDeepScientist` 保持为 controlled research backend，并用真实 study / soak / recovery proof 证明这条主线已经成立。display / paper-figure 资产化独立线绝对禁止混入。你必须按 board 顺序自行推进：先拿到 external Hermes runtime 真证据，再把 repo-side seam 切成真实 adapter，再做真实 study soak / recovery proof，再重新收口 blocker。你可以自己写 activation package、docs、tests、contracts，并在每个 honest tranche 完成后直接 absorb 到 `main`、提交、push、继续下一棒；不要因为完成一个小 tranche 就停车。只有遇到真实硬 blocker 才允许停下，例如：必须由用户提供外部安装/凭证/运行环境、必须由用户决定 study/workspace 资源、或继续前进会造成 truth drift。禁止做的事：把 repo-side seam 继续写成已完成 Hermes 集成、把 `MedDeepScientist` 直接写成已退场、提前做 physical monorepo migration、把 display 线混入本线。
