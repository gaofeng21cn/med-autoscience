# MAS Stage Surface Standardization Program

Status: `stage skill surfaces landed / ideal-state proof surfaces landed / route-memory grouping landed / provider live apply pending`
Date: `2026-05-14`
Owner: `MedAutoScience Stage-Led Autonomy + Quality OS`
Purpose: 定义 MAS 在 OPL stage-led framework 下更理想、更统一、更易维护的 stage 表达形态，并记录当前差距、统一模板与后续执行计划。
State: `stage_skill_surfaces_landed; provider_residency_read_model_landed; guarded_apply_harness_landed; review_index_workspace_locator_proof_landed; memory_receipt_inventory_grouping_review_landed; workbench_ref_projection_landed; runtime_owner_followthrough_landed; opl_production_proof_ingested; standard_agent_purity_projection_landed; production_provider_live_apply_pending`
Machine boundary: 本文是人读规划与维护合同。机器真相继续归 canonical route / contract / runtime surfaces：`stage_route_contract.yaml`、stage knowledge plane contracts、stage quality contract、MAS controller/domain-authority refs surfaces、OPL current-control-state、product-entry manifest、sidecar receipts、AI reviewer artifacts、publication gate、evidence/review ledgers 和真实 workspace artifact proof；Markdown 只解释和导航，不成为机器 truth。

## 结论

MAS 的理想形态不是继续增加程序化科研分流器，而是把每个医学研究 `Stage` 做成清晰、同构、可发现、可执行、可审计的 domain surface。

理想维护单元应是：

```text
Stage card
  -> route contract
  -> prompt / skill surface
  -> callable owner tools
  -> knowledge packet obligations
  -> durable output / closeout obligations
  -> Stage Deliverable Review Page / Stage Deliverable Index
  -> quality gate / reviewer rubric
  -> OPL descriptor / artifact locator projection
```

这条链路的核心原则是：OPL 承载 stage attempt、queue、wakeup、retry/dead-letter、human gate transport、receipt 和 projection；MAS 持有医学研究路线、证据、质量、publication verdict、artifact authority 和 owner route。这里的 `verdict` 必须是 AI-first stage quality gate 的审阅结果，不是脚本函数的直接返回值。程序只能校验 reviewer record / quality pack output / evidence refs 的完整性，持久化 durable surface，签发 owner receipt 或 typed blocker，并阻止 OPL/App/provider 越权写 MAS truth。

## 理想形态

理想状态下，MAS 的每个 stage 都应满足同一组形式要求。

| surface | ideal contract |
| --- | --- |
| `stage card` | 一页人读 stage 摘要，说明目的、进入条件、退出条件、禁止动作、human gate 和 next routes。 |
| `route contract` | `stage_route_contract.yaml` 是 canonical source；每个 route 都有 `key_question`、`goal`、`enter_conditions`、`hard_success_gate`、`durable_outputs_minimum`、`human_gate_boundary`、`next_routes`、`route_back_triggers`。 |
| `prompt / skill` | 每个主 stage 都有独立可读 `SKILL.md` 或同等 stage prompt surface；append block 只用于横切补充，不作为长期主说明面。 |
| `tool surface` | 每个 stage 明确允许调用哪些 MAS owner callable surface；工具只进入 controller-authorized CLI/MCP/product-entry/runtime/action catalog，不旁路写研究产物。 |
| `knowledge input` | 每个探索、分析、写作、审阅和决策 stage 都有明确 `stage_knowledge_packet` 输入义务；无义务也要显式说明为什么不需要。 |
| `closeout` | 每个能产生 reusable lesson、failed path、route impact、citation gap 或 reviewer lesson 的 stage 都有 `stage_memory_closeout_packet` 和 router receipt 规则。 |
| `deliverable review page` | 每个 stage 的最终人读交付物统一收敛成一页 `Stage Deliverable Review Page`，供论文人工审阅者判断该 stage 是否能进入下一步；它是可选人工审阅记录，不是默认卡点。 |
| `deliverable index` | 每条 paper line 有一个 `Stage Deliverable Index`，按 stage 列出最新 review page、源 artifact refs、owner receipt、freshness、人工判断状态和下一步；索引只做 locator/projection，不改 MAS truth。 |
| `quality gate` | 每个 stage 都有医学、统计、证据、写作或投稿质控 rubric；ready / done / pass 只能由 AI-first reviewer / quality-pack record、evidence refs、reviewer OS trace、route-back reason 或 typed blocker 支撑。代码不得用规则、regex、固定分支或普通脚本直接替代医学 judgment。 |
| `artifact locator` | repo 只保存 contract、prompt、policy、schema、Markdown memory body、seed index 和 locator；真实 workspace artifact body 留在 workspace/runtime root。 |
| `OPL projection` | OPL 只消费 descriptor、refs、freshness、attempt receipt 和 source locator；不生成医学 truth、不接受 memory writeback、不授权 publication readiness。 |

### 理想目录口径

当前 repo 已通过 `standard_domain_agent_skeleton` 把现有路径映射到标准 slot。后续更理想的物理形态是让新增人读 stage surface 默认进入标准目录，现有路径只保留为明确 repo mapping、生成资产或 provenance locator：

| standard slot | owner | target content |
| --- | --- | --- |
| `agent/stages/` | MAS Stage-Led Autonomy | stage cards、route summaries、stage-to-route map。 |
| `agent/prompts/` | MAS overlay / agent entry | Codex/OpenClaw/other executor prompt projections。 |
| `agent/skills/` | MAS app skill / overlay | 每个主 stage 的 human-readable skill surface。 |
| `agent/knowledge/` | MAS domain memory owner | publication route memory policy、Markdown library、seed index、locator contract、writeback rules。 |
| `agent/quality_gates/` | Quality OS | AI reviewer policy、publication gate、reporting guideline pack、stage quality rubrics。 |
| `contracts/runtime/sidecar/` | Runtime OS + OPL bridge | sidecar export/dispatch、guarded task receipt、forbidden-write proof。 |
| `runtime/artifact_locator/` | Artifact OS | workspace/runtime artifact root locator refs，不保存 artifact body。 |

短期不需要一次性物理搬目录；当前更重要的是先统一概念、字段和入口，再按低风险方式逐步迁移。

### AI-first verdict 口径

`publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict`、`artifact_mutation_authorization` 和 `publication_route_memory_accept_reject` 都不能被维护者理解成“某个 Python 函数算出最终结论”。它们是 stage 质控链路上的 authority boundary：

| boundary | standard stage form | program role |
| --- | --- | --- |
| `ai_reviewer_quality_decision` | `review` stage 的 AI reviewer record、reviewer OS trace、route-back / pass / blocker 判断。 | 校验 reviewer output currentness、provenance 和必需字段；持久化 `medical_prose_review` / AI reviewer-backed eval；缺失时 fail closed。 |
| `publication_quality_verdict` | `write` / `review` / `finalize` stage 组合后的 submission-facing quality gate。 | 汇总 AI reviewer、publication gate、evidence/review ledger 和 artifact freshness refs；不能直接替代 reviewer judgment。 |
| `source_readiness_verdict` | `scout` / source-intake stage 对数据、文献、cohort、endpoint 和 evidence boundary 的 AI-first readiness 判断。 | 校验 source refs、readiness rationale 和 blocker；不把文件存在性当作医学 readiness。 |
| `artifact_mutation_authorization` | `write` / `finalize` / delivery stage 在 quality gate 允许后的 artifact mutation gate。 | 只在 owner receipt 和 freshness proof 成立时允许写 canonical manuscript / package；不生成医学质量结论。 |
| `publication_route_memory_accept_reject` | stage closeout 的 reusable lesson review。 | 校验 proposal、reason、route family 和 writeback receipt；不让 OPL 或普通 transport 决定 memory body。 |

因此，MAS 可以有 validator、materializer、receipt signer 和 guard 函数；但这些函数只服务 AI-first stage output 的可信落账，不拥有医学结论本身。

AI-first stage output 必须来自与执行 agent 分离的 reviewer/auditor agent。标准链路是：executor agent 在一个 stage attempt 中产出工作、artifact/source/evidence refs 和 execution receipt；reviewer/auditor agent 通过新的 invocation 读取这些 refs，使用独立 context/task record 产出 AI reviewer record、audit receipt、route-back reason 或 typed blocker。`Codex CLI` 可以作为 executor；reviewer/auditor 也可以由 Codex CLI 以新的独立任务承担，但不能复用同一上下文让执行者审阅自己。缺少独立 reviewer/auditor record 时，quality gate 必须 fail closed 或 route back。

当前机器面已把这条边界落成 `judgment_mode`：AI-first verdict / memory decision surface 是 `ai_first_stage_gate`，artifact mutation 是 `ai_first_record_validator`，owner receipt signer 和不输出医学 verdict 的 helper 是 `mechanical_guard`。MAS 程序的统一输出策略是校验 AI-first stage gate record 后签 receipt 或 typed blocker；它不直接输出 ready/pass。缺少独立 reviewer/auditor receipt、复用 executor task/context/receipt、候选 record 来自 mechanical projection、或缺必需 AI-first refs 时，`ai_first_private_authority` validator 必须 route back 或 fail closed。

### Quality Pack Maturity Gate

stage quality pack 现在还必须声明 contract maturity，而不是只声明 pack id 和 reviewer rubric。`maturity_status` 表达 MAS contract 的可用成熟度，`promotion_evidence` 表达晋级依据。nature-skills README 中 Draft / Beta / Stable skill 状态只作为可学习的 status pattern；进入 MAS 后必须转译为 repo-tracked contract maturity，不得成为 vendor authority、default skill source、publication readiness 或 quality verdict。

`stable_contract` 的最低门槛是强证据：synthetic fixture、focused tests、real paper-line owner receipt 或 anonymized package evidence。单独的文档说明、普通测试通过、README 状态或 vendor skill 标签都不足以晋级 stable。即使是 stable 的 nature-derived pack，也仍然只作为 reviewer / auditor 消费的 explicit quality pack descriptor，`publication_readiness_authority=false` 且 `quality_verdict_authority=false`。

## 当前状态

当前已具备的基础按生命周期读成四组：

- `machine source`：`agent/stages/stage_route_contract.yaml`、stage knowledge / quality contracts、generated `docs/runtime/contracts/stage_surfaces.md`、product-entry / OPL descriptor 和 standard skeleton anchors 持有可验证 stage shape；Markdown 只解释这些 surfaces。
- `human stage surface`：主 stage 已有独立 stage skill 或等价人读面，新增或修改 stage/prompt/skill 时必须继续消费 machine-derived route、knowledge、quality、tool、closeout 和 OPL boundary refs。
- `review / memory / workbench projection`：Stage Deliverable Review Page / Index、publication-route memory inventory 和 workbench reference projection 只暴露 refs、freshness、receipt、blocker 和 optional human annotation；它们不写 MAS truth、不接受 memory body、不授权 publication readiness。
- `runtime / legacy boundary`：provider residency、guarded apply、legacy active-path tombstone 和 no-default-caller proof 只证明框架可承载 MAS refs / blockers 或旧面已进入 history/provenance；真实 paper-line provider apply、domain activity soak、human gate/resume 和 receipt scaleout 仍是 evidence gate。

当前缺口：

