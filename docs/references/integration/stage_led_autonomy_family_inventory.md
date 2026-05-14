# MAS Stage-Led Autonomy Family Inventory

Status: `descriptor adapter landed`
Date: `2026-05-10`
Owner: `MedAutoScience`
Purpose: inventory MAS Stage-Led Autonomy surfaces for OPL family descriptor projection without changing MAS study routes, controller runtime, publication authority, or execution kernel.
State: `reference inventory plus MAS-owned descriptor projection`
Machine boundary: this is human-readable inventory material. Machine truth remains in `stage_route_contract.yaml`, `stage_knowledge_plane_contract`, `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, `stage_recall_index`, evidence/review ledgers, controller decisions, runtime status, publication eval, and generated study artifacts.

## 结论

OPL family plan 在这一层只应做 `inventory / descriptor projection`：读取、索引和描述 MAS 已有 Stage-Led Autonomy surface，帮助 family-level runtime、catalog、operator UI 或 cross-domain adoption 识别能力边界。它不替换 MAS route contract，不改 route id，不增减 stage，不重排 controller runtime，也不写 study truth、publication truth、package truth 或 AI reviewer judgment。

MAS 当前的 Stage-Led Autonomy 已由以下 MAS-owned surfaces 承接：

- `stage_knowledge_packet`：给探索性 stage 注入 memory、literature、evidence、review、claim boundary 与 citation readiness 输入。
- `stage_memory_closeout_packet`：要求 stage closeout 使用 typed categories 表达 reusable lessons、citation gaps、failed paths、reference role updates、evidence/review ledger repair requests、controller decision requests、human gates 和 claim boundary decisions。
- `memory_write_router_receipt`：把 closeout proposed writes 受控路由到 workspace memory proposal、literature repair request、failed path history、reference context update request、evidence/review repair request 或 controller decision request，并保留 rejected writes 与 typed blockers。
- `stage_recall_index`：把 stage knowledge packets 和 memory router receipts 汇总成 stage recall read model，供后续 stage、Progress/Portal 和 operator projection 读取。

这些 surface 已经满足 Stage-Led Autonomy 的核心要求：stage 保持研究思考与探索空间，controller 继续守医学边界、证据账本、owner route、质量门禁、stop-loss 与 human gate。OPL family descriptor 只能把这些能力投影出去，不能把投影反向升级为 MAS authority。

MAS 现在通过 product-entry manifest 暴露 MAS-owned 标准 `family_stage_control_plane` 和深度 `family_stage_control_plane_descriptor`。前者供 OPL `stages list|inspect` 直接发现，后者保留 route snapshot、packet surfaces、memory closeout/router/recall surface、evidence/review/controller/publication refs 和 `authority_boundary` 的深度来源；两者只用于 OPL family-level indexing / display / freshness / MAS-exported dispatch discovery，不派生 route，不授权质量或投稿 readiness。

2026-05-11 update，2026-05-12 Markdown-first 校准：同一 manifest 现在也暴露 MAS-owned `domain_memory_descriptor`，其 `memory_ref_id=mas_publication_route_memory`。这个 descriptor 只提供 publication-route memory 的 policy、Markdown canonical body ref、seed index、workspace locator、stage applicability、retrieval/writeback/receipt/recall refs、migration plan ref、writeback receipt locator、freshness 和 forbidden OPL authority；它不包含 memory 正文，不授权 OPL 选择论文路线，也不把 writeback 接受/拒绝、evidence/review/controller/publication 或 artifact authority 移出 MAS。

2026-05-12 update: fresh OPL family CLI read model 已能解析 MAS/MAG/RCA 三个 standard domain-agent skeleton、`18` 个 family stages 和 `3` 个 domain-memory descriptor。MAS 的 domain-memory descriptor 当前 `migration_readiness.status=workspace_apply_closure_ready`，表示 Markdown canonical library、seed index、workspace apply、workspace memory pack locator 和 writeback receipt locator 已具备 MAS owner apply closure；OPL 仍只消费 locator / receipt refs / freshness，不持有 memory body 或 accept/reject authority。

## Scope Guard

本 inventory 固定以下边界：

- 保留 `stage_route_contract.yaml` 作为 MAS route contract source，不从 OPL descriptor 派生 route id 或 stage 数量。
- 保留 `docs/policies/study-workflow/stage_led_research_autonomy.md` 作为 Stage-Led Autonomy policy，不把本文件变成 policy。
- 保留 `stage_knowledge_plane_contract` 与四个 packet/read-model surface 作为 MAS machine-readable boundary，不在 OPL 侧复制第二套 schema authority。
- 保留 `study_charter`、`evidence_ledger`、`review_ledger`、AI reviewer-backed `publication_eval/latest.json` 和 `controller_decisions/latest.json` 作为医学质量与路线 authority。
- OPL descriptor 可以记录 family capability、surface owner、projection fields、read-only freshness 和 dispatch boundary；不能写 MAS study truth 或授权 publication readiness。

## Current MAS Surfaces

| surface | current owner | current role | family projection recommendation |
| --- | --- | --- | --- |
| `docs/policies/study-workflow/stage_led_research_autonomy.md` | MAS policy owner | Stable policy for `stage-led autonomy, controller-governed evidence` | `keep` as policy reference; expose descriptor link only |
| `docs/active/ai_first_paper_autonomy_closure_program.md` | MAS program owner | Program context tying AI reviewer repair, route decision, stage knowledge/memory, and real-paper soak | `keep` as program context; do not use as runtime contract |
| `agent/stages/stage_route_contract.yaml` | MAS route contract owner | Route contract for scout, idea, baseline, experiment, analysis-campaign, write, review, finalize, decision, journal-resolution, entry modes, gates, outputs, and route-back triggers | `keep`; OPL maps route descriptors from this source read-only |
| `src/med_autoscience/controllers/stage_knowledge_plane.py` | MAS controller/knowledge-plane owner | Machine surface for stage knowledge packets, typed closeout, memory routing receipts, and recall index | `map_to_descriptor`; descriptor mirrors surface metadata, required fields, owner, and authority boundary |
| `product-entry-manifest.family_stage_control_plane` | MAS product-entry projection owner | OPL-standard stage plane for `stages list|inspect`, mapped to existing MAS routes and action catalog refs | `landed`; OPL may consume it as descriptor only |
| `product-entry-manifest.family_stage_control_plane_descriptor` | MAS product-entry projection owner | Read-only deep family descriptor for `stage_led_autonomy` source refs, route snapshot, packet/read-model surfaces and authority boundary | `landed`; OPL may consume it as descriptor only |
| `product-entry-manifest.domain_memory_descriptor` | MAS product-entry projection owner | Read-only `publication_route_memory` locator for OPL `domain-memory list|inspect`, stage `knowledge_refs`, and writeback receipt projection | `landed`; OPL may consume locator / freshness / receipt refs only |
| `tests/test_stage_knowledge_plane.py` | MAS test owner | Verifies packet surface contract, exploratory stage obligations, missing reasons, typed closeout routing, idempotency, owner targets, and blockers | `keep`; OPL must not replace these MAS tests with family-level prose checks |
| `tests/test_stage_knowledge_entry_injection.py` | MAS test owner | Verifies entry injection consumes stage knowledge surfaces in route materialization | `keep`; expose existence as descriptor evidence |
| `tests/test_stage_knowledge_visibility.py` | MAS test owner | Verifies Progress/Portal visibility for stage knowledge and memory writeback surfaces | `map_to_descriptor`; family UI can consume visibility projection read-only |

## Classification Inventory

| category | MAS surfaces | recommendation | rationale |
| --- | --- | --- | --- |
| `expert_stage` | `stage_route_contract.yaml` route contracts for `scout`, `idea`, `baseline`, `experiment`, `analysis-campaign`, `write`, `review`, `finalize`, `decision`, `journal-resolution`; `stage_led_research_autonomy.md` | `keep` | Stage contracts encode key questions, enter conditions, hard success gates, durable outputs, human gate boundaries, next routes, and route-back triggers. They are MAS-owned stage discipline, not OPL-generated plans. |
| `guard` | `study_charter`, evidence/review ledgers, AI reviewer-backed `publication_eval/latest.json`, `controller_decisions/latest.json`, stage authority boundary fields | `split_authority` | Guards authorize medical boundary, quality, evidence, route, stop-loss, and human gate decisions. Family projection may show guard status, but MAS remains authority. |
| `router` | `memory_write_router_receipt`, proposed write destinations, owner targets, rejected writes, typed blockers, controller decision requests | `map_to_descriptor` | Routing metadata is useful for family-level queue/projection, but routed writes must execute through MAS owner surfaces. |
| `reconciler` | `stage_memory_closeout_packet`, idempotency keys, source fingerprints, typed closeout normalization, rejected study-specific workspace memory writes | `keep` | Reconciliation protects authority split and prevents free-text memory from becoming truth. OPL descriptor can report status and blockers only. |
| `dispatcher` | MAS owner routes, supervisor/sidecar paper autonomy dispatch, gate replay and AI reviewer recheck requests referenced by the autonomy closure program | `split_authority` | OPL can dispatch only MAS-exported typed pending tasks or descriptors. It must not infer medical actions from read models or prose. |
| `evaluator` | AI reviewer workflow, `publication_eval/latest.json`, review ledger, bounded analysis and route decision surfaces, stop-loss memo expectations | `keep` | Evaluator authority decides paper quality pressure and route-back. OPL may display evaluation state but cannot close reviewer-first or finalize-ready gates. |
| `read_model` | `stage_recall_index`, Progress/Portal stage knowledge visibility, product/operator projection surfaces | `downgrade_to_read_model` for any family-owned copy | Any family-side aggregation should stay projection-only, carrying source refs, freshness, owner, and non-authority flags. |

## Descriptor Projection Shape

MAS now exposes the family descriptor for this lane as `family_stage_control_plane_descriptor`; the descriptor stays thin and read-only:

- `domain_id`: `med-autoscience`
- `capability_id`: `stage_led_autonomy`
- `authority_owner`: `MAS`
- `route_contract_source`: `agent/stages/stage_route_contract.yaml`
- `knowledge_plane_contract_source`: `stage_knowledge_plane_contract`
- `packet_surfaces`: `stage_knowledge_packet`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, `stage_recall_index`
- `allowed_family_actions`: `index`, `display`, `freshness_check`, `dispatch_mas_exported_task`
- `forbidden_family_actions`: `write_study_truth`, `replace_route_contract`, `authorize_publication_quality`, `authorize_submission_readiness`, `promote_memory_to_evidence`, `infer_medical_route_from_projection`
- `source_refs_required`: policy ref, route contract ref, contract surface ref, test evidence ref, freshness/refingerprint if materialized

This descriptor is generated against MAS-owned surfaces. It carries route IDs/counts as a snapshot from `stage_route_contract.yaml`, but it does not define, add, remove, reorder or authorize routes. It should not hard-code route wording, stage counts, or Markdown paragraphs as a family truth source.

## Domain Memory Descriptor Shape

MAS exposes publication-route memory to OPL as `domain_memory_descriptor`:

- `surface_kind`: `family_domain_memory_ref`
- `memory_ref_id`: `mas_publication_route_memory`
- `memory_family`: `publication_route_memory`
- `memory_pack_ref`: policy seed plus workspace locator for MAS-owned route memory material
- `stage_applicability`: `scout`, `idea`, `decision`, `analysis-campaign`, `review`
- `retrieval_contract_ref`: `stage_knowledge_packet`
- `writeback_contract_ref`: `stage_memory_closeout_packet`
- `receipt_contract_ref`: `memory_write_router_receipt`
- `recall_projection_ref`: `stage_recall_index`
- `migration_plan_ref`: `docs/policies/study-workflow/publication_route_memory_policy.md#migration-plan`
- `seed_corpus_ref`: `docs/policies/study-workflow/publication_route_memory_seed_fixture.json`
- `writeback_receipt_locator_ref`: `portfolio/research_memory/publication_route_memory/writeback_receipts`
- `migration_readiness`: `workspace_apply_closure_ready`; real memory body migration and writeback receipt instances remain MAS workspace-owned
- `authority_boundary`: OPL is locator projection owner only; forbidden authorities include memory store, domain truth, quality verdict, artifact authority, publication route decision, publication readiness and submission readiness.

