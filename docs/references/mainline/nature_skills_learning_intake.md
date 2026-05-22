# Nature-skills Learning Intake

Status: `clean_room_pattern_absorbed_to_usable_surfaces`
Date: `2026-05-12`
Owner: `MedAutoScience Stage-Led Autonomy + Quality OS`
Purpose: 记录 nature-skills 类外部 skill/workflow 材料中可学习的论文交付模式如何以 clean-room 方式吸收进 MAS-native contracts，并说明当前已落地到可用的 machine surfaces、验收证据与剩余 live paper-line evidence tail。
State: `patterns_adopted_into_mas_owner_surfaces; contract_prompt_test_landed; no_external_dependency; live_paper_line_tail_pending`
Machine boundary: 本文是人读 reference。它不新增 runtime provider、默认 skill source、publication authority、generated contract truth 或机器可读验收面。机器真相仍归 stage quality pack、AI reviewer、evidence/review ledgers、publication gate、controller decisions、Stage Deliverable Review Page / Index、Portal read model 和真实 workspace artifact locator。

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

- `stage_quality_pack_contract`：`src/med_autoscience/stage_quality_contract.py` 与 product-entry projection 持有 reviewer response、data availability、citation/source discipline、figure/display 和 claim-evidence gate 的 quality pack contract。
- stage prompts / quality gate：主 stage skill / prompt surface 消费 generated stage card、stage knowledge obligations、quality pack refs、closeout packet、forbidden actions 和 AI reviewer / quality gate owner。
- product-entry / descriptor refs：`family_stage_control_plane_descriptor`、`family_stage_control_plane`、standard skeleton quality locator 与 stage deliverable index refs 暴露 stage、skill、quality、artifact locator 和 read-only OPL descriptor projection。
- tests：`tests/test_stage_quality_contract.py`、`tests/test_stage_surface_contract.py`、`tests/test_stage_route_assets.py`、`tests/product_entry_cases/action_catalog_parity_cases/stage_descriptor_cases.py`、`tests/test_citation_integrity_projection.py`、`tests/test_data_assets.py`、`tests/test_figure_renderer_contract.py`、`tests/test_publication_display_contract.py`、`tests/test_reviewer_refinement_loop.py` 和 `tests/progress_portal_cases/test_stage_review_surface.py` 保护 clean-room absorption 进入 MAS-native contract / prompt / descriptor / review surfaces。

## Adopt / Watch / Reject

| disposition | pattern | MAS absorption |
| --- | --- | --- |
| `adopt` | reviewer response patterns | 吸收到 AI reviewer workflow、review ledger、reviewer action matrix、response-letter stage review page 和 route-back controller decision。 |
| `adopt` | manuscript writing / polishing patterns | 吸收到 `manuscript_argument_pack`、AI reviewer prose review、claim-evidence boundary refs、section job map 和 review route-back；只作为 argument/prose rubric，不替代 AI medical writing judgment。 |
| `adopt` | statistical reporting patterns | 吸收到 `statistical_reporting_pack`、analysis contract、evidence ledger 与 publication profile；要求 sample size、denominator、effect size、CI、p value、missingness、calibration、external validation、sensitivity/subgroup/assumption 和 reproducibility refs。 |
| `adopt` | data deliverable patterns | 吸收到 statistical / data quality pack、evidence ledger、artifact freshness pack、Stage Deliverable Review Page 的 source refs 与 evidence/statistics 字段。 |
| `adopt` | Figure / display patterns | 吸收到 display-to-claim pack、figure quality/revision review notes、artifact locator、Stage Deliverable Index 的 manuscript/table/figure delta refs。 |
| `adopt` | source-grounded deliverable patterns | 吸收到 claim-evidence consistency、citation/source refs、publication gate blocker projection、review ledger closure 和 AI reviewer provenance checks。 |
| `watch` | citation HTML / export UX | 仅作为 Portal / Workbench / exporter UX 观察项；未来如落地，也只能消费 MAS source refs、citation ledger、artifact locator 和 publication profile，不成为 citation authority。 |
| `reject` | vendor dependency | 不新增 nature-skills 或外部 vendor 包、schema、prompt、runner、CLI 或 service 依赖。 |
| `reject` | runtime dependency/provider | 不把外部 skill runner 写成 MAS runtime provider、OPL provider、Agent executor adapter 或 default wakeup substrate。 |
| `reject` | direct publication authority | 不让外部 skill、HTML exporter、citation UI、review response template 或 figure checklist 直接授权 publication readiness、quality verdict、submission readiness 或 artifact authority。 |

