from __future__ import annotations

from med_autoscience.foundry_command_surface import (
    FOUNDRY_GROUP,
    FOUNDRY_TOP_LEVEL_ALIASES,
    PUBLIC_HELP_LINES,
    grouped_command_aliases,
    grouped_command_summaries,
    normalize_foundry_argv,
)

GROUPED_COMMAND_ALIASES: dict[tuple[str, str], str] = {
    **grouped_command_aliases(),
    ("doctor", "report"): "doctor",
    ("doctor", "profile"): "show-profile",
    ("doctor", "mainline-status"): "mainline-status",
    ("doctor", "mainline-phase"): "mainline-phase",
    ("doctor", "stage-route-contract"): "show-stage-route-contract",
    ("doctor", "sync-entry-assets"): "sync-agent-entry-assets",
    ("doctor", "preflight"): "preflight-changes",
    ("doctor", "preflight-contract-report"): "preflight-contract-report",
    ("doctor", "backend-audit"): "backend-audit",
    ("workspace", "bootstrap"): "bootstrap",
    ("workspace", "init"): "init-workspace",
    ("workspace", "profile-cycles"): "workspace-profile-cycles",
    ("workspace", "study-status"): "study-workspace-status",
    ("workspace", "target-state-cleanup"): "workspace-target-state-cleanup",
    ("data", "init-assets"): "init-data-assets",
    ("data", "assets-status"): "data-assets-status",
    ("data", "manifest-refs-rebuild"): "data-asset-manifest-refs-rebuild",
    ("data", "asset-retention-plan"): "data-asset-retention-plan",
    ("data", "sqlite-compact-plan"): "data-asset-sqlite-compact-plan",
    ("data", "init-memory"): "init-portfolio-memory",
    ("data", "memory-status"): "portfolio-memory-status",
    ("data", "init-literature"): "init-workspace-literature",
    ("data", "literature-status"): "workspace-literature-status",
    ("data", "prepare-external-research"): "prepare-external-research",
    ("data", "external-research-status"): "external-research-status",
    ("data", "assess-asset-impact"): "assess-data-asset-impact",
    ("data", "validate-public-registry"): "validate-public-registry",
    ("data", "startup-readiness"): "startup-data-readiness",
    ("data", "apply-asset-update"): "apply-data-asset-update",
    ("data", "diff-private-release"): "diff-private-release",
    ("data", "asset-gate"): "data-asset-gate",
    ("data", "tooluniverse-status"): "tooluniverse-status",
    ("runtime", "domain-health-diagnostic"): "domain-health-diagnostic",
    ("runtime", "reconcile-health"): "reconcile-runtime-health",
    ("runtime", "domain-action-request-materialize"): "domain-action-request-materialize",
    ("runtime", "domain-owner-action-dispatch"): "domain-owner-action-dispatch",
    ("runtime", "domain-owner-action-refresh-controller-decisions"): "domain-owner-action-refresh-controller-decisions",
    ("runtime", "paper-autonomy-stability-evidence"): "paper-autonomy-stability-evidence",
    ("runtime", "workspace-monolith-migrate"): "workspace-monolith-migrate",
    ("runtime", "legacy-ds-retire"): "legacy-ds-retire",
    ("runtime", "paper-authority-clean-migration"): "paper-authority-clean-migration",
    ("runtime", "paper-clean-room-rebuild"): "paper-clean-room-rebuild",
    ("runtime", "study-workspace-status"): "study-workspace-status",
    ("runtime", "study-config-clean-migration"): "study-config-clean-migration",
    ("runtime", "ensure-analysis-bundle"): "ensure-analysis-bundle",
    ("runtime", "maintain-storage"): "maintain-runtime-storage",
    ("runtime", "storage-audit"): "workspace-storage-audit",
    ("runtime", "overlay-status"): "overlay-status",
    ("runtime", "install-overlay"): "install-medical-overlay",
    ("runtime", "reapply-overlay"): "reapply-medical-overlay",
    ("study", "progress"): "study-progress",
    ("study", "workspace-status"): "study-workspace-status",
    ("study", "open-auto-research-soak"): "open-auto-research-soak",
    ("study", "reconcile-truth"): "reconcile-study-truth",
    ("study", "profile-cycle"): "study-profile-cycle",
    ("study", "quality-repair-batch"): "quality-repair-batch",
    ("study", "light-advisory-materialize"): "light-advisory-materialize",
    ("study", "paper-story-repair"): "paper-story-repair",
    ("study", "gate-clearing-batch"): "gate-clearing-batch",
    ("study", "real-paper-autonomy-soak-projection"): "real-paper-autonomy-soak-projection",
    ("study", "launch"): "launch-study",
    ("study", "submit-task"): "submit-study-task",
    ("study", "resolve-reference-papers"): "resolve-reference-papers",
    ("study", "delivery-sync"): "sync-study-delivery",
    ("publication", "export-submission-minimal"): "export-submission-minimal",
    ("publication", "export-inspection-package"): "export-inspection-package",
    ("publication", "materialize-display-surface"): "materialize-display-surface",
    ("publication", "sync-display-pack"): "sync-display-pack-surface",
    ("publication", "display-pack-agent-discover"): "display-pack-agent-discover",
    ("publication", "display-pack-agent-plan"): "display-pack-agent-plan",
    ("publication", "display-pack-agent-preflight"): "display-pack-agent-preflight",
    ("publication", "display-pack-agent-render"): "display-pack-agent-render",
    ("publication", "display-pack-templates"): "display-pack-list-templates",
    ("publication", "display-pack-template"): "display-pack-describe-template",
    ("publication", "display-pack-scaffold-render"): "display-pack-scaffold-render",
    ("publication", "display-pack-golden"): "display-pack-golden",
    ("publication", "display-pack-e2e"): "display-pack-e2e",
    ("publication", "display-pack-render-candidate"): "display-pack-render-candidate",
    ("publication", "time-to-event-migration"): "time-to-event-direct-migration",
    ("publication", "resolve-targets"): "resolve-submission-targets",
    ("publication", "resolve-journal-shortlist"): "resolve-journal-shortlist",
    ("publication", "resolve-journal-requirements"): "resolve-journal-requirements",
    ("publication", "materialize-journal-package"): "materialize-journal-package",
    ("publication", "export-targets"): "export-submission-targets",
    ("publication", "delivery-inspect"): "delivery-inspect",
    ("publication", "gate"): "publication-gate",
    ("publication", "aftercare-plan"): "publication-aftercare-plan",
    ("publication", "clean-authority-migration"): "paper-authority-clean-migration",
    ("publication", "clean-room-rebuild"): "paper-clean-room-rebuild",
    ("publication", "study-workspace-status"): "study-workspace-status",
    ("publication", "materialize-ai-reviewer-eval"): "materialize-ai-reviewer-publication-eval",
    ("publication", "materialize-ai-reviewer-record"): "materialize-ai-reviewer-publication-eval-record",
    ("publication", "materialize-ai-medical-prose-review"): "materialize-ai-medical-prose-review",
    ("publication", "literature-audit"): "medical-literature-audit",
    ("publication", "reporting-audit"): "medical-reporting-audit",
    ("publication", "surface"): "medical-publication-surface",
    ("publication", "figure-loop-guard"): "figure-loop-guard",
    ("publication", "route-memory-inventory"): "publication-route-memory-inventory",
    ("product", "governance-report"): "storage-governance-report",
    ("product", "backfill-apply"): "delivery-authority-backfill-apply",
    ("product", "authority-migration-audit"): "workspace-authority-migration-audit",
    ("product", "artifact-lifecycle-report"): "artifact-lifecycle-report",
    ("product", "artifact-lifecycle-soak-summary"): "artifact-lifecycle-continuous-soak-summary",
}

