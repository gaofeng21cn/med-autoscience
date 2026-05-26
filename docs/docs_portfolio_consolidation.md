# MAS 文档组合治理

Status: `active_docs_governance`
Owner: `MedAutoScience`
Purpose: `docs_lifecycle_governance`
State: `active_support`
Machine boundary: 本文是人读治理入口。MAS 机器真相继续归 runtime/controller/schema/source/generated surfaces、CLI/MCP/API 行为、study workspace artifacts、domain manifests、owner receipts 和语义化 `human_doc:*` id。

## 当前结论

`docs/**` 是 MAS 的中文内部开发与维护参考，不维护 docs 层双语镜像。稳定路径优先使用无语言后缀 `.md` 承载中文 canonical 内容。历史文件可以保留旧双语、旧路径或 dated 过程描述作为 provenance，但 active/reference 索引必须指向当前无后缀路径。

MAS 采用 OPL-family canonical docs taxonomy：

`active/public/product/runtime/delivery/source/policies/specs/references/history`

这个目录集合按长期职责保留，不按当前文件数量决定。`product/public/source/specs` 当前可以较薄，但必须在 README 或 owner 文档中说明进入条件和不进入条件。

## 生命周期原则

- 主文档只记录最新情况：当前定位、当前边界、当前功能/结构差距、测试/证据差距、完善顺序和禁止误写口径。
- 历史演变、dated evidence、process follow-through、closeout 过程、旧 board、旧 activation package 和完整流水进入 `docs/history/**`。
- 如果历史文件仍含 current truth，先抽取当前结论进入当前 owner 文档，再保留原文件作为 provenance。
- 每份长期文档必须在开头或索引中明确 owner、purpose、state 和 machine boundary。`state=active_plan` 表示仍决定执行顺序；`state=active_support` 表示仍支撑当前 owner 但不自行排队；`support_reference` 表示参考材料；`history_only` / `history_provenance` 表示不能作为 current truth。
- 已落地基础文档只有在仍承担 guard、provenance 分类、source intake 规则或 drift 判断时才留在 `docs/active/`；纯过程、旧 lane table、旧 activation package、旧 full record 和 dated closeout 必须放入 `docs/history/**`。
- `docs/decisions.md` 保留决策日期日志；不要为了压缩过程流水而改写 decisions 的历史记录。
- dated specs、dated closeout 和历史 full record 不能直接作为 current truth；当前 truth 必须由核心五件套、当前 owner doc、machine-readable contract 或 runtime/controller surface 承载。
- `docs/status.md` 只维护当前状态摘要，不承载 dated follow-up ledger；执行顺序只在 `docs/active/current-development-lines.md` 维护；program 文档组合只在 `docs/active/program_portfolio_consolidation.md` 维护。2026-05-20 这轮收敛记录见 [Docs lifecycle governance closeout 2026-05-20](./history/program/docs_lifecycle_governance_closeout_2026_05_20.md)。
- OPL doc doctor 只作为预检信号：它可以提示缺少 lifecycle header、旧词汇或 active/history 边界风险，但不能直接变成执行清单。每条 warning 都必须回到 live source、contracts、tests、CLI/read-model、runtime receipt/blocker 或 canonical docs 证明后，才决定是更新 current owner 文档、折回 history/tombstone，还是保留为历史/决策语境。

## 与 OPL 的分层

OPL 系列项目全局主参考由 OPL 仓维护。MAS 文档只维护医学研究 domain agent 的目标、差距、study/publication/artifact authority、direct MAS app skill path、OPL-hosted sidecar/projection/receipt 边界，以及 MAS-to-OPL 上收候选。

MAG、RCA、MDS 或 OPL-owned App/workbench 的并行 backlog 不写入 MAS active docs。

## 目录职责

| 目录 | 长期职责 | 当前 MAS 承载 |
| --- | --- | --- |
| `docs/` root | docs 入口、核心五件套、docs governance | `README.md`、核心五件套、本文件。 |
| `docs/active/` | 当前执行、当前差距、active baton、当前 owner plan | current development lines、program portfolio、ideal-state gap plan、paper autonomy / OPL workbench / Temporal retirement / stage standardization 等 active owner docs。 |
| `docs/public/` | repo home 之后的公开叙事 | 当前较薄，保持 public narrative index；不承载 study truth。 |
| `docs/product/` | MAS app skill、product-entry、operator/workbench-facing guidance | direct path / product entry / OPL App drilldown 指南。 |
| `docs/runtime/` | runtime contracts、control、projection、display、active designs | 当前核心技术承载之一。完成或退役计划进入 `docs/history/runtime/`。 |
| `docs/delivery/` | manuscript、package、submission/export、medical-display 等交付支撑 | `delivery/medical-display/` 已承载能力族；domain artifact authority 仍归 MAS domain artifact surfaces。 |
| `docs/source/` | study workspace、source readiness、external intake、source truth consumption | 承接 workspace/source intake 与 source truth 边界。 |
| `docs/policies/` | 长期规则 | quality、study-workflow、runtime-governance、repo-ops。 |
| `docs/specs/` | 当前有效技术规格索引 | 新增 active spec 前先确认是否更适合 runtime/policies/references 或 machine contract。 |
| `docs/references/` | 支撑参考、定位、integration、MDS parity、workspace、med-deepscientist | target/support/reference，不承担 active owner，不保存 dated verification ledger。 |
| `docs/history/` | dated snapshot、provenance、retired board、process archive | 旧 `program/`、旧 `capabilities/`、runtime/OMX/superpowers history、过程性 closeout 摘要。 |

## 非 canonical 目录

旧 `docs/program/` 和 `docs/capabilities/` active 目录已物理退役：

- 当前 program-baton 材料进入 `docs/active/`。
- medical-display 能力族进入 `docs/delivery/medical-display/`。
- 历史 program/capability 材料只保留在 `docs/history/`，不得继续作为 recurring material 落点。

## 内容级整合规则

1. 当前 factual truth 合入核心五件套、runtime/controller/schema/source、machine-readable contract 或当前 owner doc。
2. 当前执行、差距、program baton 和仍决定下一步顺序的 owner plan 留在 `docs/active/`。
3. Runtime/control/projection/display 进入 `docs/runtime/`；完成或退役计划进入 `docs/history/runtime/`。
4. Medical display 和 delivery authority support 进入 `docs/delivery/`；真实 artifact authority 仍归 MAS domain artifact surfaces。
5. Source/workspace/intake 支撑进入 `docs/source/`；generic shell 候选记录为 MAS-to-OPL 上收边界。
6. 稳定规则进入 `docs/policies/`；一次性计划不得放入 policies。
7. MDS/DeepScientist 只作为 historical fixture、explicit archive import、backend audit、upstream intake、source provenance 或 parity oracle reference。
8. dated evidence、verification ledger、real-study verification note、follow-through、过程流水和 closeout 摘要进入 `docs/history/program/` 或相应 `docs/history/<area>/`。

## Direct Retirement

当旧模块、旧接口、旧 CLI alias、旧 wrapper、旧 facade、旧测试入口或旧文档入口已被当前 owner surface 替代时，默认直接退役。迁移 active caller 后删除旧面；需要来龙去脉时只保留 history/tombstone/provenance，不新增 compatibility shim、别名或聚合测试。

直接退役的判断顺序固定为：

1. 证明没有 default CLI/MCP/product-entry/app-skill/OPL active caller。
2. 证明没有 public surface、fixture 或 provenance 必须依赖该旧入口。
3. 证明 replacement owner surface、history link 或 tombstone contract 已存在。
4. 删除旧源码、命令 wrapper、alias、facade 和对应兼容测试；测试改断言当前 machine-readable contract、schema、CLI/API、manifest 或 generated artifact。

满足上述条件后，不保留旧名兼容层，不新增聚合兼容测试，也不把旧文档路径当成稳定机器接口。

## Path-Stable Active 文档收敛

少数 `docs/active/*.md` 仍被 `human_doc:*`、contract、source projection 或测试 manifest 指向。它们可以暂留原路径，但必须收窄为单一职责：

- `mas-ideal-state-gap-plan.md` 是唯一当前 gap / 完善计划。
- `current-development-lines.md` 是唯一当前执行内容地图。
- `program_portfolio_consolidation.md` 只解释旧 program 文档组合与生命周期，不维护第二 backlog。
- `ai_first_paper_autonomy_closure_program.md` 只定义论文自治验收合同。
- `stage_surface_standardization_program.md` 只维护 stage pack 形态。
- `opl_app_mas_runtime_workbench_program.md` 只维护 MAS refs-only projection 到 OPL App/workbench 的边界。
- `mas_single_project_mds_absorb_program.md` 与 `../runtime/domain_authority_refs_index_guard.md` 只保留 landed foundation guard、provenance 和 drift 判断。

这些路径暂留不是兼容承诺。若后续 machine/human_doc caller 迁出，且当前结论已吸收到 gap plan、runtime/source/delivery/policy 或 history，文档应直接移动到 `docs/history/**` 或 tombstone；不新增重定向文档、兼容 alias 或平行索引。

## Coverage Ledger

### 2026-05-26 product / workbench boundary tranche

本轮覆盖 MAS product/status/workbench、owner-route handoff、Progress Portal 和 OPL App/workbench 相关文档边界。目标是让 product 入口一眼指向当前 generated/default owner、strict source-purity tail、Progress Portal diagnostic path 和 OPL App 主工作台分层，避免把 repo-local product/status/workbench shell、Portal UI、OPL refs-only ledger、provider proof 或 App projection 写成 MAS paper closure、publication-ready、artifact authority、generic runtime owner 或 active source 可删除状态。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/README.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/active/program_portfolio_consolidation.md`, `docs/active/opl_app_mas_runtime_workbench_program.md`.
- Product / runtime / reference docs: `docs/product/README.md`, `docs/runtime/display/progress_portal.md`, `docs/runtime/projections/study_macro_state_and_owner_route.md`, `docs/references/integration/progress_portal_opl_app_integration.md`.
- Machine surfaces: `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`.
- CLI/read-model: `PYTHONPATH=src python -m med_autoscience.cli --help`, `PYTHONPATH=src python -m med_autoscience.cli workspace progress-portal --help`, and failed `product-entry` / `owner-route-handoff` probes that confirmed the current direct CLI names are `product-entry-*`, `sidecar-*`, `owner-route-reconcile`, `domain-action-request-materialize` and `domain-owner-action-dispatch`.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | `docs/product/README.md` full file; `docs/runtime/display/progress_portal.md` lifecycle header, entry conclusion, OPL App integration, runtime drilldown boundary, user experience contract, authority boundary, action endpoint, landed implementation surface; `docs/runtime/projections/study_macro_state_and_owner_route.md` owner-route sections; `docs/active/opl_app_mas_runtime_workbench_program.md` current role/status/lane/contract boundary; `docs/references/integration/progress_portal_opl_app_integration.md` entry conclusion, MAS/OPL responsibilities and forbidden upgrade boundary; `docs/status.md` product/workbench current machine facts; `docs/active/mas-ideal-state-gap-plan.md` `workbench_sidecar_status_cutover`, Progress Portal carrier thinning and next prompt. | `docs/product/README.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. `docs/runtime/display/progress_portal.md`, `docs/active/opl_app_mas_runtime_workbench_program.md` and `docs/references/integration/progress_portal_opl_app_integration.md` remain useful active/support documents; their larger dated subsections still need a future compaction pass before the entire files can be marked fully paragraph-covered.

Uncovered docs in this semantic area:

- `docs/product/inspection_package.md`.
- Remaining paragraph-level cleanup inside `docs/runtime/display/progress_portal.md`, especially older 2026-05 landed note chronology that should be folded when a dedicated Portal display-contract tranche is opened.
- Other integration references under `docs/references/integration/*.md` not listed above.

Remaining stale / retire candidates:

- Product/status/workbench/sidecar/controller/progress shell source remains an active strict source-purity tail, not a docs-retire item. Physical deletion still requires OPL generated/default caller cutover, active-caller proof, MAS owner receipt or typed blocker parity, focused tests, no-forbidden-write proof and tombstone/provenance refs.
- Progress Portal workspace carrier remains active diagnostic / no-App / evidence path because `medautosci workspace progress-portal`, `--serve` and `ops/mas/bin/start-web` are active callers.
- Older Progress Portal dated note chronology is a compaction candidate, but current text still carries display-contract support and should not be deleted without paragraph-level replacement into `docs/runtime/display/progress_portal.md`, history/provenance or machine contracts.

Next tranche write scope:

- MAS `docs/runtime/display/progress_portal.md` paragraph compaction and Portal display-contract coverage, or MAS `docs/runtime/projections/**` owner-route / domain-ref projection coverage.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

### 2026-05-26 Progress Portal display-contract tranche

