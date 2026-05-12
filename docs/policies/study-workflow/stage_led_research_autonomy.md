# Stage-Led Research Autonomy Policy

Status: `active policy`
Date: `2026-05-10`
Owner: `MedAutoScience`
Purpose: preserve exploratory research autonomy while keeping medical evidence, claim boundaries, and publication quality auditable.
State: `active operating policy`
Machine boundary: this is a human-readable policy. Machine truth remains in `study_charter`, `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, `stage_recall_index`, evidence/review ledgers, controller decisions, runtime status, publication eval, and generated result/manuscript/package surfaces.

2026-05-10 update: Stage-Led Autonomy 已由 `stage_knowledge_packet`、`stage_memory_closeout_packet`、`memory_write_router_receipt` 和 `stage_recall_index` 承接为 MAS-owned operating surface。它们给 stage 提供 memory/literature 输入、typed closeout 和受控写回，但不授权论文质量、claim 扩大或 publication readiness。

2026-05-11 memory apply update，2026-05-12 Markdown-first 校准：`publication_route_memory` 已从 descriptor/seed index 推进到 workspace apply closure。MAS 可把 repo Markdown canonical library 应用到 workspace-owned `publication_route_memory_pack`，stage entry 只消费小集合 `publication_route_memory_refs`，stage closeout 生成 typed writeback proposal，`memory_write_router_receipt` 负责接受、拒绝或阻断并写入 workspace receipt locator。repo seed JSON 只做 locator/index；repo 不保存真实 pack 或 receipt 实例；真实 artifact 仍属于 workspace/runtime root。

2026-05-11 status calibration: Stage-Led Autonomy 的核心 operating surface 已经落地；机械分流层已经降级为 audit/router/materializer，但仍有兼容入口、historical reader、fixture 和旧命名残留。开发纪律是先确认默认路径不再调用、direct skill 与 OPL handoff 都能回到同一 MAS-owned stage/route surface，再删除旧 vocabulary 或迁入 history；不能为了“清干净”破坏 restore/provenance/parity 证据。

2026-05-11 OPL integration calibration: OPL 现在可以把 MAS 识别为 aligned standard domain-agent skeleton、6-stage family stage plane，并把 `mas_publication_route_memory` 作为 MAS-owned resolved family domain-memory descriptor 解析；同一 OPL family index 也已能解析 MAG/RCA 的标准 domain-memory descriptor。这个状态说明 stage-led autonomy 已具备被 OPL 托管的 descriptor / memory / sidecar 条件；它仍不等于真实 paper line 已完成 provider-hosted long-running soak。MAS 的研究判断、publication quality、claim boundary、artifact authority 继续只由 MAS durable truth surface 持有。

2026-05-12 OPL platform calibration: OPL family index fresh read 显示 MAS/MAG/RCA 三个 domain agent 均 descriptor-aligned，family stage plane 共 `18` 个 stages，domain-memory descriptor 共 `3` 个且无 missing；MAS 的 `mas_publication_route_memory` descriptor 已被 OPL 解析为 MAS-owned locator。OPL family-runtime 当前本机 provider 是 `local_sqlite`，`provider_ready=true`，`full_online_ready=false`，`durable_online_ready=false`；OPL roadmap 已落地 Temporal provider core、attempt start/query/signal、worker helper、Temporal residency proof 和 Codex runner harness。这个状态把 MAS 的 OPL-hosted 条件从 descriptor-only 推到 local provider 可执行/可索引阶段，但 production Temporal service、managed worker residency、真实 paper-line live apply soak 和 human gate/resume 运行证明仍是目标态缺口。

## 总目标与运行模型

MAS 的总目标是长时间自治地完成高质量医学论文，而不是只自动运行一批分析脚本或拼接投稿包。

推荐运行模型是：

- 人类专家经验先拆分研究 stage，并为每个 stage 定义医学目标、进入条件、自由度、禁区、质量要求和退出条件。
- `Codex CLI` 作为强执行器，在 stage packet 约束内自主探索、实现、验证、修复和总结。
- `AI-first` 质量层像 PI、统计审稿人和医学审稿人一样督工：检查 stage 初版输出是否达到医学、统计、证据和写作要求；未达到时驱动修复、补证、降级、转向或止损。
- 对会影响论文走向的 stage，例如 scout、idea、baseline、experiment、analysis-campaign、review 和 decision，必须保留灵活探索机制，而不是只执行固定 checklist。
- 每个 stage closeout 都必须留下 durable outputs，供下一 stage、controller 和 AI reviewer 读取；系统推进依赖这些 durable surfaces，而不是依赖聊天记忆。

因此，MAS 的自动化应是 `expert-stage decomposition + Codex autonomous execution + AI-first supervision + controller evidence governance`。stage 负责产生高质量初版研究结果，AI-first 负责判断是否达标并推动完善，controller 负责把边界、证据、路线和人类审批守住。

## 结论

MAS 的研究推进不应被设计成“程序替 Codex 逐条排序分析清单”。正确形态是：

- `controller` 负责医学边界、权限、证据账本、质量门禁、owner route 和止损。
- `stage` 负责研究思考、候选路线、方法比较、结果解释和下一步判断。
- `Codex CLI` 是强执行器，应在 stage 目标、医学先验、数据边界和审计输出约束下自由探索，而不是被 controller 拆成过细的机械任务。

换句话说，MAS 要采用 `stage-led autonomy, controller-governed evidence`：用 stage/skill 给 Codex 足够大的研究空间，用 controller 保证医学诚实性、可复现性、可回放和人类可审计。

## 为什么需要这条 policy

当前 MAS 已有 `study_line_decision_engine`、`route_decision_orchestrator`、bounded-analysis candidate board 和统计纪律 surface。它们能表达候选方向、弱结果、route-back、bounded repair、switch line 和 stop-loss。

风险在于，如果这些 surface 变成主驱动，MAS 会退化成：

1. 先按固定维度给方向打分。
2. 机械选择一个方向。
3. 运行一组预列分析。
4. 结果强就写，结果弱就补几个有界分析。
5. 最后把剩余阳性结果包装成论文。

这不是理想的医学科研自治。它会削弱 Codex CLI 的推理和执行能力，也会让研究路线变得保守、局部、缺少真正的方向探索。

这些结构化 surface 应该作为 `audit and routing contract`，而不是作为 `thought generator`。真正的研究思考应发生在 `scout`、`idea`、`baseline`、`experiment`、`analysis-campaign`、`write`、`review`、`decision` 这些 stage 内。

## 两类探索能力

### 1. 非 ML 医学研究方向探索

多数 MAS 论文不会涉及算法创新，但仍然需要研究方向探索。这里的探索不是盲目试 p 值，而是围绕医学问题寻找最强、最诚实、最有发表价值的研究形态。

这类探索至少包括：

- clinical problem reframing：同一数据能回答哪个临床问题最有意义。
- population / phenotype exploration：人群、亚型、暴露、结局和时间窗是否有更合理定义。
- data affordance scan：数据真实支持哪些结论，哪些只是写作想象。
- literature gap mapping：当前数据能否填补临床或指南中的真实空白。
- endpoint and display exploration：什么 endpoint / table / figure 最能表达医学价值。
- claim boundary search：主张应停在描述、关联、预测、分层、外部验证、流程改造还是机制增强。

输出不是一组固定分析清单，而是一个 `medical research frontier`：

- active clinical question
- plausible candidate paths
- rejected or deferred paths
- clinical priors and literature anchors
- data-fit and endpoint feasibility
- expected evidence gain
- stop / pivot rule
- next stage recommendation

### 2. ML / AI 课题的医学先验算法创新

当研究涉及机器学习、影像、病理、多模态、LLM/agent 临床任务或模型更新时，MAS 需要保留旧 DeepScientist/MDS 的 `algorithm_first optimize -> experiment -> frontier review` 能力。

但这条能力必须医学化。算法创新不能变成单纯 benchmark chasing。每个 algorithm-first frontier 都必须从医学问题出发：

- clinical bottleneck：当前临床任务为什么难。
- medical prior：医学知识、病理机制、诊疗流程或数据生成机制提供了什么先验。
- data contract：数据版本、模态、划分、外部验证和禁止更改项。
- evaluation contract：主指标、校准、临床效用、亚组、公平比较和失败条件。
- innovation scope：允许改模型、特征、训练、推理、融合、解释或 workflow 的哪一层。
- paper-facing rationale：为什么这个方法创新能回答医学问题，而不是只提高一个分数。

这条路线可以吸收 DeepScientist 的 candidate brief、durable line、implementation candidate、experiment、frontier review、fusion/debug/stop 纪律，但导入 MAS 主线时必须回写为：

- algorithm scout report
- innovation hypothesis
- final method proposal
- experiment result summary
- prior limitation analysis
- claim-to-evidence map
- failure and negative-result history

## Stage 与 Controller 的职责分离

### Stage 负责“怎么想”

每个研究 stage 都应给 Codex 一个较完整的研究问题，而不是一串微任务。stage packet 至少回答：

- 当前 stage 的 key question 是什么。
- 当前医学边界、数据边界和 claim 边界是什么。
- 有哪些可探索路径，为什么值得探索。
- 哪些动作被禁止，例如扩大人群、偷换 endpoint、事后改 primary claim。
- 允许的 freedom budget 是什么，例如候选方向数量、分析预算、外部数据范围、计算预算。
- 需要留下哪些 durable outputs。
- 什么情况必须进入 decision 或 human gate。

### Controller 负责“怎么守住”

controller 不应该替 Codex 做科研思考。controller 的职责是：

- 校验 stage 是否可进入。
- 冻结 study charter 和 human gate boundary。
- 读取 stage output 并写 owner route / controller decision。
- 防止越权 claim、隐藏负结果、重复派发、stale truth 和机械 gate 授权质量。
- 要求每个 stage closeout 都能回指 evidence refs、failed paths、next route 和 source fingerprint。

### 结构化评分负责“怎么审计”

`study_line_decision_engine` 这类评分面适合做比较和审计，不适合作为唯一生成器。

正确顺序是：

1. stage 内先产生医学上有意义的候选路线。
2. 再用结构化维度做比较、排序、阻断和记录。
3. 最终由 controller 把选择结果写入 durable decision。

如果反过来先让固定维度生成研究思路，系统会变得机械。

### 流程优化的开发纪律

后续优化研究流程时，默认优先改 `stage`、`skill`、stage packet、prompt contract 和 AI reviewer rubric，而不是新增程序化研究分流器。

允许保留或新增的程序控制只限于：

- boundary guard：权限、人群、endpoint、claim boundary、human gate 和 publication gate。
- evidence governance：ledger、source refs、citation refs、artifact freshness 和 replay proof。
- route router：把 stage closeout 转成 owner route、controller decision、repair work unit 或 human gate。
- observability：progress、Portal、Live Console、SLO、fingerprint、idempotency 和 retry budget。
- audit comparator：对 stage 已产生的候选路线做比较、排序、阻断和记录。

不允许保留或新增的程序控制包括：

- 自动生成研究问题并绕过 stage 思考。
- 把固定评分矩阵当作研究想法来源。
- 把 positive-result harvesting 当作路线选择。
- 用 mechanical gate 授权医学论文质量。
- 用 read model 或 projection 直接替代 Codex stage 的研究判断。

已有代码中如果存在“替 Codex 决定研究思路”的分流逻辑，应逐步退役、降级或重构为 guard / router / audit / read-model。清理时必须先保留行为 parity fixture，再把主动权迁回 stage/skill/prompt，最后删除旧入口，避免形成第二套污染源。

当前已完成的降级口径：

- `study_line_decision_engine` 只能比较 stage 产出的候选路线，角色是 `audit_comparator_only`。
- `route_decision_orchestrator` 只能把 stage output、evidence refs、failed paths 和 controller inputs 物化成 owner route、stop-loss 或 executable task，角色是 `route_router_and_materializer`。
- controller decision 必须带 `route_generation_owner=stage_output`，且 `can_generate_winning_path_without_stage_output=false`。
- 缺少 `stage_output_refs` 时，route decision write 应 fail-closed，而不是由程序从评分表直接生成 winning path。

仍需持续清理的对象：

- 只为历史 MDS / DeepScientist parity 保留的 compat vocabulary。
- explicit archive / restore / historical reader 中已经有新 MAS-owned reader 替代的入口。
- 只能服务旧 mechanical route 的 product-entry 或 MCP projection。
- 文档中把 `router`、`materializer` 或 `read model` 写成 route thinker / quality owner 的表述。

与理想形态的剩余距离：

- `scout / idea / analysis-campaign / review / decision` 的 stage contract 已具备 autonomy policy 和 memory 输入/closeout 机制；DM002、DM003、Obesity 已给出 read-only typed closeout projection，但还需要 provider-hosted live apply 中证明 Codex CLI 长时间执行后能稳定生成 MAS owner receipt。
- `publication_route_memory` 已能作为 stage 输入和 closeout writeback proposal 载体，DM002 已形成 workspace memory pack / writeback receipt proof；还需要更多真实 reusable lesson 的 accepted/rejected receipt 和 stale/deprecated review 纪律。
- route decision / repair / gate replay 已经能作为 MAS owner callable surface 工作，但旧 mechanical vocabulary 和 historical compatibility reader 仍需按 parity gate 继续删除或归档。
- OPL 托管路径还需要通过 production Temporal provider residency、managed worker 长驻、human gate/resume 和真实 paper-line live apply 证明不降低 direct MAS app skill 路径的能力，不改变 MAS owner route，不绕过 AI reviewer / publication gate。

## 文献、引用与研究记忆平面

MAS 需要保留旧 DeepScientist / MDS 中“参考文献、引用文献、研究记忆帮助 agent 不断累积上下文”的能力，但实现方式应按医学论文 authority 分层，而不是把 quest-local memory 直接作为论文真相源。

当前 MAS 的等价分层是：

- workspace canonical literature：跨 study 复用的文献 authority root，位于 `portfolio/research_memory/literature/registry.jsonl`、`references.bib` 和 `coverage/latest.json`。
- portfolio research memory：跨 study 复用的研究记忆，位于 `portfolio/research_memory/topic_landscape.md`、`dataset_question_map.md`、`venue_intelligence.md` 和 `study_recall_index.md`。
- study reference context：单篇 study 选中的 reference set，位于 `studies/<study_id>/artifacts/reference_context/latest.json`，并标明 `framing_anchor`、`claim_support`、`journal_fit_neighbor`、`adjacent_inspiration` 等角色。
- quest materialization：runtime working copy，位于 `quest_root/literature/*`、`quest_root/paper/references.bib` 和 `quest_root/paper/reference_coverage_report.json`，只能作为本轮执行材料，不升级为 canonical truth。
- literature provider runtime / literature intelligence OS：把 PubMed、Crossref、Semantic Scholar 等 provider 响应、检索策略、来源 provenance、citation ledger refs、guideline / systematic review / journal neighbor refs 和 evidence node provenance 投影成可审计 surface。
- evidence and citation ledgers：所有写作引用、claim 支撑和 reviewer-facing evidence 必须回指 evidence / citation refs，不能只依赖记忆卡片或正文叙述。

与旧 DeepScientist 的关系如下：

- 旧 DeepScientist 的 `memory.write/read/search/list_recent/promote_to_global` 更偏通用 quest/global memory card，适合 prompt-led stage 在每轮开始时检索可复用经验。
- MAS 的当前实现更偏医学 publication authority：先把文献与研究记忆分到 workspace、study、quest 三层，再让 stage packet、readiness、AI reviewer 和 publication gate 消费。
- 因此，MAS 在 citation grounding、文献 authority 和跨 study 复用上更强；Stage-Led Autonomy 落地后，旧 MDS generic memory service 的目的已通过 authority split 方式承接，但不追求 1:1 复刻自由文本 memory truth service。

当前默认约束不是恢复一个第二 truth source，而是让每个探索性 stage 在进入时显式读取 `stage_knowledge_packet`，在 closeout 时生成 typed `stage_memory_closeout_packet`，再由 `memory_write_router` 把可复用 lesson、失败路径、引用缺口和研究方向判断回写到正确层级。这样既保留 DeepScientist 的探索记忆能力，又不牺牲 MAS 的医学证据和引用纪律。memory / literature 只能作为输入、lesson、citation gap 或 route evidence，不能授权 publication quality、claim expansion 或 finalize readiness。

### Publication route memory

高产出论文套路应作为 `publication_route_memory` 进入 stage knowledge plane，而不是做成程序化 recipe engine。

这类记忆包括 clinical classifier / risk stratification、clinical subtype reconstruction、external validation / model update、gray-zone triage、survey trend analysis、mechanistic sidecar extension 等可复用发表路线经验。它们应保持自然语言为主，带少量检索元数据，用于帮助 Codex CLI 在当前数据、文献和 charter 边界内自主思考。

使用规则：

- route memory 通过 `stage_knowledge_packet` 小批量注入当前 stage，不把整库塞进提示词。
- route memory pack 与 migration/writeback receipts 位于 MAS workspace `portfolio/research_memory/publication_route_memory/`，OPL 只持 locator refs。
- route memory 只提供经验、警示、常见 evidence package、figure/table route 和失败模式。
- `scout` / `idea` / `decision` 仍必须产出自己的 candidate routes、rejected paths、selection rationale 和 stop/pivot rule。
- 结构化比较器只能审计 stage 已产出的候选路线，不能从 memory card 自动生成 winning path。
- 成熟经验可通过 `stage_memory_closeout_packet` 提议写回；写回必须经 `memory_write_router` 按 owner surface 分流。

详细维护规则见 [Publication Route Memory Policy](./publication_route_memory_policy.md)。

## 结果不理想时的实质行为

弱结果或负结果不应只改变一个状态字段。它必须产生实质行为差异：

- `debug`：怀疑数据、代码、endpoint、变量方向、模型设定或统计计划有问题时，启动有界诊断。
- `bounded_repair`：当前 claim 仍可能成立，但缺失必要敏感性、亚组、外部验证或展示支撑时，启动补充 evidence campaign。
- `claim_downgrade`：主结果不足以支持原 claim 时，降级为更诚实的描述、关联、探索性或限定条件 claim。
- `switch_line`：同一 charter 边界内另一条候选路线明显更强时，切换研究线。
- `return_to_scout`：当前 candidate frontier 整体不足时，回到方向探索。
- `stop_loss`：继续尝试只会制造 post-hoc narrative 时，停止当前 paper line。
- `human_gate`：涉及临床解释、伦理/权限、目标期刊策略或边界重置时交给人类。

这些动作的区别应体现为不同 owner route、不同 required outputs、不同 artifact delta predicate 和不同 next route，而不是只在 dashboard 上显示不同标签。

## Stop-loss 裁决

任何 stage 都可以发现 stop-loss 信号，但正式止损只能由 `decision` stage 和 controller decision 完成。

各 stage 的职责如下：

- `scout`：发现研究问题没有临床意义、文献空白不存在、数据根本不能回答问题，提出 `return_to_scout`、`switch_line` 或 `stop_loss_candidate`。
- `idea`：候选路线整体 novelty、clinical relevance、data fit、journal fit 或 external validation ceiling 不足，提出 `stop_loss_candidate` 或选择替代路线。
- `baseline`：基线、队列、endpoint、样本量、缺失或可重复性不足以支撑主 claim，提出 `claim_downgrade`、`bounded_repair` 或 `stop_loss_candidate`。
- `experiment`：主结果无效、不可复现、反向或与医学解释冲突，提出 `bounded_repair`、`switch_line`、`claim_downgrade` 或 `stop_loss_candidate`。
- `analysis-campaign`：补充分析进入 plateau，新增结果不能提高证据强度或只能靠 post-hoc narrative 支撑，提出 `stop_loss_candidate`。
- `write`：写作时发现 claim-evidence map 无法闭合、正文只能靠包装弱证据成立，必须 route back 到 `decision`，不能继续美化。
- `review`：AI reviewer 判断 novelty、rigor、evidence、citation 或 claim restraint 不足且修复收益低，提出 `stop_loss_candidate` 或 human gate。
- `decision`：汇总 evidence refs、failed paths、repair attempts、alternative routes、human gate boundary 和 publication fit，正式写出 continue、bounded repair、claim downgrade、switch line、return to scout、stop-loss 或 human gate。

正式 stop-loss 至少需要：

- attempted paths and failed paths
- evidence gain ceiling
- why bounded repair cannot close the gap
- why claim downgrade / switch line is insufficient or deferred
- publication fit and ethics/permission boundary
- recommended archive / memory writeback
- human gate question if final termination needs human confirmation

这条规则的目的不是让 MAS 更保守，而是防止系统为了完成论文把不可发表路线包装成阳性故事。

## 关于“朝阳性结果努力”

MAS 可以朝“最强可证据化结论”努力，不能朝“制造阳性结果”努力。

允许的努力包括：

- 选择更合理的 endpoint 定义。
- 检查错误编码、缺失、时间窗和数据质量。
- 比较统计上正当的模型族。
- 做预先声明或有医学理由的亚组、敏感性和稳健性分析。
- 将强 claim 降级成数据确实支持的较弱 claim。
- 改写研究问题，让它更贴近数据真实能力和临床价值。

禁止的努力包括：

- 隐藏失败分析。
- 多重尝试后只报告显著结果。
- 事后把 exploratory 结果写成 primary evidence。
- 为了维持结论突破 study charter、权限或人群边界。
- 把 nominal p-value 当作唯一发表价值。

## 推荐目标架构

MAS 的顶层研究循环应分成四层。

### Layer 1: Charter and Boundary

冻结医学问题、数据来源、权限、人群、endpoint、claim boundary、reporting guideline、human gate 和目标读者。

该层回答：当前可以探索什么，绝不能探索什么。

### Layer 2: Stage-Led Research Frontier

每个 stage 由 Codex 在 stage packet 内自由探索：

- `scout`：临床问题和文献空白探索。
- `idea`：候选研究线生成、比较和选择。
- `baseline`：验证数据和主方向是否足够成立。
- `experiment`：当需要模型、算法、主实验或计算任务时执行。
- `analysis-campaign`：围绕 claim / reviewer / evidence gap 做有界补强。
- `write`：把当前证据转成 manuscript-native medical prose。
- `review` / AI reviewer：像审稿人一样打回 claim、evidence、novelty、rigor 和 writing gap。
- `decision`：继续、转向、降级、止损或 human gate。

该层回答：研究上下一步最聪明的动作是什么。

### Layer 3: Evidence and Route Control

所有 stage closeout 都必须变成 durable evidence：

- stage packet
- candidate frontier
- accepted / rejected paths
- result refs
- failed path history
- claim-evidence map
- display-to-claim map
- controller decision
- next owner route

该层回答：这次探索留下了什么可审计证据，下一步由谁执行。

### Layer 4: Publication Quality Closure

AI reviewer、publication gate、medical writing quality、reporting checklist 和 package rebuild proof 负责最终质量闭环。

该层回答：当前论文是否真的可以对外，而不是系统是否已经“忙过”。

## 开发拆解

### P0: 固定本 policy 和 route 语义

把 stage-led research autonomy 明确为 MAS 的长期设计原则。后续改动不得把 route contract 退化为机械 checklist executor。

### P1: Stage packet / knowledge packet operating contract

为 `scout`、`idea`、`baseline`、`experiment`、`analysis-campaign`、`write`、`review`、`decision` 固定统一 stage packet：

- key question
- current boundary
- clinical prior
- candidate frontier
- freedom budget
- forbidden moves
- evidence obligations
- failed paths
- next route
- high_signal_memory
- literature_gaps
- citation_readiness
- current_claim_boundary
- source_fingerprint

`scout`、`idea`、`analysis-campaign`、`review` 是强制消费 `stage_knowledge_packet` 的核心探索 stage。`write` / `finalize` 读取 evidence/review/claim map，不开放扩大探索。

### P2: Medical research frontier surface

在 `idea` 和 `analysis-campaign` 之间增加医学研究 frontier 投影。它应表达临床逻辑、数据能力和文献空白，而不只是分数表。

### P3: Executable negative-result loop

让 weak / negative / contradictory / blocked result 自动进入不同实质动作：debug、bounded repair、claim downgrade、switch line、return to scout、stop-loss 或 human gate。

### P4: Medically grounded algorithm-first lane

对 ML/AI 课题恢复 algorithm-first 能力，但必须由 MAS charter 输入医学先验和评价契约；算法 sidecar 或 optimize loop 只能在这些边界内探索。

### P5: Real paper soak and parity proof

用真实论文线验证：

- 非 ML 临床统计论文能保持探索性，而不是固定清单执行。
- ML/AI 论文能进入 algorithm-first frontier，而不是只做统计补充。
- 负结果会产生真实路线变化，而不是 dashboard 标签变化。
- 写作前能看到 claim-evidence、display-to-claim 和 failed-path 历史。

## 验收标准

一个高质量 MAS 研究循环必须满足：

- Codex 在 stage 内有足够研究自由，而不是只执行微任务列表。
- 每次自由探索都有 durable closeout，不依赖聊天记忆。
- 医学先验、文献空白、数据能力和 claim 边界都能在 route decision 里看见。
- 弱结果会改变实质 route，而不是只显示 blocker。
- algorithm-first 只在医学任务需要时进入，且输出可导入论文证据链。
- 所有阳性、阴性、弱、反向和失败路径都能在 ledger 或 failed path history 中追踪。
- stage entry 必须显示消费了哪些 knowledge / literature refs，不能退化成静态 docs 链接或聊天记忆。
- stage closeout 必须通过 typed router receipt 显示 accepted / rejected writes、route impact 和 next owner。

## 非目标

- 不恢复旧 MDS daemon 作为第二 owner。
- 不让 OPL/Hermes 解释 MAS study truth 或 publication quality。
- 不把 Bayesian optimizer、AutoML 或 evolutionary search 作为所有医学论文的默认依赖。
- 不把探索自由解释成允许 p-hacking、claim expansion 或绕过 human gate。
- 不把 Markdown policy 作为机器 truth；实现仍必须落到 controller/runtime/schema/ledger surface。
