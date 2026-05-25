# PaperOrchestra Learning Intake 2026-05-02

Owner: `MedAutoScience`
Purpose: `program_history_record`
State: `history_provenance`
Machine boundary: 人读 program/process 历史记录。当前执行顺序、gap、runtime truth 和 owner boundary 继续归 active owner docs、核心五件套、contracts、source、runtime/controller surfaces 和 owner receipts。

这份记录对应维护者触发的 PaperOrchestra 学习吸收。目标是把外部论文写作流水线中可复用的论文生产纪律转成 MAS-owned contract、projection 和 regression surface；不是引入 PaperOrchestra 作为 MAS runtime、用户入口或第二 publication owner。

## Source Snapshot

- source SHA: `Ar9av/PaperOrchestra@d5dce670e37d51011f36fa382ffe2b1870d623e0`
- source date: `2026-04-28T11:27:40Z`
- source paper: `Song et al. PaperOrchestra: A Multi-Agent Framework for Automated AI Research Paper Writing. arXiv:2604.05018v1`
- source links:
  - [PaperOrchestra README](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/README.md)
  - [PaperOrchestra architecture](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/docs/architecture.md)
  - [paper-orchestra orchestrator skill](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/paper-orchestra/SKILL.md)
  - [pipeline reference](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/paper-orchestra/references/pipeline.md)
  - [outline agent](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/outline-agent/SKILL.md)
  - [plotting agent](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/plotting-agent/SKILL.md)
  - [literature review agent](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/literature-review-agent/SKILL.md)
  - [section writing agent](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/section-writing-agent/SKILL.md)
  - [content refinement agent](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/content-refinement-agent/SKILL.md)
  - [paper autoraters](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/paper-autoraters/SKILL.md)
  - [agent research aggregator](https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/agent-research-aggregator/SKILL.md)

## Decision Matrix

| Lesson | Decision | MAS mapping | Boundary |
| --- | --- | --- | --- |
| Five-stage paper authoring DAG: outline, plotting, literature review, section writing, content refinement | `adopt_contract` | Map to MAS `pre_draft_quality_runtime`, authoring workplan projection, evidence/review ledgers, and publication eval route-back. | This does not create a PaperOrchestra runtime inside MAS. |
| Parallel plotting and literature branches | `adopt_template` | Permit independent medical literature hydration and display/artifact preparation once study direction and evidence scope are locked. | Parallel branches remain MAS controller-visible work units. |
| Structured input tuple `idea.md`, `experimental_log.md`, `template.tex`, `conference_guidelines.md`, figures | `adopt_template` | Translate to `study_charter`, `evidence_ledger`, `publication_profile`, `medical_reporting_contract`, and display-to-claim artifacts. | MAS does not adopt LaTeX-first or CS-conference-first workspace shape. |
| Deterministic helpers for schema validation, citation coverage, orphan citation, LaTeX sanity, anti-leakage, and provenance | `adopt_contract` | Add deterministic evidence/blocker projections for citation, numeric grounding, display grounding, internal-language leakage, and artifact rebuild proof. | Mechanical gates cannot authorize scientific quality or submission readiness. |
| Literature review candidate discovery, dedup, citation key sync, and citation coverage | `adopt_template` | Strengthen medical literature lane with PubMed/DOI/guideline provenance and citation hygiene. | Semantic Scholar remains optional auxiliary indexing, not medical literature authority. |
| Content refinement accept/revert loop with snapshots and worklog | `adopt_contract` | Map accept to AI reviewer-backed `publication_eval/latest.json`; map revert to same-line route-back and controller decision. | The loop cannot edit `current_package` directly or invent new evidence. |
| Paper autoraters and side-by-side quality scoring | `watch_only` | Use as Evaluation OS reference for future quality regression over MAS drafts, human revisions, and final packages. | LLM judge scores remain calibration evidence, not publication authority. |
| Agent research aggregator over coding-agent caches | `watch_only` | Reuse only the idea of structured material intake when MAS durable ledgers are incomplete. | Agent caches never replace MAS `evidence_ledger`, `review_ledger`, or study truth. |
| PaperBanana / generated illustration backbone | `watch_only` | Useful future reference for display-side visual refinement. | Display runtime remains its own MAS capability lane and is not mixed into this tranche. |
| PaperOrchestra as a user-facing paper generator skill pack | `reject` | MAS keeps its single MAS app skill, CLI, MCP, controller, and durable surfaces. | No external skill pack becomes MAS product entry. |
| PaperOrchestra pipeline as publication owner | `reject` | MAS `Quality OS` and AI reviewer workflow remain the authority for medical manuscript quality and publishability. | No second publication owner is introduced. |

