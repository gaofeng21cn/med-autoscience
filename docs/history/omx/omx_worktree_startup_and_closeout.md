# 历史 OMX Worktree 启动与收尾操作规约

> 历史归档文档。它保留 OMX 时代的 worktree 运行手册，供审计与回溯使用。当前 worktree 规则以仓库根 `AGENTS.md`、`docs/README*` 和活跃核心文档为准。

这份文档保留 `Med Auto Science` 当时使用 OMX 的操作手册。

它解决的不是“怎么让 hook 完全变成 session 级”，因为这件事由 `oh-my-codex` 上游实现决定；它解决的是：

- 在当前工作方式下，怎样把多对话干扰降到最低；
- 什么时候必须开独立 worktree；
- 什么时候允许在仓库根工作树启动 OMX；
- 一条 OMX 主线结束后，怎样把进程、session 目录、worktree、branch 一次性收口；
- 怎样以可重复的方式重开下一条 owner lane。

这份文档与 [主线集成与清理节奏](../../program/mainline_integration_and_cleanup.md) 配套：

- `../../program/mainline_integration_and_cleanup.md` 负责定义“代码主线怎么吸收和清理”；
- 本文负责定义“OMX 执行面怎么启动、隔离、收尾和去污染”。

## 一句话原则

当前仓库内的正确用法不是“同一个 cwd 下同时挂很多条 OMX 线”，而是：

**一条重型 OMX 主线，只占一个独立 owner worktree；根工作树只承担轻操作、吸收与清理，不承担长期 `ralph/team/autopilot` 执行。**

## 为什么必须这样用

当前 hook 注册是 **工作目录级** 的，不是严格 session 级的。

这意味着同一个 cwd 下的多个对话，会共用：

- `.codex/hooks.json` 注册入口；
- `.omx/state/` 根级状态目录；
- 同一批 root-level hook 判定面。

如果在同一个 cwd 下并行跑多个 `ralph/team/autopilot`，容易出现下面这些污染：

- 旧 `session.json` 覆盖当前会话指针；
- 旧 `ralph-state.json` 继续把 Stop hook 判成 active；
- 历史 `skill-active-state.json` 让新对话误以为自己继承了旧技能态；
- `sessions/*` 里堆积的历史 session 目录被 fallback 扫到；
- 旧 detached tmux / worker 进程继续占住会话与资源。

因此，当前最有效的隔离手段不是“在同一个 cwd 里强行多开”，而是：

1. 用独立 worktree 做物理隔离；
2. 用明确的收尾流程把旧 session / 旧 tmux / 旧 worker 退场；
3. 把根工作树限制为轻执行面。

## 角色划分

### 根工作树

根工作树默认只允许做下面这些事：

- 阅读仓库真相；
- 做轻量文档改动；
- 做 merge-back / 吸收到 `main`；
- 做 worktree / branch 清理；
- 做 stale OMX state / tmux / session hygiene；
- 做非长驻、非重型的短操作。

根工作树默认 **不应** 承担：

- display / runtime / active-program 的长期 owner lane；
- 长时间 `ralph` 外循环；
- `team` 多 worker 长驻执行；
- `autopilot` 风格的连续实现线。

### Owner worktree

owner worktree 是一条 OMX 主线的唯一正式执行面。

owner worktree 负责：

- 当前子线的 tracked code / tracked docs 修改；
- 当前子线的 focused verification；
- 当前子线的 worktree-local `.omx` 报告面；
- 当前子线的 merge-back ready 证据。

当前项目里，**只有 owner worktree 应承载长期执行的 `ralph/team/autopilot`。**

## 启动前检查

在任何一条新 OMX 主线启动前，先做下面五项检查。

### 1. 根工作树必须干净

至少确认：

- `git status --short` 为空；
- `git worktree list` 里没有不明 active owner worktree；
- `main` 已经是你要继承的最新代码基线。

### 2. 当前线是否真的需要 owner worktree

如果任务只是：

- 读状态；
- 写短报告；
- 对账；
- 轻量 merge / cleanup；

那就在根工作树完成，不要为了形式再开一条 owner。

如果任务会进入下面任一类，就必须开 owner worktree：

- tracked code 改动；
- tracked docs 大改；
- 持续多轮验证；
- 需要 `ralph` 长循环；
- 需要 `team` 协调多个有写集的执行者。

