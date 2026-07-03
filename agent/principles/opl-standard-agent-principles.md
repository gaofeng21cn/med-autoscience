# OPL Standard Agent Principles Projection

Owner: `one-person-lab`
Purpose: repo-local projection of the OPL standard-agent AI-first principle pack.
State: `active_projection`
Machine boundary: this file projects the principle ids consumed by `contracts/standard-agent-principles-adoption.json`. Canonical OPL policy remains in `contracts/opl-framework/standard-agent-principles.json` and `human_doc:one-person-lab/docs/policies/standard-agent-ai-first-principles.md`.

This projection does not create a second truth source. OPL owns the shared principle vocabulary; MAS owns study truth, source readiness, publication quality, artifact package authority, current package authority, memory accept/reject, owner receipts, typed blockers, human gates, and controller decisions.

| Principle id | Principle | Domain adoption meaning |
| --- | --- | --- |
| `ai_first_execution` | AI-first execution | AI performs open-ended medical research reasoning, drafting, review, diagnosis, and revision inside bounded stage attempts. |
| `contract_backed_boundary` | Contract-backed boundary | Contracts, schemas, tests, and readbacks guard identity, authority, inputs, outputs, evidence, and recovery. |
| `domain_truth_authority` | Domain truth authority | Study truth, source readiness, quality/export verdicts, artifact authority, memory body, owner receipts, and typed blockers stay with MAS. |
| `stage_prompt_skill_tool_separation` | Prompt / Skill / Tool separation | MAS stage prompts define goals and accepted answer shapes; professional skills carry medical methods; tool catalogs describe affordances and limits. |
| `domain_intake_mapping` | Domain intake mapping | `domain_intake` is an owner-handoff pattern mapped to MAS `01-study_intake` and `study_task_intake*.py`, not an independent Skill. |
| `workspace_source_intake_shell` | Workspace/source shell | OPL owns generic locator and refs-only source intake transport; MAS owns clinical/source semantics, readiness, provenance, and study task truth. |
| `owner_delta_progress` | Owner-delta progress | Progress is measured by paper/study deltas, owner receipts, reviewer receipts, route-back refs, typed blockers, human gates, or handoff packets. |
| `parallel_executor_autonomy` | Bounded executor autonomy | Executors may choose order, tools, substitutions, and safe parallelism inside declared authority and permission boundaries. |
| `module_organization` | Module organization | OPL brand modules hold framework primitives; MAS is a declarative domain pack plus minimal authority functions; ScholarSkills is a capability pack, not domain intake. |

For MAS, these ids are adopted through the medical-research specialization in `agent/principles/domain-specialization.md` and the mapping contract in `contracts/standard-agent-principles-adoption.json`.
