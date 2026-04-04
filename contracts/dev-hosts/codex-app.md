# Codex App Host Adapter

Use this host adapter when the session is running in Codex App or plain Codex without OMX runtime.

## Activation Signals

Typical signals include:

- no active OMX runtime state for the current session
- the session was started directly in Codex App
- the user is asking for repository work without explicitly launching `omx ...`

## Host Behavior

- Do not auto-activate OMX runtime workflows from keywords alone
- Treat `autopilot`, `ralph`, `ultrawork`, `ultraqa`, `team`, and `ecomode` as runtime-only workflows that require explicit OMX runtime support
- Prefer App-safe surfaces such as `deep-interview`, `ralplan`, `plan`, `/prompts:*`, and native subagents
- If the user explicitly wants OMX runtime behavior, launch it through the shell instead of pretending the App session already has runtime state

## Boundary

This adapter controls host behavior only.
It must not override the project-native MedAutoScience truth source in `contracts/med-autoscience-repository/AGENTS.md`.
