# OMX CLI Host Adapter

Use this host adapter when the current session is actually running under OMX CLI/runtime.

## Activation Signals

Typical signals include:

- the session was launched through `omx`
- OMX runtime state is available under `.omx/`
- OMX-specific lifecycle, team, HUD, or trace surfaces are active
- the user explicitly asks to run `omx ...` in the shell

## Host Behavior

- Runtime-only workflows such as `autopilot`, `ralph`, `ultrawork`, `ultraqa`, `team`, and `ecomode` may be activated when their normal gates are satisfied
- OMX runtime state, `.omx/` artifacts, tmux workers, and `omx team` lifecycle surfaces may be treated as first-class execution infrastructure
- `omx explore` and `omx sparkshell` may be preferred for qualifying read-only workflows when the repository contract enables them

## Boundary

This adapter controls host behavior only.
It must not override the project-native MedAutoScience truth source in `contracts/med-autoscience-repository/AGENTS.md`.
