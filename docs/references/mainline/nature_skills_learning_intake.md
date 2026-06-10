# Nature-skills Learning Intake

Status: `clean_room_pattern_absorbed_to_usable_surfaces`
Date: `2026-05-22`
Owner: `MedAutoScience Stage-Led Autonomy + Quality OS`
Purpose: 记录 nature-skills 类外部 skill/workflow 材料中可学习的论文交付模式如何以 clean-room 方式吸收进 MAS-native contracts，并说明当前已落地到可用的 machine surfaces、验收证据与剩余 live paper-line evidence tail。
State: `patterns_adopted_into_mas_owner_surfaces; contract_prompt_test_landed; no_external_dependency; live_paper_line_tail_pending`
Machine boundary: 本文是人读 reference。它不新增 runtime provider、默认 skill source、publication authority、generated contract truth 或机器可读验收面。机器真相仍归 stage quality pack、AI reviewer、evidence/review ledgers、publication gate、controller decisions、Stage Deliverable Review Page / Index、Portal read model 和真实 workspace artifact locator。

Landing boundary: 本 reference 记录 nature-skills pattern 如何进入 MAS-native quality surfaces；reference、prompt floor 或 contract 不单独等于 worker / executor landing。是否可写成 landed，按 [External Learning Adoption Closure Runbook](../../runtime/control/external_learning_adoption_closure.md) 的 owner surface、read-model、worker/sidecar、callable/action catalog、quality pack consumer 和验证门槛判断。

## 结论

nature-skills 的价值已经按 clean-room pattern absorption 处理，并已从泛泛 intake 推进到 MAS 可用面：MAS 只吸收可验证的论文工作模式，不复制外部 vendor 代码、prompt、目录结构、runtime 语义或 authority 边界。

吸收后的能力必须回到 MAS-native surfaces：

- stage quality pack：承载 reviewer response、manuscript argument/prose flow、statistical reporting、data/reporting、figure/display、citation/source discipline 的 stage-level rubric。
- AI reviewer：持有医学质量、审稿意见响应质量、manuscript voice、claim restraint 和 submission-facing readiness。
- evidence ledger / review ledger：记录 claim、数据、source、reviewer concern、response action 和 closure evidence。
- publication gate：持有机械完整性、submission package freshness、source/package blocker 与 publication projection。
- controller decisions：持有 route、stop/pivot、human gate、route-back 和 next owner。
- Stage Deliverable Review Page / Index：把 stage 输出、source refs、claim impact、figure/data/citation risk、quality gate state 和 next owner 聚成论文审阅面。
- Portal read model：只读展示 stage/index/source/quality refs，不写 truth，不把 UI 状态升格为 authority。

当前已采用的 machine surfaces 是：

- `stage_quality_pack_contract`：`src/med_autoscience/stage_quality_contract.py` 与 product-entry projection 持有 reviewer response、data availability、citation/source discipline、figure/display 和 claim-evidence gate 的 quality pack contract；每个 pack 显式声明 `maturity_status` 与 `promotion_evidence`，把 Draft / Beta / Stable 这类外部 README 状态信号吸收为 MAS contract maturity，而不是 vendor skill authority。
- `extension_contracts`：剩余值得学习的 nature-skills 模式已经作为 pack-level ref floor 落到 `journal_response_pack`、`data_availability_fair_pack`、`citation_integrity_pack`、`figure_evidence_contract_pack`、`manuscript_argument_pack`、`paper_reader_grounding_pack` 和 `paper_presentation_pack`。这些 contracts 只能要求 refs、typed blocker 或 out-of-scope reason，不能授权 publication readiness、quality verdict、submission readiness、source readiness 或 artifact authority。
- stage prompts / quality gate：主 stage skill / prompt surface 消费 generated stage card、stage knowledge obligations、quality pack refs、closeout packet、forbidden actions 和 AI reviewer / quality gate owner。
- product-entry / descriptor refs：`family_stage_control_plane_descriptor`、`family_stage_control_plane`、standard skeleton quality locator 与 stage deliverable index refs 暴露 stage、skill、quality、artifact locator 和 read-only OPL descriptor projection。
- tests：`tests/test_nature_skills_learning_contract.py`、`tests/test_stage_quality_contract.py`、`tests/test_stage_surface_contract.py`、`tests/test_stage_route_assets.py`、`tests/product_entry_cases/action_catalog_parity_cases/stage_descriptor_cases.py`、`tests/test_citation_integrity_projection.py`、`tests/test_data_assets.py`、`tests/test_figure_renderer_contract.py`、`tests/test_publication_display_contract.py`、`tests/test_reviewer_refinement_loop.py` 和 `tests/progress_portal_cases/test_stage_review_surface.py` 保护 clean-room absorption 进入 MAS-native contract / prompt / descriptor / review surfaces。

