# Life Science Research Learning Intake

Status: `clean_room_source_discovery_pack_landed`
Date: `2026-05-27`
Owner: `MedAutoScience Source Readiness + Quality OS`
Purpose: 记录 OpenAI Life Science Research 插件中可学习的生命科学 source discovery / evidence helper 模式如何以 MAS-native contract、refs-only source adapter output、product-entry descriptor 和测试面吸收。
State: `patterns_adopted_into_mas_owner_surfaces; no_external_dependency; no_external_authority`
Machine boundary: 本文是人读 clean-room intake。它不新增 runtime provider、默认 skill source、source readiness authority、publication authority、quality verdict authority、artifact authority 或机器可读验收面。机器真相继续归 `stage_quality_pack_contract`、MAS source adapter output、stage knowledge packet、evidence/review ledgers、AI reviewer、controller decisions、owner receipts、typed blockers 和 workspace source/artifact refs。

## 来源

本轮核对的是 OpenAI 官方 `openai/plugins` 仓库中的 `plugins/life-science-research`，本地浅克隆 observed head 为 `603a6e80711116e3584c33ecb8897548ed03d4f6`。

该插件定位为 Codex 的通用 life-sciences research layer，打包 50 个 modular skills。核心模式是：先解释研究问题，规范 gene/protein/disease/variant/compound/tissue/species/accession/pathway 等实体，再选择最小有用技能集合，必要时并行独立 evidence lanes，最后综合 genetics、omics、biology、chemistry、clinical evidence、literature 和 public dataset discovery 的证据与 caveat。

## Adopt / Watch / Reject

| disposition | pattern | MAS absorption |
| --- | --- | --- |
| `adopt_contract` | `research-router-skill` 的实体规范化、最小 evidence lane、独立 lane 才并行、冲突/缺口 synthesis | 吸收到 `life_science_source_discovery_pack`，由 `stage_quality_pack_contract` 投影；只形成 source refs、review input refs、typed blocker 或 source repair route。 |
| `adopt_contract` | literature / public study discovery：NCBI Entrez、PMC、bioRxiv、ClinicalTrials.gov、NCBI Datasets 等 | 映射到 `literature_intelligence_os`、`literature_provider_runtime`、stage knowledge packet 和 evidence ledger refs；不能授权 source readiness verdict。 |
| `adopt_contract` | human genetics / variant evidence：Open Targets、GWAS Catalog、ClinVar、gnomAD、Ensembl、GTEx、locus-to-gene mapper | 映射到 source readiness refs、claim evidence refs 和 reviewer caveat refs；association、cohort ranking、p 值和模型预测不能写成因果或临床结论。 |
| `adopt_template` | expression、functional genomics、protein/pathway、chemistry/pharmacology、多组学 dataset context | 作为按 study archetype 选择的 optional stage evidence refs；先不进入默认执行路径，不成为 provider readiness authority。 |
| `watch_only` | PheWAS cohort、large dataset API、GraphQL schema、PharmGKB/HMDB/IPD access、CELLxGENE/ENCODE/PRIDE/MetaboLights/MGnify 大 payload | 需要 ancestry、版本、license、rate-limit、dataset citation 和 source currentness 证据后才能晋级。 |
| `reject` | 把 50 个外部 skills 注入 MAS `skill_catalog` 或作为 MAS runtime/default skill source | MAS 保持单一 `mas` domain app skill；外部插件只作为 clean-room pattern/source catalog 输入。 |
| `reject` | 复制外部脚本、prompt、schema、目录布局或 runner semantics | 本轮只落地 MAS-owned contract 和 refs-only source adapter helper，不复制外部代码。 |
| `reject` | API 成功、cache hit、raw payload、script exit、provider ranking、association p-value 或 model prediction 直接授权 readiness/quality | 这些只能形成 source refs、caveat、typed blocker、review input 或 source repair route。 |

## Landed MAS Surfaces

- `life_science_source_discovery_pack`：作为一等 stage quality pack 进入 `stage_quality_pack_contract`，覆盖 source families、required record fields、router pattern、implementation policy 和 forbidden authority。
- `build_life_science_source_adapter_output()`：在 MAS source adapter 边界内生成 refs-only output，要求 `source_family_id`、`provider_id`、`accessed_at`、`query_fingerprint`、`checked_at` 和 `expires_or_stale_after`。
- product-entry / OPL descriptor：`family_stage_control_plane_descriptor.source_refs.life_science_source_discovery_pack_source` 和 `quality_pack_contract.source_discovery_pack_ref` 只暴露 locator，不新增外部 skill。
- skill catalog：继续只暴露单一 `mas` skill；Life Science Research 不成为 visible default skill source。

## Required Source Record Fields

进入 MAS source adapter output 的记录必须至少具备：

- `record_id`
- `source_pointer`
- `refs`
- `metadata.source_family_id`
- `metadata.provider_id`
- `metadata.accessed_at`
- `metadata.query_fingerprint`
- `metadata.identifier_crosswalk`
- `metadata.version_or_release`
- `metadata.limitation_flags`
- `metadata.checked_at`
- `metadata.expires_or_stale_after`
- `body_included=false`
- `write_mas_truth=false`
- `rejection_log`

缺 entity normalization、query fingerprint、provider provenance、currentness proof、source refs 或 rejection log 时，只能 fail closed、typed blocker 或 source repair route。

## Authority Boundary

Life Science Research derived surfaces 不得输出：

- `source_readiness_verdict`
- `quality_verdict`
- `publication_readiness`
- `submission_readiness`
- `mas_truth_write`
- `artifact_authority`
- `current_package` mutation

外部 source / skill 名称只作为 provenance labels。最终 source readiness verdict、医学质量 verdict、publication route、artifact mutation authorization 和 owner receipt 仍归 MAS AI-first stage gate、controller decision、evidence/review ledger、AI reviewer 和 owner surface。

## Acceptance Evidence

Repo-level landed evidence:

- `tests/test_life_science_source_discovery_pack.py`
- `tests/test_life_science_source_adapter_output.py`
- `tests/product_entry_cases/action_catalog_parity_cases/life_science_source_pack_cases.py`
- `tests/product_entry_cases/product_entry_markdown_and_skill_catalog.py`

Expected verification when touching these surfaces:

```bash
scripts/run-pytest-clean.sh tests/test_life_science_source_discovery_pack.py tests/test_life_science_source_adapter_output.py tests/product_entry_cases/action_catalog_parity_cases/life_science_source_pack_cases.py -q
scripts/run-pytest-clean.sh tests/test_stage_quality_contract.py tests/test_product_entry.py -q
make test-meta
scripts/verify.sh
```

Remaining live evidence tail:

- 真实 paper-line source discovery output 被 stage knowledge packet 消费。
- Evidence/review ledger 留下 source refs、query fingerprint、currentness proof、caveat 和 rejection log。
- AI reviewer-backed `publication_eval/latest.json` 使用这些 refs 做 reviewer input，而不是把 provider result 当质量结论。
- Controller decision 或 owner receipt 明确处理 source gap、route-back、human gate 或 typed blocker。

