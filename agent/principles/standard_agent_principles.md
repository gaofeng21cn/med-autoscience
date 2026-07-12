# MAS Standard Agent Principles

Owner: `MedAutoScience`
Purpose: legacy MAS-local pointer for standard-agent principle projection and domain specialization.
State: `active_agent_source`
Machine boundary: human-readable compatibility pointer. Machine-readable adoption is in `contracts/standard-agent-principles-adoption.json`; canonical local projections are `agent/principles/opl-standard-agent-principles.md` and `agent/principles/domain-specialization.md`.

MAS now adopts the OPL Standard Agent AI-first principle pack through the ten canonical principle ids:

- `ai_first_execution`
- `contract_backed_boundary`
- `domain_truth_authority`
- `stage_prompt_skill_tool_separation`
- `domain_intake_mapping`
- `workspace_source_intake_shell`
- `owner_delta_progress`
- `quality_budget_progress_first`
- `parallel_executor_autonomy`
- `module_organization`

For MAS-specific detail, read `agent/principles/domain-specialization.md`. The key boundary is unchanged: `domain_intake` maps to MAS `01-study_intake` and `src/med_autoscience/study_task_intake*.py`, not to an independent Skill. MAS retains study truth, source readiness, publication quality, artifact/current-package authority, owner receipts, typed blockers, human gates, and controller decisions. MAS ScholarSkills remains a refs-only capability pack with active modules `display`, `tables`, `stats`, `lit`, `write`, `review`, `submit`, and `data`; `intake` is not an active ScholarSkills module and `omics` remains deferred/reference.
