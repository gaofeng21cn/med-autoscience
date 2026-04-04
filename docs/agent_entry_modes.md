# Agent Entry Modes

Canonical source: `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`.

## Compatible Agents
- Codex, Claude Code, OpenClaw

## Runtime Modes
- lightweight, managed

## Mode Contract

### full_research (Full Research)
- default_runtime_mode: managed
- lightweight_scope: none
- preconditions: workspace/profile available
- managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
- lightweight_routes: (none)
- managed_routes: doctor, bootstrap, overlay-status, scout, idea, write, finalize
- startup_boundary_gated_routes: baseline, experiment, analysis-campaign
- governance_routes: decision
- auxiliary_routes: (none)
- upgrade_triggers: (none)

### literature_scout (Literature Scout)
- default_runtime_mode: lightweight
- lightweight_scope: early evidence framing
- preconditions: workspace/profile available
- managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
- lightweight_routes: scout
- managed_routes: doctor, bootstrap, overlay-status, scout, idea, write, finalize
- startup_boundary_gated_routes: baseline, experiment, analysis-campaign
- governance_routes: decision
- auxiliary_routes: (none)
- upgrade_triggers: hypothesis viability confirmed

### idea_exploration (Idea Exploration)
- default_runtime_mode: lightweight
- lightweight_scope: route selection and study framing
- preconditions: workspace/profile available
- managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
- lightweight_routes: idea, decision
- managed_routes: doctor, bootstrap, overlay-status, scout, idea, write, finalize
- startup_boundary_gated_routes: baseline, experiment, analysis-campaign
- governance_routes: decision
- auxiliary_routes: (none)
- upgrade_triggers: experiment execution approved

### project_optimization (Project Optimization)
- default_runtime_mode: lightweight
- lightweight_scope: pathway adjustment and stop-loss
- preconditions: workspace/profile available
- managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
- lightweight_routes: decision
- managed_routes: doctor, bootstrap, overlay-status, scout, idea, write, finalize
- startup_boundary_gated_routes: baseline, experiment, analysis-campaign
- governance_routes: decision
- auxiliary_routes: (none)
- upgrade_triggers: major direction change approved

### writing_delivery (Writing Delivery)
- default_runtime_mode: lightweight
- lightweight_scope: manuscript and delivery packaging
- preconditions: workspace/profile available
- managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
- lightweight_routes: write
- managed_routes: doctor, bootstrap, overlay-status, write, finalize
- startup_boundary_gated_routes: (none)
- governance_routes: (none)
- auxiliary_routes: journal-resolution
- upgrade_triggers: submission bundle or final delivery requested

## Upgrade Rules
If `upgrade_triggers` is non-empty and any trigger is satisfied, upgrade from lightweight to managed before continuing.

## Startup Boundary Rule
Run `ensure-study-runtime` before any managed compute decision. Do not enter `startup_boundary_gated_routes` unless that controller reports `startup_boundary_gate.allow_compute_stage = true`; otherwise stay within `managed_routes`, `governance_routes`, and any writing-only delivery route.
