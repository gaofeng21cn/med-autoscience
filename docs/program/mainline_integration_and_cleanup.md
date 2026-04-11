# Mainline Integration And Cleanup Cadence

这份文档定义 `Med Auto Science` 当前主线的一个固定纪律：

- 子线怎么吸收到 `main`
- 什么时候清理 worktree / branch / team 残留
- 什么时候才允许切到下一条固定子线

它的目的不是增加流程负担，而是防止主执行面、历史 worktree、tmux pane、team mailbox 与 `main` 状态长期漂移。

## 一句话原则

当前主线的正确节奏不是：

- 想起了再收口
- 觉得乱了再清理
- 做完一个子线就自然停住

而是：

**每条子线都必须经过 `验证 -> clean integration -> 吸收进 main -> 清理残留 -> 再切下一条` 这条固定收尾流程。**

## 为什么必须有这条 cadence

如果没有固定收尾流程，仓库会持续积累下面这些漂移：

- 已完成但未吸收到 `main` 的 branch
- 已完成但仍保留的 clean integration / minimal validation worktree
- 已退出但仍残留的 team worker worktree
- 已归档但仍被误当成真相源的 mailbox / state
- `CURRENT_PROGRAM` / reports 与真实运行面不同步

这类漂移不会立刻让代码坏掉，但会持续削弱：

- 当前活跃子线是否清楚
- 哪些结果已经成为 inherited truth
- 哪些分支只是历史候选
- 当前执行主线是否该继续还是该收口

## 固定五步收尾流程

## Step 1. 子线完成判定

当前子线只有在满足下面条件后，才算进入“可吸收”阶段：

- contract convergence 已完成
- 必要验证已完成
- reports 已更新
- 结论已经明确：
  - `main-absorption candidate ready`
  - 或等价表述

如果还没满足这一步，就不应提前切下一子线。

## Step 2. clean integration

一旦进入“可吸收”阶段，必须立刻转入 clean integration：

- 基于当前 `main`
- 新建独立 clean worktree
- 只回放经过验证的最小切片
- 不夹带旧 team checkpoint、归档 worker diff、无关 docs 漂移

推荐吸收方式：

- `git cherry-pick` 已验证的最小提交切片
- 或者在 clean worktree 中重建 patch-equivalent 的最小 slice

不推荐：

- 直接把历史开发 worktree 当成正式吸收面
- 把多轮 team history 一并 merge 回 `main`

## Step 3. acceptance verification

clean integration 形成后，必须在该 worktree 原位重跑 acceptance verification：

- focused tests
- py_compile / lint / diff check
- 与当前 `main` 的 diff 面复核

只有这一步通过，才允许吸收到 `main`。

## Step 4. 吸收到 `main`

当 clean integration 通过后，应立即：

1. 吸收到根 checkout `main`
2. 在 `main` 上重新确认 focused verification
3. 更新 reports / CURRENT_PROGRAM（如果当前唯一活跃子线发生变化）

这一步完成后，当前子线的结果才算正式成为：

- inherited truth
- active mainline history

## Step 5. 清理残留

吸收到 `main` 后，同一轮里应立即清理：

- 该子线的 clean integration worktree
- 该子线的 feature branch
- 该子线相关的 team worker worktree
- 该子线已完成的 nested phase-b worker worktree
- 已归档且不再作为当前真相源的 mailbox/state 残留
- 已退出的 tmux worker pane / HUD pane

当前不应清理的对象只有两类：

1. 仍有活 tmux pane / 活 team state 占用的对象
2. 尚未决定“吸收 or 放弃”的主候选 worktree / branch

也就是说：

- 可以优先清理 worker 壳
- 不能在未做最终判断前误删主候选线

## 什么时候才允许切到下一固定子线

只有在下面三件事都成立后，才允许切下一条固定子线：

1. 当前子线已吸收到 `main`
2. 当前子线的历史残留已完成最小清理
3. reports 已明确把下一条固定子线提升为唯一 active subline

如果缺任意一项，就不算真正完成切线。

## 固定时间节点

为了避免“只有想起来才收口”，当前推荐把收口纪律固定成 4 个时间节点。

## 时间点 A：子线 ready 当天

触发条件：

- 当前子线形成 `main-absorption candidate ready`

动作：

- 当天进入 clean integration

## 时间点 B：吸收到 `main` 的同一轮

触发条件：

- clean integration 验证通过
- 已吸收到 `main`

动作：

- 当轮清掉 feature branch / clean integration worktree / worker 壳

## 时间点 C：每日 hygiene sweep

触发条件：

- 每天一次
- 或每次准备让 Codex 开新主线前

动作至少包括：

- `git worktree list`
- `git branch --list 'codex/*'`
- `tmux list-panes -a`
- `git status --short`
- `git rev-list --left-right --count origin/main...main`

目标是快速识别：

- 哪些分支已经没必要继续存在
- 哪些 worktree 只剩历史壳
- 哪些 tmux pane 只是残留
- `main` 是否该 push 却没 push

## 时间点 D：phase / subline 切换前

触发条件：

- 准备从当前子线切到下一条固定子线

动作：

- 先完成当前子线的 integration / cleanup
- 再切换 `CURRENT_PROGRAM` / reports
- 最后才允许开下一条子线的 team

## 当前推荐口径

今后统一按下面这条口径理解：

- 子线完成不等于主线收口完成
- clean integration 是正式吸收前的必经环节
- 吸收到 `main` 后必须立即清理残留
- 只有完成 integration + cleanup，才允许切到下一固定子线

也就是说：

**主线推进不是“开发完一个子线就自然结束”，而是“开发、吸收、清理、再继续”的循环。**
