# Agent Runtime Interface

这份文档写给 `Codex` 等 Agent、内部技术合作者，以及需要审阅 Agent 行为的人。

它属于仓库跟踪的运行面文档层，因此收口在 `docs/runtime/`，但不属于首页默认双语公开面。
与之相对，`docs/superpowers/` 更偏本地内部设计稿、plan、spec 和 agent 工作过程产物，不作为公开主入口。
如果未来要把这份文档提升到默认公开面，必须同步提供英文 `.md` 与中文 `.zh-CN.md` 镜像。

`MedAutoScience` 对外可以继续称为医学自动科研平台，但更准确的理解是：它对外是 `Research Ops Gateway`，对内由一个 `Agent-first, human-auditable` 的医学自动科研 harness 驱动：

- 人类负责提出研究任务、提供数据、审阅结果和做关键决策
- Agent 负责调用稳定接口，推进数据治理、研究执行和论文交付组织
- 平台负责提供可验证、可审计、可重复调用的 gateway 入口，而不是要求医学用户手工维护底层状态

当前默认本地执行形态仍是 `Codex-default host-agent runtime`。

当前 formal-entry matrix 继续固定为：

- `default_formal_entry`：`CLI`
- `supported_protocol_layer`：`MCP`
- `internal_controller_surface`：`controller`

其中：

- `CLI-first` 指的是 Agent runtime 的默认正式入口
- `MCP` 是兼容的协议层，不改写 `CLI-first` 的默认入口语义
- `controller` 属于内部控制面，不与 `CLI`、`MCP` 并列作为对外 formal entry
- 当前 repo-tracked 产品主线按 `Auto-only` 理解；未来若做 `Human-in-the-loop` 产品，应作为兼容 sibling 或 upper-layer product 复用同一 substrate

## 当前主线与 monorepo 长线的关系

当前这条 repo-tracked 主线，优先级仍然是：

- 保持 `MedAutoScience -> MedDeepScientist` runtime contract 稳定
- 保持 execution handle、durable surface 与 fail-closed gate semantics 不漂移
- 在 external runtime gate 清除前，以手工测试驱动稳定化，而不是重开新的大架构 tranche

这不等于 monorepo 目标取消。

`monorepo / runtime core ingest / controlled cutover` 仍然是 `MedAutoScience` 的明确长线，目标仍是把系统按三块主模块收进同一 repo：

- `controller_charter`
- `runtime`
- `eval_hygiene`

但这条长线当前不属于四仓统一 `Phase C` 的直接交付。
在 external runtime gate、对象边界、报告边界与 `controller_charter / runtime / eval_hygiene` 防火墙继续稳定前，不应提前进入 physical migration、cross-repo refactor 或 scaffold cutover。

## Execution Handle 与 Durable Surface

当前主线下，Agent 不应把所有运行身份混写成一个“run id”。

必须至少区分：

- `program_id`
  - 当前 `research-foundry-medical-mainline` 的 control-plane / report-routing 指针
  - 默认回写到 `.omx/context/CURRENT_PROGRAM.md` 与 `.omx/reports/<program_id>/`
- `study_id`
  - study 聚合根身份
  - 对应 `studies/<study_id>/`
- `quest_id`
  - 受控 `MedDeepScientist` managed quest 的正式运行句柄
  - 对应 `ops/med-deepscientist/runtime/quests/<quest_id>/`
- `active_run_id`
  - 当前 live daemon run 的细粒度执行句柄
  - 只在 live execution / runtime audit 场景里出现

当前 canonical durable surface 至少包括：

- `study_runtime_status`
- `runtime_watch`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
- `studies/<study_id>/artifacts/runtime/last_launch_report.json`

这意味着：

- `publication_eval` 必须继续落在 study-owned latest surface，而不是回写到 runtime 临时目录
- `runtime_escalation_record` 与 `runtime_watch` 继续是 quest-owned runtime artifact
- `controller_decisions/latest.json` 是 study-owned outer-loop / controller decision surface
- `.omx/` 继续只承载机器本地 handoff，不替代 repo-tracked runtime truth

