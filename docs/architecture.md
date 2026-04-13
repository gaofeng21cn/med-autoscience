# 架构概览

## 主链路

仓库的能力表达遵循 `policy -> controller -> overlay -> adapter` 主链路，避免旁路把临时状态升级为真相。关键运行语义以 contract 形式固化在 repo-tracked 文档与代码里，再由 controller 负责执行与审计。

当前 runtime 拓扑固定为：

- `MedAutoScience`：唯一研究入口、research gateway、study/workspace/outer-loop authority owner
- repo-side future outer-runtime seam：负责承接 backend-generic runtime contract、runtime handle 与 durable surface 的边界
- `MedDeepScientist`：controlled research backend，保留当前仍需由 research runtime 承担的 backend execution 能力

旧 `Codex-default host-agent runtime` 当前承担迁移期对照面与回归参考角色。

## 当前执行链路真相（family 默认）

- `MedAutoScience` 是 gateway / authority / outer-loop owner，不直接打模型。
- 当前底层执行链路固定为：`med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist -> MedDeepScientist CodexRunner -> codex exec autonomous agent loop`。
- family 默认 concrete executor 是 `codex_cli_autonomous`；默认 model / reasoning 继承本机 Codex 默认（`inherit_local_codex_default`）。
- `chat-only executor` 在 contract 上是 forbidden（`chat_completion_only_executor_forbidden = true`）。
- `Hermes-native` 只有 full agent loop 才算（`hermes_native_requires_full_agent_loop = true`）。
- 同一个 executor-adapter contract 上还显式挂了 `hermes_native_proof` opt-in lane：
  - 只有 caller 显式请求 `executor_kind = hermes_native_proof` 时才会启用
  - pass-through 到 `MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation`
  - 默认 model / reasoning 同样继承本机 Hermes 默认配置，而不是 repo-local pin
  - 它当前只作为 full-agent-loop proof lane，不构成 family 默认执行器替换

## 入口与控制面

- 默认正式入口：`CLI`
- 支持协议层：`MCP`
- 内部控制面：`controller`

入口只描述 Agent 进入 runtime 的方式，不改变 repo-tracked 主线的 `Auto-only` 定义。

## 入口 taxonomy 与 OPL handoff

当前需要明确区分三层入口：

- `operator entry`
  - 给人类操作同事使用的 workspace 准备、调试、检查和治理入口
- `agent entry`
  - 给 `Codex`、Claude Code、OpenClaw 等 host-agent 使用的 `CLI` / `MCP`
- `product entry`
  - 给最终用户直接进入的产品入口

当前真实状态是：前两层已存在，第三层还没有成熟落地；但 repo-tracked 轻量 `product-entry shell` 已经把“启动 / 下任务 / 看进度”的当前产品操作面收出来了。

目标中的 domain 级链路应是：

`User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`

与 `OPL` 的家族级衔接应是：

`User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`

`OPL -> Med Auto Science` 的最小 handoff envelope 至少包括：

- `target_domain_id`
- `task_intent`
- `entry_mode`
- `workspace_locator`
- `runtime_session_contract`
- `return_surface_contract`

在这层公共 envelope 之上，医学研究域继续补充 `study_id`、`journal_target`、`evidence_boundary` 等 domain payload。

## OPL family orchestration contracts 吸收方向

OPL 顶层将冻结 5 类 family contracts：

- family event envelope
- family checkpoint lineage
- family action graph
- family human gate
- family product-entry manifest v2

对 MAS 来说，本轮优先吸收 runtime-oriented 那一半：`family event envelope`、`family checkpoint lineage`、`family human gate`。
它们将进入 `study_runtime_status`、`runtime_watch`、`controller_decisions/latest.json` 的主线 contract 与 durable surface 语义，约束运行事件、恢复链路与人审门控的统一定义。
`family product-entry manifest v2` 作为 family discovery companion 使用，辅助 product-entry shell / handoff 的对齐与发现，不改变 MAS 的运行底座所有权。

MAS 仍保持 domain-owned durable truth；运行底座与执行器边界继续分层，吸收 family contracts 不等于把 `OPL` 写成 runtime owner，也不构成跨仓 runtime core ingest 的既成事实。

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

## 目标中的 Hermes-Agent 与当前 seam 工作逻辑

