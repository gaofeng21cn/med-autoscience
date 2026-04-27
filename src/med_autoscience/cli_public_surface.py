from __future__ import annotations


GROUPED_COMMAND_ALIASES: dict[tuple[str, str], str] = {
    ("doctor", "report"): "doctor",
    ("doctor", "profile"): "show-profile",
    ("doctor", "mainline-status"): "mainline-status",
    ("doctor", "mainline-phase"): "mainline-phase",
    ("doctor", "entry-modes"): "show-agent-entry-modes",
    ("doctor", "sync-entry-assets"): "sync-agent-entry-assets",
    ("doctor", "preflight"): "preflight-changes",
    ("doctor", "backend-upgrade"): "backend-upgrade-check",
    ("doctor", "hermes-runtime"): "hermes-runtime-check",
    ("workspace", "bootstrap"): "bootstrap",
    ("workspace", "init"): "init-workspace",
    ("workspace", "cockpit"): "workspace-cockpit",
    ("workspace", "profile-cycles"): "workspace-profile-cycles",
    ("data", "init-assets"): "init-data-assets",
    ("data", "assets-status"): "data-assets-status",
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
    ("runtime", "watch"): "watch",
    ("runtime", "supervision-status"): "runtime-supervision-status",
    ("runtime", "ensure-supervision"): "runtime-ensure-supervision",
    ("runtime", "remove-supervision"): "runtime-remove-supervision",
    ("runtime", "maintain-storage"): "runtime-maintain-storage",
    ("runtime", "overlay-status"): "overlay-status",
    ("runtime", "install-overlay"): "install-medical-overlay",
    ("runtime", "reapply-overlay"): "reapply-medical-overlay",
    ("runtime", "ensure-analysis-bundle"): "ensure-study-runtime-analysis-bundle",
    ("study", "ensure-runtime"): "ensure-study-runtime",
    ("study", "progress"): "study-progress",
    ("study", "profile-cycle"): "study-profile-cycle",
    ("study", "quality-repair-batch"): "quality-repair-batch",
    ("study", "launch"): "launch-study",
    ("study", "submit-task"): "submit-study-task",
    ("study", "resolve-reference-papers"): "resolve-reference-papers",
    ("study", "delivery-sync"): "sync-study-delivery",
    ("publication", "export-submission-minimal"): "export-submission-minimal",
    ("publication", "materialize-display-surface"): "materialize-display-surface",
    ("publication", "sync-display-pack"): "sync-display-pack-surface",
    ("publication", "time-to-event-migration"): "time-to-event-direct-migration",
    ("publication", "resolve-targets"): "resolve-submission-targets",
    ("publication", "resolve-journal-shortlist"): "resolve-journal-shortlist",
    ("publication", "resolve-journal-requirements"): "resolve-journal-requirements",
    ("publication", "materialize-journal-package"): "materialize-journal-package",
    ("publication", "export-targets"): "export-submission-targets",
    ("publication", "gate"): "publication-gate",
    ("publication", "materialize-ai-reviewer-eval"): "materialize-ai-reviewer-publication-eval",
    ("publication", "literature-audit"): "medical-literature-audit",
    ("publication", "reporting-audit"): "medical-reporting-audit",
    ("publication", "surface"): "medical-publication-surface",
    ("publication", "figure-loop-guard"): "figure-loop-guard",
    ("product", "frontdesk"): "product-frontdesk",
    ("product", "preflight"): "product-preflight",
    ("product", "start"): "product-start",
    ("product", "manifest"): "product-entry-manifest",
    ("product", "skill-catalog"): "skill-catalog",
    ("product", "build-entry"): "build-product-entry",
}

GROUPED_COMMAND_NAMES = {group for group, _ in GROUPED_COMMAND_ALIASES}
GROUPED_COMMAND_PROGS = {
    flat_command: f"medautosci {group} {subcommand}"
    for (group, subcommand), flat_command in GROUPED_COMMAND_ALIASES.items()
}
GROUPED_COMMAND_SUMMARIES: dict[str, str] = {
    "doctor": "doctor 审计、profile、mainline 与 entry-mode 检查。",
    "workspace": "workspace 初始化与 readiness cockpit。",
    "data": "研究资产、public data、registry 与 literature/memory 准备。",
    "runtime": "runtime watch、Hermes supervision、overlay、analysis bundle 与 storage maintenance。",
    "study": "study runtime、progress、launch 与 delivery sync。",
    "publication": "投稿包、display surface、journal/target 与 publication gate。",
    "product": "frontdesk、preflight、start、manifest 与 build-entry。",
}
GROUPED_SUBCOMMANDS: dict[str, tuple[str, ...]] = {
    group: tuple(subcommand for candidate_group, subcommand in GROUPED_COMMAND_ALIASES if candidate_group == group)
    for group in GROUPED_COMMAND_NAMES
}


def print_public_help() -> None:
    lines = [
        "Usage: medautosci <group> <command> [options]",
        "",
        "Public command groups:",
    ]
    for group in ("doctor", "workspace", "data", "runtime", "study", "publication", "product"):
        lines.append(f"  {group:<12}{GROUPED_COMMAND_SUMMARIES[group]}")
    lines.extend(
        [
            "",
            "Examples:",
            "  medautosci doctor report --profile <profile>",
            "  medautosci study progress --profile <profile> --study-id <study_id>",
            "  medautosci product manifest --profile <profile> --study-id <study_id>",
            "  medautosci product skill-catalog --profile <profile> --format json",
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

    if len(argv) >= 2 and (argv[0], argv[1]) in GROUPED_COMMAND_ALIASES:
        return [GROUPED_COMMAND_ALIASES[(argv[0], argv[1])], *argv[2:]]

    if argv[0] in GROUPED_COMMAND_NAMES:
        raise SystemExit(f"Grouped command requires a supported subcommand under `{argv[0]}`.")

    return argv