本轮覆盖 MAS `docs/runtime/display/progress_portal.md` 的入口结论、历史 landed note、OPL App/workbench boundary、runtime drilldown boundary、UX / authority / action endpoint、implementation surface 和验收段落。目标是把 Portal 当前 display contract 读回 live contract/source/test/CLI 事实，并删除 active 文档中的 dated landed chronology 形态，尤其避免把历史 execution/conversation UI 误读成当前 MAS-owned terminal、conversation 或 runtime event drilldown。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/product/README.md`, `docs/docs_portfolio_consolidation.md`, `docs/active/opl_app_mas_runtime_workbench_program.md`.
- Machine surfaces: `contracts/test-lane-manifest.json#focused_lanes.portal-route-decision-trail`, `contracts/test-lane-manifest.json#focused_lanes.mas-workbench-projection`, `contracts/functional_privatization_audit.json`, `src/med_autoscience/controllers/opl_unique_control_plane_boundary_parts/generated_surface_handoff.py`.
- Source surfaces: `src/med_autoscience/controllers/progress_portal_parts/workspace_carrier.py`, `src/med_autoscience/controllers/progress_portal_parts/study_workbench.py`, `src/med_autoscience/controllers/progress_portal_parts/runtime_workbench_projection.py`.
- CLI/read-model: `PYTHONPATH=src python -m med_autoscience.cli workspace progress-portal --help`.
- Focused test evidence read from current source: `tests/test_progress_portal.py` asserts `conversation` and runtime conversation read-model are not accepted, `terminal/log stream` is absent, and terminal/log projection requires external OPL control-plane.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | `docs/runtime/display/progress_portal.md` lifecycle header, entry conclusion, dated landed note cluster, OPL App integration conclusion, runtime drilldown boundary, user experience contract, data/authority boundary, static/serve/action endpoint contract, Portal/runtime drilldown evidence, old MDS relation, implementation surface, acceptance criteria. Support evidence came from the live truth inputs listed above. | `docs/runtime/display/progress_portal.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The dated Portal narrative was folded inside the same active display contract because its remaining useful content is current support material plus provenance pointers; no standalone history document was needed in this tranche.

Uncovered docs in this semantic area:

- `docs/runtime/projections/**` owner-route / domain-ref projection docs.
- `docs/product/inspection_package.md`.
- Other integration references under `docs/references/integration/*.md` not already covered by the product/workbench and Portal tranches.

Remaining stale / retire candidates:

- Progress Portal workspace carrier remains active diagnostic / no-App / evidence path because `medautosci workspace progress-portal`, `--serve`, and `ops/mas/bin/start-web` remain active callers.
- `progress_portal_parts/rendering.py` no longer carries `conversation-*` CSS residue; focused Progress Portal tests now guard that runtime conversation read models and conversation timeline UI remain outside the active MAS Portal contract.
- Any future Portal prose that mentions execution conversation, terminal/log stream, provider runtime event drilldown, or old MDS WebUI must explicitly route those concerns to OPL `current_control_state` / provider attempt projection or history/provenance.

Next tranche write scope:

- MAS `docs/runtime/projections/**` owner-route / domain-ref projection coverage, or MAS `docs/product/inspection_package.md`.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

### 2026-05-26 runtime projections owner-boundary tranche

本轮覆盖 MAS `docs/runtime/projections/**` 8 份 projection support 文档。目标是把 projection 文档统一读回当前 MAS / OPL owner split：MAS 持有 study truth、domain blocker、owner receipt、typed blocker、artifact/source/quality refs 和 human-readable read model；OPL 持有 provider-backed stage runtime、Temporal substrate、current-control-state、attempt/queue/retry/dead-letter/worker liveness/terminal-log truth。projection 文档只能解释 read-model 和 refs，不能变成 runtime substrate、provider completion、paper closure、artifact authority 或 long-running attempt truth。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/architecture.md`, `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/docs_portfolio_consolidation.md`.
- Runtime projection docs: `docs/runtime/projections/ai_first_observability.md`, `artifact_inventory_projection.md`, `progress_projection_history_contract.md`, `runtime_capability_matrix.md`, `runtime_health_kernel.md`, `study_macro_state_and_owner_route.md`, `study_progress_projection.md`, `study_truth_kernel.md`.
- Machine surfaces: `contracts/functional_privatization_audit.json`, `contracts/generated_surface_handoff.json`, `contracts/test-lane-manifest.json`, `contracts/action_catalog.json`, `contracts/stage_control_plane.json`.
- Source / test surfaces: CodeGraph context for `study_progress` / `user_visible_projection` / runtime health / owner route read models; `src/med_autoscience/controllers/study_progress_parts/user_visible_projection.py`, `src/med_autoscience/mcp_server_parts/study_progress_projection.py`, `src/med_autoscience/controllers/progress_portal_parts/*`, `tests/test_study_progress.py`, `tests/test_runtime_health_kernel.py`, `tests/test_truth_projection_surfaces.py`, `tests/test_domain_health_diagnostic.py`, and owner-route focused lanes listed in `contracts/test-lane-manifest.json`.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | All 8 files under `docs/runtime/projections/`: lifecycle headers, surface contracts, provider/executor/back-end wording, detail/history loading rules, StudyTruth/RuntimeHealth dominance boundaries, owner-route handoff rules, Progress Portal / OPL App relation, MDS / DeepScientist / Hermes references, and terminal/log/current-control-state wording. | `docs/runtime/projections/runtime_capability_matrix.md`; `docs/runtime/projections/progress_projection_history_contract.md`; `docs/runtime/projections/study_progress_projection.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The projection docs remain active runtime support because they explain current read-model semantics and domain/OPL boundary; stale provider/backend phrasing was rewritten in place rather than moved to history.

Uncovered docs in this semantic area:

- `docs/product/inspection_package.md`.
- Remaining integration references under `docs/references/integration/*.md` that mention Progress Portal, OPL App/workbench, domain refs, or owner-route read-model consumption.
- Runtime support docs outside `docs/runtime/projections/**`, especially `docs/runtime/contracts/**`, `docs/runtime/control/**`, and `docs/runtime/stage_route_handoff_standard.md`.

Remaining stale / retire candidates:

- `runtime_capability_matrix.md` should continue using `provider_owner` / `executor_kind` wording; future edits must not reintroduce MAS-owned provider backend, Hermes production substrate, or DeepScientist backend as current runtime owner.
- `progress_projection_history_contract.md` now treats terminal/log/runtime event detail as bounded OPL refs; future prose must not imply MAS reads unbounded terminal logs or launches/relaunches provider workers from a projection read.
- `study_progress_projection.md` still lists historical `last_launch_report` and `active_run_id` fields as input/provenance; current wording requires OPL current-control-state refs for live worker truth. Treat any new claim based only on `active_run_id` / launch report as stale-pollution candidate.
- The projection docs explain current domain-read-model semantics; they do not close MAS `domain_ref_consumer_thinning`, `workbench_sidecar_status_cutover`, real paper-line provider apply, provider SLO long soak, or App/workbench production evidence tails.

Next tranche write scope:

- MAS `docs/product/inspection_package.md`, or integration references under `docs/references/integration/*.md` that still carry product/workbench/Portal/owner-route current-truth claims.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

### 2026-05-26 inspection package product/delivery tranche

本轮覆盖 MAS `inspection_package` 产品、交付与 delivery-plane contract 文档。目标是把 human-inspection-only inspection surface 读回 live source、tests、CLI/read-model、product-entry 和 runtime contract 事实，明确它可以物化 blocked/stale snapshot，也可以在 existing controller-authorized `current_package.zip` 已 current 时只返回 `authorized_current_package_available` review pointer；两条路径都不能授权投稿、质量放行、`current_package` 写入、`submission_minimal` 写入、delivery sync、gate closeout 或 eval / decision artifact 更新。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/README.md`, `docs/status.md`, `docs/architecture.md`, `docs/invariants.md`, `docs/decisions.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file.
- Product / delivery / runtime docs: `docs/product/README.md`, `docs/product/inspection_package.md`, `docs/delivery/README.md`, `docs/delivery/inspection_package.md`, `docs/runtime/contracts/delivery_plane_contract_map.md`, `docs/runtime/control/controllers.md`.
- Machine surfaces: `contracts/action_catalog.json`, `contracts/generated_surface_handoff.json`, `contracts/artifact_locator_contract.json`.
- Source surfaces: `src/med_autoscience/controllers/submission_inspection_export.py`, `src/med_autoscience/controllers/delivery_visibility_projection.py`, `src/med_autoscience/action_catalog.py`, `src/med_autoscience/controllers/product_entry_parts/manifest_shell_surfaces.py`, `src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/readiness_and_delivery.py`.
- CLI/read-model: `PYTHONPATH=src python -m med_autoscience.cli publication --help`, `PYTHONPATH=src python -m med_autoscience.cli publication delivery-inspect --help`, `PYTHONPATH=src python -m med_autoscience.cli publication export-inspection-package --help`.
- Focused tests: `tests/test_inspection_package_contract.py`, `tests/test_submission_inspection_export.py`, `tests/test_product_entry.py::test_product_entry_exposes_publication_inspection_package_operator_surface`, `tests/test_product_entry.py::test_product_entry_surfaces_delivery_inspection_in_cockpit_and_entry_status`, `tests/test_product_entry.py::test_product_entry_counts_layout_migration_even_when_stale_status_is_primary`, `tests/test_product_entry.py::test_product_entry_does_not_normalize_retired_delivery_projection_input`, and `tests/product_entry_cases/delivery_inspection_visibility.py`.
- Structural context: CodeGraph context / explore for `inspection_package`, `human_inspection_only`, `not_for_submission`, `gate_blocked_snapshot`, and related tests.

Fresh semantic result：

- `export_inspection_package` can materialize `inspection_package_materialized` into `manuscript/inspection_package/`, `manuscript/inspection_package.zip`, `manuscript/inspection_package_manifest.json`, and `artifacts/inspection_package/*`; the receipt sets `human_inspection_only=true`, `can_submit=false`, and forbidden writes for `current_package`, `submission_minimal`, `publication_eval`, and `controller_decisions`.
- When `delivery_inspector` sees current authorized `current_package.zip` and `--force-materialize` is not set, `export_inspection_package` returns `authorized_current_package_available`, writes only inspection metadata / receipt, and points `recommended_human_review_path` to the existing current package; it still keeps `inspection_only=true` and does not generate a new submission authority or freshness proof.
- Product-entry exposes `export_inspection_package` as a descriptor-only / human-inspection-only operator surface; MCP descriptor projection remains non-runtime and the public tool manifest does not expose a mutable `export_inspection_package` tool.
- `delivery_inspection` / `workspace_delivery_inspection` remain `observability_projection_only`; they can show status, source labels and inspection package availability but cannot authorize submission, publication quality or delivery sync.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | `docs/product/inspection_package.md` full file; `docs/delivery/inspection_package.md` full file; `docs/runtime/contracts/delivery_plane_contract_map.md` inspection-package sections and delivery-plane artifact row; `docs/runtime/control/controllers.md` inspection package contract section; `docs/product/README.md` and `docs/delivery/README.md` inspection-package index rows; support evidence came from the live truth inputs listed above. | `docs/product/inspection_package.md`; `docs/delivery/inspection_package.md`; `docs/runtime/contracts/delivery_plane_contract_map.md`; `docs/runtime/control/controllers.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The product, delivery and runtime contract docs remain active support because they hold distinct product, export and delivery-plane boundary roles.

Uncovered docs in this semantic area:

- Remaining integration references under `docs/references/integration/*.md` that mention Progress Portal, OPL App/workbench, domain refs, owner-route read-model consumption or inspection/delivery visibility.
- Runtime support docs outside the touched delivery-plane contract and controller section, especially other `docs/runtime/contracts/**`, `docs/runtime/control/**`, and `docs/runtime/stage_route_handoff_standard.md` body sections not inspected in this tranche.

Remaining stale / retire candidates:

- `inspection_package` is not a retire candidate in this tranche; live source and tests prove it is an active human-inspection-only delivery surface.
- Future prose must keep blocked snapshot materialization separate from `authorized_current_package_available` pointer mode, and must not describe either mode as `current_package` freshness proof, formal submission package, publication verdict, quality gate closeout, delivery-sync dispatch, or artifact mutation authority.
- Inspection package must never be used as canonical paper repair input, AI reviewer verdict input, `submission_minimal` / `current_package` freshness proof, delivery sync authorization or publication gate closeout.
- Product-entry / cockpit inspection surfaces remain observability / human-inspection-only. They do not close MAS `workbench_sidecar_status_cutover`, generated/default caller cutover, real paper-line provider apply, owner-chain dispatch evidence, or App/workbench production evidence tails.

Next tranche write scope:

- MAS integration references under `docs/references/integration/*.md`, or runtime support docs under `docs/runtime/contracts/**` / `docs/runtime/control/**` that still carry product/workbench/Portal/owner-route current-truth claims.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

### 2026-05-26 integration references handoff tranche

本轮覆盖 MAS `docs/references/integration/*.md` 的 product-entry / OPL handoff / runtime-owner / App-workbench integration 语义。目标是把 integration reference 读回当前 `MedAutoScienceDomainEntry`、product-entry CLI、generated-surface handoff、OPL/Temporal 默认 hosted runtime 和 MAS authority boundary，删除仍把 external runtime gate、MedDeepScientist backend、Hermes host 或未成熟 product-entry shell 写成当前阻塞的旧口径。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/architecture.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/references/positioning/mas_ideal_state.md`, this docs-governance file.
- Integration docs: `docs/references/integration/codex_plugin.md`, `lightweight_product_entry_and_opl_handoff.md`, `opl-family-contract-adoption.md`, `opl-managed-runtime-three-layer-contract.md`, `progress_portal_opl_app_integration.md`, `stage_led_autonomy_family_inventory.md`.
- Machine surfaces: `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, `contracts/action_catalog.json`.
- Source surfaces: `src/med_autoscience/domain_entry_contract.py`, `src/med_autoscience/domain_entry.py`, `src/med_autoscience/cli_parts/product_entry_parsers.py`, `src/med_autoscience/cli_parts/product_entry_commands.py`, `src/med_autoscience/controllers/product_entry_parts/entry_runtime.py`, `src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py`.
- CLI/read-model: `PYTHONPATH=src python -m med_autoscience.cli --help`, `PYTHONPATH=src python -m med_autoscience.cli build-product-entry --help`, `PYTHONPATH=src python -m med_autoscience.cli product-entry-manifest --help`, `PYTHONPATH=src python -m med_autoscience.cli workspace progress-portal --help`.
- Structural context: CodeGraph context / explore for `MedAutoScienceDomainEntry`, `SERVICE_SAFE_DOMAIN_COMMANDS`, `build-product-entry`, product-entry CLI commands and Progress Portal handoff.

Fresh semantic result：

- `MedAutoScienceDomainEntry` is the service-safe structured entry shared by direct MAS skill, CLI and OPL generated / hosted surfaces. Current service-safe commands include product-entry status/preflight/start/manifest, skill catalog, workspace cockpit, study progress/projection, submit/launch study and `build-product-entry`.
- Public CLI grouping exposes `medautosci product build-entry`; the internal service-safe command id and parser command remain `build-product-entry`. Product-entry manifest remains descriptor/read-model surface, not domain truth or quality authority.
- The shared handoff envelope now centers `domain_authority_handoff_contract`, `managed_runtime_contract`, `return_surface_contract`, `domain_entry_contract` and `user_interaction_contract`; old `runtime_session_contract` wording is stale for this reference.
- OPL/Temporal is the default hosted autonomous runtime owner. External MedDeepScientist backend, Hermes host and local LaunchAgent must only appear as provenance, backend audit, explicit non-default executor/proof lane, parity oracle, diagnostic or history.
- Product/status/workbench/sidecar shell remains a strict source-purity tail and active migration surface, not a long-term MAS-owned generic product runtime.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | All six files under `docs/references/integration/`: lifecycle headers, product-entry/Hermes/MDS wording, OPL family contract adoption, three-layer runtime owner split, Progress Portal / OPL App handoff, Stage-Led Autonomy family descriptor inventory, and stale wording scan for runtime gate / handoff envelope / product-entry maturity claims. | `docs/references/integration/lightweight_product_entry_and_opl_handoff.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The integration references remain support references; only stale current-truth claims in the lightweight product-entry / OPL handoff reference were rewritten in place.

Uncovered docs in this semantic area:

- Runtime support docs under `docs/runtime/contracts/**` and `docs/runtime/control/**` outside previously covered projection/display/inspection/controller snippets.
- `docs/runtime/stage_route_handoff_standard.md` beyond the risk scan and references read in this tranche.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any integration prose that says MAS still has a current external runtime gate, current MedDeepScientist backend dependency, or pending Hermes host switch is stale unless it is explicitly history/provenance.
- Product-entry / sidecar / status / workbench shell may stay active as direct handler, domain target, diagnostic bridge or migration surface, but future prose must keep OPL generated/default caller cutover as the target state.
- OPL App, native helper, product-entry manifest and Progress Portal projections must not be written as MAS study truth, publication quality, artifact authority, `current_package` freshness proof, memory body owner or domain-ready verdict.

Next tranche write scope:

- MAS runtime support docs under `docs/runtime/contracts/**`, `docs/runtime/control/**` or `docs/runtime/stage_route_handoff_standard.md` that still need paragraph-level current-truth reconciliation.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

### 2026-05-26 runtime id / binding currentness tranche

本轮覆盖 MAS runtime support docs 中最容易误导后续自动化的 runtime id、runtime binding 与 provider-owner 口径。目标是把 active current truth、runtime backend contract、runtime handle contract 和 capability projection 中的旧 `opl_provider_backed_stage_runtime` 机器 id 写法，对齐当前 live `opl_runtime_contract.py`、`write_runtime_binding`、product-entry manifest 和 focused tests：当前 machine ref 是 `opl_hosted_stage_runtime` / `opl-hosted-stage-runtime`，OPL/Temporal provider-backed 是 owner/topology 语义，MAS domain adapter 是 `mas_domain_intent_adapter` / `mas_domain_owner_receipt_adapter`。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/architecture.md`, `docs/invariants.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/references/positioning/mas_ideal_state.md`, this docs-governance file.
- Runtime docs: `docs/runtime/contracts/*.md`, `docs/runtime/control/*.md`, `docs/runtime/stage_route_handoff_standard.md`, and already covered `docs/runtime/projections/runtime_capability_matrix.md` risk line.
- Machine/source surfaces: `src/med_autoscience/opl_runtime_contract.py`, `src/med_autoscience/runtime_protocol/study_runtime.py`, `src/med_autoscience/controllers/opl_provider_ready_adapter.py`, `src/med_autoscience/controllers/product_entry_parts/entry_runtime.py`, `src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py`, `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, `contracts/production_acceptance/mas-production-acceptance.json`, `contracts/test-lane-manifest.json`.
- CLI/read-model: `PYTHONPATH=src python -m med_autoscience.cli --help`, `PYTHONPATH=src python -m med_autoscience.cli sidecar --help`, `PYTHONPATH=src python -m med_autoscience.cli runtime --help`, `PYTHONPATH=src python -m med_autoscience.cli runtime maintain-storage --help`, `PYTHONPATH=src python -m med_autoscience.cli runtime storage-audit --help`, and a failed stale probe for nonexistent `runtime-storage` that confirmed storage commands live under `runtime maintain-storage` / `runtime storage-audit`.
- Focused tests / assertions read as evidence: `tests/test_opl_runtime_contract.py`, `tests/test_runtime_protocol_study_runtime.py`, `tests/test_profiles.py`, `tests/test_cli_cases/owner_route_handoff_command_cases/export_cases.py`, `tests/product_entry_cases/repo_shell_runtime_assertions.py`, `tests/test_mainline_status.py`.
- Structural context: CodeGraph context for MAS runtime refs, runtime event records, sidecar/owner-route handoff and CLI/runtime command surfaces.

Fresh semantic result：

- Current runtime machine identity is `runtime_substrate=opl_hosted_stage_runtime`, `runtime_ref=opl_hosted_stage_runtime`, and `runtime_engine_id=opl-hosted-stage-runtime`.
- `runtime_binding.yaml` writes `runtime_substrate`, `opl_runtime_ref`, `runtime_ref`, `runtime_engine_id`, `research_backend_id`, `research_backend`, `research_engine_id`, `runtime_home`, and `runtime_quests_root`; it no longer writes `runtime_backend_id` or `runtime_backend` in current protocol tests.
- OPL/Temporal provider-backed stage runtime remains the default generic runtime owner/topology. That owner wording must not be converted back into a MAS-local backend id or callable module.
- MAS current role is domain authority refs, owner receipt, typed blocker, artifact/source/quality refs and diagnostic explanation. Legacy `runtime_backend_id`, `runtime_backend`, `mas_runtime_core`, local scheduler, Hermes gateway cron and MDS backend fields are migration/provenance/diagnostic-only unless an explicit non-default proof lane says otherwise.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Risk scan across all files under `docs/runtime/contracts/**`, `docs/runtime/control/**`, `docs/runtime/stage_route_handoff_standard.md`, plus focused review of runtime id / backend / binding sections in `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/runtime/contracts/runtime_backend_interface_contract.md`, `docs/runtime/contracts/runtime_handle_and_durable_surface_contract.md`, `docs/runtime/contracts/agent_runtime_interface.md`, and `docs/runtime/projections/runtime_capability_matrix.md`. Support evidence came from the live truth inputs listed above. | `docs/status.md`; `docs/active/mas-ideal-state-gap-plan.md`; `docs/runtime/contracts/runtime_backend_interface_contract.md`; `docs/runtime/contracts/runtime_handle_and_durable_surface_contract.md`; `docs/runtime/contracts/agent_runtime_interface.md`; `docs/runtime/projections/runtime_capability_matrix.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. This tranche corrected current-truth wording in place; the affected documents remain active support / active current truth owners.

Uncovered docs in this semantic area:

- Paragraph-level coverage remains open for most of `docs/runtime/contracts/**`, especially long support bodies not touched beyond lifecycle header / heading / stale-id risk scan.
- Paragraph-level coverage remains open for `docs/runtime/control/study_runtime_control_surface.md` and `docs/runtime/control/study_runtime_orchestration.md` beyond the runtime binding / owner split sections inspected here.
- `docs/runtime/stage_route_handoff_standard.md` was risk-scanned and read for owner split, but not fully rewritten or marked fully paragraph-covered.

Remaining stale / retire candidates:

- Any future prose that writes `opl_provider_backed_stage_runtime` as a current machine id, required `runtime_backend_id`, required `runtime_backend`, or MAS-local callable backend is stale. Use `opl_hosted_stage_runtime` / `opl-hosted-stage-runtime` for machine identity and OPL/Temporal provider-backed wording for owner/topology.
- `runtime_backend_id` and `runtime_backend` may appear only as legacy migration / provenance fields or historical input names; they must not become current required `runtime_binding.yaml` fields again.
- MAS runtime support docs still contain older broad support text that should be compacted in future paragraph-level passes, but this tranche found no additional active-current runtime owner contradiction requiring immediate archive/tombstone/delete.

### 2026-05-26 standard-agent direct/control boundary tranche

本轮覆盖 MAS core entry docs 与 runtime control support docs 中的 standard OPL Agent purity 口径。目标是把 README、project、architecture 与 controller/control 文档统一收敛到当前 long-horizon 目标：MAS 保留医学研究 truth、domain handler target、authority refs、owner receipt / typed blocker producer、AI reviewer / publication gate 和必要医学 helper；OPL generated/default callers、queue、attempt、retry/dead-letter、provider worker、current-control-state、generic transition transport、App/workbench shell 和长期 runtime owner 归 OPL。现有 CLI/MCP/product-entry/sidecar/controller/read-model 是 direct path、diagnostic ref、migration input 或 domain target，不再被写成 MAS 长期自有 generic wrapper / capability owner。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `README.zh-CN.md`, `docs/project.md`, `docs/architecture.md`, `docs/status.md`, this docs-governance file.
- Runtime control docs: `docs/runtime/control/controllers.md`, `docs/runtime/control/study_runtime_control_surface.md`, `docs/runtime/control/study_runtime_orchestration.md`.
- Machine / source surfaces: `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, `contracts/stage_control_plane.json`, `src/med_autoscience/controllers/owner_route_handoff_parts/owner_route_handoff_tasks.py`, and current OPL runtime binding / provider-owner surfaces listed in the runtime id / binding tranche.

Fresh semantic result：

- Public/core docs now name root `agent/` as the canonical OPL Agent semantic pack source and root `contracts/*.json` as required-file / generated-surface contract input.
- CLI/MCP/product-entry/sidecar/controller surfaces are current discoverable operator/direct surfaces, but long-term they must be generated/default caller targets, MAS domain handler targets, authority functions, owner receipt / typed blocker producers or diagnostic refs. They are not MAS-owned generic runtime/product wrappers.
- `request_opl_stage_attempt(...)`, pause/stop/relaunch and orchestration persistence text now separates MAS-facing domain refs / owner authorization / typed blocker / diagnostic artifacts from OPL-owned provider pause/stop/relaunch/current-control-state writes.
- Retired transport helpers such as historical resume/relaunch transport are provenance / diagnostic mapping only; they do not revive MAS scheduler, queue, provider worker, retry/dead-letter or lifecycle ownership.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Core entry positioning in `README.zh-CN.md`, `docs/project.md`, `docs/architecture.md`; runtime control boundary sections in `docs/runtime/control/controllers.md`, `docs/runtime/control/study_runtime_control_surface.md`, and `docs/runtime/control/study_runtime_orchestration.md`. | `README.zh-CN.md`; `docs/project.md`; `docs/architecture.md`; `docs/runtime/control/controllers.md`; `docs/runtime/control/study_runtime_control_surface.md`; `docs/runtime/control/study_runtime_orchestration.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. These files remain active entry/current-truth/support docs; this tranche only corrected owner-boundary wording in place.

Uncovered docs in this semantic area:

- Paragraph-level coverage remains open for `docs/runtime/contracts/**` outside the runtime id / binding risk scan.
- Additional runtime/control paragraphs outside the touched pause/stop/relaunch/persistence sections still need future compaction if they carry generic runtime-owner wording.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future prose must not call current MAS CLI/MCP/product-entry/sidecar/controller shell a long-term generic capability owner. Keep it as direct path, migration input, diagnostic ref, generated/default caller target, domain handler target or minimal authority implementation.
- MAS must not claim OPL queue, attempt ledger, provider worker, retry/dead-letter, current-control-state, App/workbench shell or generic runtime lifecycle ownership through controller wording.
- Source physical deletion remains gated by active-caller proof, parity/receipt evidence, no-forbidden-write proof, focused tests and tombstone/provenance refs.

### 2026-05-26 stage-route handoff standard currentness tranche

本轮覆盖 MAS `docs/runtime/stage_route_handoff_standard.md` 的 paragraph-level currentness。目标是把 stage / route / handoff / owner-route attempt protocol 读回当前 live contracts、source 和 focused tests，明确 MAS 只声明 domain route 语义、authority refs、currentness basis、allowed/forbidden surfaces、typed closeout requirement 和 completion boundary；OPL 持有 queue、attempt、retry、dead-letter、provider liveness、generic transition transport、stage graph consumption 和 App/operator projection。文档不能把 route 写成 MAS-owned stage，不能把 `stage_graph_handoff` 写成 MAS child scheduler，不能把 provider completion、stage graph hints、zero forbidden writes 或 contract readability 写成 paper-line domain closeout。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, this docs-governance file.
- Runtime / semantic docs and contracts: `docs/runtime/stage_route_handoff_standard.md`, `agent/stages/stage_route_contract.yaml`, `contracts/stage_control_plane.json`, `contracts/action_catalog.json`, `contracts/generated_surface_handoff.json`, `contracts/test-lane-manifest.json`, `contracts/functional_privatization_audit.json`.
- Source surfaces: `src/med_autoscience/controllers/owner_route_handoff_parts/owner_route_handoff_tasks.py`, `src/med_autoscience/runtime_control/owner_route_attempt_protocol.py`.
- Focused tests / assertions read as evidence: `tests/test_sidecar_owner_route_handoff.py`, `tests/owner_route_reconcile_cases/test_owner_route_attempt_protocol.py`.

Fresh semantic result：

- `route != stage` remains the key invariant: MAS declares route semantics and domain obligations; OPL owns provider-backed stage lifecycle and generic transition transport.
- `owner_route_handoff_tasks.py` emits `route_transition_contract` and `stage_graph_handoff` as body-free refs/hints. Current source declares `stage_lifecycle_owner=one-person-lab`, `runtime_transition_owner=one-person-lab`, `queue_owner=one-person-lab`, `domain_truth_owner=med-autoscience`, and forbidden writes for `.ds/runtime_state.json`, `.ds/user_message_queue.json`, publication eval, controller decisions and `current_package`.
- `stage_graph_handoff` gives OPL-owned hints for `journal-resolution` / `finalize` under `finalize_and_publication_handoff`; it does not authorize MAS child scheduling, publication/submission readiness, artifact readiness, domain completion or physical delete decisions.
- `mas-owner-route-attempt-protocol.v1` requires registered reasons, currentness basis, allowed/forbidden surfaces, required closeout packet and fail-closed missing-field behavior. OPL owns queue/attempt/retry/dead-letter/provider liveness; MAS owns domain truth, AI reviewer, publication gate, artifact authority, owner receipt and typed blocker.
- Real paper-line canary, owner-chain closeout, long-soak, artifact movement and human gate receipt remain open evidence tails after this docs tranche.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | `docs/runtime/stage_route_handoff_standard.md` full file; supporting read of current stage route source, stage control plane, generated handoff, owner-route handoff source and focused owner-route tests. | `docs/runtime/stage_route_handoff_standard.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The stage-route handoff standard remains active runtime support because it explains current MAS-to-OPL route/stage/handoff boundaries.

Uncovered docs in this semantic area:

- Paragraph-level coverage remains open for `docs/runtime/contracts/**`, especially `runtime_event_and_outer_loop_input_contract.md`, `durable_workflow_contract.md`, `stage_route_contract.md`, `stage_surfaces.md`, and `workspace_knowledge_and_literature_contract.md`.
- Paragraph-level coverage remains open for `docs/runtime/control/study_runtime_control_surface.md` and `docs/runtime/control/study_runtime_orchestration.md`.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that treats `route_transition_contract`, `stage_graph_handoff`, descriptor parity, zero forbidden writes, provider completion or OPL runner pass as MAS owner receipt, publication-ready, submission-ready, artifact-ready, App release ready, physical delete authorization or domain completion is stale.
- Runtime/control source thinning remains a strict source-purity tail. Physical deletion still requires active-caller proof, no-forbidden-write proof, MAS owner receipt or typed blocker parity, focused tests and tombstone/provenance refs.
- Real OPL attempt -> MAS owner chain remains an evidence-after-contract tail until a real paper-line run produces progress delta, AI reviewer/gate receipt, artifact movement, human gate, stop-loss and owner receipt or stable typed blocker.

Next tranche write scope:

- Immediate same-run follow-up: the runtime control owner-route / current-control-state tranche below covers `study_runtime_control_surface.md` and `study_runtime_orchestration.md`.
- Remaining MAS runtime contract coverage after the same-run follow-up: bounded `docs/runtime/contracts/**` bodies such as `stage_route_contract.md`, `stage_surfaces.md`, or `workspace_knowledge_and_literature_contract.md`.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

### 2026-05-26 runtime control owner-route/current-control-state tranche

本轮覆盖 MAS runtime control 文档中最容易误读成 MAS 私有 provider control 的 stop / pause / relaunch / current-control-state 段落。目标是把 `study_runtime_control_surface.md` 与 `study_runtime_orchestration.md` 对齐当前 owner-route / OPL current-control-state 边界：MAS 只输出 domain refs、owner authorization、owner receipt、typed blocker、diagnostic refs 或 owner-route handoff；OPL 持有 provider pause/stop/relaunch、queue、attempt、retry/dead-letter、worker liveness 和 current-control-state truth。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/references/positioning/mas_ideal_state.md`, this docs-governance file.
- Runtime support docs: `docs/runtime/control/study_runtime_control_surface.md`, `docs/runtime/control/study_runtime_orchestration.md`, `docs/runtime/contracts/runtime_event_and_outer_loop_input_contract.md`, `docs/runtime/contracts/durable_workflow_contract.md`, `docs/runtime/stage_route_handoff_standard.md`.
- Machine/source surfaces: CodeGraph context / explore for `owner_route_handoff`, `owner_route_handoff_task`, `opl_current_control_state_handoff_path`, `opl_current_control_state_study_handoff_projection`, `_request_opl_stage_attempt`, `OplRuntimeRefs`.
- Contract/test surfaces: `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`, `tests/owner_route_reconcile_cases/owner_route_test_helpers.py`, `tests/owner_route_reconcile_cases/test_owner_route_contract.py`, `tests/test_study_outer_loop_cases/runtime_resume_cases.py`, `tests/test_study_outer_loop_cases/user_gate_cases.py`, `tests/study_progress_cases/opl_current_control_state_handoff_projection.py`, `tests/product_entry_cases/opl_current_control_state_handoff_projection.py`, `tests/progress_portal_cases/test_authorized_actions.py`.
- CLI/read-model: `scripts/run-python-clean.sh -m med_autoscience.cli runtime --help`.

Fresh semantic result：

- `owner_route_handoff` writes `surface_kind=mas_runtime_owner_route_handoff`, `domain_truth_owner=med-autoscience`, `queue_owner=one-person-lab`, and `authority_boundary` with `mas_writes_generic_runtime_queue=false`, `mas_submits_runtime_chat=false`, `mas_resumes_provider_worker=false`, `opl_writes_mas_truth=false`, `mas_owner_receipt_required=true`; `mark_owner_route_handoff` returns `runtime_state_mutated=false`.
- `owner_route_handoff_task` produces a refs-only `domain_route/owner-handoff` task, declares `stage_lifecycle_owner=one-person-lab`, `runtime_transition_owner=one-person-lab`, `queue_owner=one-person-lab`, and forbids `.ds/runtime_state.json`, `.ds/user_message_queue.json`, runtime queue/retry/dead-letter/worker-liveness truth, publication eval, controller decisions and `current_package` mutation.
- OPL current-control-state handoff is read as `artifacts/supervision/opl_current_control_state/latest.json`, with study projection `authority=observability_only`; MAS consumes the projection for operator/status/read-model context and does not turn it into MAS runtime truth.
- `request_opl_stage_attempt(...)` remains MAS domain refs / controller authorization contract. For paused/stopped/failed/no-live/waiting-owner states it may output intent, typed blocker or owner-route handoff; provider terminal-state release, attempt hydration, pause/stop/relaunch and queue/retry/dead-letter remain OPL runtime owner responsibilities.
- `runtime_event_and_outer_loop_input_contract.md`, `durable_workflow_contract.md` and `stage_route_handoff_standard.md` were read as support proof and already align with this boundary; no edit was required there in this tranche.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | `docs/runtime/control/study_runtime_control_surface.md` sections 1-4, 6, 8-10; `docs/runtime/control/study_runtime_orchestration.md` current owner summary, scope, Domain Refs, retired decision projection, preflight/handoff, retired execution provenance, artifact/receipt persistence and non-stable internals; support read of `runtime_event_and_outer_loop_input_contract.md`, `durable_workflow_contract.md`, and `stage_route_handoff_standard.md` owner-boundary sections. | `docs/runtime/control/study_runtime_control_surface.md`; `docs/runtime/control/study_runtime_orchestration.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The runtime control docs remain active support; stale provider-control wording was corrected in place because the files still own the human-readable runtime control contract.

Uncovered docs in this semantic area:

- Paragraph-level coverage remains open for the remaining long support bodies under `docs/runtime/contracts/**`, especially `stage_route_contract.md`, `stage_surfaces.md`, `workspace_knowledge_and_literature_contract.md` and other contracts not covered by prior runtime-id/current-control tranches.
- `docs/runtime/stage_route_handoff_standard.md` is covered by the immediately preceding stage-route handoff standard currentness tranche; future work there should be limited to new live-truth drift, not first-pass paragraph coverage.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that says MAS directly pauses/stops/resumes/relaunches provider workers, writes generic runtime queue/chat/state, owns retry/dead-letter/worker liveness truth, or treats stopped relaunch as ordinary resume is stale.
- Historical transport helper names such as `_resume_quest(...)`, `_relaunch_stopped_quest(...)`, `_pause_quest(...)` and daemon result are allowed only as retired provenance, diagnostic mapping or test-only patch-target context; they must not be reintroduced as MAS-owned runtime control contracts.
- `stop_runtime`, `pause_runtime` and `request_opl_stage_attempt_relaunch` are MAS controller/domain action names. They are not MAS provider-control write APIs and do not close real paper-line provider apply, owner-chain dispatch evidence, human gate/resume, provider SLO long-soak or generated/default caller cutover tails.

Next tranche write scope:

- MAS paragraph-level coverage for a bounded subset of `docs/runtime/contracts/**`, preferably `stage_route_contract.md`, `stage_surfaces.md` or `workspace_knowledge_and_literature_contract.md`.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

### 2026-05-26 runtime contract stage / knowledge plane coverage tranche

本轮覆盖 MAS runtime contract 中的 stage route、generated stage surface、workspace knowledge / literature 三个长支撑文档。目标是确认这些文档仍然只是人读 support surface，并且当前段落没有把 generated Markdown、stage route projection、workspace literature、quest-local materialization、stage memory closeout 或 provider projection 写成 MAS 之外的机器 truth、quality authority、publication/submission readiness 或 OPL-owned generic runtime control。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, this docs-governance file, and preceding runtime id / control-boundary ledger entries.
- Runtime contract docs: `docs/runtime/contracts/stage_route_contract.md`, `docs/runtime/contracts/stage_surfaces.md`, `docs/runtime/contracts/workspace_knowledge_and_literature_contract.md`.
- Machine / source surfaces: `agent/stages/stage_route_contract.yaml`, `contracts/stage_control_plane.json`, `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`, `src/med_autoscience/stage_knowledge_contract.py`, `src/med_autoscience/controllers/stage_knowledge_plane.py`, `src/med_autoscience/controllers/workspace_literature.py`, `src/med_autoscience/runtime_protocol/workspace_literature_status.py`.
- Structural context: CodeGraph context for stage knowledge packets, workspace literature and runtime workspace contract summaries.
- Focused test inventory read as evidence: `tests/test_stage_route_contract.py`, `tests/test_stage_surface_contract.py`, `tests/test_stage_quality_contract.py`, `tests/test_stage_knowledge_plane.py`, `tests/test_stage_knowledge_entry_injection.py`, `tests/test_stage_knowledge_visibility.py`, `tests/test_workspace_literature.py`, `tests/test_cli_cases/stage_memory_cli_commands.py`, `tests/test_cli_cases/study_state_matrix_memory_writeback_receipts.py`, `tests/test_runtime_protocol_study_runtime_cases/test_owner_route_stage_knowledge_hydration.py`, `tests/product_entry_cases/action_catalog_parity_cases/stage_descriptor_cases.py`, and `tests/progress_portal_cases/test_stage_review_surface.py`.

Fresh semantic result：

- `stage_route_contract.md` remains a human-readable projection of `agent/stages/stage_route_contract.yaml`. The YAML still owns route ids, mode contracts, knowledge input obligations, memory closeout obligations, evidence/review contract, medical handoff, route-back, quality loop and startup boundary rules.
- `stage_surfaces.md` already states it is generated human-reading Markdown, not machine truth. Its stage cards continue to point to canonical route contract refs, `stage_knowledge_packet`, `stage_recall_index`, `stage_memory_closeout_packet`, `memory_write_router_receipt`, publication eval / evidence / review / controller decision refs, and OPL read/dispatch-only boundaries.
- `workspace_knowledge_and_literature_contract.md` remains aligned with source: workspace canonical literature lives under `portfolio/research_memory/literature/*`, study reference context is study-owned, quest literature is materialized working copy only, stage closeout proposes writes, and `memory_write_router_receipt` / owner surfaces decide acceptance.
- No paragraph in the reviewed set currently reintroduces retired default-runtime / legacy entrypoint wording, `opl_provider_backed_stage_runtime` machine id, MAS-owned generic runtime owner, publication-ready, submission-ready, artifact-ready or production-ready leakage.
- No archive/tombstone/delete action is justified in this tranche: the three files still have distinct active runtime-support roles.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/contracts/stage_route_contract.md`, `docs/runtime/contracts/stage_surfaces.md`, and `docs/runtime/contracts/workspace_knowledge_and_literature_contract.md`, with live source/contract/test inventory checks listed above. | this coverage ledger only |

Archived / tombstoned / deleted docs: none. The reviewed files remain active support docs.

Uncovered docs in this semantic area:

- Remaining paragraph-level coverage is still open for other long support bodies under `docs/runtime/contracts/**`, especially `runtime_event_and_outer_loop_input_contract.md`, `durable_workflow_contract.md`, `runtime_boundary.md`, `runtime_core_convergence_and_controlled_cutover.md`, `runtime_backend_interface_contract.md`, `runtime_handle_and_durable_surface_contract.md`, and delivery/artifact/source adjacent contracts not covered by prior focused tranches.
- MAS product/status/workbench and progress/domain-ref projection coverage remains open outside prior Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary and this stage/knowledge contract block.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future prose must not treat generated stage surface Markdown, stage graph hints, route contract readability, workspace literature registry presence, stage memory closeout packet, memory router receipt, provider projection or zero forbidden writes as MAS owner receipt, publication-ready, submission-ready, artifact-ready, App release ready, physical delete authorization, domain completion or production readiness.
- Quest-local literature materialization remains a working copy. It must not be promoted to workspace canonical literature, study reference context, evidence authority, AI reviewer verdict or controller decision.
- Stage memory closeout remains proposed writeback plus router receipt. It must not bypass owner acceptance, evidence ledger, review ledger, controller decision or human gate.

Next tranche write scope:

- MAS paragraph-level coverage for another bounded `docs/runtime/contracts/**` group, preferably `runtime_event_and_outer_loop_input_contract.md` + `durable_workflow_contract.md`, or `runtime_boundary.md` + runtime backend / handle contracts if current owner wording drifts.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.
- Keep App docs delayed until active release/GUI lanes are safe to govern.

### 2026-05-26 runtime event / durable workflow contract coverage tranche

本轮覆盖 MAS runtime contract 中的 runtime event / outer-loop input 与 durable workflow 两个支撑文档。目标是确认文档仍然把 generic runtime event、attempt、retry/dead-letter、human-gate transport、provider liveness 和 repair projection 归给 OPL/current-control-state，把 MAS 边界限定在 domain authority refs、outer-loop judgment、owner receipt、typed blocker、runtime escalation 和 diagnostic blocker refs，不把 runtime transport proof 升格成 publication、artifact、quality、domain 或 production readiness。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, this docs-governance file, `docs/active/mas-ideal-state-gap-plan.md`, and preceding runtime id / control-boundary / stage-knowledge coverage ledger entries.
- Runtime contract docs: `docs/runtime/contracts/runtime_event_and_outer_loop_input_contract.md`, `docs/runtime/contracts/durable_workflow_contract.md`, with support reads of `docs/runtime/contracts/delivery_plane_contract_map.md`, `docs/runtime/control/study_runtime_control_surface.md`, and `docs/runtime/control/study_runtime_orchestration.md`.
- Machine / source surfaces: `src/med_autoscience/controllers/study_outer_loop.py`, `contracts/functional_privatization_audit.json`, `contracts/stage_control_plane.json`, and `contracts/test-lane-manifest.json`.
- Focused test inventory read as evidence: `tests/test_durable_workflow_contract.py`, `tests/test_study_outer_loop.py`, and `tests/test_study_outer_loop_cases/controller_and_manifest_cases.py` runtime event, runtime escalation, supervisor tick freshness, retry budget and family human-gate cases.

Fresh semantic result：

- `runtime_event_and_outer_loop_input_contract.md` remains aligned with live outer-loop behavior: `runtime_event_ref` comes from OPL current_control_state / provider-backed stage runtime, MAS may consume and expose refs, and managed runtime inputs fail closed when runtime event identity, supervisor freshness or runtime escalation refs are missing or mismatched.
- `durable_workflow_contract.md` remains a human-readable support contract for pause/resume, replay, idempotent ticks, human-gate durability and retry budget semantics. The durable event log, attempt/retry/dead-letter/provider repair owner remains OPL; MAS writes only bounded projection, domain health diagnostic, runtime escalation and controller decision refs where its domain authority applies.
- Focused tests continue to assert replay from `restore_point_id`, reconstruction of `retry_budget_remaining`, `retry_budget_decremented`, retry-budget exhaustion requiring `runtime_escalation_record.json`, duplicate tick idempotency, and durable human-gate decision requirements.
- The reviewed prose does not currently reintroduce MAS-owned generic queue, attempt ledger, worker liveness, runtime lifecycle scheduler, publication-ready, submission-ready, artifact-ready, App release ready, domain-ready or production-ready claims.
- No archive/tombstone/delete action is justified in this tranche: both files still have distinct active runtime-support roles.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/contracts/runtime_event_and_outer_loop_input_contract.md` and `docs/runtime/contracts/durable_workflow_contract.md`, with live source/contract/test inventory checks listed above. | this coverage ledger only |

Archived / tombstoned / deleted docs: none. The reviewed files remain active support docs.

Uncovered docs in this semantic area:

- Remaining paragraph-level coverage is still open for other long support bodies under `docs/runtime/contracts/**`, especially `runtime_boundary.md`, `runtime_core_convergence_and_controlled_cutover.md`, `runtime_backend_interface_contract.md`, `runtime_handle_and_durable_surface_contract.md`, `agent_runtime_interface.md`, and delivery/artifact/source adjacent contracts not covered by prior focused tranches.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge and this runtime-event/durable-workflow block.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future prose must not treat missing or fallback `runtime_event_ref`, stale supervisor tick, runtime escalation, retry budget exhaustion, human-gate signal, domain health diagnostic, OPL provider closeout, queue completion or current_control_state projection as MAS domain completion, publication-ready, submission-ready, artifact-ready, quality-ready, App release ready or production-ready.
- `runtime_escalation_record.json`, `domain_health_diagnostic`, owner-route handoff refs and typed blockers are MAS diagnostic / blocker outputs; they must not become MAS-owned retry/dead-letter, provider repair, worker liveness, generic resume or runtime lifecycle truth.
- Durable human gate remains a decision ref with scope and evidence refs. It must not be rewritten as chat permission, executor self-approval, controller shortcut or automatic publication/quality override.

Next tranche write scope:

- MAS paragraph-level coverage for another bounded `docs/runtime/contracts/**` group, preferably `runtime_boundary.md` with runtime backend / handle contracts, or delivery/artifact/source adjacent contracts if owner wording drifts.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.
- Keep App docs delayed until active release/GUI lanes are safe to govern.

### 2026-05-26 runtime boundary / backend / handle contract coverage tranche

本轮覆盖 MAS runtime contract 中的 runtime owner boundary、backend interface、execution handle / durable surface 和 agent runtime interface 四个长支撑文档。目标是确认这些文档仍然把默认 generic runtime owner、provider attempt、queue、wakeup、retry/dead-letter、worker residency、transition runner、provider transport 与 current-control-state 归给 OPL provider-backed stage runtime；MAS 只承担 domain authority refs、DomainIntent / owner route、owner receipt、typed blocker、artifact/source/quality refs、guarded apply receipt、diagnostic explanation 和研究治理边界。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/architecture.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file, and preceding runtime id / owner-route control / stage-knowledge / runtime-event coverage ledger entries.
- Runtime contract docs: `docs/runtime/contracts/runtime_boundary.md`, `docs/runtime/contracts/runtime_backend_interface_contract.md`, `docs/runtime/contracts/runtime_handle_and_durable_surface_contract.md`, `docs/runtime/contracts/agent_runtime_interface.md`.
- Machine / source surfaces: `contracts/modules/runtime/module_contract.yaml`, `contracts/modules/controller_charter/module_contract.yaml`, `contracts/functional_privatization_audit.json`, `contracts/action_catalog.json`, `contracts/production_acceptance/mas-production-acceptance.json`, `src/med_autoscience/opl_runtime_contract.py`, `src/med_autoscience/runtime_protocol/study_runtime.py`, `src/med_autoscience/controllers/opl_runtime_refs.py`, `src/med_autoscience/runtime_protocol/domain_authority_refs_index.py`, `src/med_autoscience/action_catalog.py`.
- Structural context: CodeGraph context for runtime owner refs, `OplRuntimeRefs`, default runtime operation contract and control intent identity.
- Focused test inventory read as evidence: `tests/test_opl_runtime_contract.py`, `tests/test_runtime_protocol_study_runtime.py`, `tests/product_entry_cases/repo_shell_runtime_assertions.py`, `tests/test_opl_family_persistence_adapter.py`, `tests/product_entry_cases/manifest_launch_and_task_intake.py`, `tests/owner_route_reconcile_cases/owner_route_test_helpers.py`, and `tests/test_control_plane_generalization_cases/test_runtime_facts.py`.

Fresh semantic result：

- `runtime_boundary.md` remains aligned with current owner split: OPL provider-backed stage runtime owns generic runtime core, MAS owns domain authority refs and owner surfaces, and product projection only reads OPL current-control-state plus MAS domain refs.
- `runtime_backend_interface_contract.md` remains aligned with live machine contract: default runtime identity is `runtime_substrate/runtime_ref=opl_hosted_stage_runtime` and `runtime_engine_id=opl-hosted-stage-runtime`; `domain_runtime_adapter_id=mas_domain_intent_adapter`; `runtime_backend_role=mas_domain_owner_receipt_adapter`; `runtime_backend_is_generic_owner=false`; `default_runtime_backend_is_opl_provider_owned=true`; external MDS is not required for default operation.
- `runtime_handle_and_durable_surface_contract.md` remains aligned with source/tests: `program_id`, `study_id`, `quest_id` and `active_run_id` stay separate; `runtime_binding.yaml` writes `runtime_substrate`, `opl_runtime_ref`, `runtime_ref`, `runtime_engine_id`, `research_backend_id`, `research_backend`, `research_engine_id`, `runtime_home` and `runtime_quests_root`; `mas_runtime_core` and `hermes` runtime refs are rejected as current OPL runtime refs.
- `agent_runtime_interface.md` remains aligned with current product-entry / agent runtime surfaces: default executor remains `Codex CLI`, OPL is default generic runtime owner, MAS is domain entry / authority owner, MDS and Hermes wording stays in provenance / explicit diagnostic / explicit proof-lane context, and `study ensure-runtime` / MAS private scheduler style entrypoints are not reintroduced as current defaults.
- The reviewed prose does not currently reintroduce MAS-owned generic runtime owner, provider backend, runtime backend registry, hidden MDS fallback, Hermes default substrate, publication-ready, submission-ready, artifact-ready, App release ready, domain-ready or production-ready claims.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/contracts/runtime_boundary.md`, `docs/runtime/contracts/runtime_backend_interface_contract.md`, `docs/runtime/contracts/runtime_handle_and_durable_surface_contract.md`, and `docs/runtime/contracts/agent_runtime_interface.md`, with live source/contract/test inventory checks listed above. | this coverage ledger only |

Archived / tombstoned / deleted docs: none. The reviewed files remain active support docs with distinct roles.

Uncovered docs in this semantic area:

- MAS paragraph-level coverage remains open for `docs/runtime/contracts/runtime_core_convergence_and_controlled_cutover.md` and delivery/artifact/source-adjacent runtime contracts not covered by prior focused tranches.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow and runtime-boundary/backend/handle blocks.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future prose must not treat `mas_runtime_core`, `runtime_backend_id`, local scheduler, LaunchAgent, MDS daemon, Hermes gateway cron, `Codex-default host-agent runtime`, product-entry shell, sidecar, status or workbench helpers as current MAS-owned generic runtime owner or provider backend.
- `runtime_binding.yaml`, `progress_projection`, `domain_health_diagnostic`, `runtime_escalation_record.json`, `controller_decisions/latest.json`, runtime health snapshots and domain authority refs are durable refs/projections; they must not be promoted into OPL provider attempt truth, publication quality verdict, artifact mutation authorization, App release readiness or production readiness.
- Explicit MDS / Hermes / legacy local references remain source provenance, historical fixture, explicit archive import, backend audit, diagnostic adapter or proof-lane context only. Any future default-operation dependency on them is stale.

Next tranche write scope:

- MAS paragraph-level coverage for `docs/runtime/contracts/runtime_core_convergence_and_controlled_cutover.md`, or delivery/artifact/source-adjacent runtime contracts if owner wording drifts.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.
- Keep App docs delayed until active release/GUI lanes are safe to govern.

### 2026-05-26 runtime core convergence / controlled cutover coverage tranche

本轮覆盖 MAS runtime contract 中的 runtime core convergence / controlled cutover 支撑文档。目标是确认该文档仍然以 default independence / functional monolith closeout 为当前事实，不把旧 MDS resident daemon、WebUI、workspace-local service、MAS local scheduler、runtime lifecycle SQLite、turn runner 或 `mas_runtime_core` 写回当前默认 runtime owner，也不把 behavior-equivalence matrix 中保留的差异误写成 active implementation backlog。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/architecture.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file, and preceding runtime owner / runtime-event / runtime-boundary coverage ledger entries.
- Runtime / parity docs: `docs/runtime/contracts/runtime_core_convergence_and_controlled_cutover.md` and `docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md`.
- Machine / source surfaces: `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`, `contracts/production_acceptance/mas-production-acceptance.json`, `contracts/runtime/legacy-active-path-tombstones.json`, `src/med_autoscience/opl_runtime_contract.py`, `src/med_autoscience/controllers/mds_capability_parity_parts/behavior_equivalence.py`, `src/med_autoscience/controllers/mds_capability_parity_parts/paper_progress_degradation.py`, `src/med_autoscience/controllers/owner_route_reconcile_parts/scan_output.py`, and `src/med_autoscience/controllers/workspace_monolith_migration.py`.
- Focused test inventory read as evidence: `tests/test_mds_capability_parity.py`, `tests/test_opl_runtime_contract.py`, `tests/test_module_boundary_audit.py`, `tests/test_architecture_owner_boundary.py`, and study-progress runtime owner naming guard cases.

Fresh semantic result：

- `runtime_core_convergence_and_controlled_cutover.md` remains aligned with current contracts: default operation no longer requires external MDS repo, daemon, runtime root or WebUI; MDS is source provenance, historical fixture, explicit archive import, backend audit and parity oracle reference only.
- The document correctly separates `default_independence` / `functional_monolith_completion=landed` from full resident daemon behavior equivalence. The MDS behavior-equivalence matrix remains the owner for retained differences such as resident WebSocket/session continuity, connector background delivery, in-memory session API and interactive console parity.
- OPL provider-backed stage runtime / OPL scheduler replacement remains the default generic runtime and cadence owner. MAS keeps domain authority refs, owner receipt, typed blocker, artifact/source/quality refs, paper-progress SLO explanation and diagnostic projection.
- MAS local scheduler / LaunchAgent and Hermes gateway cron are still only explicit legacy diagnostic / cleanup / provenance contexts. They are not current MAS active scheduler options and are not default runtime truth.
- No reviewed paragraph currently reintroduces MDS daemon/WebUI/default backend dependency, workspace-local launchd/systemd/cron/docker service, MAS-owned generic runtime owner, `mas_runtime_core` active adapter, publication-ready, submission-ready, artifact-ready, App release ready, domain-ready or production-ready leakage.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/contracts/runtime_core_convergence_and_controlled_cutover.md`, with support read of `docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md` and live source/contract/test inventory checks listed above. | this coverage ledger only |

Archived / tombstoned / deleted docs: none. The reviewed file remains an active runtime-support / behavior-equivalence reference bridge with a distinct role.

Uncovered docs in this semantic area:

- MAS paragraph-level coverage remains open for delivery/artifact/source-adjacent runtime contracts not covered by prior focused tranches.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle and this runtime-core-convergence block.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future prose must not treat `functional_monolith_completion=landed`, default independence, Portal/Live Console read-only parity, behavior-equivalence purpose equivalence or zero external-MDS requirement as full resident-daemon equivalence, domain completion, production readiness or App release readiness.
- MDS resident daemon, WebUI, connector background delivery, in-memory session API, workspace-local launchd/systemd/cron/docker service, MAS local scheduler, Hermes gateway cron and `mas_runtime_core` can appear only as historical fixture, backend audit, parity oracle, explicit diagnostic / cleanup adapter or tombstone/provenance context.
- Behavior-equivalence matrix gaps should remain parity / UX / evidence candidates. They must not reopen MDS as default runtime owner or let UI/connector/old daemon surfaces bypass MAS study truth, publication gate, quality authority, artifact authority or OPL current-control-state.

Next tranche write scope:

- MAS paragraph-level coverage for delivery/artifact/source-adjacent runtime contracts, or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.
- Keep App docs delayed until active release/GUI lanes are safe to govern.

### 2026-05-26 artifact / baseline / retention contract coverage tranche

本轮覆盖 MAS delivery/artifact/source-adjacent runtime contracts 中的 artifact retention、canonical artifact 和 baseline refresh 三个支撑文档。目标是把文件生命周期、derived artifact authority 和 comparator/baseline refresh 读回当前 live source / tests / stage policy：MAS 可以产出 artifact authority refs、canonical rebuild proof、read-only retention candidate、baseline refresh obligation 和 typed blocker；OPL 继续持有 generic cleanup / restore / retention shell、provider stage runtime、queue / attempt / retry / dead-letter 和 App/workbench shell。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file, and preceding runtime-owner / runtime-core-convergence coverage ledger entries.
- Runtime contract docs: `docs/runtime/contracts/artifact_retention_operations_contract.md`, `docs/runtime/contracts/canonical_artifact_contract.md`, `docs/runtime/contracts/baseline_refresh_contract.md`, plus support read of `docs/runtime/contracts/delivery_plane_contract_map.md` and `docs/source/README.md`.
- Machine / source surfaces: `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`, `contracts/stage_control_plane.json`, `src/med_autoscience/controllers/artifact_retention_operations_plan.py`, `src/med_autoscience/controllers/artifact_lifecycle_operations_report.py`, `src/med_autoscience/controllers/storage_governance_policy_kernel.py`, `src/med_autoscience/controllers/canonical_artifact_contract.py`, `src/med_autoscience/stage_knowledge_contract.py`, and `src/med_autoscience/overlay/templates/medical-research-baseline.block.md`.
- Focused test evidence read from current source: `tests/test_artifact_retention_operations_plan.py`, `tests/test_storage_governance_policy_kernel.py`, `tests/test_canonical_artifact_contract.py`, `tests/test_body_free_evidence_refs_scaleout.py`, `tests/test_domain_entry.py::test_domain_entry_rejects_control_plane_cleanup_apply`, `tests/test_installed_mcp_smoke.py`, `tests/product_entry_cases/authority_operation_manifest.py`, and `tests/test_stage_surface_contract.py`.

Fresh semantic result：

- `artifact_retention_operations_plan` and `artifact_lifecycle_report` remain read-only planning / report surfaces. They can mark `delete_safe_cache` as a candidate and project restore-contract gaps, but public CLI, domain entry, product-entry command contracts and installed MCP must not expose cleanup apply commands. Physical cleanup / restore / retention apply belongs to the OPL owner shell after explicit parity and receipt gates.
- `canonical_artifact_contract` and `artifact_rebuild_integrity_contract` remain MAS artifact authority support. `manuscript/current_package/`, `artifacts/final/`, `current_package.zip` and `submission_minimal/` are derived projections / handoff surfaces, never edit source, quality authority or submission authorization root; rebuild proof requires source refs, fingerprints, quality decision ref, controller decision ref and generated artifact role.
- `baseline_refresh_contract` is currently enforced as a route / stage policy obligation through `baseline` stage inputs, memory closeout obligations and `medical-research-baseline.block.md`, not as an independent public CLI or artifact mutation command. Comparator, cohort, endpoint, Table 1, external-validation or manuscript-facing baseline changes need durable reason, affected surface list, verification refs and route / human-gate decision before becoming authoritative.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/contracts/artifact_retention_operations_contract.md`, `docs/runtime/contracts/canonical_artifact_contract.md`, and `docs/runtime/contracts/baseline_refresh_contract.md`, with support reads and live source/test evidence listed above. | `docs/runtime/contracts/artifact_retention_operations_contract.md`; `docs/runtime/contracts/baseline_refresh_contract.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. All three docs remain active runtime support; stale apply-command wording was rewritten in place because the document still holds the current read-only retention contract role.

Uncovered docs in this semantic area:

- Paragraph-level coverage remains open for `docs/runtime/contracts/standard_domain_agent_skeleton.md` beyond the quick support read.
- MAS source-support docs outside `docs/source/README.md` and delivery/medical-display documents that mention baseline refresh or artifact lifecycle remain outside this tranche.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that says MAS exposes `control-plane-cleanup-apply` / `control-plane-safe-cache-cleanup-apply`, performs physical cleanup from retention reports, or treats `delete_safe_cache` as already applied should be treated as stale pollution unless a new OPL owner shell and MAS receipt parity are proven.
- Any future prose that treats derived packages, DOCX/PDF/zip, `current_package`, `submission_minimal`, inspection packages, display packs, provider completion or executor logs as edit source, quality authority, source readiness verdict, publication-ready, submission-ready or artifact mutation authorization is stale pollution.
- Baseline refresh remains a stage-policy contract. A future materializer must produce durable refresh record / blocker / route refs; it must not silently overwrite comparator, Table 1, display pack, publication eval or submission package.

Next tranche write scope:

- MAS paragraph-level coverage for remaining `docs/runtime/contracts/standard_domain_agent_skeleton.md` and source/delivery support docs that mention source truth, artifact lifecycle, baseline refresh or standard-domain-agent anchors.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 standard-domain-agent skeleton / source-delivery support coverage tranche

本轮覆盖 MAS standard-domain-agent skeleton 支撑文档以及 source / delivery 目录索引中会影响 source truth、artifact authority、generated surface 和 OPL/MAS owner 边界的段落。目标是把 repo-source physical anchor、body-free locator、source readiness、artifact mutation 与 generated surface handoff 读回当前 contracts / source / tests：MAS 持有 `agent/` 语义包、source readiness / artifact authority gate、owner receipt、typed blocker 和 minimal authority functions；OPL 持有 generated CLI/MCP/Skill/product-entry/status/workbench shell、generic locator/projection/workbench 和 provider/runtime transport。

Live truth inputs：

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/references/positioning/mas_ideal_state.md`, this docs-governance file, and preceding artifact / runtime coverage ledger entries.
- Reviewed support docs: `docs/runtime/contracts/standard_domain_agent_skeleton.md`, `docs/source/README.md`, and `docs/delivery/README.md`.
- Machine / source surfaces: `agent/standard-domain-agent-anchor.json`, `contracts/runtime/standard-domain-agent-anchor.json`, `runtime/artifact_locator/workspace-runtime-artifact-root.locator.json`, `contracts/pack_compiler_input.json`, `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, `contracts/production_acceptance/mas-production-acceptance.json`, `src/med_autoscience/controllers/opl_provider_ready_adapter_parts/skeleton_mapping.py`, `src/med_autoscience/controllers/opl_provider_ready_adapter.py`, and product-entry manifest assembly.
- Focused test evidence read from current source: `tests/test_dev_preflight_contract.py`, `tests/test_opl_family_persistence_adapter.py`, `tests/product_entry_cases/action_catalog_parity_cases/memory_and_skeleton_cases.py`, `tests/test_opl_standard_pack.py`, `tests/test_body_free_evidence_refs_scaleout.py`, `tests/test_real_paper_autonomy_soak_inventory_cases/test_canary_body_free_packets.py`, and product-entry skeleton / workspace runtime evidence receipt cases.

Fresh semantic result：

- `standard_domain_agent_skeleton.md` remains active runtime support, but its first paragraph needed tightening: repo-source anchors are landed as standard placement / locator / descriptor anchors; existing callable/product/status/workbench surfaces are migration inputs and direct-path bridges, not long-term MAS-owned generated shells.
- The standard skeleton machine surface reads `mapping_mode=repo_source_physical_anchors_landed`, `repo_tracks_real_workspace_artifacts=false`, `repo_source_boundary.required_dirs=[agent, contracts, runtime, docs]`, `repo_source_boundary.forbidden_dirs=[artifacts]`, `artifact_roots_are_locators=true`, and default new surface slots under `agent/stages`, `agent/prompts`, `agent/skills`, `agent/knowledge`, `agent/quality_gates` and `contracts/runtime/*`.
- `runtime/artifact_locator/workspace-runtime-artifact-root.locator.json` remains locator-only. It may name workspace artifact roots, owner-route receipt refs, stage review indexes, publication-eval refs and controller-decision refs; it cannot move artifact bodies into repo source, authorize source readiness, mark publication quality, update `current_package`, or replace owner receipt / typed blocker evidence.
- `docs/source/README.md` remains aligned: Semantic Scholar is a read-model-only adapter/source for candidate refs and metadata enrichment; it cannot authorize source readiness verdict, publication quality, submission readiness, finalize readiness, artifact mutation, controller decision or publication gate pass. PubMed/CrossRef/PMC remain the grounding / crosswalk / provenance calibration layer.
- `docs/delivery/README.md` remains aligned as a delivery support index: manuscript/package/submission/export/review gate support stays MAS-owned; generic artifact lifecycle primitive is an OPL upscope candidate; active delivery boards must not accumulate old process logs.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/contracts/standard_domain_agent_skeleton.md`, `docs/source/README.md`, and `docs/delivery/README.md`, with live contract/source/test evidence listed above. | `docs/runtime/contracts/standard_domain_agent_skeleton.md`; `docs/source/README.md`; `docs/delivery/README.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The reviewed files remain active support docs with distinct roles; stale generated-facade wording was rewritten in place because the standard skeleton doc still owns the repo-source anchor explanation.

Uncovered docs in this semantic area:

- MAS source-support documents outside `docs/source/README.md`, including workspace architecture / disease workspace references and source-readiness policy docs, remain outside this tranche.
- MAS delivery docs outside `docs/delivery/README.md` and the already-covered inspection/artifact/baseline blocks remain outside this tranche, including medical-display support docs that mention artifact lifecycle, source truth or package authority.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle, runtime-core-convergence, artifact/baseline/retention and this standard skeleton/source-delivery index block.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future prose must not treat MAS repo-source anchors, existing direct-path callables, product/status/workbench wrappers or generated docs as MAS-owned generated shell ownership. They are descriptor / locator / receipt / typed-blocker / authority-function refs until OPL generated/default caller cutover proves replacement and no-active-caller deletion gates.
- Future prose must not treat source provider ranking, citation count, abstract match, cache hit, package freshness, file presence, generated-interface readiness, test pass or provider completion as source readiness, publication quality, submission readiness, artifact mutation authorization or `current_package` update.
- `runtime/artifact_locator` and body-free evidence packets must stay locator/ref/receipt/blocker surfaces. Any artifact body, memory body, study truth body or quality verdict body entering repo source or OPL projection is stale pollution.

Next tranche write scope:

- MAS paragraph-level coverage for source references under `docs/references/workspace/**` and source-readiness / study-workflow policy docs, or delivery / medical-display docs that mention artifact lifecycle, source truth or package authority.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 workspace / source reference coverage tranche

本轮覆盖 MAS workspace/source references 中会影响 workspace lifecycle、source truth、artifact locator、root Git retirement、Hermes/MDS retained-role 和 OPL/MAS owner split 的段落。目标是把 workspace bootstrap / architecture prose 读回当前 live contracts / source / tests：MAS 持有 source readiness、study truth、quality gate、artifact authority、owner receipt 和 typed blocker；OPL 持有 generic workspace/file lifecycle、artifact locator、restore/retention shell、provider runtime、queue/attempt/retry/dead-letter 和 App/operator projection shell。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/references/positioning/mas_ideal_state.md`, this docs-governance file, and preceding artifact / runtime / standard skeleton coverage ledger entries.
- Reviewed support docs: `docs/references/workspace/disease_workspace_quickstart.md`, `docs/references/workspace/workspace_architecture.md`, `docs/source/README.md`, `docs/policies/study-workflow/workspace_autoscience_rules.md`, `docs/policies/study-workflow/stage_led_research_autonomy.md`, and `docs/policies/study-workflow/data_asset_management.md`.
- Machine / source surfaces: `contracts/workspace_lifecycle_policy.json`, `contracts/functional_privatization_audit.json`, `contracts/pack_compiler_input.json`, `contracts/stage_control_plane.json`, `profiles/workspace.profile.template.toml`, `src/med_autoscience/controllers/workspace_init.py`, `src/med_autoscience/controllers/workspace_init_parts/profile_config.py`, `src/med_autoscience/controllers/workspace_init_parts/retired_entries.py`, `src/med_autoscience/controllers/runtime_storage_maintenance.py`, `src/med_autoscience/controllers/storage_governance_policy_kernel.py`, `src/med_autoscience/controllers/workspace_literature.py`, and `src/med_autoscience/profiles.py`.
- Focused test evidence read from current source: `tests/test_workspace_init.py`, `tests/test_workspace_init_cases/workspace_creation.py`, `tests/test_workspace_init_cases/managed_script_bindings.py`, `tests/test_runtime_storage_maintenance.py`, `tests/test_profiles.py`, and `tests/test_opl_runtime_contract.py`.

Fresh semantic result:

- `disease_workspace_quickstart.md` remains active workspace bootstrap reference, but its machine boundary and lifecycle paragraphs needed tightening: SQLite / ledger / manifest surfaces are durable refs/projections, not MAS generic lifecycle ownership. Generic workspace/file lifecycle, artifact locator, restore/retention shell and operator projection belong to OPL primitives.
- `workspace_architecture.md` remains active workspace architecture support. The retained workspace shape still uses `runtime/quests`, `runtime/archives`, `runtime/restore_index`, `artifacts/runtime`, `ops/medautoscience` and `ops/mas`, while root Git and quest Git remain retired from active truth. The updated wording separates MAS source/artifact/quality/study truth authority from OPL lifecycle/locator/provider ownership.
- Hermes remains an optional external executor adapter / proof lane / diagnostic / historical reference. It must not be written as default outer runtime substrate or scheduler owner. MDS / DeepScientist remains source provenance, historical fixture, explicit archive import, backend audit, upstream intake or parity oracle reference only.
- `docs/source/README.md` and the reviewed study-workflow policies remain aligned: source provider readiness, literature records, data asset registry, ToolUniverse output, workspace memory or quest-local materialization cannot authorize source readiness verdict, publication quality, submission readiness, artifact mutation, `current_package` update or controller decision.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/references/workspace/disease_workspace_quickstart.md` and `docs/references/workspace/workspace_architecture.md`; support read of source index / study-workflow policies and live contract/source/test evidence listed above. | `docs/references/workspace/disease_workspace_quickstart.md`; `docs/references/workspace/workspace_architecture.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. Both workspace reference files remain active support docs with distinct roles; stale owner wording was rewritten in place because they still own current workspace bootstrap / architecture explanation.

Uncovered docs in this semantic area:

- Source-readiness policy and stage workflow docs were read as support in this tranche, but full paragraph-level governance remains open for all `docs/policies/study-workflow/*.md` outside the specific source/workspace owner-boundary sections listed above.
- MAS delivery / medical-display docs outside the already-covered inspection, artifact/baseline/retention and delivery index blocks remain open when they mention artifact lifecycle, source truth, package authority or display-pack authority.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle, runtime-core-convergence, artifact/baseline/retention, standard skeleton/source-delivery index and this workspace/source reference block.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that treats runtime lifecycle SQLite, lifecycle ledgers, storage audit, root Git retirement, restore index, artifact locator, provider completion or OPL read model as MAS-owned generic lifecycle authority is stale pollution.
- Any future prose that writes Hermes, MAS `local` adapter, LaunchAgent, `mas_runtime_core`, MDS/DeepScientist daemon, workspace-local service or root/quest Git back into default runtime owner, scheduler owner, active adapter, diagnostic fallback or compatibility alias is stale pollution.
- Any future prose that treats source provider ranking, citation count, abstract match, ToolUniverse output, data asset registry, workspace literature, quest-local cache, file presence, package freshness, test pass or provider completion as source readiness, publication quality, submission readiness, artifact mutation authorization or `current_package` update is stale pollution.

Next tranche write scope:

- MAS paragraph-level coverage for remaining study-workflow source-readiness / data-asset policy docs, or delivery / medical-display docs that mention artifact lifecycle, source truth, package authority or display-pack authority.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 workspace profile / source policy correction tranche

本轮在已有 workspace / source reference coverage 之后，补齐两个 residual drift：workspace architecture 仍把旧 `managed_runtime_backend_id=opl_provider_backed_stage_runtime` 写成 profile/default machine truth，profile template 仍把 Hermes 写成 outer runtime substrate cutover；data asset policy 仍用 `MedDeepScientist` 主控作 ToolUniverse 的对照。目标是把这些 support/profiles 文字重新对齐 live `profiles.py`、profile template、runtime-id contract、source/workspace policy 和 stage knowledge / literature truth：当前 profile field 是 `opl_runtime_ref`，默认值是 `opl_hosted_stage_runtime`，engine id 是 `opl-hosted-stage-runtime`；OPL/Temporal provider-backed 是 owner/topology 语义；Hermes 只作显式非默认 executor adapter、proof lane、diagnostic 或历史参考；ToolUniverse 只作外部工具适配层，不能替代 MAS source / study / quality / artifact authority 或 OPL runtime owner。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, preceding runtime-id / standard skeleton / workspace-source coverage ledger entries.
- Reviewed docs / templates: `docs/references/workspace/workspace_architecture.md`, `docs/policies/study-workflow/data_asset_management.md`, `profiles/workspace.profile.template.toml`, and support read of `docs/source/README.md`, `docs/references/workspace/disease_workspace_quickstart.md`, `docs/runtime/contracts/workspace_knowledge_and_literature_contract.md`, and `docs/policies/study-workflow/workspace_autoscience_rules.md`.
- Machine / source surfaces: `src/med_autoscience/profiles.py`, `src/med_autoscience/opl_runtime_contract.py`, `src/med_autoscience/runtime_protocol/study_runtime.py`, `src/med_autoscience/runtime_protocol/workspace_literature_status.py`, `src/med_autoscience/stage_knowledge_contract.py`, `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`, and `contracts/stage_control_plane.json`.
- Focused test evidence read from current source: `tests/test_profiles.py`, `tests/test_runtime_protocol_study_runtime.py`, `tests/test_stage_knowledge_plane.py`, `tests/test_stage_knowledge_entry_injection.py`, `tests/test_semantic_scholar_provider_runtime_contract.py`, and workspace init / managed script binding tests referenced by the prior workspace-source tranche.

Fresh semantic result:

- `workspace_architecture.md` now names `opl_runtime_ref` rather than `managed_runtime_backend_id` as the active profile field, and states the current default runtime machine ref as `opl_hosted_stage_runtime` with engine id `opl-hosted-stage-runtime`.
- `profiles/workspace.profile.template.toml` no longer calls Hermes the outer runtime substrate cutover path; it is now explicitly scoped to non-default executor adapter / proof / diagnostic / history roles.
- `data_asset_management.md` now states ToolUniverse cannot replace MAS source readiness, study truth, quality gate, artifact authority or OPL provider/runtime owner.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Focused correction read of `workspace_architecture.md` profile contract section, `data_asset_management.md` ToolUniverse principle, `profiles/workspace.profile.template.toml` Hermes comments, plus support reads and live truth inputs listed above. | `docs/references/workspace/workspace_architecture.md`; `docs/policies/study-workflow/data_asset_management.md`; `profiles/workspace.profile.template.toml`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. These files remain active support / template surfaces with distinct roles; the drift was current wording, not a retire/delete case.

Uncovered docs in this semantic area:

- Full paragraph-level governance remains open for other `docs/policies/study-workflow/*.md` files not explicitly covered in the workspace/source and this correction tranche.
- MAS delivery / medical-display docs outside the already-covered inspection, artifact/baseline/retention and delivery index blocks remain open when they mention artifact lifecycle, source truth, package authority or display-pack authority.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that writes `managed_runtime_backend_id` or `opl_provider_backed_stage_runtime` as current workspace profile machine truth is stale. Use `opl_runtime_ref=opl_hosted_stage_runtime` for profile/runtime ref identity, and reserve OPL/Temporal provider-backed wording for owner/topology.
- Any future prose that writes Hermes as default outer runtime substrate, default scheduler owner or required workspace bootstrap dependency is stale unless it is explicitly history/provenance.
- Any future prose that uses ToolUniverse, data asset registry, workspace literature, provider output or test pass as source readiness verdict, publication quality verdict, artifact mutation authority, `current_package` freshness proof or OPL provider completion is stale.

Next tranche write scope:

- MAS paragraph-level coverage for remaining study-workflow source-readiness / data-asset policy docs, or delivery / medical-display docs that mention artifact lifecycle, source truth, package authority or display-pack authority.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 study-workflow policy authority-boundary tranche

本轮逐段覆盖 MAS `docs/policies/study-workflow/` policy set、publication-route memory body/index、source index 与 stage/workspace knowledge runtime contract。目标是把 study workflow policy 读回当前 live stage route contract、stage knowledge plane、workspace literature、data asset、source-provider 与 owner-route/read-model 事实：自然语言 memory、candidate board、provider metadata、workspace literature、data asset registry、ToolUniverse 输出和 package projection都只能作为 context、refs、readiness input、proposal、receipt 或 blocker；正式 source readiness、route decision、publication quality、submission readiness、artifact authority、`current_package` 更新和 human-gate 判断仍由 MAS owner surfaces 授权，OPL 只承接 provider runtime、queue/wakeup/resume/human-gate transport、locator/projection 和 App/workbench shell。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/project.md`, `docs/status.md`, `docs/architecture.md`, `docs/invariants.md`, `docs/decisions.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/references/positioning/mas_ideal_state.md`, this docs-governance file, and preceding workspace/source/profile coverage ledger entries.
- Reviewed policy docs: all files under `docs/policies/study-workflow/`, including `README.md`, `stage_led_research_autonomy.md`, `publication_route_memory_policy.md`, `publication_route_memory_library.md`, `publication_route_memory_seed_fixture.json`, `study_archetypes.md`, `research_route_bias_policy.md`, `study_route_contract.md`, `data_asset_management.md`, `submission_revision_operating_contract.md`, `bounded_analysis_frontier_policy.md`, and `workspace_autoscience_rules.md`.
- Support docs: `docs/source/README.md`, `docs/runtime/contracts/workspace_knowledge_and_literature_contract.md`, and `docs/runtime/contracts/stage_route_contract.md`.
- Machine / source surfaces: `agent/stages/stage_route_contract.yaml`, `src/med_autoscience/stage_knowledge_contract.py`, `src/med_autoscience/controllers/stage_knowledge_plane.py`, `src/med_autoscience/controllers/data_assets.py`, `src/med_autoscience/controllers/workspace_literature.py`, `src/med_autoscience/runtime_protocol/workspace_literature_status.py`, `contracts/stage_control_plane.json`, `contracts/action_catalog.json`, `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, and `contracts/opl-framework/family-contract-adoption.json`.
- Focused test evidence read from current source: `tests/test_stage_knowledge_plane.py`, `tests/test_stage_knowledge_entry_injection.py`, `tests/test_stage_knowledge_visibility.py`, `tests/test_stage_route_contract.py`, `tests/test_stage_route_assets.py`, `tests/test_semantic_scholar_provider_runtime_contract.py`, `tests/test_data_asset_gate.py`, `tests/product_entry_cases/action_catalog_parity_cases/memory_and_skeleton_cases.py`, and workspace init / managed-script tests referenced by the prior workspace-source tranches.

Fresh semantic result:

- `study_route_contract.md` remains active policy support for the canonical YAML route contract, but its stage-packet wording was tightened: stage packet is a handoff / read-model input, not route authority; official go / stop / reroute / human-gate decisions still require controller decisions, ledgers, publication eval, owner receipts or typed blockers.
- `bounded_analysis_frontier_policy.md` remains active policy support for bounded repair discipline. It now states that candidate boards are stage execution / audit traces, not route scorers or quality/source verdicts, and that selected paths or stop reasons can only feed controller / AI reviewer / publication gate.
- `submission_revision_operating_contract.md` remains active contract support for same-line revision and submission delivery. It now distinguishes controller-authorized `paper/` sources from current-package / DOCX / PDF / ZIP projections and treats foreground package edits as review overlays until reconciled into canonical paper sources.
- `workspace_autoscience_rules.md` remains the thin workspace-side summary. It now names MAS controller / owner surfaces for data, gate and delivery updates, and OPL as runtime/projection shell owner; workspace literature, data asset registry, ToolUniverse output and provider cache/ranking cannot authorize source readiness or publication/package authority.
- `publication_route_memory_policy.md`, `publication_route_memory_library.md`, `publication_route_memory_seed_fixture.json`, `study_archetypes.md`, and `research_route_bias_policy.md` remain aligned: Markdown body is the canonical natural-language memory source, JSON is locator/index, workspace packs/receipts are generated MAS owner surfaces, and route memory / archetype / route bias is context only, not a recipe engine, route scorer, controller decision or publication quality owner.
- `data_asset_management.md`, `docs/source/README.md`, `workspace_knowledge_and_literature_contract.md`, and the generated `stage_route_contract.md` remain aligned with live implementation: provider readiness, workspace canonical literature, quest materialization, data asset status and stage recall can fail closed or route to repair, but cannot be promoted to source readiness verdict, claim expansion, finalize readiness, artifact mutation or controller route.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of all `docs/policies/study-workflow/*` Markdown files and the seed fixture JSON; support read of `docs/source/README.md`, `docs/runtime/contracts/workspace_knowledge_and_literature_contract.md`, `docs/runtime/contracts/stage_route_contract.md`; live contract/source/test evidence listed above. | `docs/policies/study-workflow/study_route_contract.md`; `docs/policies/study-workflow/bounded_analysis_frontier_policy.md`; `docs/policies/study-workflow/submission_revision_operating_contract.md`; `docs/policies/study-workflow/workspace_autoscience_rules.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The study-workflow policy files remain active policy/support docs with distinct roles; this tranche corrected current authority-boundary wording rather than retiring surfaces.

Uncovered docs in this semantic area:

- `docs/policies/study-workflow/` is paragraph-covered for this source/stage-workflow authority-boundary pass.
- MAS delivery / medical-display docs outside the already-covered inspection, artifact/baseline/retention and delivery index blocks remain open when they mention artifact lifecycle, source truth, package authority or display-pack authority.
- Runtime support docs outside previously covered projection/display/inspection/controller/stage route snippets remain open, especially other `docs/runtime/contracts/**`, `docs/runtime/control/**`, and medical-display / delivery-facing stage-handoff sections.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that treats stage packet, candidate board, publication-route memory card, route-bias prose, workspace literature, data asset registry, ToolUniverse output, source-provider ranking/cache, package projection, file presence, test pass or provider completion as source readiness, route authority, publication quality, submission readiness, artifact mutation authorization or `current_package` freshness is stale pollution.
- Any future prose that reintroduces route memory as recipe engine / winning-route scorer, or lets controller/materializer/read-model generate a winning path without stage output and evidence refs, is stale pollution.
- Any future prose that writes OPL as MAS memory body owner, study truth owner, quality owner, artifact authority or source readiness owner is stale pollution; OPL remains locator/projection/provider/runtime owner.
- Route-memory library cards remain advisory reusable experience. They should not become fixed workflows or ordinary-user edit UI without audited evidence obligations, owner boundary, receipt generation and failure behavior.

Next tranche write scope:

- MAS delivery / medical-display paragraph coverage for docs that mention artifact lifecycle, source truth, package authority or display-pack authority.
- Or MAS runtime/control support docs under `docs/runtime/contracts/**` and `docs/runtime/control/**` not already covered.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 medical-display delivery authority coverage tranche

本轮覆盖 MAS `docs/delivery/medical-display/` 中最容易影响下一轮 display work 路由的入口、portfolio、figure route、platform mainline 和 active board 文档。目标是把 medical-display 能力族读回当前 live route / renderer / pack contract / artifact authority 边界：display 支撑可以定义 renderer、schema、template、layout QC、route cookbook、display-to-claim audit input 和 generated display artifacts；source readiness、publication quality、submission readiness、artifact mutation、`current_package` freshness、delivery sync、paper closure、domain ready 和 production ready 继续归 MAS owner authority / receipt / typed blocker 与真实 workspace evidence。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/delivery/README.md`, this docs-governance file, and preceding source / delivery / artifact authority coverage ledger entries.
- Reviewed medical-display docs: `docs/delivery/medical-display/README.md`, `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`, `docs/delivery/medical-display/contracts/domain_handler_figure_routes.md`, `docs/delivery/medical-display/contracts/medical_display_platform_mainline.md`, and `docs/delivery/medical-display/board/medical_display_active_board.md`.
- Machine / source surfaces: `contracts/pack_compiler_input.json`, `contracts/stage_control_plane.json`, `contracts/artifact_locator_contract.json`, `agent/knowledge/source_readiness_and_artifact_authority.md`, `src/med_autoscience/figure_routes.py`, `src/med_autoscience/figure_renderer_contract.py`, `src/med_autoscience/display_pack_contract.py`, `src/med_autoscience/display_pack_loader.py`, and display materialization / layout QC source indexed by CodeGraph.
- Focused test evidence read from current source: `tests/test_figure_routes.py`, `tests/test_figure_renderer_contract.py`, `tests/test_display_pack_contract.py`, `tests/test_display_pack_loader.py`, `tests/test_figure_loop_guard.py`, and the display-pack / layout-QC / materialization test inventory under `tests/display_*` and `tests/test_display_*`.

Fresh semantic result:

- `figure_routes.py` currently accepts only `figure_script_fix:<figure-id>` and `figure_illustration_program:<figure-id>`; ambiguous `sidecar:<figure-id>` and removed autofigure routes fail closed. The help text already states figure route metadata is display-to-claim QA input and does not authorize publication readiness.
- `figure_renderer_contract.py` keeps evidence figures on `python` / `r_ggplot2`, allows `html_svg` only for illustration / submission companion semantics, and requires `fallback_on_failure=false` plus `failure_action=block_and_fix_environment`; renderer failure cannot justify a renderer-family switch.
- Display pack contracts validate namespaced pack/template ids, audit families, renderer family, schema refs, QC refs, required exports, paper roles and pack source/version refs. Those contracts are template / renderer / inventory truth, not artifact mutation authority, source readiness verdict or submission readiness.
- `domain_handler_figure_routes.md`, `medical_display_platform_mainline.md` and `medical_display_active_board.md` already preserve the main boundary: OPL owns transport/projection, MAS owns artifact / quality / domain authority, and visual/display gates are necessary support rather than final paper readiness.
- The medical-display subtree needed one first-screen delivery-authority guard in its README so future owners do not treat display-pack readiness, generated display artifacts, route cookbook, visual audit or exemplar intake as source/publication/artifact/domain readiness.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/delivery/medical-display/README.md`, `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`, `docs/delivery/medical-display/contracts/domain_handler_figure_routes.md`, `docs/delivery/medical-display/contracts/medical_display_platform_mainline.md`, and `docs/delivery/medical-display/board/medical_display_active_board.md`, with live source/contract/test evidence listed above. | `docs/delivery/medical-display/README.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The reviewed files remain active delivery support docs with distinct roles; stale authority leakage was handled by adding the missing first-screen boundary to the subtree README.

Uncovered docs in this semantic area:

- Full paragraph-level coverage remains open for the long medical-display inventory / catalog / plan / provenance bodies: `medical_display_audit_guide.md`, `medical_display_visual_audit_protocol.md`, `medical_display_arsenal.md`, `medical_display_template_backlog.md`, `medical_display_template_catalog.md`, `medical_figure_route_cookbook.md`, `medical_display_template_pack_architecture.md`, `medical_display_family_roadmap.md`, and `medical_display_anchor_paper_audit.md`.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle, runtime-core-convergence, artifact/baseline/retention, standard skeleton/source-delivery index, workspace/source references, study-workflow policy block and this bounded medical-display block.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that treats display pack presence, template count, generated display artifact, visual-audit pass, route cookbook, exemplar intake, renderer success, display materialization, package source/version lock or OPL projection as source readiness verdict, publication quality verdict, submission readiness, artifact mutation authorization, `current_package` update, delivery sync, paper closure, domain ready or production ready is stale pollution.
- External drawing / sidecar / autofigure route wording must stay retired unless a new explicit owner route, artifact authority receipt, focused tests and tombstone/provenance boundary are landed. `figure_illustration_program` cannot be used to edit evidence, claim text, result plots or source/statistics refs.
- Long medical-display catalogs and plans still need dedicated future coverage because their size and inventory role make them unsuitable for this bounded tranche.

Next tranche write scope:

- MAS paragraph-level coverage for the remaining medical-display catalog / plan / audit-guide bodies, preferably `medical_display_audit_guide.md` + `medical_display_visual_audit_protocol.md` or `medical_display_template_pack_architecture.md`.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 medical-display audit protocol coverage tranche

本轮继续覆盖 MAS `docs/delivery/medical-display/contracts/` 中两份直接定义显示审计边界的长 support 文档。目标是把 `medical_display_audit_guide.md` 与 `medical_display_visual_audit_protocol.md` 读回当前 live renderer / schema / display pack / layout QC / publication-display / submission-minimal 事实：显示审计可以定义 deterministic lower bound、视觉审计格式、style/override 合同、generated display output 接受门和 promotion-to-contract/QC/golden-regression 路径；它不能授权 source readiness、publication quality verdict、submission readiness、artifact mutation、`current_package` freshness、delivery sync、paper closure、domain ready 或 production ready。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file, and the preceding medical-display delivery authority coverage ledger.
- Reviewed medical-display docs: `docs/delivery/medical-display/contracts/medical_display_audit_guide.md` and `docs/delivery/medical-display/contracts/medical_display_visual_audit_protocol.md`.
- Machine / source surfaces: `src/med_autoscience/figure_routes.py`, `src/med_autoscience/figure_renderer_contract.py`, `src/med_autoscience/display_pack_contract.py`, `src/med_autoscience/display_pack_loader.py`, `src/med_autoscience/publication_display_contract.py`, `src/med_autoscience/controllers/display_surface_materialization/`, `src/med_autoscience/display_layout_qc/`, `src/med_autoscience/controllers/medical_publication_surface.py`, and `src/med_autoscience/controllers/submission_minimal.py`.
- Focused test evidence read from current source: `tests/test_figure_renderer_contract.py`, `tests/test_publication_display_contract.py`, `tests/test_submission_minimal_display_surface.py`, `tests/test_medical_publication_surface.py`, plus CodeGraph context for display pack loader, figure routes, publication display, submission minimal and display surface materialization.

Fresh semantic result:

- `medical_display_audit_guide.md` remains the active engineering audit surface for deterministic display lower-bound coverage, audited template inventory, schema/renderer/QC/export coupling and change protocol.
- The guide now scopes generated display outputs, `paper/submission_minimal/`, `paper/publication_style_profile.json` and readability failures to display / projection / visual-style authority. These surfaces do not become artifact authority, source truth, source readiness verdict, publication quality verdict, submission readiness or package freshness authority.
- `medical_display_visual_audit_protocol.md` remains the active AI-first visual audit support protocol above deterministic QC. Its finding format, promotion rules and minimal Codex loop remain valid, but acceptance wording is now scoped to paper-facing display-surface completion.
- `visual audit clear` means the generated display surface can be accepted for the paper-facing display lane after deterministic and visual findings are closed or explicitly accepted. It does not close publication gate, submission package readiness, artifact mutation, `current_package`, delivery sync, paper closure, domain ready or production ready.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/delivery/medical-display/contracts/medical_display_audit_guide.md` and `docs/delivery/medical-display/contracts/medical_display_visual_audit_protocol.md`, with live source/contract/test evidence listed above. | `docs/delivery/medical-display/contracts/medical_display_audit_guide.md`; `docs/delivery/medical-display/contracts/medical_display_visual_audit_protocol.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. Both files remain active delivery contract support docs with distinct roles; stale authority leakage was corrected in place.

Uncovered docs in this semantic area:

- Full paragraph-level coverage remains open for the remaining long medical-display inventory / catalog / provenance bodies: `medical_display_arsenal.md`, `medical_display_template_backlog.md`, `medical_display_template_catalog.md`, `medical_figure_route_cookbook.md`, `medical_display_family_roadmap.md`, and `medical_display_anchor_paper_audit.md`.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle, runtime-core-convergence, artifact/baseline/retention, standard skeleton/source-delivery index, workspace/source references, study-workflow policy block and this bounded medical-display block.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose that treats `gate clear`, `visual audit clear`, generated display outputs, visual style profile, display overrides, submission-minimal projection, renderer/QC pass, display pack lock or catalog entry as source readiness, formal publication-quality verdict, submission readiness, artifact mutation authorization, `current_package` freshness, delivery sync, paper closure, domain ready or production ready is stale pollution.
- Hidden post-processing, handmade figure cleanup, fallback renderer substitution, external exemplar copying, legacy sidecar/autofigure route wording and compatibility aliases remain retire candidates unless a new explicit MAS owner route, artifact authority receipt, focused tests and tombstone/provenance boundary are landed.

Next tranche write scope:

- MAS paragraph-level coverage for `medical_display_arsenal.md` + `medical_display_template_backlog.md` + `medical_display_template_catalog.md`, or `medical_figure_route_cookbook.md` + `medical_display_family_roadmap.md` + `medical_display_anchor_paper_audit.md`.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 medical-display route roadmap provenance coverage tranche

本轮覆盖 MAS medical-display route / roadmap / provenance 三件套。目标是把 `medical_figure_route_cookbook.md`、`medical_display_family_roadmap.md` 与 `medical_display_anchor_paper_audit.md` 读回当前 live figure-route source、domain-handler figure-route contract、display audit / catalog truth 和 anchor-paper closure lifecycle：cookbook 是 paper-facing route family support，不是 dispatchable route registry；roadmap 是 long-horizon paper-family target，不是当前 execution queue；anchor audit 是 `001/003` closure snapshot provenance，不是当前 package freshness、publication quality、submission readiness、artifact mutation、paper closure、domain ready 或 production ready 判据。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file, and preceding medical-display delivery authority / audit-protocol / catalog inventory / template-pack lifecycle ledger entries.
- Reviewed medical-display docs: `docs/delivery/medical-display/catalogs/medical_figure_route_cookbook.md`, `docs/delivery/medical-display/portfolio/medical_display_family_roadmap.md`, `docs/delivery/medical-display/provenance/medical_display_anchor_paper_audit.md`, plus role/index review of `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`.
- Machine / source surfaces: `src/med_autoscience/figure_routes.py`, `src/med_autoscience/controllers/figure_loop_guard.py`, `docs/delivery/medical-display/contracts/domain_handler_figure_routes.md`, `docs/delivery/medical-display/contracts/medical_display_platform_mainline.md`, `docs/delivery/medical-display/contracts/medical_display_audit_guide.md`, generated template catalog, registry/schema contracts and current display-pack source/tests.
- Focused test evidence read from current source: `tests/test_figure_routes.py`, `tests/test_figure_loop_guard.py`, display pack / materialization / submission-minimal display tests, and CodeGraph context for `FigureRoute`, `build_figure_route`, `parse_figure_route`, `normalize_required_route`, `partition_required_routes` and figure-loop guard route consumption.

Fresh semantic result:

- `medical_figure_route_cookbook.md` remains active support for paper-facing route families. It now distinguishes cookbook route families from executable MAS/OPL route ids, points dispatchable figure-route truth to `figure_routes.py` and the domain-handler route contract, and states that only `figure_script_fix:<figure-id>` and `figure_illustration_program:<figure-id>` are current parseable figure-route metadata. `sidecar:<figure-id>`, autofigure and external drawing routes remain retired / fail-closed.
- `medical_display_family_roadmap.md` remains active support for the long-horizon `A-H` paper-family roadmap. Its anchor-paper recovery section now reads as post-recovery direction rather than an open figure-QA execution queue, and it explicitly keeps roadmap progress separate from source readiness, publication quality, submission readiness, artifact mutation, `current_package` freshness, paper closure, domain ready and production ready.
- `medical_display_anchor_paper_audit.md` remains `history_provenance` for the `001/003` closure snapshot. It now labels its authority / verification wording as closure-time provenance and prevents historical `fresh` / `clear` language from being used as current package freshness, publication quality, submission readiness, paper closure, domain ready or production ready evidence.
- `medical_display_portfolio_consolidation.md` now separates route references from anchor-paper provenance in the portfolio map.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/delivery/medical-display/catalogs/medical_figure_route_cookbook.md`, `docs/delivery/medical-display/portfolio/medical_display_family_roadmap.md`, and `docs/delivery/medical-display/provenance/medical_display_anchor_paper_audit.md`; role/index review of `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`, with live source/contract/test evidence listed above. | `docs/delivery/medical-display/catalogs/medical_figure_route_cookbook.md`; `docs/delivery/medical-display/portfolio/medical_display_family_roadmap.md`; `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`; `docs/delivery/medical-display/provenance/medical_display_anchor_paper_audit.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The cookbook and roadmap remain active support with distinct route-family and roadmap roles; the anchor audit remains history provenance.

Uncovered docs in this semantic area:

- The bounded medical-display subtree named in prior tranches is now covered at paragraph level for the delivery authority, audit protocol, catalog/inventory, template-pack lifecycle, route cookbook, roadmap and anchor-paper provenance bodies.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle, runtime-core-convergence, artifact/baseline/retention, standard skeleton/source-delivery index, workspace/source references, study-workflow policy block and bounded medical-display blocks.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future route cookbook prose that treats cookbook route families as dispatchable MAS/OPL route ids, revives `sidecar:<figure-id>` / autofigure / external drawing routes, or treats figure-route metadata as artifact authority, quality verdict, source readiness, submission readiness or paper closure is stale pollution.
- Future roadmap prose that turns `A-H` target families into an active execution queue, checklist-completion gate or production/domain readiness claim is stale pollution.
- Future anchor-paper audit prose that uses the `001/003` historical clear/fresh results as current package freshness, current workspace authority, publication quality, submission readiness, artifact mutation authorization, paper closure, domain ready or production ready evidence is stale pollution.

Next tranche write scope:

- MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks, or source/delivery shell docs that still mention artifact lifecycle, source truth or package authority.
- Or choose the next exact OPL/RCA/MAG/App uncovered body from the family coverage ledger.

### 2026-05-26 medical-display catalog inventory coverage tranche

本轮覆盖 MAS medical-display catalog / inventory 三件套。目标是把 `medical_display_arsenal.md`、`medical_display_template_backlog.md` 与 `medical_display_template_catalog.md` 读回当前 audited display source、audit guide、template-pack source/tests 和已完成 backlog 出队事实：catalog / arsenal / backlog 是 human-readable inventory 和 candidate pool，不是 active owner round、执行流水、吸收记录、source readiness、publication quality、submission readiness、artifact mutation、`current_package` freshness、paper closure、domain ready 或 production ready 判据。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/invariants.md`, `docs/decisions.md`, this docs-governance file, and preceding medical-display delivery authority / audit-protocol / template-pack lifecycle ledger entries.
- Reviewed medical-display docs: `docs/delivery/medical-display/catalogs/medical_display_arsenal.md`, `docs/delivery/medical-display/catalogs/medical_display_template_backlog.md`, `docs/delivery/medical-display/catalogs/medical_display_template_catalog.md`, plus role/index review of `docs/delivery/medical-display/README.md` and `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`.
- Machine / source surfaces: `src/med_autoscience/display_registry.py`, `src/med_autoscience/display_schema_contract.py`, `src/med_autoscience/display_schema_contract_parts/**`, `src/med_autoscience/display_pack_contract.py`, `src/med_autoscience/display_pack_loader.py`, `src/med_autoscience/display_pack_resolver.py`, `src/med_autoscience/display_pack_lock.py`, `src/med_autoscience/display_pack_bootstrap.py`, `src/med_autoscience/display_pack_runtime.py`, `src/med_autoscience/controllers/display_surface_materialization/`, `src/med_autoscience/display_layout_qc/`, `src/med_autoscience/controllers/medical_publication_surface.py`, and `src/med_autoscience/controllers/submission_minimal.py`.
- Focused test evidence read from current source: `tests/test_display_pack_contract.py`, `tests/test_display_pack_loader.py`, `tests/test_display_pack_resolver.py`, `tests/test_display_pack_runtime.py`, `tests/test_display_pack_lock.py`, `tests/test_display_pack_bootstrap.py`, `tests/test_display_pack_surface_sync.py`, `tests/test_display_pack_renderer_structure.py`, `tests/test_display_surface_materialization.py`, `tests/test_submission_minimal_display_surface.py`, and golden / contract inventories under `tests/display_*` and `tests/test_display_*`.

Fresh semantic result:

- `medical_display_arsenal.md` remains active support as the human-readable capability inventory. Its current audited inventory count is `98`; the stale intra-file reference to current total `93` was corrected to `98`. Family membership counts remain paper-question duplicated counts and are not unique template totals.
- `medical_display_template_backlog.md` remains active support for inactive candidate pool and historical backlog cleanup. It now states that it does not preserve current round execution流水、commit 指令或 absorb state; landed template truth comes from audit guide, template catalog, registry/source and focused tests. Old “本轮/上一轮 absorb” wording was normalized to current out-of-backlog state so future agents do not treat it as an active execution queue.
- `medical_display_template_catalog.md` remains the exhaustive human-readable generated matrix for registered templates, renderers, schemas and QC profiles. Its header already ties truth to `med_autoscience.display_registry` and `med_autoscience.display_schema_contract`; no catalog rewrite was needed.
- The reviewed index docs already route catalogs as inventory and preserve delivery authority boundaries. No index relocation was needed.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/delivery/medical-display/catalogs/medical_display_arsenal.md`, `docs/delivery/medical-display/catalogs/medical_display_template_backlog.md`, and `docs/delivery/medical-display/catalogs/medical_display_template_catalog.md`; role/index review of `docs/delivery/medical-display/README.md` and `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`, with live source/test evidence listed above. | `docs/delivery/medical-display/catalogs/medical_display_arsenal.md`; `docs/delivery/medical-display/catalogs/medical_display_template_backlog.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. All three catalog docs remain active support with distinct inventory/candidate roles.

Uncovered docs in this semantic area:

- Remaining long medical-display route / roadmap / provenance bodies: `medical_figure_route_cookbook.md`, `medical_display_family_roadmap.md`, and `medical_display_anchor_paper_audit.md`.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle, runtime-core-convergence, artifact/baseline/retention, standard skeleton/source-delivery index, workspace/source references, study-workflow policy block and bounded medical-display blocks.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future catalog/backlog prose that reports stale template totals, preserves “本轮 absorb / 将随本轮进入 main” as current execution state, or treats inactive candidates / historical cleanup as active blocker is stale pollution.
- Future catalog/backlog prose must not downgrade audited registry/source/schema/display-pack/QC surfaces into “not started” plan language, and must not upgrade catalog presence, candidate pool entries, generated matrix or pack refs into source readiness、publication quality、submission readiness、artifact mutation、`current_package` freshness、paper closure、domain ready or production ready.

Next tranche write scope:

- MAS paragraph-level coverage for `medical_figure_route_cookbook.md` + `medical_display_family_roadmap.md` + `medical_display_anchor_paper_audit.md`.
- Or MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 medical-display template-pack plan lifecycle tranche

本轮覆盖 MAS medical-display template-pack plan 文档生命周期。目标是把 template-pack architecture / implementation-plan 读回当前 live display-pack source、tests、contracts 和已完成迁移事实：架构文档保留为 active support design；Phase 1-2 逐步实施计划保留为 history/provenance，不能继续留在 active `plans/` 下作为当前 agent work queue、checkbox 任务包、expected-failure 流水或 commit 指令来源。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file, and the preceding medical-display delivery authority / audit-protocol coverage ledger entries.
- Reviewed medical-display docs: `docs/delivery/medical-display/plans/medical_display_template_pack_architecture.md`, `docs/history/capabilities/medical-display/medical_display_template_pack_implementation_plan_2026_04.md`, `docs/delivery/medical-display/README.md`, `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`, and `docs/history/capabilities/medical-display/README.md`.
- Machine / source surfaces: CodeGraph context for `LoadedDisplayPack`, `LoadedDisplayTemplate`, `DisplayPackManifest`, `load_display_pack_manifest`, `load_enabled_local_display_pack_records`, and `load_enabled_local_display_template_records`; source/test evidence from `src/med_autoscience/display_pack_contract.py`, `src/med_autoscience/display_pack_loader.py`, `src/med_autoscience/display_pack_resolver.py`, `src/med_autoscience/display_pack_lock.py`, `tests/test_display_pack_contract.py`, `tests/test_display_pack_loader.py`, `tests/test_display_pack_runtime.py`, and `tests/test_display_pack_lock.py`.

Fresh semantic result:

- The template-pack plan is no longer a current implementation queue. Live source already contains the package manifest contract, enabled pack/template record loader, resolver, display-pack lock payload and provenance write path; focused tests cover namespaced ids, local pack loading, runtime consumption and lock provenance.
- `medical_display_template_pack_architecture.md` remains active support because it explains the split between MAS host-platform duties and pack ecosystem duties, exact-version / repo-paper configuration intent, pack-local assets and remaining ecosystem gaps.
- The old `medical_display_template_pack_implementation_plan.md` was physically moved to `docs/history/capabilities/medical-display/medical_display_template_pack_implementation_plan_2026_04.md` and marked `history_provenance`. Its checkboxes, expected failures, code snippets, command sequences and commit instructions are historical execution provenance only.
- Active medical-display README and portfolio map now route users to template-pack architecture as current support design and to the moved file as implementation provenance, avoiding a second active work queue under `docs/delivery/medical-display/plans/`.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/delivery/medical-display/plans/medical_display_template_pack_architecture.md` and the full moved Phase 1-2 implementation plan; role/index review of `docs/delivery/medical-display/README.md`, `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`, and `docs/history/capabilities/medical-display/README.md`, with live source/test evidence listed above. | `docs/delivery/medical-display/README.md`; `docs/delivery/medical-display/portfolio/medical_display_portfolio_consolidation.md`; `docs/delivery/medical-display/plans/medical_display_template_pack_architecture.md`; `docs/history/capabilities/medical-display/README.md`; `docs/history/capabilities/medical-display/medical_display_template_pack_implementation_plan_2026_04.md`; this coverage ledger. |

Archived / tombstoned / deleted docs:

- Moved `docs/delivery/medical-display/plans/medical_display_template_pack_implementation_plan.md` to `docs/history/capabilities/medical-display/medical_display_template_pack_implementation_plan_2026_04.md`.

Uncovered docs in this semantic area:

- Remaining long medical-display inventory / catalog / provenance bodies: `medical_display_arsenal.md`, `medical_display_template_backlog.md`, `medical_display_template_catalog.md`, `medical_figure_route_cookbook.md`, `medical_display_family_roadmap.md`, and `medical_display_anchor_paper_audit.md`.
- MAS product/status/workbench, progress/domain-ref projection and source/delivery shell coverage remains open outside the already-covered Portal/projection/App-workbench, inspection-package, runtime-binding, owner-route/control-boundary, stage/knowledge, runtime-event/durable-workflow, runtime-boundary/backend/handle, runtime-core-convergence, artifact/baseline/retention, standard skeleton/source-delivery index, workspace/source references, study-workflow policy block and bounded medical-display blocks.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any active doc that links the Phase 1-2 implementation plan as current work, preserves its checkbox tasks as open execution, or tells agents to run its historical command sequence is stale pollution.
- Future template-pack prose must not downgrade live package contracts, loader/resolver/lock surfaces, namespaced template ids, generated catalog/provenance and focused tests back into “not started” plan language.
- Display pack presence, lock presence, pack source/version refs and generated catalog provenance still do not authorize source readiness, publication quality, submission readiness, artifact mutation, `current_package` freshness, delivery sync, paper closure, domain ready or production ready.

Next tranche write scope:

- MAS paragraph-level coverage for `medical_display_arsenal.md` + `medical_display_template_backlog.md` + `medical_display_template_catalog.md`, or `medical_figure_route_cookbook.md` + `medical_display_family_roadmap.md` + `medical_display_anchor_paper_audit.md`.
- Or choose the next exact OPL uncovered body from the family coverage ledger.

### 2026-05-26 MAS active-truth source-shape reconciliation tranche

本轮覆盖 MAS active truth plan 与 status 中关于 standard OPL Agent source shape、product/status/workbench/domain-handler/controller/progress shell 和 functional structure gap 的当前口径。目标是把 `docs/active/mas-ideal-state-gap-plan.md` 读回当前 machine-readable contract 与 focused tests：functional / structural gates 已关闭，剩余 work 是真实 paper-line / workspace / provider evidence tail；former wrapper 物理删除仍需要 replacement parity、MAS owner receipt 或 stable typed blocker、no-active-caller proof、focused tests 与 tombstone/provenance proof，但不能继续在 active plan 里写成 open functional / structural gap。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file.
- Machine surfaces: `contracts/functional_privatization_audit.json`, `contracts/generated_surface_handoff.json`, `contracts/test-lane-manifest.json`.
- Source / generated contract source: `src/med_autoscience/controllers/opl_unique_control_plane_boundary_parts/functional_followthrough_gaps.py`.
- Focused tests read as evidence: `tests/test_opl_standard_pack.py`, `tests/test_opl_family_contract_adoption.py`.

Fresh semantic result:

- `functional_privatization_audit` now fixes `classification_gap_count=0`, `functional_structure_gap_count=0`, `active_private_generic_residue_count=0`, `repo_local_wrapper_tail_count=0`, `source_purity_cutover_status=standard_agent_source_shape_landed`, `remaining_functional_followthrough_gate_ids=[]`, and `remaining_gap_classification=live_provider_paper_line_evidence_gates`.
- Closed functional / structural gates include `generated_surface_default_owner_cutover`, `domain_authority_refs_thinning`, `standard_agent_purity_guard`, `opl_app_workbench_drilldown`, `lifecycle_locator_retention_restore_ledger_reconciliation`, and `domain_ref_consumer_physical_thinning`.
- The active plan now treats product/status/workbench/domain-handler/controller/progress retained code as MAS domain handler target, authority function, owner receipt / typed blocker producer or refs-only projection input. It no longer preserves `workbench_domain_handler_status_cutover` or `domain_ref_consumer_thinning` as open functional / structural gaps.
- `physical_delete_authorized=false` remains true for former wrapper tails. Direct retirement remains gated by OPL generated/default parity, MAS owner receipt or stable typed blocker, no-active-caller proof, focused tests and tombstone/provenance proof; this is a delete authorization gate, not a current structure gap.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | `docs/active/mas-ideal-state-gap-plan.md` current progress, landed rows, functional / structural gap section, next-round prompt required actions, closeout gate and cannot-declare guard; `docs/status.md` functional/structure state and source-shape closeout sections; `docs/docs_portfolio_consolidation.md` product/status/workbench carry-forward lines; machine/test evidence listed above. | `docs/active/mas-ideal-state-gap-plan.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The tranche corrected stale active-truth wording in place; no retired doc or history move was needed.

Uncovered docs in this semantic area:

- MAS runtime/control/support docs not already paragraph-covered remain outside this source-shape reconciliation tranche.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future prose that puts `strict_purity_cutover_pending`, `workbench_domain_handler_status_cutover`, `domain_ref_consumer_thinning`, product/status/workbench/domain-handler/controller/progress wrapper tail, or active private generic residue back into MAS functional / structural gap tables is stale unless the machine contract regresses.
- Future prose must not use functional / structural closure to claim paper closure, publication quality, source readiness, artifact mutation authorization, `current_package` freshness, domain ready or production ready.
- Former wrapper physical deletion remains a direct-retirement candidate only after replacement parity, MAS owner receipt or stable typed blocker, no-active-caller proof, focused tests and tombstone/provenance proof.

Next tranche write scope:

- MAS runtime/control support docs under `docs/runtime/contracts/**` / `docs/runtime/control/**` not already paragraph-covered, or the next exact OPL/App uncovered body from the family coverage ledger.

### 2026-05-26 mainline reference coverage tranche

本轮覆盖 MAS `docs/references/mainline/*.md` 七份 mainline support/reference 文档。目标是把 quality/autonomy、AI-first Research OS、ARS / nature-skills pattern intake、modularity、test-lane governance 和旧 repair-priority map 读回当前 live contract/source/test/read-model 事实，确保它们只作为 support reference / dated snapshot / external learning provenance，而不承载 active execution queue、runtime truth、quality verdict、publication readiness、artifact authority、generic runtime owner、domain ready 或 production ready。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `README.md`, `docs/README.md`, `docs/references/README.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file.
- Reviewed mainline docs: `docs/references/mainline/ai_first_research_os_architecture.md`, `ars_learning_intake.md`, `nature_skills_learning_intake.md`, `mas_single_project_quality_and_autonomy_mainline.md`, `mas_modularity_assessment_2026_05_07.md`, `project_repair_priority_map.md`, `test_lane_governance_2026_05_08.md`.
- Machine / source surfaces: `src/med_autoscience/ars_learning_projection.py`, `contracts/opl-framework/family-contract-adoption.json#academic_research_skills_learning_projection`, `src/med_autoscience/stage_quality_contract.py`, `contracts/stage_control_plane.json`, `contracts/test-lane-manifest.json`, `contracts/action_catalog.json`, `src/med_autoscience/controllers/mainline_status.py`, `src/med_autoscience/controllers/module_boundary_audit.py`, and `src/med_autoscience/controllers/architecture_owner_boundary.py`.
- Structural context: CodeGraph context / explore for `build_ars_learning_projection`, `build_stage_quality_pack_contract`, `read_mainline_status`, `build_module_boundary_audit_report`, and `build_architecture_owner_boundary_report`.

Fresh semantic result:

- `ai_first_research_os_architecture.md` already reads as target/support architecture reference. It preserves MAS as medical research / quality / artifact owner and keeps Evaluation OS / Observability OS / MDS Deconstruction as target layers requiring real-paper soak and evidence.
- `ars_learning_intake.md` remains `active_support`: `build_ars_learning_projection()` and family-contract adoption prove ARS is an external pattern source only, with projection-only absorbed patterns, body-free refs, rejection-log adapter contract and no MAS truth / publication / artifact authority.
- `nature_skills_learning_intake.md` remains clean-room learning support: `stage_quality_pack_contract` exposes descriptor/ref/freshness/locator/authority fields, `publication_readiness_authority=false`, `quality_verdict_authority=false`, and extension contracts are quality-pack inputs rather than vendor dependency or quality authority.
- `mas_single_project_quality_and_autonomy_mainline.md` carried useful single-project owner truth but still used strong “当前 tranche” language. It was rewritten to mark that language as the formation-time tranche / support boundary and to route current completion判断 to the active gap plan, contracts, tests and live evidence.
- `mas_modularity_assessment_2026_05_07.md` remains useful architecture-fitness support. Its Sentrux / boundary-fitness / hub-role evidence is now explicitly dated and cannot be used as a permanent quality budget or current completion proof.
- `project_repair_priority_map.md` already states that old runtime/workspace/cutover repair priorities are superseded by the ideal-state gap plan and cannot reopen MAS-owned generic runtime, Hermes/default scheduler, MDS default backend, monorepo cutover or compatibility shim.
- `test_lane_governance_2026_05_08.md` already states its collected test counts are dated snapshots and that `contracts/test-lane-manifest.json` is the durable read model for lane intent and overlap policy.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of all seven `docs/references/mainline/*.md` files listed above; boundary review against ARS projection, family contract adoption, stage quality pack, stage control plane, test-lane manifest, mainline status, module boundary audit and architecture owner boundary surfaces. | `docs/references/mainline/mas_single_project_quality_and_autonomy_mainline.md`; `docs/references/mainline/mas_modularity_assessment_2026_05_07.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The mainline references still carry useful support/provenance roles; stale risk was corrected in place where wording could be misread as current active queue or current fitness proof.

Uncovered docs in this semantic area:

- `docs/references/mainline/*.md` is covered at paragraph level for the current inventory.
- MAS runtime/control support docs under `docs/runtime/contracts/**` / `docs/runtime/control/**` not already paragraph-covered remain open.
- MAS product/status/workbench and progress/domain-ref projection shell docs outside already-covered blocks remain open.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future mainline reference prose that adds “current tranche”, “fresh evidence”, phase checklist, collected test counts, Sentrux numbers or repair priority language without dated/support boundary is stale pollution.
- External ARS / nature-skills material must remain clean-room pattern source only; future prose must not introduce vendor dependency, runtime provider, default skill source, citation/body store, publication gate, quality verdict, submission readiness or artifact authority.
- Modularity / test-lane snapshots must not be used as current source-shape completion, production readiness, domain readiness, physical-delete authorization, permanent test budget or substitute for repo-native verification.

Next tranche write scope:

- MAS runtime/control support docs under `docs/runtime/contracts/**` / `docs/runtime/control/**` not already paragraph-covered, or MAS product/status/workbench/progress/domain-ref projection shell reconciliation outside the already-covered blocks.
- Or choose the next exact OPL/RCA/App uncovered body from the family coverage ledger.

### 2026-05-26 journal package builtins design coverage tranche

本轮覆盖 MAS `docs/runtime/designs/journal_package_builtins_upgrade_design.md`。目标是把该 runtime design support 文档从早期“待新增 controller / workflow”读法收敛到当前 live source/test 事实：`journal_requirements`、`journal_package`、publication gate 状态解析与 supervisor sync 已落地；文档继续保留为设计边界支撑，但不能重新打开已落地 checklist，也不能把 target-specific projection 写成最终投稿 ready、publication ready、quality verdict 或 artifact authority。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, this docs-governance file, and `docs/history/program/journal_package_builtins_upgrade_plan.md`.
- Runtime design doc: `docs/runtime/designs/journal_package_builtins_upgrade_design.md`.
- Source surfaces: `src/med_autoscience/journal_requirements.py`, `src/med_autoscience/controllers/journal_requirements.py`, `src/med_autoscience/controllers/journal_package.py`, `src/med_autoscience/controllers/publication_gate_parts/state_resolvers.py`, `src/med_autoscience/controllers/publication_gate_parts/report_builders.py`, `src/med_autoscience/controllers/publication_gate_parts/supervisor_and_cli.py`, `src/med_autoscience/cli.py`, and `src/med_autoscience/cli_parts/parser.py`.
- Support contracts/docs: `docs/delivery/inspection_package.md` and `docs/runtime/contracts/delivery_plane_contract_map.md` forbidden-write boundaries around journal package materialization.
- Focused test inventory read as evidence: `tests/test_journal_requirements_controller.py`, `tests/test_journal_package_controller.py`, `tests/test_publication_gate_cases/drift_and_state_cases.py`, `tests/test_publication_gate_cases/supervisor_cases.py`, `tests/test_cli_cases/public_entry_commands.py`, and `tests/test_cli_cases/domain_handler_and_submission_commands.py`.
- Structural context: CodeGraph context / explore for `resolve_journal_requirements`, `materialize_journal_package`, `resolve_journal_requirement_state`, `resolve_journal_package_state`, publication gate sync and `submission_packages/<journal_slug>`.

Fresh semantic result:

- `publication resolve-journal-requirements` and `publication materialize-journal-package` are current CLI/controller surfaces, not future design proposals.
- `journal_requirements` writes study-local durable `paper/journal_requirements/<journal_slug>/requirements.json` / `.md`; source authority still depends on official guideline URL and structured payload provenance.
- `materialize_journal_package` writes shallow `submission_packages/<journal_slug>/`, `audit/submission_manifest.json`, `audit/journal_requirements_snapshot.json`, target-confirmation metadata, formatting boundary and zip; unconfirmed targets remain `journal_targeted_projection`.
- publication gate reports `journal_requirements_status`, `journal_package_status`, missing-package blockers and can materialize a stale/missing package when requirements are resolved.
- Inspection package remains human-inspection-only and must not call journal package materialization; journal package projection also does not authorize `current_package`, publication eval, controller decisions, final submission or quality gate closure.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/designs/journal_package_builtins_upgrade_design.md`, with supporting source/test/doc evidence listed above. | `docs/runtime/designs/journal_package_builtins_upgrade_design.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The design remains active runtime support because it records current journal requirement / target-specific package boundary. The implementation plan already lives under `docs/history/program/` as provenance.

Uncovered docs in this semantic area:

- Other files under `docs/runtime/designs/**` were not paragraph-covered in this tranche.
- Remaining MAS runtime/control support docs under `docs/runtime/contracts/**` / `docs/runtime/control/**` not already covered by prior ledger entries remain open.
- MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside already-covered blocks remains open.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future prose in this design area that says journal requirements or journal package controllers are missing, still only skill/manual/study-local temporary materialization, or still a future CLI addition is stale.
- Any future prose that treats `submission_packages/<journal_slug>/`, requirements snapshot, package zip, package currentness, or publication gate missing-package sync as final journal-ready formatting, confirmed submission package, publication quality verdict, artifact mutation authorization, `current_package` freshness proof or paper closure is stale.
- Cover letter / DOCX title-page wording must stay aligned with current materializer output; if future code adds these outputs, docs should cite the source/test surface rather than revive early design suggestions.

Next tranche write scope:

- MAS paragraph-level coverage for another bounded runtime design/support group, or remaining `docs/runtime/contracts/**` / `docs/runtime/control/**` bodies not covered by prior tranches.
- Or choose the next exact OPL/RCA/App uncovered body from the family coverage ledger.

### 2026-05-26 runtime root / refs-index guard coverage tranche

本轮覆盖 MAS runtime root index 与 domain authority refs index guard。目标是把 `docs/runtime/README.md` 的 runtime docs taxonomy 和 `docs/runtime/domain_authority_refs_index_guard.md` 读回当前 live refs-only contract：MAS 可以维护 owner receipt、typed blocker、archive/provenance 和 artifact/source/status locator refs；generic persistence/runtime owner、provider queue、attempt ledger、retry/dead-letter、current control state 与 hosted autonomy 继续归 OPL。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/runtime/README.md`, `docs/runtime/domain_authority_refs_index_guard.md`, and this coverage ledger.
- Machine / source surfaces: `src/med_autoscience/runtime_protocol/domain_authority_refs_index.py`, `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`, `contracts/production_acceptance/mas-production-acceptance.json`, and product-entry / family-adoption surfaces that consume the refs index.
- Focused test inventory read as evidence: `tests/test_opl_family_persistence_adapter.py`, `tests/test_opl_standard_pack.py`, `tests/test_test_lane_governance.py`, and runtime layout / production acceptance tests that reference `domain_authority_refs_index`.

Fresh semantic result:

- `domain_authority_refs_index_contract()` declares `role=refs_only_domain_authority_receipt_index`, `owner=med-autoscience`, `generic_persistence_owner=one-person-lab`, `generic_runtime_owner=one-person-lab`, `stores_body=false`, `stores_domain_truth=false`, and `runtime_control_owner=one-person-lab`.
- `record_archive_ref`, `record_owner_route_receipt`, `record_dispatch_receipt` and `workspace_authority_refs_index_path` support body-free refs, receipts and archive/provenance indexing. They do not make MAS SQLite a generic lifecycle engine, runtime queue, provider ledger, retry/dead-letter store, or current control state owner.
- `docs/runtime/README.md` now describes `designs/` as active / landed runtime design support rather than only "not yet contract" design. This keeps the already-covered journal requirements / journal package support from being misread as an unlanded future plan while preserving source/contracts/tests/CLI-read-model as implementation truth.
- `docs/runtime/domain_authority_refs_index_guard.md` remains active support guard and now names the current machine contract/test entrances. It still does not own schema evolution, production readiness, paper truth, publication quality, artifact mutation authorization, domain ready, or generic runtime readiness.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/README.md` and `docs/runtime/domain_authority_refs_index_guard.md`, with live refs-only source/contract/test evidence listed above; portfolio placement review in this file. | `docs/runtime/README.md`; `docs/runtime/domain_authority_refs_index_guard.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The guard remains current active support; no history move or tombstone was required.

Uncovered docs in this semantic area:

- Remaining MAS runtime/control/support docs under `docs/runtime/contracts/**`, `docs/runtime/control/**`, `docs/runtime/projections/**`, `docs/runtime/display/**`, and other `docs/runtime/designs/**` bodies not already paragraph-covered by prior ledger entries remain open.
- MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside already-covered blocks remains open.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future runtime root prose that says `designs/` only contains uncontracted future plans is stale when the design has live source/test/contract support; design docs must still defer machine truth to source/contracts/tests/CLI-read-model.
- Future refs-index prose that claims MAS owns generic persistence, lifecycle, queue, provider attempt truth, retry/dead-letter, current control state, hosted autonomy, production readiness, paper truth, publication quality, artifact mutation, or `current_package` freshness through SQLite is stale pollution.
- Any active doc that reopens retired runtime lifecycle SQLite, root/quest Git lifecycle truth, MDS daemon, local scheduler, workspace-local generic service, alias/facade wrapper, or default MAS provider path from this guard must be retired or tombstoned.

Next tranche write scope:

- MAS paragraph-level coverage for the remaining `docs/runtime/contracts/**` / `docs/runtime/control/**` bodies not covered by prior ledger entries.
- Or choose the next exact OPL/RCA/App uncovered body from the family coverage ledger.

### 2026-05-26 runtime control docs currentness tranche

本轮覆盖 MAS runtime-control support docs 中关于 controller source shape、typed status surface、OPL stage-attempt handoff 与 retired private runtime modules 的当前事实。目标是把 `docs/runtime/control/controllers.md` 与 `docs/runtime/control/study_runtime_orchestration.md` 从旧 `study_runtime_router.py` / `study_runtime_execution.py` / `study_runtime_transport.py` 兼容叙述收敛到当前 split module、typed surface 和 no-resurrection tests。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/architecture.md`, `docs/status.md`, `docs/runtime/control/study_runtime_control_surface.md`, and this coverage ledger.
- Runtime control docs: `docs/runtime/control/controllers.md`, `docs/runtime/control/study_runtime_orchestration.md`, and `docs/runtime/control/study_runtime_control_surface.md`.
- Source surfaces: `src/med_autoscience/controllers/domain_status_projection.py`, `src/med_autoscience/controllers/progress_projection.py`, `src/med_autoscience/controllers/progress_projection_parts/`, `src/med_autoscience/controllers/study_runtime_types.py`, `src/med_autoscience/controllers/study_runtime_decision.py`, `src/med_autoscience/controllers/study_runtime_decision_parts/`, `src/med_autoscience/controllers/study_runtime_startup.py`, `src/med_autoscience/controllers/study_runtime_completion.py`, `src/med_autoscience/controllers/study_runtime_resolution.py`, `src/med_autoscience/controllers/study_runtime_execution_parts/`, and `src/med_autoscience/runtime_control/ports.py`.
- Machine / contract surfaces: `contracts/action_catalog.json`, `contracts/functional_privatization_audit.json`, and `contracts/test-lane-manifest.json`.
- Focused tests read as evidence: `tests/test_study_runtime_router.py`, `tests/test_study_runtime_router_topology.py`, `tests/test_study_runtime_typed_surface.py`, `tests/test_progress_projection_evidence_adoption.py`, `tests/test_opl_standard_pack.py`, `tests/product_entry_cases/action_catalog_parity_cases/provider_cases.py`, `tests/test_study_runtime_execution_control_intent_cases/`, and `tests/test_study_runtime_execution_evidence_adoption_cases/`.

Fresh semantic result:

- `study_runtime_router.py`, `study_runtime_execution.py`, and `study_runtime_transport.py` are not current importable active surfaces. Their names can appear only as retired provenance, migration input, tombstone, diagnostic explanation, or no-resurrection test context.
- Current status/projection shape is `domain_status_projection.progress_projection(...)` plus `progress_projection.py` / `progress_projection_parts/` typed status model. `study_runtime_types.py` is a lazy typed-name import shim; it is not a router re-export compatibility contract.
- `runtime_control.ports.request_opl_stage_attempt(...)` and the injected domain-health-diagnostic stage-attempt port read `progress_projection` payload and emit OPL admission / owner-handoff refs. They do not execute provider resume/relaunch, queue hydration, retry/dead-letter, current-control-state writes, or MAS-local lifecycle mutation.
- `study_runtime_execution_parts/` is the current controller authorization / owner handoff / control-intent lifecycle / receipt / work-unit evidence adoption helper family. Its internals are not a stable public contract unless upgraded into explicit spec.
- `StudyRuntimeExecutionContext` and `StudyRuntimeExecutionOutcome` are retired execution aggregates; typed-surface tests assert they remain absent from `study_runtime_types` and `domain_status_projection`.
- `docs/runtime/control/study_runtime_control_surface.md` remained aligned with current stop/pause/rerun and owner-handoff semantics; no edit was needed beyond coverage recording.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/control/controllers.md`, `docs/runtime/control/study_runtime_orchestration.md`, and `docs/runtime/control/study_runtime_control_surface.md`, with live source/contract/test evidence listed above. | `docs/runtime/control/controllers.md`; `docs/runtime/control/study_runtime_orchestration.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The retired runtime module names were corrected in place because they function here as support-doc stale wording, not as standalone documents needing a history move.

Uncovered docs in this semantic area:

- Remaining MAS runtime/control docs outside this bounded group, especially `docs/runtime/contracts/**`, `docs/runtime/projections/**`, `docs/runtime/display/**`, and remaining `docs/runtime/designs/**` bodies not already paragraph-covered by prior ledger entries.
- MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside already-covered blocks remains open.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future active prose that writes `study_runtime_router.py`, `study_runtime_execution.py`, `study_runtime_transport.py`, router helper monkeypatches, MAS-local transport helper refs, or provider backend alias as current active implementation, compatibility surface, patch target, or MAS-owned generic runtime owner is stale pollution.
- Any future typed-surface prose that exposes `StudyRuntimeExecutionContext` or `StudyRuntimeExecutionOutcome` as current stable names is stale unless the source and focused tests intentionally change.
- Any future controller prose that treats OPL stage-attempt admission, owner-route handoff, provider completion, queue completion, or current-control-state metadata as MAS study truth, publication quality verdict, artifact authority, `current_package` freshness, paper closure, domain ready, or production ready is stale.

Next tranche write scope:

- MAS paragraph-level coverage for the remaining `docs/runtime/contracts/**` bodies, or the next bounded runtime projection/display/design group not already covered.
- Or choose the next exact OPL/RCA/App uncovered body from the family coverage ledger.

### 2026-05-26 delivery plane contract full currentness tranche

本轮覆盖 MAS `docs/runtime/contracts/delivery_plane_contract_map.md` 全文。目标是把 delivery-plane contract support 读回当前 runtime/control、journal requirements / journal package、publication gate、inspection export 与 study decision record 的 live source/test 事实：delivery map 继续作为人读 contract support，不承载 runtime truth、publication quality verdict、artifact mutation authority、`current_package` freshness proof、paper closure、domain ready 或 production ready。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/runtime/contracts/delivery_plane_contract_map.md`, `docs/runtime/control/study_runtime_control_surface.md`, `docs/runtime/control/study_runtime_orchestration.md`, `docs/runtime/designs/journal_package_builtins_upgrade_design.md`, and this coverage ledger.
- Source surfaces: `src/med_autoscience/runtime_protocol/study_runtime.py`, `src/med_autoscience/runtime_protocol/study_runtime_models.py`, `src/med_autoscience/study_decision_record.py`, `src/med_autoscience/controllers/gate_authority_currentness.py`, `src/med_autoscience/controllers/publication_gate_parts/state_resolvers.py`, `src/med_autoscience/controllers/journal_package.py`, `src/med_autoscience/journal_requirements.py`, `src/med_autoscience/controllers/study_delivery_sync_parts/`, `src/med_autoscience/controllers/submission_inspection_export.py`, and `src/med_autoscience/controllers/delivery_inspector.py`.
- Focused test inventory read as evidence: `tests/test_journal_package_controller.py`, `tests/test_publication_gate_cases/supervisor_cases.py`, `tests/test_study_outer_loop_cases/runtime_resume_cases.py`, `tests/test_domain_health_diagnostic_cases/event_scan_cases.py`, `tests/test_autonomy_governance.py`, `tests/test_study_delivery_sync_cases/delivery_sync_cases.py`, `tests/test_inspection_package_contract.py`, and `tests/test_submission_inspection_export.py`.
- Structural context: CodeGraph context for delivery/artifact/runtime authority surfaces including `persist_runtime_artifacts`, `StudyRuntimeArtifacts`, `StudyDecisionRecord`, `write_runtime_escalation_record`, `write_study_decision_record`, `GateAuthorityCurrentness`, and `materialize_journal_package`.

Fresh semantic result:

- The delivery-plane map now distinguishes generic `rerun` as an unsupported executable action from explicit stopped-quest relaunch, which is supported only through `request_opl_stage_attempt_relaunch` or a direct controller entry with explicit stopped relaunch permission.
- `runtime_protocol.study_runtime.persist_runtime_artifacts(...)` is documented as writing MAS-facing `launch_report` / `runtime_binding` projections. OPL current-control-state and provider attempt ledgers remain runtime truth.
- Current delivery projection surfaces include `study_root/submission_packages/<journal_slug>/` alongside `submission_minimal/`, paper-local `journal_submissions/<publication_profile>/`, `manuscript/current_package/`, inspection packages and artifact mirrors.
- `journal_package` is documented as a controller-owned target-specific package projection with requirements snapshot and formatting boundary. Missing confirmed target, requirements/QC currentness or publication/quality authority refs keeps it at `journal_targeted_projection`; it must not be read as final journal-ready formatting, submission authorization, publication quality verdict, artifact mutation authority, `current_package` freshness proof or paper closure.
- Inspection package, publication gate and study delivery sync remain projection / guard / handoff surfaces only; they do not create a second delivery authority root.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/runtime/contracts/delivery_plane_contract_map.md`, with support reads of `docs/runtime/control/study_runtime_control_surface.md`, `docs/runtime/control/study_runtime_orchestration.md`, and `docs/runtime/designs/journal_package_builtins_upgrade_design.md`; live source/test/structural evidence listed above. | `docs/runtime/contracts/delivery_plane_contract_map.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The contract support doc is still active; stale currentness wording was corrected in place.

Uncovered docs in this semantic area:

- Remaining MAS runtime projections/display/design bodies not already paragraph-covered by prior ledger entries remain open.
- MAS product/status/workbench and progress/domain-ref projection shell reconciliation outside already-covered blocks remains open.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future delivery-plane prose that treats generic rerun as fully supported, or treats explicit stopped relaunch as generic automatic rerun, is stale.
- Future prose saying `study_runtime_execution.py` writes current runtime truth or owns `launch_report` is stale; current docs must route MAS-facing projection wording through `runtime_protocol.study_runtime.persist_runtime_artifacts(...)` and runtime truth through OPL control/provider surfaces.
- Future prose treating `submission_packages/<journal_slug>/`, `journal_package`, inspection exports or delivery sync as final journal-ready / submission-ready / publication-quality / artifact-authority / `current_package`-freshness / paper-closure proof is stale.

Next tranche write scope:

- MAS paragraph-level coverage for remaining runtime projection/display/design support docs, or MAS product/status/workbench/progress/domain-ref projection shell reconciliation. The stage-surface support owner is covered by the tranche below.
- Or choose the next exact OPL/RCA/App uncovered body from the family coverage ledger.

### 2026-05-26 stage-surface support owner currentness tranche

本轮覆盖 MAS `docs/active/stage_surface_standardization_program.md` 全文。目标是把该 active support owner 从旧“stage 统一计划 / 后续执行计划”读法收窄到当前 live stage-surface support 角色：它维护 stage card / route / prompt / skill / knowledge / closeout / review-index / memory / quality pack / workbench projection 边界与剩余 evidence tail；它不再作为 MAS production closure 总计划、按日期增长的执行流水、OPL framework closure 平行计划或 Markdown-only stage truth。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/runtime/contracts/stage_surfaces.md`, this docs-governance file, and prior stage route / stage knowledge / product-workbench / runtime projection ledger entries.
- Machine / source surfaces: `agent/stages/stage_route_contract.yaml`, `src/med_autoscience/stage_surface_contract.py`, `src/med_autoscience/stage_knowledge_contract.py`, `src/med_autoscience/stage_quality_contract.py`, `src/med_autoscience/controllers/progress_portal_parts/stage_review_parts/locator.py`, `src/med_autoscience/controllers/progress_portal_parts/stage_review_parts/materializer.py`, `src/med_autoscience/controllers/progress_portal_parts/runtime_workbench_projection.py`, `src/med_autoscience/controllers/opl_unique_control_plane_boundary_parts/generated_surface_handoff.py`, `src/med_autoscience/controllers/opl_unique_control_plane_boundary_parts/consumer_migration.py`, `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, and `contracts/test-lane-manifest.json`.
- Focused test evidence read from current source: `tests/test_stage_surface_contract.py`, `tests/test_stage_knowledge_plane.py`, `tests/test_stage_quality_contract.py`, `tests/test_stage_route_assets.py`, `tests/test_progress_portal.py`, `tests/product_entry_cases/action_catalog_parity_cases/memory_and_skeleton_cases.py`, and workbench / stage-review projection tests referenced by `contracts/test-lane-manifest.json`.
- Structural context: CodeGraph context for `build_stage_surface_contract`, stage knowledge closeout packets, stage quality pack projections, stage deliverable review locator/materializer and `mas_opl_runtime_workbench_projection`.

Fresh semantic result:

- `stage_surface_standardization_program.md` remains active support because it is the only content-level owner that ties stage surface shape, AI-first verdict wording, stage quality pack maturity, Stage Deliverable Review / Index, publication-route memory receipt scaleout and workbench projection together.
- The document now has a current date and first-screen `当前读法` guard. It explicitly states that the file is a support owner, not a production closure plan, execution log, OPL framework closure parallel plan or Markdown truth surface.
- Live machine surfaces remain aligned: `build_stage_surface_contract()` declares Markdown as generated human-reading surface, OPL as projection / dispatch / read-refs only, and MAS as domain truth / quality verdict / artifact authority / owner receipt / typed blocker owner. `stage_knowledge_contract.py` keeps stage knowledge / closeout / memory router receipts as context/router contracts that cannot authorize publication quality, submission readiness or controller decisions. `stage_quality_contract.py` keeps quality packs as descriptors / reviewer rubrics with `publication_readiness_authority=false` and `quality_verdict_authority=false`.
- Stage review and workbench projection source keeps review/index/materialized refs body-free and read-only. OPL App / workbench may consume latest review page, deliverable index, memory receipt and freshness refs; it must not write MAS truth, memory body, publication eval, controller decisions, artifact authority or `current_package`.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/active/stage_surface_standardization_program.md`, with live route / stage-surface / stage-knowledge / stage-quality / stage-review / workbench projection evidence listed above. | `docs/active/stage_surface_standardization_program.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The file remains active support with a unique stage-surface owner role; stale plan wording was narrowed in place.

Uncovered docs in this semantic area:

- MAS product/status/workbench/progress/domain-ref shell docs outside prior Portal/projection/App-workbench, integration, inspection-package, runtime projection/control and this stage-surface owner tranche remain open only where the cumulative ledger has not already marked them paragraph-covered.
- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future stage-surface prose that treats this file as MAS production closure plan, OPL framework closure owner, execution diary, commit checklist, generated `stage_surfaces.md` truth source or proof ledger is stale pollution.
- Future prose must not treat stage card, generated Markdown, quality pack descriptor, stage review page, deliverable index, publication-route memory refs, workbench projection, provider completion, queue completion or product-entry descriptor as source readiness, publication quality verdict, submission readiness, artifact mutation authorization, `current_package` freshness, paper closure, domain ready or production ready.
- External research-harness / nature-skills patterns remain clean-room support patterns only; they must not become MAS runtime dependency, provider, default executor adapter, skill source, quality authority or artifact authority.

Next tranche write scope:

- Continue MAS repo-wide paragraph coverage from the remaining exact uncovered doc list, or choose the next OPL/RCA/MAG/App uncovered body from the family coverage ledger.
- Keep RCA/App docs delayed while their main checkouts carry unrelated dirty implementation / release changes.

### 2026-05-26 governance reference six-repo scope tranche

本轮覆盖 MAS `docs/references/governance/series-doc-governance-checklist.md` 与 `docs/references/README.md` 的 reference-governance discoverability。目标是把 MAS 的系列文档治理 checklist 从旧四仓口径校准到当前六仓 OPL series scope，并避免把 App/OMA 角色误写成 domain truth、artifact authority、owner receipt authority 或默认 runtime owner。

Live truth inputs:

- MAS core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/architecture.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/references/positioning/mas_ideal_state.md`, and this docs-governance file.
- MAS reviewed references: `docs/references/governance/series-doc-governance-checklist.md`, `docs/references/README.md`, and the prior `docs/references/integration/*.md` coverage ledger.
- MAS machine surfaces: `contracts/generated_surface_handoff.json`, `contracts/functional_privatization_audit.json`, and `contracts/production_acceptance/mas-production-acceptance.json`.
- OPL support truth: OPL current status / decisions / coverage ledger for the `OPL Framework -> One Person Lab App -> Foundry Agents` layering, plus App and OMA status/readme surfaces confirming One Person Lab App is the desktop workbench and OPL Meta Agent is the Agent Foundry / builder-test managed module.

Fresh semantic result:

- MAS governance checklist now names the current six-repo OPL series scope: `one-person-lab`, `one-person-lab-app`, `med-autoscience`, `med-autogrant`, `redcube-ai`, and `opl-meta-agent`.
- The same checklist now keeps MAS runtime wording at the current split: MAS owns runtime-facing domain authority refs, owner receipt and typed blocker; OPL/Temporal owns the default hosted autonomous runtime.
- One Person Lab App is written as App/workbench and operator projection consumer.
- OPL Meta Agent is written as Agent Foundry / new-agent builder-test managed module, not MAS/MAG/RCA domain truth, artifact authority or owner receipt authority.
- `docs/references/README.md` now links the governance reference directory so this support checklist is discoverable from the references index.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/references/governance/series-doc-governance-checklist.md`; support read of `docs/references/README.md`, MAS core/current docs, prior MAS integration-reference coverage ledger, MAS generated-surface / functional-privatization / production-acceptance contracts, and OPL/App/OMA role docs. | `docs/references/governance/series-doc-governance-checklist.md`; `docs/references/README.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. The governance checklist remains an active support reference; stale scope wording was corrected in place.

Uncovered docs in this semantic area:

- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks.
- Runtime support docs, product/status/workbench/progress/domain-ref projection shell reconciliation, and remaining display/design bodies stay under the cumulative MAS coverage ledger unless already listed in earlier tranches.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Any future MAS governance checklist wording that reverts to four-repo scope, omits One Person Lab App, or promotes OPL Meta Agent into MAS/MAG/RCA domain truth, artifact authority, owner receipt authority, default runtime owner, production-ready claim or quality verdict is stale pollution.
- Any future MAS reference wording that treats MAS runtime-facing refs or owner receipts as MAS-owned generic queue/provider/worker runtime ownership is stale; default hosted autonomous runtime remains OPL/Temporal.

Next tranche write scope:

- MAS paragraph-level coverage for remaining runtime projection/display/design support docs, or MAS product/status/workbench/progress/domain-ref projection shell reconciliation.
- Or choose the next exact OPL/RCA/App uncovered body from the family coverage ledger.

### 2026-05-26 policy governance tranche

本轮覆盖 MAS `docs/policies/**` 中尚未进入 coverage ledger 的 policy index、quality policy、runtime-governance policy、repo-ops policy、publication-route memory policy 与第一代 study workflow support。目标是把 policy 文档读回当前 MAS / OPL owner split：policy 是稳定人读规则，不是 active backlog、runtime truth、publication verdict、artifact authority、submission authorization、`current_package` freshness proof、domain ready 或 production ready 判据。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/architecture.md`, `docs/active/mas-ideal-state-gap-plan.md`, and this docs-governance file.
- Policy docs: all tracked Markdown under `docs/policies/**`, with focused reads of `docs/policies/README.md`, `docs/policies/runtime-governance/platform_operating_model.md`, `docs/policies/runtime-governance/external_runtime_dependency_gate.md`, `docs/policies/runtime-governance/mas_mds_owner_boundary_contract.md`, `docs/policies/repo-ops/mainline_integration_and_cleanup.md`, `docs/policies/repo-ops/merge_and_cutover_gates.md`, `docs/policies/repo-ops/repository_ci_preflight.md`, and `docs/policies/study-workflow/README.md`.
- Machine surfaces: `contracts/functional_privatization_audit.json`, `contracts/generated_surface_handoff.json`, `contracts/production_acceptance/mas-production-acceptance.json`, `contracts/action_catalog.json`, and `contracts/test-lane-manifest.json`.
- Stale-risk scan over policy docs for gateway / Hermes / MDS / DeepScientist / default runtime / production-ready / domain-ready / wrapper / alias / facade wording.

Fresh semantic result:

- `docs/policies/README.md` already carries the correct index role: policy docs are stable human-readable rules and must not become active backlog or runtime truth.
- Runtime-governance and repo-ops policies already keep Hermes / MedDeepScientist / DeepScientist in explicit executor/proof diagnostic, historical fixture, explicit archive import, backend audit, upstream intake, parity oracle, history/provenance or dev/CI/offline baseline roles. They do not make those surfaces the MAS default runtime owner.
- `platform_operating_model.md` had one stale active-surface phrase: "gateway / controller" was narrowed to `domain-agent entry`, controller, and generated descriptor / read-model surface so active policy wording follows the current domain-entry / OPL-hosted runtime split.
- Production acceptance and generated-surface contracts still say OPL cannot authorize MAS domain ready, publication ready, medical ready, artifact mutation, memory body, publication verdict or `current_package`; policy docs must keep those authority boundaries.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | All tracked Markdown under `docs/policies/**` at directory / role level; full or focused paragraph read of policy indexes, runtime-governance policies, repo-ops policies, quality policy group, publication-route memory policy group, study archetypes, research route bias and already-covered study workflow policies, with live contract evidence listed above. | `docs/policies/runtime-governance/platform_operating_model.md`; this coverage ledger. |

Exact reviewed policy paths not already named by prior ledger entries:

- `docs/policies/domain_memory_markdown_first_policy.md`
- `docs/policies/quality/ai_first_quality_boundary.md`
- `docs/policies/quality/ai_reviewer_calibration_corpus.md`
- `docs/policies/quality/dm002_manuscript_quality_self_evolution_20260518.md`
- `docs/policies/quality/dm003_manuscript_quality_self_evolution_20260522.md`
- `docs/policies/quality/evidence_review_contract.md`
- `docs/policies/quality/medical_manuscript_first_draft_quality.md`
- `docs/policies/quality/publication_gate_policy.md`
- `docs/policies/runtime-governance/manual_runtime_stabilization_checklist.md`
- `docs/policies/study-workflow/publication_route_memory_library.md`
- `docs/policies/study-workflow/publication_route_memory_policy.md`
- `docs/policies/study-workflow/research_route_bias_policy.md`
- `docs/policies/study-workflow/study_archetypes.md`

Archived / tombstoned / deleted docs: none. The policy docs remain active policy/support material; stale current-surface wording was corrected in place.

Uncovered docs in this semantic area:

- `docs/policies/**` is now covered at policy-directory level for current owner / purpose / state / machine-boundary and stale-runtime-owner risk. Future substantial policy-body edits still need focused paragraph review if they add new authority, route, memory, publication, artifact, runtime or App/workbench claims.
- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks and this policy tranche.
- Remaining exact uncovered clusters include large history/provenance trees, selected references, and three projection support docs already identified by the inventory-vs-ledger pass.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future policy prose that writes `gateway` as a current MAS owner surface, or treats Hermes / MDS / DeepScientist / local scheduler as default runtime owner, default diagnostic owner, production substrate, study truth, publication quality authority, artifact authority or `current_package` authority is stale pollution.
- Future repo-ops policy prose must keep merge/verification gates separate from runtime cutover, OPL provider soak, MAS owner receipts, typed blockers and real paper-line evidence; a clean docs tranche, descriptor conformance or provider completion cannot become paper closure or production ready.
- Publication-route memory and study-workflow policy docs must keep Markdown as human/Codex-readable body and keep JSON / generated workspace packs / receipts / projections as structured or refs-only surfaces. OPL may consume locators, freshness and receipt refs, not memory body or publication-route decisions.

Next tranche write scope:

- MAS paragraph-level coverage for remaining exact uncovered clusters, preferably `docs/runtime/projections/artifact_inventory_projection.md`, `docs/runtime/projections/runtime_health_kernel.md`, and `docs/runtime/projections/study_truth_kernel.md`, or a bounded `docs/references/med-deepscientist/**` / `docs/history/**` tranche.
- Keep App docs delayed until active release / GUI lanes are safe or explicitly assigned.

### 2026-05-26 active support owner coverage tranche

本轮覆盖 MAS `docs/active/` 中尚未进入 coverage ledger 的 4 个 active/support 文档。目标是确认 active 层仍只有 single Active Truth plan、内容线索引、论文自治验收、MDS provenance guard 与 canary registry guard 等唯一 owner 角色；active docs 不保存 dated proof ledger、长执行流水、OPL provider truth、App/workbench backlog 或旧 MDS/Hermes/local scheduler 复活口径。

Live truth inputs:

- Core / active docs: `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/active/current-development-lines.md`, `docs/active/program_portfolio_consolidation.md`, and this docs-governance file.
- Reviewed active docs: `docs/active/README.md`, `docs/active/ai_first_paper_autonomy_closure_program.md`, `docs/active/mas_single_project_mds_absorb_program.md`, and `docs/active/unique_control_plane_canary_registry.md`.
- Machine / source surfaces: `contracts/unique_control_plane_canary_registry.json`, `contracts/functional_privatization_audit.json`, `contracts/generated_surface_handoff.json`, `contracts/production_acceptance/mas-production-acceptance.json`, `contracts/test-lane-manifest.json`, CodeGraph context for `AutonomyGovernanceContract`, `build_autonomy_governance_contract`, `OplRuntimeRefs`, `resolve_opl_runtime_refs`, and `unique_control_plane_canary_registry`.

Fresh semantic result:

- `docs/active/README.md` already routes active reading to `mas-ideal-state-gap-plan.md` as the single Active Truth owner and keeps process proof / closeout material in history.
- `ai_first_paper_autonomy_closure_program.md` remains the paper autonomy target / acceptance owner. It needed one currentness sync: provider-hosted paper apply now records DM002 owner receipt success refs observed with scaleout still pending; this does not authorize paper closure, submission readiness, publication-ready, artifact mutation, or `current_package` freshness.
- `mas_single_project_mds_absorb_program.md` remains landed foundation support for MDS provenance, archive/import, backend audit, upstream learning and parity oracle. It does not reopen MDS default backend, MDS WebUI, MDS daemon, workspace-local service or Git runtime lifecycle.
- `unique_control_plane_canary_registry.md` matches live registry contract: OPL is canonical control-plane owner; MAS owns study truth, quality verdict, artifact authority, owner route facts and owner receipt authority. The registry only produces executable regression / work-order素材 and forbids patching owner-route / materializer / dispatch surfaces from Agent Lab work orders.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/active/README.md`, `docs/active/ai_first_paper_autonomy_closure_program.md`, `docs/active/mas_single_project_mds_absorb_program.md`, and `docs/active/unique_control_plane_canary_registry.md`, with support evidence from core active docs, contracts and CodeGraph surfaces listed above. | `docs/active/ai_first_paper_autonomy_closure_program.md`; this coverage ledger. |

Archived / tombstoned / deleted docs: none. All four active/support docs retain unique roles; stale currentness wording was corrected in place.

Uncovered docs in this semantic area:

- `docs/active/` currently has no exact uncovered paths in the inventory-vs-ledger check after this tranche.
- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks and this active-support tranche.
- Remaining exact uncovered clusters are mostly `docs/history/**`, `docs/references/med-deepscientist/**`, selected `docs/references/mainline/**`, selected integration / MDS parity references, `docs/public/README.md`, and `docs/specs/README.md`.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future active docs that add dated proof ledgers, attempt ids, branch names, command traces or closeout chronology should be folded into `docs/history/**`, runtime ledgers, real workspace receipts or the coverage ledger rather than active owner docs.
- Future paper-autonomy prose must not upgrade DM002 owner receipt refs, OPL provider completion, queue completion, repo tests or provider attempt completion into paper closure, publication-ready, artifact mutation authorization, submission readiness or `current_package` freshness.
- Future MDS / DeepScientist / Hermes wording in active docs must stay in provenance, archive/import, backend audit, upstream learning, parity oracle, explicit executor/proof, or history roles; it must not return as default runtime owner, diagnostic owner, quality owner, artifact authority or hidden runnable substitute.
- Future canary-registry prose must keep Agent Lab output bounded to executable regression/work order素材 and no-forbidden-write proof; it must not authorize MAS study truth writes, quality verdicts or direct patching of forbidden owner-route/materializer/dispatch refs.

Next tranche write scope:

- MAS exact uncovered history/reference clusters, preferably `docs/references/med-deepscientist/**` or a bounded history index tranche.
- Keep App docs delayed until active release / GUI lanes are safe or explicitly assigned.

### 2026-05-26 MedDeepScientist reference coverage tranche

本轮覆盖 MAS `docs/references/med-deepscientist/**` 中尚未进入 coverage ledger 的 8 份 support-reference 文档。目标是把 MDS / DeepScientist 学习、解构、upstream intake、source provenance 与 legacy fork intake 语义读回当前 MAS / OPL owner split：MDS 只能作为 historical source archive、parity fixture、explicit legacy diagnostic、backend audit、source provenance、upstream intake 或 parity oracle reference；它不是默认 runtime owner、默认 diagnostic owner、quality authority、publication readiness surface、artifact authority、`current_package` freshness proof 或 hosted packaging surface。

Live truth inputs:

- MAS `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/architecture.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/active/program_portfolio_consolidation.md`, and this docs-governance file.
- MAS med-deepscientist reference docs: `docs/references/med-deepscientist/README.md`, `docs/references/med-deepscientist/deepscientist_continuous_learning_policy.md`, `docs/references/med-deepscientist/deepscientist_latest_update_learning_protocol.md`, `docs/references/med-deepscientist/med_deepscientist_continuous_learning_plan.md`, `docs/references/med-deepscientist/med_deepscientist_deconstruction_map.md`, `docs/references/med-deepscientist/med_deepscientist_method_learning_disciplines.md`, `docs/references/med-deepscientist/med_deepscientist_upstream_source_provenance.md`, and `docs/references/med-deepscientist/upstream_intake.md`.
- Machine / source surfaces: `src/med_autoscience/med_deepscientist_repo_manifest.py`, `src/med_autoscience/controllers/backend_audit.py`, `contracts/functional_privatization_audit.json`, and `contracts/test-lane-manifest.json`.
- Stale-risk scan over the reference cluster for default backend/runtime, WebUI/daemon, quality/publication/artifact authority, `current_package`, gateway/provider/Hermes and hosted packaging wording.

Fresh semantic result:

- The reference index already keeps this family in support-reference scope and points current execution queue to `docs/active/program_portfolio_consolidation.md`; it does not create a second active board.
- The learning policy/protocol now routes normal "learn DeepScientist latest update" work directly through MAS-owned upstream audit, decision matrix, worktree landing, verification and absorb-back flow. External `med-deepscientist` checkout is only touched for explicit legacy fork maintenance, backend audit, source archive or parity fixture refresh.
- `med_deepscientist_deconstruction_map.md`, method-learning disciplines and continuous-learning plan keep MDS in frozen source / fixture / legacy diagnostic / provenance roles. They route new quality/autonomy/operator work to MAS and keep generic provider/runtime ownership in OPL.
- `upstream_intake.md` is scoped as explicit legacy fork intake reference; it does not make `med-deepscientist/main` the default learning target or MAS default runtime path.
- `med_deepscientist_repo_manifest.py` exposes `truth_authority_role=event_source_only`, allows only event/source/runtime-health observations, and forbids MDS authority surfaces such as `canonical_next_action`, `publication_gate_state`, `package_state`, `delivery_state`, `runtime_health_epoch`, `canonical_runtime_action`, `worker_liveness_state`, and `allowed_controller_actions`.
- `backend_audit.py` keeps external runtime optional (`EXTERNAL_RUNTIME_OPTIONAL=true`) and returns `default_operation_blocked=false` when the controlled backend repo is unconfigured, so unavailable legacy backend audit cannot block default MAS operation.
- `contracts/functional_privatization_audit.json` continues to say generic runtime has been removed from MAS, OPL replacement exists, production long-run soak is not complete, MAS cannot claim generic runtime owner, and OPL cannot authorize quality/export or write domain truth.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of the 8 tracked Markdown files under `docs/references/med-deepscientist/**`, with support evidence from MAS core/current docs, MDS manifest inspection source, backend-audit source, functional privatization contract and test-lane manifest listed above. | this coverage ledger |

Exact MAS med-deepscientist reference paths newly recorded by this tranche: `docs/references/med-deepscientist/README.md`; `docs/references/med-deepscientist/deepscientist_continuous_learning_policy.md`; `docs/references/med-deepscientist/deepscientist_latest_update_learning_protocol.md`; `docs/references/med-deepscientist/med_deepscientist_continuous_learning_plan.md`; `docs/references/med-deepscientist/med_deepscientist_deconstruction_map.md`; `docs/references/med-deepscientist/med_deepscientist_method_learning_disciplines.md`; `docs/references/med-deepscientist/med_deepscientist_upstream_source_provenance.md`; `docs/references/med-deepscientist/upstream_intake.md`.

Archived / tombstoned / deleted docs: none. The cluster remains useful support/reference material with a consistent owner/purpose/state/machine-boundary shape.

Uncovered docs:

- `docs/references/med-deepscientist/**` now has no exact uncovered Markdown path in the inventory-vs-ledger check after this tranche.
- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks and this reference tranche. Remaining exact uncovered clusters are mostly `docs/history/**`, selected `docs/references/mainline/**`, selected integration / MDS parity references, `docs/public/README.md`, and `docs/specs/README.md`.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger.

Remaining stale / retire candidates:

- Future MDS / DeepScientist reference prose that treats MDS as default runtime owner, default backend, default diagnostic owner, WebUI/daemon surface, quality/publication authority, artifact authority, `current_package` authority, hosted package surface or hidden runnable substitute is stale pollution.
- Future upstream-learning prose must keep provider/UI/marketing changes out of MAS owner truth unless a MAS-owned contract/template/code slice and verification target are explicitly defined.
- Legacy fork intake stays explicit-only; ordinary DeepScientist learning must keep landing and verification in `med-autoscience/main`, not external `med-deepscientist/main`.

Next tranche write scope:

- MAS exact uncovered history/reference clusters, preferably bounded `docs/history/**` index/provenance groups or remaining selected `docs/references/mainline/**`, `docs/references/integration/**`, `docs/references/mds-parity/**`, `docs/public/README.md`, and `docs/specs/README.md`.
- Keep App docs delayed until active release / GUI lanes are safe or explicitly assigned.

### 2026-05-26 MDS parity runtime-drift coverage tranche

本轮覆盖 MAS `docs/references/mds-parity/**` 中仍未进入 coverage ledger 的 3 份 support-reference 文档，并顺手修正同一 cluster 内已覆盖但已被当前机器事实 supersede 的 behavior-equivalence prose。目标是把 MDS WebUI / Live Console / terminal attach parity 口径读回当前 MAS / OPL owner split：MAS 只保留 Progress Portal payload、per-study static page、route-decision read-only projection、source/artifact refs、owner receipt 和 typed blocker refs；MAS private Live Console、conversation/session read model、terminal attach gate 和 Portal local action endpoint 已物理退役；运行对话、terminal/log/provider drilldown 和未来 attach/control 必须来自 OPL `current_control_state` 或 provider attempt projection。

Live truth inputs:

- MAS `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, `docs/active/opl_app_mas_runtime_workbench_program.md`, and this docs-governance file.
- MAS mds-parity docs: `docs/references/mds-parity/mds_capability_parity_matrix.md`, `docs/references/mds-parity/mds_webui_cleanroom_behavior_spec.md`, `docs/references/mds-parity/mds_webui_user_parity_gap_review.md`, plus supporting read of `docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md`.
- Machine / source / test surfaces: `src/med_autoscience/controllers/mds_capability_parity.py`, `src/med_autoscience/controllers/mds_capability_parity_parts/behavior_equivalence.py`, `src/med_autoscience/controllers/progress_portal_parts/workspace_carrier.py`, `contracts/functional_privatization_audit.json`, `contracts/test-lane-manifest.json`, `tests/test_mds_capability_parity.py`, `tests/test_progress_portal.py`, `tests/progress_portal_cases/test_materialized_surfaces.py`, `tests/test_mas_mds_absorb_governance.py`, and `tests/test_mds_truth_boundary.py`.

Fresh semantic result:

- `mds_capability_parity_matrix.md` now reflects current machine truth: `runtime_core_daemon` is `retired_mas_runtime_surface`; `worker_runner_lifecycle` is read as MAS domain authority refs / owner receipt / typed blocker consumer; generic queue, attempt continuation, provider lifecycle, worker liveness, terminal/log/provider drilldown and future attach/control belong to OPL `current_control_state` / provider attempt projection.
- `mds_webui_user_parity_gap_review.md` no longer claims `landed_mas_native_terminal_attach_mvp`, MAS terminal attach owner gate, MAS runtime owner apply, or MAS private Live Console as current landed surface. It now states that MAS Progress Portal owns paper/domain progress while runtime drilldown joins through OPL.
- `mds_webui_cleanroom_behavior_spec.md` now describes MAS Progress Portal + OPL runtime drilldown clean-room behavior, not a MAS Live Console implementation spec. MAS-owned projection topics are progress/domain topics; terminal/log/provider/attach/control topics are OPL runtime-owner topics.
- `mds_behavior_equivalence_gap_matrix.md` was corrected as supporting stale prose so its human reference agrees with `build_mds_behavior_equivalence_matrix()` and focused tests: private runtime console, terminal attach gate, authorized Portal actions and terminal attach are retired/no-alias or OPL-owned; MAS Portal does not expose runtime control or terminal command files.
- Current tests/source already fixed the hard machine boundary: `tests/test_mds_capability_parity.py` asserts `mas_private_runtime_console=retired_physical_no_alias_surface`, `websocket_terminal_attach=not_exposed_by_mas`, `terminal_attach_gate=retired_physical_no_alias_surface`, `terminal_attach_owner=one-person-lab`, and `authorized_portal_actions=not_supported_by_mas_portal`; `tests/test_progress_portal.py` keeps the Portal free of private Live Console links; materialized Progress Portal writes only read-model/static HTML artifacts with `active_callers=[]`.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/references/mds-parity/mds_capability_parity_matrix.md`, `docs/references/mds-parity/mds_webui_cleanroom_behavior_spec.md`, and `docs/references/mds-parity/mds_webui_user_parity_gap_review.md`; focused support correction of `docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md`, with live source/contract/test evidence listed above. | `docs/references/mds-parity/mds_capability_parity_matrix.md`; `docs/references/mds-parity/mds_webui_cleanroom_behavior_spec.md`; `docs/references/mds-parity/mds_webui_user_parity_gap_review.md`; `docs/references/mds-parity/mds_behavior_equivalence_gap_matrix.md`; this coverage ledger. |

Exact MAS mds-parity reference paths newly recorded by this tranche: `docs/references/mds-parity/mds_capability_parity_matrix.md`; `docs/references/mds-parity/mds_webui_cleanroom_behavior_spec.md`; `docs/references/mds-parity/mds_webui_user_parity_gap_review.md`.

Archived / tombstoned / deleted docs:

- none. The cluster remains support-reference material; stale current-surface wording was corrected in place rather than archived because the behavior / UX oracle remains useful.

Uncovered docs:

- `docs/references/mds-parity/**` now has no exact uncovered Markdown path in the inventory-vs-ledger check after this tranche.
- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks and this mds-parity tranche. Remaining exact uncovered clusters are `docs/history/program`, `docs/history/superpowers/plans`, `docs/history/superpowers/specs`, `docs/history/runtime`, `docs/history/positioning`, `docs/history/capabilities/medical-display`, selected `docs/references/mainline/**`, selected `docs/references/integration/**`, `docs/history/omx`, `docs/history/README.md`, `docs/history/capabilities/README.md`, and `docs/history/superpowers/README.md`.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger; App full-doc coverage remains delayed while active release / GUI lanes are dirty or externally owned.

Remaining stale / retire candidates:

- Future mds-parity prose that claims MAS private Live Console, MAS conversation/session read model, terminal attach owner gate, Portal `--serve --enable-actions`, MAS runtime owner apply, terminal command queue, or local HTTP action endpoint is current landed capability is stale pollution.
- Future WebUI parity prose must keep old MDS WebUI / daemon as clean-room UX oracle and historical fixture, not source import, default runtime owner, diagnostic owner, quality/publication authority, artifact authority, terminal owner, or hidden runnable substitute.
- Runtime drilldown, terminal/log/provider refs and attach/control belong to OPL `current_control_state` / provider attempt projection; MAS may expose domain refs, owner receipts, typed blockers and handoff links only.

Next tranche write scope:

- Continue MAS exact uncovered history/reference inventory, preferably a bounded `docs/references/mainline/**` / `docs/references/integration/**` tranche or `docs/history/**` index/provenance group.
- Keep App docs delayed until active release / GUI lanes are safe or explicitly assigned.

### 2026-05-27 mainline / integration exact-path reconcile tranche

本轮重新覆盖 MAS `docs/references/mainline/**` 与 `docs/references/integration/**` 中仍被 exact inventory 标为未覆盖的 7 份 support-reference 文档，并修正同一 integration cluster 中 product-entry handoff 参考的当前 CLI / generated-shell 口径漂移。目标是把已有段落级覆盖转成可由 inventory 精确核对的路径记录，同时确保这些 reference 不承载 active execution queue、current CLI truth、runtime owner、domain ready、production ready、quality verdict、publication readiness、artifact authority 或 `current_package` freshness proof。

Live truth inputs:

- MAS `AGENTS.md`, `TASTE.md`, `docs/status.md`, `docs/active/mas-ideal-state-gap-plan.md`, and this docs-governance file.
- Mainline docs: `docs/references/mainline/ars_learning_intake.md`, `docs/references/mainline/nature_skills_learning_intake.md`, `docs/references/mainline/project_repair_priority_map.md`, and `docs/references/mainline/test_lane_governance_2026_05_08.md`.
- Integration docs: `docs/references/integration/opl-family-contract-adoption.md`, `docs/references/integration/opl-managed-runtime-three-layer-contract.md`, and `docs/references/integration/stage_led_autonomy_family_inventory.md`; supporting currentness read of `docs/references/integration/lightweight_product_entry_and_opl_handoff.md`, `codex_plugin.md`, and `progress_portal_opl_app_integration.md`.
- Machine / source / CLI surfaces: `src/med_autoscience/ars_learning_projection.py`, `src/med_autoscience/medical_material_passport.py`, `src/med_autoscience/stage_quality_contract.py`, `src/med_autoscience/domain_entry_contract.py`, `src/med_autoscience/domain_entry.py`, `src/med_autoscience/cli_public_surface.py`, `src/med_autoscience/cli_parts/parser.py`, `src/med_autoscience/cli_parts/study_action_commands.py`, `src/med_autoscience/controllers/product_entry_parts/manifest_shell_surfaces.py`, `src/med_autoscience/opl_domain_pack/family_adoption.py`, `contracts/opl-framework/family-contract-adoption.json`, `contracts/test-lane-manifest.json`, `contracts/action_catalog.json`, and `contracts/schemas/v1/product-entry-manifest.schema.json`.
- CLI/read-model probes: `PYTHONPATH=src python3 -m med_autoscience.cli domain-handler export --help`, `PYTHONPATH=src python3 -m med_autoscience.cli domain-handler dispatch --help`, and negative current-parser probes for top-level `product-entry-manifest` / `build-product-entry`.
- Structural context: CodeGraph status/context/explore for ARS projection, medical material passport, stage quality pack, family stage control plane descriptor, domain memory descriptor and domain entry command surfaces.

Fresh semantic result:

- `ars_learning_intake.md` matches live ARS projection and family adoption contract: ARS is external pattern source only; absorbed patterns expose refs / metadata / freshness / typed blockers / owner boundary and forbid memory body, evidence/review ledger body, publication verdict body and paper/package blobs.
- `nature_skills_learning_intake.md` matches live `stage_quality_pack_contract`: nature-skills patterns are clean-room quality-pack / prompt / descriptor / test inputs, with maturity and promotion evidence, not vendor dependency, runtime provider, publication authority, quality verdict authority or submission readiness surface.
- `project_repair_priority_map.md` and `test_lane_governance_2026_05_08.md` remain support/provenance references. Current execution order and gap truth stay in the MAS active plan, contracts, test-lane manifest, live source and fresh verification output.
- The three exact integration references align with current OPL/Temporal default hosted runtime, MAS-owned quality/projection/memory/domain refs, body-free memory descriptor, stage control-plane descriptor, and explicit MDS / Hermes provenance-only boundaries.
- `lightweight_product_entry_and_opl_handoff.md` had stale wording that described `product-entry-status`, `workspace-cockpit`, `product-entry-manifest`, `progress-projection` and `build-product-entry` as the current service-safe entry command set and named `medautosci product build-entry` as a current CLI. Live `SERVICE_SAFE_DOMAIN_COMMANDS` only contains `study-progress`, `launch-study`, `submit-study-task` and authority-operation commands; current parser exposes direct study commands and `domain-handler export|dispatch`, while product-entry status/workbench/manifest/build-entry are schema, manifest-shell, OPL generated/default caller or read-model refs. The doc was corrected in place.

| repo | reviewed docs/sections | edited docs |
| --- | --- | --- |
| `med-autoscience` | Full paragraph reread of the 7 exact-missing mainline / integration reference docs listed above; focused currentness correction in `docs/references/integration/lightweight_product_entry_and_opl_handoff.md`, with live source/contract/CLI/CodeGraph evidence listed above. | `docs/references/integration/lightweight_product_entry_and_opl_handoff.md`; this coverage ledger. |

Exact MAS reference paths newly recorded by this tranche: `docs/references/mainline/ars_learning_intake.md`; `docs/references/mainline/nature_skills_learning_intake.md`; `docs/references/mainline/project_repair_priority_map.md`; `docs/references/mainline/test_lane_governance_2026_05_08.md`; `docs/references/integration/opl-family-contract-adoption.md`; `docs/references/integration/opl-managed-runtime-three-layer-contract.md`; `docs/references/integration/stage_led_autonomy_family_inventory.md`.

Archived / tombstoned / deleted docs:

- none. The target documents remain support references; one stale current-surface statement was corrected in place.

Uncovered docs:

- `docs/references/mainline/**` and `docs/references/integration/**` now have no exact uncovered path in the inventory-vs-ledger check for this cluster after this tranche.
- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks and this exact-path reconcile tranche. Remaining exact uncovered clusters are history-heavy: `docs/history/program`, `docs/history/superpowers/plans`, `docs/history/superpowers/specs`, `docs/history/runtime`, `docs/history/positioning`, `docs/history/capabilities/medical-display`, `docs/history/omx`, and history directory indexes.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger; App full-doc coverage remains delayed while active release / GUI lanes are dirty or externally owned.

Remaining stale / retire candidates:

- Future product-entry / OPL handoff prose that writes retired top-level `product-entry-manifest`, top-level `build-product-entry`, or `medautosci product build-entry` as current MAS CLI truth is stale unless a live parser / generated caller proves it. Use source, schema, OPL generated shell refs and `domain-handler export|dispatch` boundaries instead of prose memory.
- Future ARS / nature / external-skill prose must stay clean-room / projection-only. External patterns cannot become runtime dependency, default skill source, publication quality authority, source body owner, artifact authority, submission readiness or `current_package` freshness proof.
- Future integration prose must keep OPL/Temporal as default hosted runtime owner and keep MDS / DeepScientist / Hermes in provenance, explicit archive/import, backend audit, upstream intake, parity oracle or explicit non-default executor/proof roles.

Next tranche write scope:

- Continue MAS exact uncovered history inventory, preferably a bounded `docs/history/**` index/provenance group.
- Keep App docs delayed until active release / GUI lanes are safe or explicitly assigned.

### 2026-05-27 OMX history no-resurrection coverage tranche

本轮覆盖 MAS `docs/history/omx/**` 这个历史/provenance cluster。目标是让 OMX-era worktree 手册保持可审计，但第一屏明确它不是当前执行入口，避免后续读者把文内 dated “当前/推荐/必须/正确用法”误读成今天的 MAS workflow。本轮不关闭全局 `/goal`，也不表示 MAS repo-wide README/docs 覆盖完成。

Live truth inputs:

- MAS `AGENTS.md`, `TASTE.md`, `docs/invariants.md`, `docs/decisions.md`, `docs/delivery/medical-display/contracts/medical_display_platform_mainline.md`, `docs/delivery/medical-display/board/medical_display_active_board.md`, and this docs-governance file.
- Target docs: `docs/history/omx/README.md` and `docs/history/omx/omx_worktree_startup_and_closeout.md`.
- Doctor preflight from `/Users/gaofeng/workspace/opl-doc-governance/scripts/opl_doc_doctor.py`, used only as structural risk map.

Fresh semantic result:

- `docs/decisions.md` already records the 2026-04-11 decision that `OMX` only remains under `docs/history/omx/` and `.omx/` is forbidden as current workflow entry.
- `docs/invariants.md` states repo-tracked contracts, durable surfaces, runtime/controller surfaces and generated artifacts are authoritative; project-level `.codex` and `.omx` are retired.
- Medical-display current docs explicitly replace project-local `.omx/.codex` state with tracked active board / contract surfaces and keep `docs/history/omx/` as audit provenance only.
- The OMX history README now carries a first-screen dated-read / no-resurrection guard.
- The long OMX worktree manual now keeps its operational details as historical provenance while explicitly warning that its “current/recommended/must” language belongs to the OMX era only.

Reviewed documents:

| Repo | Reviewed docs / sections | Edited docs this tranche |
| --- | --- | --- |
| `med-autoscience` | Full paragraph read of `docs/history/omx/README.md` and `docs/history/omx/omx_worktree_startup_and_closeout.md`; supporting current-boundary read of `docs/decisions.md`, `docs/invariants.md`, medical-display mainline contract and active board. | `docs/history/omx/README.md`; `docs/history/omx/omx_worktree_startup_and_closeout.md`; `docs/docs_portfolio_consolidation.md` |
| `one-person-lab` | OPL family ledger foldback for this MAS OMX history tranche. | `docs/active/development-document-portfolio.md` |

Exact MAS history paths newly recorded by this tranche: `docs/history/omx/README.md`; `docs/history/omx/omx_worktree_startup_and_closeout.md`.

Archived / tombstoned / deleted docs:

- none. The OMX materials remain useful audit provenance and no-resurrection guard material; stale current-workflow risk was corrected by first-screen lifecycle wording.

Unreviewed docs:

- `docs/history/omx/**` now has no exact uncovered Markdown path in this cluster after this tranche.
- MAS repo-wide `README*` and `docs/**/*.md` full paragraph coverage remains open outside prior focused MAS chunks and this OMX history tranche. Remaining exact uncovered clusters are other history-heavy groups: `docs/history/program`, `docs/history/superpowers/plans`, `docs/history/superpowers/specs`, `docs/history/runtime`, `docs/history/positioning`, `docs/history/capabilities/medical-display`, and history directory indexes.
- OPL series coverage outside MAS remains open per the OPL family coverage ledger; App full-doc coverage remains delayed while active release / GUI lanes are dirty or externally owned.

Remaining stale / retire candidates:

- Future MAS prose that treats project-level `.omx`, `.codex`, root hook scanning, tmux/session pointer files, OMX prompt/report state, or old owner worktree notes as current authoritative execution surface is stale pollution.
- Future worktree guidance must point to repo `AGENTS.md`, active docs, contracts/source/tests and OPL/Temporal owner-route surfaces, not to OMX-era local state.
- Other MAS history clusters still need bounded first-screen lifecycle/no-resurrection coverage.

Verification before absorb:

- MAS OMX history tranche worktree: `git diff --check`; strict README/docs/contracts conflict-marker scan; OPL Doc Governance doctor active truth pass / no findings.
- OPL ledger worktree: `git diff --check`; strict README/docs/contracts conflict-marker scan; OPL Doc Governance doctor active truth pass / no findings.

Next tranche write scope:

- Continue MAS exact uncovered history inventory, preferably `docs/history/program`, `docs/history/runtime`, `docs/history/positioning`, `docs/history/superpowers/**`, or `docs/history/capabilities/medical-display/**` as bounded provenance/no-resurrection groups.
- Keep App docs delayed until active release / GUI lanes are safe or explicitly assigned.
