# Research Harness Learning Intake 2026-05-11

Status: `dated recurring-lane snapshot`
Date: `2026-05-11`
Owner: `MedAutoScience`
Purpose: `external research-harness learning intake`
Machine boundary: this is a human-readable clean-room intake record. It does not create machine truth, dependencies, runtime ownership, publication authority, or artifact authority.
State: `history_provenance`

## Conclusion

`research-harness@006ab44c5926` is useful to MAS as a research-domain template source, not as a dependency or runtime owner. The useful lessons are its persistent paper pool language, source-readiness checks, numeric trace discipline, claim-evidence coverage posture, adversarial resolution artifacts, and stage-gated research workflow. These lessons should land in MAS only as MAS-owned contracts, projections, reviewer inputs, or controller-readable artifacts.

The OPL split remains fixed:

- `OPL` may learn family/control-plane language: stage descriptor, stage attempt, provider attempt, queue/handoff/receipt, projection freshness, retry/dead-letter, and human-gate transport.
- `MAS` absorbs the medical research domain template: source readiness, claim/evidence coverage, numeric trace, adversarial resolution, reviewer route-back, and paper-line quality closure.

This intake is clean-room. The source license is `PolyForm Noncommercial 1.0.0`; MAS must not copy source code, vendor the project, or depend on it for default operation.

## Source Snapshot

