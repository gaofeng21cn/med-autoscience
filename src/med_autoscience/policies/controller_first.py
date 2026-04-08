from __future__ import annotations


def render_controller_first_block() -> str:
    lines = [
        "## Controller-first execution contract",
        "",
        "Prefer mature MedAutoScience controllers, CLI entrypoints, and overlay skills before any freeform external execution.",
        "",
        "Default controller-first order for common managed tasks:",
        "- portfolio research memory: inspect `portfolio/research_memory/*` and use `portfolio-memory-status` before fresh disease-topic, dataset-question, or venue-neighborhood rediscovery",
        "- optional external AI deep research: only after portfolio memory reuse, use `prepare-external-research` / `external-research-status` as an optional enrichment surface; never treat it as a startup gate or a substitute for study-local evidence",
        "- literature and reference anchors: `resolve-reference-papers` before broad freeform literature expansion",
        "- venue selection and journal shortlist evidence: `resolve-journal-shortlist` before any journal-facing recommendation or tier discussion",
        "- submission targets and journal requirements: only after a primary venue decision, use `resolve-submission-targets`, then `journal-resolution` when the target is still unresolved",
        "- public dataset discovery and registration: for scout-first route selection and every paper-bound route, complete at least one proactive public-data discovery pass unless the study contract explicitly waives public sidecars; check `portfolio/data_assets/public/registry.json`, use `data-assets-status`, `startup-data-readiness`, and `tooluniverse-status` before acquisition, record retain / reject outcomes through `apply-data-asset-update`, and start immediate download or materialization follow-through for retained anchors",
        "- startup and publication gates: use the existing startup/data/publication gate controllers before inventing ad-hoc route logic",
        "",
        "Fallback rule:",
        "- Only when the platform does not already provide a stable controller, CLI, or overlay skill for the task may the agent use freeform external execution such as browser automation, web browsing, or document extraction.",
        "",
        "Write-back rule:",
        "- If fallback execution is used, the result must still be written back into MedAutoScience durable state such as study artifacts, paper artifacts, startup contracts, or the public/private data-asset registries.",
        "- Do not leave durable research state only in transient chat output.",
    ]
    return "\n".join(lines) + "\n"


def render_controller_first_summary() -> str:
    return (
        "Controller-first rule: prefer mature MedAutoScience controllers before freeform external execution. "
        "Use `portfolio-memory-status` and the existing `portfolio/research_memory/*` layer before re-deriving disease topic landscapes, dataset question maps, or venue neighborhoods from scratch. "
        "When broader external AI deep research is still useful, use `prepare-external-research` as an optional enrichment scaffold and write raw reports to `portfolio/research_memory/external_reports/`; this is not a startup prerequisite. "
        "Use `resolve-reference-papers`, `resolve-journal-shortlist`, and, only after a venue decision, "
        "`resolve-submission-targets` plus `journal-resolution`. For scout-first or paper-bound routes, complete "
        "one proactive public-data discovery pass unless the study contract explicitly waives public sidecars: "
        "check `portfolio/data_assets/public/registry.json`, then use `data-assets-status`, `startup-data-readiness`, "
        "`tooluniverse-status`, and `apply-data-asset-update`, and start immediate download or materialization "
        "follow-through for retained anchors whenever the task falls inside their covered surface. Only when the platform does not already provide a "
        "stable controller may the agent fall back to browser/web/document tools, and any such fallback must be "
        "written back into durable MedAutoScience state."
    )
