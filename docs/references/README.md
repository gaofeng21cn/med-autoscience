# References

This directory holds useful technical context that remains relevant but is not
the active development-plan, runtime-contract, or execution-gate layer.

Use these files to understand background, integration shape, parity evidence,
positioning, and verification history. Current execution gates stay in
`docs/program/`, runtime authority stays in `docs/runtime/`, and active truth
starts from the core docs:

- [Docs guide](../README.md)
- [Project](../project.md)
- [Status](../status.md)
- [Architecture](../architecture.md)
- [Invariants](../invariants.md)
- [Decisions](../decisions.md)
- [Program portfolio consolidation](../program/program_portfolio_consolidation.md)

## Current Mainline References

- [MAS single-project quality and autonomy mainline](./mas_single_project_quality_and_autonomy_mainline.md)
- [AI-first research OS architecture](./ai_first_research_os_architecture.md)
- [Project repair priority map](./project_repair_priority_map.md)
- [Series doc governance checklist](./series-doc-governance-checklist.md)

## Workspace And Integration References

- [Disease workspace quickstart](./disease_workspace_quickstart.md)
- [Workspace architecture](./workspace_architecture.md)
- [Lightweight product entry and OPL handoff](./lightweight_product_entry_and_opl_handoff.md)
- [Codex plugin](./codex_plugin.md)
- [Codex plugin release](./codex_plugin_release.md)
- [Domain gateway harness OS](./domain_gateway_harness_os.md)
- [OPL family contract adoption](./opl_family_contract_adoption.md)
- [OPL-managed runtime three-layer contract](./opl_managed_runtime_three_layer_contract.md)

## MDS Learning And Intake References

- [MedDeepScientist references](./med-deepscientist/README.md)

`med-deepscientist/` includes the active policy and protocol for recurring
DeepScientist learning. Dated intake records are stored under
`docs/history/program/` as completed-round snapshots.

## Positioning And Architecture References

- [Domain Harness OS positioning](./domain-harness-os-positioning.md)
- [Open Harness OS architecture](./open_harness_os_architecture.md)
- [Research Foundry positioning](./research_foundry_positioning.md)
- [Research Foundry medical phase ladder](./research_foundry_medical_phase_ladder.md)
- [Repo split between Research Foundry and Med Auto Science](./repo_split_between_research_foundry_and_med_autoscience.md)

## Ledgers, Parity, And Verification References

- [Plan completion ledger](./plan_completion_ledger.md)
- [MDS capability parity matrix](./mds_capability_parity_matrix.md)
- [Real-study relaunch verification](./real_study_relaunch_verification.md)

## Grouping Rules

New reference files should enter one of the groups above before the root-level
file list grows:

- Mainline references: enduring MAS quality, autonomy, repair-priority, or docs-governance context.
- Workspace and integration references: workspace setup, plugin, handoff, gateway, and family-contract context.
- MDS learning and intake references: standing learning policies and protocols; dated intake snapshots belong in history.
- Positioning and architecture references: repo positioning, external model comparison, and architectural rationale.
- Ledgers, parity, and verification references: evidence ledgers, parity matrices, and verification narratives.

If a new reference does not fit an existing group, first decide whether it is
actually an active program, runtime contract, policy, capability-family doc, or
history snapshot. Add a new references group only when the category is recurring
and likely to hold more than one file. Otherwise link it from the closest owner
README instead of letting loose root-level reference files continue expanding.

## Lifecycle Rule

References are support material. They may preserve rationale, comparison,
integration notes, and evidence history, but they do not certify current runtime
state, publication readiness, controller authority, or active execution gates.
When a reference conflicts with current truth, use the core docs, runtime
contracts, policy docs, durable JSON/schema surfaces, and active program board.

OPL family lifecycle governance is a documentation-management input only. MAS
does not inherit OPL owner routes by placement in `docs/references/`; MAS domain
truth remains in MAS-owned contracts, controllers, generated catalogs, schemas,
and durable workspace surfaces.