| gap | current impact | next proof |
| --- | --- | --- |
| Production provider-hosted live apply 仍未闭合 | 只能说 stage skill surfaces landed、descriptor / adapter ready、provider projection 与 typed blocker proof landed；不能说 production-hosted paper automation 已完成。 | 真实 provider attempt 在 paper line 上留下 `attempt query -> typed closeout -> MAS owner receipt -> artifact delta / gate replay / human gate / stop-loss / typed blocker`。 |
| OPL production provider residency proof 已落地，MAS managed-state read model 已收口，真实 domain activity soak 仍未收口 | 当前 OPL production proof 已显示 `production_residency_proven`，MAS product-entry / sidecar ingestion 可把 provider availability 切到 available，并暴露 managed service / worker state consistency projection；剩余风险是真实 MAS domain activity 长时运行证据，以及 OPL App/status 面消费同一 projection。 | OPL `family-runtime status --provider temporal` 与 MAS `managed_temporal_state_consistency` 同口径显示；真实 domain activity attempt 能 re-query、restart、retry/dead-letter，并串到 MAS sidecar dispatch receipt。 |
| Stage prompt、policy、quality rubric 仍需要持续守住 owner boundary | 新增或修改 skill 时必须继续消费 stage card、canonical route contract、stage knowledge obligations、quality pack refs、RH clean-room gates 和 MAS owner closeout packet，不能回退为 Markdown-only 规则。 | overlay / agent-entry asset validation 加上 focused route/knowledge/quality contract tests；新增 stage skill 必须带 machine-derived surface block。 |
| AI-first verdict alignment 仍需完成 | 当前 authority/function wording 容易让维护者误读为脚本直接裁决；必须把 verdict 明确写成 standard stage quality gate 的 AI-first output，并要求 executor 与 reviewer/auditor 独立调用。 | 每个 verdict surface 都能追到独立 reviewer/auditor invocation、task/context record、reviewer / quality-pack record、evidence refs、reviewer OS trace、route-back 或 typed blocker；focused tests 防止 self-review、mechanical projection、regex、固定分支或普通脚本替代 quality judgment。 |
| 真实 paper-line review/index instance 仍需继续扩展 | repo-level workspace locator proof 已能物化 review page / index 并由 Portal / Workbench 只读展示；仍不能说 production provider-hosted paper automation 已自动生成真实论文线 closeout。 | provider-hosted attempt 在真实 paper line 上触发 MAS owner closeout，并留下 owner receipt、review/index locator、artifact freshness、gate replay 或 typed blocker。 |
| publication-route memory 仍需更多真实 receipt 泛化 | body-free receipt inventory、operator grouping 和 stale/deprecated review summary 已能投影 migration/writeback accepted/rejected refs；更多 accepted / rejected reusable lessons 仍需从真实论文线进入 workspace memory pack。 | 多 paper-line `stage-memory-closeout-route -> memory_write_router_receipt -> inventory/export` proof，覆盖 accepted、rejected、route-back lessons、grouping 和 review summary。 |
| repo-source skeleton 已有 physical anchors，仍需后续按新增 surface 持续使用 | `standard_domain_agent_skeleton.repo_source_anchor_status` 已证明最小 physical anchors；真实 workspace artifact body 仍 locator-only。 | 新增 material 默认按标准 slot 落位；现有路径只保留明确 repo mapping、生成资产或 locator/provenance。 |
| 旧 MDS / Hermes / local scheduler residue 已归入 history/provenance | current product-entry / sidecar / read-model 默认只暴露 `standard_agent_purity`、domain refs、owner receipts 和 typed blockers；旧 residue/compat/standard Agent purity 细节不再作为 active/default surface。legacy tombstone contract 只在明确 legacy 引用或 provenance 语境中读取。仍需按 stale-surface 与无 fixture/provenance dependency 逐项删除可删代码。 | generated/hosted parity + MAS receipt parity + focused boundary tests + no-forbidden-write proof。 |

## Planning Gate Classification

本 program 现在只承担 [MAS Current Development Lines](./current-development-lines.md) 中 stage / prompt / skill / knowledge / quality / review-index 相关的横向 planning。它不是 MAS production closure 总计划，也不声明 provider live apply 已完成。

| stage-surface gate | gate class | current planning status | done evidence |
| --- | --- | --- | --- |
| `skill_change_guard` | `landed_foundation` | `planned; machine_derived_surface_block_landed` | 新增或修改 stage skill 时继续消费 generated stage card、route contract、knowledge obligations、quality pack refs、RH clean-room gates 和 MAS closeout refs。 |
| `stage_review_index_live_provider_followthrough` | `functional_follow_through_gate` | `planned; workspace_locator_proof_landed` | Live provider attempt 触发 MAS owner closeout 后产生 latest review page / index refs、freshness、claim impact、human annotation、next owner 或 typed blocker。 |
| `standard_skeleton_physicalization` | `functional_follow_through_gate` | `planned; repo_source_anchors_landed` | 新 repo-source surface 默认按 standard slot 落位；破坏性目录移动必须有 direct/hosted parity、provenance、restore 和 no-forbidden-write proof。 |
| `stage_closeout_owner_chain` | `production_evidence_gate` | `planned; guarded_apply_harness_landed` | Provider-hosted live apply 产出 MAS owner receipt，证明 stage closeout / memory / quality / artifact delta 沿 MAS owner surface 闭合，或返回 typed blocker。 |
| `ai_first_verdict_alignment` | `functional_follow_through_gate` | `required; authority_wording_split_pending` | `publication_quality_verdict`、`ai_reviewer_quality_decision`、`source_readiness_verdict` 等必须由独立 reviewer/auditor agent 产生的 AI-first stage quality gate 输出支撑；程序只做 validator / materializer / receipt signer / guard。 |
| `quality_pack_maturity_gate` | `functional_follow_through_gate` | `landed; maturity_and_promotion_evidence_contract_landed` | 每个 stage quality pack 都投影 `maturity_status` / `promotion_evidence`；stable contract 必须有 synthetic fixture、focused tests、real paper-line owner receipt 或 anonymized package evidence 之一的强证据；nature-derived pack 仍无 publication readiness / quality verdict authority。 |

具体 landed proof、focused tests 和 dated receipt 由 machine-readable contracts、test manifests、product-entry / sidecar surfaces、[Plan Completion Ledger](../history/program/plan_completion_ledger.md) 和 [MAS standard agent 文档过程归档 2026-05](../history/program/mas-standard-agent-doc-process-history-2026-05.md) 承担。本文不再维护按日期增长的 proof ledger。

## 距离理想情况

按当前实际状态，MAS 已经越过“形式不可维护”的阶段：主 stage 的 route contract、generated stage card、独立 skill surface、knowledge / closeout obligations、stage quality pack、Research Harness clean-room gates、OPL descriptor locator 和 typed blocker proof 已经是可用维护形态。开发者日常修改 stage 时，主要应关注 prompt / skill / tool / knowledge / quality / closeout 是否继续消费这些 machine-owned surfaces。

距离理想情况还差在运行闭环和产品闭环，而不是再写一批 Markdown：

