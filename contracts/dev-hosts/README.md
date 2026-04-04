# Development Host Adapters

This directory holds versioned host adapter contracts for repository development sessions.

It exists to keep host/runtime differences out of the MedAutoScience project-native contract and out of machine-specific local overlays.

## Layers

Use the following layering model:

1. Root repository development contract: `AGENTS.md`
2. Host adapter contract from this directory
3. Project-native contract: `contracts/med-autoscience-repository/AGENTS.md`
4. Optional local-only overlay: `.omx/local/AGENTS.local.md`

## Files

- `omx-cli.md`: host behavior when the session is running under OMX CLI/runtime
- `codex-app.md`: host behavior when the session is running in Codex App or plain Codex without OMX runtime

## Local Overlay Convention

Machine-specific paths, personal shell workflow, private launch hints, and other non-portable guidance belong in:

`.omx/local/AGENTS.local.md`

That file must stay untracked.

## Portability Rule

Keep this directory reusable across repositories that share the same development workflow.
Host adapter contracts may describe execution surfaces and activation gates, but they must not redefine the MedAutoScience project truth.
