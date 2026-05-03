# Open Auto Research Learning Intake 2026-05-04

这份记录对应维护者触发的 “PaperOrchestra 相邻 Auto Research 开源项目” fresh learning intake。目标是把近期外部 open-source auto research / deep research / multi-agent research workflow 中可复用的机制转成 `MAS` owner 下的 contract、template、watch list 和后续落地计划；不是把外部框架、skill pack、provider runtime 或论文生成器接成 `MAS` 第二运行时。

本轮在线检索截至 `2026-05-04`。GitHub API 在本机请求中触发 rate limit，因此 star / release 等热度信号只作为网页可见近似信号；本记录的可执行依据以官方 repo、官方 docs、论文页和项目页中可核对的机制为准。

## Source Snapshot

### Paper / experiment generation systems

- [PaperOrchestra](https://github.com/Ar9av/PaperOrchestra) / [paper](https://arxiv.org/abs/2604.05018): multi-agent AI research paper writing; prior MAS intake already landed the input tuple, staged writing DAG and evaluator watch record.
- [AI-Scientist-v2](https://github.com/SakanaAI/AI-Scientist-v2) / [paper](https://arxiv.org/abs/2504.08066): generalized end-to-end scientific discovery with progressive agentic tree search and an experiment manager agent; source license is not a MAS code-adoption basis.
- [AI-Scientist v1](https://github.com/SakanaAI/AI-Scientist): template-bound autonomous research generation; useful as a high-success template-lane contrast to v2 exploratory search.
- [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) / [paper](https://arxiv.org/abs/2501.04227): three-stage literature review, experimentation and report writing with human feedback at each stage.
- [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw): 23 stages across 8 phases, gate stages, PIVOT / REFINE research decisions, resume / from-stage execution, citation verification, sandboxed experiments and per-run lessons.
- [OpenAI PaperBench](https://openai.com/index/paperbench/) / [code](https://github.com/openai/preparedness/tree/main/project/paperbench) / [paper](https://arxiv.org/abs/2504.01848): 20 ICML 2024 papers, 8,316 individually gradable tasks, author-co-developed hierarchical rubrics and LLM judge evaluation.
- [ResearchTown](https://github.com/ulab-uiuc/research-town) / [docs](https://docs.auto-research.dev/) / [paper](https://arxiv.org/abs/2412.17767): simulator of a human research community using researcher agents, environments and finite-state engines.

### Literature / deep research systems

- [PaperQA2 / paper-qa](https://github.com/Future-House/paper-qa) / [PaperQA2 announcement](https://www.futurehouse.org/research-announcements/paperqa2-achieves-sota-performance-on-rag-qa-arena-science-benchmark) / [paper](https://arxiv.org/abs/2409.13740): scientific literature RAG with metadata-aware retrieval, contextual summaries, citation / journal quality metadata and LitQA2-style evaluation.
- [Open Deep Research](https://github.com/langchain-ai/open_deep_research): configurable open-source deep research agent over multiple model providers, search tools and MCP servers; records Deep Research Bench updates.
- [STORM / Co-STORM](https://github.com/stanford-oval/storm) / [STORM paper](https://arxiv.org/abs/2402.14207): Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking; pre-writing reference collection, perspective-guided questioning, simulated expert conversation, outline and article generation.
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher) / [docs](https://docs.gptr.dev/): autonomous online research agent with planner / researcher / writer / publisher flow, source tracking and MCP data-source support.
- [AutoSurvey](https://github.com/AutoSurveys/AutoSurvey) / [paper](https://arxiv.org/abs/2406.10252): survey generation and evaluation using retrieval, outline generation, subsection drafting, integration, refinement and RAG/reference budgets.
- [SurveyX](https://github.com/IAAR-Shanghai/SurveyX) / [paper](https://arxiv.org/abs/2502.14776): AttributeTree and two-stage survey preparation / generation; open implementation is not yet a MAS core dependency candidate.
- [OpenResearcher](https://github.com/TIGER-AI-Lab/OpenResearcher) / [paper](https://arxiv.org/abs/2603.20278): fully open long-horizon deep-research trajectory synthesis over offline search / open / find primitives and a 15M-document corpus.
- [MiroFlow](https://github.com/MiroMindAI/MiroFlow) / [paper](https://arxiv.org/abs/2602.22808): open-source deep research agent framework with agent graph, optional deep reasoning mode, robust execution and benchmark reproduction.

### Runtime / orchestration systems

- [OpenHands](https://github.com/OpenHands/OpenHands) / [runtime architecture](https://docs.openhands.dev/usage/architecture/runtime): sandboxed action execution server, REST action / observation protocol, Docker / local / remote execution and runtime plugin surface.
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution) / [persistence](https://docs.langchain.com/oss/python/langgraph/persistence) / [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview): checkpointed graph state, resumable execution, replay / time travel, human interrupts, subagents and virtual filesystem.
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) / [trajectories](https://swe-agent.com/0.7/usage/trajectories/) / [CLI](https://swe-agent.com/latest/usage/cli/): Docker sandbox, replayable trajectories, batch evaluation and run-replay.
- [CAMEL Workforce](https://docs.camel-ai.org/key_modules/workforce) / [CAMEL](https://github.com/camel-ai/camel) / [OWL](https://github.com/camel-ai/owl): coordinator, task planner, dynamic workers, snapshots, pause / resume, status, log tree, KPI and failure handling.
- [CrewAI Flows](https://docs.crewai.com/en/concepts/flows) / [production architecture](https://docs.crewai.com/en/concepts/production-architecture): Flow controls state and execution; Crews are work units delegated by a stateful flow.
- [Microsoft AutoGen](https://github.com/microsoft/autogen) / [termination docs](https://microsoft.github.io/autogen/0.4.8/user-guide/agentchat-user-guide/tutorial/termination.html): useful termination / handoff concepts, but current official repo state is not a MAS dependency target.
- [MetaGPT](https://github.com/FoundationAgents/MetaGPT): SOP-as-team and structured artifacts; useful as a watch reference, not a medical research runtime owner.

## Decision Matrix

| Lesson | Decision | MAS mapping | Boundary |
| --- | --- | --- | --- |
| PaperBench hierarchical rubrics and author-co-developed task trees | `adopt_contract` | Add future `MAS Evaluation OS` paper-specific rubric tree, judge calibration and score-tree evidence for manuscript / analysis reproduction. | Rubric score cannot authorize medical publication quality; `publication_eval/latest.json` and AI reviewer judgement remain authority. |
| PaperQA2 scientific literature RAG, metadata-aware retrieval and contradiction detection | `adopt_contract` | Strengthen medical literature hydration with citation-grounded QA, metadata provenance, full-text evidence summaries, contradiction flags and guideline-aware retrieval. | PaperQA2 is not imported as a dependency in this tranche; medical evidence authority remains MAS ledger / audit surface. |
| STORM multi-perspective question asking and outline-first pre-writing | `adopt_template` | Use perspective discovery for introduction / discussion / reviewer-revision framing before drafting. | Wikipedia-style or generic web article generation is not a MAS manuscript owner. |
| Open Deep Research graph decomposition: search, research, compression and final report | `adopt_template` | Split literature scan, evidence compression and report/writeback into visible work units with source ledgers and final report lineage. | Generic web research does not replace PubMed / DOI / guideline / study evidence hierarchy. |
| LangGraph checkpoint / replay / human interrupt discipline | `adopt_contract` | Map to `active_run_id -> durable step snapshots -> resumable runtime_watch` and controller-owned interrupt / resume contract. | Replay of side-effect actions must be guarded by MAS idempotency records; external graph runtime is not adopted. |
| OpenHands action-observation sandbox and SWE-agent trajectories | `adopt_contract` | Treat runtime tool execution as sandboxed action -> observation -> trajectory proof, with batch replay and artifact lineage. | MAS cannot execute untrusted autonomous code outside controlled runtime / workspace gates. |
| AI-Scientist-v2 progressive agentic tree search | `adopt_template` | Represent competing analysis / experiment hypotheses as bounded candidate path graph with stop, pivot, refine and evidence rules. | MAS does not import custom-licensed code or use open-ended ML paper discovery as medical quality authority. |
| Agent Laboratory stage-level human feedback and checkpointing | `adopt_template` | Move human feedback checkpoints to direction lock, experiment design, evidence interpretation and submission-facing gate. | Human feedback does not become hidden manual authorship of derived artifacts. |
| AutoResearchClaw 23-stage PIVOT / REFINE, citation gate and per-run lessons | `adopt_contract` | Adopt stage-gate language for literature screen, experiment design, quality gate, pivot/refine route-back and failure-to-lesson projection. | Reject auto-approve finalization and graceful degradation for medical publication gates. |
| GPT Researcher planner / crawler / writer / publisher and source ledger | `adopt_template` | Useful for product-entry research intake: question decomposition, source summary ledger and publisher-style final report materialization. | Source aggregation is evidence intake only, not claim validation. |
| CAMEL Workforce pause / resume / status / KPI and CrewAI Flow-over-Crew control split | `adopt_template` | Reinforce MAS principle: controller / flow owns state and gates; agents do bounded work units; operator projection shows status / KPI. | Dynamic worker expansion cannot bypass `controller_decisions/latest.json` or study truth. |
| OpenResearcher and MiroFlow offline trajectories / benchmark reproduction | `watch_only` | Watch for future reproducible deep-research eval hygiene, offline search corpora and long-horizon trajectory schemas. | Not a current MAS dependency or runtime target. |
| ResearchTown researcher-community simulation | `watch_only` | Useful for future reviewer rehearsal, consensus review and rebuttal simulation. | Simulation output cannot become publication gate authority. |
| AutoSurvey / SurveyX survey taxonomy and reference/RAG budgets | `watch_only` | Useful for disease/domain evidence taxonomy and taxonomy-vs-grounding budget split. | Open implementations and generic survey metrics are insufficient for medical evidence authority. |
| AI-Scientist v1 template-bound lane | `watch_only` | Useful as a high-success template-lane contrast for tightly scoped MAS reporting workflows. | Template success must not be mistaken for open-ended discovery quality. |
| External skill-pack, provider UI, generic persona library or framework runtime identity | `reject` | MAS keeps single MAS skill, CLI, MCP, controller and durable truth surfaces. | No external framework becomes MAS product entry, publication owner or study truth owner. |

## MAS Learning Plan

### Immediate absorb lanes

1. `Evaluation OS rubric tree`: promote PaperBench-style hierarchical rubrics into MAS quality-regression planning. The first acceptable landing is a contract/read-model surface that records rubric nodes, evidence refs, judge calibration and human/AI reviewer distinction.
2. `Medical literature evidence graph`: promote PaperQA2 / STORM / Open Deep Research lessons into PubMed / DOI / guideline-aware source ledgers, metadata-aware evidence summaries, contradiction detection and perspective-guided outline planning.
3. `Runtime trajectory proof`: promote LangGraph / OpenHands / SWE-agent lessons into durable step snapshots, action-observation records, replay-aware side-effect guards and batch verification evidence.
4. `Candidate path graph`: promote AI-Scientist-v2 / AutoResearchClaw lessons into bounded candidate analysis paths with explicit `proceed`, `refine`, `pivot`, `stop` and route-back decisions.

### Near-term template lanes

1. `Research intake planner`: GPT Researcher-style question decomposition and source-summary ledger for `product-frontdesk` / `workspace-cockpit` research intake.
2. `Perspective-first writing packet`: STORM / Co-STORM style multi-perspective question generation before introduction, discussion and reviewer-revision writing.
3. `Stage feedback checkpoint`: Agent Laboratory / AutoResearchClaw style checkpoints at literature screen, experiment design, evidence interpretation and final package audit.
4. `Operator work-unit projection`: CAMEL / CrewAI style state, pause/resume, KPI and worker log projection, constrained to MAS controller authority.

### Watch lanes

- `OpenResearcher` and `MiroFlow`: offline long-horizon trajectories, reproducible benchmark environments, trajectory schema and retrieval-success-vs-answer-accuracy analysis.
- `ResearchTown`: simulated research community, reviewer rehearsal and consensus critique.
- `AutoSurvey`, `SurveyX` and `SurveyForge`-style survey systems: evidence taxonomy, outline memory and reference budget techniques.
- `AutoGen` successor direction and `MetaGPT` SOP materials: termination conditions, run introspection and artifact discipline.

## Owner Boundaries

- `MAS study truth` remains in `study_charter`, evidence / review ledgers, `study_runtime_status`, `runtime_watch`, `publication_eval/latest.json` and `controller_decisions/latest.json`.
- `MAS Quality OS` owns medical writing quality, scientific quality, publishability and route-back semantics.
- `MAS Evaluation OS` may record rubrics, judge calibration and quality-regression evidence, but cannot authorize publication quality by itself.
- `MAS Runtime OS` may record action-observation trajectories, checkpoints and resume proof, but cannot silently re-execute side-effect actions without idempotency evidence.
- `MAS Artifact OS` owns canonical rebuild proof and artifact lineage; external generators cannot directly patch `current_package` or submission-facing artifacts.
- External projects stay source references. Their code, licenses, provider adapters, UI shells, skill packs and role/persona libraries are not MAS dependencies in this tranche.

## Continued Learning Saturation Protocol

后续继续学习 Auto Research 项目族时执行：

1. 固定 source date、official source links、paper / docs coverage、license / dependency risk if relevant。
2. 将 lesson 分类为 `adopt_contract`、`adopt_template`、`watch_only` 或 `reject`。
3. 只有能改变 MAS `Quality OS`、`Artifact OS`、`Evaluation OS`、`Runtime OS`、`Observability OS`、operator projection 或 meta tests 的 lesson 才进入 landing lane。
4. 已由 MAS 合同覆盖的 lesson 标记为 `saturated_by_existing_contract`，不得重复新增同义文档。
5. 只剩 provider / UI / generic role-play、non-medical benchmark、license-risk code adoption、skill-pack identity、unbounded autonomous paper generation 或重复表述时，当前 source snapshot 视为 `MAS-actionable saturated`。

## MAS Landing Rule

本轮可接受的落地方式是 selective learning：吸收可加强医学文献证据、pre-draft 规划、层级 rubric、长期运行轨迹、候选路径搜索、stage gate 和 operator projection 的合同或模板；观察需要医学 fixture / reproducible environment / benchmark calibration 后才能进入主线的机制；拒绝任何把研究真相、论文质量判断、artifact authority 或 controller decision 移交给外部 open-source framework 的模式。
