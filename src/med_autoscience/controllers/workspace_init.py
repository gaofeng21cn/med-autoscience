from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from med_autoscience.controllers import portfolio_memory as portfolio_memory_controller
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


def _workspace_directories(workspace_root: Path) -> list[Path]:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    return [
        workspace_root / "datasets",
        workspace_root / "contracts",
        workspace_root / "studies",
        workspace_root / "portfolio" / "data_assets",
        workspace_root / "portfolio" / "research_memory",
        workspace_root / "portfolio" / "research_memory" / "prompts",
        workspace_root / "portfolio" / "research_memory" / "external_reports",
        workspace_root / "refs",
        workspace_root / "ops" / "medautoscience" / "bin",
        workspace_root / "ops" / "medautoscience" / "profiles",
        layout.bin_root,
        layout.runtime_root,
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
        "7. 阅读 `WORKSPACE_AUTOSCIENCE_RULES.md`，确认 controller-first 与 automation-ready 默认约束。\n\n"
        "8. 优先维护 `portfolio/research_memory/`，把疾病热点、课题地图与期刊邻域沉淀为可复用研究资产。\n\n"
        "9. 如需额外外部视角，使用 `ops/medautoscience/bin/prepare-external-research` 准备 prompt；它是 optional enrichment，不是启动门。\n\n"
        "## Runtime Boundary\n\n"
        "- `MedAutoScience` 是研究入口与治理层。\n"
        "- `ops/med-deepscientist/` 只保留 runtime 状态和运维脚本。\n"
        "- 不要直接通过 `med-deepscientist` UI、CLI 或 daemon HTTP API 发起研究 quest。\n"
        "- 如果需要启动、查看或停止 runtime，只把 `ops/med-deepscientist/bin/*` 当作运维面，不把它当成研究入口。\n"
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
        "- 边界明确且 startup-ready 后，默认切入 `med-deepscientist` managed runtime 的自动持续推进。\n"
        "- 不要在已经满足自动推进条件的 study 上持续停留在碎片化人工交互。\n"
        f"- {automation_ready_summary}\n"
    )


def _render_workspace_profile(
    *,
    workspace_root: Path,
    workspace_name: str,
    default_publication_profile: str,
    default_citation_style: str,
) -> str:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    return (
        f'name = "{workspace_name}"\n'
        f'workspace_root = "{workspace_root}"\n'
        f'runtime_root = "{layout.quests_root}"\n'
        f'studies_root = "{workspace_root / "studies"}"\n'
        f'portfolio_root = "{workspace_root / "portfolio"}"\n'
        f'med_deepscientist_runtime_root = "{layout.runtime_root}"\n'
        'med_deepscientist_repo_root = "/ABS/PATH/TO/med-deepscientist"\n'
        f'default_publication_profile = "{default_publication_profile}"\n'
        f'default_citation_style = "{default_citation_style}"\n'
        "enable_medical_overlay = true\n"
        'medical_overlay_scope = "workspace"\n'
        'medical_overlay_skills = ["intake-audit", "scout", "baseline", "idea", "decision", "experiment", "analysis-campaign", "figure-polish", "write", "review", "rebuttal", "finalize"]\n'
        'medical_overlay_bootstrap_mode = "ensure_ready"\n'
        'research_route_bias_policy = "high_plasticity_medical"\n'
        'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]\n'
        'default_startup_anchor_policy = "scout_first_for_continue_existing_state"\n'
        'legacy_code_execution_policy = "forbid_without_user_approval"\n'
        'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]\n'
    )


def _render_medautoscience_config(*, workspace_root: Path, profile_relpath: Path) -> str:
    profile_path = workspace_root / profile_relpath
    return (
        "# Set the absolute path to the shared MedAutoScience checkout.\n"
        'MED_AUTOSCIENCE_REPO="/ABS/PATH/TO/med-autoscience"\n'
        "# Optional: override the default local profile file.\n"
        f'MED_AUTOSCIENCE_PROFILE="{profile_path}"\n'
    )


def _render_med_deepscientist_config() -> str:
    return (
        "# Set the absolute path to the local med-deepscientist launcher binary.\n"
        'MED_DEEPSCIENTIST_LAUNCHER="/ABS/PATH/TO/ds"\n'
    )


def _render_medautoscience_readme(*, profile_relpath: Path) -> str:
    return (
        "# MedAutoScience Workspace Entry\n\n"
        "这个目录是当前 workspace 面向用户和 Agent 的本地入口层。\n\n"
        "默认 profile:\n\n"
        f"- `{profile_relpath.as_posix()}`\n"
    )


