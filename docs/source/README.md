# Source 文档

Owner: `MedAutoScience`
Purpose: `medical_source_workspace_support`
State: `active_support`
Machine boundary: 人读索引。Source truth 继续归 study workspaces、external-source ledgers、canonical data、manifests、source contracts 与 owner receipts。

本目录承接 MAS study workspace、source readiness、external research intake、source provenance 和 source truth consumption 支撑。通用 workspace/source shell 候选应记录为 MAS-to-OPL 上收候选。

当前入口先看：

- [架构](../architecture.md)
- [当前状态](../status.md)
- [References](../references/README.md)
- [Workspace Knowledge And Literature Contract](../runtime/contracts/workspace_knowledge_and_literature_contract.md)
- [Standard Domain Agent Skeleton](../runtime/contracts/standard_domain_agent_skeleton.md)

## Standard Agent Source Boundary

标准 OPL Domain Agent skeleton 只把 repo-source 语义面固定到 `agent/`、`contracts/`、`runtime/` 和 `docs/` 这些 anchors。它不会把 workspace source body、provider raw response body、publication-route memory body、artifact body、quality verdict 或 submission package 纳入仓库。

MAS 继续持有 source truth、source readiness verdict、medical grounding、source provenance 和 owner receipt。OPL generated / hosted surfaces 可以消费 source refs、locator refs、provider readiness、currentness/freshness proof 和 typed blocker refs，但不能写 MAS source truth，也不能把 source-provider 查询成功、metadata enrichment、cache hit、candidate ranking 或 descriptor readiness 升级成 source readiness verdict。

## Literature Provider Runtime

`Semantic Scholar` 是 MAS `literature_provider_runtime` 必需 provider 的仓内可执行 adapter/source。它的角色是把 Semantic Scholar 查询、论文元数据、引用图谱和候选文献结果物化为 MAS 可审计的 source record；它不是外部 hosted provider service、不是 production long-soak 证明，也不是医学 grounding authority。

该 provider surface 必须保持 read-model-only。Semantic Scholar adapter/materializer 可以产出 provider readiness、candidate source refs、metadata/citation enrichment、screening input 和 blocker refs；不能授权 source readiness verdict、publication quality、submission readiness、finalize readiness、artifact mutation、controller decision 或 publication gate 通过。

每次 provider 查询和物化都必须保留可追溯 ledger，而不是只保存整理后的候选列表。最低可审计信息包括 raw provider response ledger、credential scope、rate-limit state、cache key/status、query fingerprint、citation ledger refs、screening reason、currentness/freshness proof、dedupe/crosswalk decision 和 typed blocker。缺这些 refs 时，stage knowledge packet、workspace canonical literature 或 study reference context 只能 fail closed 或 route to source repair。

`PubMed`、`CrossRef` 和 `PMC` 继续承担医学 grounding、DOI/PMID/PMCID crosswalk、full-text / metadata reconciliation 和 provenance 校准。Semantic Scholar 可以扩展 discovery、citation-neighborhood 和 metadata enrichment，但不能替代 PubMed/CrossRef/PMC 的医学证据 grounding，也不能把 provider ranking、citation count、abstract match 或 cache 命中写成医学结论。

## Life Science Source Discovery Pack

OpenAI Life Science Research 插件的可学习内容已按 clean-room pattern 吸收到 MAS `life_science_source_discovery_pack` 和 refs-only source adapter output。它提供实体规范化、多 evidence lane 路由、公共数据库 / 文献 / 数据集 discovery、cross-source conflict 和 evidence gap synthesis 的 source helper 纪律；不成为 MAS runtime provider、默认 skill source、source readiness authority、publication authority 或质量 verdict owner。

进入 MAS 的输出只能是 source refs、query fingerprint、currentness proof、limitation/caveat refs、typed blocker、source repair route 或 reviewer input refs。完整 intake 见 [Life Science Research Learning Intake](../references/mainline/life_science_research_learning_intake.md)。

## AutoSci / OmegaWiki Research Lifecycle Intake

`skyllwt/AutoSci` 的可学习内容已按 clean-room pattern 吸收到 MAS `autosci_learning_projection` 和 stage quality pack extension contracts。MAS 采用的是 typed knowledge graph、proposal/action source discovery split、negative research memory、experiment deploy/collect/eval receipts、independent reviewer verdict mapping 和 source-DAG render QA 这些 contract 形状；不采用 AutoSci 的 Claude slash skills、remote GPU runner、prompt-only permission policy、partial authoritative ingest success 或通用 CS wiki taxonomy。

进入 MAS 的输出只能是 source candidate refs、semantic/citation/provenance edge refs、dedup/currentness proof、memory writeback proposal/ref、experiment design/deploy/monitor/collect/eval refs、reviewer verdict refs、render QA refs、typed blocker 或 owner receipt。完整 intake 见 [AutoSci Learning Intake](../references/mainline/autosci_learning_intake.md)。

## Co-Scientist Hypothesis Portfolio Intake

Co-Scientist 的可学习内容已按 clean-room pattern 进入 MAS `hypothesis portfolio / evidence pack` 叙事。MAS 采用的是候选假设组合、source/evidence refs、反思与演化记录、相邻/重复假设聚类、negative / failed-path ledger、decision trace 和独立 reviewer / human gate closeout 这些 contract shape；不采用外部 Co-Scientist runtime，也不把 Elo、ranking、proximity 或 novelty score 写成 source readiness、医学质量或 publication authority。

进入 MAS 的输出只能是 hypothesis refs、source refs、evidence pack refs、candidate comparison advisory、proximity cluster advisory、reviewer input refs、human/expert gate refs、typed blocker 或 owner receipt。完整 intake 见 [Co-Scientist Hypothesis Portfolio Intake](../references/mainline/co_scientist_hypothesis_portfolio_intake.md)。

## ARK Research Workflow Intake

`kaust-ark/ARK` 的可学习内容已按 clean-room pattern 转译为 MAS reviewer issue/progress ledger、display artifact manifest、source citation authority pack 和 progress-first external learning contract。MAS 学习的是 review loop、goal anchor、issue repair validation、API-first citation、figure manifest、page adjustment、human-intervention UX、micro-study canary、operator preview、real-run closeout、compiled visual QA 和 citation lifecycle queue 的 contract shape；不采用 ARK runtime、SQLite authority、conda project model、Telegram/webapp service、agent prompt、代码或依赖。

进入 MAS 的输出只能是 reviewer issue refs、goal-anchor currentness proof、typed repair work unit、platform repair work unit、source-refresh work unit、artifact/layout QA work unit、operator preview ref、typed blocker、reviewer/auditor input 或 owner receipt。完整 intake 见 [ARK Research Workflow Intake](../references/mainline/ark_learning_intake.md)。
