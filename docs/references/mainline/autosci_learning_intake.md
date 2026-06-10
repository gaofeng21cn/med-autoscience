# AutoSci Learning Intake

Status: `clean_room_research_lifecycle_contract_landed`
Date: `2026-05-28`
Owner: `MedAutoScience Source Truth + Quality OS + Artifact OS`
Purpose: 记录 `skyllwt/AutoSci` / `OmegaWiki` 中可学习的研究 wiki、source discovery、实验生命周期、reviewer verdict 和 poster artifact 模式如何以 MAS-native contract、quality pack、product-entry projection 和 tests 吸收。
State: `patterns_adopted_into_mas_owner_surfaces; no_external_dependency; no_external_runtime_authority`
Machine boundary: 本文是人读 clean-room intake。机器真相继续归 `src/med_autoscience/autosci_learning_projection.py`、`stage_quality_pack_contract`、product-entry manifest、domain-handler export、evidence/review ledgers、AI reviewer、controller decisions、owner receipts、typed blockers 和 artifact authority refs。

Landing boundary: 本 reference 记录 AutoSci / OmegaWiki pattern 的 MAS-owned projection 与 quality-pack absorption；projection 或 contract 不单独证明 execution landing。是否可写成 landed，按 [External Learning Adoption Closure Runbook](../../runtime/control/external_learning_adoption_closure.md) 的 landing status 判断，并继续保留 no external runtime / no authority boundary。

## 来源

本轮核对的是 `https://github.com/skyllwt/AutoSci`，本地浅克隆 observed head 为 `d89cc72a884a2d091b6fac5719f30b4c64d2c6bd`。README 当前以 `OmegaWiki` 为产品名，核心形态是 wiki-centric research lifecycle：paper/source ingestion、typed wiki graph、idea generation、experiment design/run/eval、paper writing/review 和 poster artifact。

该项目本轮只作为 external pattern source。MAS 不引入它作为 runtime dependency、Claude slash skill source、remote runner、permission model、source readiness authority、quality verdict authority、publication authority 或 artifact authority。

## Adopt / Watch / Reject

| disposition | pattern | MAS absorption |
| --- | --- | --- |
| `adopt_contract` | typed wiki graph：entities / edges / xref / conventions，把 semantic edges、citation edges、reverse refs、terminal exception 和 append-only log 分开 | 落到 `mas_autosci_learning_projection.knowledge_graph_contract` 和 `life_science_source_discovery_pack.typed_knowledge_graph_edge_contract`；MAS 不复制 AutoSci taxonomy，映射到 study/source/evidence/review/publication/artifact refs。 |
| `adopt_contract` | `/discover` 只推荐不写入，`/daily-arxiv` 只有显式 `auto-ingest` 且 high confidence 才进入 ingest | 落到 `proposal_action_source_discovery_contract`；candidate shortlist 不能写 MAS truth，真实 ingestion/source repair 必须走 MAS owner-authorized action。 |
| `adopt_contract` | failed / eliminated ideas 写入 `failure_reason`，作为 anti-repetition memory | 落到 `negative_research_memory_contract`；失败 hypothesis、重复 route、reviewer rejection 或 typed blocker 只有经 `memory_write_router_receipt` 才能进入 reusable memory。 |
| `adopt_template` | idea -> pilot -> formal experiment，`exp-run` deploy / monitor / collect，`exp-eval` 独立 verdict | 落到 `experiment_lifecycle_receipt_contract`；MAS analysis campaign 只消费 design/deploy/monitor/collect/eval refs 和 controller next-route，不把 deploy success 写成 analysis success。 |
| `adopt_contract` | independent reviewer output 映射 verdict、score、weakness、action 和 wiki/source mapping | 落到 `independent_reviewer_verdict_mapping_contract`；self-review 不能关闭 quality gate，分歧走 conservative route-back 或 typed blocker。 |
| `adopt_template` | poster pipeline 的 source DAG、figure manifest、render QA、overflow check 和 reviewer critique | 落到 `source_dag_render_qa_artifact_contract`；render success 是 artifact projection evidence，不授权 publication readiness 或 artifact mutation。 |
| `watch_only` | prompt-level `writers.yaml` 权限表 | 上游自身是 descriptive policy，不是 fail-closed runtime gate；MAS 只能吸收为 descriptor，不作为权限系统。 |
| `watch_only` | Paper Copilot / S2 / DeepXiv ranking 权重 | 推荐信号有价值，但医学 source readiness 需要 PubMed/CrossRef/PMC/guideline/cohort provenance，不直接采用 CS venue/citation ranking。 |
| `watch_only` | GitHub Actions daily cron | 可作 notification / digest artifact scaffold；MAS generic runtime owner 仍是 OPL/Temporal。 |
| `reject` | 直接依赖外部 Claude Code slash skills、SSH/rsync/screen remote runner、prompt-only permission、partial authoritative ingest success、AutoSci entity taxonomy、self-review 降级 gate | 与 MAS 标准 OPL Agent target、AI reviewer independence、source/publication/artifact authority 和 fail-closed owner receipts 冲突。 |