## MAS Landing Map

| MAS layer | Adopted shape | Durable surface |
| --- | --- | --- |
| Quality OS | Pre-draft authoring workplan; section obligations; route-back before first full draft | `paper/pre_draft_writing_readiness.json`, `study_charter.paper_quality_contract`, `publication_eval/latest.json` |
| Artifact OS | Deterministic rebuild and grounding gates for manuscript, figures, tables, and package | canonical artifact contract, artifact runtime proof, display-to-claim artifacts |
| Evaluation OS | Future side-by-side regression and historical repair-toil calibration | AI reviewer calibration corpus and quality regression fixtures |
| Runtime OS | Parallel branches are visible work units with restore and handoff records | `study_runtime_status`, `runtime_watch`, `controller_decisions/latest.json` |

## Explicit Reject / Watch Record

- 不引入 PaperOrchestra 作为 MAS runtime、scheduler、controller 或 user-facing product entry。
- 不引入 CS conference LaTeX workspace 作为 MAS 默认工作区形态。
- 不把 citation coverage percentage 当成医学文献质量 authority。
- 不让 deterministic gate 替代 AI reviewer-backed `publication_eval/latest.json`。
- 不让 agent cache aggregation 替代 MAS durable evidence 或 review ledger。
- 不在本 tranche 混入 display runtime 或 PaperBanana implementation。
- `watch_only`: paper autoraters, side-by-side judges, and PaperWritingBench are useful for future Evaluation OS calibration, but they need MAS-specific medical fixtures before becoming regression gates.

## Continued Learning Saturation Protocol

后续继续学习 PaperOrchestra 或相邻论文写作项目时，执行标准与外部 orchestration intake 一致：

1. 固定 source SHA、paper version、source file coverage。
2. 将 lesson 分类为 `adopt_contract`、`adopt_template`、`watch_only` 或 `reject`。
3. 只有能改变 MAS `Quality OS`、`Artifact OS`、`Evaluation OS`、`Runtime OS`、operator projection 或 meta tests 的 lesson 才能进入 landing lane。
4. 已经由 MAS contract 覆盖的 lesson 标记为 `saturated_by_existing_contract`，不得反复新增同义文档。
5. 只剩外部 owner、CS-conference-specific mechanics、generic LaTeX packaging、non-medical benchmark labels、provider-specific plotting runtime 或重复表述时，当前 source snapshot 视为 `MAS-actionable saturated`。

本轮 source coverage 的 MAS-actionable saturation record：

| Source area | Coverage | MAS-actionable result | Saturation status |
| --- | --- | --- | --- |
| Orchestrator and pipeline references | five-stage DAG, parallel Step 2/3, halt and provenance shape | land as authoring workplan and lane split discipline | `new_contract_landing` |
| Literature review agent | discovery, pre-dedup, verification, citation key sync, coverage gate | land medical citation hygiene and literature projection discipline | `new_template_landing` |
| Section writing agent | one global writing call, table extraction, figure grounding, citation key check | land deterministic grounding gates and pre-draft inputs | `new_contract_landing` |
| Content refinement agent | reviewer loop, worklog, snapshots, accept/revert, anti-reward-hack rules | land reviewer refinement read model with AI reviewer authority | `new_contract_landing` |
| Autoraters | citation F1, lit review quality, side-by-side judges | keep as future Evaluation OS calibration reference | `watch_only` |
| Agent research aggregator | scattered-agent-log synthesis into paper inputs | watch as structured intake pattern only | `watch_only` |
| PaperOrchestra host skill pack identity | external skill directory and host-agent execution contract | no MAS owner value beyond selective lessons | `reject_saturated` |

## MAS Landing Rule

The acceptable landing path is selective learning: adopt contracts that strengthen MAS-owned pre-draft planning, deterministic evidence gates, reviewer refinement discipline, and future quality regression; adopt templates that improve medical literature and display-to-claim preparation; watch benchmark and aggregation mechanisms until MAS-specific medical evidence exists; reject any source pattern that moves authority away from MAS study truth, publication judgment, artifact authority, or controller decisions.