如果你是医学用户，希望先理解这个项目是什么、适合什么课题、能产出什么，请先看仓库首页 [README.md](../README.md)。

## 技术入口路径

根据任务类型，从这里继续进入：

- 工作区接入与部署：[`bootstrap/README.md`](../bootstrap/README.md)
- workspace 标准架构与 legacy 迁移：[`workspace_architecture.md`](./workspace_architecture.md)
- `main` 合并门与现网切换门：[`merge_and_cutover_gates.md`](./merge_and_cutover_gates.md)
- external runtime blocker package：[`../program/external_runtime_dependency_gate.md`](../program/external_runtime_dependency_gate.md)
- external gate 未清除前的手工测试与 repo-side 稳定化清单：[`manual_runtime_stabilization_checklist.md`](../program/manual_runtime_stabilization_checklist.md)
- `Phase 6` 当前 repo-tracked activation baseline：[`integration_harness_activation_package.md`](./integration_harness_activation_package.md)
- `MedAutoScience` / `MedDeepScientist` 边界：[`runtime_boundary.md`](./runtime_boundary.md)
- 运行句柄与持久表面合同：[`runtime_handle_and_durable_surface_contract.md`](./runtime_handle_and_durable_surface_contract.md)
- managed study runtime 状态机与执行 contract：[`study_runtime_orchestration.md`](./study_runtime_orchestration.md)
- 上游 intake 与 fork 升级流程：[`upstream_intake.md`](./upstream_intake.md)
- 控制器与内部能力：[`controllers/README.md`](../controllers/README.md)
- 数据资产策略：[`policies/data_asset_management.md`](./policies/data_asset_management.md)
- 默认研究场景：[`policies/study_archetypes.md`](./policies/study_archetypes.md)
- 研究路线偏置：[`policies/research_route_bias_policy.md`](./policies/research_route_bias_policy.md)
- sidecar provider 与 figure routes 指南：[`sidecar_figure_routes.md`](./sidecar_figure_routes.md)
- 第三方 Agent 入口模式：[`agent_entry_modes.md`](./agent_entry_modes.md)

## 第三方 Agent 入口资产

当前对外按兼容消费来表达的 Agent 包括：`Codex`、`Claude Code`、`OpenClaw`。

如果你需要把 `MedAutoScience` 的入口契约直接交给受控 Agent 或内部技术协作者，而不是只让它阅读 README，可优先使用这些仓库跟踪资产：

- 入口模式契约：[`agent_entry_modes.md`](./agent_entry_modes.md)
- 机器可读镜像：[`../templates/agent_entry_modes.yaml`](../templates/agent_entry_modes.yaml)
- `Codex` 入口模板：[`../templates/codex/medautoscience-entry.SKILL.md`](../templates/codex/medautoscience-entry.SKILL.md)
- `OpenClaw` 入口模板：[`../templates/openclaw/medautoscience-entry.prompt.md`](../templates/openclaw/medautoscience-entry.prompt.md)

`Claude Code` 不单独维护专有入口模板，默认复用 `Codex` 这一套入口契约。

这些资产只负责声明：

- 哪些模式默认走 `managed`
- 哪些模式默认走 `lightweight`
- 何时需要从轻量专项模式升级为正式纳管模式
- 每个模式可调用的 entry actions、研究 routes、governance routes 和 auxiliary routes

“先定目标期刊，再反推选题和数据要求”的前置规划任务，不单独拆成第六类正式入口。
这类任务默认仍属于轻量专项模式，通常组合使用 `literature_scout`、`idea_exploration`、`decision`，并在需要把目标期刊要求解析为正式约束时调用 `journal-resolution`；其交付应停在数据建议要求清单，而不是从这个场景直接升级到正式 managed 研究。

如果你只是做一次性的文献调研、思路启发、补实验判断或稿件整理，Agent 可以直接按轻量专项模式调用相应 route。
如果任务已经进入需要正式纳管的自动科研推进，则应按契约先走 `doctor -> bootstrap -> overlay-status`，再进入对应 managed route。

## 唯一研究入口

