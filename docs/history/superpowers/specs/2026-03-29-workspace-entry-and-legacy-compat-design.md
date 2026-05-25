# NF-PitNET Workspace Entry And Legacy Compatibility Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

## 背景

当前 `NF-PitNET workspace` 已经在真实课题中沉淀出一批有效能力，但这些能力分散在两层：

1. `workspace/ops/deepscientist/controllers/*` 这一层的本地外层控制器和交付脚本
2. `MedAutoScience` 中正在抽取出来的通用治理、controller、adapter、overlay、policy

下一篇论文需要默认走 `MedAutoScience` 作为顶层入口，而不是继续依赖专病 workspace 里的 `DeepScientist` 魔改层。
但已经完成主稿的 `002-early-residual-risk` 仍然可能进入返修或补实验阶段，因此不能破坏其已有维护能力。

## 目标

建立一个升级友好、职责清晰、用户体验稳定的迁移方案，使得：

- `MedAutoScience` 成为顶层入口与通用治理层
- `DeepScientist` 退回为底层 runtime 依赖
- 专病 workspace 只承载课题资产和一层很薄的本地入口脚本
- `002` 保持维护态兼容
- 下一篇新论文从立项开始默认使用 `MedAutoScience`

## 非目标

- 本轮不重写 `DeepScientist core`
- 本轮不强制迁移 `002` 的全部运行路径
- 本轮不把专病特异的假设、变量设计、终点定义上升为平台默认规则

## 必须兼容清单

迁移后不允许功能降级的能力包括：

1. `publication_gate`
2. `medical_publication_surface`
3. `runtime_watch`
4. `submission_minimal`
5. `study_delivery_sync`
6. 浅路径正式交付目录：
   - `studies/<study-id>/manuscript/`
   - `studies/<study-id>/artifacts/final/`
7. `profile/bootstrap/overlay` 驱动的医学治理入口

其中，前四项在 `MedAutoScience` 已有基础实现；`study_delivery_sync` 与正式交付 contract 的完整接管仍需本轮补齐。

## 浅路径交付物兼容矩阵

不能只要求 `studies/<study-id>/.../final/` 目录存在，还必须冻结最小文件级 contract。

### `submission_minimal` 阶段

- `studies/<study-id>/manuscript/manuscript.docx`
- `studies/<study-id>/manuscript/paper.pdf`
- `studies/<study-id>/manuscript/submission_manifest.json`
- `studies/<study-id>/manuscript/delivery_manifest.json`
- `studies/<study-id>/artifacts/final/figures/*`
- `studies/<study-id>/artifacts/final/tables/*`

### `finalize` 阶段额外要求

- `studies/<study-id>/manuscript/SUMMARY.md`
- `studies/<study-id>/manuscript/status.md`
- `studies/<study-id>/manuscript_claim_ledger.md`
- `studies/<study-id>/manuscriptize_resume_packet.md`
- `studies/<study-id>/artifacts/final/paper_bundle_manifest.json`
- `studies/<study-id>/artifacts/final/compile_report.json`

### `delivery_manifest.json` 最小 schema

- `schema_version`
- `generated_at`
- `stage`
- `study_id`
- `quest_id`
- `source.paper_root`
- `source.worktree_root`
- `targets.study_root`
- `targets.manuscript_root`
- `targets.artifacts_final_root`
- `copied_files[]`

## 设计原则

### 1. 平台与课题分层

`MedAutoScience` 只放跨课题、跨专病可复用的能力：

- controller
- adapter
- overlay
- policy
- study archetype
- CLI 入口
- publication/delivery 工作流

`workspace` 只放课题资产：

- `studies/*`
- `portfolio/*`
- `ops/deepscientist/startup_*`
- 本地课题文档
- 一层很薄的本地调用脚本

### 2. 用户入口稳定

用户不应在日常工作时同时在脑中切换：

- `workspace/ops/deepscientist/controllers/*.py`
- `python -m med_autoscience...`
- `DeepScientist` 自己的 runtime 路径

因此，专病 workspace 需要保留一层本地入口，例如：

- `ops/medautoscience/bin/show-profile`
- `ops/medautoscience/bin/bootstrap`
- `ops/medautoscience/bin/watch-runtime`
- `ops/medautoscience/bin/publication-gate`
- `ops/medautoscience/bin/medical-surface`
- `ops/medautoscience/bin/export-submission`
- `ops/medautoscience/bin/sync-delivery`

这些脚本内部再去调用 `MedAutoScience`。

规范命令映射如下：

| workspace wrapper | MedAutoScience CLI | legacy 路径 |
| --- | --- | --- |
| `bin/show-profile` | `show-profile --profile ...` | 无 |
| `bin/bootstrap` | `bootstrap --profile ...` | 无 |
| `bin/watch-runtime` | `watch --runtime-root ...` | `runtime_watch_controller.py` |
| `bin/publication-gate` | `publication-gate --quest-root ...` | `publication_gate_controller.py` |
| `bin/medical-surface` | `medical-publication-surface --quest-root ...` | `medical_publication_surface_controller.py` |
| `bin/export-submission` | `export-submission-minimal --paper-root ...` | `submission_minimal_export.py` |
| `bin/sync-delivery` | `sync-study-delivery --paper-root ...` | `study_delivery_sync.py` |