GROUPED_COMMAND_NAMES = {group for group, _ in GROUPED_COMMAND_ALIASES}
GROUPED_COMMAND_PROGS = {
    flat_command: f"medautosci {group} {subcommand}"
    for (group, subcommand), flat_command in GROUPED_COMMAND_ALIASES.items()
}
GROUPED_COMMAND_SUMMARIES: dict[str, str] = {
    **grouped_command_summaries(),
    "doctor": "doctor 审计、profile、mainline 与 stage-route contract 检查。",
    "workspace": "workspace 初始化与 data/literature readiness。",
    "data": "研究资产、public data、registry 与 literature/memory 准备。",
    "runtime": "domain health diagnostic、domain owner handoff 与 overlay。",
    "study": "progress、launch 与 delivery sync。",
    "publication": "投稿包、display surface、journal/target 与 publication gate。",
    "product": "authority governance、backfill 与 artifact lifecycle surfaces。",
}
GROUPED_SUBCOMMANDS: dict[str, tuple[str, ...]] = {
    group: tuple(subcommand for candidate_group, subcommand in GROUPED_COMMAND_ALIASES if candidate_group == group)
    for group in GROUPED_COMMAND_NAMES
}


def print_public_help() -> None:
    lines = [
        "Usage: medautosci <group> <command> [options]",
        *PUBLIC_HELP_LINES,
        "",
        "Public command groups:",
    ]
    for group in (FOUNDRY_GROUP, "doctor", "workspace", "data", "runtime", "study", "publication", "product"):
        lines.append(f"  {group:<12}{GROUPED_COMMAND_SUMMARIES[group]}")
    lines.extend(
        [
            "",
            "Examples:",
            "  medautosci foundry status --json",
            "  medautosci foundry interfaces --json",
            "  medautosci status --json",
            "  medautosci doctor report --profile <profile>",
            "  medautosci study progress --profile <profile> --study-id <study_id>",
            "  medautosci product governance-report --workspace-root <workspace>",
        ]
    )
    print("\n".join(lines))


def print_group_help(group: str) -> None:
    lines = [
        f"Usage: medautosci {group} <command> [options]",
        "",
        GROUPED_COMMAND_SUMMARIES[group],
        "",
        "Commands:",
    ]
    for subcommand in GROUPED_SUBCOMMANDS[group]:
        lines.append(f"  {subcommand}")
    print("\n".join(lines))


def maybe_handle_public_help(argv: list[str]) -> int | None:
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print_public_help()
        return 0
    if argv[0] in GROUPED_COMMAND_NAMES and (len(argv) == 1 or argv[1] in {"-h", "--help", "help"}):
        print_group_help(argv[0])
        return 0
    return None


def normalize_public_command_argv(argv: list[str] | None) -> list[str] | None:
    if argv is None:
        return None
    if not argv:
        return argv

    argv = normalize_foundry_argv(argv)

    if len(argv) >= 2 and (argv[0], argv[1]) in GROUPED_COMMAND_ALIASES:
        return [GROUPED_COMMAND_ALIASES[(argv[0], argv[1])], *argv[2:]]

    if argv[0] in FOUNDRY_TOP_LEVEL_ALIASES:
        return [f"foundry-{argv[0]}", *argv[1:]]

    if argv[0] in GROUPED_COMMAND_NAMES:
        raise SystemExit(f"Grouped command requires a supported subcommand under `{argv[0]}`.")

    return argv