在当前架构里，`MedAutoScience` 是唯一研究入口和 `Research Ops Gateway`，`MedDeepScientist`（仓库名 `med-deepscientist`）是默认受控 runtime；`DeepScientist` 只在上游比较、兼容审计和历史命名里单独出现。

因此：

- Agent 不应直接调用 `MedDeepScientist` daemon HTTP API 发起 quest
- Agent 不应把 `MedDeepScientist` UI / CLI 当成研究入口
- `ops/med-deepscientist/bin/*` 只用于 runtime 运维，不用于研究治理
- 所有正式研究推进都应经由 `doctor`、`bootstrap`、`overlay-status`、`ensure-study-runtime` 和受管 route

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
3. 不直接调用 `MedDeepScientist` daemon API，也不绕过 `MedAutoScience` controller
4. 把可审计结果落到 workspace 中，而不是只停留在会话上下文
5. 变更数据资产时，优先使用统一 mutation 入口，而不是散落地手工更新多个文件

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
2. 用 `doctor` 检查 `workspace_root`、`runtime_root`、`studies_root`、`portfolio_root`、`med_deepscientist_runtime_root`
3. 用 `bootstrap` 初始化 overlay 和数据资产层

典型命令如下：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli bootstrap --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli overlay-status --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli med-deepscientist-upgrade-check --profile profiles/my-study.local.toml --refresh
```

如果这些环境还没接好，不要急着调用研究阶段接口，因为很多状态落盘路径都依赖 workspace contract。

## MedDeepScientist 上游升级检查

当 Agent 发现 `MedDeepScientist` 所跟踪的 upstream `DeepScientist` 有新提交，或者准备把本机运行时切到新的 intake 版本时，不应直接原地升级。推荐先执行：

```bash
PYTHONPATH=src python3 -m med_autoscience.cli med-deepscientist-upgrade-check --profile profiles/my-study.local.toml --refresh
```

这个检查会统一汇总：

- `repo_check`
  - `med_deepscientist_repo_root` 是否已配置
  - 目标目录是否存在、是否是 Git repo
  - 当前 branch、`HEAD`、comparison ref
  - 相对 comparison ref 的 `ahead_count / behind_count`
  - 当前工作树是否干净
  - 如果目标 repo 根目录存在 `MEDICAL_FORK_MANIFEST.json`，则额外暴露受控 fork manifest：
    - `engine_family`
    - `freeze_base_commit`
    - `applied_commits`
    - `is_controlled_fork`
    - `upstream_remote_name`
    - `upstream_ref`
- `workspace_check`
  - 当前 workspace / runtime / MedDeepScientist runtime contract 是否仍然完整
- `overlay_check`
  - 医学 overlay 是否仍然全部处于 `overlay_applied`

核心目标是把“上游有更新”与“现在适合升级”分开判断。

典型 `decision` 含义如下：

- `upgrade_available`
  - upstream 有新提交，且当前 repo / workspace / overlay 状态允许进入升级流程
- `needs_branch_review`
  - 当前 checkout 不在稳定主线；如果只是受控 fork 的 `main` 保留了经过审计的领先提交，这一项不应触发
- `blocked_dirty_repo`
  - 本地 `MedDeepScientist` repo 有未提交改动，应先清理
- `overlay_reapply_needed`
  - 当前没有 upstream 更新，但医学 overlay 已不再处于理想状态，应先重覆写
- `up_to_date`
  - 当前既没有检测到 upstream 更新，也没有 overlay 漂移

对于 Agent 来说，推荐流程是：

1. 先跑 `med-deepscientist-upgrade-check`
2. 只在结果明确允许时，才去更新 `MedDeepScientist` 运行时
3. 更新后重新跑 `med-deepscientist-upgrade-check`
4. 必要时执行 `reapply-medical-overlay`
5. 最后再执行一次 `bootstrap` 或至少 `overlay-status`

普通的非 fork 仓库可以继续把 `origin/main` 作为默认的 comparison ref，当前 `med-deepscientist-upgrade-check` 也会以这个 ref 作为比较基础。

如果目标 repo 是受控 fork，`recommended_actions` 可能返回 `run_controlled_fork_intake_workflow`，表示应走 intake 流程，而不是直接对稳定线执行 `pull origin main`。

对于受控 fork，推荐的 remote 语义应固定为：

- `origin` 指向 fork 自己的 GitHub 主仓，其 `main` 维护 fork 的稳定线和 intake 合并点
- `upstream` 指向 `DeepScientist` 上游仓库，所有兼容审计、`med-deepscientist-upgrade-check` 等命令都应以 `upstream/main` 作为 comparison ref

## Phase 1 gate 与真实执行

当前所谓 Phase 1 已经允许把 `med_deepscientist_repo_root` 指向一个受控的 sibling fork，例如本地 checkout 或 GitHub repo `med-deepscientist`；它对外的产品名是 `MedDeepScientist`。当前主链已经把 `adapters/deepscientist/*` 退出正式运行面，但这仍不等于 `MedAutoScience` 已经完成 engine-neutral runtime 切换。`med_deepscientist_repo_root` 现阶段主要仍服务于 `med-deepscientist-upgrade-check` 这类审计与升级流程；如果 repo 根目录存在 `MEDICAL_FORK_MANIFEST.json`，系统会把它识别为受控 fork 并暴露 manifest 元数据。与此同时，`ops/med-deepscientist/behavior_equivalence_gate.yaml` 仍是关键 gate artifact，`med_autoscience.workspace_contracts.inspect_behavior_equivalence_gate` 依赖其中的 `schema_version`、`phase_25_ready` 与 `critical_overrides`，后者通常指向 site-packages 级别的本地改动。

只要 `phase_25_ready=false`，`med-deepscientist-upgrade-check` 就会在 `workspace_check.behavior_gate` 里产生 `blocked_behavior_equivalence_gate` / `behavior_gate.phase_25_ready_false`，同时 `repo_check` 和 `overlay_check` 会被 `blocked_by_behavior_equivalence_gate` 的 skip 逻辑挡住，因此不能据此宣称“已经完成 execution truth 切换”。受控 fork manifest 只能说明 repo 身份已开始受控，不能替代 Phase 2.5 行为等价门。只有当 `behavior_equivalence_gate.yaml` 把 `phase_25_ready` 设为 `true`、`critical_overrides` 清单里的 site-packages 补丁已经被正式迁移，并且 gate 通过后，才可以在 Phase 2/3 把 `med_deepscientist_repo_root` 视作真正的执行真相来源。

## Runtime Protocol Surface

Phase 2 开始，`MedAutoScience` 明确把 runtime 布局与 quest 状态解析提升为自己的协议层，而不是继续散落在 controller 或 adapter 里。

- `med_autoscience.runtime_protocol.layout`
  - 负责 workspace 内 `ops/med-deepscientist/`、runtime root、quests root、startup brief / payload root、behavior gate 等 project-local runtime 路径契约
  - `study_runtime_router`、`workspace_contracts`、`workspace_init` 等 controller / scaffold 代码应统一经由这层派生路径，而不是散落硬编码 `ops/med-deepscientist/...`
- `med_autoscience.runtime_protocol.topology`
  - 负责 `paper_root`、`worktree_root`、`quest_root`、`study_root` 之间的关系解析
  - 当前显式承认的受管布局是 `ops/med-deepscientist/runtime/quests/<quest_id>/.ds/worktrees/<worktree>/paper`
  - `study_delivery_sync` 这类 controller 应调用 `resolve_paper_root_context()`，而不是自己拼 `.ds/worktrees/...` 或依赖 `parents[4]` 这类脆弱层级
- `med_autoscience.runtime_protocol.quest_state`
  - 负责 `runtime_state.json`、quest status、active quest 枚举、main `RESULT.json`、active `stdout.jsonl` 与最近 stdout 行的统一读取
  - `publication_gate`、`runtime_watch`、`study_runtime_router` 这类 controller 应直接消费这一层，而不是各自重复遍历 `.ds/...`
- `med_autoscience.runtime_protocol.paper_artifacts`
  - 负责 latest `paper_root`、`paper_bundle_manifest.json`、`artifact_manifest.json`、`submission_minimal` 输出路径的统一解析
  - `publication_gate`、`medical_publication_surface`、`submission_targets` 不再自己猜测 `paper/` 下的交付拓扑
- `med_autoscience.runtime_protocol.user_message`
  - 负责 `.ds/user_message_queue.json`、`.ds/runtime_state.json` 中 `pending_user_message_count`、以及 `.ds/interaction_journal.jsonl` 的一致落盘
  - `data_asset_gate`、`figure_loop_guard`、`medical_publication_surface` 这类 controller 不再自己维护 queue/journal 真相

Phase 3 开始，transport 面也开始显式收口：

- `med_autoscience.runtime_transport.med_deepscientist`
  - 负责 daemon URL 解析、quest create / pause / resume / control 这类 engine-specific HTTP transport
  - 允许优先读取 `<runtime_root>/runtime/daemon.json` 中的 live URL，并在缺失时回退到 `<runtime_root>/config/config.yaml`
  - 不负责 quest state、artifact topology 或 user message queue 这些协议真相
  - 对 study runtime controller 来说，它仍是稳定 transport 调用面；内部若存在更薄的 controller-local seam，只属于实现层，不额外提升为公开 contract

这一步仍不等于 engine-neutral transport 已经完成；`MedAutoScience` 现在只是把 transport 显式命名出来。当前正式主链已经不再保留 `adapters/deepscientist/*` 作为运行时依赖，production code 只允许依赖 `runtime_protocol` / `runtime_transport`。

对于单个 study 的 runtime 编排，`study_runtime_router` 的稳定入口、typed surface 归属、decision 执行边界与 side-effect 约束，另见 [`study_runtime_orchestration.md`](./study_runtime_orchestration.md)。

## Target Layering

理想形态下，这个系统应收敛成 5 层，而且每层只做一类事情：

1. `policy`
   - 只表达医学治理规则、发表约束、数据资产规则、研究路线偏置
   - 不读写 runtime 文件，不发 daemon 请求
2. `controller`
   - 只负责把政策、study 状态和任务目标编排成明确动作
   - 不自己猜路径，不自己拼 `.ds/...`，不自己维护 queue 文件
3. `runtime_protocol`
   - 只负责 `MedAutoScience` 承认的 runtime 文件契约
   - 包括 topology、quest_state、paper_artifacts、user_message
   - 这是 filesystem-facing truth
4. `runtime_transport`
  - 只负责 engine-specific transport
  - 当前就是 `med_deepscientist` daemon HTTP create / pause / resume / control
  - 这是 process/network-facing truth
5. `engine`
  - 当前是受控 fork `med-deepscientist`
  - 负责真正长时运行、状态机推进、daemon、UI 与 quest 执行

对应关系应是单向的：

- `policy -> controller`
- `controller -> runtime_protocol`
- `controller -> runtime_transport`
- `runtime_transport -> engine`

`controller` 不应反向依赖 adapter，也不应直接触碰 engine 私有实现细节。

## What We Intend To Remove

沿这条主线，后面会继续优化掉这些没必要的部分：

- adapter 中重复存在的一套“第二真相”
  - 例如 `paper_bundle.py`、`mailbox.py`、`daemon_api.py`、`runtime.py` 曾分别重新承载 artifact、queue、transport、quest state 解析
- controller 内部重复的拓扑推导
  - 例如手写 `.ds/worktrees/...`、`parents[4]`、零散 `glob`
- 同一概念混放在一个文件里
  - 例如一个模块同时做本地 queue 落盘和 daemon HTTP control
- 只为兼容历史命名而保留的多层转发
  - `adapters/deepscientist/*` 已经从正式主链删除；后续不要重新引入第二套 protocol / transport 真相
- 没有必要长期保留的 `DeepScientist` 品牌耦合命名
  - 对外 profile、transport 与 workspace 路径已经统一收口到 `med_deepscientist_*`、`med_deepscientist` 与 `ops/med-deepscientist/*`
  - 剩余 legacy 命名只允许停留在上游比较语境或 runtime 兼容名里

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
