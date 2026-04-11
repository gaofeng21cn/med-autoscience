# Merge And Cutover Gates

这份文档定义两件事：

- 什么时候当前 repo-side tranche 可以吸收到 `main`
- 什么时候一个正在运行中的医学项目可以平滑迁到更大的 integration harness / cutover surface

另见：[`./external_runtime_dependency_gate.md`](./external_runtime_dependency_gate.md)，用于把当前 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB` 收口成 repo-side canonical blocker package。

它不讨论“是否值得做 `med-deepscientist`”；这个决策已经做完。这里讨论的是何时可以安全收口。

## 两类门

要分清两个不同的门：

1. `merge gate`
   - 判断当前 repo-side tranche 能不能进 `main`
2. `runtime cutover gate`
   - 判断真实运行面能不能把 study 切到更大的 harness / cutover surface

`merge gate` 通过，不自动意味着 `runtime cutover gate` 通过。

## 2026-04-11 / 当前位置

截至 `2026-04-11`，当前已知事实应按下面这条顺序理解：

1. `P0` / `P1` / `P2` 与 `real-study relaunch and verify` 已 absorbed 到 `main`
2. `integration harness activation package` 已 absorbed 到 `main`
3. `external runtime dependency gate` 已作为 canonical blocker package 固定下来
4. 当前 broader cutover 的正式停车终态继续是 `EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB`
5. 当前 repo-side 仍允许继续推进一个更窄的 same-repo tranche：
   - `Hermes backend continuation board`
   - `Hermes backend activation package`
   - `MedDeepScientist deconstruction map`
6. 这条 same-repo tranche 的目标不是 reopening cutover，而是把“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam”压成可吸收的 repo-side truth

## Merge Gate

当前 repo-side tranche 只有在下面条件全部满足时，才应该并回 `main`：

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
- `tests/test_runtime_contract_docs.py`
- `tests/test_dev_preflight_contract.py`
- `tests/test_integration_harness_activation_package.py`
- `make test-meta`

如果当前改动同时触及 activation wording / preflight surface，继续补跑：

- `tests/test_dev_preflight.py`
- `tests/test_runtime_watch.py`
- `tests/test_study_delivery_sync.py`
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

- profile 中的 `med_deepscientist_repo_root` 已经指向受控的 `med-deepscientist`
- `MEDICAL_FORK_MANIFEST.json` 能说明当前 fork 身份
- 需要的历史补丁已经在 fork 或 `med-autoscience` 中显式落盘

### 2. behavior equivalence gate 放行

必须满足：

- `ops/med-deepscientist/behavior_equivalence_gate.yaml` 存在
- `phase_25_ready` 为 `true`
- `critical_overrides` 中列出的 site-packages 级补丁已经迁出或被替换

只要这道门没过，就不应该宣称运行面已经完成切换。

### 3. external `Hermes` runtime truth 已就位

至少要确认：

- external `Hermes` runtime repo / workspace / daemon truth 已被独立验证
- 当前 repo-side `Hermes` outer substrate contract 与 external runtime 实际部署语义一致
- 不再需要把 repo 内兼容 wiring 误写成 external runtime cutover 既成事实

### 4. workspace contract 全绿

至少要确认：

- `doctor`
- `bootstrap`
- `overlay-status`
- `med-deepscientist-upgrade-check`

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
- 当前 external blocker 的 repo-side canonical package 见 `./external_runtime_dependency_gate.md`

原因是：

- repo-side contract 已完成 authority / delivery / real-study 的收口，并已把默认 outer-runtime seam label 切到 `hermes` 以指向上游目标
- repo-side 仍可继续收紧 `runtime backend interface` contract，并把 `MedDeepScientist` 解构为 controlled research backend
- 但真实运行面的切换，仍取决于 controlled fork 固定、behavior equivalence gate 放行，以及 external `Hermes` runtime / workspace surface

## 当前建议

### 当前 tranche 何时算 closeout 成立

下面这些条件全部满足时，当前“上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam” tranche 才算可以 absorb：

1. 当前 runtime mainline docs / tests / preflight / code 一致
2. targeted regression 与 meta verification 通过
3. `git diff --check` clean
4. external blocker 仍被诚实保留，没有被 repo-side wording 偷删

### 何时才可以继续往更大 cutover 推进

只有当下面这些条件一起满足时，才建议继续：

- controlled fork 固定
- `behavior_equivalence_gate.yaml` 放行
- external `Hermes` runtime truth 已独立就位
- 至少 1 个真实项目完成 create / resume / pause + controller 落盘 + paper 交付热身
- external workspace-side blocker 不再要求 repo 继续越权 widening
