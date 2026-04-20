# 当前状态

**更新时间：2026-04-20**

## 当前角色与边界

- `OPL` 是位于 MAS 之上的家族级 gateway 与 domain handoff surface。
- `MedAutoScience` 是医学 `Research Ops` domain gateway，负责医学 study intake、workspace 语境、证据推进、进度投影和人工决策点。
- 当前正式入口继续是 `CLI`，支持协议层继续是 `MCP`，内部控制面继续是 `controller`。
- 当前产品主线保持 `Auto-only`，公开收口面集中在医学用户回路、managed runtime 监管与 product-entry bridge。
- 当前用户回路围绕 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study` 与 `study-progress` 展开；`product-entry-manifest` 与 `build-product-entry` 继续作为 machine-readable bridge。
- 上游 `Hermes-Agent` 指外部 managed runtime target 与 supervision owner；当前 repo-side seam 继续消费这条目标链路。
- 当前执行链路继续收口在 `med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist -> MedDeepScientist CodexRunner -> codex exec autonomous agent loop`。
- 从 `2026-04-18` 起，MAS 复用 `one-person-lab` 持有的 `opl-harness-shared` 来提供 managed runtime、Hermes supervision、product-entry companion 与 family orchestration helper。
- 受控 backend、runtime adapter、handoff envelope、product-entry companion、monorepo / runtime core ingest / controlled cutover 继续留在 runtime / program / reference 层阅读。
- 从当前主线判断开始，方向锁定后的普通科研推进、论文质量判断与 `bounded_analysis` 一类有限补充分析推进默认由 `MAS` 自主完成；human gate 收口到重大边界与最终投稿前审计。

## 当前可用用户回路

- 打开 MAS frontdoor：`uv run python -m med_autoscience.cli product-frontdesk --profile <profile>`
- 查看 workspace inbox：`uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>`
- 写入 study 任务：`uv run python -m med_autoscience.cli submit-study-task --profile <profile> --study-id <study_id> --task-intent '<task_intent>'`
- 启动或续跑 study：`uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>`
- 查看当前进度：`uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>`

这条回路是当前公开推荐路径：`direct MAS entry / OPL handoff -> product-frontdesk -> workspace-cockpit -> submit-study-task -> launch-study -> study-progress`。
`product-entry-manifest` 与 `build-product-entry` 继续作为 OPL / agent 消费的 machine-readable bridge，公开叙事不再把它们放在用户认知中心。

## 当前执行与监管模型

- 默认 executor：`codex_cli_autonomous`，模型和 reasoning effort 继承本机 Codex 默认配置。
- 默认人机界面：`CLI` / `MCP` / `controller` 三层 formal entry 驱动 MAS 的 `medautosci` surfaces。
- 长期在线监管：repo-side supervision surface 持续检查外部 runtime 证据与恢复语义。
- 受控 backend：`MedDeepScientist` 仍作为当前 internal research backend，公开路径继续围绕 study/workspace truth 组织。
- 关键 durable surfaces：`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json`、`controller_decisions/latest.json`。
- 关键身份：`program_id`、`study_id`、`quest_id`、`active_run_id`。公开用户面优先展示 `study_id`、任务摘要、监管 freshness、阻塞和下一步。

## 内部参考边界

- 历史程序命名、迁移记录与运行边界形成过程继续留在 runtime / program 文档中，用于维护者追溯当前边界如何形成。
- `OPL -> Med Auto Science` integration contract、`build-product-entry`、handoff envelope、family product-entry manifest companion 属于 machine-readable bridge 和 internal reference。
- `Domain Harness OS`、runtime owner、outer runtime substrate owner、backend deconstruction、physical monorepo absorb 继续留在 reference / program 层。
- 医学展示 / 论文配图资产化是独立 capability line，仍不改写 MAS 研究任务回路。

## 当前维护重点

1. 把 `README*`、`docs/status.md`、`docs/README*` 继续保持为 OPL/MAS/Hermes 的用户认知入口。
2. 继续把 `docs/project.md`、`docs/architecture.md`、`mainline-status` 与 `product-entry-manifest` payload 保持在同一入口模型上。
3. 保持 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 作为 MAS 的核心可执行回路。
4. 保持 `Hermes-Agent` 作为外部长期在线网关的 readiness 检查，并把维护者细节继续留在 reference / program 层。
5. 把“医学论文质量 + 长时间全自动驾驶优化”正式收口到 `MAS` 单项目主线，由 `controller_charter / runtime / eval_hygiene` 共同承担 owner；`MDS` 迁移期角色收敛为 research backend、行为等价 oracle、上游 intake buffer，详见 [MAS Single-Project Quality And Autonomy Mainline](./program/mas_single_project_quality_and_autonomy_mainline.md)。
6. 把 study charter 升级为质量总合同入口；`paper evidence ledger` 与 `review ledger` 作为该合同的执行与审阅记录，统一承载主结果、`bounded_analysis`、reviewer concern 与 submission hygiene 的落地状态。
