from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import json
import re
import tomllib

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
        layout.bin_root,
        layout.runtime_root,
        layout.quests_root,
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
        f"2. 编辑 `{profile_relpath.as_posix()}`，补全 publication profile 与 `med-deepscientist` repo 信息。\n"
        "3. 编辑 `ops/medautoscience/config.env`，设置共享 `MedAutoScience` 仓库路径。\n"
        "4. 编辑 `ops/med-deepscientist/config.env`，设置本机 `ds` launcher 路径。\n"
        "5. 运行 `ops/medautoscience/bin/show-profile` 和 `ops/medautoscience/bin/bootstrap`。\n"
        "6. 通过 `ops/medautoscience/bin/enter-study` 或 `ensure-study-runtime` 进入正式研究流程。\n\n"
        "7. 如需让 workspace 托管监管持续在线，运行 `ops/medautoscience/bin/install-watch-runtime-service`；后续用 `watch-runtime-service-status` / `uninstall-watch-runtime-service` 管理 Hermes-hosted supervision job。\n\n"
        "8. 阅读 `WORKSPACE_AUTOSCIENCE_RULES.md`，确认 controller-first 与 automation-ready 默认约束。\n\n"
        "9. 优先维护 `portfolio/research_memory/`，把疾病热点、课题地图与期刊邻域沉淀为可复用研究资产。\n\n"
        "10. 如需额外外部视角，使用 `ops/medautoscience/bin/prepare-external-research` 准备 prompt；它是 optional enrichment，不是启动门。\n\n"
        "## Runtime Boundary\n\n"
        "- `MedAutoScience` 是研究入口与治理层。\n"
        "- `ops/med-deepscientist/` 只保留 runtime 状态和运维脚本。\n"
        "- 不要直接通过 `med-deepscientist` UI、CLI 或 daemon HTTP API 发起研究 quest。\n"
        "- 如果需要启动、查看或停止 runtime，只把 `ops/med-deepscientist/bin/*` 当作运维面，不把它当成研究入口。\n"
    )


def _render_workspace_agents(*, workspace_name: str) -> str:
    return render_workspace_agents(workspace_name=workspace_name)

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
        "- 边界明确且 startup-ready 后，默认切入 `Hermes-backed` managed runtime 的自动持续推进。\n"
        "- 不要在已经满足自动推进条件的 study 上持续停留在碎片化人工交互。\n"
        "- 必须显式通知用户自动驾驶已启动或已被检测到，并提供监督入口。\n"
        "- 一旦检测到 live managed runtime，前台必须立即进入 supervisor-only 监管态。\n"
        "- live managed runtime 需要持续在线的 Hermes-hosted supervision tick；默认由 Hermes gateway cron 托管 `ops/medautoscience/bin/watch-runtime` 的单次 tick，避免 supervisor tick 回落为 `stale`。\n"
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
        '  "med-autoscience",\n'
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


