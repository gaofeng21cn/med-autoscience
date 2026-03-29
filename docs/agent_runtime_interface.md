# Agent Runtime Interface

这份文档写给 `Codex` 等 Agent 以及需要审阅 Agent 行为的技术合作者。

`MedAutoScience` 对外可以继续称为医学自动科研平台，但它的本质是一个 `Agent-first, human-auditable` 的医学自动科研运行层：

- 人类负责提出研究任务、提供数据、审阅结果和做关键决策
- Agent 负责调用稳定接口，推进数据治理、研究执行和论文交付组织
- 平台负责提供可验证、可审计、可重复调用的运行入口，而不是要求医学用户手工维护底层状态

如果你是医学用户，希望先理解这个项目是什么、适合什么课题、能产出什么，请先看仓库首页 [README.md](../README.md)。

## 技术入口路径

根据任务类型，从这里继续进入：

- 工作区接入与部署：[`bootstrap/README.md`](../bootstrap/README.md)
- 控制器与内部能力：[`controllers/README.md`](../controllers/README.md)
- 数据资产策略：[`policies/data_asset_management.md`](../policies/data_asset_management.md)
- 默认研究场景：[`policies/study_archetypes.md`](../policies/study_archetypes.md)
- 研究路线偏置：[`policies/research_route_bias_policy.md`](../policies/research_route_bias_policy.md)

## 运行层分工

在这个运行层里，不建议把人类和 Agent 的职责混在一起：

- 人类定义研究目标、确认课题边界、提供或授权数据、审阅研究输出、决定是否继续推进
- Agent 负责调用 CLI 和稳定接口，组织数据资产、推进研究阶段、收敛论文交付
- 技术同事负责接入 workspace、核对 profile、维护实现层与 controller 行为

因此，README 首页不再承担“教人逐条执行命令”的职责；命令、payload 和运行约束统一收在这份文档里，供 Agent 调用和人类审计。

## 接口使用原则

Agent 调用接口时，优先遵守以下顺序：

1. 先读状态，再做变更
2. 优先使用平台提供的稳定入口，不直接改底层状态文件
3. 把可审计结果落到 workspace 中，而不是只停留在会话上下文
4. 变更数据资产时，优先使用统一 mutation 入口，而不是散落地手工更新多个文件

对数据资产相关任务，通常先读这些状态：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli data-assets-status --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli assess-data-asset-impact --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli validate-public-registry --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli startup-data-readiness --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli tooluniverse-status --workspace-root /path/to/workspace
PYTHONPATH=src python3 -m med_autoscience.cli data-asset-gate --quest-root /path/to/runtime/quests/<study-id>
```

如果需要初始化数据资产层，可用：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli init-data-assets --workspace-root /path/to/workspace
```

如果需要比较私有数据版本差异，可用：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli diff-private-release --workspace-root /path/to/workspace --family-id master --from-version v2026-03-28 --to-version v2026-04-10
```

## 统一 mutation 入口

当 Agent 需要对数据资产注册表施加可审计变更时，优先使用统一 mutation 入口：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli apply-data-asset-update --workspace-root /path/to/workspace --payload-file /tmp/data_update.json
```

这个入口适合：

- 新增或更新 public dataset 登记
- 新增或更新 private release manifest
- 需要把变更操作作为正式审计记录落盘

这个入口不适合：

- 用来替代所有只读查询
- 把随意的自由文本状态塞进 registry
- 绕过既有 policy 或 release contract，直接做无边界写入

简单说，先判断是不是“要改 registry 状态”；如果不是，先用只读命令。只有当 Agent 需要提交一笔可审计的数据资产变更时，才进入 mutation 流程。

Agent 驱动的数据更新审计会写到：

- `portfolio/data_assets/mutations/`

私有版本差异报告默认写到：

- `portfolio/data_assets/private/diffs/`

startup 阶段的数据准备度摘要默认写到：

- `portfolio/data_assets/startup/latest_startup_data_readiness.json`

quest 级 `data-asset-gate` 采用双层信号：

- 私有数据过期或 release contract 未闭合：`hard block`
- public-data 扩展机会：`advisory`

因此，不要把 public-data 扩展机会误当成必须立刻中断主实验的阻断信号。

## mutation payload 示例

### 示例 1：登记 public dataset

```json
{
  "action": "upsert_public_dataset",
  "dataset": {
    "dataset_id": "geo-gse000001",
    "source_type": "GEO",
    "accession": "GSE000001",
    "roles": ["external_validation"],
    "target_families": ["master"],
    "target_study_archetypes": ["clinical_classifier"],
    "status": "candidate",
    "rationale": "Candidate external validation cohort."
  }
}
```

### 示例 2：登记 private release manifest

```json
{
  "action": "upsert_private_release_manifest",
  "family_id": "master",
  "version_id": "v2026-04-10",
  "manifest": {
    "dataset_id": "nfpitnet_master",
    "raw_snapshot": "followup_refresh",
    "generated_by": "pipeline/v2.py",
    "main_outputs": {
      "analysis_csv": "analysis.csv"
    },
    "release_contract": {
      "update_type": ["followup_refresh"],
      "qc_status": "locked"
    }
  }
}
```

这些 payload 是接口示例，不是给医学用户手工填写的表单。Agent 在构造 payload 前，应先确认：

- 当前变更是否确实属于 registry 更新
- 目标 dataset family、study archetype 或 dataset id 是否有明确归属
- 写入后是否能被人类审阅和追踪

## workspace / profile / bootstrap 衔接

Agent 在真正推进研究前，应先确认 workspace 已正确接入。最短路径是：

1. 阅读并准备 [`bootstrap/README.md`](../bootstrap/README.md) 中的 profile 和 workspace 要求
2. 用 `doctor` 检查 `workspace_root`、`runtime_root`、`studies_root`、`portfolio_root`、`deepscientist_runtime_root`
3. 用 `bootstrap` 初始化 overlay 和数据资产层

典型命令如下：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli bootstrap --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli overlay-status --profile profiles/my-study.local.toml
```

如果这些环境还没接好，不要急着调用研究阶段接口，因为很多状态落盘路径都依赖 workspace contract。

## 审计与人类复核

`human-auditable` 不等于“人类手工逐条执行命令”，而是：

- Agent 所做的变更有明确接口和落盘位置
- 人类可以审阅数据资产变化、研究阶段输出和最终交付材料
- 关键继续/停止决策仍由人类负责

因此，推荐的工作方式是：

1. 人类定义研究目标和边界
2. Agent 调用运行层接口推进
3. 平台把关键状态和结果落盘
4. 人类基于这些审计痕迹做关键判断
