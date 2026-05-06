# CI Soft Preflight Design

## 背景

这个仓库最近一批 GitHub CI failed 主要不是同一个问题：

- 一部分是 `study_runtime_router` / `runtime_transport` / typed runtime surface 正在迁移时的中间态提交。
- 一部分是文档、生成 catalog、README 链接与测试断言不同步。
- 还有一条是 GitHub Actions workflow 自身引用了不存在的 `setup-uv` tag。

这些失败说明当前仓库缺的是“提交前最小必要验证面”，而不是“必须阻断 `push main`”。

用户明确要求：

- 保持可以直接 `push main`
- 不用 branch protection / required checks 卡住推送
- CI 更适合作为事后告警，而不是远端闸门

## 目标

建立一套软约束：

1. GitHub CI 继续保留，但只承担远端告警职责。
2. 本地提供显式、可审计、低成本的变更感知预检入口。
3. 预检只跑与当前改动直接相关的测试和构建步骤，不默认全量跑仓库测试。
4. 预检规则必须是显式映射，不允许启发式猜测。

## 非目标

- 不恢复 `required_status_checks`
- 不恢复 `required_pull_request_reviews`
- 不引入 `pre-push` hook 或任何自动阻断 `git push` 的本地钩子
- 不做“改了某类文件大概猜一下该跑什么”的模糊分类
- 不把医生面向的 README 改成开发者操作手册

## 备选方案

### 方案 A：只保留远端 CI

优点：

- 不需要新增任何本地能力

缺点：

- 已经重复出现过的低级不同步问题仍会继续在远端暴露
- CI 会继续承担本地本可提前发现的错误发现职责

### 方案 B：远端 CI 告警 + 本地显式预检命令

优点：

- 不拦 `push main`
- 能把高频失败前移到本地
- 预检成本远低于每次全量 `pytest`

缺点：

- 需要维护一份“改动面 -> 检查面”的显式规则表

这是推荐方案。

### 方案 C：`pre-push` hook

优点：

- 理论上更强制

缺点：

- 直接与“不要卡住我的 push”冲突
- 很容易重新演变成新的硬门

不采用。

## 设计

### 1. GitHub CI 角色收紧

调整 `.github/workflows/ci.yml`：

- 保留 `push` 到 `main`、`development`
- 去掉 `pull_request` 触发

含义：

- 主线仍有远端回归告警
- 临时 worktree、clean integration branch、PR 试运行不再自动制造额外 CI 噪音

`release.yml` 保持原语义不变，只继续服务 tag release。

## 2. 本地预检入口

新增一个显式 CLI 子命令：

- `medautosci preflight-changes`

支持三种输入来源：

1. `--files <path> ...`
2. `--staged`
3. `--base-ref <git-ref>`

其中：

- `--files` 是最显式、最可审计的模式
- `--staged` 用于提交前检查 staged 改动
- `--base-ref` 用于和某个基线比较，例如 `origin/main`

命令输出支持：

- `--format text`
- `--format json`

默认输出 text。

## 3. 预检分类必须是显式 contract

新增一份仓库内的规则表，作为唯一分类来源。

建议文件：

- `src/med_autoscience/dev_preflight_contract.py`

它只做两件事：

1. 把路径前缀/具体文件精确映射到预检类别
2. 把预检类别精确映射到要执行的命令集合

不允许：

- 正则大杂烩式模糊命中
- 基于文件内容猜类别
- 根据历史经验隐式跳过

## 4. 第一版预检类别

第一版只覆盖最近已经实际出过问题的改动面。

### `workflow_surface`

命中范围：

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `scripts/install-macos.sh`
- `pyproject.toml`

执行：

- `uv run pytest tests/test_release_workflow.py -q`
- `uv run pytest tests/test_release_installer.py -q`
- `uv run python -m build --sdist --wheel`

### `codex_plugin_docs_surface`

命中范围：

- `README.md`
- `guides/`
- `scripts/install-codex-plugin.sh`
- `tests/test_codex_plugin.py` 相关引用文件

执行：

- `uv run pytest tests/test_codex_plugin.py -q`
- `uv run pytest tests/test_codex_plugin_installer.py -q`
- `uv run pytest tests/test_codex_plugin_installer_script.py -q`

### `display_publication_surface`

命中范围：

- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/display_layout_qc.py`
- `src/med_autoscience/controllers/display_surface_materialization.py`
- `src/med_autoscience/controllers/medical_publication_surface.py`
- `src/med_autoscience/controllers/publication_gate.py`
- `guides/medical_display_audit_guide.md`

执行：

- `uv run pytest tests/test_display_schema_contract.py -q`
- `uv run pytest tests/test_display_surface_materialization.py -q`
- `uv run pytest tests/test_display_layout_qc.py -q`
- `uv run pytest tests/test_publication_gate.py -q`
- `uv run pytest tests/test_medical_publication_surface.py -q`

### `runtime_contract_surface`

命中范围：

- `src/med_autoscience/controllers/study_runtime_router.py`
- `src/med_autoscience/controllers/study_runtime_startup.py`
- `src/med_autoscience/controllers/study_runtime_status.py`
- `src/med_autoscience/runtime_transport/med_deepscientist.py`
- `src/med_autoscience/runtime_protocol/`

执行：

- `uv run pytest tests/test_study_runtime_router.py -q`
- `uv run pytest tests/test_runtime_transport_med_deepscientist.py -q`
- `uv run pytest tests/test_runtime_protocol_study_runtime.py -q`
- `uv run pytest tests/test_runtime_protocol_runtime_watch.py -q`

## 5. 未分类改动的处理

这是这个设计里最关键的严格性要求。

如果输入改动里存在未命中的文件，`preflight-changes`：

- 直接报告 `unclassified_changes`
- 返回非零退出码
- 列出所有未覆盖路径

它不会：

- 静默跳过
- 自动扩成全量测试
- 假装“应该没事”

这样做的目的，是把“预检 contract 尚未覆盖新的改动面”显式暴露出来。

是否继续 `push` 由人决定，但平台不能伪装自己已经检查过。

## 6. 多类别组合语义

一次改动可能同时命中多个类别。

此时：

- 按类别合并命令集合
- 去重后顺序执行
- 输出每个类别的命中结果、执行命令、通过/失败状态

默认策略：

- 只要有一条命令失败，整体退出非零

## 7. 输出面

命令结果需要形成稳定输出结构，至少包含：

- `input_mode`
- `changed_files`
- `matched_categories`
- `unclassified_changes`
- `planned_commands`
- `results`
- `ok`

这样后续无论是人读、agent 读，还是未来挂到更高层 controller，都不需要重新解析终端文本。

## 8. 文档面

不改医生面向的主页叙事。

新增一份面向维护者 / agent 的稳定指南：

- `guides/repository_ci_preflight.md`

只说明：

- 远端 CI 现在是什么角色
- 本地什么时候该跑 `medautosci preflight-changes`
- 三种输入模式分别适合什么场景
- 如果出现 `unclassified_changes` 应该怎么补 contract

## 9. 需要修改的表面

- `.github/workflows/ci.yml`
- `src/med_autoscience/cli.py`
- `src/med_autoscience/dev_preflight_contract.py`
- `src/med_autoscience/dev_preflight.py`
- `tests/test_dev_preflight_contract.py`
- `tests/test_dev_preflight.py`
- `guides/repository_ci_preflight.md`

## 验证标准

### 正向

- 改 `README.md` 时，能只命中 `codex_plugin_docs_surface`
- 改 `study_runtime_router.py` 时，能只命中 `runtime_contract_surface`
- 改 display contract 相关文件时，能只命中 `display_publication_surface`
- 改 workflow / packaging 文件时，能命中 `workflow_surface`
- 同时改多个区域时，能合并类别并去重命令

### 反向

- 改到未纳入 contract 的文件时，命令必须返回 `unclassified_changes`
- `ci.yml` 不再在 `pull_request` 上自动触发
- 没有任何本地 hook 会自动阻断 `git push`

## 实施顺序

1. 先实现 preflight contract 和执行器
2. 再接入 CLI 子命令
3. 然后补测试
4. 最后收紧 `ci.yml` 并写维护指南

## 风险与边界

主要风险不是实现复杂度，而是 contract 漏覆盖。

这个风险不通过“默认跑全量测试”解决，而通过以下方式控制：

- 未分类改动直接显式失败
- 规则表 checked-in
- 新增重要改动面时必须同步扩 contract 和测试

这样能保持规则刚性，同时不把仓库重新做成 push-blocking 系统。