## Clean-room Boundary

本 intake 的 clean-room 口径固定为：

- no vendor copy：不复制外部仓库代码、prompt 文本、目录布局、schema、runner 实现、HTML 模板或自动化脚本。
- no external runtime dependency：MAS 不依赖外部 skill runtime、vendor worker、hosted service 或 browser/export service 才能推进论文。
- no default skill source：MAS stage skill 的默认来源仍是 repo-tracked MAS app skill、stage prompt/skill surface、canonical route contract 和 owner callable tools。
- no direct authority：外部材料只能提供学习背景；最终 authority 必须由 MAS owner surfaces 产出。
- no generated truth hand edit：generated stage cards、product-entry manifest、contracts、publication eval、controller decisions、runtime status 和 workspace artifact truth 不从本文手工改写。

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
| citation/export UX | Portal read model, exporter profile, publication profile | 只读展示和导出体验，不写 citation truth、publication readiness 或 package authority。 |

## Current Absorption State

当前可声明的状态是：

- reviewer response、manuscript writing/polishing、statistical reporting、data、figure/source-grounded deliverable patterns 已作为 MAS-native stage / quality / review / evidence / publication surface 的学习模式吸收，并有 contract / prompt / descriptor / test surface 保护。
- 这些模式服务 stage skill authoring、Stage Deliverable Review Page / Index、AI reviewer rubric、evidence/review ledger closure、publication gate blocker projection 和 Portal read model；它们不依赖 nature-skills runner 才能使用。
- `stage_quality_pack_contract`、stage prompt / quality gate refs、product-entry / descriptor refs 和 focused tests 已落地为当前可用的维护面。
- citation HTML/export UX 仍是 watch 项；只有在未来有 MAS owner refs、export profile、Portal/Workbench read model 与 artifact locator proof 时，才可进入实现计划。

当前不得声明：

- nature-skills 是 MAS dependency、runtime provider、default skill pack、default exporter 或 publication authority。
- 外部 vendor skill 可以直接写 MAS stage truth、publication eval、controller decisions、evidence/review ledgers、current package 或 artifact authority。
- citation/export UI 已经替代 MAS source refs、citation ledger、publication profile 或 package proof。

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
- stage prompts / quality gate 已把 quality pack refs、durable output refs、closeout packet、gate owner 和 forbidden actions 接入主 stage skill / prompt surface；`manuscript_argument_pack` 与 `statistical_reporting_pack` 已进入写作、审阅和执行 skill 的 required refs / typed blocker 口径。
- product-entry / descriptor refs 已暴露 `family_stage_control_plane_descriptor`、`family_stage_control_plane`、stage deliverable index、standard skeleton quality locator 和 owner receipt refs，供 OPL 只读发现。
- focused tests 已覆盖 stage quality contract、stage surface contract、stage route assets、product-entry descriptor parity、citation integrity、data assets、figure renderer contract、publication display contract、reviewer refinement loop 和 stage review portal surface。
- `git diff --check` 是本 lane docs-only closeout 的必跑验证。

Remaining live paper-line evidence tail:

- Stage Deliverable Review Page / Index refs point to MAS owner receipts, evidence/review ledger refs, publication eval refs, controller decision refs and artifact locator refs.
- AI reviewer-backed `publication_eval/latest.json` carries required provenance before any submission-facing quality closure.
- Portal / Workbench renders source, figure, citation and reviewer-response refs as read-only projection.
- No external vendor runtime, default skill source or publication authority is introduced.
- A real paper-line attempt leaves `attempt id -> MAS owner receipt -> artifact delta / gate replay / reviewer update / route decision / human gate / stop-loss / typed blocker` evidence; provider completion or queue completion alone is not paper closure.
