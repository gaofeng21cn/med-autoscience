# Research Trajectory And Medical Narrative

Owner: MedAutoScience
Contract: `contracts/research_trajectory_contract.json`
Current snapshot schema: `contracts/schemas/v2/mas-research-trajectory-snapshot-v2.schema.json`
Narrative schema: `contracts/schemas/v2/mas-medical-narrative.schema.json`

## Purpose

Maintain a current, reader-facing account of how the study question, principal
hypothesis, validation strategy, evidence interpretation, research route, and
next step evolve while the MAS Attempt is running. This is a progress reference
for clinicians, professors, and biomedical researchers. It is not a publication
quality verdict, an acceptance receipt, or an execution log.

## Update The Two Fixed Artifacts Together

When a meaningful scientific change occurs, the current MAS Attempt directly
updates both of these study-relative artifacts as one semantic update:

```text
artifacts/research_trajectory/TRAJECTORY.md
artifacts/research_trajectory/snapshot.json
```

`TRAJECTORY.md` is the human-readable medical account. `snapshot.json` is the
lightweight structured source used to draw the map. Increment the snapshot
revision once for the dual-file update. Both files must describe the same
current hypothesis, evidence judgment, route, and next step.

Do not create a candidate event, accepted-event log, checkpoint submission,
checkpoint manifest, binding, working-checkpoint layer, or trajectory-specific
receipt. Do not wait for an independent reviewer before recording current
progress. The nullable Stage output field `research_trajectory_delta_ref` is
v1 read compatibility only and is not a v2 write gate.

## Meaningful Scientific Changes

Update the two artifacts when the study does at least one of the following:

- proposes or revises the principal hypothesis;
- completes a claim-relevant validation;
- interprets a positive, negative, null, mixed, or inconclusive result;
- continues, refines, narrows, pivots, stops, or sends the route to researcher
  judgment;
- materially changes the next research step.

An execution failure merits an update only when it materially changes the
validation boundary, route, or next step. Do not update for a tool call,
heartbeat, retry, provider or queue state, formatting change, packaging,
hashing, transport, or other activity without a scientific change.

## Keep Three Judgments Separate

Always distinguish:

1. **Execution outcome**: whether the validation was completed, failed,
   cancelled, or not run.
2. **Evidence interpretation**: whether the observed result supports the
   hypothesis, does not support it, remains inconclusive, cannot be interpreted
   under the current design, or was not assessed.
3. **Route decision**: whether to continue, refine, narrow, pivot, stop, or
   request researcher judgment.

An execution failure is not evidence against a hypothesis. State that the
validation was not completed and the evidence was not assessed. A completed
validation that yields discordant evidence may be described as not supporting
the current hypothesis. A completed or partial validation with imprecise,
conflicting, or sparse evidence is inconclusive. Do not collapse these states.

Negative and null findings are evidence and remain visible. Preserve an
unsuccessful route in the graph and explain why the study changed direction;
do not delete the prior hypothesis, test, or finding to make the current route
look linear.

## Medical Results And Discussion Style

Write for medical and scientific readers. Each current account states:

- the research question and population, evidence, endpoint, and time scope;
- the validation method at the level needed to understand the result;
- the observed finding without implementation detail;
- uncertainty, limitations, and relevant design constraints;
- the evidence judgment supported by the cited material;
- the route adjustment and its scientific reason;
- the next research step and its intended decision value.

Use restrained Results and Discussion language. Distinguish statements such as
“the result supports the current hypothesis”, “the result does not support the
current hypothesis”, “the available evidence is insufficient for a determinate
judgment”, and “the current design is insufficient to answer the question”. Do
not infer mechanism, causality, subgroup effects, clinical benefit, or safety
beyond the actual evidence.

`TRAJECTORY.md` uses these reader-facing headings:

- 研究问题
- 研究范围
- 当前主要假设
- 验证方法
- 主要发现
- 证据判断
- 路线调整
- 下一研究步骤
- 来源与依据

The Markdown may include a concise route map, but its labels must use the same
medical wording as the surrounding document.

## Structured Map

The v2 snapshot contains the current revision and status, summary, current
focus, active branch, explicit current-focus and active-branch node refs, nodes,
edges, overall medical narrative, machine source refs, and conditions.

Every edge endpoint and current-route ref must name an existing node. Nodes from
earlier or unsuccessful routes remain present and are marked historical or
superseded as appropriate. The current route is explicit; Framework and the App
must not infer it from branch names or medical text.

All visible labels, summaries, edge descriptions, condition explanations, and
medical narratives are authored by MAS. Framework and the App may validate,
read, transport, lay out, and display these fields, but may not translate,
summarize, rewrite, accept, reject, or infer medical judgment.

## Reader-Safe Boundary

Do not expose code or file paths, node or event identifiers, StageRun or Attempt
identifiers, payloads, hashes, provider or queue state, checkpoint mechanics,
retry mechanics, or internal chain-of-thought in human-visible prose. Machine
source refs remain hidden by default. In “来源与依据”, cite recognizable study
protocols, cohort definitions, analysis plans, tables, figures, guidelines,
registries, or publications.

Codex may read linked sessions to recover omissions or update the current
account, but may use only user-visible messages, tool results, artifact refs,
and explicit conclusions. It must not extract or publish implicit reasoning and
must not turn a session summary into evidence without source support.

## Review Boundary

Ordinary trajectory updates do not start an independent reviewer. Existing
independent review remains available at an applicable Stage end, after a major
scientific route switch, and at a formal manuscript or publication quality
gate. Record the current progress first; any required review follows through the
existing Stage lifecycle and is not a prerequisite for writing these files.

Passing schema or fixture tests proves only structure, fixed paths, graph
reference integrity, and absence of selected machine terms. It does not prove
that medical prose is publication quality or that a scientific conclusion is
correct.

## Stage Emphasis

- `direction_and_route_selection`: hypotheses, selected and unsuccessful
  alternatives, route rationale, stop conditions, and next validation.
- `baseline_and_evidence_setup`: population, endpoint, comparator, source,
  feasibility, and material validation-plan changes.
- `bounded_analysis_campaign`: completed or materially failed validation,
  observed result, evidence interpretation, uncertainty, and route decision.
- `manuscript_authoring`: only scientific interpretation or route changes
  revealed during writing, not ordinary prose or layout edits.
- `review_and_quality_gate`: review findings only when they materially change
  the evidence judgment, claim boundary, limitation, route, or next step.
- `finalize_and_publication_handoff`: terminal research or publication-route
  decisions, not mechanical packaging or transport.

Legacy v1 event and snapshot schemas remain readable for historical studies.
Do not create new v1 events or silently convert historical acceptance metadata
into v2 progress authority.
