# ARK Research Workflow Intake

Owner: `MedAutoScience`
Purpose: `clean_room_research_workflow_contract_intake`
State: `contract_landing_in_progress`
Machine boundary: 本文是人读 external intake 记录。机器真相继续归 `agent/` pack、`contracts/`、源码、focused tests、runtime/controller surfaces、study workspaces、owner receipts、AI reviewer / auditor records、publication gate、artifact authority 和 source authority。

Landing boundary: 本 reference 记录 ARK workflow affordance 与 MAS-native contract target；`adopt_contract` 不等于 functional landing。是否可写成 landed，按 [External Learning Adoption Closure Runbook](../../runtime/control/external_learning_adoption_closure.md) 的 landing status 判断；缺 owner surface、read-model consumer、worker/sidecar slot、callable/action catalog 或验证时必须继续标为 `contract_only_gap` / `projection_only_gap`。

本文把 `kaust-ark/ARK` 中值得学习的 idea-to-paper workflow pattern 转译为 MAS-native contract-first surface。ARK 只作为外部模式来源；MAS 不引入 ARK runtime、SQLite authority、conda project model、Telegram/webapp service、agent prompt、代码或依赖。当前外部依据是 `kaust-ark/ARK` `main` commit `01cab1048cc78fa4d33e8274e4f963a44d70dc48`、README、ARCHITECTURE、`ark/memory.py`、`ark/pipeline.py`、`ark/citation.py`、`ark/figure_manifest.py` 与 `skills/builtin/*`。

## Intake Conclusion

ARK 的价值不是“替代 MAS 研究 runtime”，而是把开放式科研写作推进整理成可操作的 workflow affordance：

- review loop 把 `compile -> review -> plan -> execute -> validate` 变成可重复推进节拍；
- goal anchor 防止多轮执行偏离研究目标；
- issue memory / repair validation 让重复问题转成下一轮 work unit；
- API-first citation 和 no-fabrication skill 把引用与结果从 LLM 自由生成中拿出来；
- figure manifest 和 page adjustment skill 把图表数据、展示布局和版面压缩分层；
- human intervention skill 把阻塞转成带后果的用户选择。

MAS 的吸收口径是：这些模式进入 MAS-owned reviewer ledger、display artifact manifest、source citation authority pack、stage-quality pack 和 operator projection。它们只能产出 refs、typed blocker、repair/source-refresh work unit、reviewer input 或 owner receipt；不能授权 publication readiness、quality verdict、source readiness verdict、artifact mutation、memory accept / reject 或 human approval。

## Adoption Map

