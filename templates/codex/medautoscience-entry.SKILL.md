# MedAutoScience Agent Entry (Codex)

Use this contract to select entry mode and route actions without changing canonical definitions.

Compatible agents: Codex, Claude Code, OpenClaw
Runtime modes: lightweight, managed

## Mode Contract
- full_research: runtime=managed, scope=none
  preconditions: workspace/profile available
  managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
  lightweight_routes: (none)
  managed_routes: doctor, bootstrap, overlay-status, scout, idea, experiment, write, finalize
  governance_routes: decision
  auxiliary_routes: (none)
  upgrade_triggers: (none)
- literature_scout: runtime=lightweight, scope=early evidence framing
  preconditions: workspace/profile available
  managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
  lightweight_routes: scout
  managed_routes: doctor, bootstrap, overlay-status, scout, idea, experiment, write, finalize
  governance_routes: decision
  auxiliary_routes: (none)
  upgrade_triggers: hypothesis viability confirmed
- idea_exploration: runtime=lightweight, scope=route selection and study framing
  preconditions: workspace/profile available
  managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
  lightweight_routes: idea, decision
  managed_routes: doctor, bootstrap, overlay-status, scout, idea, experiment, write, finalize
  governance_routes: decision
  auxiliary_routes: (none)
  upgrade_triggers: experiment execution approved
- project_optimization: runtime=lightweight, scope=pathway adjustment and stop-loss
  preconditions: workspace/profile available
  managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
  lightweight_routes: decision
  managed_routes: doctor, bootstrap, overlay-status, scout, idea, experiment, write, finalize
  governance_routes: decision
  auxiliary_routes: (none)
  upgrade_triggers: major direction change approved
- writing_delivery: runtime=lightweight, scope=manuscript and delivery packaging
  preconditions: workspace/profile available
  managed_entry_actions: doctor, bootstrap, overlay-status, ensure-study-runtime
  lightweight_routes: write
  managed_routes: doctor, bootstrap, overlay-status, write, finalize
  governance_routes: (none)
  auxiliary_routes: journal-resolution
  upgrade_triggers: submission bundle or final delivery requested

## Upgrade Rule
If `upgrade_triggers` is non-empty and any trigger is satisfied, upgrade from lightweight to managed before continuing.
