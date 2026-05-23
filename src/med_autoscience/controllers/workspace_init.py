from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess

from med_autoscience.controllers import portfolio_memory as portfolio_memory_controller
from med_autoscience.controllers import workspace_entry_rendering as workspace_entry_rendering_controller
from med_autoscience.controllers import workspace_literature as workspace_literature_controller
from med_autoscience.controllers.workspace_agents_template import render_workspace_agents
from med_autoscience.controllers.workspace_git_boundary import (
    ensure_workspace_git,
    is_workspace_gitignore_path,
    merge_workspace_gitignore_content,
    render_workspace_gitignore,
    workspace_git_plan,
)
from med_autoscience.controllers.workspace_init_parts.shell_rendering import (
    _render_behavior_equivalence_gate,
    _render_forward_script,
    _render_mas_runtime_bridge_forward,
    _render_mas_runtime_bridge_shared,
    _render_mas_runtime_bridge_show_config,
    _render_mas_runtime_bridge_stop_script,
    _render_medautosci_shared,
    _render_progress_portal_start_web_script,
    _render_profile_optional_forward_script,
    _render_materialize_domain_action_requests_script,
    _render_progress_projection_script,
    _render_supervisor_execute_dispatch_script,
    _render_scan_domain_routes_script,
    _render_domain_health_diagnostic_script,
)
from med_autoscience.controllers.workspace_init_parts.retired_entries import (
    retired_file_cleanup_reason,
    retired_workspace_service_paths,
)
from med_autoscience.controllers.workspace_init_parts.legacy_entries import legacy_managed_runtime_entry_reason
from med_autoscience.controllers.workspace_init_parts.profile_config import (
    merge_medautoscience_config_content,
    merge_workspace_profile_content,
    render_workspace_profile_entries,
)
from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.policies.controller_first import render_controller_first_summary
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout


@dataclass(frozen=True)
class RenderedFile:
    path: Path
    content: str
    executable: bool = False


