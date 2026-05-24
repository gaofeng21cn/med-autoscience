# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-24`

## 文档读法

- 本文是 MAS 当前唯一 single Active Truth plan：维护当前唯一真相、目标态、已落地状态、功能/结构差距、测试/证据差距、当前 `/goal` 收口范围和历史索引。
- MAS 的 north-star 目标态读 [MAS 理想目标态](../references/positioning/mas_ideal_state.md)。本文只保留面向执行的差距和顺序。
- [MAS 当前开发线路](./current-development-lines.md) 只作为内容线索引；若它与本文冲突，以本文为准，并把仍有效内容折回本文、核心 canonical docs 或 history/tombstone。
- dated closeout、receipt id、命令流水、旧 phase checklist、长 follow-through 清单和 proof 过程归档到 [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md)、[Plan Completion Ledger](../history/program/plan_completion_ledger.md) 或对应 `docs/history/**`。active 文档只保留当前结论和仍决定下一步的门槛。
- 差距按目标态判断。当前实现可运行只能作为迁移输入、风险和证据来源，不能反向定义 MAS 长期架构。

## 当前唯一真相

| 主题 | 当前结论 |
| --- | --- |
| MAS 身份 | MAS 是医学研究 domain agent，也是 OPL-compatible package。direct MAS app skill path 与 OPL-hosted path 必须回到同一套 MAS-owned stage、controller、durable truth、quality verdict、artifact authority、memory decision、owner receipt 和 typed blocker。 |
| 默认运行 | hosted autonomous runtime 默认由 OPL/Temporal 承担；OPL 持有 stage attempt、queue、wakeup、retry/dead-letter、resume、human-gate transport、provider query、worker residency 和 operator projection。`Codex CLI` 是 stage 内第一公民 executor；Codex App 只承担 direct entry / 人机操作面，不作为任务启动后的外围持续 driver。 |
| MAS authority | MAS 持有 study truth、stage semantics、AI reviewer / auditor quality gate、publication route、domain transition table、publication-route memory body 与 accept/reject/blocker decision、artifact/package authority、source readiness、owner receipt、safe action refs 和 typed blocker。 |
| OPL authority | OPL 持有通用 scheduler、queue、attempt ledger、generic transition runner、lifecycle/index、memory/artifact locator、restore/retention shell、observability、repair projection、generated CLI/MCP/Skill/product-entry/sidecar/status/workbench wrapper 和 App/workbench shell。 |
| MDS / DeepScientist | 只作为 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。它不回到 MAS 默认 backend、quality owner、artifact authority 或 runtime owner。 |
| 当前机器面 | `agent/` 是 canonical medical research semantic pack；`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`、`contracts/generated_surface_handoff.json`、`contracts/functional_privatization_audit.json` 和 `contracts/production_acceptance/mas-production-acceptance.json` 是主要 machine-readable truth。 |

## 目标态

MAS 的目标态是：

`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal medical authority functions`

这表示 MAS 只长期保留医学研究语义、stage pack、quality gate、publication/artifact/memory/source authority、domain transition、owner receipt 和必要医学 helper。通用 runtime platform、queue、attempt ledger、state-machine runner、memory/artifact locator、lifecycle/restore/retention、observability、workbench 和 generated entry/status wrapper 上收到 OPL Framework / shared family layer。

AI-first quality gate 必须由独立 reviewer/auditor agent invocation 关闭。程序函数只做 schema/provenance/authority refs 校验、持久化、owner receipt 签发、typed blocker、safe action refs 和 no-forbidden-write guard；脚本、regex、scorecard、file presence、queue completion 或 executor 自审不能替代医学质量判断。

## 已落地

