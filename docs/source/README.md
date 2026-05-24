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

## Literature Provider Runtime

`Semantic Scholar` 是 MAS `literature_provider_runtime` 必需 provider 的仓内可执行 adapter/source。它的角色是把 Semantic Scholar 查询、论文元数据、引用图谱和候选文献结果物化为 MAS 可审计的 source record；它不是外部 hosted provider service、不是 production long-soak 证明，也不是医学 grounding authority。

该 provider surface 必须保持 read-model-only。Semantic Scholar adapter/materializer 可以产出 provider readiness、candidate source refs、metadata/citation enrichment、screening input 和 blocker refs；不能授权 source readiness verdict、publication quality、submission readiness、finalize readiness、artifact mutation、controller decision 或 publication gate 通过。

每次 provider 查询和物化都必须保留可追溯 ledger，而不是只保存整理后的候选列表。最低可审计信息包括 raw provider response ledger、credential scope、rate-limit state、cache key/status、query fingerprint、citation ledger refs、screening reason、currentness/freshness proof、dedupe/crosswalk decision 和 typed blocker。缺这些 refs 时，stage knowledge packet、workspace canonical literature 或 study reference context 只能 fail closed 或 route to source repair。

`PubMed`、`CrossRef` 和 `PMC` 继续承担医学 grounding、DOI/PMID/PMCID crosswalk、full-text / metadata reconciliation 和 provenance 校准。Semantic Scholar 可以扩展 discovery、citation-neighborhood 和 metadata enrichment，但不能替代 PubMed/CrossRef/PMC 的医学证据 grounding，也不能把 provider ranking、citation count、abstract match 或 cache 命中写成医学结论。