def _quote_toml_string(value: str | Path) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _render_workspace_profile_entries(
    *,
    workspace_root: Path,
    workspace_name: str,
    default_publication_profile: str,
    default_citation_style: str,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None,
    include_hermes_placeholders: bool,
) -> list[tuple[str, str]]:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    entries: list[tuple[str, str]] = [
        ("name", f"name = {_quote_toml_string(workspace_name)}"),
        ("workspace_root", f"workspace_root = {_quote_toml_string(workspace_root)}"),
        ("runtime_root", f"runtime_root = {_quote_toml_string(layout.quests_root)}"),
        ("studies_root", f"studies_root = {_quote_toml_string(workspace_root / 'studies')}"),
        ("portfolio_root", f"portfolio_root = {_quote_toml_string(workspace_root / 'portfolio')}"),
        (
            "med_deepscientist_runtime_root",
            f"med_deepscientist_runtime_root = {_quote_toml_string(layout.runtime_root)}",
        ),
        ("med_deepscientist_repo_root", 'med_deepscientist_repo_root = "/ABS/PATH/TO/med-deepscientist"'),
    ]
    if hermes_agent_repo_root is not None:
        entries.append(
            (
                "hermes_agent_repo_root",
                f"hermes_agent_repo_root = {_quote_toml_string(Path(hermes_agent_repo_root).expanduser().resolve())}",
            )
        )
        resolved_hermes_home_root = (
            Path(hermes_home_root).expanduser().resolve()
            if hermes_home_root is not None
            else (Path.home() / ".hermes").resolve()
        )
        entries.append(
            (
                "hermes_home_root",
                f"hermes_home_root = {_quote_toml_string(resolved_hermes_home_root)}",
            )
        )
    elif include_hermes_placeholders:
        entries.extend(
            [
                ("hermes_agent_repo_root", 'hermes_agent_repo_root = "/ABS/PATH/TO/hermes-agent"'),
                ("hermes_home_root", 'hermes_home_root = "~/.hermes"'),
            ]
        )
    entries.extend(
        [
            (
                "default_publication_profile",
                f"default_publication_profile = {_quote_toml_string(default_publication_profile)}",
            ),
            ("default_citation_style", f"default_citation_style = {_quote_toml_string(default_citation_style)}"),
            ("enable_medical_overlay", "enable_medical_overlay = true"),
            ("medical_overlay_scope", 'medical_overlay_scope = "workspace"'),
            (
                "medical_overlay_skills",
                'medical_overlay_skills = ["intake-audit", "scout", "baseline", "idea", "decision", "experiment", "analysis-campaign", "figure-polish", "write", "review", "rebuttal", "finalize"]',
            ),
            ("medical_overlay_bootstrap_mode", 'medical_overlay_bootstrap_mode = "ensure_ready"'),
            ("research_route_bias_policy", 'research_route_bias_policy = "high_plasticity_medical"'),
            (
                "preferred_study_archetypes",
                'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
            ),
            (
                "default_startup_anchor_policy",
                'default_startup_anchor_policy = "scout_first_for_continue_existing_state"',
            ),
            ("legacy_code_execution_policy", 'legacy_code_execution_policy = "forbid_without_user_approval"'),
            (
                "public_data_discovery_policy",
                'public_data_discovery_policy = "required_for_scout_route_selection"',
            ),
            (
                "startup_boundary_requirements",
                'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]',
            ),
        ]
    )
    return entries


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
    entries = _render_workspace_profile_entries(
        workspace_root=workspace_root,
        workspace_name=workspace_name,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        hermes_agent_repo_root=hermes_agent_repo_root,
        hermes_home_root=hermes_home_root,
        include_hermes_placeholders=include_hermes_placeholders,
    )
    return "\n".join(line for _, line in entries) + "\n"


def _render_behavior_equivalence_gate() -> str:
    return (
        "schema_version: v1\n"
        "phase_25_ready: true\n"
        "critical_overrides: []\n"
    )


