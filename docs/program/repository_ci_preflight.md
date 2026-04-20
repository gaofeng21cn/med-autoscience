# Repository CI Preflight

这个仓库当前采用的是“主线可直接 push，push CI 只承载稳定核心验证，重构高漂移面进入独立 advisory workflow”的模式。

这意味着：

- `main` 和 `development` 的 `push` 触发 `macOS CI`
- `macOS CI` 只运行 `quick-checks` stable core：`meta / fast / build`
- 提交前如果想提前发现高频问题，应优先运行本地 preflight
- 常规 `quick-checks` lane 保留 submission-facing DOCX/PDF 仍会实际消费的 `pandoc` 与 `BasicTeX`
- `display-heavy` 与 `family` lane 迁入 `macOS Advisory`，支持手动触发和每日定时触发
- `macOS Advisory` 的 `display-heavy` lane 继续承担 analysis bundle ready 的重型远端回归提示，并显式准备 `BasicTeX`、`graphviz`、`R`、`pkg-config` 与 `libxml2` 支撑 PDF 导出和 R 包编译
- `macOS Advisory` 的 `family` lane 承担 OPL shared boundary / family shared modules 的跨仓合同提示
- `release/full` lane 继续保持严格，用来覆盖正式发布前的整条重型验证链路

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
