---
name: med-autoscience
description: Use when Codex needs MedAutoScience (MAS) to plan, conduct, review, or publish medical research, including research questions, study design, cohorts and endpoints, evidence synthesis, bounded analysis, scientific figures/tables, manuscript writing, quality review, and publication handoff. Do not use for patient-specific diagnosis, treatment, triage, or emergency advice; medical grant applications; or generic Office formatting without a research objective.
---

# MedAutoScience

Canonical OPL Agent id is `mas`; `med-autoscience` is the package/plugin Skill locator. Operate MAS through OPL-generated interfaces while MAS retains medical, evidence, artifact, quality, and publication authority.

## Admission

- Admit MAS only when the requested outcome is medical research or a research artifact tied to an identifiable study, evidence question, dataset/cohort, manuscript, or publication package.
- Do not route patient-specific clinical-care requests to MAS. Keep diagnosis, treatment choice, dosing, triage, and emergency guidance outside this research Agent and direct the user to appropriate clinical care when needed.
- Route funding-call strategy and grant application authoring to MAG. Route generic slides to RCA and generic document formatting to the relevant document capability unless the work is subordinate to a MAS research artifact.
- Bind the current research objective, source/data cohort, study/workspace identity, accepted upstream refs, and intended claim before selecting an action. Do not infer scientific readiness from file presence or package/runtime status.

## Action Routing

Choose the earliest unresolved owning Stage action from the installed OPL-generated interface:

- `direction_and_route_selection`: define or repair the research question, route, feasibility, and governing assumptions.
- `baseline_and_evidence_setup`: establish the protocol/method baseline, evidence/source map, cohort/phenotype, endpoints, governance, and analysis readiness.
- `bounded_analysis_campaign`: execute a bounded, reproducible analysis against an accepted design and frozen inputs.
- `manuscript_authoring`: write or materially revise the scientific manuscript and its display artifacts from current evidence refs.
- `review_and_quality_gate`: run independent scientific, statistical, evidence-integrity, reference, figure/table, or manuscript review.
- `finalize_and_publication_handoff`: assemble the final publication handoff after current review evidence and explicit human submission authority.

`qualification_work_item_provisioning_authority_evaluate`, `study_lifecycle_reactivation_authority_evaluate`, `candidate_admission_authority_evaluate`, `build_dependency_currentness_authority_evaluate`, and `paper_mission_authority_evaluate` are internal registry-bound authority actions. They have no public CLI, MCP, Skill, product-entry, OpenAI, or AI SDK route and must not be invoked as user actions.

## Default Workflow

1. Select one public action from the research intent and current accepted refs; do not begin with package lifecycle or environment commands when the user asked for research work.
2. For an inactive study receiving an explicit manuscript-revision instruction, first persist durable user-instruction evidence and a `reviewer_revision` intake that binds the full checklist, independent review packet, first owning Stage, and allowed revision scope. Use the hosted lifecycle admission flow; runtime activity alone never reactivates MAS business truth.
3. Preserve one OPL StageRun lineage and exact source/data/artifact refs while Codex routes among declared MAS stages.
4. Use the installed `mas-scholar-skills` capability package for focused medical methods. Acquire another external Skill only for a named or demonstrated coverage gap after provenance, permissions, data/credential scope, and compatibility review.
5. For every initial draft, apply the MAS-owned `initial_draft_evidence_integrity_requirements` in `contracts/manuscript_first_draft_quality_policy.json` at their declared earliest Stage owners. Missing or unresolved requirements are quality debt and cannot be hidden by prose, Skill output, render success, or runtime completion.
6. Prepare the declarative runtime environment only when the selected analysis/display work requires it. An environment receipt proves execution readiness only, never medical or publication quality.
7. Separate producing and independent reviewer/auditor invocations, task records, and receipts before closing a formal quality gate.
8. Freeze one candidate after bounded previews, then run complete export, exact-byte inventory, and affected independent review once for that candidate.

## Quality And Hard Stops

- Treat raw/partial artifacts, negative or null results, failed attempts, review findings, and no-output diagnostics as route context. A consumable delta may advance as `completed_with_quality_debt`.
- Do not edit `submission/` or launch a Stage from a paused, delivered-paused, or stopped business projection. Reactivation requires a current MAS receipt plus matching OPL all-or-rollback materialization receipt; neither a Temporal-running signal nor provider completion is sufficient.
- A qualification-only work item may prove Full VM identity and lifecycle transport only. It never authorizes a Stage body, business action, publication, or submission, even after its MAS provisioning receipt and matching OPL materialization receipt are current.
- Retry, review, and repair limits are quality budgets. Exhaustion preserves the best evidence-bearing artifact and closes quality, publication, export, and submission-ready claims; it does not create an infinite stage loop.
- Negative findings remain evidence. Preserve lineage and route back to the owning hypothesis, cohort/data, endpoint, analysis design, writing, or review stage instead of optimizing for a positive result.
- For new or materially repaired paper-facing figures, use `medical-figure-design`; use `medical-figure-style` for final visual QA and `medical-figure-composer` only for separately assembled panels.
- Only executor unavailability, wrong-target identity/currentness, real authority/safety/credential boundaries, irreversible action, protected data/material, or an explicit human decision may hard-stop progress.

## Output Expectations

- Return the selected public action and Stage, exact research/source/data/artifact refs, methods or analysis outputs, review/authority refs, typed blockers, remaining quality debt, and the next owning Stage.
- Match every scientific claim to its evidence class and locator. Do not promote external Skill output, preview/cache evidence, runtime receipts, generated descriptors, or provider completion into MAS authority.
- Name artifact maturity precisely: plan, frozen baseline, bounded analysis result, manuscript draft, review finding, publication handoff candidate, or owner-authorized final handoff.
- Preserve MAS-owned owner receipts and publication/submission authority; OPL may transport and persist refs but cannot author medical truth or sign those decisions.

## References

- `contracts/action_catalog.json`
- `agent/stages/manifest.json`
- `contracts/artifact_iteration_efficiency_policy.json`
- `contracts/stage_quality_cycle_policy.json`
- `contracts/runtime_environment_requirements.json`
- `contracts/owner_receipt_contract.json`
- `contracts/domain_handler_registry.json`
