# Init Workspace Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

## 背景

当前 `MedAutoScience` 已经通过文档明确了“病种级 workspace”是默认工作单元，但新项目启动仍依赖 Agent 读取文档后自行创建目录与入口文件。

这对强 Agent 用户是可行的，但仍有两个问题：

- 缺少一个稳定、可审计、可复现的初始化入口。
- 同一个 Agent 在不同会话里可能生成略有漂移的 workspace 骨架。

因此需要增加一个 `agent-first` 的 `init-workspace` 入口，让 Agent 可以直接调用平台完成病种 workspace 初始化，而不是复制静态模板目录。

## 目标

新增一个 `medautosci init-workspace` 命令，能够：

- 在目标路径创建病种级 workspace 最小骨架
- 生成最小 `ops/medautoscience/profiles/*.local.toml` 示例 profile
- 生成 `ops/medautoscience/config.env.example` 与 `ops/deepscientist/config.env.example`
- 生成一个简短的 workspace 根 `README.md`
- 支持 `--dry-run`，以 JSON 形式返回将创建的目录与文件，方便 Agent 先审计再执行

## 非目标

- 不 clone `DeepScientist`
- 不安装 Python、uv、Codex 或其他系统依赖
- 不自动写入真实本机路径到 `config.env`
- 不自动创建首个 `study-id`
- 不替代 `bootstrap`

## 设计原则

### 1. Agent-first

默认行为是真正落盘，因为 Agent 需要可执行入口。

同时提供 `--dry-run`，让 Agent 在需要时先看计划、再决定是否应用。

### 2. 最小骨架

只创建当前平台真正依赖的骨架：

- `datasets/`
- `contracts/`
- `studies/`
- `portfolio/data_assets/`
- `refs/`
- `ops/medautoscience/{bin,profiles}/`
- `ops/deepscientist/{bin,runtime,startup_briefs,startup_payloads}/`

不引入大而全模板。

### 3. 不替代 profile-driven 设计

`init-workspace` 只负责初始化 workspace 本地层。

它不寻找外部 repo，不做隐式路径猜测，不破坏当前“显式配置优先”的原则。

### 4. 幂等

重复执行时：

- 已存在目录不报错
- 已存在文件默认不覆盖
- 如需覆盖，必须显式 `--force`

## 推荐实现

### CLI

新增子命令：

```bash
medautosci init-workspace \
  --workspace-root /ABS/PATH/TO/NEW-WORKSPACE \
  --workspace-name diabetes \
  --profile-file ops/medautoscience/profiles/diabetes.local.toml \
  --dry-run
```

建议参数：

- `--workspace-root` 必填
- `--workspace-name` 必填
- `--profile-file` 选填，默认 `ops/medautoscience/profiles/<workspace-name>.local.toml`
- `--default-publication-profile` 选填，默认 `general_medical_journal`
- `--default-citation-style` 选填，默认 `AMA`
- `--dry-run`
- `--force`

### Controller

新增独立 controller，例如：

- `src/med_autoscience/controllers/workspace_init.py`

职责：

- 计算目录骨架
- 渲染示例文件内容
- 在 `--dry-run` 时返回计划
- 在执行模式下创建目录与文件

### 输出

统一返回 JSON，至少包含：

- `workspace_root`
- `workspace_name`
- `created_directories`
- `created_files`
- `skipped_files`
- `profile_path`
- `next_steps`
- `dry_run`

## 测试

至少覆盖：

- `--dry-run` 不落盘但返回计划
- 正常执行会创建目录和文件
- 二次执行默认跳过已存在文件
- `--force` 会覆盖可覆盖文件
- profile 示例内容指向正确相对路径

## 成功标准

- Agent 可直接调用 `init-workspace` 建立新病种 workspace
- 新 workspace 无需复制旧病种目录
- 生成结果与当前文档描述一致
- 生成物仍然遵守 profile-driven 和显式配置原则