| ARK pattern | Classification | MAS owner surface | Local target | Progress-first rule |
| --- | --- | --- | --- | --- |
| Review loop with plan / execute / validate | `adopt_contract` | Reviewer OS / Quality OS / controller projection | `reviewer_issue_progress_contract` | issue repeat generates typed repair work unit or route-back; it does not freeze all stage execution. |
| Goal Anchor reinjected into every agent call | `adopt_contract` | Study charter / Stage Knowledge OS | `goal_anchor_currentness` fields in reviewer issue contract | stale digest routes to anchor refresh or reviewer route-back; it is not a publication verdict. |
| Issue repeat tracking, repair methods, stagnation | `adopt_contract` | Reviewer OS | issue ledger required fields and repair validation refs | stagnation is advisory until a MAS hard gate is named. |
| API-first citation retrieval and verification | `adopt_contract` | Source Authority / Stage Quality OS | `source_citation_authority_pack` | missing currentness creates source-refresh work unit; critical claim/source gate can fail closed. |
| No simulated experiments / claim traceability | `adopt_contract` | Source Authority / Evidence OS | source citation pack and research-integrity quality refs | missing result/source ref blocks the claim, not unrelated agent progress. |
| Figure manifest with protected/scalable/placement | `adopt_contract` | Artifact OS / Delivery medical display | `display_artifact_manifest` | layout changes can proceed only when data/claim/statistical digests remain unchanged. |
| Page adjustment without deleting science | `adopt_template` | Delivery / Artifact OS | display manifest page-adjustment policy | page fitting creates layout work units; it cannot edit values or claim refs. |
| Human intervention skill with options | `adopt_contract` | Runtime operator projection / human gate | `ark_progress_first_learning_contract` human decision request | typed human requests are reserved for named hard gates; unrelated work continues. |
| Small synthetic project canary | `adopt_contract` | Runtime OS / Quality OS | `ark_progress_first_learning_contract` micro-study canary | plan → experiment → write → review canary failures create platform repair work units, not real-study stalls. |
| Telegram message preview harness | `adopt_template` | Operator projection / Workbench display | `ark_progress_first_learning_contract` operator preview | preview checks readability/redaction/action refs only; it has no transport or study authority. |
| Figure/table lineage spot-check | `adopt_contract` | Artifact OS / Evidence OS | `ark_progress_first_learning_contract` figure lineage QA | missing/mismatched refs create artifact-QA work units unless a named hard gate is touched. |
| No simulation / real-run closeout | `adopt_contract` | Evidence OS / owner receipt | `ark_progress_first_learning_contract` executor real-run closeout | missing resources stay blocked with command evidence; no degraded fallback or LLM substitute is accepted. |
| Compiled PDF visual region checks | `adopt_contract` | Delivery visual QA / Artifact OS | `ark_progress_first_learning_contract` compiled visual region QA | overlap, overflow or template-width failures create layout work units unless publication/artifact hard gates are touched. |
| Stagnation without meaningful delta | `adopt_contract` | Reviewer OS / paper progress delta | `ark_progress_first_learning_contract` semantic no-progress evidence | trivial deltas become reviewer issue evidence and bounded work units, not global stop rules. |
| Citation lifecycle cleanup / refresh queue | `adopt_contract` | Source Authority / Reviewer OS | `ark_progress_first_learning_contract` citation lifecycle queue | stale, unused or mismatched refs route to source-refresh/reviewer work units without blocking unrelated progress. |
| Per-project conda env and sandboxed HOME | `watch_only` | OPL runtime / workspace lifecycle | none in MAS repo | OPL owns generic environment isolation; MAS may project env blocker refs. |
| ARK SQLite DB as source of truth | `reject` | none | none | conflicts with MAS durable truth / owner receipt authority. |
| Score threshold as paper acceptance | `reject` | none | none | MAS readiness requires reviewer currentness, publication eval, source/artifact authority and human/expert gates. |
| ARK runtime / dashboard / Telegram import | `reject` | none | none | foreign runtime or product shell would blur OPL/MAS owner boundary. |

## Landed Surface Set

This intake is considered usable only when the following repo-owned surfaces and tests exist:

- `reviewer_issue_progress_contract`: MAS-owned issue ledger, goal anchor currentness, repair validation and progress-first route-back policy.
- `display_artifact_manifest`: MAS-owned medical display artifact contract with source digests, rendered artifact digests, visual QA receipts, mutation authority and page-adjustment constraints.
- `source_citation_authority_pack`: MAS stage-quality/source pack that forbids LLM-authored authoritative citation records and requires source API or human curator provenance.
- `ark_progress_first_learning_contract`: MAS-owned progress-first continuation contract covering short micro-study canary, typed human decision request, operator message preview, figure/data lineage QA, executor real-run closeout, compiled visual region QA, semantic no-progress evidence and citation lifecycle queue.
- Docs foldback: `docs/source/README.md`, `docs/references/README.md` and the active gap plan must point to the surfaces without turning this intake into current truth.

## Verification Gate

Minimum verification for this intake:

- focused tests for each new or modified contract surface;
- `rtk git diff --check`;
- `rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs contracts src tests`;
- repo-native `scripts/verify.sh` after absorbing all lanes back to `main`;
- `make test-meta` when generated machine-readable contract surfaces or test manifests are touched.

## Do Not Reintroduce

- Do not import ARK as a package or copy its source code.
- Do not create ARK-compatible runtime, project layout, SQLite owner, Telegram dependency or dashboard bridge inside MAS.
- Do not treat ARK examples, paper screenshots, README claims, scores, issue categories or stagnation heuristics as MAS authority.
- Do not let new gates block unrelated stage progress. Missing refs should become typed repair/source-refresh/artifact-qa work units unless they touch source readiness, publication gate, artifact mutation, human/expert gate or another named hard gate.
