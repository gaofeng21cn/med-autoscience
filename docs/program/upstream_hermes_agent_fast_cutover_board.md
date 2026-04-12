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
- 对真实外部环境执行检查后，已确认 external Hermes repo、launcher、managed `.venv`、`~/.hermes/state.db`、logs/sessions root 均存在
- 当前 honest blocker 已缩窄为两项外部环境真问题：provider/model 未配置、gateway service 未加载
- 因此下一棒不能诚实进入 F2 real adapter cutover，除非先由外部环境把这两个 blocker 清掉；repo-side 不应伪装成“已经完成 Hermes 接管”

## 默认验证

- `scripts/verify.sh meta`
- 必要的 runtime / topology / transport / outer-loop regression
- 真实 external `Hermes-Agent` runtime proof
- 至少一条真实 study soak / recovery proof

## 长线 Codex 提示词

> 你现在负责 `MedAutoScience` 的 `upstream Hermes-Agent fast cutover` 主线。先完整读取并遵守：`AGENTS.md`、`README.md`、`docs/project.md`、`docs/status.md`、`docs/architecture.md`、`docs/program/external_runtime_dependency_gate.md`、`docs/program/med_deepscientist_deconstruction_map.md`、`docs/runtime/agent_runtime_interface.md`、`docs/program/upstream_hermes_agent_fast_cutover_board.md`。你的目标不是继续打磨 repo-side consumer-only seam，也不是直接完全解构 `MedDeepScientist`。你的目标是以最快速度把真实 external `Hermes-Agent` 接成 outer runtime substrate owner，同时继续把 `MedDeepScientist` 保持为 controlled research backend，并用真实 study / soak / recovery proof 证明这条主线已经成立。display / paper-figure 资产化独立线绝对禁止混入。你必须按 board 顺序自行推进：先拿到 external Hermes runtime 真证据，再把 repo-side seam 切成真实 adapter，再做真实 study soak / recovery proof，再重新收口 blocker。你可以自己写 activation package、docs、tests、contracts，并在每个 honest tranche 完成后直接 absorb 到 `main`、提交、push、继续下一棒；不要因为完成一个小 tranche 就停车。只有遇到真实硬 blocker 才允许停下，例如：必须由用户提供外部安装/凭证/运行环境、必须由用户决定 study/workspace 资源、或继续前进会造成 truth drift。禁止做的事：把 repo-side seam 继续写成已完成 Hermes 集成、把 `MedDeepScientist` 直接写成已退场、提前做 physical monorepo migration、把 display 线混入本线。
