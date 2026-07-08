# Product 文档

Owner: `MedAutoScience`
Purpose: `domain_product_entry_support`
State: `active_support`
Machine boundary: 人读索引。可调用真相继续归 MAS app skill、CLI/MCP/API、contracts、source 与 product-entry manifests。

本目录承接 MAS direct app-skill、product-entry 与 operator 指南。它不持有 study truth、publication verdict、manuscript/package authority 或 OPL framework primitive。

当前 product / skill / workbench 默认叙事是 artifact-first paper mission：用户 entry surface 先使用 `paper-mission` / `PaperMissionRun`，next-action 展示只允许来自 canonical `NextActionEnvelope`、同 identity 的 OPL receipt 或 MAS owner consumption。用户可见 workbench / display 由 OPL hosted surface 消费 MAS refs-only projection 后呈现 `artifact_first_mission_summary`、owner-route / current-owner-delta / runtime drilldown。`artifact_first_mission_summary.paper_mission_run` 对齐 `contracts/paper_mission_run_contract.json` / `paper-mission-run.v1`；domain diagnostic、currentness、storage、owner-route、dispatch 和 PaperRecovery 只作为 observability-only diagnostics / import / migration / provenance 读取，不能作为 product、skill 或 domain-handler 的默认论文主线，也不能声明 paper progress、publication-ready、runtime-ready、`current_package` authority 或 DM002/DM003 完成。

默认可见入口：

- CLI：`medautosci paper-mission inspect --profile <profile> --study-id <study_id> --format json`
- CLI：`medautosci paper-mission start --profile <profile> --study-id <study_id> --objective <objective> --dry-run --format json`
- CLI：`medautosci paper-mission resume --profile <profile> --study-id <study_id> --mission-id <mission_id> --dry-run --format json`
- CLI：`medautosci paper-mission consume-candidate --profile <profile> --study-id <study_id> --candidate <candidate_ref> --dry-run --format json`
- product-entry：`medical_paper_product_entry.default_action_intent = paper_mission/start_or_resume`
- domain-handler export：默认 task kind / action intent 为 `paper_mission/start_or_resume`，并携带 no-write authority boundary；旧 `stage_outcome/opl-handoff` 若出现，必须是 `default_paper_mission_entry=false` / `migration_diagnostic_only=true`。

当前入口先看：

- [项目概览](../project.md)
- [架构](../architecture.md)
- [Runtime docs](../runtime/README.md)
- [Inspection package 产品契约](inspection_package.md)
- [OPL App MAS Runtime Workbench Program](../active/opl_app_mas_runtime_workbench_program.md)

## 当前边界

MAS product surface 只解释 direct app-skill、product-entry、artifact-first mission summary、owner-route diagnostic handoff、sidecar dispatch refs 和 OPL App/workbench 消费边界。当前机器真相显示：

- `contracts/generated_surface_handoff.json` 声明 CLI、MCP、Skill、product-entry manifest、sidecar export/dispatch、status read model、workbench drilldown 和 test harness 的 generated/default owner 是 `one-person-lab`；MAS 只提供 domain handler、domain refs、owner receipt、typed blocker、authority refs 和必要医学 helper。当前 MAS skill-facing paper path 应消费 `PaperMissionRun` readback 和 `paper_mission/start_or_resume`，不把 domain diagnostic/owner-callable/PaperRecovery 当成普通用户入口。
- `contracts/functional_privatization_audit.json` 把 generic scheduler、daemon、queue、attempt ledger、generic runner、generic workbench、memory locator、artifact lifecycle 和 observability 归为 OPL / shared-family owner；MAS 不能把 repo-local product/status/workbench shell 写成长期 generic platform。
- `contracts/test-lane-manifest.json` 的 `mas-workbench-projection` 与 `mas-functional-consumer-followthrough` 只允许 App/workbench 消费 MAS refs-only projection 和 action receipt，不允许写 study truth、publication eval、controller decisions、terminal commands、current package、evidence/review ledger、memory body 或 artifact authority。
- MAS 不再提供 repo-local Progress Portal / static HTML display materializer；默认 study read model 是 artifact-first mission summary，platform repair 折叠进 diagnostics。`medautosci workspace progress-portal`、`--serve`、`--enable-actions` 和 `ops/mas/bin/start-web` 不是当前入口。OPL hosted workbench / App shell 消费 MAS refs-only projection；MAS 不写 paper/package、publication gate、controller decision 或 provider runtime state。

## MAS Stage 主提示词与专业 Skill 单源

MAS 只维护 stage 主提示词/策略和 stage projection：canonical repo source 是 `agent/stages/` + `agent/prompts/`；`write`、`review`、`figure` 等 stage 负责阶段进入、证据门槛、route-back、owner gate 和采纳边界。`src/med_autoscience/overlay/templates/*.SKILL.md` 与运行时 `.codex/skills/medical-research-*` 只是 Codex discovery 兼容投影，不是 stage source，也不是 professional specialist skill source。

professional specialist skill 单源在外部 `mas-scholar-skills` 仓库。MAS 侧只在 `contracts/capability_map.json` 保留消费边界和 route index，指向默认医学论文专业 Skill：`medical-manuscript-writing`、`medical-manuscript-review`、`medical-figure-design`、`medical-research-lit`、`medical-statistical-review`、`medical-table-design`、`medical-submission-prep` 和 `medical-data-governance`。Display 的 active module 仍是 `mas-scholar-skills.display`；Claude Science figure-style / figure-composer 的吸收点改为 dedicated `medical-figure-style` / `medical-figure-composer` 子 Skill，由 `medical-figure-design` 作为 orchestrator route 统一接回 figure stage 和 MAS owner gate。这些 Skill 通过 OPL Connect 同步到 workspace 或 quest，产物默认只是 candidate refs、execution receipts、style/layout QA、route-back hints 或 owner-gate requests。

