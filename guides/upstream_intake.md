# Upstream Intake Guide

这份文档定义 `med-deepscientist` 如何吸收 `DeepScientist` 上游更新，以及 `MedAutoScience` 如何对这类吸收做兼容审计。

它的目标不是“尽快同步 upstream”，而是把 upstream 变化收口成一条受控、可验证、可回滚的 intake 流程。

更高优先级的主线工作不是 intake 本身，而是把 `MedAutoScience -> MedDeepScientist` 的 runtime protocol、compatibility contract 和 adapter 退出路径收紧。

## 一句话版本

上游更新只能先进入 intake worktree，经过双层验证与 manifest 审计后，才允许进入 `med-deepscientist/main`。

看到 upstream 多一个 commit，不意味着要立刻逐个研究它干了什么。

## 为什么不能直接跟上游同步

`med-deepscientist` 的价值不只是“有一份 fork”，而是：

- 稳定执行真相
- 保留 `MedAutoScience` 当前依赖的 daemon API / quest / worktree 契约
- 明确拒绝 prompt 广告、未审 workflow 变化和不受控依赖漂移

因此，上游更新必须先回答三个问题：

1. 这是不是我们真的需要的变化？
2. 这会不会破坏当前 `MedAutoScience` 的协议假设？
3. 这次吸收是否留下了清晰的审计痕迹？

## Intake 原则

- 不直接在 `med-deepscientist/main` 上吸收上游更新
- 不直接把 upstream branch merge 进生产线
- 优先以 commit / PR 为单位做受控 `cherry-pick`
- 每次 intake 都必须在独立 worktree 中完成
- 每次 intake 都必须更新 fork 审计记录
- intake 是周期性、按价值触发的维护动作，不是持续主线
- 默认不逐 commit 跟踪 upstream；只有出现明确价值的变更集合时才发起 intake

## 主线优先级

在当前阶段，工程优先级应按以下顺序理解：

1. 让 `MedDeepScientist` 成为 `MedAutoScience` 的稳定默认 runtime
2. 收口 `runtime_protocol` / `runtime_transport` / controller 对 runtime 的契约
3. 去掉不必要的 adapter 与隐式 layout 依赖
4. 只在合适时机做有明确收益的 upstream intake

## Remote 命名

`med-deepscientist` 本身是受控 fork，因此 remote 语义要明确分工。对于普通非 fork 仓库，`origin/main` 仍然可以当作默认 upstream，并直接作为 `med-deepscientist-upgrade-check` 的 comparison ref；但在受控 fork 场景里，必须避免把 `origin/main` 当成真正的上游。

在 intake 流程里应保持以下 remote 约定：

- `origin` 指向 fork 自己的 GitHub 主仓，用于维护 `med-deepscientist/main` 的稳定线和 intake 合并点；
- `upstream` 指向原始的 `DeepScientist` 仓库，针对兼容审计（如 `med-deepscientist-upgrade-check`）和 intake 分叉准备的命令都应以 `upstream/main` 作为 comparison ref，确保不会误用 fork 的 `origin/main` 做上游引用。

## 允许吸收的更新类型

优先级最高：

- daemon / runtime bugfix
- document asset / file resolution 修复
- 明确的 deterministic correctness fix
- 不改变 daemon API shape 的稳定性修复

需要单独评审：

- quest/worktree/paper/result 目录布局变化
- daemon API 字段、payload、status shape 变化
- prompt / workflow 编排大改
- UI / Web App 变化
- 锁文件与依赖大规模更新

默认拒绝：

- 广告、导流、商业化 prompt 注入
- 未经证明必要的研究策略改写
- 会让 `MedAutoScience` 重新依赖隐式 `.ds` 细节的上游结构变化

## 标准 Intake 流程

### 1. 在 `med-deepscientist` 建 intake worktree

根目录保持在 `main`，实际 intake 工作只在 `.worktree/*` 中进行。

示例：

