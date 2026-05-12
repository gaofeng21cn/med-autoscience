# MAS 当前开发线路

Status: `active content-level development map`
Date: `2026-05-11`
Owner: `MedAutoScience`
Purpose: 在 MAS monolith closeout 和 OPL stage-led framework 新定位之后，给出当前内容级开发线路图。
Machine boundary: 本文是人读规划地图。机器真相继续归 MAS runtime/controller/artifact surfaces、OPL provider/framework contracts、product-entry manifest、sidecar receipt、测试和真实 workspace evidence。

## 当前结论

`docs/program/` 现在按内容线阅读，不按整份旧计划阅读。旧文档里的部分内容仍有效，但当前任务不是“把每个旧计划从头到尾做完”。

当前执行优先级应是 framework-first：

1. 先把 OPL 做成完整的 Codex-first、stage-led 智能体框架，具备 durable stage attempt、queue/wakeup、retry/dead-letter、approval/human gate、receipt/projection、shared lifecycle/index primitive 和 provider-backed runtime。
2. 再把 MAS 迁移到这个框架：MAS 暴露 domain-agent skeleton、stage descriptor、sidecar export/dispatch、owner receipt、artifact locator、projection builder 和 authority refs；OPL 承载框架运行外围。
3. 同步把新旧功能逐块分类、迁移、分层或沉淀：domain truth 留在 MAS，framework-generic lifecycle/index/restore/retention 能力上收到 OPL，local diagnostics 和 evidence surface 显式降级。
4. 过时模块、Hermes/MDS/default-compat path、旧 manager wording 和重复 UI 入口在替代证据存在后进入退役清理；这属于迁移收口条件，不应无限期后置。
5. 最后再做真实 E2E / paper-line soak / App workbench 验收，证明新框架下 MAS paper autonomy 能产生 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 typed blocker。

这里的“最后再测试”指真实运行验收和 paper soak，不表示代码级验证后置。每个迁移步骤仍必须跑对应 focused tests、contract checks 和 repo-native verification。

## 内容线路

| 顺序 | 线路 | owner 文档 | 当前状态 | 当前实际要做 |
| --- | --- | --- | --- | --- |
| `1` | `opl_framework_foundation` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) + OPL master docs | `framework_required_before_final_soak` | 先完成 OPL 智能体框架能力：stage attempt、provider runtime、queue/wakeup、retry/dead-letter、approval transport、receipt/projection、shared lifecycle/index primitive。 |
| `2` | `mas_framework_migration` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md) | `domain_adapter_landed; migration_active; memory_soak_readonly_proof_landed` | MAS 迁移为 OPL-admitted domain agent：sidecar/receipt contract、stage descriptor、domain skeleton、artifact locator、authority refs、direct path / hosted path receipt equivalence；publication-route memory 的 DM002 paper-line proof 已能把 stage route-memory refs、typed closeout proposal、MAS router receipt refs 和 OPL/Aion receipt refs 串成 MAS-owned ref-only surface，OPL 不能写 MAS memory body 或 router acceptance。 |
| `3` | `feature_partition_and_retirement` | [OPL Temporal MAS Runtime Retirement Program](./opl_temporal_mas_runtime_retirement_program.md), [MAS Single-Project MDS Absorb Program](./mas_single_project_mds_absorb_program.md), [Runtime Lifecycle SQLite Migration Program](./runtime_lifecycle_sqlite_migration_program.md) | `classification_and_cleanup_active` | 新旧功能逐块分类为 retain/move/lift/degrade/retire；退役旧默认依赖、legacy compat、重复 UI 和过时 manager surface。 |
| `4` | `app_runtime_workbench` | [OPL App MAS Runtime Workbench Program](./opl_app_mas_runtime_workbench_program.md) | `read_only_projection_landed; app_productization_active` | 在 OPL App 中产品化迁移后的 MAS 状态、route、conversation、terminal/log、artifact、action receipt；不重新定义 runtime truth。 |
| `5` | `paper_autonomy_acceptance` | [AI-first Paper Autonomy Closure Program](./ai_first_paper_autonomy_closure_program.md) | `repo_loop_landed; three_paper_readonly_projection_landed; dm002_memory_apply_proof_landed; controlled_live_apply_still_pending` | 在 OPL framework + migrated MAS 形态下做真实 paper-line soak；当前 read-only projection 已覆盖 DM002/DM003/Obesity，DM002 已形成 memory/writeback/receipt proof，下一步仍是 guarded controlled apply 下的 artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 typed blocker。 |
| `6` | `recurring_learning_support` | `docs/status.md`, `docs/references/**` | `triggered_support` | DeepScientist / external harness / adjacent framework intake 只在触发时执行，dated snapshot 留在 history。 |

## 已过时或已降级内容