外部 `mas-scholar-skills` source 还维护 optional router/reviewer 与 named-specialty skills，例如 advanced biomed routing、methodology planning、evidence integrity review、publication routeback review、structural biology、protein design、genomics foundation models、single-cell modeling、indication dossier、PDF evidence exploration、scientific compute diagnostics、protocol/SAP、cohort phenotyping、claim map、reference integrity、rebuttal strategy、display QC、causal inference、survival analysis、risk-model transportability review、registry-atlas story architecture、portfolio memory curation、display regression debugging 和 data-freeze/readiness review。MAS profile / bootstrap / registry 只在 `optional_skill_ids` 与 optional target path templates 中暴露这些真实 skill 的本地发现路径；它们不是默认 core，不复制 skill 正文，不是第二 catalog truth，也不写 MAS owner receipt、typed blocker、publication readiness 或 paper truth。旧 evidence-gap triage、methodology routeback、owner-gate handoff 和 publication-strategy memory Skill 只作为 redirect-only provenance，由 retained reviewer / curator modes 覆盖，不再作为本地 Codex skill path 暴露。

其中一部分专业 Skill 会随带 `kernel.py` 作为 skill-local deterministic helper。helper 只做重复、可验证的小动作，例如 schema skeleton、identifier normalization、table/package/data lint、PDF evidence scan、env intent 或 log/receipt shaping；它不替代 AI 专业判断，也不管理 provider、credential、endpoint、SLURM/Modal/cloud resource lifecycle。MAS 只暴露 helper policy/readback，不复制 helper body，不把 helper 输出写成 owner acceptance。

当前策略是 `Stage Prompt + Professional Skill + Tool/Fabric execution + Domain Owner Gate`：MAS stage 决定当前工作能不能推进和交给谁；专业 Skill 做专业候选产物；工具/Fabric 做检索、渲染、检查和候选包生成。前三者都不写 MAS truth；最终接受、退回、阻塞或 human gate 只由 MAS owner surface 决定。

默认先用 `mas-scholar-skills` 八个 active module 覆盖常规医学论文需求；Display module 下的 `medical-figure-style` / `medical-figure-composer` 只算 dedicated 子 Skill。罕见重型专科工具缺口才通过 `external-scientific-skills` 走 OPL Connect `external-skills search -> inspect -> sync`，触发条件限于用户显式点名工具/数据库、核心 Skill route-back 命名缺口、stage policy 判定八个 active module 不足，或联网/云计算/敏感数据路径需要 policy/approval。K-Dense 和其他外部目录只作为 refs-only pattern/advisory，不是 MAS 权威源。

文献检索默认通过 `opl connect pubmed search --query <query> --limit <n> --json` 或 `medical-research-lit` 取得候选 refs。MAS 的 `scout`、`write`、`review` 和 `figure` 路径负责筛选、证据映射、claim/citation/display 归位和最终判断。

`medical-research-figure-polish` 只保留为 `figure` stage 的 polish/review 阶段兼容入口。图件从设计、证据 refs、panel plan、初稿渲染到 visual QA 的主路径归 `figure` stage 主提示词和 `medical-figure-design` orchestrator。`medical-figure-style` 只负责风格参考、publication-style coherence 和 style-QA candidate refs；`medical-figure-composer` 只负责 panel plan、multi-panel composition 和 layout-QA candidate refs。三者都不写 MAS truth、owner receipt、typed blocker、publication readiness 或 current package。

## 当前文档职责

| 文档 | 当前职责 | 不承载 |
| --- | --- | --- |
| `README.md` | 本目录入口和 product/workbench owner 边界。 | 不维护执行计划、proof ledger 或 current gap matrix。 |
| `inspection_package.md` | inspection package 产品契约。 | 不授权 publication verdict 或 artifact authority。 |
| `../active/opl_app_mas_runtime_workbench_program.md` | MAS refs-only projection 进入 OPL App/workbench 的 active support owner。 | 不复制通用 workbench，不定义 publication readiness。 |

## 阅读规则

- 若要判断当前 MAS product/status/workbench 是否已完成 default caller cutover，读 [MAS 理想目标态差距与完善计划](../active/mas-ideal-state-gap-plan.md) 的 `workbench_sidecar_status_cutover`，再读 contracts 和 focused tests；不要从本文或 Portal UI 文案推断完成。
- 若要实现 App-native MAS study workbench，先读 `opl_app_mas_runtime_workbench_program.md` 和 OPL App 仓合同；本仓只提供 MAS refs、receipt、blocker、source refs 和 forbidden-write 规则。
- 若要审计用户可见进度展示，按 OPL hosted workbench / App shell 读取：MAS 只提供 refs-only projection、owner receipt / typed blocker refs 和 forbidden-write 规则，长期主用户工作台归 OPL App。
- 若要判断论文推进，默认读 `artifact_first_mission_summary.paper_mission_run`、`medical_paper_product_entry`、canonical `NextActionEnvelope`、同 identity 的 OPL receipt 和 MAS owner consumption；不要把 domain diagnostic/currentness/storage/dispatch/PaperRecovery diagnostics、no-write readback、focused tests、queue/attempt 状态或 read-model clean 写成 paper progress、ready evidence 或 `current_package` authority。