def _slugify_workspace_name(workspace_name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", workspace_name.strip()).strip("-").lower()
    return normalized or "workspace"


def _profile_filename(workspace_name: str) -> str:
    return f"{_slugify_workspace_name(workspace_name)}.local.toml"


def _display_path_from_workspace_root(*, workspace_root: Path, target_path: Path) -> Path:
    try:
        return target_path.relative_to(workspace_root)
    except ValueError:
        return target_path


def _configured_medautoscience_profile_path(workspace_root: Path) -> Path | None:
    config_env_path = workspace_root / "ops" / "medautoscience" / "config.env"
    if not config_env_path.is_file():
        return None
    try:
        content = config_env_path.read_text(encoding="utf-8")
    except OSError:
        return None
    prefix = "MED_AUTOSCIENCE_PROFILE="
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.startswith(prefix):
            continue
        raw_value = stripped[len(prefix) :].strip()
        if not raw_value:
            return None
        if raw_value[0] in {'"', "'"} and raw_value[-1] == raw_value[0]:
            raw_value = raw_value[1:-1]
        candidate = Path(raw_value).expanduser()
        if not candidate.is_absolute():
            candidate = workspace_root / candidate
        return candidate.resolve()
    return None


def _workspace_profile_path(*, workspace_root: Path, workspace_name: str) -> Path:
    configured_path = _configured_medautoscience_profile_path(workspace_root)
    if configured_path is not None:
        return configured_path
    return (workspace_root / "ops" / "medautoscience" / "profiles" / _profile_filename(workspace_name)).resolve()


def _workspace_directories(workspace_root: Path) -> list[Path]:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    return [
        workspace_root / "datasets",
        workspace_root / "contracts",
        workspace_root / "studies",
        workspace_root / "portfolio" / "data_assets",
        workspace_root / "portfolio" / "research_memory",
        workspace_root / "portfolio" / "research_memory" / "literature",
        workspace_root / "portfolio" / "research_memory" / "literature" / "coverage",
        workspace_root / "portfolio" / "research_memory" / "prompts",
        workspace_root / "portfolio" / "research_memory" / "external_reports",
        workspace_root / "refs",
        workspace_root / "ops" / "medautoscience" / "bin",
        workspace_root / "ops" / "medautoscience" / "logs",
        workspace_root / "ops" / "medautoscience" / "profiles",
        workspace_root / "ops" / "mas" / "progress",
        layout.bin_root,
        layout.runtime_root,
        layout.quests_root,
        layout.archives_root,
        layout.restore_index_root,
        layout.runtime_artifacts_root,
        layout.runtime_artifacts_root / "progress_portal",
        layout.startup_briefs_root,
        layout.startup_payloads_root,
    ]


def _render_workspace_readme(*, workspace_name: str, profile_relpath: Path) -> str:
    return (
        f"# {workspace_name} Research Workspace\n\n"
        "这个 workspace 由 `medautosci init-workspace` 初始化。\n\n"
        "它默认是病种级工作区，而不是单篇论文目录，负责管理：\n\n"
        "- 共享数据底座\n"
        "- 多条 study 研究线\n"
        "- 稿件与投稿交付物\n\n"
        "## 下一步\n\n"
        "1. 整理原始数据、变量定义、终点定义和参考资料。\n"
        f"2. 编辑 `{profile_relpath.as_posix()}`，补全 publication profile、citation style 与 workspace 路径信息。\n"
        "3. 编辑 `ops/medautoscience/config.env`，设置共享 `MedAutoScience` 仓库路径。\n"
        "4. `ops/mas/config.env` 是 MAS domain refs bridge 配置面，默认不需要外部 MDS launcher。\n"
        "5. 运行 `ops/medautoscience/bin/show-profile` 和 `ops/medautoscience/bin/bootstrap`。\n"
        "6. 通过 OPL stage 控制面提交或恢复正式研究流程；MAS workspace 只暴露 domain authority refs 与只读进度入口。\n\n"
        "7. 运行 `ops/medautoscience/bin/progress-portal` 刷新固定进度入口，然后打开 `ops/mas/progress/index.html` 查看当前进度。\n\n"
        "8. 如需查看 stage attempt、provider、terminal/log stream 与 retry/dead-letter 状态，读取 OPL current_control_state；MAS 不生成私有 runtime console 或 runtime read model。\n\n"
        "9. 如需检查 MAS domain health，运行 `medautosci runtime domain-health-diagnostic --runtime-root <runtime_root>`；stage/runtime lifecycle 只读 OPL current_control_state refs-only handoff。\n\n"
        "10. 阅读 `WORKSPACE_AUTOSCIENCE_RULES.md`，确认 controller-first 与 automation-ready 默认约束。\n\n"
        "11. 优先维护 `portfolio/research_memory/`，把疾病热点、课题地图与期刊邻域沉淀为可复用研究资产。\n\n"
        "12. 如需额外外部视角，使用 `ops/medautoscience/bin/prepare-external-research` 准备 prompt；它是 optional enrichment，不是启动门。\n\n"
        "## Runtime Boundary\n\n"
        "- `MedAutoScience` 是研究入口与治理层。\n"
        "- `runtime/` 保存运行态，`artifacts/runtime/` 保存 SQLite refs index 与维护 ledger，`ops/mas/` 只保留薄运维桥。\n"
        "- 不要直接通过外部后端 UI、CLI 或 daemon HTTP API 发起研究 quest。\n"
        "- 如果需要启动、查看或停止 runtime，必须走 OPL stage/runtime 控制面；MAS 不提供私有 scheduler、runner、attempt 或 runtime console 入口。\n"
    )


def _render_workspace_agents(*, workspace_name: str) -> str:
    return render_workspace_agents(workspace_name=workspace_name)


def _render_progress_portal_placeholder() -> str:
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "  <title>MedAutoScience Progress Portal</title>\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        "    <h1>MedAutoScience Progress Portal</h1>\n"
        "    <p>进度快照尚未生成。运行 <code>ops/medautoscience/bin/progress-portal</code> 刷新此入口。</p>\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def _render_workspace_rules() -> str:
    controller_first_summary = render_controller_first_summary()
    automation_ready_summary = render_automation_ready_summary()
    return (
        "# Workspace Autoscience Rules\n\n"
        "这个文件由 `medautosci init-workspace` 自动生成，用于声明新 workspace 默认继承的运行约束。\n\n"
        "## Controller-First Default\n\n"
        "- 优先复用 MedAutoScience 已覆盖的成熟 controller / CLI / overlay skill。\n"
        "- 不要在已有平台能力覆盖的任务上自由发挥或发明平行流程。\n"
        f"- {controller_first_summary}\n\n"
        "## Automation-Ready Default\n\n"
        "- 边界明确且 startup-ready 后，默认切入 MAS-owned managed runtime 的自动持续推进。\n"
        "- 不要在已经满足自动推进条件的 study 上持续停留在碎片化人工交互。\n"
        "- 必须显式通知用户自动驾驶已启动或已被检测到，并提供监督入口。\n"
        "- 一旦检测到 live managed runtime，前台必须立即进入 supervisor-only 监管态。\n"
        "- live managed runtime 的默认 cadence / wakeup / provider SLO 由 OPL provider/runtime manager 承载；MAS 只暴露 `ops/medautoscience/bin/domain-health-diagnostic` 这种 one-shot domain diagnostic 入口；`local` 已物理退役为 tombstone/provenance-only。Hermes gateway cron 只在显式 status/remove 时作为 legacy diagnostic cleanup adapter。\n"
        "- 不得直接写入 runtime-owned 的 study / quest / paper surface；如需人工接管，先显式暂停 runtime。\n"
        "- 只要 `publication_supervisor_state.bundle_tasks_downstream_only = true`，就把 bundle/build/proofing 视为硬阻断，不得抢跑。\n"
        f"- {automation_ready_summary}\n"
    )


def _medautoscience_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _render_workspace_pyproject(*, workspace_root: Path, workspace_name: str) -> str:
    repo_relpath = Path(os.path.relpath(_medautoscience_repo_root(), workspace_root)).as_posix()
    project_name = f"{_slugify_workspace_name(workspace_name)}-workspace"
    return (
        "[project]\n"
        f'name = "{project_name}"\n'
        'version = "0.1.0"\n'
        f'description = "Managed Python environment for the {workspace_name} workspace."\n'
        'requires-python = ">=3.12,<3.13"\n'
        "dependencies = [\n"
        '  "med-autoscience[analysis]",\n'
        "]\n\n"
        "[dependency-groups]\n"
        "dev = [\n"
        '  "pytest>=9,<10",\n'
        "]\n\n"
        "[tool.uv]\n"
        'default-groups = ["dev"]\n\n'
        "[tool.uv.sources]\n"
        f'med-autoscience = {{ path = "{repo_relpath}", editable = true }}\n'
    )


def _detect_github_username() -> str | None:
    env_login = os.environ.get("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN")
    if env_login and env_login.strip():
        return env_login.strip()
    if shutil.which("gh") is None:
        return None
    try:
        completed = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    login = completed.stdout.strip()
    return login or None


def _render_workspace_profile(
    *,
    workspace_root: Path,
    workspace_name: str,
    default_publication_profile: str,
    default_citation_style: str,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None,
    include_hermes_placeholders: bool,
) -> str:
    entries = render_workspace_profile_entries(
        workspace_root=workspace_root,
        workspace_name=workspace_name,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        hermes_agent_repo_root=hermes_agent_repo_root,
        hermes_home_root=hermes_home_root,
        include_hermes_placeholders=include_hermes_placeholders,
        github_username=_detect_github_username(),
    )
    return "\n".join(line for _, line in entries) + "\n"


def _is_workspace_profile_path(path: Path) -> bool:
    return len(path.parts) >= 4 and path.parts[-4:-1] == ("ops", "medautoscience", "profiles") and path.suffix == ".toml"


def _is_medautoscience_config_path(path: Path) -> bool:
    return len(path.parts) >= 3 and path.parts[-3:] == ("ops", "medautoscience", "config.env")


def _rendered_file_action(item: RenderedFile, *, force: bool) -> str:
    if not item.path.exists():
        return "create"
    if force:
        return "overwrite"
    try:
        existing_content = item.path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "skip"
    if legacy_managed_runtime_entry_reason(path=item.path, existing_content=existing_content) is not None:
        return "upgrade"
    if _is_workspace_profile_path(item.path) and existing_content != item.content:
        return "upgrade"
    if _is_medautoscience_config_path(item.path) and existing_content != item.content:
        return "upgrade"
    if is_workspace_gitignore_path(item.path) and existing_content != item.content:
        return "upgrade"
    return "skip"


def _rendered_files(
    *,
    workspace_root: Path,
    workspace_name: str,
    profile_path: Path,
    default_publication_profile: str,
    default_citation_style: str,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None,
) -> list[RenderedFile]:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    profile_relpath = _display_path_from_workspace_root(workspace_root=workspace_root, target_path=profile_path)
    files = [
        RenderedFile(
            path=workspace_root / ".gitignore",
            content=render_workspace_gitignore(),
        ),
        RenderedFile(
            path=workspace_root / "pyproject.toml",
            content=_render_workspace_pyproject(workspace_root=workspace_root, workspace_name=workspace_name),
        ),
        RenderedFile(
            path=workspace_root / "README.md",
            content=_render_workspace_readme(workspace_name=workspace_name, profile_relpath=profile_relpath),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "mas" / "progress" / "index.html",
            content=_render_progress_portal_placeholder(),
        ),
        RenderedFile(
            path=workspace_root / "AGENTS.md",
            content=_render_workspace_agents(workspace_name=workspace_name),
        ),
        RenderedFile(
            path=workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md",
            content=_render_workspace_rules(),
        ),
        RenderedFile(
            path=profile_path,
            content=_render_workspace_profile(
                workspace_root=workspace_root,
                workspace_name=workspace_name,
                default_publication_profile=default_publication_profile,
                default_citation_style=default_citation_style,
                hermes_agent_repo_root=hermes_agent_repo_root,
                hermes_home_root=hermes_home_root,
                include_hermes_placeholders=True,
            ),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "config.env",
            content=workspace_entry_rendering_controller.render_medautoscience_config(
                workspace_root=workspace_root,
                profile_relpath=profile_relpath,
            ),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "config.env.example",
            content=workspace_entry_rendering_controller.render_medautoscience_config(
                workspace_root=workspace_root,
                profile_relpath=profile_relpath,
            ),
        ),
        RenderedFile(
            path=layout.config_env_path,
            content=workspace_entry_rendering_controller.render_mas_runtime_bridge_config(),
        ),
        RenderedFile(
            path=layout.config_env_example_path,
            content=workspace_entry_rendering_controller.render_mas_runtime_bridge_config(),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "README.md",
            content=workspace_entry_rendering_controller.render_medautoscience_readme(profile_relpath=profile_relpath),
        ),
        RenderedFile(
            path=layout.readme_path,
            content=workspace_entry_rendering_controller.render_mas_runtime_bridge_readme(),
        ),
        RenderedFile(
            path=layout.behavior_gate_path,
            content=_render_behavior_equivalence_gate(),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh",
            content=_render_medautosci_shared(profile_relpath),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "bootstrap",
            content=_render_forward_script("workspace bootstrap", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "show-profile",
            content=_render_forward_script("doctor profile", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "enter-study",
            content=_render_forward_script("launch-study", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "progress-projection",
            content=_render_progress_projection_script(),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "domain-health-diagnostic",
            content=_render_domain_health_diagnostic_script(workspace_root=workspace_root, runtime_quests_root=layout.quests_root),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "owner-route-reconcile",
            content=_render_scan_domain_routes_script(),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "domain-action-request-materialize",
            content=_render_materialize_domain_action_requests_script(),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "domain-owner-action-dispatch",
            content=_render_supervisor_execute_dispatch_script(),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "maintain-runtime-storage",
            content=_render_forward_script("runtime maintain-storage", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "storage-audit",
            content=_render_forward_script("runtime storage-audit", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "progress-portal",
            content=_render_forward_script("progress-portal", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "publication-gate",
            content=_render_forward_script("publication gate"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "medical-surface",
            content=_render_forward_script("publication surface"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "figure-loop-guard",
            content=_render_forward_script("publication figure-loop-guard"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "resolve-submission-targets",
            content=_render_profile_optional_forward_script("publication resolve-targets"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "resolve-journal-shortlist",
            content=_render_forward_script("publication resolve-journal-shortlist"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory",
            content=_render_forward_script("data init-memory"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "portfolio-memory-status",
            content=_render_forward_script("data memory-status"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "init-workspace-literature",
            content=_render_forward_script("data init-literature"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "workspace-literature-status",
            content=_render_forward_script("data literature-status"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research",
            content=_render_forward_script("data prepare-external-research"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "external-research-status",
            content=_render_forward_script("data external-research-status"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "export-submission",
            content=_render_profile_optional_forward_script("publication export-targets"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "sync-delivery",
            content=_render_forward_script("study delivery-sync"),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "_shared.sh",
            content=_render_mas_runtime_bridge_shared(),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "doctor",
            content=_render_mas_runtime_bridge_forward("doctor report"),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "show-config",
            content=_render_mas_runtime_bridge_show_config(),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "start-web",
            content=_render_progress_portal_start_web_script(),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "status",
            content=_render_mas_runtime_bridge_forward("workspace cockpit", command_suffix=" --format json"),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "stop",
            content=_render_mas_runtime_bridge_stop_script(),
            executable=True,
        ),
    ]
    for item in portfolio_memory_controller.render_portfolio_memory_files(workspace_root=workspace_root):
        files.append(RenderedFile(path=item.path, content=item.content))
    for item in workspace_literature_controller.render_workspace_literature_files(workspace_root=workspace_root):
        files.append(RenderedFile(path=item.path, content=item.content))
    return files


def init_workspace(
    *,
    workspace_root: Path,
    workspace_name: str,
    dry_run: bool = False,
    force: bool = False,
    default_publication_profile: str = "general_medical_journal",
    default_citation_style: str = "AMA",
    hermes_agent_repo_root: Path | None = None,
    hermes_home_root: Path | None = None,
    initialize_git: bool = False,
) -> dict[str, object]:
    workspace_root = workspace_root.expanduser().resolve()
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    profile_path = _workspace_profile_path(workspace_root=workspace_root, workspace_name=workspace_name)
    directories = _workspace_directories(workspace_root)
    files = _rendered_files(
        workspace_root=workspace_root,
        workspace_name=workspace_name,
        profile_path=profile_path,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        hermes_agent_repo_root=hermes_agent_repo_root,
        hermes_home_root=hermes_home_root,
    )
    if not force:
        prepared_files: list[RenderedFile] = []
        for item in files:
            if item.path == profile_path and item.path.exists():
                try:
                    existing_content = item.path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    prepared_files.append(item)
                    continue
                prepared_files.append(
                    RenderedFile(
                        path=item.path,
                        content=merge_workspace_profile_content(
                            existing_content=existing_content,
                            workspace_root=workspace_root,
                            workspace_name=workspace_name,
                            default_publication_profile=default_publication_profile,
                            default_citation_style=default_citation_style,
                            hermes_agent_repo_root=hermes_agent_repo_root,
                            hermes_home_root=hermes_home_root,
                            github_username=_detect_github_username(),
                        ),
                        executable=item.executable,
                    )
                )
                continue
            if _is_medautoscience_config_path(item.path) and item.path.exists():
                try:
                    existing_content = item.path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    prepared_files.append(item)
                    continue
                prepared_files.append(
                    RenderedFile(
                        path=item.path,
                        content=merge_medautoscience_config_content(
                            existing_content=existing_content,
                            workspace_root=workspace_root,
                            profile_relpath=_display_path_from_workspace_root(
                                workspace_root=workspace_root,
                                target_path=profile_path,
                            ),
                        ),
                        executable=item.executable,
                    )
                )
                continue
            if is_workspace_gitignore_path(item.path) and item.path.exists():
                try:
                    existing_content = item.path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    prepared_files.append(item)
                    continue
                prepared_files.append(
                    RenderedFile(
                        path=item.path,
                        content=merge_workspace_gitignore_content(existing_content),
                        executable=item.executable,
                    )
                )
                continue
            prepared_files.append(item)
        files = prepared_files

    created_directories: list[str] = []
    created_files: list[str] = []
    skipped_files: list[str] = []
    overwritten_files: list[str] = []
    upgraded_files: list[str] = []
    removed_files: list[str] = []
    retained_retired_files: list[str] = []
    retired_service_paths = retired_workspace_service_paths(workspace_root)

    if dry_run:
        created_directories = [str(path) for path in directories if not path.exists()]
        for path in retired_service_paths:
            reason = retired_file_cleanup_reason(path)
            if reason is not None:
                removed_files.append(str(path))
            elif path.exists():
                retained_retired_files.append(str(path))
        for item in files:
            action = _rendered_file_action(item, force=force)
            if action == "create":
                created_files.append(str(item.path))
            elif action == "overwrite":
                overwritten_files.append(str(item.path))
            elif action == "upgrade":
                upgraded_files.append(str(item.path))
            else:
                skipped_files.append(str(item.path))
        workspace_git = workspace_git_plan(workspace_root=workspace_root, initialize_git=initialize_git, dry_run=True)
    else:
        for path in directories:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created_directories.append(str(path))
        for path in retired_service_paths:
            reason = retired_file_cleanup_reason(path)
            if reason is not None:
                path.unlink()
                removed_files.append(str(path))
            elif path.exists():
                retained_retired_files.append(str(path))
        for item in files:
            action = _rendered_file_action(item, force=force)
            if action == "skip":
                skipped_files.append(str(item.path))
                continue
            item.path.parent.mkdir(parents=True, exist_ok=True)
            if action == "overwrite":
                overwritten_files.append(str(item.path))
            elif action == "upgrade":
                upgraded_files.append(str(item.path))
            else:
                created_files.append(str(item.path))
            item.path.write_text(item.content, encoding="utf-8")
            if item.executable:
                item.path.chmod(item.path.stat().st_mode | 0o111)
        workspace_git = ensure_workspace_git(workspace_root=workspace_root, initialize_git=initialize_git)

    return {
        "workspace_root": str(workspace_root),
        "workspace_name": workspace_name,
        "dry_run": dry_run,
        "force": force,
        "created_directories": created_directories,
        "created_files": created_files,
        "skipped_files": skipped_files,
        "overwritten_files": overwritten_files,
        "upgraded_files": upgraded_files,
        "removed_files": removed_files,
        "retained_retired_files": retained_retired_files,
        "workspace_git": workspace_git,
        "profile_path": str(profile_path),
        "next_steps": [
            f"edit {workspace_root / 'ops' / 'medautoscience' / 'config.env'}",
            f"review {profile_path}",
            f"run {workspace_root / 'ops' / 'medautoscience' / 'bin' / 'show-profile'}",
            f"run {workspace_root / 'ops' / 'medautoscience' / 'bin' / 'bootstrap'}",
            f"run {workspace_root / 'ops' / 'medautoscience' / 'bin' / 'progress-portal'}",
            f"open {workspace_root / 'ops' / 'mas' / 'progress' / 'index.html'}",
        ],
    }