| layer | current distance to ideal | practical meaning |
| --- | --- | --- |
| Stage form / skill authoring | `near_target` | 已可按统一模板维护；风险是新增 skill 绕过 machine-derived refs 或把 prose 写成 truth。 |
| Knowledge / memory / quality contract | `usable_with_more_real_receipts_needed` | contract、CLI owner entry、body-free receipt inventory、operator grouping 和 stale/deprecated review summary 已可用；仍需要更多真实 paper-line accepted/rejected receipt 扩展 route memory，而不是引入 recipe engine。 |
| Stage deliverable review / index | `workspace_locator_proof_landed_more_instances_needed` | 字段、locator 和 Portal/Workbench 只读展示已落地；repo-level proof 可追到 paper-line workspace refs；还需要更多真实 workspace review page / index instance。 |
| OPL-hosted execution | `production_proof_ingested_guarded_harness_landed_live_apply_pending` | descriptor、sidecar、typed closeout、forbidden-write proof、provider residency read model、OPL production proof ingestion、MAS provider availability 和 guarded apply harness 已有；还缺真实 domain activity soak 与 provider-hosted paper apply soak。 |
| User-facing operation | `reference_projection_landed_app_polish_pending` | MAS Progress Portal / OPL descriptor/workbench projection 能读 provider/review/memory/safety refs；理想态还要 OPL App UI 完整 drilldown。 |
| Legacy references | `history_provenance_only` | 默认路径已迁走；旧词汇、alias surface、cleanup gate 和 tombstone 细节只在 history/provenance 或明确 legacy contract 语境中读取，不能重新进入 current product-entry / sidecar / read-model 默认面。 |

因此，开发者的理解可以调整为：在 stage 内部，确实应主要维护自然语言 skill、stage prompt、知识包、工具边界和质控；但在 stage 与运行框架、workspace artifact、publication authority、human gate、provider live apply 的交界处，仍必须关心程序 contract、owner receipt 和验证证据。理想的分工不是“开发者完全不关心程序”，而是“日常科研语义维护尽量落在人读 stage surface，跨边界动作必须由 machine-owned MAS / OPL contract 兜住”。

## Stage 标准模板

后续每个主 stage 的人读 surface 应采用同一模板。

```markdown
# <Stage Name>

Status:
Owner:
Route id:
Machine source:
Machine boundary:

## Purpose
## When To Enter
## Inputs
## Allowed Tools
## Knowledge Packet
## Work Rules
## Quality Gate
## Durable Outputs
## Closeout And Memory
## Route Back / Human Gate
## Forbidden Actions
## OPL Projection Boundary
```

字段含义：

| field | meaning |
| --- | --- |
| `Machine source` | 指向 canonical contract，例如 `stage_route_contract.yaml` 或 stage knowledge contract，不让 Markdown 成为机器真相。 |
| `Allowed Tools` | 只列 MAS owner callable surface，例如 `stage-knowledge-packet`、`stage-memory-closeout-route`、`owner-route-reconcile`、`ai-reviewer`、`publication_gate` 等。 |
| `Knowledge Packet` | 写清 stage 开始前必须读取的 memory/literature/evidence/review refs。 |
| `Quality Gate` | 写清谁能给 PASS / FAIL / NEEDS_REVIEW，哪些 surface 只能做 projection。 |
| `Closeout And Memory` | 写清哪些内容进入 evidence ledger、review ledger、controller decision、publication route memory 或 incident learning。 |
| `OPL Projection Boundary` | 写清 OPL 只能 index/display/freshness/dispatch MAS-exported task，不能写 MAS truth。 |

## Stage Deliverable Review Page

`Stage Deliverable Review Page` 是每个 stage 的最终人读交付物。它不是新的机器真相源，也不是替代 generated stage card 的手写 contract；它是把该 stage 结束时论文人工审阅需要判断的材料收敛成一页。

每个 review page 必须面向论文人工审阅者回答：

- 这个 stage 是否完成了对当前论文有意义的交付；
- 交付物支持、削弱或改变了哪些 claim；
- 证据、统计、引用、图表、叙事、投稿或伦理声明是否存在阻塞；
- 下一步应进入哪个 stage、route back、stop-loss、human gate 或 finalize；
- 判断所依赖的 MAS truth surface、artifact locator、owner receipt 和 freshness proof 是什么。

Review page 的建议字段是：

| field | purpose |
| --- | --- |
| `stage_id` / `paper_line` / `active_run_id` | 让审阅者确认一页属于哪条论文线、哪个 stage 和哪个运行上下文。 |
| `review_question` | 用一句话写清本页要帮助人工判断的问题，例如能否写入主文、是否需要补实验、是否可进入 finalize。 |
| `deliverable_summary` | 用论文语境概括本 stage 的最终交付，不复述 executor 日志。 |
| `source_refs` | 指向 canonical artifact、evidence ledger、review ledger、publication eval、controller decision、package proof 或 workspace locator refs。 |
| `claim_impact` | 标明 strengthened、weakened、rewritten、removed、unsupported、newly_blocked 或 no_claim_change，并列出受影响 claim。 |
| `evidence_and_statistics` | 对医学证据、统计可重复性、数值一致性、negative/failed path 和 uncertainty 做人工可审阅摘要。 |
| `manuscript_impact` | 标明需要修改的 manuscript、table、figure、supplement、reference、response letter、package/delivery，或说明本阶段只产生 analysis/review record 而无 paper asset body delta。 |
| `quality_gate_state` | 引用 AI reviewer、publication gate、quality pack 或 reporting guideline 的状态；只报告，不自行授权 publication readiness。 |
| `human_judgment` | 人工审阅字段：`accept_for_next_stage`、`needs_revision`、`route_back`、`stop_or_pivot`、`human_gate_required`。前四类只是审阅记录；只有 `human_gate_required` 且命中 MAS human-gate boundary 时才阻塞自动推进。 |
| `reviewer_notes` | 人工审阅者写给下一 stage owner 的简短判断、风险和不可省略的检查点。 |
| `next_action` | 指向下一 route、owner tool、blocked reason 或 terminal decision surface。 |
| `freshness` | 写清 artifact/package/ledger 是否新鲜，过期时必须给出刷新 owner 或 blocker。 |

人工判断字段必须保留论文审阅语义，不能退化成任务完成状态。`provider_done`、`queue_completed`、`tests_passed` 或 `page_generated` 都不能替代 `human_judgment`。

