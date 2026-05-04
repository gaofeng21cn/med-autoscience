# Repository CI Preflight

这个仓库当前采用的是“主线可直接 push，push CI 承载 change-aware preflight 与 build，重构高漂移面进入独立 advisory/nightly workflow”的模式。

这意味着：

- `main` 和 `development` 的 `push` 触发 `macOS CI`
- `macOS CI` 只运行 `quick-checks`：`scripts/verify.sh ci-preflight <base-ref>` 与 build
- 提交前如果想提前发现高频问题，应优先运行本地 preflight
- `regression`、`display`、`submission`、`family` 与 `meta` lane 迁入 `macOS Advisory`，支持手动触发和每日定时触发
- `macOS Advisory` 的 `display-heavy` lane 继续承担 analysis bundle ready 的重型远端回归提示，并显式准备 `BasicTeX`、`graphviz`、`R`、`pkg-config` 与 `libxml2` 支撑 PDF 导出和 R 包编译
- `macOS Advisory` 的 `submission-heavy` lane 承担 submission-facing DOCX/PDF 产物和投稿包相关回归，并显式准备 `pandoc` 与 `BasicTeX`
- `macOS Advisory` 的 `family` lane 承担 OPL shared boundary / family shared modules 的跨仓合同提示
- `macOS Advisory` 的 `meta` lane 承担 repo-tracked contract、docs、workflow 与入口面一致性提示
- `macOS Advisory` 为重 lane 预留 `MAS_TEST_LANE_SUMMARY_PATH`，并以非阻塞 run log 摘要、artifact 上传 lane summary 和只读 history summary 观察 duration drift、相对基线百分比变化与失败前后的耗时变化
- GitHub Actions 只在执行环境层使用 `uv` dependency cache、同 ref 旧 run concurrency cancellation 与短期 artifact retention 控制成本；这些机制不改变 `ci-preflight`、advisory 或 full 的质量语义
- `release/full` lane 继续保持严格，用来覆盖正式发布前的整条重型验证链路

## 验证职责

`smoke`、`regression`、`ci-preflight` 与 `structure` 的职责分开：

- `smoke`：本地默认入口，即不带参数的 `scripts/verify.sh`。它负责快速确认当前 checkout 的基础 sanity 与 fast tests，适合提交前和小改动自检。`line budget` 是有意保留在 smoke 前置 sanity 里的 sanity gate，用来及时发现测试或源码文件继续膨胀；这不改变默认 smoke 的 fast-test 行为。
- `regression`：显式回归入口，即 `scripts/verify.sh regression`。它负责比 smoke 更宽的行为回归，默认由 advisory/nightly 承接，避免把高漂移或高耗时回归压到每次 push。
- `ci-preflight`：push CI 入口，即 `scripts/verify.sh ci-preflight <base-ref>`。它负责基于 base ref 展开 checked-in preflight contract，只检查本次变更实际触达的高风险面，并与 build 一起保护主线。
- `structure`：显式结构入口，即 `scripts/verify.sh structure`。structure lane 继续承担 line budget 与 Sentrux 的结构检查职责；smoke 中的 line budget 只作为轻量 sanity gate，不取代 structure lane。

## 耗时预算

耗时预算只用于观察和提醒，不作为 push 阻塞条件。预算漂移应该先进入 advisory run log、artifact、只读 history summary、run summary 或人工排查；history summary 可以显示 `delta_from_baseline_percent`，也可以用 `--format json` 给后续 dashboard 消费，但它仍是 observability/advisory 信号。除非另有 repo 决策，不能把 duration guard 回灌到 `macOS CI` 的 `quick-checks`。

`--format json` contract 是 `scripts/summarize-test-lane-history.py` 的只读消费面，当前稳定字段为 `surface_kind`、`summary_dir` 与 `lanes[]`。每个 `lanes[]` 项保留 lane 名称、样本数、中位耗时、最大耗时、最慢 summary 路径，以及 `delta_from_baseline_percent`；其中 duration / sample 字段保持 number，缺少可用 baseline 或 baseline 非正数时 `delta_from_baseline_percent` 保持 number-or-null 语义并输出 JSON `null`。