| 内容 | 当前处置 |
| --- | --- |
| “P0 等于 MAS-only runtime 完成” | 已过时。P0 是目标和验收，产品/框架依托分别在 P1/P2。 |
| “整份 P1 workbench 计划都要做完” | 已替换为 P1 内容 lane：read-only workbench、action receipt、terminal attach、provider join。 |
| “整份 P2 Temporal retirement 计划都要做完” | 已替换为 framework-first 的 P2 内容 lane：OPL framework foundation、MAS framework migration、framework-generic lift、legacy retirement、再进入 paper-line soak。 |
| Hermes-first 或 MAS local scheduler 作为 Full online target | 已降级。local scheduler 是 diagnostics/fallback；Hermes 是 legacy/optional proof lane，除非未来证据改变。 |
| 旧 MDS daemon/WebUI/runtime transport 作为默认依赖 | 默认路径已退役；只保留 provenance、explicit archive import、backend audit、upstream learning 或 parity reference。 |
| Runtime lifecycle Git-era cleanup 作为活跃大迁移 | 已落地。新发现问题按 P3a drift/maintenance 处理，除非证明有 live writer regression。 |
| Local Portal / Live Console 作为最终主产品面 | OPL App workbench 成为主用户面后，local Portal / Live Console 降级为 fallback/debug/evidence。 |
| 依赖 Markdown wording 的测试或脚本 | 方向无效。机器接口应使用 schema、JSON、CLI/API payload、manifest 或 durable semantic ID。 |

## 合并与吸收规则

编辑旧 program 内容时按下表归位：

| 内容类型 | 归属 |
| --- | --- |
| 论文质量、reviewer repair、route decision、stage knowledge/memory、live-soak acceptance | P0 |
| App-native 状态、路线视图、conversation timeline、terminal/log panel、安全 action UI | P1 |
| OPL provider、Temporal attempt、queue、retry/dead-letter、approval transport、sidecar receipt、provider projection | P2 或 OPL master docs |
| MDS provenance、compatibility guard、explicit archive import、no-history source intake、behavior parity | P3 或 `docs/references/mds-parity/` / `docs/references/med-deepscientist/` |
| runtime lifecycle authority、SQLite/file boundary、Git retirement drift、restore proof | P3a |
| 可服务多个 domain 的 lifecycle/index/restore/retention primitive | 先进入 P2 的 `lift_to_opl_framework`，再进入 OPL framework docs |
| dated evidence、旧 phase table、旧 activation package、superseded checklist | `docs/history/program/` |
| recurring external learning trigger 和 absorption rule | `docs/status.md` 或 `docs/references/**`，单次执行快照进入 history |

## 优先级规则

1. Framework-first：OPL 完整智能体框架是 MAS 迁移和真实 paper soak 的前置条件。
2. 迁移优先于测试：真实 E2E / paper soak 应验证迁移后的目标形态，不应验证一个即将退役的 MAS-local 运行外围。
3. 退役清理属于迁移收口：旧默认依赖、legacy compat、重复 UI、过时 manager surface 不应无限期留作“以后再说”；删除前必须有替代证据、无默认调用、无 fixture/provenance 必需。
4. 只上收通用 framework primitive：lifecycle、locator、retention、restore proof、attempt receipt、cache cleanup 可以进入 OPL；study truth 和 publication authority 留在 MAS。
5. 产品 workbench 跟随框架迁移：OPL App 展示 OPL framework + MAS owner receipts 的状态，不重新发明第二套 runtime truth。
6. 代码级验证持续执行：每个 contract、runtime、projection 或 cleanup 步骤都要跑 focused tests；最后的真实 paper soak 是目标形态验收。

## 当前完成信号

| 线路 | 完成信号 |
| --- | --- |
| `opl_framework_foundation` | OPL provider/framework 能稳定承载 stage attempt、queue/wakeup、retry/dead-letter、approval/human gate、receipt/projection 和 shared lifecycle/index primitive。 |
| `mas_framework_migration` | MAS direct skill path 与 OPL-hosted path 使用同一 MAS owner receipts，且 OPL 不写 forbidden MAS truth surface。 |
| `feature_partition_and_retirement` | 旧默认依赖、legacy compat、重复 UI、过时 manager surface 完成分类、替代和退役清理；保留项都有明确 owner 和用途。 |
| `app_runtime_workbench` | 用户在 OPL App 看到 MAS study progress、route、conversation、terminal/log、artifacts、source refs 和 safe action receipts，不必依赖 CLI 或 local HTML。 |
| `paper_autonomy_acceptance` | 迁移后的目标形态中，真实论文线反复产出 artifact delta、gate replay、reviewer update、route decision、human gate、stop-loss 或 MAS owner surface 下的 typed blocker。 |
| `monolith_and_mds_foundation_guard` | 后续 MDS/DeepScientist 引用被分类，不能成为默认 runtime、quality 或 artifact authority。 |
| `runtime_lifecycle_foundation_guard` | 新 runtime/Git/path drift 被 inventory、必要时 archive/restore、完成验证，并保持在默认 MAS authority 之外。 |

## 验证

Docs-only 维护：

- `git diff --check`；
- 用 `rg` spot-check inbound links 和 stale references；
- 不新增断言 prose wording 的测试。

Contract/runtime/product 变更：

- 跑触及线路的 focused owner-surface tests；
- 修改 machine-readable contract、action metadata、schema 或 runtime semantics 时跑 `make test-meta`；
- 常规代码变更跑 `scripts/verify.sh`；
- guarded apply 前先有真实 workspace read-only evidence；
- OPL/App/provider integration 必须显式验证 forbidden-write 边界。
