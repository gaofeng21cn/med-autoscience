# Merge And Cutover Gates

这份文档定义两件事：

- 什么时候当前 repo-side tranche 可以吸收到 `main`
- 什么时候一个正在运行中的医学项目可以平滑迁到更大的 integration harness / cutover surface

另见：[`../runtime-governance/external_runtime_dependency_gate.md`](../runtime-governance/external_runtime_dependency_gate.md)。该文档现在是 explicit executor/proof diagnostic / historical backend / explicit archive import / parity audit gate，用来保留旧 cutover blocker 语义；它不再表示 MAS 默认运行被 external runtime 阻塞。

它不讨论“是否值得做 `med-deepscientist`”；这个决策已经做完。这里讨论的是何时可以安全收口。

## 两类门

要分清两个不同的门：

1. `merge gate`
   - 判断当前 repo-side tranche 能不能进 `main`
2. `runtime cutover gate`
   - 判断真实运行面能不能把 study 切到更大的 harness / cutover surface

`merge gate` 通过，不自动意味着 `runtime cutover gate` 通过。

## 2026-04-11 历史位置与 2026-05-11 当前读法

截至 `2026-04-11`，当时已知事实按下面这条顺序理解：

1. `P0` / `P1` / `P2` 与 `real-study relaunch and verify` 已 absorbed 到 `main`
2. `integration harness activation package` 已 absorbed 到 `main`
3. `external runtime dependency gate` 已作为 canonical blocker package 固定下来
4. 当时 broader cutover 的正式停车终态是 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`
5. 当前 repo-side 仍允许继续推进一个更窄的 same-repo tranche：
   - `Hermes backend continuation board`
   - `Hermes backend activation package`
   - `MedDeepScientist deconstruction map`
6. 这条 same-repo tranche 的目标不是 reopening cutover，而是把“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam”压成可吸收的 repo-side truth

2026-05-11 当前读法：MAS monolith closeout 已经完成默认运行、默认诊断、默认进度面和默认质量入口的收回；旧 external blocker 只能用于 explicit executor/proof diagnostic、historical backend audit、explicit archive import 或 parity gate。新的 Full online cutover 必须按 OPL provider-backed stage-led framework 判断，不能沿用 2026-04-11 旧 Hermes 默认路线停车口径作为 MAS 默认状态。

## Merge Gate

当前 repo-side tranche 只有在下面条件全部满足时，才应该并回 `main`。本节保留旧 tranche 的合并纪律作为 provenance；当前 MAS/OPL 工作以 `scripts/verify.sh`、machine-readable contracts、single Active Truth plan 和对应 focused tests 为准。

### 1. 当前 write-set 与 tranche 边界一致

必须满足：

- 当前 tranche 只落在 repo-tracked runtime / gateway / contract 迁移允许的 docs / tests / preflight / code 范围
- 不把 `end-to-end study harness`、cutover、cross-repo write、external runtime truth 偷渡进来
- 不把 display / paper-facing asset packaging 独立线混入 runtime 主线

### 2. worktree 模式成立

必须满足：

- 主仓根目录保持在 `main`
- 当前 tracked 实现发生在独立 `.worktrees/...` worktree
- root checkout 继续只承接 control-plane / absorb 动作

### 3. 当前 baseline proof 通过

至少要有：

- `tests/test_runtime_backend.py`
- `tests/test_runtime_transport_hermes.py`
- `tests/test_runtime_protocol_layout.py`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_study_runtime_router.py`
- `tests/test_dev_preflight_contract.py`
- `make test-meta`

如果当前改动同时触及 activation wording / preflight surface，继续补跑：

- `tests/test_dev_preflight.py`
- `tests/test_domain_health_diagnostic.py`
- `tests/test_study_delivery_sync.py`

纯 Markdown wording / integration-harness 文案变更只需要人工/Agent documentation review，不再通过 pytest 锁定具体措辞。
- `tests/test_publication_gate.py`

### 4. wording / artifact / preflight audit 一致

必须满足：

- repo-tracked docs 对当前 absorbed position、active tranche、真实 blocker 的表述一致
- preflight contract 已收口当前 runtime mainline surface
- `runtime_binding.yaml` 的 substrate / research-backend 分层语义与代码、文档、测试一致
- manual-test package 与 reports 可追溯到 fresh evidence

## Runtime Cutover Gate

正在运行的项目只有在下面条件全部满足时，才建议平滑切到更大的 harness / cutover surface。

### 1. controlled fork 已固定

必须满足：

- profile 的 explicit archive import reference controlled backend repo root 已经指向受控的 `med-deepscientist`
- `MEDICAL_FORK_MANIFEST.json` 能说明当前 fork 身份
- 需要的历史补丁已经在 fork 或 `med-autoscience` 中显式落盘

### 2. behavior equivalence gate 放行

必须满足：

