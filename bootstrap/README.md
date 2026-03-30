# Bootstrap

这份说明主要写给 Codex 或其他 AI 执行者。

目标是让一台新电脑尽快具备运行 `MedAutoScience` 的基本条件，而不是在界面里手动点来点去。

`MedAutoScience` 默认按 `Agent-first, human-auditable` 设计：

- Agent 调用 CLI / controller 作为稳定执行面
- 人类主要提供任务、数据和审阅反馈
- 底层状态更新应优先通过结构化 payload 驱动，而不是直接手改 registry

因此，这里的 bootstrap 说明主要是给 Agent 看“如何接入并接管一个医学 workspace”，不是要求医生自己维护运行细节。

## 先建立正确心智模型

这里的默认单位是“病种级 workspace”，不是“单篇论文目录”。

- 一个 workspace 负责管理同一病种的一批私有/公开数据资产
- 一个 workspace 可以并行推进多个 `study`
- `bootstrap` 发生在 workspace 级，不是某个单独 study 级
- `study` 消费 workspace 已登记的数据版本，并收敛出自己的稿件与交付物

## 预期前提

- 仓库已 clone 到本机任意工作目录
- Python：`>= 3.12`
- 本机已具备可用的 `DeepScientist` 与 `Codex` 环境
- 已存在一个病种级医学研究 workspace，里面至少有：
  - `datasets/`
  - `contracts/`
  - `studies/`
  - `portfolio/`
  - `ops/medautoscience/`
  - `ops/deepscientist/runtime/`
  - 若要启用 finalize 的浅路径正式交付 contract，还需要 `ops/medautoscience/bin/sync-delivery`

## 新病种 workspace 的最小骨架

如果你是新建一个疾病项目，推荐最小骨架如下：

```text
<workspace>/
├── datasets/
├── contracts/
├── studies/
├── portfolio/
│   └── data_assets/
├── refs/
└── ops/
    ├── medautoscience/
    │   ├── bin/
    │   ├── profiles/
    │   ├── config.env
    │   └── README.md
    └── deepscientist/
        ├── bin/
        ├── config.env
        ├── runtime/
        ├── startup_briefs/
        └── startup_payloads/
```

这里需要注意：

- 这是病种级顶层目录，不是某一篇论文自己的目录
- 可以先有空的 `studies/`，并不要求创建 profile 时就已经有首个 study
- 不要在每个病种 workspace 里再 clone 一份 `DeepScientist`

## 最小部署步骤

### 1. clone 仓库

```bash
git clone <repo-url> med-autoscience
```

### 2. 进入仓库并检查 Python

```bash
cd med-autoscience
python3 --version
```

### 3. 准备 workspace profile

复制模板并新建一个本地 `profiles/*.local.toml` 文件，至少填写：

- `name`
- `workspace_root`
- `runtime_root`
- `studies_root`
- `portfolio_root`
- `deepscientist_runtime_root`
- `deepscientist_repo_root`
- `default_publication_profile`
- `default_citation_style`
- `enable_medical_overlay`
- `medical_overlay_skills`

建议做法：

```bash
cd med-autoscience
cp profiles/workspace.profile.template.toml profiles/my-disease.local.toml
```

然后编辑：

- [workspace.profile.template.toml](../profiles/workspace.profile.template.toml)

注意：

- `profiles/*.local.toml` 是本机私有配置，不应提交到公开仓库
- 仓库本身只保留模板，不保留真实路径
- 这个 profile 描述的是病种级 workspace，而不是单篇论文

### 4. 运行 doctor

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/my-disease.local.toml
```

期望看到：

- `workspace_exists: true`
- `runtime_exists: true`
- `studies_exists: true`
- `portfolio_exists: true`
- `deepscientist_runtime_exists: true`

如果同时配置了 `deepscientist_repo_root`，`doctor` 和 `show-profile` 也会把它显示出来，方便 Agent 在升级前核对源码仓库位置。

### 5. 显示 profile

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli show-profile --profile profiles/my-disease.local.toml
```

### 6. 执行 bootstrap

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli bootstrap --profile profiles/my-disease.local.toml
```

这一步当前会做三件事：

- 检查 profile 指向的 workspace / runtime 是否可见
- 按 profile 中声明的 `medical_overlay_skills` 安装并校验医学 overlay
- 通过 controller 统一刷新并汇总数据资产状态，包括 private release、public registry、study impact 和 startup data readiness

这里的数据资产刷新是 workspace 级的：

- private release 与 public registry 都是 workspace 级登记面
- `study impact` 是“这些数据资产会影响哪些 study”
- 同一个已登记的数据版本，可以被多个 study 复用

如果想单独重跑数据资产层，也可以继续显式执行：

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli init-data-assets --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli data-assets-status --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli assess-data-asset-impact --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli validate-public-registry --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli startup-data-readiness --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli apply-data-asset-update --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE --payload-file /tmp/data_update.json
PYTHONPATH=src python3 -m med_autoscience.cli diff-private-release --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE --family-id master --from-version v2026-03-28 --to-version v2026-04-10
PYTHONPATH=src python3 -m med_autoscience.cli tooluniverse-status --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli data-asset-gate --quest-root /ABS/PATH/TO/MEDICAL-WORKSPACE/ops/deepscientist/runtime/quests/<study-id>
```