def _render_med_deepscientist_readme() -> str:
    return (
        "# med-deepscientist Workspace Entry\n\n"
        "这个目录保留当前 workspace 的 `med-deepscientist` project-local runtime state 与薄入口脚本。\n\n"
        "它是 runtime 运维面，不是研究入口。\n\n"
        "请遵守下面的边界：\n\n"
        "- 研究 quest 的创建、恢复、门禁判断统一走 `MedAutoScience`。\n"
        "- 不要从这里直接发起研究，不要把 `start-web`、`status`、`doctor`、`stop` 当成研究入口。\n"
        "- 需要进入 study 时，使用 `ops/medautoscience/bin/enter-study`、`ops/medautoscience/bin/bootstrap`、`ensure-study-runtime` 等受管入口。\n"
        "- 如果需要查看或维护 runtime，本目录下脚本只用于运维审计，不承担医学研究治理责任。\n"
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
        "run_medautosci() {\n"
        '  uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
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
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci watch \\\n'
        f'  --runtime-root "{runtime_quests_root}" \\\n'
        '  "$@"\n'
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
        '    PYTHONPATH="${MED_AUTOSCIENCE_REPO_RESOLVED}/src${PYTHONPATH:+:${PYTHONPATH}}" \\\n'
        '      python3 - "${PROFILE_PATH}" <<'"'"'PY'"'"'\n'
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
        '    CONTRACT_JSON="${payload_json}" python3 - <<'"'"'PY'"'"'\n'
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
    default_publication_profile: str,
    default_citation_style: str,
) -> list[RenderedFile]:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    profile_relpath = Path("ops") / "medautoscience" / "profiles" / _profile_filename(workspace_name)
    files = [
        RenderedFile(
            path=workspace_root / "README.md",
            content=_render_workspace_readme(workspace_name=workspace_name, profile_relpath=profile_relpath),
        ),
        RenderedFile(
            path=workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md",
            content=_render_workspace_rules(),
        ),
        RenderedFile(
            path=workspace_root / profile_relpath,
            content=_render_workspace_profile(
                workspace_root=workspace_root,
                workspace_name=workspace_name,
                default_publication_profile=default_publication_profile,
                default_citation_style=default_citation_style,
            ),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "config.env",
            content=_render_medautoscience_config(workspace_root=workspace_root, profile_relpath=profile_relpath),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "config.env.example",
            content=_render_medautoscience_config(workspace_root=workspace_root, profile_relpath=profile_relpath),
        ),
        RenderedFile(
            path=layout.config_env_path,
            content=_render_med_deepscientist_config(),
        ),
        RenderedFile(
            path=layout.config_env_example_path,
            content=_render_med_deepscientist_config(),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "README.md",
            content=_render_medautoscience_readme(profile_relpath=profile_relpath),
        ),
        RenderedFile(
            path=layout.readme_path,
            content=_render_med_deepscientist_readme(),
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh",
            content=_render_medautosci_shared(profile_relpath),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "bootstrap",
            content=_render_forward_script("bootstrap", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "show-profile",
            content=_render_forward_script("show-profile", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "enter-study",
            content=_render_forward_script("ensure-study-runtime", with_profile=True),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime",
            content=_render_watch_runtime_script(runtime_quests_root=layout.quests_root),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "publication-gate",
            content=_render_forward_script("publication-gate"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "medical-surface",
            content=_render_forward_script("medical-publication-surface"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "figure-loop-guard",
            content=_render_forward_script("figure-loop-guard"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "resolve-submission-targets",
            content=_render_profile_optional_forward_script("resolve-submission-targets"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "resolve-journal-shortlist",
            content=_render_forward_script("resolve-journal-shortlist"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory",
            content=_render_forward_script("init-portfolio-memory"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "portfolio-memory-status",
            content=_render_forward_script("portfolio-memory-status"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research",
            content=_render_forward_script("prepare-external-research"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "external-research-status",
            content=_render_forward_script("external-research-status"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "export-submission",
            content=_render_profile_optional_forward_script("export-submission-targets"),
            executable=True,
        ),
        RenderedFile(
            path=workspace_root / "ops" / "medautoscience" / "bin" / "sync-delivery",
            content=_render_forward_script("sync-study-delivery"),
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
    return files


def init_workspace(
    *,
    workspace_root: Path,
    workspace_name: str,
    dry_run: bool = False,
    force: bool = False,
    default_publication_profile: str = "general_medical_journal",
    default_citation_style: str = "AMA",
) -> dict[str, object]:
    workspace_root = workspace_root.expanduser().resolve()
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    directories = _workspace_directories(workspace_root)
    files = _rendered_files(
        workspace_root=workspace_root,
        workspace_name=workspace_name,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
    )

    created_directories: list[str] = []
    created_files: list[str] = []
    skipped_files: list[str] = []
    overwritten_files: list[str] = []

    if dry_run:
        created_directories = [str(path) for path in directories]
        created_files = [str(item.path) for item in files]
    else:
        for path in directories:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created_directories.append(str(path))
        for item in files:
            if item.path.exists() and not force:
                skipped_files.append(str(item.path))
                continue
            item.path.parent.mkdir(parents=True, exist_ok=True)
            if item.path.exists() and force:
                overwritten_files.append(str(item.path))
            else:
                created_files.append(str(item.path))
            item.path.write_text(item.content, encoding="utf-8")
            if item.executable:
                item.path.chmod(item.path.stat().st_mode | 0o111)

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / _profile_filename(workspace_name)
    return {
        "workspace_root": str(workspace_root),
        "workspace_name": workspace_name,
        "dry_run": dry_run,
        "force": force,
        "created_directories": created_directories,
        "created_files": created_files,
        "skipped_files": skipped_files,
        "overwritten_files": overwritten_files,
        "profile_path": str(profile_path),
        "next_steps": [
            f"edit {workspace_root / 'ops' / 'medautoscience' / 'config.env'}",
            f"edit {layout.config_env_path}",
            f"review {profile_path}",
            f"run {workspace_root / 'ops' / 'medautoscience' / 'bin' / 'show-profile'}",
            f"run {workspace_root / 'ops' / 'medautoscience' / 'bin' / 'bootstrap'}",
        ],
    }