| Area | 当前状态 | 当前证据入口 | 当前读法 |
| --- | --- | --- | --- |
| MAS semantic pack / generated handoff | `landed_with_evidence_tail` | `agent/`、`contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、product-entry stage descriptor | `agent/` 是 canonical semantic pack；stage descriptor 已投影 `codex_cli_launch_packet`、runtime event refs、quality refs 和 forbidden authority。真实 stage attempt 与独立 reviewer/auditor receipt 仍属 evidence tail。 |
| Functional privatization boundary | `closed_with_delete_gates` | `contracts/functional_privatization_audit.json`、`contracts/production_acceptance/mas-production-acceptance.json`、`docs/status.md` | 未分类 generic owner 回流关闭；MAS retained surfaces 只能读作 declarative pack / generated surface handoff、domain authority refs、minimal authority function 或 tombstone/provenance gate。 |
| Default runtime owner | `opl_owned_default` | runtime backend default contract、product-entry manifest、sidecar export/read-model | 默认 backend 是 `opl_provider_backed_stage_runtime`；`default_autonomous_runtime` 默认启用，provider 为 `temporal`，wakeup/retry/resume owner 为 OPL。历史 `mas_runtime_core` 只能按 retired provenance / migration input 读取。 |
| Runtime / lifecycle no-alias retirement | `retired_no_alias_guarded` | `contracts/runtime/legacy-active-path-tombstones.json`、`contracts/runtime/mas-runtime-surface-retirement-inventory.json`、functional boundary audit | `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、`lifecycle_refs_adapter.py` 和旧 lifecycle refs SQLite writer 只能作为 tombstone/provenance、OPL handoff refs 或 standard Agent purity guard 读取。 |
| Owner-route / dispatch currentness | `active_current_truth` | `docs/decisions.md` 2026-05-22/23 decisions、owner-route protocol contracts、sidecar export/dispatch behavior | `mas-owner-route-attempt-protocol.v1` 要求 reason registry、priority lattice、currentness basis、source/work-unit/truth/runtime fingerprint 和 typed closeout boundary。它只授权 OPL transport，不授权 paper closure 或 package freshness。 |
| Body-free evidence packet shape | `landed_shape_scaleout_pending` | `paper_line_guarded_apply_evidence`、`body_free_evidence_packets`、production acceptance contract | progress delta、AI reviewer/gate、artifact movement、human gate/resume、stable typed blocker 和 no-forbidden-write proof 已有 refs-only packet shape；真实关闭仍需要 MAS owner chain 在真实 workspace 产出 owner receipt 或 stable typed blocker。 |
| Read-only transition materialization | `landed_with_live_receipt_tail` | `study_state_matrix` action、action catalog、product-entry / CLI / Skill / descriptor-only MCP projection | MAS 暴露 domain transition spec/cases；OPL generic runner 消费 spec。matrix pass 不等于 publication quality、artifact authority、submission readiness 或 paper closure。 |
| Legacy aliases | `direct_retired` | focused fail-closed tests、status / tombstone docs | T2E legacy display alias、submission-target `publication_profile` 输入 alias、旧 human-gate output alias 都不再作为当前输入 fallback；旧 workspace 走迁移、fail-closed 或 tombstone/provenance。 |

## 当前功能/结构差距

以下差距是结构和 owner 边界差距。它们不能被真实 evidence tail、provider completion、repo tests 或 refs-only ledger 消费结果替代。

| 差距 | 当前实际 | 关闭门槛 |
| --- | --- | --- |
| `workbench_sidecar_status_retirement` | product-entry / status / workbench projection shell、sidecar export/dispatch 与 owner-route handoff 仍承担 direct MAS path、OPL handoff 输入或 diagnostic read model。它们当前只能输出 domain projection refs、owner receipt、typed blocker、authority refs 或 diagnostic refs。 | OPL generated product/status/workbench/sidecar 成为 production/default caller；MAS receipt parity、focused sidecar/product tests、no-forbidden-write proof、tombstone/provenance refs 同时成立后，旧 wrapper/facade/compat test 直接删除、archive 或 tombstone。 |
| `remaining_domain_ref_consumers` | `progress_projection`、`owner_route_dispatch_receipt`、`domain_authority_refs_index`、storage/artifact/memory locator 和 runtime storage maintenance 仍是 current domain-ref consumer。它们不是 MAS generic runtime owner。 | 每个 retained surface 写清 active caller、authority boundary、body-free output、不能上收原因和删除门；当 OPL primitive parity 与 MAS owner receipt parity 成立后，去掉只保护旧路径的兼容面。 |
| `physical_source_morphology_guard` | 旧 runtime 名称、developer repair/worktree 元数据、legacy diagnostics 或历史 surface id 仍可能出现在 docs、tests、fixtures 或 audit maps 中。 | current docs/tests/callers 不得把旧名读成 active runtime adapter；developer repair / worktree / verification 元数据迁入 OPL Agent Lab、developer repair lane 或 explicit contract refs。发现 generic queue、attempt ledger、scheduler、worker residency、runtime lifecycle owner 语义时按复活旧控制面处理。 |
| `ai_first_quality_record_scaleout` | quality gate contract 和 validator 边界已落地，但真实 paper-line 的独立 reviewer/auditor record 数量仍需要扩展。 | 多条真实 paper-line stage attempt 产出独立 reviewer/auditor invocation、context/task record、quality receipt 或 typed blocker；程序继续只做校验、持久化和防越权。 |
| `compat_test_retirement` | 部分 tests / fixtures / docs 仍可能以 legacy / managed / old runtime wording 保护旧调用路径。 | 改为验证 current contract、standard Agent purity guard、fail-closed、tombstone semantics、owner receipt 或 typed blocker；删除只维护旧调用路径的兼容测试。 |

