from __future__ import annotations

from pathlib import Path
import shutil


def render_medautoscience_config(*, workspace_root: Path, profile_relpath: Path) -> str:
    profile_path = profile_relpath if profile_relpath.is_absolute() else workspace_root / profile_relpath
    detected_node = shutil.which("node")
    node_config_value = detected_node if detected_node and Path(detected_node).is_absolute() else "/ABS/PATH/TO/node"
    return (
        "# Set the absolute path to the shared MedAutoScience checkout.\n"
        'MED_AUTOSCIENCE_REPO="/ABS/PATH/TO/med-autoscience"\n'
        "# Optional: set the absolute path to the uv binary used by workspace entry scripts and host services.\n"
        'MED_AUTOSCIENCE_UV_BIN="/ABS/PATH/TO/uv"\n'
        "# Optional: set the absolute path to Rscript so host services can still see it under minimal PATH environments.\n"
        'MED_AUTOSCIENCE_RSCRIPT_BIN="/ABS/PATH/TO/Rscript"\n'
        "# Optional: set the absolute path to node so managed runtime services can still launch node-backed backends under minimal PATH environments.\n"
        f'MED_AUTOSCIENCE_NODE_BIN="{node_config_value}"\n'
        "# Optional: override the default local profile file.\n"
        f'MED_AUTOSCIENCE_PROFILE="{profile_path}"\n'
    )


def render_med_deepscientist_config() -> str:
    return (
        "# Set the absolute path to the local med-deepscientist launcher binary.\n"
        'MED_DEEPSCIENTIST_LAUNCHER="/ABS/PATH/TO/ds"\n'
    )


def render_medautoscience_readme(*, profile_relpath: Path) -> str:
    return (
        "# MedAutoScience Workspace Entry\n\n"
        "这个目录是当前 workspace 面向用户和 Agent 的本地入口层。\n\n"
        "默认 profile:\n\n"
        f"- `{profile_relpath.as_posix()}`\n"
        "\n"
        "推荐的长时监管入口：\n\n"
        "- `bin/watch-runtime`\n"
        "- `bin/install-watch-runtime-service`\n"
        "- `bin/watch-runtime-service-status`\n"
        "- `bin/uninstall-watch-runtime-service`\n\n"
        "其中 `install-watch-runtime-service` / `watch-runtime-service-status` / `uninstall-watch-runtime-service`\n"
        "会管理 Hermes-hosted supervision job，而不是再安装第二个 workspace-local 常驻 service。\n"
    )


def render_med_deepscientist_readme() -> str:
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
