# DeepScientist Latest-Update Learning Protocol

这份协议定义维护者说“学习一下 `DeepScientist` 的最新更新”时，`MAS` / `MDS` 应默认执行什么。

它不是泛泛调研请求，也不是要求把 upstream 整体同步进来。它表示启动一轮受控的 learning-and-landing intake：先审计 upstream 最新变化，再把真正值得学的能力切成可验证 lane，落到 `MAS` / `MDS` 各自正确的 owner surface。

## 触发短语

以下表达都按本协议处理：

- “学习一下 `DeepScientist` 的最新更新”
- “看看 `DeepScientist` 最近更新，有什么值得吸收”
- “按上次那套学习一下 `DeepScientist`”
- “一周后再学习 `DeepScientist` upstream”

默认含义：

1. 立即进入执行型任务，不停在只读建议。
2. 先读当前 repo truth，再 fetch upstream。
3. 分类、落地、验证、吸收回 `main`、清理 worktree。
4. 需要同时考虑 `MDS` backend/runtime 层和 `MAS` owner/contract/template 层。

## 固定阅读入口

每轮开始前必须读：

- `MAS`: `docs/program/deepscientist_continuous_learning_policy.md`
- `MAS`: `docs/program/med_deepscientist_continuous_learning_plan.md`
- `MAS`: `docs/program/med_deepscientist_method_learning_disciplines.md`
- `MAS`: `docs/program/med_deepscientist_upstream_source_provenance.md`
- `MDS`: `docs/upstream_intake.md`
- `MDS`: `docs/status.md`

这些文档决定 owner 边界。它们优先于临时记忆和上一轮对话总结。

## 固定执行流程

### 1. Fresh upstream audit

This is the `fresh upstream audit` step.

在 `med-deepscientist` 中：

```bash
git fetch upstream --prune
git rev-list --left-right --count main...upstream/main
git log --reverse --oneline main..upstream/main
```

同时看 upstream README / docs / skills / runtime surface 中被强调的新能力。判断对象是 capability，不是 commit 数量。

### 2. Decision matrix

每个候选变化必须归入一类：

- `adopt_code_slice`: 直接对 `MDS` runtime/backend 有价值，且能用 focused regression 验证。
- `adopt_contract`: 不搬代码，把行为吸收到 `MAS` runtime / controller / eval / publication contract。
- `adopt_template`: 学 stage packet、SOP、skill discipline，落到医学 overlay template 或 stage packet。
- `watch_only`: 有启发，但现在只记录，不改变主线。
- `reject`: provider / UI / marketing / product-shell 扩面，或会削弱医学 owner truth。

分类时必须写清：

- upstream range 或 commit
- learned capability
- owner surface
- decision
- verification target

### 3. Parallel worktrees

如果有多个互不冲突 lane，默认并行开 worktree：

- `MDS runtime/backend lane`: 改 `med-deepscientist`，写源码和 fork-local tests。
- `MAS contract/template lane`: 改 `med-autoscience` docs / templates / meta tests。
- `MAS runtime-consumer lane`: 只有当 MAS 侧需要消费新 runtime surface 时才开。

每条 lane 完成后必须吸收回对应 repo 的 `main` 并清理临时 worktree / branch。

### 4. Verification gate

声称落地前至少要有：

- MDS focused pytest 或 `scripts/verify.sh` 对应切片。
- MAS 对应 meta tests；涉及 runtime/docs contract 时至少跑相关 tests，必要时跑 `make test-meta`。
- `git diff --check`。
- 最终 root checkout 状态核对。

如果改了 daemon API、quest layout、built-in MCP、prompt/skill 列表或 baseline/artifact contract，验证必须覆盖 MDS 与 MAS 两侧。

### 5. Audit record

每轮必须留下 repo-tracked intake record：

- `MAS`: `docs/program/deepscientist_learning_intake_YYYY_MM_DD.md`
- `MDS`: 如果吸收代码 slice，同时更新 `docs/upstream_intake_round_YYYY_MM_DD.md` 或对应 fork audit surface。

记录必须说明没有吸收的内容，尤其是 provider / UI / marketing 变化为什么不进入主线。

## 默认落地边界

优先落地：

- retry / interrupt / resume / takeover / mailbox 这类长期自治能力
- artifact / baseline / workspace truth 刷新能力
- stage packet / SOP / route-back / failed-path learning
- operator visibility / durable checkpoint / recovery proof

默认不落地：

- upstream provider 扩面
- connector 商业入口
- UI shell / modal / settings / marketing 文案
- 会让 `MDS` 重新成为医学质量 owner 的改动

## 完成定义

一轮 “学习 `DeepScientist` 最新更新” 完成，必须同时满足：

1. upstream delta 已 fresh 审计。
2. 候选变化已按 decision matrix 分类。
3. 选中的 code / contract / template slice 已落地。
4. 相关 tests 已通过。
5. 分支和 worktree 已清理。
6. `main` 上有可追溯 commit。
7. 如果用户明确要求推送，两个相关 repo 都已 push。

如果 upstream 没有值得吸收的变化，也要留下简短 intake record，说明 range、分类和 `watch_only` / `reject` 原因。