这里的人工审阅是“可介入”，不是“必须人工介入”。MAS 默认仍按 controller/runtime owner surface 全自动推进；review page 上的人工判断默认只是审阅注释，`blocks_auto_advance=false`。只有方向重置、claim 边界扩大、停止或重开、投稿或外部释放、伦理/署名/数据授权这类 human-gate boundary 被 MAS owner surface 判定触发时，才进入 `human_gate_required` 并阻塞自动推进。人工注释本身不能授权 quality verdict、submission readiness、publication readiness 或 artifact authority。

论文资产变化、claim trace 和 freshness 的处理口径也已经固定为审阅投影：

- 论文资产变化类型包括 manuscript、table、figure、supplement、reference、response letter、analysis record、review record、package/delivery 和 no paper asset body delta；它只说明本阶段改了什么，不授权 artifact authority。
- claim trace 状态包括 strengthened、weakened、rewritten、removed、unsupported、newly_blocked 和 no_claim_change；它服务论文质量审阅，不授权 quality verdict。
- freshness 采用 green / yellow / red：green 表示当前 refs 新鲜一致，yellow 表示建议刷新，red 表示过期或不一致。red/yellow 是人工审阅风险信号，默认不阻塞自动推进；真正阻塞仍由 MAS owner surface 的 human gate、quality gate、controller decision 或 artifact authority 决定。

## Stage Deliverable Index

`Stage Deliverable Index` 是 paper-line 级索引。它按 stage 串起最新 review page，让人工审阅者能从一处看到整篇论文走到哪里、每个 stage 的最终人读交付页在哪里、哪些页仍阻塞下一步。

Index 最少应包含：

- paper line / study id / active run id；
- stage 顺序与 latest review page ref；
- 每个 stage 的 source artifact refs、owner receipt、freshness、quality gate state 和可选 `human_judgment`；
- 当前全局 next route、route back、human gate、stop-loss 或 finalize readiness；
- 明确说明 OPL 只能展示和索引这些 refs，不能接受人工判断写回为 MAS truth，也不能把人工判断转成 publication ready 或 quality verdict。

当前状态是：review page / index 已进入 generated machine contract，product-entry / OPL descriptor 已暴露只读 locator，repo-level workspace locator proof 已能把 latest review page 与 paper-line index 落到 workspace artifact locator，并由 Progress Portal / OPL Workbench 直接展示。该 proof 仍不得替代 MAS owner receipts、quality verdict、publication readiness 或 artifact authority，也不得把人工审阅变成默认人工审批流。

Portal / Workbench 接入现在作为只读审阅入口落地：人工审阅者不需要翻 JSON、ledger 或 package proof，就能看到 current stage、latest review page、freshness traffic-light、paper asset delta type、claim impact、human review annotation、next owner 和 blocker。该 UI 只能消费本 contract 和 MAS owner refs，不得把 UI 状态写回为 MAS truth。剩余产品闭环是 production provider-hosted live apply 在真实 paper line 上持续触发 MAS owner closeout 并产生同一组 locator proof。

## Stage 统一目标表

| stage | current surface | target standardization |
| --- | --- | --- |
| `scout` | independent skill + route contract + generated stage card + knowledge obligations | 保留独立 skill；让 literature scout OS、public data discovery、venue intelligence 的 output shape 更紧凑。 |
| `idea` | independent skill + route contract + generated stage card + knowledge obligations | 保留独立 skill；把 candidate frontier、selection scorecard、stop rule 和 publication route memory 使用继续收敛到 stage card / skill。 |
| `baseline` | independent skill + route contract + generated stage card + knowledge / closeout obligations + quality pack refs | 保持独立 stage skill；让 cohort、endpoint、comparator、startup context 和 failed comparator lesson 在人读面中同构可见。 |
| `experiment` | independent skill + route contract + generated stage card + knowledge / closeout obligations + quality pack refs | 保持独立 stage skill；让 data contract、analysis plan、run lineage、endpoint/comparator deviation 和 negative-result lesson 在人读面中同构可见。 |
| `analysis-campaign` | independent skill + bounded analysis policy + generated stage card + knowledge obligations + statistical discipline pack refs | 保持独立 stage skill；保持 candidate board；把 closeout categories 与 statistical discipline pack 显式接到 stage work rules。 |
| `write` | independent skill + rich writing contract + generated stage card + knowledge / closeout obligations | 保留独立 skill；把 claim-evidence map、display-to-claim map、reporting guideline pack、journal neighbor memory 和质量包 refs 对齐。 |
| `review` | independent skill + AI reviewer workflow + generated stage card + knowledge / closeout obligations + quality pack refs | 保持独立 stage skill；把 reviewer action matrix、citation repair、claim downgrade 和 reusable critique lesson 写成统一 closeout。 |
| `finalize` | independent skill + package/readiness rules + generated stage card + knowledge / closeout obligations | 保留独立 skill；把 publication eval、controller decision、package freshness proof、declarations、human gate status 和 artifact freshness pack 对齐。 |
| `decision` | independent skill + stop-loss rules | 保留独立 skill；继续作为 official go/stop/reroute/human gate surface；强化 Stop-loss Memo 与 rejected-alternative memory closeout。 |
| `journal-resolution` | independent skill + generated stage card + knowledge / closeout obligations | 保留独立 skill；让 official guidelines、selected journal evidence、supported exporter profiles 和 blocked-profile evidence 显式进入 stage skill。 |

## 质量包分层

质量不应继续只靠单个大 prompt。理想形态是按 stage 和 study archetype 组合小型 quality pack：

| quality pack | applies to | owner |
| --- | --- | --- |
| `medical_claim_evidence_pack` | write, review, finalize, decision | evidence ledger + review ledger + AI reviewer |
| `statistical_analysis_pack` | baseline, experiment, analysis-campaign | controller + analysis contract |
| `reporting_guideline_pack` | write, review, finalize, journal-resolution | Quality OS + publication profiles |
| `display_to_claim_pack` | analysis-campaign, write, review | display contract + claim-evidence map |
| `route_memory_pack` | scout, idea, analysis-campaign, review, decision | publication route memory |
| `stop_loss_pack` | idea, baseline, experiment, analysis-campaign, review, decision | controller decision |
| `artifact_freshness_pack` | write, finalize, delivery sync | Artifact OS |
| `human_gate_pack` | all boundary-changing stages | controller / OPL signal transport |

Reporting guideline selection should be explicit:

- observational / cohort / registry study: STROBE-family pack.
- diagnostic or prognostic model: TRIPOD / TRIPOD-AI-family pack.
- randomized or intervention study: CONSORT-family pack.
- systematic review / meta-analysis: PRISMA-family pack.
- diagnostic accuracy: STARD-family pack.
- case report or case series: CARE-family pack.
- AI / ML medical study: AI/ML extension pack plus relevant clinical base guideline.

这些 pack 是质控输入和 reviewer rubric，不是 publication readiness authority。最终质量仍由 AI reviewer-backed `publication_eval/latest.json`、publication gate、controller decision 和 artifact proof 共同闭合。

## Research Harness 后续学习整合

`Biajin-PKU/research-harness@006ab44` / `v0.4.0` 对 MAS 的当前价值不是引入外部 runtime、SQLite schema、MCP server、dashboard、parser backend 或 auto-runner，而是提醒本 program 不要只停在 generated stage card。MAS 已经落地 stage card、knowledge / closeout obligations、stage quality pack contract、numeric trace / claim-evidence gate、OPL descriptor projection，并已把这些 machine surfaces 消费进主 stage skill surface；真实 production provider-hosted live apply 仍需沿 MAS paper owner receipt 闭合。

可继续学习并整合的内容只按 MAS owner surface 落地：

| RH pattern | MAS current surface | next integration |
| --- | --- | --- |
| typed research checkpoint / evidence gate | `stage_surface_contract.py`、`stage_knowledge_contract.py`、`stage_quality_contract.py`、`publication_eval/latest.json`、publication gate | `baseline`、`experiment`、`analysis-campaign`、`review` 独立 skill 已显式消费 stage card ref、knowledge obligations、quality pack refs、durable output refs、closeout packet 和 gate owner。 |
| literature / source readiness | `literature_provider_runtime`、`literature_intelligence_os`、workspace literature status、citation ledger refs | `scout` skill 保持独立，并消费 provider provenance、search strategy、anchor/guideline/journal-neighbor refs 和 citation readiness；provider read model 仍不能授权质量。 |
| gap ranking / candidate path | `Study Line Selection Scorecard`、`route_decision_orchestrator`、bounded analysis candidate board、stop-loss memo | `idea`、`baseline`、`analysis-campaign` skill 只消费 scorecard / candidate path / stop rule 作为 route evidence；最终 go/stop/pivot 仍由 controller decision 和 human gate owner surface 支撑。 |
| adversarial review / contradiction handling | `contradiction_flags`、AI reviewer workflow、`reviewer_refinement_loop`、review ledger、publication critique policy | `review` skill 已把 contradiction flag 收成 `review_signal_only`，并把 claim downgrade、citation repair、reusable critique lesson 和 route-back request 显式进入 closeout。 |
| paper writing gate | `medical_claim_evidence_pack`、`display_to_claim_pack`、`reporting_guideline_pack`、`artifact_freshness_pack`、`medical_reporting_audit` | `write`、`finalize`、`journal-resolution` skill 继续保留独立入口，并显式消费 stage quality pack refs；numeric trace、claim-evidence、display-to-claim 和 reporting guideline 缺口仍是 MAS gate blocker，不是 prose suggestion。 |
| human checkpoint / resume | OPL signal transport、MAS controller decision、human gate status、owner receipt | provider projection / typed blocker proof 已落地；production provider-hosted live apply 还必须证明 `OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker`，不能把 provider completion 或 queue completion 写成 paper closure。 |

Semantic Scholar 现在按 `literature_provider_runtime` 的必需 provider adapter/source 读取：仓内 adapter/materializer 负责把 provider 查询、raw response、metadata、citation graph、candidate record 和 screening input 转成 MAS source refs。这个 surface 仍是 read-model-only；它可以支撑 `scout` 的 discovery、citation-neighborhood、metadata enrichment 和 source repair request，但不能授权 source readiness verdict、publication quality、submission readiness、finalize readiness、artifact mutation 或 controller route。执行证据必须保留 raw provider response ledger、credential/rate-limit/cache 状态、query fingerprint、citation ledger refs、screening reason 和 currentness/freshness proof；缺失时只能给 typed blocker 或 source repair route。PubMed、CrossRef 和 PMC 继续作为医学 grounding、DOI/PMID/PMCID crosswalk、full-text / metadata reconciliation 和 provenance 校准的主锚点；Semantic Scholar 不替代这些 grounding surface，也不代表已有 production hosted long-soak 或外部 provider service。

执行时按以下顺序给开发 Agent 分工：

1. `skill_surface_migration`：`baseline`、`experiment`、`analysis-campaign`、`review` 已从 append-block 主说明升级为独立可读 skill surface。每个 skill 都指向 generated stage card、canonical route contract、stage knowledge obligations、quality pack refs、allowed MAS owner tools、forbidden actions 和 closeout packet。
2. `skill_pack_consumption`：已有独立 skill（`scout`、`idea`、`write`、`finalize`、`decision`、`journal-resolution`）已消费 quality pack / knowledge / closeout refs 与 RH clean-room gates，避免 generated cards 和真实 executor prompt 脱节。
3. `review_write_gate_alignment`：RH 启发的 adversarial review、number verification 和 claim-evidence consistency 已只收敛到 MAS `review` / `write` / `finalize` gate，不新增第二套 paper-ready verdict。
4. `provider_soak_evidence`：OPL production residency proof 与 MAS ingestion 已落地；下一步是用真实 provider-hosted live apply 证明 stage closeout、memory writeback、AI reviewer、gate replay、artifact delta、human gate 或 typed blocker 沿 MAS owner surface 闭合。

明确不做：

- 不把 `research-harness` 的 `pool.db`、dashboard、HTTP/API/Web/MCP server、checkpoint runner、Docling parser path 或 Cursor rules 作为 MAS 依赖。
- 不把 RH 的研究领域判断、paper-ready verdict、citation/number quality authority 或 runner semantics 写入 OPL descriptor。
- 不新增 Markdown-only 规则来替代 `stage_route_contract.yaml`、stage knowledge plane、stage quality contract、publication gate、AI reviewer artifact、evidence/review ledger 或 controller decision。
- 不把 quality pack、rubric score、candidate ranking、contradiction flag 或 read-only projection 写成 publication readiness authority。

## Nature-skills Clean-room Pattern Intake