## Adopt / Watch / Reject

| disposition | pattern | MAS absorption |
| --- | --- | --- |
| `adopt` | reviewer response patterns | 吸收到 AI reviewer workflow、review ledger、reviewer action matrix、response-letter stage review page 和 route-back controller decision。 |
| `adopt` | manuscript writing / polishing patterns | 吸收到 `manuscript_argument_pack`、AI reviewer prose review、claim-evidence boundary refs、section job map 和 review route-back；只作为 argument/prose rubric，不替代 AI medical writing judgment。 |
| `adopt` | statistical reporting patterns | 吸收到 `statistical_reporting_pack`、analysis contract、evidence ledger 与 publication profile；要求 sample size、denominator、effect size、CI、p value、missingness、calibration、external validation、sensitivity/subgroup/assumption 和 reproducibility refs。 |
| `adopt` | data deliverable patterns | 吸收到 statistical / data quality pack、evidence ledger、artifact freshness pack、Stage Deliverable Review Page 的 source refs 与 evidence/statistics 字段。 |
| `adopt` | Figure / display patterns | 吸收到 display-to-claim pack、figure quality/revision review notes、artifact locator、Stage Deliverable Index 的 manuscript/table/figure delta refs。 |
| `adopt` | source-grounded deliverable patterns | 吸收到 claim-evidence consistency、citation/source refs、publication gate blocker projection、review ledger closure 和 AI reviewer provenance checks。 |
| `adopt` | academic-search source-tier discipline | 吸收到 `literature_search_source_pack`：T1/T2/T3 source tier、MeSH/biomedical query discipline、multi-source attempt refs、dedup basis 与 search `checked_at` / `expires_or_stale_after` 字段。 |
| `adopt` | citation verification discipline | 吸收到 `citation_verification_pack`：claim segment、citation ref、identifier refs、source tier、metadata match、support grade、evidence basis、checked_at、expires/stale 和 unverified blocker 字段。 |
| `adopt` | journal policy currentness discipline | 吸收到 `journal_policy_currentness_pack`：official policy refs、policy scope、checked_at、expires_or_stale_after、currentness state 和 stale/missing blocker/ref 语义。 |
| `watch` | citation HTML / export UX | 仅作为 Portal / Workbench / exporter UX 观察项；未来如落地，也只能消费 MAS source refs、citation ledger、artifact locator 和 publication profile，不成为 citation authority。 |
| `reject` | vendor dependency | 不新增 nature-skills 或外部 vendor 包、schema、prompt、runner、CLI 或 service 依赖。 |
| `reject` | runtime dependency/provider | 不把外部 skill runner 写成 MAS runtime provider、OPL provider、Agent executor adapter 或 default wakeup substrate。 |
| `reject` | direct publication authority | 不让外部 skill、HTML exporter、citation UI、review response template 或 figure checklist 直接授权 publication readiness、quality verdict、submission readiness 或 artifact authority。 |
| `reject` | search/policy refs as quality authority | 文献检索结果、source tier、MeSH 查询、citation verification report 或期刊 policy refs 只能形成 evidence/review input、typed blocker 或 reference-only record；没有 MAS AI reviewer / owner receipt / controller decision 时，不能输出 quality verdict、publication readiness 或 submission readiness。 |

## Extension Contract Closeout

