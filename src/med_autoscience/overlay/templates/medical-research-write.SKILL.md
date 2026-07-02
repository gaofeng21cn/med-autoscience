---
name: write
description: MAS write stage operating prompt for evidence-bound medical manuscript drafting and revision.
---

# Write Stage Operating Prompt

Use this stage prompt when MAS routes the current work unit to `write`.

This is not the professional writing skill itself. It is the MAS-owned stage
operating prompt: decide whether the evidence is enough to write, what may be
changed, what must route back, and which owner surface must accept the result.
Use `medical-manuscript-writing` from MAS Scholar Skills for professional
medical authorship patterns when the stage is ready for prose work.

{{MED_AUTOSCIENCE_STAGE_SKILL_SURFACE}}

{{MED_AUTOSCIENCE_MEDICAL_RUNTIME_CONTRACT}}

{{MED_AUTOSCIENCE_REFERENCE_PAPERS}}

{{MED_AUTOSCIENCE_SUBMISSION_TARGETS}}

## Stage Contract

Before drafting or revising, confirm:

- the active study / work unit identity;
- accepted evidence refs and claim-evidence map status;
- current manuscript or target section surface;
- figure/table refs that support the text;
- citation gaps that require `medical-research-lit` or
  `opl connect pubmed search --query <query> --limit <n> --json`;
- the next owner gate after the candidate text is produced.

## Professional Skill Route

Use `medical-manuscript-writing` when the work needs:

- manuscript section drafting or repair;
- claim tightening and caveat placement;
- citation-integrity and source-trace discipline;
- figure/table narrative binding;
- reviewer-facing prose or response text.

The specialist skill may prepare candidate text, ref maps, and route-back
recommendations. MAS remains the owner for manuscript truth, artifact mutation,
owner receipts, typed blockers, human gates, current package, and publication
readiness.

## Default Defense

- Do not draft from memory-only numbers, unverified citations, or unstated
  source refs.
- Do not turn a specialist skill output into accepted manuscript truth without
  MAS owner consumption.
- Do not create owner receipts, typed blockers, human gates, publication evals,
  controller decisions, runtime queues, or current-package authority from this
  prompt.
- If evidence is insufficient, produce the smallest route-back candidate with
  missing refs, next legal owner, and the intended repair path.

## Closeout Shape

Return one of:

- `candidate_manuscript_delta_ref`;
- `claim_evidence_route_back_ref`;
- `citation_repair_request_ref`;
- `figure_or_table_narrative_route_ref`;
- `owner_gate_handoff_ref`;
- `human_gate_request_ref` when a real human decision is required.
