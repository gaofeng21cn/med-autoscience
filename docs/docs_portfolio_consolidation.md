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