2026-05-22 的追加审计把 9 个 upstream skill 的剩余可学习模式全部收敛为 MAS-native ref contracts、prompt floors、focused tests 和人读边界说明。这里的 `learned_from` 只是 clean-room provenance，不是 vendor dependency 或默认 skill source。

| upstream skill | final disposition | MAS-native landed surface |
| --- | --- | --- |
| `nature-response` | `adopt` | `reviewer_response_edge_case_contract` 要求 decision / editor instruction / stable comment id / taxonomy / action / missing author input / difficult-case / appeal-like refs；缺失时进入 `journal_response_traceability_blocker`。 |
| `nature-writing` | `adopt` | 基础 writing / statistical / reporting patterns 已进入 `manuscript_argument_pack`、`statistical_reporting_pack`、stage prompts 和 AI reviewer quality gate；写作仍由 AI executor / reviewer judgment 承接。 |
| `nature-polishing` | `adopt` | `prose_polish_claim_boundary_contract` 要求 paper type、section role、reader question sequence、writing failure mode、section architecture、evidence ladder、hedging 和 overclaim refs。 |
| `nature-data` | `adopt` | `restricted_access_fair_metadata_contract` 要求 dataset inventory、access route、restricted-access process、repository / persistent identifier、dataset citation、licence / rights / provenance / README、code/material/protocol split 和 FAIR metadata refs。 |
| `nature-citation` | `adopt` | `strict_citation_scope_and_export_contract` 要求 claim segment、source segment、claim boundary、batch strategy、accepted journal scope、identifier / dedup refs、support grade、contradictory/limiting evidence、metadata-only flag 和 ENW / RIS / Zotero RDF 等 export refs。 |
| `nature-academic-search` | `adopt` | `literature_search_source_pack` 要求 source preflight、source failure、fallback route、MeSH strategy proof、dedup result 和 id conversion refs；failed/degraded source 只能形成 typed blocker 或 explicit fallback ref。 |
| `nature-figure` | `adopt` | `figure_backend_export_qa_contract` 要求 core conclusion、evidence chain、panel map、selected backend、backend exclusivity proof、export format、editable text、source data、statistics、image integrity 和 visual QA refs。 |
| `nature-reader` | `adopt` | `full_paper_reader_source_map_contract` 要求 full-paper source map、stable text block、caption block、figure/table asset id、page/block anchor、near-first-substantive-mention 和 uncertainty / source-grounded follow-up refs。 |
| `nature-paper2ppt` | `adopt` | `pptx_asset_manifest_and_package_qa_contract` 要求 presentation logic、evidence spine、selected figure asset refs、asset manifest、embedded media、speaker notes、text overflow check 和 PPTX reopen/package QA refs。 |
| citation HTML / export UX and upstream runners | `watch/reject` | citation/export UX 只保留为未来 Portal / Workbench read-only UX watch；upstream MCP、scripts、templates、HTML browser、figure gallery、deck generator、skill status 和 runner completion 不进入 MAS runtime、authority 或 default skill source。 |

## Clean-room Boundary

本 intake 的 clean-room 口径固定为：

- no vendor copy：不复制外部仓库代码、prompt 文本、目录布局、schema、runner 实现、HTML 模板或自动化脚本。
- no external runtime dependency：MAS 不依赖外部 skill runtime、vendor worker、hosted service 或 browser/export service 才能推进论文。
- no default skill source：MAS stage skill 的默认来源仍是 repo-tracked MAS app skill、stage prompt/skill surface、canonical route contract 和 owner callable tools。
- no direct authority：外部材料只能提供学习背景；最终 authority 必须由 MAS owner surfaces 产出。
- no vendor maturity authority：nature-skills README 中 Draft / Beta / Stable skill 状态只作为可学习的 status pattern；MAS 中对应字段是 `maturity_status` / `promotion_evidence`，由 repo-tracked contract、focused tests、synthetic fixtures、real paper-line owner receipt 或 anonymized package evidence 支撑。
- no search authority：source tier、multi-source search、MeSH strategy、citation verification 和 official journal policy currentness 只约束证据输入质量；它们不授权医学质量结论。
- no generated truth hand edit：generated stage cards、product-entry manifest、contracts、publication eval、controller decisions、runtime status 和 workspace artifact truth 不从本文手工改写。

