# Research Trajectory And Medical Narrative

Owner: MedAutoScience
Contract: `contracts/research_trajectory_contract.json`
Event schema: `contracts/schemas/v2/mas-research-trajectory-event.schema.json`
Snapshot schema: `contracts/schemas/v2/mas-research-trajectory-snapshot.schema.json`
Narrative schema: `contracts/schemas/v2/mas-medical-narrative.schema.json`

## Purpose

Maintain a durable account of how the study question, principal hypothesis,
validation strategy, evidence interpretation, and research route evolve. The
human-readable document and map are for clinicians, professors, and biomedical
researchers. They must read like a concise medical paper or research conference
summary, not an execution log.

## Scientific Separation

Always record these three dimensions independently:

1. **Execution outcome**: whether the planned validation was run, completed,
   failed, cancelled, or not run.
2. **Evidence interpretation**: whether the result supports the current
   hypothesis, does not support it, remains inconclusive, or cannot be
   interpreted because the current design is inadequate.
3. **Route decision**: whether to continue validation, refine or narrow the
   question, pivot, stop, or request researcher judgment.

A script, environment, data-access, or other execution failure is not evidence
against a scientific hypothesis. In that case, record the execution outcome and
leave the evidence interpretation as `not_assessed` unless interpretable evidence
was actually produced. Negative and null findings are evidence and must not be
discarded. A null estimate may be classified as not supporting the current
hypothesis, inconclusive, or design-invalid only from the actual design,
uncertainty, sensitivity analyses, and evidence refs.

## Semantic Checkpoints

Emit a `research_trajectory_delta_ref` when a Stage produces at least one of the
following scientific deltas:

- proposes, selects, refines, supersedes, or retires a principal hypothesis;
- plans or materially changes a validation method, analysis, comparator,
  endpoint, cohort, evidence boundary, or stopping rule;
- observes a positive, negative, null, mixed, failed, or methodologically
  uninterpretable result;
- interprets evidence as supportive, non-supportive, inconclusive, or
  design-invalid;
- decides to continue, refine, narrow, pivot, stop, or request researcher
  judgment;
- produces an artifact that materially changes the accepted scientific story or
  publication route.

Return `research_trajectory_delta_ref: null` when the Stage only performs
mechanical packaging, formatting, transport, retry, or other work that does not
change those scientific semantics. Do not manufacture an event merely to show
activity.

## Acceptance And Storage

The Stage output is a structured candidate. Keep it in the Stage artifact or
closeout packet until an exact MAS owner receipt or decisive independent reviewer
receipt accepts it. A candidate, provider completion, readable file, test pass,
ranking, or generated projection is not accepted study truth.

Candidate provenance may leave the StageRun and Attempt refs null. Before an
event is accepted, copy `stage_id`, `stage_run_ref`, and `attempt_ref` exactly
from the host-injected trusted decisive Stage context. Never construct, infer,
normalize, or repair these refs inside MAS; OPL Framework owns their locator
format. Missing or mismatched accepted provenance fails closed.

Only receipt-bound accepted exact bytes may be materialized at:

```text
artifacts/research_trajectory/events/<event_id>.json
```

The rebuildable current graph and human projection are fixed at:

```text
artifacts/research_trajectory/snapshot.json
artifacts/research_trajectory/TRAJECTORY.md
```

An accepted event is immutable. Replaying the same event identity and digest is
an idempotent no-op; the same identity with different bytes fails closed. A
revised hypothesis or interpretation creates a new event and explicitly links
to the earlier event or node rather than rewriting history.

## Medical Narrative

Every map node, relationship, three-axis interpretation, snapshot summary, and
`TRAJECTORY.md` statement must be authored by MAS. OPL and the App may validate,
persist, lay out, and display that text, but must not infer medical wording from
machine kinds or status codes.

Use these reader-facing headings:

- 研究问题
- 当前主要假设
- 验证方法
- 主要发现
- 证据判断
- 路线调整
- 下一研究步骤
- 来源与依据

Write with the conventions of a medical abstract, Results section, or
Discussion section: identify the population or evidence scope, method, observed
finding, uncertainty, limitations, interpretation, and justified next step.
Prefer restrained statements such as “该结果支持当前假设”“该结果不支持当前
假设”“现有证据尚不足以得出确定判断” and “当前研究设计不足以判断”. Use
“继续验证”“返回并修订研究假设或研究设计”“收窄研究问题”“调整研究路线”
“暂停该研究路线” and “需要研究者判断” for route descriptions.

Do not expose code paths, file paths, node or event identifiers, StageRun or
Attempt identifiers, payloads, hashes, provider state, runtime queues, retry
mechanics, or internal chain-of-thought in user-visible prose. Put exact source,
lineage, receipt, and diagnostic locators only in machine refs. Human-facing
“来源与依据” should cite recognizable study artifacts, tables, figures,
protocol sections, guidelines, registries, or publications.

## Stage-Specific Checkpoints

- `direction_and_route_selection`: record proposed or refined hypotheses,
  selected and rejected scientific routes, stop conditions, and continue,
  narrow, pivot, stop, or researcher-judgment decisions.
- `baseline_and_evidence_setup`: record material cohort, endpoint, comparator,
  source, feasibility, and validation-plan changes; preserve data insufficiency,
  null baselines, and design-invalid findings.
- `bounded_analysis_campaign`: record each claim-relevant completed or failed
  analysis, positive/negative/null/mixed result, evidence interpretation, and
  resulting route decision.
- `manuscript_authoring`: record only scientific interpretation or route changes
  revealed during writing; ordinary prose, citation formatting, or layout edits
  do not create trajectory events.
- `review_and_quality_gate`: record the independent reviewer's decisive evidence
  interpretation, limitations that alter the claim, and accepted continue,
  refine, pivot, stop, or route-back decision.
- `finalize_and_publication_handoff`: record a terminal research-route or
  publication-route decision and a materially accepted artifact; mechanical
  packaging and transport alone return a null trajectory delta.

## Session Reconciliation

Codex may inspect linked sessions for historical reconstruction, omission
detection, or candidate-delta drafting. Use only user-visible messages, tool
results, artifact refs, and explicit conclusions. Never extract or publish
implicit reasoning. Session summaries remain candidates and pass through the
same MAS acceptance gate before entering the accepted trajectory.
