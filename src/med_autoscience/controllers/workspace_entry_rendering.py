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
        "- `bin/study-state-matrix`\n"
        "- `bin/owner-route-reconcile`\n"
        "\n"
        "Progress-first 监控建议使用 `bin/study-progress <study_id>` "
        "读取单 study 当前进度；需要结构化 JSON 时使用 "
        "`bin/study-progress <study_id> --format json`，使用 "
        "`bin/study-state-matrix --format json` 读取 workspace 级 study 矩阵。\n\n"
        "默认 stage/runtime lifecycle 由 OPL current_control_state refs-only handoff 承接。"
        "MAS 只保留 `domain-health-diagnostic`、owner receipt、typed blocker 与 domain authority refs；"
        "`bin/domain-action-request-materialize` 和 `bin/domain-owner-action-dispatch` "
        "已物理退役为 tombstone/provenance-only；generic transition runtime 和 owner-callable execution "
        "必须经 OPL primitive/readback 承接。\n"
    )
