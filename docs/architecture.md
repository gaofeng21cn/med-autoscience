# 架构概览

## 主链路

仓库的能力表达遵循 `policy -> controller -> overlay -> adapter` 主链路，避免旁路把临时状态升级为真相。关键运行语义以 contract 形式固化在 repo-tracked 文档与代码里，再由 controller 负责执行与审计。

当前 runtime 拓扑固定为：

- `MedAutoScience`：唯一研究入口、research gateway、study/workspace/outer-loop authority owner
- `Hermes`：外层 runtime substrate owner，负责 backend-generic runtime contract、runtime handle 与 durable surface
- `MedDeepScientist`：controlled research backend，保留当前仍需由 research runtime 承担的 backend execution 能力

旧 `Codex-default host-agent runtime` 不再是长期产品 runtime 深化方向，只保留为迁移期对照面。

## 入口与控制面

- 默认正式入口：`CLI`
- 支持协议层：`MCP`
- 内部控制面：`controller`

入口只描述 Agent 进入 runtime 的方式，不改变 repo-tracked 主线的 `Auto-only` 定义。

## 权威与 durable surface

可审计真相必须落在 repo-tracked contract 与明确的 durable surface。关键身份与运行面包括：

- `program_id`、`study_id`、`quest_id`、`active_run_id`
- `study_runtime_status`、`runtime_watch`
- `publication_eval/latest.json`
- `runtime_escalation_record.json`
- `controller_decisions/latest.json`

具体 contract 以运行层文档为准，例如：

- `runtime/agent_runtime_interface.md`
- `program/med_deepscientist_deconstruction_map.md`
- `runtime/runtime_handle_and_durable_surface_contract.md`
- `runtime/study_runtime_control_surface.md`
- `runtime/delivery_plane_contract_map.md`

## Hermes 整合后的工作逻辑

当前整合 `Hermes` 之后，整个平台应按下面这条主链理解，而不是按函数名或某个 daemon 名称理解：

`问题定义 -> startup boundary -> Hermes managed runtime -> publication gate -> study completion sync`

展开后，逻辑上是：

1. 人类或 Agent 把疾病问题、数据边界、目标期刊、终点定义、证据要求送入 `MedAutoScience`。
2. `MedAutoScience` 先在 study / workspace 层收紧 `study charter`、`startup boundary`、journal shortlist、reporting contract 与 evidence package，而不是直接放任 runtime 自己开跑。
3. 只有在启动边界明确、数据准备度和报告逻辑过线后，`MedAutoScience` 才把 quest 绑定到 `Hermes` 托管的 managed runtime。
4. `Hermes` 持有外层 runtime substrate 的 handle、binding 和 durable surface，负责把运行句柄、transport contract、watch surface、pause / stop / resume / relaunch 这些外层语义稳定下来。
5. `MedDeepScientist` 只负责当前仍属于 research backend 的 inner research execution，例如 quest 内部代码执行、paper worktree、daemon worker、bash session 与 quest-local runtime state。
6. `MedAutoScience` 的 outer-loop 再持续读取 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json`、`controller_decisions/latest.json`，决定继续、暂停、重启、停止还是进入 completion sync。

这套机制不是“保证必然发表”的机器。
它做的是把研究推进拆成一串 fail-closed gate，让系统在证据不足、边界不清、publication hygiene 不过线时诚实阻断，而不是假装已经形成论文。
因此它追求的是一步步逼近 SCI-ready 投稿态，而不是跳过研究治理直接赌最后一跳。

## 为什么这不是逻辑降级

相对只依赖 `MedDeepScientist` 的版本，逻辑上不是降级，而是把原来混在一起的 authority 重新分层：

- `MedAutoScience` 负责研究入口、study/workspace authority、journal / reporting / publication judgment。
- `Hermes` 负责 outer runtime substrate、managed runtime handle 与 backend-generic execution contract。
- `MedDeepScientist` 负责当前仍未拆出的 inner-loop execution。

在 repo-side 已完成的范围内，功能没有因为接入 `Hermes` 而退回“只能跑一个 backend”或“只能靠对话记状态”。
相反，outer-loop / inner-loop coordination 变得更清楚：outer loop 负责研究治理与 go / stop judgment，inner loop 负责受控执行，不再把两类 authority 混写成一个 runtime body。

## 当前 outer / inner 交互怎么保证

当前这套协作不是靠口头约定，而是靠几条已经落盘的 fail-closed contract：

- 只有当 `runtime_liveness_audit.status == live`、`runtime_audit.worker_running == true`、`active_run_id != null` 同时成立时，`MedAutoScience` 才允许把托管运行视为 truly live；否则 `runtime_supervision/latest.json` 必须落到 `recovering / degraded / escalated`。
- `runtime_watch` 周期扫描 quest controller surface，`runtime_supervision/latest.json` 把掉线、恢复请求、连续失败、人工介入需求写成 study-owned durable truth。
- 一旦 `MedDeepScientist` 表面还显示 running，但 live worker 消失，MAS 可以通过 backend-generic contract 调 `ensure_study_runtime`、pause、resume、relaunch 这些路径做受控干预；不会靠 hidden fallback 或口头记忆假装恢复成功。
- 这套“及时干预”本身也受外环监管约束：只要 `supervisor_tick_audit` 变成 `missing / stale / invalid`，`study_progress` 就必须把当前状态投影成 `managed_runtime_supervision_gap`，明确说明 MAS 已不能保证及时发现掉线和自动恢复。
- 阶段性成果的人话汇报当前由 `study_progress` 只读组合 `runtime_supervision/latest.json`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`bash_exec summary`、`details projection`，而不是直接抓 inner runtime 原始日志拼装一个黑盒摘要。

## 当前还不能诚实宣称的事

- 当前 `med_autoscience.runtime_transport.hermes` 仍是 consumer-only outer substrate seam，底层 quest create / pause / resume / control 还是经由 controlled `MedDeepScientist` stable transport 完成。
- 所以如果宿主机还没有 external `Hermes` runtime，本仓“用上 Hermes”成立的是 topology / contract / durable surface / outer-loop semantics 的复用，不是“已经装好了一个独立 Hermes host 并能脱离 backend 单独托管”。
- 这也是当前真实 external blocker：本仓已经能检测、恢复请求、升级告警、医生可读汇报，但还不能把 `MedDeepScientist` 整体故障表述成“独立 Hermes 宿主已完整接管执行真相”。

## 现在比原来更好解决了什么

当前相比只靠 `MedDeepScientist` 作为默认 runtime truth 的形态，更好地解决了几类老问题：

- outer-loop / inner-loop coordination：不再把是否继续、是否暂停、是否 completion 的判断继续藏在 backend 内环里。
- study truth / quest truth coordination：study-owned judgment 和 quest-owned runtime state 现在有明确 durable surface 分工。
- backend replacement coordination：controller / outer-loop / transport 不再默认把某一个 backend 品牌名写死成唯一真相。
- publication progression coordination：系统不是只看 quest 是否还在跑，而是看它是否沿着 startup boundary、publication gate、completion sync 这条链收敛。

## 能力族与程序材料

- 能力族/专题面收口到 `docs/capabilities/`（例如 medical display 系列）。
- tranche、freeze、hardening、cleanup、intake 等程序材料收口到 `docs/program/`。
- 背景、定位、审计与非活跃参考收口到 `docs/references/`。