- Source: `Biajin-PKU/research-harness@006ab44c5926f16ce4b92968c81b00f03729cfef`
- Source commit date: `2026-05-10T00:58:06+08:00`
- License: `PolyForm Noncommercial 1.0.0`
- Source links:
  - [README](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/README.md)
  - [AGENTS.md](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/AGENTS.md)
  - [Architecture](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/docs/architecture.md)
  - [Research operating model](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/docs/research_operating_model.md)
  - [Research Harness design](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/docs/research_harness_design.md)
  - [Research primitives](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/docs/architecture/01_research_primitives.md)
  - [Execution backend](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/docs/architecture/02_execution_backend.md)
  - [Provenance system](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/docs/architecture/03_provenance.md)
  - [Orchestrator specification](https://github.com/Biajin-PKU/research-harness/blob/006ab44c5926f16ce4b92968c81b00f03729cfef/docs/architecture/06_orchestrator.md)

Local source coverage used for this intake:

- `AGENTS.md`
- `README.md`
- `LICENSE`
- `docs/architecture.md`
- `docs/research_operating_model.md`
- `docs/research_harness_design.md`
- `docs/architecture/01_research_primitives.md`
- `docs/architecture/02_execution_backend.md`
- `docs/architecture/03_provenance.md`
- `docs/architecture/06_orchestrator.md`
- `docs/v3_design/PROGRESS.md`
- `docs/roadmap.md`
- selected implementation references for concept confirmation only: `experiment/verified_registry.py`, `orchestrator/claims.py`, `orchestrator/integrity.py`, `orchestrator/adversarial.py`, `orchestrator/models.py`, `core/paper_pool.py`, `storage/db.py`, and `auto_runner/*`.

## MAS Truth Surface Binding

All adopted lessons must bind to existing MAS truth surfaces:

| MAS surface | Binding rule |
| --- | --- |
| `study_charter` | Holds the research question, claim boundary, population/outcome/timepoint scope, paper quality contract, and allowed bounded-analysis space. RH topic/direction templates can only become charter inputs. |
| `evidence_ledger` | Holds claim-to-source and result-to-claim evidence. RH claim coverage and paper pool lessons map here as evidence refs, not as a separate database. |
| `review_ledger` | Holds reviewer findings, objections, adversarial resolution notes, and repair closure. RH adversarial artifacts map here as review evidence. |
| `publication_eval/latest.json` | Holds AI reviewer-backed medical quality and publishability judgment. RH rubric, coverage, numeric trace, or adversarial resolution cannot authorize publication readiness by themselves. |
| `controller_decisions/latest.json` | Holds owner route, route-back, stop/refine/pivot decisions, and next action. RH resolution artifacts can feed this surface only through MAS controller logic. |
| `study_runtime_status` and `runtime_watch` | Hold MAS runtime/progress state. RH auto-runner/checkpoint ideas cannot replace MAS runtime truth. |
| `runtime_state` and `runtime_supervision` | Hold live run, worker, retry, supervision, and recovery facts. RH `pool.db`, dashboard, or MCP server cannot become runtime authority. |
| canonical manuscript/package surfaces | Hold artifact authority and rebuild proof. No RH code or database can patch `current_package` or bypass MAS package freshness proof. |

## Absorption Matrix

| Research Harness lesson | MAS decision | MAS mapping | Boundary |
| --- | --- | --- | --- |
| Verified number registry and numeric trace | `adopt_contract` | Add a MAS-owned numeric trace / verified-number projection that records numeric claims, source artifact refs, allowed transforms, tolerance policy, and provenance back to canonical analysis outputs and evidence ledger rows. | Do not copy RH implementation. Numeric trace is an anti-fabrication evidence surface, not AI reviewer or publication readiness authority. |
| Claim-evidence coverage projection | `adopt_contract` | Strengthen MAS claim coverage read model: orphan claims, weak evidence, contradictory evidence, missing source spans, display-to-claim gaps, and coverage density should feed `review_ledger`, `publication_eval/latest.json`, and owner route. | Coverage projection cannot directly mark a paper ready. It only supplies evidence to MAS Quality OS and AI reviewer. |
| Adversarial resolution artifact | `adopt_contract` | Represent high-risk direction, study design, route decision, and reviewer-repair disagreements as proposal snapshot, objection list, response list, unresolved counts, and resolution outcome. Store the MAS-authored result in review/controller surfaces. | No external resolver persona or RH artifact becomes the decision owner. MAS controller and AI reviewer remain authority. |
| Living paper pool and source readiness | `adopt_template` | Use paper-pool/source-readiness language to improve MAS literature readiness: source resolved, full text available, extraction quality, metadata provenance, guideline relevance, recency, and contradiction readiness. | Do not import `pool.db` as MAS truth. MAS evidence ledger and literature/workspace surfaces remain owner. |
| Stage-gated research operating model | `adopt_template` | Reuse as medical stage-language calibration for scout/idea/analysis/review/decision/write loops, especially entry/exit criteria and human checkpoint wording. | OPL consumes only family-stage descriptors. MAS owns medical stage semantics and truth. |
| Provenance-first primitive records | `adopt_contract_if_gap` | If MAS adds new paper-line projections, require source hash/ref, owner, stage, input/output refs, cost/runtime metadata when relevant, and idempotency key. | SQLite/provenance tables may index receipts only; they cannot replace evidence, review, publication, or controller files. |
| Per-stage rubrics and source-readiness scores | `adopt_template` | Use as calibration inputs for MAS Evaluation OS and AI reviewer preflight, especially for evidence coverage, counter-evidence, citation context, and reproducibility concerns. | Scores stay calibration/projection; medical quality remains AI reviewer-backed. |

## Delayed Observation

| Surface | Decision | Reason |
| --- | --- | --- |
| `auto-runner` and checkpoint loop | `watch_after_opl_temporal_soak` | This is runtime-owner territory. MAS can learn checkpoint vocabulary, but OPL provider/Temporal owns long-running family attempts, while MAS owns domain receipts and paper truth. |
| `pool.db` as unified research state | `watch_as_schema_reference` | SQLite patterns are useful for indexes and receipts. MAS must not collapse study truth, publication evaluation, controller decisions, evidence ledger, review ledger, and runtime state into an RH-style database. |
| Web dashboard/workbench | `watch_as_projection_reference` | Useful for read-only operator UX and source readiness display. MAS local Portal/Console and future OPL App workbench remain the product projection path. |
| MCP server as full research runtime | `watch_as_adapter_reference` | MCP exposure is useful, but MAS already has CLI/MCP/controller/app skill surfaces. MCP tools cannot become research or publication authority. |
| Skill pack / agent roles | `watch_as_prompt_taxonomy` | Role names may inform prompt taxonomy. MAS keeps the single MAS app skill and medical reviewer/controller roles. |

## Explicit Reject

- Reject direct dependency, vendoring, source copying, or implementation porting from `research-harness` because the source is PolyForm Noncommercial and MAS must keep a clean-room, maintainer-authored implementation path.
- Reject `pool.db` as MAS study truth, publication truth, artifact truth, or runtime truth.
- Reject any path that lets RH dashboard, MCP server, auto-runner, checkpoint, or agent role write `publication_eval/latest.json`, `controller_decisions/latest.json`, evidence ledger, review ledger, `current_package`, or artifact gate.
- Reject using RH numeric allowlists or coverage scores to bypass AI reviewer, publication gate, medical evidence hierarchy, or human-gate policy.
- Reject importing CS-paper default assumptions, venue scoring, or non-medical rubrics as medical manuscript quality authority.

## Immediate MAS Landing Shape

This snapshot does not require code changes in the current lane. The next MAS implementation lane, when opened, should use these clean-room targets:

1. `numeric_trace_projection`: a read-model or controller artifact that lists numeric manuscript claims, source artifact refs, transformations, tolerance policy, and unresolved numeric findings.
2. `claim_evidence_coverage_projection`: a review/eval input that reports orphan claims, weak evidence, contradiction flags, source-span coverage, and display-to-claim status.
3. `adversarial_resolution_artifact`: a MAS-authored artifact type for proposal/challenge/response/resolution around route decisions, study design, reviewer repair, and adverse findings.
4. `source_readiness_projection`: a literature/source readiness view that compares required evidence against available paper pool, full-text, extraction, metadata, guideline, and recency state.

All four targets must be produced from MAS-owned study/workspace inputs and must write only through MAS controller, review, evidence, publication, or read-model surfaces.

## Continued Learning Saturation Protocol

Future `research-harness` learning rounds should follow the same recurring-lane discipline as open auto research and external orchestration:

1. Pin the source commit, source date, license, and exact source-file coverage.
2. Classify every lesson as `adopt_contract`, `adopt_template`, `adopt_contract_if_gap`, `watch_only`, or `reject`.
3. Treat implementation code as non-importable unless a separate legal and architectural review explicitly allows it.
4. Promote only lessons that strengthen MAS `Quality OS`, `Evaluation OS`, `Runtime OS`, `Artifact OS`, `Observability OS`, stage-led research semantics, or operator projection.
5. Mark lessons as `saturated_by_existing_contract` when MAS already has an equivalent owner surface.
6. Stop the round when only external runtime owner, RH-specific UI/MCP mechanics, non-medical benchmark assumptions, or duplicate stage wording remains.

## MAS Landing Rule

The acceptable landing path is selective, clean-room learning: adopt research-domain contracts and templates that strengthen MAS numeric grounding, claim/evidence coverage, adversarial decision closure, and source readiness; watch runtime-owner, checkpoint, dashboard, MCP, and database patterns until OPL/MAS owner boundaries require them; reject any path that moves medical study truth, publication judgment, artifact authority, or controller decisions away from MAS.
