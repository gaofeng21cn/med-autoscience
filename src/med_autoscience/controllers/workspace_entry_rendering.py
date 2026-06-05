from __future__ import annotations

from pathlib import Path
import shutil


def _absolute_tool_path(executable: str, *, placeholder: str) -> str:
    detected = shutil.which(executable)
    if detected and Path(detected).is_absolute():
        return detected
    return placeholder


def _repo_config_path() -> str:
    candidate = Path(__file__).resolve().parents[3]
    if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "med_autoscience").is_dir():
        return str(candidate)
    return "/ABS/PATH/TO/med-autoscience"


def render_medautoscience_config(*, workspace_root: Path, profile_relpath: Path) -> str:
    profile_path = profile_relpath if profile_relpath.is_absolute() else workspace_root / profile_relpath
    repo_config_value = _repo_config_path()
    uv_config_value = _absolute_tool_path("uv", placeholder="/ABS/PATH/TO/uv")
    rscript_config_value = _absolute_tool_path("Rscript", placeholder="/ABS/PATH/TO/Rscript")
    node_config_value = _absolute_tool_path("node", placeholder="/ABS/PATH/TO/node")
    return (
        "# Set the absolute path to the shared MedAutoScience checkout.\n"
        f'MED_AUTOSCIENCE_REPO="{repo_config_value}"\n'
        "# Optional: set the absolute path to the uv binary used by workspace entry scripts and host services.\n"
        f'MED_AUTOSCIENCE_UV_BIN="{uv_config_value}"\n'
        "# Optional: set the absolute path to Rscript so host services can still see it under minimal PATH environments.\n"
        f'MED_AUTOSCIENCE_RSCRIPT_BIN="{rscript_config_value}"\n'
        "# Optional: set the absolute path to node so managed runtime commands can still launch node-backed backends under minimal PATH environments.\n"
        f'MED_AUTOSCIENCE_NODE_BIN="{node_config_value}"\n'
        "# Optional: override the default local profile file.\n"
        f'MED_AUTOSCIENCE_PROFILE="{profile_path}"\n'
    )


def render_mas_runtime_bridge_config() -> str:
    return (
        "# MAS domain refs bridge config.\n"
        "# This file intentionally has no external MDS launcher setting; default runtime control belongs to OPL.\n"
    )


def render_medautoscience_readme(*, profile_relpath: Path) -> str:
    return (
        "# MedAutoScience Workspace Entry\n\n"
        "这个目录是当前 workspace 面向用户和 Agent 的本地入口层。\n\n"
        "默认 profile:\n\n"
        f"- `{profile_relpath.as_posix()}`\n"
        "\n"
        "推荐的 domain refs 入口：\n\n"
        "- `bin/domain-health-diagnostic`\n"
        "- `bin/study-progress <study_id>`\n"
        "- `bin/progress-projection`\n"
        "- `bin/study-state-matrix`\n"
        "- `bin/owner-route-reconcile`\n"
        "- `bin/domain-action-request-materialize`\n"
        "- `bin/domain-owner-action-dispatch`\n\n"
        "Progress-first 监控建议使用 `bin/progress-projection <study_id> --format json` "
        "读取单 study 结构化状态，使用 `bin/study-state-matrix --format json` "
        "读取 workspace 级 study 矩阵；旧 `bin/progress-projection <study_id> --json` "
        "仍作为 JSON alias 保留。\n\n"
        "默认 stage/runtime lifecycle 由 OPL current_control_state refs-only handoff 承接。"
        "MAS 只保留 `domain-health-diagnostic`、owner receipt、typed blocker 与 domain authority refs；"
        "旧 workspace-local supervision 命令已物理退役为 tombstone/provenance-only。\n"
    )


def render_mas_runtime_bridge_readme() -> str:
    return (
        "# MAS Domain Refs Bridge\n\n"
        "这个目录保留当前 workspace 的 MAS domain refs 运维薄入口脚本。\n\n"
        "它不是 MAS 私有 runtime 运维面，也不是研究入口。\n\n"
        "请遵守下面的边界：\n\n"
        "- 研究 quest 的创建、恢复、门禁判断统一走 `MedAutoScience`。\n"
        "- 不要从这里直接发起研究，不要把 `start-web`、`status`、`doctor`、`stop` 当成研究入口。\n"
        "- 需要进入 study 时，使用 `ops/medautoscience/bin/enter-study`、`ops/medautoscience/bin/bootstrap` 与 OPL stage control 面。\n"
        "- 如果需要查看或维护 runtime，读取 OPL current-control-state；本目录下脚本只调用 MAS domain refs / diagnostic surface，不调用外部 MDS launcher、daemon 或 WebUI。\n"
    )
