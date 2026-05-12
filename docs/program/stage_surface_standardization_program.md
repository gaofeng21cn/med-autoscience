# MAS Stage Surface Standardization Program

Status: `active cross-cutting program`
Date: `2026-05-12`
Owner: `MedAutoScience Stage-Led Autonomy + Quality OS`
Purpose: 定义 MAS 在 OPL stage-led framework 下更理想、更统一、更易维护的 stage 表达形态，并记录当前差距、统一模板与后续执行计划。
State: `partially landed; docs-owner surface; skill-surface migration pending`
Machine boundary: 本文是人读规划与维护合同。机器真相继续归 `agent_entry_modes.yaml`、stage knowledge plane contracts、MAS controller/runtime surfaces、product-entry manifest、sidecar receipts、AI reviewer artifacts、publication gate、evidence/review ledgers 和真实 workspace artifact proof。

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
  -> quality gate / reviewer rubric
  -> OPL descriptor / artifact locator projection
```

这条链路的核心原则是：OPL 承载 stage attempt、queue、wakeup、retry/dead-letter、human gate transport、receipt 和 projection；MAS 持有医学研究路线、证据、质量、publication verdict、artifact authority 和 owner route。

## 理想形态

理想状态下，MAS 的每个 stage 都应满足同一组形式要求。

| surface | ideal contract |
| --- | --- |
| `stage card` | 一页人读 stage 摘要，说明目的、进入条件、退出条件、禁止动作、human gate 和 next routes。 |
| `route contract` | `agent_entry_modes.yaml` 是 canonical source；每个 route 都有 `key_question`、`goal`、`enter_conditions`、`hard_success_gate`、`durable_outputs_minimum`、`human_gate_boundary`、`next_routes`、`route_back_triggers`。 |
| `prompt / skill` | 每个主 stage 都有独立可读 `SKILL.md` 或同等 stage prompt surface；append block 只用于横切补充，不作为长期主说明面。 |
| `tool surface` | 每个 stage 明确允许调用哪些 MAS owner callable surface；工具只进入 controller-authorized CLI/MCP/product-entry/runtime/action catalog，不旁路写研究产物。 |
| `knowledge input` | 每个探索、分析、写作、审阅和决策 stage 都有明确 `stage_knowledge_packet` 输入义务；无义务也要显式说明为什么不需要。 |
| `closeout` | 每个能产生 reusable lesson、failed path、route impact、citation gap 或 reviewer lesson 的 stage 都有 `stage_memory_closeout_packet` 和 router receipt 规则。 |
| `quality gate` | 每个 stage 都有医学、统计、证据、写作或投稿质控 rubric；ready / done / pass 只能由对应 MAS owner truth surface 支撑。 |
| `artifact locator` | repo 只保存 contract、prompt、policy、schema、seed fixture 和 locator；真实 workspace artifact body 留在 workspace/runtime root。 |
| `OPL projection` | OPL 只消费 descriptor、refs、freshness、attempt receipt 和 source locator；不生成医学 truth、不接受 memory writeback、不授权 publication readiness。 |

### 理想目录口径

当前 repo 已通过 `standard_domain_agent_skeleton` 把现有路径映射到标准 slot。后续更理想的物理形态是保留兼容 facade，同时把人读 stage surface 向标准目录收敛：

| standard slot | owner | target content |
| --- | --- | --- |
| `agent/stages/` | MAS Stage-Led Autonomy | stage cards、route summaries、stage-to-route map。 |
| `agent/prompts/` | MAS overlay / agent entry | Codex/OpenClaw/other executor prompt projections。 |
| `agent/skills/` | MAS app skill / overlay | 每个主 stage 的 human-readable skill surface。 |
| `agent/knowledge/` | MAS domain memory owner | publication route memory policy、seed fixture、locator contract、writeback rules。 |
| `agent/quality_gates/` | Quality OS | AI reviewer policy、publication gate、reporting guideline pack、stage quality rubrics。 |
| `contracts/runtime/sidecar/` | Runtime OS + OPL bridge | sidecar export/dispatch、guarded task receipt、forbidden-write proof。 |
| `runtime/artifact_locator/` | Artifact OS | workspace/runtime artifact root locator refs，不保存 artifact body。 |

短期不需要一次性物理搬目录；当前更重要的是先统一概念、字段和入口，再按低风险方式逐步迁移。

## 当前状态

当前已具备的基础：

- `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml` 已是 stage / route contract 的 canonical source。
- `docs/runtime/contracts/agent_entry_modes.md`、`templates/agent_entry_modes.yaml`、Codex/OpenClaw entry prompt 都由 canonical payload 派生。
- `src/med_autoscience/stage_surface_contract.py` 已为 `scout`、`idea`、`baseline`、`experiment`、`analysis-campaign`、`write`、`review`、`finalize`、`decision` 和 `journal-resolution` 生成同构 stage card contract。
- `docs/runtime/contracts/stage_surfaces.md` 是 stage card 的生成人读 facade；它从 machine source 渲染，不持有第二份 truth。
- `scout`、`idea`、`write`、`finalize`、`decision`、`journal-resolution` 和 `figure-polish` 已有独立 skill template。
- `baseline`、`experiment`、`analysis-campaign`、`review`、`rebuttal`、`intake-audit` 当前以 append block 注入。
- `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt`、`stage_recall_index`、`publication_route_memory_pack` 和 `paper_soak_memory_apply_proof` 已是 MAS-owned operating surface。
- `baseline`、`experiment`、`write`、`finalize` 和 `journal-resolution` 的 knowledge / closeout obligations 已进入 `stage_knowledge_contract.py` 与 canonical entry-mode payload。
- `publication_route_memory` 已按 natural-language-first memory card 落地为小集合检索、typed closeout writeback 和 router receipt，不是机械 recipe engine。
- `stage_quality_pack_contract` 已把 stage-selectable quality packs、reporting guideline selection、locator、freshness 和 authority boundary 落成 machine-readable contract。
- `standard_domain_agent_skeleton.physical_skeleton_layout_audit` 已把 stage、prompt、skill、knowledge、quality gate、sidecar、projection builder 和 artifact locator 映射到现有 repo paths。
- `family_stage_control_plane_descriptor` 与 product-entry manifest 已把 route contract、stage knowledge plane、stage quality pack contract、quality/publication refs 和 authority boundary 投影给 OPL。

本轮已经落地的部分：

| landed slice | owner surface | proof surface |
| --- | --- | --- |
| stage card generated facade | `stage_surface_contract.py` + `docs/runtime/contracts/stage_surfaces.md` | `tests/test_stage_surface_contract.py` |
| missing knowledge / closeout obligations | `stage_knowledge_contract.py` + canonical entry-mode assets | `tests/test_stage_knowledge_plane.py` + `tests/test_agent_entry_assets.py` |
| stage-selectable quality packs | `stage_quality_contract.py` + product-entry / family descriptor projections | `tests/test_stage_quality_contract.py` + product-entry action catalog parity |

当前不足：

| gap | impact |
| --- | --- |
| `baseline`、`experiment`、`analysis-campaign`、`review` 仍主要是 append block | 人读面不够统一；开发者不容易快速看到完整 stage contract、工具、知识和质控。 |
| Stage prompt、policy、quality rubric 仍分散在 overlay、policy、controller、program 和生成文档里 | 新开发者能通过 stage card 看到主线 contract，但深入维护 prompt / skill / rubric 时仍需要跨目录拼接上下文。 |
| `stage_quality_pack_contract` 已存在，但独立 stage skill 还没有逐一消费这些 pack | 质量包已经可发现、可投影；下一步要把具体 stage skill 的自然语言工作面和 pack refs 对齐。 |
| OPL descriptor 已对齐，但 production provider-hosted long-running soak 未闭合 | 只能说 descriptor / adapter ready，不能说 production-hosted paper automation fully landed。 |
| 旧 MDS / Hermes / local scheduler residue 仍有 compat vocabulary | 容易让读者误以为旧 runtime 或旧 WebUI 仍是默认运行形态。 |

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
| `Machine source` | 指向 canonical contract，例如 `agent_entry_modes.yaml` 或 stage knowledge contract，不让 Markdown 成为机器真相。 |
| `Allowed Tools` | 只列 MAS owner callable surface，例如 `stage-knowledge-packet`、`stage-memory-closeout-route`、`runtime-supervisor-reconcile`、`ai-reviewer`、`publication_gate` 等。 |
| `Knowledge Packet` | 写清 stage 开始前必须读取的 memory/literature/evidence/review refs。 |
| `Quality Gate` | 写清谁能给 PASS / FAIL / NEEDS_REVIEW，哪些 surface 只能做 projection。 |
| `Closeout And Memory` | 写清哪些内容进入 evidence ledger、review ledger、controller decision、publication route memory 或 incident learning。 |
| `OPL Projection Boundary` | 写清 OPL 只能 index/display/freshness/dispatch MAS-exported task，不能写 MAS truth。 |

## Stage 统一目标表

| stage | current surface | target standardization |
| --- | --- | --- |
| `scout` | independent skill + route contract + generated stage card + knowledge obligations | 保留独立 skill；让 literature scout OS、public data discovery、venue intelligence 的 output shape 更紧凑。 |
| `idea` | independent skill + route contract + generated stage card + knowledge obligations | 保留独立 skill；把 candidate frontier、selection scorecard、stop rule 和 publication route memory 使用继续收敛到 stage card / skill。 |
| `baseline` | append block + route contract + generated stage card + knowledge / closeout obligations | 升级为独立 stage skill；让 cohort、endpoint、comparator、startup context 和 failed comparator lesson 在人读面中同构可见。 |
| `experiment` | append block + route contract + generated stage card + knowledge / closeout obligations | 升级为独立 stage skill；让 data contract、analysis plan、run lineage、endpoint/comparator deviation 和 negative-result lesson 在人读面中同构可见。 |
| `analysis-campaign` | append block + bounded analysis policy + generated stage card + knowledge obligations | 升级为独立 stage skill；保持 candidate board；把 closeout categories 与 statistical discipline pack 显式接到 stage work rules。 |
| `write` | independent skill + rich writing contract + generated stage card + knowledge / closeout obligations | 保留独立 skill；把 claim-evidence map、display-to-claim map、reporting guideline pack、journal neighbor memory 和质量包 refs 对齐。 |
| `review` | append block + AI reviewer workflow + generated stage card + knowledge / closeout obligations | 升级为独立 stage skill；把 reviewer action matrix、citation repair、claim downgrade 和 reusable critique lesson 写成统一 closeout。 |
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

`Biajin-PKU/research-harness@006ab44` / `v0.4.0` 对 MAS 的当前价值不是引入外部 runtime、SQLite schema、MCP server、dashboard、parser backend 或 auto-runner，而是提醒本 program 后续不要只停在 generated stage card。MAS 已经落地 stage card、knowledge / closeout obligations、stage quality pack contract、numeric trace / claim-evidence gate 和 OPL descriptor projection；接下来应把这些 machine surfaces 消费进每个 stage 的人读 skill 和真实 paper owner receipt。

可继续学习并整合的内容只按 MAS owner surface 落地：

| RH pattern | MAS current surface | next integration |
| --- | --- | --- |
| typed research checkpoint / evidence gate | `stage_surface_contract.py`、`stage_knowledge_contract.py`、`stage_quality_contract.py`、`publication_eval/latest.json`、publication gate | append-block 主 stage 迁移为独立 skill 时，必须显式列出 stage card ref、knowledge obligations、quality pack refs、durable output refs、closeout packet 和 gate owner。 |
| literature / source readiness | `literature_provider_runtime`、`literature_intelligence_os`、workspace literature status、citation ledger refs | `scout` skill 保持独立，但要把 provider provenance、search strategy、anchor/guideline/journal-neighbor refs 和 citation readiness 写成 stage work rules，不让 provider read model 授权质量。 |
| gap ranking / candidate path | `Study Line Selection Scorecard`、`route_decision_orchestrator`、bounded analysis candidate board、stop-loss memo | `idea`、`baseline`、`analysis-campaign` skill 只消费 scorecard / candidate path / stop rule 作为 route evidence；最终 go/stop/pivot 仍由 controller decision 和 human gate owner surface 支撑。 |
| adversarial review / contradiction handling | `contradiction_flags`、AI reviewer workflow、`reviewer_refinement_loop`、review ledger、publication critique policy | `review` skill 独立化时，把 contradiction flag 写成 `review_signal_only`，并把 claim downgrade、citation repair、reusable critique lesson 和 route-back request 显式进入 closeout。 |
| paper writing gate | `medical_claim_evidence_pack`、`display_to_claim_pack`、`reporting_guideline_pack`、`artifact_freshness_pack`、`medical_reporting_audit` | `write`、`finalize`、`journal-resolution` skill 继续保留独立入口，但要显式消费 stage quality pack refs；numeric trace、claim-evidence、display-to-claim 和 reporting guideline 缺口仍是 MAS gate blocker，不是 prose suggestion。 |
| human checkpoint / resume | OPL signal transport、MAS controller decision、human gate status、owner receipt | provider-hosted soak 只能证明 `OPL attempt -> MAS owner receipt -> artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker`；不能把 provider completion 或 queue completion 写成 paper closure。 |

执行时按以下顺序给开发 Agent 分工：

1. `skill_surface_migration`：先把 `baseline`、`experiment`、`analysis-campaign`、`review` 从 append block 升级为独立可读 skill surface。每个 skill 都要指向 generated stage card、canonical route contract、stage knowledge obligations、quality pack refs、allowed MAS owner tools、forbidden actions 和 closeout packet。
2. `skill_pack_consumption`：再让已有独立 skill（`scout`、`idea`、`write`、`finalize`、`decision`、`journal-resolution`）补齐 quality pack / knowledge / closeout refs，避免 generated cards 和真实 executor prompt 脱节。
3. `review_write_gate_alignment`：把 RH 启发的 adversarial review、number verification 和 claim-evidence consistency 只收敛到 MAS `review` / `write` / `finalize` gate，不新增第二套 paper-ready verdict。
4. `provider_soak_evidence`：等 OPL provider-hosted path 可用后，用真实 paper line 验证 stage closeout、memory writeback、AI reviewer、gate replay、artifact delta、human gate 或 typed blocker 沿 MAS owner surface 闭合。

明确不做：

- 不把 `research-harness` 的 `pool.db`、dashboard、HTTP/API/Web/MCP server、checkpoint runner、Docling parser path 或 Cursor rules 作为 MAS 依赖。
- 不把 RH 的研究领域判断、paper-ready verdict、citation/number quality authority 或 runner semantics 写入 OPL descriptor。
- 不新增 Markdown-only 规则来替代 `agent_entry_modes.yaml`、stage knowledge plane、stage quality contract、publication gate、AI reviewer artifact、evidence/review ledger 或 controller decision。
- 不把 quality pack、rubric score、candidate ranking、contradiction flag 或 read-only projection 写成 publication readiness authority。

## 执行计划

| priority | status | task | output | validation |
| --- | --- | --- | --- | --- |
| `P0` | `landed` | 冻结 stage surface template | 本文 + program/README/current lines 引用 | `git diff --check` |
| `P1` | `landed` | 为所有主 stage 生成 stage card | `src/med_autoscience/stage_surface_contract.py` + `docs/runtime/contracts/stage_surfaces.md` generated facade | `tests/test_stage_surface_contract.py` + route contract path spot check |
| `P1` | `pending` | 把 append block 主 stage 升级为独立可读 skill surface，并消费 stage card / knowledge / quality pack / closeout refs | baseline / experiment / analysis-campaign / review stage skill | overlay installer tests + agent entry asset tests |
| `P1` | `landed` | 补齐 knowledge / closeout obligations | 更新 `stage_knowledge_contract.py` 与 canonical YAML 中的 obligations | `tests/test_stage_knowledge_plane.py` + `tests/test_agent_entry_assets.py` |
| `P2` | `landed` | 抽出 reporting guideline quality pack 和 stage quality pack contract | `stage_quality_contract.py` + generated product-entry / family descriptor refs | `tests/test_stage_quality_contract.py` + product-entry action catalog parity |
| `P2` | `landed` | 对齐 OPL descriptor 中的 stage/skill/quality locator | product-entry manifest / skeleton mapping update | product-entry / OPL family adapter tests |
| `P3` | `pending` | 退役旧 compat vocabulary 或移入 history/reference | no default caller + replacement proof | `rg` stale scan + focused compatibility tests |
| `P4` | `pending` | 用真实 paper-line provider-hosted soak 验证 | OPL attempt -> MAS owner receipt -> artifact delta / gate replay / blocker | real paper-line read-only/guarded apply evidence |

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
- 真实 paper-line evidence 能证明 stage closeout、memory writeback、AI reviewer、gate replay、artifact delta、human gate 或 typed blocker 沿 MAS owner surface 闭合。
