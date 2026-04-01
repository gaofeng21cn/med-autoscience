# Merge And Cutover Gates

这份文档定义两件事：

- 什么时候当前这条 `MedDeepScientist` 迁移主线可以并回 `main`
- 什么时候一个正在运行中的医学项目可以平滑迁到新框架

它不讨论“是否值得做 `med-deepscientist`”；这个决策已经做完。这里讨论的是何时可以安全收口。

## 两类门

要分清两个不同的门：

1. `merge gate`
   - 判断代码分支能不能进 `main`
2. `runtime cutover gate`
   - 判断现网项目能不能把真实运行面切到这套新边界

`merge gate` 通过，不自动意味着 `runtime cutover gate` 通过。

## Merge Gate

`med-autoscience` 这条迁移 worktree 只有在下面条件全部满足时，才应该并回 `main`：

### 1. 控制路径不再依赖 adapter 真相

必须满足：

- production controller 不再直接 import `adapters.deepscientist.*`
- runtime 文件真相全部落在 `runtime_protocol`
- daemon transport 真相全部落在 `runtime_transport`
- `adapters/deepscientist/*` 只剩 compatibility shim

### 2. worktree 模式完全成立

必须满足：

- 主仓根目录保持在 `main`
- 所有未合并开发只发生在 `.worktree/...`
- `python_environment_contract` 在 worktree 下能正确解析主仓 `.venv`

### 3. 回归锁住新边界

至少要有：

- 针对 `runtime_protocol.quest_state`
- 针对 `runtime_protocol.paper_artifacts`
- 针对 `runtime_protocol.user_message`
- 针对 `runtime_transport.med_deepscientist`
- 针对“production code 不再 import `adapters.deepscientist`”的架构测试

### 4. 全量测试稳定

必须在迁移 worktree 中跑过：

```bash
PYTHONPATH=src pytest -q
```

并且通过。

### 5. intake 流程已固化

必须满足：

- `med-autoscience` 有稳定的上游 intake 规范
- `med-deepscientist` 也有对应规范
- 后续吸收 upstream 不依赖会话记忆，而依赖文档化流程

## Runtime Cutover Gate

正在运行的项目只有在下面条件全部满足时，才建议平滑切到新框架。

### 1. controlled fork 已经固定

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

### 3. workspace contract 全绿

至少要确认：

- `doctor`
- `bootstrap`
- `overlay-status`
- `med-deepscientist-upgrade-check`

这些命令对目标 workspace 都是通过状态。

### 4. 单项目热身验证通过

对每个准备切换的真实项目，至少要做一次受控热身：

1. 选一个非最关键、可回滚的 study
2. 运行 `ensure-study-runtime`
3. 验证 quest create / resume / pause 正常
4. 验证 `publication_gate`、`data_asset_gate`、`figure_loop_guard`、`medical_publication_surface` 都能正常落盘
5. 验证 paper bundle / submission minimal / user message queue 不丢状态

### 5. 旧 quest 可以继续读，新 quest 按新边界写

平滑迁移的最低要求不是“所有旧 quest 立即重写”，而是：

- 旧 quest 仍能被新协议层读取
- 新产生的运行状态只再通过新协议边界写入
- 不再向 adapter 或 site-packages 私补丁回流

## 当前判断

以 `2026-03-31` 这个时间点看：

- `merge gate` 已经非常接近完成
- `runtime cutover gate` 还没有完成

原因是：

- 代码结构上，`med-autoscience` 已基本完成 `controller -> runtime_protocol/runtime_transport` 收口
- 但真实项目是否能切，仍取决于 controlled fork 固定、behavior equivalence gate 放行，以及至少一个真实 workspace 的热身验证

## 我的建议

### 何时可以并回 main

如果接下来两项完成，我会建议尽快并回 `main`：

1. 再做一次基于真实 workspace 的 smoke 验证
2. 确认没有隐藏的 CLI / automation 还依赖旧 adapter 路径

这两项通过后，这条 worktree 就不该继续长期漂着。

### 何时可以迁真实项目

我会把“可以平滑迁”定义成下面这个标准：

- controlled fork 固定
- `behavior_equivalence_gate.yaml` 放行
- 至少 1 个真实项目完成 create/resume/pause + controller 落盘 + paper 交付热身
- 连续一段观察期内没有回退到 site-packages 私补丁

只有这几项全满足，我才会建议把正在跑的项目正式切到新框架。