def _render_medautosci_shared(profile_relpath: Path) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        f'DEFAULT_PROFILE="${{WORKSPACE_ROOT}}/{profile_relpath.as_posix()}"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'if [[ -n "${MED_AUTOSCIENCE_PROFILE:-}" ]]; then\n'
        '  PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE}"\n'
        "else\n"
        '  PROFILE_PATH="${DEFAULT_PROFILE}"\n'
        "fi\n\n"
        'if [[ -z "${MED_AUTOSCIENCE_REPO:-}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_REPO is not configured. Set it in ${CONFIG_ENV_PATH} or export it explicitly." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        'if [[ ! -f "${MED_AUTOSCIENCE_REPO_RESOLVED}/pyproject.toml" || ! -d "${MED_AUTOSCIENCE_REPO_RESOLVED}/src/med_autoscience" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_REPO does not point to a valid MedAutoScience checkout: ${MED_AUTOSCIENCE_REPO_RESOLVED}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -f "${PROFILE_PATH}" ]]; then\n'
        '  echo "Profile file not found: ${PROFILE_PATH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ${CONFIG_ENV_PATH} or install uv on PATH." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"\n'
        'if [[ -n "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '  if [[ "${MED_AUTOSCIENCE_RSCRIPT_BIN}" != /* ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN must be an absolute path: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  if [[ ! -x "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN is not executable: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "fi\n\n"
        'export MED_AUTOSCIENCE_RSCRIPT_BIN\n\n'
        'MED_AUTOSCIENCE_NODE_BIN="${MED_AUTOSCIENCE_NODE_BIN:-$(command -v node || true)}"\n'
        'if [[ -n "${MED_AUTOSCIENCE_NODE_BIN}" ]]; then\n'
        '  if [[ "${MED_AUTOSCIENCE_NODE_BIN}" != /* ]]; then\n'
        '    echo "MED_AUTOSCIENCE_NODE_BIN must be an absolute path: ${MED_AUTOSCIENCE_NODE_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  if [[ ! -x "${MED_AUTOSCIENCE_NODE_BIN}" ]]; then\n'
        '    echo "MED_AUTOSCIENCE_NODE_BIN is not executable: ${MED_AUTOSCIENCE_NODE_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "fi\n\n"
        'export MED_AUTOSCIENCE_NODE_BIN\n\n'
        "run_medautosci() {\n"
        '  "${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
        "}\n"
    )


def _render_forward_script(command: str, *, with_profile: bool = False) -> str:
    extra = f' --profile "${{PROFILE_PATH}}"' if with_profile else ""
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        f'run_medautosci {command}{extra} "$@"\n'
    )


def _render_profile_optional_forward_script(command: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'args=("$@")\n'
        "has_profile=0\n"
        'for arg in "${args[@]}"; do\n'
        '  if [[ "${arg}" == "--profile" ]]; then\n'
        "    has_profile=1\n"
        "    break\n"
        "  fi\n"
        "done\n\n"
        'if [[ "${has_profile}" -eq 1 ]]; then\n'
        f'  run_medautosci {command} "${{args[@]}}"\n'
        "else\n"
        f'  run_medautosci {command} --profile "${{PROFILE_PATH}}" "${{args[@]}}"\n'
        "fi\n"
    )


def _render_watch_runtime_script(*, runtime_quests_root: Path) -> str:
    relative_runtime_root = runtime_quests_root.relative_to(runtime_quests_root.parents[3]).as_posix()
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        f'WORKSPACE_RUNTIME_ROOT="${{WORKSPACE_ROOT}}/{relative_runtime_root}"\n\n'
        'run_medautosci runtime watch \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        '  --runtime-root "${WORKSPACE_RUNTIME_ROOT}" \\\n'
        '  --ensure-study-runtimes \\\n'
        '  --apply \\\n'
        '  --loop \\\n'
        '  "$@"\n'
    )


def _render_watch_runtime_service_runner() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_SCRIPT="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime"\n\n'
        'if [[ ! -x "${WATCH_RUNTIME_SCRIPT}" ]]; then\n'
        '  echo "watch-runtime entry is missing or not executable: ${WATCH_RUNTIME_SCRIPT}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'exec "${WATCH_RUNTIME_SCRIPT}" --interval-seconds "${WATCH_RUNTIME_INTERVAL_SECONDS}" "$@"\n'
    )


def _render_med_deepscientist_shared() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MED_DEEPSCIENTIST_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'MED_DEEPSCIENTIST_CONFIG_ENV_PATH="${MED_DEEPSCIENTIST_OPS_ROOT}/config.env"\n'
        'MEDAUTOSCI_SHARED_SH="${WORKSPACE_ROOT}/ops/medautoscience/bin/_shared.sh"\n\n'
        'if [[ ! -f "${MEDAUTOSCI_SHARED_SH}" ]]; then\n'
        '  echo "MedAutoScience shared entry is missing: ${MEDAUTOSCI_SHARED_SH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        "# shellcheck disable=SC1090\n"
        'source "${MEDAUTOSCI_SHARED_SH}"\n\n'
        'if [[ -f "${MED_DEEPSCIENTIST_CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${MED_DEEPSCIENTIST_CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'if [[ -z "${MED_DEEPSCIENTIST_LAUNCHER:-}" ]]; then\n'
        '  echo "MED_DEEPSCIENTIST_LAUNCHER is not configured. Set it in ${MED_DEEPSCIENTIST_CONFIG_ENV_PATH}." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_DEEPSCIENTIST_LAUNCHER}" != /* ]]; then\n'
        '  echo "MED_DEEPSCIENTIST_LAUNCHER must be an absolute path: ${MED_DEEPSCIENTIST_LAUNCHER}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_DEEPSCIENTIST_LAUNCHER}" ]]; then\n'
        '  echo "MED_DEEPSCIENTIST_LAUNCHER is not executable: ${MED_DEEPSCIENTIST_LAUNCHER}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        "load_med_deepscientist_contract() {\n"
        "  local payload_json\n"
        '  payload_json="$(\n'
        '    uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - "${PROFILE_PATH}" <<'"'"'PY'"'"'\n'
        "import json\n"
        "import sys\n\n"
        "from med_autoscience.profiles import load_profile, profile_to_dict\n"
        "from med_autoscience.workspace_contracts import inspect_workspace_contracts\n\n"
        "profile = load_profile(sys.argv[1])\n"
        "print(\n"
        "    json.dumps(\n"
        "        {\n"
        '            "profile": profile_to_dict(profile),\n'
        '            "contracts": inspect_workspace_contracts(profile),\n'
        "        },\n"
        "        ensure_ascii=False,\n"
        "    )\n"
        ")\n"
        "PY\n"
        '  )"\n\n'
        '  export MEDAUTOSCI_MED_DEEPSCIENTIST_CONTRACT_JSON="${payload_json}"\n\n'
        "  local contract_lines\n"
        '  contract_lines="$(\n'
        '    CONTRACT_JSON="${payload_json}" uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - <<'"'"'PY'"'"'\n'
        "import json\n"
        "import os\n\n"
        'payload = json.loads(os.environ["CONTRACT_JSON"])\n'
        'profile = payload["profile"]\n'
        'contracts = payload["contracts"]\n'
        'runtime_contract = contracts["runtime_contract"]\n'
        'launcher_contract = contracts["launcher_contract"]\n'
        'behavior_gate = contracts["behavior_gate"]\n\n'
        "pairs = {\n"
        '    "workspace_root": profile["workspace_root"],\n'
        '    "runtime_root": profile["runtime_root"],\n'
        '    "med_deepscientist_runtime_root": profile["med_deepscientist_runtime_root"],\n'
        '    "med_deepscientist_repo_root": profile.get("med_deepscientist_repo_root") or "",\n'
        '    "runtime_root_matches_med_deepscientist_runtime": str(\n'
        '        bool(runtime_contract.get("checks", {}).get("runtime_root_matches_med_deepscientist_runtime"))\n'
        '    ).lower(),\n'
        '    "runtime_contract_ready": str(bool(runtime_contract.get("ready"))).lower(),\n'
        '    "launcher_contract_ready": str(bool(launcher_contract.get("ready"))).lower(),\n'
        '    "phase_25_ready": str(bool(behavior_gate.get("phase_25_ready"))).lower(),\n'
        "}\n\n"
        "for key, value in pairs.items():\n"
        '    print(f"{key}\\t{value}")\n'
        "PY\n"
        '  )"\n\n'
        '  while IFS=$'"'"'\\t'"'"' read -r key value; do\n'
        '    case "${key}" in\n'
        '      workspace_root) MED_DEEPSCIENTIST_WORKSPACE_ROOT="${value}" ;;\n'
        '      runtime_root) MED_DEEPSCIENTIST_RUNTIME_ROOT="${value}" ;;\n'
        '      med_deepscientist_runtime_root) MED_DEEPSCIENTIST_HOME="${value}" ;;\n'
        '      med_deepscientist_repo_root) MED_DEEPSCIENTIST_REPO_ROOT_AUDIT="${value}" ;;\n'
        '      runtime_root_matches_med_deepscientist_runtime) RUNTIME_ROOT_MATCHES_MED_DEEPSCIENTIST_RUNTIME="${value}" ;;\n'
        '      runtime_contract_ready) MED_DEEPSCIENTIST_RUNTIME_CONTRACT_READY="${value}" ;;\n'
        '      launcher_contract_ready) MED_DEEPSCIENTIST_LAUNCHER_CONTRACT_READY="${value}" ;;\n'
        '      phase_25_ready) MED_DEEPSCIENTIST_PHASE_25_READY="${value}" ;;\n'
        "    esac\n"
        '  done <<< "${contract_lines}"\n\n'
        '  if [[ "${RUNTIME_ROOT_MATCHES_MED_DEEPSCIENTIST_RUNTIME:-false}" != "true" ]]; then\n'
        '    echo "runtime_root does not match med_deepscientist_runtime_root/quests for profile ${PROFILE_PATH}" >&2\n'
        "    exit 1\n"
        "  fi\n\n"
        '  if [[ -z "${MED_DEEPSCIENTIST_HOME:-}" ]]; then\n'
        '    echo "Failed to resolve med_deepscientist_runtime_root from profile ${PROFILE_PATH}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "}\n\n"
        "render_med_deepscientist_config_json() {\n"
        '  CONTRACT_JSON="${MEDAUTOSCI_MED_DEEPSCIENTIST_CONTRACT_JSON}" \\\n'
        '  LAUNCHER_PATH="${MED_DEEPSCIENTIST_LAUNCHER}" \\\n'
        '  python3 - <<'"'"'PY'"'"'\n'
        "import json\n"
        "import os\n\n"
        'payload = json.loads(os.environ["CONTRACT_JSON"])\n'
        'profile = payload["profile"]\n'
        'contracts = payload["contracts"]\n\n'
        "print(\n"
        "    json.dumps(\n"
        "        {\n"
        '            "workspace_root": profile["workspace_root"],\n'
        '            "runtime_root": profile["runtime_root"],\n'
        '            "med_deepscientist_runtime_root": profile["med_deepscientist_runtime_root"],\n'
        '            "med_deepscientist_repo_root": profile.get("med_deepscientist_repo_root"),\n'
        '            "launcher": os.environ["LAUNCHER_PATH"],\n'
        '            "runtime_contract_ready": contracts["runtime_contract"]["ready"],\n'
        '            "launcher_contract_ready": contracts["launcher_contract"]["ready"],\n'
        '            "phase_25_ready": contracts["behavior_gate"]["phase_25_ready"],\n'
        '            "behavior_gate_path": contracts["behavior_gate"]["path"],\n'
        "        },\n"
        "        ensure_ascii=False,\n"
        "        indent=2,\n"
        "    )\n"
        ")\n"
        "PY\n"
        "}\n\n"
        "run_med_deepscientist_launcher() {\n"
        '  exec "${MED_DEEPSCIENTIST_LAUNCHER}" --home "${MED_DEEPSCIENTIST_HOME}" "$@"\n'
        "}\n"
    )


def _legacy_managed_runtime_entry_reason(*, path: Path, existing_content: str) -> str | None:
    suffix = path.parts[-4:]
    if suffix == ("ops", "medautoscience", "bin", "_shared.sh"):
        if "python3 -m med_autoscience.cli" in existing_content:
            return "legacy_python_entry"
        looks_like_uv_entry = (
            "run_medautosci() {" in existing_content
            and 'uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"' in existing_content
        )
        if looks_like_uv_entry and "MED_AUTOSCIENCE_UV_BIN" not in existing_content:
            return "legacy_uv_entry"
        looks_like_managed_shared = (
            "run_medautosci() {" in existing_content
            and '"${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"'
            in existing_content
        )
        if looks_like_managed_shared and "MED_AUTOSCIENCE_RSCRIPT_BIN" not in existing_content:
            return "legacy_rscript_entry"
        if looks_like_managed_shared and "MED_AUTOSCIENCE_NODE_BIN" not in existing_content:
            return "legacy_node_entry"
        return None
    if suffix == ("ops", "medautoscience", "bin", "watch-runtime"):
        looks_like_managed_watch = (
            'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"' in existing_content
            and "--runtime-root" in existing_content
        )
        if looks_like_managed_watch:
            if "run_medautosci runtime watch" not in existing_content:
                return "legacy_watch_runtime_entry"
            if (
                'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"' not in existing_content
                or '--profile "${PROFILE_PATH}"' not in existing_content
                or "--ensure-study-runtimes" not in existing_content
                or "--apply" not in existing_content
                or "--loop" not in existing_content
            ):
                return "legacy_watch_runtime_entry"
    if suffix == ("ops", "medautoscience", "bin", "install-watch-runtime-service"):
        if "runtime ensure-supervision" not in existing_content:
            return "legacy_watch_runtime_service_install"
    if suffix == ("ops", "medautoscience", "bin", "watch-runtime-service-status"):
        if "runtime supervision-status" not in existing_content:
            return "legacy_watch_runtime_service_status"
    if suffix == ("ops", "medautoscience", "bin", "uninstall-watch-runtime-service"):
        if "runtime remove-supervision" not in existing_content:
            return "legacy_watch_runtime_service_uninstall"
    if suffix == ("ops", "medautoscience", "bin", "bootstrap"):
        if "workspace bootstrap" not in existing_content and "run_medautosci bootstrap" in existing_content:
            return "legacy_workspace_bootstrap_entry"
    if suffix == ("ops", "medautoscience", "bin", "show-profile"):
        if "doctor profile" not in existing_content and "run_medautosci show-profile" in existing_content:
            return "legacy_show_profile_entry"
    if suffix == ("ops", "medautoscience", "bin", "enter-study"):
        if "study ensure-runtime" not in existing_content and "run_medautosci ensure-study-runtime" in existing_content:
            return "legacy_enter_study_entry"
    if suffix == ("ops", "medautoscience", "bin", "publication-gate"):
        if "publication gate" not in existing_content and "run_medautosci publication-gate" in existing_content:
            return "legacy_publication_gate_entry"
    if suffix == ("ops", "medautoscience", "bin", "medical-surface"):
        if "publication surface" not in existing_content and "run_medautosci medical-publication-surface" in existing_content:
            return "legacy_publication_surface_entry"
    if suffix == ("ops", "medautoscience", "bin", "figure-loop-guard"):
        if "publication figure-loop-guard" not in existing_content and "run_medautosci figure-loop-guard" in existing_content:
            return "legacy_figure_loop_guard_entry"
    if suffix == ("ops", "medautoscience", "bin", "resolve-submission-targets"):
        if "publication resolve-targets" not in existing_content and "run_medautosci resolve-submission-targets" in existing_content:
            return "legacy_resolve_submission_targets_entry"
    if suffix == ("ops", "medautoscience", "bin", "resolve-journal-shortlist"):
        if "publication resolve-journal-shortlist" not in existing_content and "run_medautosci resolve-journal-shortlist" in existing_content:
            return "legacy_resolve_journal_shortlist_entry"
    if suffix == ("ops", "medautoscience", "bin", "init-portfolio-memory"):
        if "data init-memory" not in existing_content and "run_medautosci init-portfolio-memory" in existing_content:
            return "legacy_init_portfolio_memory_entry"
    if suffix == ("ops", "medautoscience", "bin", "portfolio-memory-status"):
        if "data memory-status" not in existing_content and "run_medautosci portfolio-memory-status" in existing_content:
            return "legacy_portfolio_memory_status_entry"
    if suffix == ("ops", "medautoscience", "bin", "init-workspace-literature"):
        if "data init-literature" not in existing_content and "run_medautosci init-workspace-literature" in existing_content:
            return "legacy_init_workspace_literature_entry"
    if suffix == ("ops", "medautoscience", "bin", "workspace-literature-status"):
        if "data literature-status" not in existing_content and "run_medautosci workspace-literature-status" in existing_content:
            return "legacy_workspace_literature_status_entry"
    if suffix == ("ops", "medautoscience", "bin", "prepare-external-research"):
        if (
            "data prepare-external-research" not in existing_content
            and "run_medautosci prepare-external-research" in existing_content
        ):
            return "legacy_prepare_external_research_entry"
    if suffix == ("ops", "medautoscience", "bin", "external-research-status"):
        if "data external-research-status" not in existing_content and "run_medautosci external-research-status" in existing_content:
            return "legacy_external_research_status_entry"
    if suffix == ("ops", "medautoscience", "bin", "export-submission"):
        if "publication export-targets" not in existing_content and "run_medautosci export-submission-targets" in existing_content:
            return "legacy_export_submission_targets_entry"
    if suffix == ("ops", "medautoscience", "bin", "sync-delivery"):
        if "study delivery-sync" not in existing_content and "run_medautosci sync-study-delivery" in existing_content:
            return "legacy_sync_study_delivery_entry"
    return None


def _is_workspace_profile_path(path: Path) -> bool:
    return len(path.parts) >= 4 and path.parts[-4:-1] == ("ops", "medautoscience", "profiles") and path.suffix == ".toml"


def _is_medautoscience_config_path(path: Path) -> bool:
    return len(path.parts) >= 3 and path.parts[-3:] == ("ops", "medautoscience", "config.env")


def _merge_medautoscience_config_content(*, existing_content: str, workspace_root: Path, profile_relpath: Path) -> str:
    if "MED_AUTOSCIENCE_NODE_BIN" in existing_content:
        return existing_content
    rendered_content = workspace_entry_rendering_controller.render_medautoscience_config(
        workspace_root=workspace_root,
        profile_relpath=profile_relpath,
    )
    rendered_lines = rendered_content.splitlines()
    try:
        comment_index = rendered_lines.index(
            "# Optional: set the absolute path to node so managed runtime services can still launch node-backed backends under minimal PATH environments."
        )
    except ValueError:
        return existing_content
    node_block = "\n".join(rendered_lines[comment_index : comment_index + 2]).strip()
    if not node_block:
        return existing_content
    base = existing_content.rstrip()
    separator = "\n\n" if base else ""
    return f"{base}{separator}{node_block}\n"


def _merge_workspace_profile_content(
    *,
    existing_content: str,
    workspace_root: Path,
    workspace_name: str,
    default_publication_profile: str,
    default_citation_style: str,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None,
) -> str:
    try:
        payload = tomllib.loads(existing_content)
    except tomllib.TOMLDecodeError:
        return existing_content
    if not isinstance(payload, dict):
        return existing_content
    required_identity_keys = {
        "name",
        "workspace_root",
        "runtime_root",
        "studies_root",
        "portfolio_root",
        "med_deepscientist_runtime_root",
    }
    if not required_identity_keys.issubset(payload):
        return existing_content
    merge_entries = _render_workspace_profile_entries(
        workspace_root=workspace_root,
        workspace_name=workspace_name,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        hermes_agent_repo_root=hermes_agent_repo_root,
        hermes_home_root=hermes_home_root,
        include_hermes_placeholders=False,
    )
    missing_lines = [line for key, line in merge_entries if key not in payload]
    if not missing_lines:
        return existing_content
    base = existing_content.rstrip()
    separator = "\n\n" if base else ""
    return f"{base}{separator}{chr(10).join(missing_lines)}\n"


def _rendered_file_action(item: RenderedFile, *, force: bool) -> str:
    if not item.path.exists():
        return "create"
    if force:
        return "overwrite"
    try:
        existing_content = item.path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "skip"
    if _legacy_managed_runtime_entry_reason(path=item.path, existing_content=existing_content) is not None:
        return "upgrade"
    if _is_workspace_profile_path(item.path) and existing_content != item.content:
        return "upgrade"
    if _is_medautoscience_config_path(item.path) and existing_content != item.content:
        return "upgrade"
    if is_workspace_gitignore_path(item.path) and existing_content != item.content:
        return "upgrade"
    return "skip"


def _render_med_deepscientist_forward(script_command: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# shellcheck disable=SC1091\n"
        'source "${SCRIPT_DIR}/_shared.sh"\n\n'
        "load_med_deepscientist_contract\n"
        f"run_med_deepscientist_launcher {script_command} \"$@\"\n"
    )


def _render_med_deepscientist_show_config() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# shellcheck disable=SC1091\n"
        'source "${SCRIPT_DIR}/_shared.sh"\n\n'
        "load_med_deepscientist_contract\n"
        "render_med_deepscientist_config_json\n"
    )


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
            content=workspace_entry_rendering_controller.render_med_deepscientist_config(),
        ),
        RenderedFile(
            path=layout.config_env_example_path,
            content=workspace_entry_rendering_controller.render_med_deepscientist_config(),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "README.md",
            content=workspace_entry_rendering_controller.render_medautoscience_readme(profile_relpath=profile_relpath),
        ),
        RenderedFile(
            path=layout.readme_path,
            content=workspace_entry_rendering_controller.render_med_deepscientist_readme(),
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
            content=_render_forward_script("study ensure-runtime", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime",
            content=_render_watch_runtime_script(runtime_quests_root=layout.quests_root),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "maintain-runtime-storage",
            content=_render_forward_script("runtime maintain-storage", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner",
            content=_render_watch_runtime_service_runner(),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service",
            content=_render_forward_script("runtime ensure-supervision", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status",
            content=_render_forward_script("runtime supervision-status", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "uninstall-watch-runtime-service",
            content=_render_forward_script("runtime remove-supervision", with_profile=True),
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
            content=_render_med_deepscientist_shared(),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "doctor",
            content=_render_med_deepscientist_forward("doctor"),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "show-config",
            content=_render_med_deepscientist_show_config(),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "start-web",
            content=_render_med_deepscientist_forward("--port 20999"),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "status",
            content=_render_med_deepscientist_forward("--status"),
            executable=True,
        ),
        RenderedFile(
            path=layout.bin_root / "stop",
            content=_render_med_deepscientist_forward("--stop"),
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
    initialize_git: bool = True,
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
                        content=_merge_workspace_profile_content(
                            existing_content=existing_content,
                            workspace_root=workspace_root,
                            workspace_name=workspace_name,
                            default_publication_profile=default_publication_profile,
                            default_citation_style=default_citation_style,
                            hermes_agent_repo_root=hermes_agent_repo_root,
                            hermes_home_root=hermes_home_root,
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
                        content=_merge_medautoscience_config_content(
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

    if dry_run:
        created_directories = [str(path) for path in directories if not path.exists()]
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
        "workspace_git": workspace_git,
        "profile_path": str(profile_path),
        "next_steps": [
            f"edit {workspace_root / 'ops' / 'medautoscience' / 'config.env'}",
            f"edit {layout.config_env_path}",
            f"review {profile_path}",
            f"run {workspace_root / 'ops' / 'medautoscience' / 'bin' / 'show-profile'}",
            f"run {workspace_root / 'ops' / 'medautoscience' / 'bin' / 'bootstrap'}",
        ],
    }