```bash
cd <med-deepscientist-root>
git fetch upstream
git worktree add .worktree/intake-2026-03-31-daemon-fix -b intake/2026-03-31-daemon-fix
```

### 2. 先在 `MedAutoScience` 做升级检查

不要先改 fork，再去看兼容性。先用 `MedAutoScience` 判定当前是否适合 intake：

```bash
cd <med-autoscience-root>
PYTHONPATH=src python3 -m med_autoscience.cli med-deepscientist-upgrade-check --profile /path/to/profile.toml --refresh
```

至少要确认：

- `repo_check` 能看到目标 upstream 差异
- 当前 controlled fork 身份仍正常
- workspace / overlay / behavior gate 没有额外阻断

### 3. 明确选中要吸收的提交

只吸收明确命名、可解释的 commit / PR，不做“整段时间窗口一起拉进来”的粗暴同步。

推荐记录：

- upstream commit
- 变更类型：`runtime_bugfix` / `compatibility_fix` / `dependency_refresh` / `workflow_change`
- 预期收益
- 潜在风险

### 4. 在 intake worktree 中吸收

优先：

```bash
git cherry-pick <upstream-commit>
```

只在这些条件同时满足时才考虑 merge：

- 一组提交必须作为原子集合进入
- 单独 cherry-pick 会破坏语义
- 相关 API / layout 没有突破当前兼容边界

### 5. 跑 `med-deepscientist` 本仓回归

至少运行与吸收面直接相关的测试。

例如 document asset / daemon 修复：

```bash
PYTHONPATH=src pytest -q tests/test_daemon_api.py -k 'document_asset_resolves_path_documents_from_active_worktree'
```

如果改动范围更大，就扩大到对应模块回归；不要只看 `cherry-pick` 是否成功。

### 6. 跑 `MedAutoScience` 兼容回归

在 `med-autoscience` 的迁移 worktree 中，使用当前 fork 重新验证。

至少覆盖：

- `med-deepscientist-upgrade-check`
- `workspace_contracts`
- 与本次 intake 相关的 controller / protocol 测试

如果 intake 触及 runtime / daemon / artifact 协议，必须额外跑：

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src pytest -q
```

### 7. 更新 fork 审计记录

每次成功 intake 后，都要同步更新：

- [`MEDICAL_FORK_MANIFEST.json`](../MEDICAL_FORK_MANIFEST.json)
- [`docs/medical_fork_baseline.md`](../docs/medical_fork_baseline.md)

最少要记录：

- upstream commit
- kind
- summary
- verification

如果是 dependency / lock 相关变化，还要补充：

- lock policy
- 是否重建了 lock
- 是否存在 source dirty context

### 8. 合并回 `med-deepscientist/main`

只有当以下条件同时成立，intake 分支才允许回到稳定线：

- fork 本仓回归通过
- `MedAutoScience` 兼容回归通过
- manifest / baseline 文档已更新
- 本次 intake 没有引入未解释的 API / layout 漂移

## 审计字段建议

`MEDICAL_FORK_MANIFEST.json` 中每条 `applied_commits` 建议至少包含：

```json
{
  "commit": "<sha>",
  "kind": "runtime_bugfix",
  "summary": "Fix worktree document asset resolution"
}
```

对应的人类可读记录建议写入 `docs/medical_fork_baseline.md`：

- commit
- kind
- reason
- verification

## 禁止做法

- 在 `main` 根目录直接改 fork 并长期不提交
- 直接 `merge upstream/main` 到稳定线
- 没有 `MedAutoScience` 回归就宣布 intake 完成
- 吸收 prompt/广告类改动却不审计
- 让 daemon API / quest layout 变化静默进入生产线

## 与 `MedAutoScience` 的对应关系

`med-deepscientist` 只负责受控吸收上游变化；
是否允许进入真实运行面，仍由 `MedAutoScience` 侧的升级检查、协议层与行为 gate 决定。

对应治理视角请看：

- [`med-autoscience/guides/upstream_intake.md`](../../med-autoscience/guides/upstream_intake.md)