nature-skills 类外部 skill/workflow 材料的吸收口径已经固定为 clean-room pattern absorption，并已从 intake 推进到可用的 MAS-native contract / prompt / descriptor / test surfaces。MAS 只采用 reviewer response、manuscript writing / polishing、statistical reporting、data deliverable、Figure/display 和 source-grounded deliverable 这类可验证工作模式，并把它们落回 `stage_quality_pack_contract`、stage prompts / quality gate、AI reviewer、evidence/review ledgers、publication gate、controller decisions、Stage Deliverable Review Page / Index、product-entry / descriptor refs 与 Portal read model。citation HTML / export UX 只作为 watch 项；如未来落地，也只能消费 MAS source refs、publication profile、artifact locator 和 read-only Portal / Workbench projection。

当前人读面继续收口的 quality pack floors 是：strict Nature / CNS citation scope 与 ENW / RIS / Zotero RDF export；full-paper reader 的 source map、page/block anchor、caption/table/figure anchor；Figure contract 的 core conclusion、archetype、backend、final size、panel map、source-data/statistics/export/QA；paper2ppt 的 selected asset manifest、crop QA、PPTX package/reopen QA、slide overflow/readability QA 与 speaker notes；reviewer response 的 difficult-case、appeal-like 和 author-input routing；Data Availability 的 restricted-access route、public metadata for restricted data、dataset citation、licence / rights / provenance / README 和 FAIR metadata。它们都是 MAS quality pack floors，只能产生 refs、reviewer rubric、typed blocker、owner receipt 或 route-back 条件；不能写成 vendor dependency、runtime dependency、default skill source、publication readiness authority、quality verdict authority、artifact authority 或 submission authority。

当前 landed evidence 是：`stage_quality_contract.py` 提供 quality pack contract；主 stage skill / prompt surface 消费 stage card、knowledge obligations、quality pack refs、closeout packet 和 forbidden actions；product-entry manifest、family stage control-plane descriptor、standard skeleton quality locator 和 stage deliverable index 暴露只读 refs；focused tests 覆盖 stage quality contract、stage surface contract、stage route assets、product-entry descriptor parity、citation/data/figure/display/reviewer-response、manuscript argument/statistical reporting 与 stage review portal surface。剩余证据尾巴是 live paper-line：真实论文线必须留下 owner receipt、evidence/review ledger refs、AI reviewer-backed `publication_eval/latest.json`、controller decision、artifact delta / gate replay / human gate / typed blocker 和 no external authority proof。

明确拒绝的边界是：不新增 vendor/runtime dependency，不把外部 skill runner 写成 MAS provider、Agent executor adapter、default skill source 或 publication authority，不复制外部代码、prompt、schema、HTML 模板或目录布局，也不让 citation/export UI、checklist 或 runner completion 直接授权 publication readiness。详细 closeout 与 acceptance evidence 见 [Nature-skills Learning Intake](../references/mainline/nature_skills_learning_intake.md)。

## 执行计划

| priority | status | task | output | validation |
| --- | --- | --- | --- | --- |
| `P0` | `landed` | 冻结 stage surface template | 本文 + active/README/current lines 引用 | `git diff --check` |
| `P1` | `landed` | 为所有主 stage 生成 stage card | `src/med_autoscience/stage_surface_contract.py` + `docs/runtime/contracts/stage_surfaces.md` generated facade | `tests/test_stage_surface_contract.py` + route contract path spot check |
| `P1` | `landed` | 把 append-block 主 stage 升级为独立可读 skill surface，并消费 stage card / knowledge / quality pack / closeout refs | baseline / experiment / analysis-campaign / review stage skill | overlay installer tests + agent entry asset tests |
| `P1` | `landed` | 补齐 knowledge / closeout obligations | 更新 `stage_knowledge_contract.py` 与 canonical YAML 中的 obligations | `tests/test_stage_knowledge_plane.py` + `tests/test_stage_route_assets.py` |
| `P2` | `landed` | 抽出 reporting guideline quality pack 和 stage quality pack contract | `stage_quality_contract.py` + generated product-entry / family descriptor refs | `tests/test_stage_quality_contract.py` + product-entry action catalog parity |
| `P2` | `landed` | 对齐 OPL descriptor 中的 stage/skill/quality locator | product-entry manifest / skeleton mapping update | product-entry / OPL family adapter tests |
| `P2` | `contract_prompt_test_landed` | 记录并关闭 nature-skills clean-room pattern absorption repo-level 落地 | `docs/references/mainline/nature_skills_learning_intake.md` + `stage_quality_pack_contract` + stage prompts / quality gate refs + product-entry / descriptor refs + focused tests | `git diff --check` + stage quality/surface/route/product-entry descriptor/citation/data/figure/display/reviewer/stage-review focused tests |
| `P3` | `history_provenance_only` | 退役旧 alias vocabulary 或移入 history/reference；不进入 current product-entry / sidecar / read-model 默认面 | legacy contract / history refs + no default caller + replacement proof | focused boundary tests + `rg` stale scan |
| `P4` | `provider_live_apply_pending` | 在已 ingest 的 OPL production proof 之上，用真实 paper-line provider-hosted live apply 验证 | OPL attempt -> MAS owner receipt -> artifact delta / gate replay / blocker | real paper-line guarded apply evidence |

## 后续细化方案

后续不应再按“一个 stage 一个 stage”顺序推进。当前可并行的工作应按缺口 owner 拆线，每条线都必须以 MAS owner receipt、OPL framework receipt 或 read-only locator 作为完成证据。

本节只覆盖 MAS stage surface 相关 follow-through。更大的 production/framework closure 当前由 OPL `/Users/gaofeng/workspace/one-person-lab/docs/active/production-framework-closure-gap-matrix.md` 持有；本 program 在其中只承担 `stage_review_index_live_provider_followthrough`、`skill_change_guard`、`standard_skeleton_followthrough` 以及与 receipt/memory/workbench projection 的 stage locator 部分。旧 OPL `production-functional-closure-plan` 只按 history provenance 阅读。不要把本 program 当作 OPL production/framework closure 的平行总计划。