## 当前测试/证据差距

以下差距是 production evidence tail。它们不改变上面的结构口径，也不能声明 publication-ready、domain-ready、artifact mutation authorization 或 `current_package` 更新。

| 证据差距 | 需要看到的证据 |
| --- | --- |
| 真实 paper-line provider apply | OPL provider -> MAS sidecar -> MAS owner chain 在真实论文线上留下 attempt query、typed closeout、MAS owner receipt 或 stable typed blocker，并暴露 progress delta、AI reviewer/gate receipt、artifact movement、human gate/resume、route decision、stop-loss 或 no-forbidden-write refs。 |
| owner-chain dispatch ledger scaleout | `domain_dispatch_evidence_record_payload` 在更多真实 owner-route / guarded-apply / aftercare / default-executor / stage-level handoff 中被 OPL identity preflight 和 refs-only ledger 消费，并在 mismatch 时 fail closed。 |
| publication-route memory receipts | 多条真实 paper line 产生 accepted/rejected/blocked memory writeback receipts，并可被后续 stage 以 small-set refs 检索。 |
| artifact lifecycle receipts | 真实 workspace 产生 artifact mutation permission、cleanup/restore/retention guarded receipt、rebuild/freshness proof 或 typed blocker。 |
| human gate / resume | approval、pause、human takeover、explicit wakeup 和 resume 操作链进入 MAS owner route，并证明不会越过 publication gate、AI reviewer gate 或 artifact authority。 |
| provider SLO long soak | 长时 provider-hosted run、restart/re-query、retry/dead-letter、no-forbidden-write 和 App/workbench drilldown 在真实 domain activity 中持续成立。 |
| family transition live receipt | `study_state_matrix` / OPL generic matrix runner 的 route/work-unit 能进入 MAS owner chain，并产出 owner receipt、typed blocker、progress delta、gate replay、human gate 或 stop-loss。 |

## 当前 `/goal` 收口范围

本轮目标不是再拆成多阶段路线，而是一次性把 MAS 标准 OPL Agent 源码形态收敛到可用边界：runtime / control-plane residue、product/status/workbench generated-shell 残留、兼容旧路径测试和 active docs 必须一起收口。并行 lane 只是一种执行手段；最终 current truth 仍以本文件、`docs/status.md`、机器合同、源码和验证结果为准。

| lane | 本轮必须落地的结果 | 不做什么 |
| --- | --- | --- |
| `runtime_control_residue` | 核对 `contracts/functional_privatization_audit.json`、production acceptance、runtime tombstone contract、OPL unique control-plane handoff 和 active callers；把仍暴露 MAS generic scheduler、queue、attempt ledger、worker residency、runtime lifecycle owner 语义的 residue 改回 OPL-owned handoff、MAS owner receipt、typed blocker 或 tombstone/provenance。 | 不把 `runtime_transport/`、`mas_runtime_core*`、turn runner、worker lease、`lifecycle_refs_adapter.py` 写回 active adapter、diagnostic fallback 或 compatibility alias。 |
| `product_status_workbench_shell` | 收窄 product-entry / status / workbench / sidecar / owner-route handoff 为 domain projection refs、owner receipt、typed blocker、authority refs 或 diagnostic refs；已满足 no-active-caller、OPL parity、MAS receipt parity、focused tests、no-forbidden-write proof 和 tombstone/provenance refs 的 wrapper / facade / alias 直接删除或 tombstone。 | 不复制 OPL App/workbench owner，不让 MAS product/status shell 承担 queue、attempt、retry/dead-letter、terminal transport、worker residency 或 lifecycle owner。 |
| `compat_test_retirement` | 把 legacy / managed / old runtime wording 的测试改为验证 current contract、standard Agent purity guard、fail-closed、tombstone semantics、owner receipt 或 typed blocker；只维护旧调用路径的兼容测试直接删除。 | 不新增兼容 alias、normalizer、fallback 或聚合测试来保护旧路径。 |
| `active_truth_docs` | `docs/status.md`、本文件、`docs/active/current-development-lines.md` 和 private implementation inventory 同步到同一 current truth：结构收口和测试/证据 tail 分开写，dated closeout 和 proof 流水折回 history/provenance。 | 不把本轮源码收口写成具体 paper closure、publication-ready、artifact mutation authorization、`current_package` 更新或真实 long-soak 完成。 |

本轮完成信号是：所有 lane 已吸收到 `main`，worktree 清理完成，focused tests / contract checks / repo-native verify 按触及面通过；仍未闭合的真实 paper-line provider apply、publication-route memory、artifact lifecycle、human gate/resume 和 provider SLO long-soak 继续保留在“当前测试/证据差距”，不能回写成结构差距。

### 接续 `/goal` 摘要