- `smoke`：目标是本地秒级到低分钟级反馈；超过预算时提醒维护者检查 fast tests、line budget 或基础 sanity 是否膨胀。
- `ci-preflight`：目标是保持 push CI 可承受，只运行 change-aware preflight 与 build；耗时提醒用于判断 preflight contract 是否过宽，不额外触发重 lane。
- `full`：目标是正式发布前完整覆盖，允许显著慢于 smoke / ci-preflight；耗时漂移通过 advisory / full summary 与 history summary 观察，不能替代质量失败或变成日常 push 门禁。

重 lane 慢测试画像使用只读入口 `scripts/profile-heavy-test-lanes.py --print-only` 生成可复现的
`pytest --durations` 命令；实际 profiling 由维护者显式运行，不进入 push CI。

## 何时运行

以下场景建议在本地先跑：

- 改了 README、Codex plugin 文档、安装脚本
- 改了 display contract、publication gate、display guide
- 改了 runtime contract、router、runtime transport、runtime protocol
- 改了 integration harness activation package、cutover readiness、相关 preflight contract
- 改了 workflow、打包和 release 相关文件

## 命令入口

最显式的方式：

```bash
uv run medautosci preflight-changes --files README.md docs/references/codex_plugin.md
```

检查 staged 改动：

```bash
uv run medautosci preflight-changes --staged
```

和某个基线比较：

```bash
uv run medautosci preflight-changes --base-ref origin/main
```

如果要给 agent 或其他自动化消费结构化结果：

```bash
uv run medautosci preflight-changes --staged --format json
```

## Sentrux git history 审计

本仓库和 MAS/MDS 工作区默认保留 `worktree.useRelativePaths=true`。该配置会让 Git 在需要时写入 `extensions.relativeWorktrees`，方便重度 worktree 开发和目录整体迁移。部分外部审计工具尚未支持这个 Git extension；遇到 Sentrux MCP `git_stats` 因该 extension 失败时，不要修改主仓库配置。

使用仓库内 helper 准备一个只供审计使用的 shared clone：

```bash
scripts/prepare-sentrux-gitstats-clone.sh
```

输出中的 `sentrux_git_stats_clone` 是兼容 clone 路径。把这个路径传给 Sentrux MCP `scan`，再运行 `git_stats`。审计结束后执行输出中的 `cleanup_command` 删除临时 clone。

这个入口只创建临时 clone，不会 unset 或改写源仓库的 `worktree.useRelativePaths` / `extensions.relativeWorktrees` 配置。

## 规则边界

preflight 不是启发式脚本。

它只按照仓库内的 checked-in contract 分类改动面，并展开对应命令：

- `workflow_surface`
- `codex_plugin_docs_surface`
- `display_publication_surface`
- `runtime_contract_surface`
- `integration_harness_surface`

如果你的改动不在当前 contract 覆盖范围内，结果会显式返回 `unclassified_changes`。

这不是 bug，也不是降级兜底，而是在提醒：

- 当前改动面还没有正式纳入 preflight contract
- 不能把“未检查”伪装成“已检查”

## 遇到 `unclassified_changes` 时怎么做

正确处理方式是：

1. 确认这批改动是否属于一个新的高风险改动面
2. 如果是，就把对应路径和命令补进 `src/med_autoscience/dev_preflight_contract.py`
3. 同步补测试，再继续使用 preflight

不要：

- 静默跳过
- 临时把它塞进不相关的类别
- 直接把 preflight 改成“未分类就全量跑所有测试”

## 维护原则

- 本地 preflight 负责把高频、可预测失败前移
- 远端 CI 负责主线回归告警
- 两者都应保持可审计、可解释、边界明确
