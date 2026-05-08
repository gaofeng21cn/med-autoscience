# DeepScientist Latest-Update Learning Protocol

这份协议定义维护者说“学习一下 `DeepScientist` 的最新更新”时，`MAS` 应默认执行什么。

它不是泛泛调研请求，也不是要求把 upstream 整体同步进来。它表示启动一轮受控的 learning-and-landing intake：先审计 upstream 最新变化，再把真正值得学的能力切成可验证 lane，落到 `MAS` 自己的 owner surface。外部 `MDS` 不再是默认落点，只能作为 frozen source archive、historical fixture、explicit legacy diagnostic 或 provenance/parity reference 出现。

## 触发短语

以下表达都按本协议处理：

- “学习一下 `DeepScientist` 的最新更新”
- “看看 `DeepScientist` 最近更新，有什么值得吸收”
- “按上次那套学习一下 `DeepScientist`”
- “一周后再学习 `DeepScientist` upstream”

默认含义：

1. 立即进入执行型任务，不停在只读建议。
2. 先读当前 MAS repo truth，再审计 upstream `DeepScientist`。
3. 分类、落地、验证、吸收回 `med-autoscience/main`、清理 worktree。
4. 只在用户显式要求 legacy fork maintenance、backend audit 或 parity fixture refresh 时，才触碰外部 `med-deepscientist` checkout。

## 固定阅读入口

每轮开始前必须读：

- `MAS`: `docs/references/med-deepscientist/deepscientist_continuous_learning_policy.md`
- `MAS`: `docs/references/med-deepscientist/med_deepscientist_continuous_learning_plan.md`
- `MAS`: `docs/references/med-deepscientist/med_deepscientist_method_learning_disciplines.md`
- `MAS`: `docs/references/med-deepscientist/med_deepscientist_upstream_source_provenance.md`
- `MAS`: `docs/references/med-deepscientist/source_provenance.json`
- `MAS`: `docs/status.md`
- `MAS`: `docs/program/program_portfolio_consolidation.md`
- `MAS`: `docs/program/mas_single_project_mds_absorb_program.md`

这些文档决定 owner 边界。它们优先于临时记忆、上一轮对话总结和旧 `MDS` fork intake 习惯。若本轮确实需要审计外部 `med-deepscientist` checkout，再额外读该 checkout 的当前 `docs/status.md` / fork audit surface；这一步是例外，不是默认学习入口。

## 固定执行流程

### 1. Fresh upstream audit

This is the `fresh upstream audit` step.

在配置好的 upstream `DeepScientist` source 或只读 mirror 中：

```bash
git fetch upstream --prune
git rev-list --left-right --count main...upstream/main
git log --reverse --oneline main..upstream/main
```

同时看 upstream README / docs / skills / runtime surface 中被强调的新能力。判断对象是 capability，不是 commit 数量。审计记录必须写清 upstream ref/range；如果使用本机 `med-deepscientist` checkout 作为 source mirror，必须标注它只是 source mirror / provenance input，不是默认 runtime owner 或 landing repo。

### 2. Decision matrix

每个候选变化必须先归入 intake decision：

- `adopt_code_slice`: 需要在 `MAS` 内部以 MAS-owned 模块、测试和 no-history provenance 方式实现或重写。
- `adopt_contract`: 不搬代码，把行为吸收到 `MAS` runtime / controller / eval / publication contract。
- `adopt_template`: 学 stage packet、SOP、skill discipline，落到医学 overlay template 或 stage packet。
- `fixture_only`: 只保留为 regression / parity / negative fixture，不进入默认运行面。
- `watch_only`: 有启发，但现在只记录，不改变主线。
- `reject`: provider / UI / marketing / product-shell 扩面，或会削弱医学 owner truth。

如果候选变化要进入 retained capability / cutover inventory，还必须再标注 MAS capability classification：`mas_owned`、`rewrite_in_mas`、`fixture_only`、`retire` 或 `external_source_archive_only`。

分类时必须写清：

- upstream range 或 commit
- learned capability
- owner surface
- decision
- verification target
- no-history / contributor-footprint 影响

### 3. Parallel worktrees

如果有多个互不冲突 lane，默认并行开 worktree：

- `MAS runtime/code lane`: 改 `med-autoscience` 的 Runtime OS、Artifact OS、Quality OS、Evaluation OS 或 controller/runtime code，并写 focused tests。
- `MAS contract/template lane`: 改 `med-autoscience` docs / contracts / templates / meta or focused tests。
- `MAS fixture/parity lane`: 只有当 lesson 需要保留 upstream/MDS trace 作为 fixture 或 parity oracle 时才开。
- `legacy MDS maintenance lane`: 只有用户显式要求继续维护外部 fork，或本轮必须刷新 legacy diagnostic source 时才开；它不得成为默认学习路线。

每条 lane 完成后必须吸收回对应 repo 的 `main` 并清理临时 worktree / branch。默认只有 `med-autoscience/main` 会发生变更。

### 4. Verification gate

声称落地前至少要有：

- MAS 对应 contract / template / runtime 行为验证；纯叙述性 docs 只做人工 review、`git diff --check` 和必要的链接 spot-check，不用 pytest 固定 Markdown 措辞、标题或锚点。
- `git diff --check`。
- 最终 root checkout 状态核对。
- 如果改动涉及 machine-readable contract、CLI/MCP/API、runtime behavior、生成器或 retained fixture，运行对应 focused tests 或 `scripts/verify.sh` 相关 lane。

如果显式触碰外部 `med-deepscientist` checkout、legacy restore/import diagnostic、MDS fixture 或 source archive，需要额外覆盖对应 legacy/parity 验证；否则不要求 MDS repo 测试。

### 5. Audit record

每轮必须留下 repo-tracked intake record：

- `MAS`: `docs/history/program/deepscientist_learning_intake_YYYY_MM_DD.md`
- `MDS`: 只有当本轮显式修改外部 fork 或刷新 legacy source archive/parity fixture 时，才更新该 repo 的 fork audit surface。

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
- 会让外部 `MDS` 重新成为默认 runtime、progress、quality、publication 或 diagnostic owner 的改动

## 完成定义

一轮 “学习 `DeepScientist` 最新更新” 完成，必须同时满足：

1. upstream delta 已 fresh 审计。
2. 候选变化已按 decision matrix 分类。
3. 选中的 code / contract / template slice 已落地。
4. 相关 tests 已通过。
5. 分支和 worktree 已清理。
6. `med-autoscience/main` 上有可追溯 commit。
7. 如果用户明确要求推送，已推送本轮实际触碰的 repo；默认只推 `med-autoscience`。

如果 upstream 没有值得吸收的变化，也要留下简短 intake record，说明 range、分类和 `watch_only` / `reject` 原因。
