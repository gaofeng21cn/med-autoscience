# Bootstrap

这份说明主要写给 Codex 或其他 AI 执行者。

目标是让一台新电脑尽快具备运行 `MedAutoScience` 的基本条件，而不是在界面里手动点来点去。

## 预期前提

- 仓库已 clone 到本机任意工作目录
- Python：`>= 3.12`
- 本机已具备可用的 `DeepScientist` 与 `Codex` 环境
- 已存在一个具体医学研究 workspace，里面至少有：
  - `studies/`
  - `portfolio/`
  - `ops/deepscientist/runtime/`
  - 若要启用 finalize 的浅路径正式交付 contract，还需要 `ops/medautoscience/bin/sync-delivery`

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
- `default_publication_profile`
- `default_citation_style`
- `enable_medical_overlay`
- `medical_overlay_skills`

建议做法：

```bash
cd med-autoscience
cp profiles/workspace.profile.template.toml profiles/my-study.local.toml
```

然后编辑：

- [workspace.profile.template.toml](../profiles/workspace.profile.template.toml)

注意：

- `profiles/*.local.toml` 是本机私有配置，不应提交到公开仓库
- 仓库本身只保留模板，不保留真实路径

### 4. 运行 doctor

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/my-study.local.toml
```

期望看到：

- `workspace_exists: true`
- `runtime_exists: true`
- `studies_exists: true`
- `portfolio_exists: true`
- `deepscientist_runtime_exists: true`

### 5. 显示 profile

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli show-profile --profile profiles/my-study.local.toml
```

### 6. 执行 bootstrap

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli bootstrap --profile profiles/my-study.local.toml
```

这一步当前会做三件事：

- 检查 profile 指向的 workspace / runtime 是否可见
- 按 profile 中声明的 `medical_overlay_skills` 安装并校验医学 overlay
- 初始化并汇总数据资产状态，包括 private release、public registry、study impact 和 startup data readiness

如果想单独重跑数据资产层，也可以继续显式执行：

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli init-data-assets --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli data-assets-status --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli assess-data-asset-impact --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli validate-public-registry --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli startup-data-readiness --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli diff-private-release --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE --family-id master --from-version v2026-03-28 --to-version v2026-04-10
PYTHONPATH=src python3 -m med_autoscience.cli tooluniverse-status --workspace-root /ABS/PATH/TO/MEDICAL-WORKSPACE
PYTHONPATH=src python3 -m med_autoscience.cli data-asset-gate --quest-root /ABS/PATH/TO/MEDICAL-WORKSPACE/ops/deepscientist/runtime/quests/<study-id>
```

如果只想单独检查或重覆写 overlay，也可以直接运行：

```bash
cd med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli overlay-status --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli install-medical-overlay --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli reapply-medical-overlay --profile profiles/my-study.local.toml
```

## 当前范围

现在的 bootstrap 还不是“一键安装全部依赖”的最终版。

当前它能保证的是：

- 仓库结构已经独立
- profile 机制已经可用
- AI 可以先确认目标 workspace 是否接入正确
- AI 可以按 profile 自动接管医学 stage overlays（通常以 workspace 作用域部署，因此 overlay 只影响当前研究，不污染全局）
- AI 可以初始化并检查 `portfolio/data_assets/` 下的数据资产层，并在启动时直接生成 `startup_data_readiness` 摘要
- AI 可以通过 CLI 调用关键 controller 与 `sync-study-delivery`，并且当 finalized paper bundle 已经形成 `submission_minimal` 时，finalize stage 的 overlay skill 会自动调度 `study_delivery_sync(stage="finalize")`，把论文交付、总结与 proofing 材料同步到 `studies/<study-id>/…/final`，使正式交付流程完全在平台内闭环

后续会继续补：

- 一键 bootstrap 脚本
- workspace-local thin entry layer 的模板化与自动生成
- 新课题启动/选题的统一入口