继续治理 `/Users/gaofeng/workspace/med-autoscience` 的 MAS 标准 OPL Agent 源码形态收口。先读 AGENTS、TASTE、核心五件套、本文、current development lines、关键 contracts/source/tests/read-model。优先核实并收口 `workbench_sidecar_status_retirement`、`remaining_domain_ref_consumers`、`physical_source_morphology_guard` 和 `compat_test_retirement`。不要写真实 study workspace artifact、paper body、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、memory body 或 artifact body。验证至少包含 `git diff --check`、触及面的 focused tests；修改 machine-readable contract、action metadata、schema 或 runtime semantics 时追加 `make test-meta` / `scripts/verify.sh`。

## 历史索引

| 需要追溯的内容 | 当前入口 |
| --- | --- |
| 当前状态摘要 | [当前状态](../status.md) |
| 架构与 owner 边界 | [架构概览](../architecture.md) |
| 不可变约束 | [不可变约束](../invariants.md) |
| 日期决策日志 | [关键决策记录](../decisions.md) |
| north-star 目标态 | [MAS 理想目标态](../references/positioning/mas_ideal_state.md) |
| 当前内容线索引 | [MAS 当前开发线路](./current-development-lines.md) |
| 文档生命周期治理 | [MAS 文档组合治理](../docs_portfolio_consolidation.md) |
| 2026-05 标准 Agent 文档过程归档 | [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md) |
| 历史完成台账 | [Plan Completion Ledger](../history/program/plan_completion_ledger.md) |

## Active / History Foldback

| 内容 | Foldback target | 规则 |
| --- | --- | --- |
| dated closeout、attempt / receipt id、命令流水、旧 phase checklist | `docs/history/program/` 或对应 `docs/history/<area>/` | 只保留 provenance；不得作为 current truth 或 active backlog。 |
| 已被 current owner surface 替代的旧 runtime/workbench/scheduler/alias 文案 | `docs/history/**` tombstone / provenance，或 machine-readable tombstone refs | active docs 只写当前 owner、删除门和 standard Agent purity guard。 |
| 已关闭功能/结构 gap | 本文 `已落地`，必要时加 compact tombstone pointer | 不保留旧 checklist chronology。 |
| 仍缺 live evidence 的能力 | 本文 `当前测试/证据差距` | 不回写成结构未完成，也不写成 production/domain ready。 |

## 当前不能写成

- 不能把 OPL provider proof、suite pass、queue completion、refs-only ledger receipt 或 provider completion 写成 MAS paper closure、publication-ready、domain-ready、medical-ready、artifact mutation authorization 或 `current_package` 更新。
- 不能把 MAS production acceptance receipt 写成具体论文线 publication-ready；它只承认 structural / physical conformance 与 production-like receipt chain 的边界。
- 不能把 `mas_owner_receipt_present`、stable blocker、body-free evidence packet 或 OPL workorder preflight 写成 workspace mutation、artifact authority 放行、memory writeback success 或 paper closure。
- 不能把 MAS 已经没有任何私有程序面写成绝对清零；准确口径是私有面已收敛为 declarative pack / generated surface handoff、domain authority refs、minimal authority function 或 explicit tombstone/provenance refs。
- 不能把旧 `runtime_transport/`、turn runner、worker lease、runtime lifecycle SQLite、`lifecycle_refs_adapter.py`、MDS/DeepScientist、Hermes、local scheduler、workspace wrapper 或 `mas_runtime_core` 写成 MAS 默认 active runtime owner、active adapter、diagnostic fallback、compat alias 或 retained caller。
- 不能把 product-entry / workbench / owner-route / progress projection shell 写成长期 MAS generic workbench、queue、attempt ledger、retry/dead-letter、worker residency、terminal transport 或 lifecycle owner；它们当前只能输出 domain projection refs、owner receipt、typed blocker、authority refs 或 diagnostic refs。
- 不能把 `study_state_matrix` 或 OPL `family-transition-runner` matrix pass 写成 paper closure、publication quality、artifact authority、submission readiness 或 domain ready。
- 不能把真实 paper apply、memory receipt、artifact receipt、human gate/resume 或 provider SLO 写成可由 repo tests、descriptor ready 或 conformance 替代。
- 不能把 `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 或类似 verdict 写成脚本/函数直接决定；它们必须是 AI-first stage quality gate 的可审计输出。
- 不能把 executor agent 自审、同一上下文内的执行后复核、或 executor summary 改名成 reviewer/auditor output；AI-first quality gate 必须消费独立 reviewer/auditor agent invocation 的记录。
- 不能把 dated specs、dated closeout、follow-through 记录或历史 full record 当成 current truth；需要过程脉络时读取 history/provenance。