其中：

- `export-submission` 是 workspace wrapper 名
- `export-submission-minimal` 是平台 CLI 规范名
- `sync-delivery` 只作为手工补同步或补救入口，不替代自动同步 contract

### 3. 兼容优先于洁癖式重构

`002` 已经形成了一套真实使用过的论文生产链。
迁移时应优先保住行为，而不是追求一次性结构最漂亮。

因此本轮优先顺序是：

1. 把缺失但关键的交付链路收回 `MedAutoScience`
2. 给 workspace 建立新的薄入口层
3. 用文档和配置明确“平台逻辑”和“课题逻辑”的分界

### 4. 配置显式化，禁止隐式猜测

workspace 本地脚本不允许通过搜索父目录或读取全局默认来“猜”平台 repo。

必须显式声明：

- `MedAutoScience` checkout 路径
- workspace-local profile 路径
- overlay scope

缺失配置时应 fail-fast，而不是悄悄落到全局路径。

## 迁移期策略

`002-early-residual-risk` 进入维护态之前，旧 `ops/deepscientist/controllers/*.py` 与现有 closeout 自动同步路径继续视为冻结兼容 shim。

这意味着：

- 旧路径在 `002` 维护期内仍被允许使用
- 不再优先向旧路径新增通用功能
- 所有新能力优先落到 `MedAutoScience`
- 当 `002` 退出维护态后，再评估 legacy shim 的退役窗口

## 自动同步 contract

### `submission_minimal`

`export-submission-minimal` 成功后，如果能够解析到 study 上下文，必须自动执行 `study_delivery_sync(stage="submission_minimal")`。

换句话说：

- 导出投稿最小包
- 生成 `submission_manifest.json`
- 自动抬升到浅路径 `studies/<study-id>/.../final/`

应属于同一条正式交付链，而不是两个分离的人手步骤。

`sync-delivery` 仅保留为补同步、补救或人工修复入口。

### `finalize`

对 `002` 的现有维护兼容，保留 legacy closeout 自动同步路径。
对后续新课题，`MedAutoScience` 需要逐步接管这一 contract，避免最终 `finalize` 退化成纯手工补同步。

## 方案比较

### 方案 A：立刻要求用户直接使用 `medautosci ...`

优点：

- 平台入口最纯粹

缺点：

- 对当前 workspace 用户体验变化过大
- 不利于 `002` 维护期兼容
- 用户容易把“平台 repo 路径”和“课题目录路径”混在一起

### 方案 B：workspace 保留本地薄脚本入口，内部调用 `MedAutoScience`

优点：

- 迁移平滑
- 用户心智负担最低
- 后续新论文可直接按新入口工作
- `002` 可继续维护而不丢功能

缺点：

- 需要多维护一层非常薄的 wrapper

### 结论

采用方案 B。

## 本轮落地范围

### 子项目 1：把 `study_delivery_sync` 收回 `MedAutoScience`

原因：

- 这是“正式投稿交付物放到浅路径 final 目录”所依赖的核心链路
- 它已经在 workspace 真实使用过
- 如果这一层不回收，`MedAutoScience` 还不能算真正接管交付层

交付形式：

- 新增 `src/med_autoscience/controllers/study_delivery_sync.py`
- 新增测试
- 新增 CLI 子命令
- `export-submission-minimal` 自动触发 `stage="submission_minimal"` 浅路径同步

### 子项目 2：为 workspace 建立本地薄入口层

交付形式：

- `ops/medautoscience/README.md`
- `ops/medautoscience/compatibility_inventory.md`
- `ops/medautoscience/config.env`
- `ops/medautoscience/profiles/nfpitnet.workspace.toml`
- `ops/medautoscience/bin/*`

这些入口统一调用 `MedAutoScience`，而不是再直接调 workspace 里的旧 controller。
repo 定位方式必须显式配置，不能通过路径搜索隐式猜测。

### 子项目 3：形成兼容清单和经验回流规则

交付形式：

- 一份 workspace 内的迁移说明文档
- 明确哪些经验应回流到 `MedAutoScience`
- 明确哪些内容只应留在专病 workspace

## 经验回流规则

只有满足以下条件的改动，才上升到 `MedAutoScience`：

- 跨课题可复用
- 不依赖 NF-PitNET 专病特定变量语义
- 会影响默认科研治理、论文质量、或正式交付链路

以下内容默认留在 workspace：

- 终点定义
- 变量工程与临床语义映射
- 专病 backlog
- 审稿意见和具体返修策略
- 只适用于某一个数据集的经验

## 成功标准

满足以下条件即视为本轮迁移成功：

1. `MedAutoScience` 内具备 `study_delivery_sync`
2. `export-submission-minimal` 在存在 study 上下文时自动完成浅路径同步
3. `MedAutoScience` CLI 能直接跑关键 controller 与交付同步
4. `NF-PitNET workspace` 出现统一的本地薄入口层
5. `002` 不失去现有返修/补实验维护能力
6. 下一篇新论文可以从 workspace 本地入口默认走 `MedAutoScience`