### 3. 同一个 cwd 下只能有一条重型 OMX 线

在同一个 cwd 下，默认只允许一个 active 的：

- `ralph`
- `team`
- `autopilot`
- `ultrawork`

如果同一个 cwd 已经有一条重型 OMX 线在跑，下一条线必须：

- 换 worktree；
- 或者等当前线完成收尾后再开。

### 4. owner worktree 必须是 fresh 基线

新 owner worktree 的最低要求：

- 从当前 `main` 或指定吸收锚点创建；
- `git status --short` 为空；
- 不带旧的 tracked 改动；
- 不复用已经漂移过很久的历史 worktree；
- 若 `.omx/state/` 已存在，必须先判定它是否是当前线自己的 fresh 状态，否则先清理。

### 5. 当前线的 truth source 必须固定

启动前必须明确：

- 当前唯一 active 主线是什么；
- 当前权威 docs / reports / worktree 是哪些；
- 当前不要碰哪些别的 program / refactor / monorepo 线。

如果这一步没写清楚，就不要让 OMX 直接开跑。

## 标准启动流程

## Step 1. 从根工作树创建 fresh owner worktree

推荐路径模式：

```bash
git worktree add .worktrees/codex/<lane>-<timestamp> -b codex/<lane>-<timestamp> main
```

其中：

- `<lane>` 使用明确的业务语义；
- `<timestamp>` 使用 UTC 时间戳，避免命名冲突。

### 推荐命名

- display lane：`medical-display-<family-or-capability>-<timestamp>`
- runtime lane：`runtime-<subline>-<timestamp>`
- active program lane：`<program>-<subline>-<timestamp>`

## Step 2. 在 owner worktree 内确认 clean baseline

至少确认：

- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse --short HEAD`
- `git status --short`
- `.omx/state/` 是否为空或不存在

如果 owner worktree 一打开就带着旧 `.omx/state/session.json`、旧 `ralph-state.json`、旧 `skill-active-state.json`，先清掉，再启动新会话。

## Step 3. 只在 owner worktree 内启动重型 OMX

一旦确认这条线要跑长循环，启动位置必须是 owner worktree，而不是根工作树。

默认执行规则：

- `ralph` 负责长线自动推进；
- `leader-only / single-lane` 负责核心实现写集；
- `team` 只在 write set 明确不重叠时启用；
- 核心 tracked code 文件进入实现后，优先回到单 lane。

## Step 4. 启动后立即固定真相面

启动后一开始就要写清楚：

- 当前 active 主线；
- 当前 owner worktree 路径；
- 当前 branch；
- 当前 scope；
- 当前 reports / baton / open issues；
- 什么情况下允许停车。

如果不先固定这些，后面再强行追溯上下文，污染会迅速放大。

## `medical-display-mainline` 的推荐启动形态

`medical-display-mainline` 现在不是“偶尔修一张图”的短线，而是一条持续滚动的 display 主线。

因此它的正确启动方式应固定为两层：

### 第一层：根工作树上的主线控制面

根工作树只负责：

- 读取 `docs/capabilities/medical-display/medical_display_*` 的 tracked 真相；
- 读取 `.omx/reports/medical-display-mainline/*` 的 baton 与 backlog；
- 判定当前 phase；
- 决定下一簇 capability cluster；
- 在上一轮 merge-back 后做清理与 reroute。

根工作树 **不应** 直接承载 display 的长期实现。

### 第二层：独立 owner worktree 上的重型执行面

一旦 display 主线进入以下任一状态：

- 当前 next cluster 已选定；
- owner brief 已收口；
- 需要进入 `Phase 2` 的 tracked code / tracked docs 改动；
- 需要长期 `ralph` 外循环推进；

就必须：

1. 从最新 `main` 新开唯一 owner worktree；
2. 只在该 owner worktree 内启动重型 OMX；
3. 用 `leader-only / single-lane` 承接 display 核心写集；
4. 完成后 merge-back、清理 worktree / branch；
5. 再回到根工作树进入下一轮 reroute。

### display 主线的默认循环

`medical-display-mainline` 的正常工作节奏应固定理解为：

1. 根工作树做 `Phase 4` 路由与 owner brief 收口；
2. 新开 owner worktree，进入 `Phase 2` capability cluster 实现；
3. 若真实图面暴露 paper-facing 问题，则进入 `Phase 3` visual audit；
4. 回到 `Phase 5` merge-back / cleanup；
5. 再回根工作树继续下一轮 `Phase 4`。

这里的 phase 边界是 **阶段切换点**，不是默认停车点。

### display 主线的当前推荐实践

对当前 `medical-display-mainline`，建议固定使用两类 prompt：

- 根工作树：
  - `.omx/context/OMX_MEDICAL_DISPLAY_MAINLINE_AUTOPILOT_PROMPT.md`
  - `.omx/context/OMX_MEDICAL_DISPLAY_MAINLINE_SHORT_PROMPT.md`
- 新开的 owner worktree：
  - 针对当前 cluster 的 owner prompt，例如 `.omx/context/OMX_MEDICAL_DISPLAY_SPATIAL_OWNER_REOPEN_PROMPT.md`

这样可以把：

- 主线控制面；
- 当前 implementation baton；
- worktree 隔离纪律；
- merge-back 之后的自动续跑；

放在稳定、可复用、可审计的 surface 上，而不是靠会话记忆维持。

## 执行中纪律

### 1. 不在同一个 cwd 里再开第二条重型线

如果想同时做另一条线：

- 新开第二个 worktree；
- 在第二个 worktree 内启动第二条线。

不要在同一个 cwd 下靠“不同对话”硬分离。

### 2. 根工作树只做轻量协调

当 owner worktree 在跑时，根工作树只做：

- 读 reports；
- 写短手册；
- 做 merge-back 准备；
- 做 stale cleanup；
- 做最终吸收。

不要在根工作树再开一条新的 owner。

### 3. team 不是默认选项

只有当任务满足下面两个条件，才开 `team`：

- 任务可以拆成明确互不重叠的 write set；
- worker 停掉后不会留下难以判断的 ownership 漂移。

如果剩余 blocker 写集高度重叠，就坚持：

- `leader-only`
- `single-lane`

### 4. 停车不等于完成

owner lane 可以停车，但停车前至少要写清楚：

- 当前停在哪个 phase；
- tracked 代码是否 clean；
- 是否 merge-back ready；
- 当前 worktree 是否仍然是 active owner；
- 下一棒是谁；
- 什么时候必须继续。

## 标准收尾流程

## Step 1. 先完成当前线的验证与报告

收尾前至少明确：

- 代码或文档改动是否已提交；
- `git status --short` 是否为空；
- 关键 focused verification 是否通过；
- reports 是否已更新到当前真相；
- 当前线是 `blocked`、`in_progress`、`merge-back ready` 还是 `closed`。

## Step 2. 吸收到 `main`

如果 owner worktree 产出了独立提交：

- 先做 clean integration；
- 再吸收到根工作树 `main`；
- 在 `main` 上做最小 acceptance verification。

如果 owner branch 与 `main` 完全同头、没有独立提交：

- 不需要保留空壳；
- 直接删除 worktree 和 branch。

## Step 3. 立刻清理 worktree 与 branch

一条线的结果一旦已经吸收到 `main`，或确认没有独立提交，就应在同一轮清掉：

- owner worktree；
- owner branch；
- 该线留下的临时 clean integration worktree；
- 该线遗留的无效 worker worktree。

不要把“空壳 worktree”当作未来保留位。

需要时，之后再从最新 `main` 新建 fresh owner worktree。

## Step 4. 清理 OMX 执行残留

至少检查：

- 旧 detached tmux session；
- 旧 Codex worker / leader 进程；
- `.omx/state/session.json`
- `.omx/state/ralph-state.json`
- `.omx/state/skill-active-state.json`
- `.omx/state/sessions/*`
- `.omx/state/team/*`

如果它们不再对应当前 live session，就不能继续留在 active state root 里。

### 推荐做法

- 当前 live session 保留在 `.omx/state/sessions/<current-session>/`
- 其余历史 session 目录整体移到 archive 目录
- root-level 旧指针文件移到 archive 目录
- 旧 `team/` canonical state 目录移到 archive 目录

不要简单堆在 `.omx/state/sessions/` 里继续让 hook 扫到。

## Step 5. 再决定是否开下一条线

只有在下面三件事都成立时，才允许开下一条 owner line：

1. 旧线代码面已经吸收到 `main` 或确认无需吸收；
2. 旧线的 worktree / branch / tmux / session 已完成最小清理；
3. 新线的 scope、truth source、owner worktree 已重新固定。

## Stale OMX 清理流程

这一步用于“当前项目没有别的 OMX 对话在工作，但 root `.omx/state` 已经很脏”的场景。

## Step A. 先识别当前 live session

以进程真实命令行为准，找到当前 session 的：

- `model_instructions_file=.../.omx/state/sessions/<session_id>/AGENTS.md`

当前 live session 对应的 `<session_id>` 必须保留。

## Step B. 杀掉旧 detached tmux session

按仓库维度筛出：

- `omx-<repo>-main-*`

保留当前 live session 对应的 tmux session，其余全部杀掉。

## Step C. 杀掉旧 Codex / worker 进程

凡是命令行仍引用本仓库旧 `model_instructions_file`，但不属于当前 live session 的：

- leader
- worker
- 旧 team worker

都应终止。

## Step D. 归档旧 session 目录

只保留当前 live session 对应目录，其余：

- `sessions/*`

整体移到 archive 目录。

推荐 archive 模式：

```text
.omx/state/session-archive-<timestamp>/
```

## Step E. 归档 root-level 旧状态指针

对于已经失真的 root-level 状态：

- `session.json`
- `ralph-state.json`
- `skill-active-state.json`
- `ralph-last-steer-at`

不要继续留在 active 根目录。

## Step F. 归档旧 team canonical state

如果当前没有 live team，旧的：

- `.omx/state/team/*`

也应移走，避免被误当作 canonical team state。

## fresh spatial owner worktree 重开规范

当 display 下一轮要继续 `spatial_niche_map_panel` 或其他 spatial lane 时，统一按下面流程重开。

## 1. 先在根工作树完成 hygiene

要求：

- `main` clean；
- 旧 owner worktree / branch 已删；
- 旧 detached OMX 进程已收口；
- `.omx/state/sessions/` 里只保留当前 live session；
- root-level 失真指针已清理或归档。

## 2. 从最新 `main` 新建 fresh worktree

推荐：

```bash
git worktree add .worktrees/codex/medical-display-spatial-niche-<timestamp> \
  -b codex/medical-display-spatial-niche-<timestamp> \
  main
```

## 3. 进入 worktree 后先做 baseline check

最少检查：

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD
git status --short
find .omx -maxdepth 3 -type f
```

目标是确认：

- 分支正确；
- 基线干净；
- 没带旧 `.omx` 脏状态。

## 4. 只在这个 worktree 里启动 OMX

新的 spatial line 只允许在这个 fresh worktree 里启动。

根工作树不得同时再开 display owner execution。

## 5. 当前 lane 的 scope 一开始就写死

例如：

- 当前唯一 active lane：`medical-display-spatial-niche`
- 当前只做：`new template + schema + QC + visual audit`
- 当前不并入 trajectory lane
- 当前不回根工作树写 tracked code

## 6. 收尾后立刻吸收与清理

当 spatial lane 完成时：

- 先 merge-back 到 `main`
- 再删 owner worktree / branch
- 再清 OMX 执行残留

不要长期保留一个“下次也许还要用”的旧 spatial worktree。

## 固定禁令

下面这些行为，在当前仓库里默认禁止：

- 在根工作树同时跑多条 `ralph/team/autopilot` 主线；
- 把旧 owner worktree 当作长期常驻执行面；
- 把无独立提交的空壳 branch / worktree 长期保留；
- 在 tracked 代码线已经结束后，继续把旧 session 目录留在 active `sessions/` 下；
- 让旧 detached team worker 常驻数天以上仍不清理；
- 用“不同对话”代替 worktree 物理隔离。

## 当前推荐口径

今后统一按下面这条口径理解：

- hook 是 cwd 级注册的，隔离靠 worktree，不靠侥幸；
- owner line 靠 fresh worktree 隔离；
- 根工作树只做轻协调、吸收和清理；
- 一条线结束后，代码面和 OMX 运行态都要同轮收口；
- 新一轮 spatial lane 应从 fresh worktree 重开，而不是复用历史空壳。