| lane | status | owner boundary | next work | done signal |
| --- | --- | --- | --- | --- |
| `provider_residency_and_activity_soak` | `proof_ingestion_landed; domain_activity_soak_pending` | OPL production provider / Temporal-backed runtime | `provider_runtime_residency_read_model` 已能表达四类必需 receipt 和 typed blocker；OPL proof 可被 MAS product-entry / sidecar ingestion 消费。下一步是真实 domain activity 长时运行、worker restart/re-query 可见性和 retry/dead-letter proof。 | OPL ledger / status 同时显示 provider 长驻、attempt 可查询、失败可重试/进 dead letter，真实 domain activity attempt 串到 MAS sidecar receipt，且没有 MAS forbidden write。 |
| `provider_guarded_apply_soak` | `harness_landed; live_apply_pending` | MAS paper owner surface + OPL attempt receipt | harness 已覆盖 provider unavailable、MAS owner receipt gate、duplicate idempotency、conflict fail-closed、forbidden-write guard；下一步在真实 paper line 上执行 provider-hosted guarded apply。 | 每条 proof 都包含 typed closeout、MAS owner receipt、artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker、no-forbidden-write proof。 |
| `stage_review_index_workspace_proof` | `locator_proof_landed; more_instances_needed` | MAS artifact locator + review/index projection | Portal / Workbench 已能从 `artifacts/stage_reviews/index.json` 读取 latest review page 与 index proof；后续 provider live apply 继续消费同一 contract。 | 多条真实 paper line 可以从 index 打开 latest review page，并能追到 MAS owner refs；UI 不写 truth。 |
| `publication_route_memory_receipt_scaleout` | `body_free_grouping_review_landed; more_receipts_needed` | MAS stage knowledge plane / workspace memory pack | OPL/Aion body-free receipt inventory、operator grouping 和 stale/deprecated review summary 已落地；下一步从更多真实论文线收集 accepted / rejected route lessons。 | `publication-route-memory-inventory` 显示多条真实 receipt、ref-only grouping、review summary 和 freshness，OPL/Aion 不持有 memory body 或 acceptance authority。 |
| `skill_change_guard` | `ongoing; companion_block_guard_landed` | overlay installer + stage route/knowledge/quality contracts | 对后续任何 stage skill 变更保持 machine-derived stage surface block、canonical route refs、knowledge obligations、quality pack refs、closeout refs、required companion block 和 forbidden actions。 | overlay / agent-entry focused tests 通过，required companion block 被物化并纳入 readiness audit，且新增 prose 没有替代 machine truth。 |
| `standard_agent_purity_projection` | `standard_agent_purity_landed; selective_cleanup_pending` | P2 migration / P3 provenance guard | current product-entry / sidecar / read-model 默认只暴露标准 Agent 口径、domain refs、owner receipts 和 typed blockers；旧 active-path、cleanup gate、compat alias 和 standard Agent purity 细节只在 history/provenance 或明确 legacy contract 语境中读取。下一步只按 stale-surface 与 fixture/provenance 需要删除可删代码或保留 provenance。 | generated/hosted parity + MAS receipt parity + focused boundary tests + no-forbidden-write proof；文档不再暗示旧 runtime 是默认形态。 |
| `standard_skeleton_physicalization` | `slot_audit_landed; physical_move_later` | standard domain agent skeleton / repo source layout | 新增 surface 默认 slot、现有 repo path 映射和 mapping explanation 已落地；现有路径只保留明确 repo mapping、生成资产或 locator/provenance，避免一次性大搬迁。 | skeleton audit 能解释标准 slot 与实际路径；无破坏性目录重组。 |

在 OPL umbrella plan 下的推荐执行顺序是：先由 OPL/OPL+domain lane 统一 provider readiness、owner receipt envelope 和 memory/lifecycle apply receipt；MAS 本 program 并行保持 `stage_review_index_workspace_proof`、`skill_change_guard`、`standard_skeleton_physicalization` 和 `standard_agent_purity_projection`，并把 stage locator / review/index refs 接入 owner receipt 与 workbench projection。真实 `provider_guarded_apply_soak` 继续作为 production evidence gate，不由本 stage surface program 单独宣布完成。

每条线的验证下限：

- docs-only 更新：`git diff --check` 加 stale link/reference spot-check。
- skill / prompt / overlay 更新：overlay installer、agent-entry asset、stage surface、stage knowledge 和 stage quality focused tests。
- product-entry / OPL descriptor 更新：product-entry action catalog parity、manifest/descriptor projection tests、forbidden-write proof。
- provider / live apply 更新：先 read-only evidence，再 guarded apply；最终证据必须来自真实 workspace / provider receipt，不用 repo tests 或 queue completion 代替。

## 不做的事

- 不把 publication route memory 做成固定 recipe engine。
- 不让 OPL 选择医学研究路线、接受 memory writeback、授权 publication readiness 或写 MAS truth。
- 不用 Markdown prose 当机器接口；需要机器约束时进入 schema、contract、CLI/MCP payload、manifest 或 durable JSON。
- `docs/runtime/contracts/stage_surfaces.md` 是由 `src/med_autoscience/stage_surface_contract.py` 从 canonical route contract 和 machine source refs 渲染的人读面；更新语义时先改 machine surface 或 renderer，不手写 Markdown 作为第二真相源。
- 不因为形式统一而一次性搬大目录；先统一 owner、字段、模板、tests，再做低风险物理迁移。
- 不把真实 provider-hosted soak 未完成的状态写成 production automation 已完成。

## Definition Of Done

这条 program 的完成标准是：

- 每个主 stage 都有同构的人读 surface，开发者能直接看到 purpose、tools、knowledge、outputs、quality、closeout 和 OPL boundary。
- 每个 stage 的 route contract 仍从 canonical machine source 派生，不由文档手写第二份 truth。
- 每个主 stage 的 knowledge 和 closeout 义务要么明确存在，要么明确说明不适用。
- 质量包按 study archetype / stage 可组合，reporting guideline 不再散落在长 prompt 中。
- OPL descriptor 能发现 stage、prompt、skill、knowledge、quality gate 和 artifact locator，但不能越权写 domain truth。
- direct MAS app skill path 与 OPL-hosted path 消费同一 MAS owner receipts。
- 已落地的 provider projection / typed blocker proof / OPL production proof ingestion 不能替代 production live apply；最终还需要真实 paper-line evidence 证明 stage closeout、memory writeback、AI reviewer、gate replay、artifact delta、human gate 或 typed blocker 沿 MAS owner surface 闭合。