The standard `family_stage_control_plane` now links route-sensitive stages to this descriptor through `knowledge_refs`. OPL may display and inject the ref into provider attempts; MAS still owns actual retrieval, closeout normalization, router receipt, accepted/rejected writes, and publication route decisions. For human/operator inspection, the current MAS owner entry is `medautosci publication route-memory-inventory --workspace-root <workspace>`, which defaults to body-free card metadata, locators, filters, receipt summary and authority boundary; `--include-card-body` is reserved for maintainer-level prose review.

## Adoption Recommendations

| recommendation | applies to | action |
| --- | --- | --- |
| `keep` | MAS route contracts, policy, AI reviewer/publication quality authority, evidence/review/controller surfaces | Preserve in MAS unchanged; family adoption reads them as owner surfaces. |
| `map_to_descriptor` | knowledge-plane contract metadata, packet surface names, required fields, owner/freshness/source refs, Progress/Portal visibility | Add family descriptor fields that point back to MAS sources and declare non-authority behavior. |
| `downgrade_to_read_model` | any OPL-side stage memory index, dashboard aggregation, family catalog copy, operator UI projection | Store only source refs, status, freshness, and owner labels; never write back to MAS truth from the read model itself. |
| `split_authority` | dispatch, guard, evaluator, repair routing, human gate, publication readiness | OPL may queue or notify from MAS-exported typed tasks; MAS executes and writes receipts/decisions. |

## Descriptor Adapter Closeout

The first MAS-side adapter is now landed in the MAS product-entry projection. It deliberately avoids changes to route ids, stage count, controller runtime, publication gate, truth surfaces and execution kernel. The descriptor is validated by product-entry tests for source traceability, route contract snapshot stability, OPL read-only role, and MAS ownership of publication/quality authority.

No MAS route id, stage count, controller runtime, truth surface, or execution kernel change is required for first-round adoption.