- `ops/med-deepscientist/behavior_equivalence_gate.yaml` 存在
- `phase_25_ready` 为 `true`
- `critical_overrides` 中列出的 site-packages 级补丁已经迁出或被替换

只要这道门没过，就不应该宣称运行面已经完成切换。

### 3. OPL provider / explicit executor-proof diagnostic 已就位

至少要确认：

- OPL provider truth 或显式 `hermes_agent` executor/proof diagnostic repo / workspace / daemon evidence 已被独立验证
- 当前 repo-side provider / Hermes legacy contract 与 external runtime 实际部署语义一致
- 不再需要把 repo 内兼容 wiring 误写成 external runtime cutover 既成事实

### 4. workspace contract 全绿

至少要确认：

- `doctor`
- `bootstrap`
- `overlay-status`
- `backend-audit`

这些命令对目标 workspace 都是通过状态。

### 5. 单项目热身验证通过

对每个准备切换的真实项目，至少要做一次受控热身：

1. 选一个非最关键、可回滚的 study
2. 运行 `ensure-study-runtime`
3. 验证 quest create / resume / pause 正常
4. 验证 `publication_gate`、`data_asset_gate`、`figure_loop_guard`、`medical_publication_surface` 都能正常落盘
5. 验证 paper bundle / submission minimal / user message queue 不丢状态

### 6. 旧 quest 可以继续读，新 quest 按新边界写

平滑迁移的最低要求不是“所有旧 quest 立即重写”，而是：

- 旧 quest 仍能被新协议层读取
- 新产生的运行状态只再通过新协议边界写入
- 不再向 adapter 或 site-packages 私补丁回流

## 当前判断

以 `2026-04-11` 这个时间点看：

- repo-side `merge gate` 对 activation baseline 与 external blocker package 来说都已经满足
- 当前新 tranche 的 `merge gate`，取决于“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam”这批 code / docs / tests / preflight 是否 fresh green
- `runtime cutover gate` 还没有完成
- 当前 external blocker 的 repo-side canonical package 见 `../runtime-governance/external_runtime_dependency_gate.md`

以 `2026-05-23` 当前状态看：

- MAS 默认路径不再等待 external MDS、旧 MDS WebUI 或 retired Hermes default-provider runtime cutover。
- OPL provider / Temporal / explicit executor-proof readiness 只决定 OPL-hosted Full online path 或显式 proof lane，不决定 MAS direct skill path 是否可读、可诊断或可推进。
- 真实论文推进仍以 MAS owner receipts、artifact delta、gate replay、AI reviewer judgment、human gate 或 stop-loss 为准。

原因是：

- repo-side contract 已完成 authority / delivery / real-study 的收口；当前默认 hosted path 由 OPL/Temporal 承担持久在线 stage runtime、attempt、queue、wakeup、retry/dead-letter、resume 和 worker residency。
- `MedDeepScientist` 只保留 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。
- `runtime cutover gate` 现在按 OPL provider-backed stage-led runtime、MAS owner receipt / typed blocker、no-forbidden-write proof 和真实 paper-line evidence 判断；旧 controlled fork / behavior equivalence / Hermes runtime 条件只作为历史迁移背景或显式 parity/proof lane 参考。

## 当前建议

### 当前 MAS/OPL tranche 何时算 closeout 成立

下面这些条件全部满足时，当前 MAS/OPL docs/runtime tranche 才算可以 absorb：

1. 当前 runtime / docs / contracts / source / tests 的 owner 边界一致。
2. repo-native verification 通过；触及 machine-readable contract、action metadata、schema 或 runtime semantics 时追加 `make test-meta`。
3. `git diff --check` clean
4. single Active Truth plan 已把 closed item、仍开放的功能/结构删除门和测试/证据 tail 分开表达。
5. 不把 OPL provider completion、descriptor ready、refs-only ledger record 或 conformance proof 写成 MAS paper closure、publication-ready、artifact mutation authorization 或 domain-ready。

### 何时才可以继续往 hosted production evidence 推进

只有当下面这些条件一起满足时，才建议继续：

- OPL provider / Temporal attempt、queue、retry/dead-letter、resume 和 worker residency 证据独立就位。
- MAS sidecar/export/dispatch 只交 body-free refs、owner route、typed blocker、no-forbidden-write proof 和 safe action receipt，不写 study truth、publication eval、controller decisions、paper body、memory body 或 artifact body。
- 至少一条真实 paper line 通过 OPL provider -> MAS owner chain 产出 owner receipt、progress delta、gate replay、human gate、stop-loss 或 stable typed blocker。
- Direct MAS path 与 OPL-hosted path 消费同一 MAS-owned stage/controller/quality/artifact surface。
- MDS/DeepScientist/Hermes/local provider 只作为 explicit provenance、parity oracle、executor/proof lane 或 diagnostic reference，不回到默认 runtime owner。