当前在“上游 `Hermes-Agent` 目标 + repo-side seam”这条过渡态下，整个平台应按下面这条主链理解：

`问题定义 -> startup boundary -> repo-side outer-runtime seam -> publication gate -> study completion sync`

展开后，逻辑上是：

1. 人类或 Agent 把疾病问题、数据边界、目标期刊、终点定义、证据要求送入 `MedAutoScience`。
2. `MedAutoScience` 先在 study / workspace 层收紧 `study charter`、`startup boundary`、journal shortlist、reporting contract 与 evidence package，而不是直接放任 runtime 自己开跑。
3. 只有在启动边界明确、数据准备度和报告逻辑过线后，`MedAutoScience` 才把 quest 绑定到 future outer-runtime seam 所描述的托管运行边界。
4. 当前 repo-side seam 持有外层 runtime substrate 的 handle、binding 和 durable-surface contract，负责把运行句柄、transport contract、watch surface、pause / stop / resume / relaunch 这些外层语义稳定下来；真实执行仍通过受控 backend 完成。
5. `MedDeepScientist` 只负责当前仍属于 research backend 的 inner research execution，例如 quest 内部代码执行、paper worktree、daemon worker、bash session 与 quest-local runtime state。
6. `MedAutoScience` 的 outer-loop 再持续读取 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json`、`controller_decisions/latest.json`，决定继续、暂停、重启、停止还是进入 completion sync。

这套机制把研究推进拆成一串 fail-closed gate，让系统在证据不足、边界不清、publication hygiene 不过线时诚实阻断。
它追求的是一步步逼近 SCI-ready 投稿态，并把研究治理保持在主链上。

## 为什么这不是逻辑降级

相对只依赖 `MedDeepScientist` 的版本，逻辑上不是降级，而是把原来混在一起的 authority 重新分层：

- `MedAutoScience` 负责研究入口、study/workspace authority、journal / reporting / publication judgment。
- 上游 `Hermes-Agent` 是目标 outer runtime substrate owner；当前仓内只是先冻结了对应 seam、managed runtime handle 与 backend-generic execution contract。
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

## Runtime substrate 与 research executor 的分层

当前这条迁移线统一采用：

- `Hermes-Agent` 管长期在线 runtime substrate / orchestration
- `MedAutoScience` 管研究入口、authority、outer-loop judgment
- `MedDeepScientist` 管当前仍保留的 research executor / backend execution

这意味着“接入 Hermes”不等于“每个研究动作都必须由 Hermes 自己重新执行”。

在当前阶段，只要 backend contract 没变，inner-loop execution 仍可以继续复用受控 backend 里已经工作的执行生态，例如：

- backend 内部 agent/tool routing
- `Codex` 与其技能生态
- 受控 bash / code execution / paper worktree side effects

后续如果要继续解构 `MedDeepScientist`，正确顺序也不是先强制换脑，而是：

1. 先让 `Hermes-Agent` 稳定持有 session / run / watch / recovery / scheduling
2. 再把研究执行里的某一类动作通过显式 contract 迁到新的 executor adapter
3. 只有当新的 executor route 拿到等价 proof 时，才允许替换旧 backend path

因此，这条线当前追求的是“runtime substrate owner 切换”，不是“单步执行器立刻单一化”。

## 当前还不能诚实宣称的事

- 当前 `med_autoscience.runtime_transport.hermes` 已不再是 consumer-only seam；它已经是一个 profile/runtime-bound real adapter，会先绑定 external `Hermes-Agent` runtime 证据并 fail-closed，再把底层 quest create / pause / resume / control 委托给 controlled `MedDeepScientist` stable transport。
- 所以如果宿主机还没有 external `Hermes-Agent` runtime，本仓“用上 Hermes”成立的是 topology / contract / durable surface / outer-loop semantics 与 adapter-level runtime gate 的复用，不是“已经装好了一个独立上游 `Hermes-Agent` host 并能脱离 backend 单独托管”。
- 这也是当前真实 external blocker：本仓已经能做到 substrate-bound 检测、恢复请求、升级告警与医生可读汇报，但还没有完成真实 study soak / recovery proof，因此仍不能把 `MedDeepScientist` 整体故障表述成“独立 `Hermes-Agent` 宿主已完整接管执行真相”。

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
