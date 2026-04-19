# 当前状态

**更新时间：2026-04-18**

## 当前角色与边界

- `OPL` 是顶层 GUI 与管理壳，负责把用户意图、workspace 选择、任务状态和跨 domain 导航收在一个外层入口。
- `MedAutoScience` 是 `OPL` 壳下的一级医学 domain module / agent，负责医学 study intake、workspace 语境、证据推进、进度投影和人工决策点。
- `Codex` 是 MAS 默认交互与执行表面；当前正式入口继续是 `CLI`，支持协议层继续是 `MCP`，内部控制面继续是 `controller`。
- 当前产品主线保持 `Auto-only`，当前 repo stage 继续收口在 `Phase 1 mainline established` 尾声与 `F4 blocker closeout`。
- 当前用户回路围绕 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study` 与 `study-progress` 展开；`product-entry-manifest` 与 `build-product-entry` 继续作为 machine-readable bridge。
- 上游 `Hermes-Agent` 是外部备用模式与长期在线网关，承担 supervised runtime continuity、恢复、调度和 always-on visibility。
- 当前执行链路继续收口在 `med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist -> MedDeepScientist CodexRunner -> codex exec autonomous agent loop`。
- 从 `2026-04-18` 起，MAS 复用 `one-person-lab` 持有的 `opl-harness-shared` 来提供 managed runtime、Hermes supervision、product-entry companion 与 family orchestration helper。
- `Hermes-Agent gateway cron` 是唯一长期托管入口；模型与 reasoning effort 继续继承本机 Codex 默认。
- 受控 backend、runtime adapter、handoff envelope、product-entry companion、monorepo / runtime core ingest / controlled cutover 继续留在 runtime / program / reference 层阅读。

## 当前可用用户回路

- 打开 MAS frontdoor：`uv run python -m med_autoscience.cli product-frontdesk --profile <profile>`
- 查看 workspace inbox：`uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>`
- 写入 study 任务：`uv run python -m med_autoscience.cli submit-study-task --profile <profile> --study-id <study_id> --task-intent '<task_intent>'`
- 启动或续跑 study：`uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>`
- 查看当前进度：`uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>`
- 查看 repo 阶段：`uv run python -m med_autoscience.cli mainline-status` 与 `uv run python -m med_autoscience.cli mainline-phase --phase current`

这条回路是当前公开推荐路径：`OPL shell -> MAS domain module/agent -> Codex default interaction + execution`。
`product-entry-manifest` 与 `build-product-entry` 继续作为 OPL / agent 消费的 machine-readable bridge，公开叙事不再把它们放在用户认知中心。

## 当前执行与监管模型

- 默认 executor：`codex_cli_autonomous`，模型和 reasoning effort 继承本机 Codex 默认配置。
- 默认人机界面：Codex App / Codex CLI 驱动 MAS 的 `medautosci` 命令和 MCP 工具。
- 长期在线监管：`Hermes-Agent gateway cron` 作为外部 always-on gateway；`hermes-runtime-check` 用于检查外部 runtime 证据。
- 受控 backend：`MedDeepScientist` 仍作为内部 research backend 参考，公开路径不再围绕 backend ownership 组织。
- 关键 durable surfaces：`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json`、`controller_decisions/latest.json`。
- 关键身份：`program_id`、`study_id`、`quest_id`、`active_run_id`。公开用户面优先展示 `study_id`、任务摘要、监管 freshness、阻塞和下一步。

## 内部参考边界

- 历史 tranche 命名、blocker package 与迁移 readiness 继续留在 runtime / program 文档中，用于维护者追溯当前边界如何形成。
- `OPL -> Med Auto Science` integration contract、`build-product-entry`、handoff envelope、family product-entry manifest companion 属于 machine-readable bridge 和 internal reference。
- `Domain Harness OS`、runtime owner、outer runtime substrate owner、backend deconstruction、physical monorepo absorb 继续留在 reference / program 层。
- 医学展示 / 论文配图资产化是独立 capability line，仍不改写 MAS 研究任务回路。

## 下一阶段

1. 把 `README*`、`docs/status.md`、`docs/README*` 继续保持为 OPL/MAS/Codex/Hermes 的用户认知入口。
2. 继续把 `docs/project.md`、`docs/architecture.md`、`mainline-status` 与 `product-entry-manifest` payload 保持在同一入口模型上。
3. 保持 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 作为 MAS 的核心可执行回路。
4. 保持 `Hermes-Agent` 作为外部长期在线网关的 readiness 检查，不把 backup gateway wording 重新写成用户首屏 runtime-owner 叙事。