如果只想单独检查或重覆写 overlay，也可以直接运行：

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli overlay-status --profile profiles/my-disease.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli install-medical-overlay --profile profiles/my-disease.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli reapply-medical-overlay --profile profiles/my-disease.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli deepscientist-upgrade-check --profile profiles/my-disease.local.toml --refresh
```

`deepscientist-upgrade-check` 的目的不是替 Agent 直接升级 `DeepScientist`，而是在真正升级前先回答几件事：

- profile 是否已经显式绑定本机 `DeepScientist` 源码仓库
- 当前 checkout 是否是干净的 Git 工作树
- 当前 branch 是否仍然适合作为运行时主线
- `origin/main` 相对本机 checkout 是否已经有新提交
- 医学 overlay 当前是否仍处于 `overlay_applied` 状态，还是已经被 upstream 覆写或漂移

这一步的输出是机器可读 JSON，适合给 Agent 作为“现在该不该升级”的前置门控，而不是靠人工目测仓库状态。

## 新病种项目的首次启动顺序

如果你是在一台新电脑上，或第一次接入一个新病种项目，推荐顺序如下：

1. 建立病种级 workspace 骨架
2. 放入原始数据、数据说明、变量定义、终点定义与已有参考资料
3. 准备 `profiles/*.local.toml`
4. 运行 `doctor`
5. 运行 `bootstrap`
6. 再在 `studies/` 下创建首个 `study-id`，并开始 intake / scout / startup brief

也就是说，workspace 级接入和数据资产登记应先完成，再开始某一条具体研究线。

## 当前范围

现在的 bootstrap 还不是“一键安装全部依赖”的最终版。

当前它能保证的是：

- 仓库结构已经独立
- profile 机制已经可用
- AI 可以先确认目标 workspace 是否接入正确
- AI 可以按 profile 自动接管医学 stage overlays（通常以 workspace 作用域部署，因此 overlay 只影响当前研究，不污染全局）
- AI 可以初始化并检查 `portfolio/data_assets/` 下的数据资产层，并在启动时直接生成 `startup_data_readiness` 摘要
- AI 可以在 runtime 中区分 data hard block 与 public-data advisory，避免因为扩展机会本身中断主实验
- AI 可以通过 CLI 调用关键 controller 与 `sync-study-delivery`，并且当 finalized paper bundle 已经形成 `submission_minimal` 时，finalize stage 的 overlay skill 会自动调度 `study_delivery_sync(stage="finalize")`，把论文交付、总结与 proofing 材料同步到 `studies/<study-id>/…/final`，使正式交付流程完全在平台内闭环

需要明确的是，当前 Phase 1 只完成 state contract（runtime contract）、launcher contract 与 behavior equivalence gate 的审计；`deepscientist_repo_root` 仅在 `deepscientist-upgrade-check` 的 repo_check 中用作审计路径，实际执行仍可能来自 workspace 内的 `site-packages` overlay 或 legacy 补丁。为了控制何时可以把执行移动到外部 repo，workspace 需要在 `ops/deepscientist/behavior_equivalence_gate.yaml` 保留一个稳定 artifact，`med_autoscience.workspace_contracts.inspect_behavior_equivalence_gate` 会读取其中的 `schema_version`、`phase_25_ready`（布尔）与 `critical_overrides`（记录 site-packages/launcher 补丁）。只要 `phase_25_ready=false`，`deepscientist-upgrade-check` 就会返回 `blocked_behavior_equivalence_gate`/`behavior_gate.phase_25_ready_false`，在 `repo_check` 和 `overlay_check` 里直接跳过后续检查，因此不能据此宣称已经完成外部执行切换；`critical_overrides` 之所以存在，是为了让 site-packages overlay 级别的补丁有明确的迁移或替换步骤，再经过 Phase 2/2.5 逐步清理。

后续会继续补：

- 一键 bootstrap 脚本
- workspace-local thin entry layer 的模板化与自动生成
- 新课题启动/选题的统一入口
- 更高层的 Agent 调用适配，使自然语言任务更容易落到结构化 controller payload