## Contract Maturity Gate

MAS 已把 status pattern 收敛为 quality pack 的 contract maturity gate：

- `maturity_status` 表达 MAS 对 pack descriptor 本身的成熟度，例如 `beta_contract` 或 `stable_contract`。
- `promotion_evidence` 表达晋级依据，包含 evidence kind、ref、role、strength 和 authority boundary。
- `stable_contract` 不能只靠文档或普通测试晋级；必须至少具备 `synthetic_fixture`、`focused_tests`、`real_paper_line_owner_receipt` 或 `anonymized_package_evidence` 之一的 strong evidence。
- nature-derived pack 即使达到 `stable_contract`，仍然保持 `publication_readiness_authority=false` 与 `quality_verdict_authority=false`；它们只是 reviewer / auditor 可消费的 explicit quality pack descriptor。
- `paper_presentation_pack` 当前保留为 `beta_contract`，因为它仍偏 human-facing projection；后续要晋级为 stable，需要同样留下强证据，而不是复用 README 状态。

## MAS Owner Boundary

adopted patterns 的 owner 映射如下：

| capability family | owner surface | authority boundary |
| --- | --- | --- |
| reviewer response | AI reviewer, review ledger, controller decisions | AI reviewer 输出审稿质量判断；controller 只记录 route/back/next owner；review ledger 记录 closure evidence。 |
| manuscript argument / prose flow | manuscript argument pack, AI reviewer, publication eval | quality pack 定义 paper-type logic、argument spine、section job map 和 claim boundary rubric；AI reviewer 持有主观论文质量 verdict。 |
| statistical reporting | statistical reporting pack, analysis contract, evidence ledger, publication profile | pack 要求 journal-facing statistical refs；analysis owner 和 AI reviewer 决定缺口是否 route back，pack 本身不授权 ready。 |
| data / table deliverable | stage quality pack, evidence ledger, publication gate | quality pack 定义 rubric；evidence ledger 记录 claim/data refs；publication gate 只投影机械完整性与 blocker。 |
| Figure / display deliverable | display-to-claim pack, artifact locator, Stage Deliverable Review Page / Index | review page/index 展示 figure delta、claim impact 和 freshness；artifact authority 仍由 canonical artifact proof 持有。 |
| source-grounded output | evidence/review ledgers, citation refs, AI reviewer provenance checks | source refs 支撑 claim；缺 source 或 provenance 时 fail-closed 到 review_required / route_back_required。 |
| literature search / citation verification | citation integrity pack, paper reader grounding pack, evidence ledger | T1/T2/T3 source tier、MeSH/keyword query、dedup 和 verification report 只形成 source refs、support grade 或 blocker；metadata-only、missing、stale 或 unverified 状态不能支撑 claim closure。 |
| journal policy currentness | journal response pack, data availability FAIR pack, citation integrity pack | official policy refs 必须有 `checked_at` 与 `expires_or_stale_after`；缺失或过期时只能形成 blocker/ref，不能升级为 publication readiness、quality verdict 或 submission readiness。 |
| citation/export UX | Portal read model, exporter profile, publication profile | 只读展示和导出体验，不写 citation truth、publication readiness 或 package authority。 |

## Current Absorption State

当前可声明的状态是：

- reviewer response、manuscript writing/polishing、statistical reporting、data、citation/search、figure、reader 和 presentation patterns 已作为 MAS-native stage / quality / review / evidence / publication surface 的学习模式吸收，并有 contract / prompt / descriptor / test surface 保护。
- 这些模式服务 stage skill authoring、Stage Deliverable Review Page / Index、AI reviewer rubric、evidence/review ledger closure、publication gate blocker projection 和 Portal read model；它们不依赖 nature-skills runner 才能使用。
- `stage_quality_pack_contract`、stage prompt / quality gate refs、product-entry / descriptor refs 和 focused tests 已落地为当前可用的维护面。
- `extension_contracts`、`literature_search_source_pack`、`journal_policy_currentness_pack` 与 `citation_verification_pack` 已落到 stage quality pack descriptor：它们固定 response/data/citation/figure/reader/presentation ref floors、source tiers、official/current policy refs、checked_at / expires_or_stale_after、citation verification output fields 与 forbidden authority。
- citation HTML/export UX 仍是 watch 项；只有在未来有 MAS owner refs、export profile、Portal/Workbench read model 与 artifact locator proof 时，才可进入实现计划。

