# Nature-skills Learning Intake

Status: `clean_room_pattern_absorbed`
Date: `2026-05-12`
Owner: `MedAutoScience Stage-Led Autonomy + Quality OS`
Purpose: 记录 nature-skills 类外部 skill/workflow 材料中可学习的论文交付模式如何以 clean-room 方式吸收进 MAS-native contracts。
State: `patterns_adopted_into_mas_owner_surfaces; no_external_dependency`
Machine boundary: 本文是人读 reference。它不新增 runtime provider、默认 skill source、publication authority、generated contract truth 或机器可读验收面。机器真相仍归 stage quality pack、AI reviewer、evidence/review ledgers、publication gate、controller decisions、Stage Deliverable Review Page / Index、Portal read model 和真实 workspace artifact locator。

## 结论

nature-skills 的价值已经按 clean-room pattern absorption 处理：MAS 只吸收可验证的论文工作模式，不复制外部 vendor 代码、prompt、目录结构、runtime 语义或 authority 边界。

吸收后的能力必须回到 MAS-native surfaces：

- stage quality pack：承载 reviewer response、data/reporting、figure/display、citation/source discipline 的 stage-level rubric。
- AI reviewer：持有医学质量、审稿意见响应质量、manuscript voice、claim restraint 和 submission-facing readiness。
- evidence ledger / review ledger：记录 claim、数据、source、reviewer concern、response action 和 closure evidence。
- publication gate：持有机械完整性、submission package freshness、source/package blocker 与 publication projection。
- controller decisions：持有 route、stop/pivot、human gate、route-back 和 next owner。
- Stage Deliverable Review Page / Index：把 stage 输出、source refs、claim impact、figure/data/citation risk、quality gate state 和 next owner 聚成论文审阅面。
- Portal read model：只读展示 stage/index/source/quality refs，不写 truth，不把 UI 状态升格为 authority。

## Adopt / Watch / Reject

| disposition | pattern | MAS absorption |
| --- | --- | --- |
| `adopt` | reviewer response patterns | 吸收到 AI reviewer workflow、review ledger、reviewer action matrix、response-letter stage review page 和 route-back controller decision。 |
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
| data / table deliverable | stage quality pack, evidence ledger, publication gate | quality pack 定义 rubric；evidence ledger 记录 claim/data refs；publication gate 只投影机械完整性与 blocker。 |
| Figure / display deliverable | display-to-claim pack, artifact locator, Stage Deliverable Review Page / Index | review page/index 展示 figure delta、claim impact 和 freshness；artifact authority 仍由 canonical artifact proof 持有。 |
| source-grounded output | evidence/review ledgers, citation refs, AI reviewer provenance checks | source refs 支撑 claim；缺 source 或 provenance 时 fail-closed 到 review_required / route_back_required。 |
| citation/export UX | Portal read model, exporter profile, publication profile | 只读展示和导出体验，不写 citation truth、publication readiness 或 package authority。 |

## Current Absorption State

当前可声明的状态是：

- reviewer response、data、figure/source-grounded deliverable patterns 已作为 MAS-native stage / quality / review / evidence / publication surface 的学习模式吸收。
- 这些模式服务 stage skill authoring、Stage Deliverable Review Page / Index、AI reviewer rubric、evidence/review ledger closure、publication gate blocker projection 和 Portal read model。
- citation HTML/export UX 仍是 watch 项；只有在未来有 MAS owner refs、export profile、Portal/Workbench read model 与 artifact locator proof 时，才可进入实现计划。

当前不得声明：

- nature-skills 是 MAS dependency、runtime provider、default skill pack、default exporter 或 publication authority。
- 外部 vendor skill 可以直接写 MAS stage truth、publication eval、controller decisions、evidence/review ledgers、current package 或 artifact authority。
- citation/export UI 已经替代 MAS source refs、citation ledger、publication profile 或 package proof。

## Expected Acceptance Evidence

最终集成 agent 可在 machine-readable contracts、test manifests、owner receipts 或 history/provenance 中补真实验证证据；本文只预留 expected commands。

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

Expected live/workspace proof when adopted patterns are exercised on a real paper line:

- Stage Deliverable Review Page / Index refs point to MAS owner receipts, evidence/review ledger refs, publication eval refs, controller decision refs and artifact locator refs.
- AI reviewer-backed `publication_eval/latest.json` carries required provenance before any submission-facing quality closure.
- Portal / Workbench renders source, figure, citation and reviewer-response refs as read-only projection.
- No external vendor runtime, default skill source or publication authority is introduced.