## Landed MAS Surfaces

- `build_autosci_learning_projection()`：生成 MAS-owned external pattern projection，固定 source snapshot、absorbed pattern ids、watch/reject 边界和 authority boundary。
- `stage_quality_pack_contract`：在既有 quality packs 上新增 AutoSci-derived extension contracts：
  - `ai_native_expert_judgment_pack.independent_reviewer_verdict_mapping_contract`
  - `life_science_source_discovery_pack.proposal_action_source_discovery_contract`
  - `life_science_source_discovery_pack.typed_knowledge_graph_edge_contract`
  - `route_memory_pack.negative_research_memory_contract`
  - `statistical_analysis_pack.experiment_lifecycle_receipt_contract`
  - `paper_presentation_pack.source_dag_render_qa_artifact_contract`
- Product-entry manifest：暴露 `autosci_learning_projection`，并在 `family_stage_control_plane_descriptor` 内嵌同一 projection。
- Domain-handler export：暴露 `autosci_learning_projection` 作为 refs-only OPL-readable domain descriptor。
- `contracts/opl-framework/family-contract-adoption.json#autosci_learning_projection`：固定 descriptor surfaces、target quality-pack contracts、allowed/forbidden export 和 authority boundary。

## Authority Boundary

AutoSci-derived surfaces 不得输出：

- source readiness verdict
- quality verdict
- publication readiness
- submission readiness
- artifact mutation authorization
- MAS truth write
- evidence/review ledger body
- publication eval / controller decision body
- external runtime provider or slash-command runner

它们只能形成 refs、metadata、freshness、typed blocker、owner boundary、quality pack descriptor 或 route-back input。最终医学 source readiness、publication quality、artifact mutation、memory writeback 和 owner receipt 仍归 MAS owner surfaces。

## Acceptance Evidence

Repo-level landed evidence:

- `tests/test_autosci_learning_projection.py`
- `tests/test_stage_quality_contract.py`
- `tests/test_opl_family_contract_adoption.py`
- `tests/product_entry_cases/action_catalog_parity_cases/stage_descriptor_cases.py`
- `tests/test_cli_cases/owner_route_handoff_command_cases/export_cases.py`

Expected verification when touching these surfaces:

```bash
scripts/run-pytest-clean.sh tests/test_autosci_learning_projection.py tests/test_stage_quality_contract.py tests/test_opl_family_contract_adoption.py tests/product_entry_cases/action_catalog_parity_cases/stage_descriptor_cases.py tests/test_cli_cases/owner_route_handoff_command_cases/export_cases.py -q
make test-meta
scripts/verify.sh
```

Remaining live evidence tail:

- 真实 source discovery line 输出 candidate shortlist、decision artifact、source adapter rejection log、typed blocker 或 source repair route。
- 真实 analysis campaign 留下 design/deploy/monitor/collect/eval refs，并由 independent reviewer / controller route 消费。
- 真实 paper deliverable 的 poster/slide/visual abstract 生成 source DAG、figure manifest、render QA、reviewer critique 和 artifact authority receipt 或 typed blocker。