当前不得声明：

- nature-skills 是 MAS dependency、runtime provider、default skill pack、default exporter 或 publication authority。
- 外部 vendor skill 可以直接写 MAS stage truth、publication eval、controller decisions、evidence/review ledgers、current package 或 artifact authority。
- citation/export UI 已经替代 MAS source refs、citation ledger、publication profile 或 package proof。
- Draft / Beta / Stable vendor skill 状态可以绕过 MAS contract maturity 直接决定 pack 成熟度、publication readiness、quality verdict 或 submission readiness。
- 文献检索、MeSH 查询、source tier、citation verification report 或期刊 official policy refs 本身已经授权 quality verdict、publication readiness 或 submission readiness。

## Expected Acceptance Evidence

当前文档治理验收已从 expected intake 更新为 landed evidence + remaining tail。repo-level acceptance evidence 是 machine-readable contracts、test manifests、product-entry / descriptor refs 和 stage prompt / quality gate refs；真实论文线验收仍需后续 live evidence。

Expected minimum docs-only validation:

```bash
git diff --check
```

Expected integration validation when code / generated descriptor surfaces are touched by other lanes:

```bash
scripts/verify.sh
make test-meta
pytest tests/test_stage_quality_contract.py
pytest tests/test_stage_surface_contract.py
pytest tests/test_ai_first_quality_boundary.py
pytest tests/test_publication_eval_latest.py
```

Landed repo-level acceptance evidence:

- `stage_quality_pack_contract` 已在 product-entry manifest 与 family stage control-plane descriptor 中投影，并由 stage descriptor parity tests 保护 locator、freshness、authority boundary 和 pack ids。
- `stage_quality_pack_contract` 已暴露 `extension_contracts`，覆盖 reviewer response edge-case routing、restricted Data Availability / FAIR metadata、strict citation scope / reference export、figure backend / export / visual QA、manuscript argument failure-mode、full-paper reader source map / block anchors 和 PPTX asset-manifest / package QA。
- `stage_quality_pack_contract` 已为每个 pack 投影 `maturity_status` 与 `promotion_evidence`；stable pack 的晋级证据必须来自 synthetic fixture、focused tests、real paper-line owner receipt 或 anonymized package evidence，不能只靠 docs 或普通 tests。
- stage prompts / quality gate 已把 quality pack refs、durable output refs、closeout packet、gate owner 和 forbidden actions 接入主 stage skill / prompt surface；response、manuscript argument、statistical reporting、Data Availability、citation/export、figure/table、reader 和 presentation refs 已进入写作、审阅、finalize 和 execution receipt 的 required refs / typed blocker 口径。
- product-entry / descriptor refs 已暴露 `family_stage_control_plane_descriptor`、`family_stage_control_plane`、stage deliverable index、standard skeleton quality locator 和 owner receipt refs，供 OPL 只读发现。
- focused tests 已覆盖 nature-skills extension contracts、stage quality contract、stage surface contract、stage route assets、product-entry descriptor parity、citation integrity、data assets、figure renderer contract、publication display contract、reviewer refinement loop 和 stage review portal surface。
- `git diff --check` 是本 lane docs-only closeout 的必跑验证。

Remaining live paper-line evidence tail:

- Stage Deliverable Review Page / Index refs point to MAS owner receipts, evidence/review ledger refs, publication eval refs, controller decision refs and artifact locator refs.
- AI reviewer-backed `publication_eval/latest.json` carries required provenance before any submission-facing quality closure.
- Portal / Workbench renders source, figure, citation and reviewer-response refs as read-only projection.
- No external vendor runtime, default skill source or publication authority is introduced.
- A real paper-line attempt leaves `attempt id -> MAS owner receipt -> artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker` evidence; provider completion or queue completion alone is not paper closure.
