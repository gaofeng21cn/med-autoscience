from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from med_autoscience.domain_entry_contract import SERVICE_SAFE_ENTRY_TARGET


GENERATED_MARKER = "# Generated MAS workspace compatibility entry; canonical execution stays in the OPL module carrier."


@dataclass(frozen=True)
class WorkspaceEntryAsset:
    path: Path
    content: str
    executable: bool = False
    preserve_existing: bool = False


def _repo_config_path() -> Path:
    candidate = Path(__file__).resolve().parents[3]
    if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "med_autoscience").is_dir():
        return candidate
    return Path("/ABS/PATH/TO/med-autoscience")


def _resolved_profile_path(*, workspace_root: Path, profile_ref: Path) -> Path:
    candidate = profile_ref if profile_ref.is_absolute() else workspace_root / profile_ref
    return candidate.expanduser().resolve()


def render_medautoscience_config(
    *,
    workspace_root: Path,
    profile_relpath: Path,
    repo_root: Path | None = None,
) -> str:
    profile_path = _resolved_profile_path(workspace_root=workspace_root, profile_ref=profile_relpath)
    source_root = (repo_root or _repo_config_path()).expanduser().resolve()
    return (
        "# MAS domain-handler source used by OPL-managed workspace compatibility entries.\n"
        f'MED_AUTOSCIENCE_REPO="{source_root}"\n'
        "# Optional: override the OPL-managed module runtime root. No workspace-local venv is used.\n"
        '# MAS_OPL_MODULE_RUNTIME_ROOT="/ABS/PATH/TO/opl-managed/medautoscience"\n'
        "# Optional: override the default workspace profile.\n"
        f'MED_AUTOSCIENCE_PROFILE="{profile_path}"\n'
    )


def render_medautoscience_readme(*, profile_relpath: Path) -> str:
    return (
        "# MedAutoScience Workspace Entry\n\n"
        "这个目录保留 workspace-local 兼容入口；canonical 接口由 OPL 生成，医学行为统一进入 "
        f"`{SERVICE_SAFE_ENTRY_TARGET}`。\n\n"
        "默认 profile:\n\n"
        f"- `{profile_relpath.as_posix()}`\n\n"
        "当前入口：\n\n"
        "- `bin/study-state-matrix --format json`\n"
        "- `bin/study-progress <study_id> --format json`\n"
        "- `bin/paper-mission inspect --study-id <study_id> --format json`\n"
        "- `bin/enter-study <study_id> --format json`\n\n"
        "这些脚本不创建 workspace-local Python 环境，不调用 MAS 私有 CLI，也不持有 domain truth。\n"
    )


def _render_shared(profile_relpath: Path) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
{GENERATED_MARKER}

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
MEDAUTOSCI_OPS_ROOT="$(cd "${{SCRIPT_DIR}}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${{SCRIPT_DIR}}/../../.." && pwd)"
DEFAULT_PROFILE="${{WORKSPACE_ROOT}}/{profile_relpath.as_posix()}"
CONFIG_ENV_PATH="${{MEDAUTOSCI_OPS_ROOT}}/config.env"

if [[ -f "${{CONFIG_ENV_PATH}}" ]]; then
  # shellcheck disable=SC1090
  source "${{CONFIG_ENV_PATH}}"
fi

PROFILE_PATH="${{MED_AUTOSCIENCE_PROFILE:-${{DEFAULT_PROFILE}}}}"
if [[ ! -f "${{PROFILE_PATH}}" ]]; then
  echo "Profile file not found: ${{PROFILE_PATH}}" >&2
  exit 1
fi

if [[ -z "${{MED_AUTOSCIENCE_REPO:-}}" ]]; then
  echo "MED_AUTOSCIENCE_REPO is not configured in ${{CONFIG_ENV_PATH}}." >&2
  exit 1
fi
MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${{MED_AUTOSCIENCE_REPO}}" && pwd -P)"
DOMAIN_ENTRY_CARRIER="${{MED_AUTOSCIENCE_REPO_RESOLVED}}/scripts/opl-module-dispatch.sh"
if [[ ! -x "${{DOMAIN_ENTRY_CARRIER}}" ]]; then
  echo "Canonical MAS domain-entry carrier is missing or not executable: ${{DOMAIN_ENTRY_CARRIER}}" >&2
  exit 1
fi

run_domain_entry() {{
  exec "${{DOMAIN_ENTRY_CARRIER}}" "$@"
}}
"""


def _render_study_state_matrix() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
{GENERATED_MARKER}
source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"

profile_path="${{PROFILE_PATH}}"
entry_mode=""
study_ids=()
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --format)
      [[ "$#" -ge 2 ]] || {{ echo "--format requires a value" >&2; exit 2; }}
      [[ "$2" == "json" ]] || {{ echo "study-state-matrix only emits JSON" >&2; exit 2; }}
      shift 2
      ;;
    --format=json)
      shift
      ;;
    --profile|--profile-ref)
      [[ "$#" -ge 2 ]] || {{ echo "$1 requires a value" >&2; exit 2; }}
      profile_path="$2"
      shift 2
      ;;
    --study-id)
      [[ "$#" -ge 2 ]] || {{ echo "--study-id requires a value" >&2; exit 2; }}
      study_ids+=("$2")
      shift 2
      ;;
    --entry-mode)
      [[ "$#" -ge 2 ]] || {{ echo "--entry-mode requires a value" >&2; exit 2; }}
      entry_mode="$2"
      shift 2
      ;;
    --)
      shift
      while [[ "$#" -gt 0 ]]; do study_ids+=("$1"); shift; done
      ;;
    -*)
      echo "Unsupported study-state-matrix argument: $1" >&2
      exit 2
      ;;
    *)
      study_ids+=("$1")
      shift
      ;;
  esac
done

request_args=(--dispatch-command study-state-matrix --string-field profile_ref "${{profile_path}}")
[[ -z "${{entry_mode}}" ]] || request_args+=(--string-field entry_mode "${{entry_mode}}")
if [[ "${{#study_ids[@]}}" -gt 0 ]]; then
  for study_id in "${{study_ids[@]}}"; do request_args+=(--list-field study_ids "${{study_id}}"); done
fi
run_domain_entry "${{request_args[@]}}"
"""


def _render_study_progress() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
{GENERATED_MARKER}
source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"

profile_path="${{PROFILE_PATH}}"
study_id=""
entry_mode=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --format)
      [[ "$#" -ge 2 ]] || {{ echo "--format requires a value" >&2; exit 2; }}
      [[ "$2" == "json" ]] || {{ echo "study-progress only emits JSON" >&2; exit 2; }}
      shift 2
      ;;
    --format=json)
      shift
      ;;
    --profile|--profile-ref)
      [[ "$#" -ge 2 ]] || {{ echo "$1 requires a value" >&2; exit 2; }}
      profile_path="$2"
      shift 2
      ;;
    --study-id)
      [[ "$#" -ge 2 ]] || {{ echo "--study-id requires a value" >&2; exit 2; }}
      study_id="$2"
      shift 2
      ;;
    --entry-mode)
      [[ "$#" -ge 2 ]] || {{ echo "--entry-mode requires a value" >&2; exit 2; }}
      entry_mode="$2"
      shift 2
      ;;
    -*)
      echo "Unsupported study-progress argument: $1" >&2
      exit 2
      ;;
    *)
      [[ -z "${{study_id}}" ]] || {{ echo "study-progress accepts one study id" >&2; exit 2; }}
      study_id="$1"
      shift
      ;;
  esac
done
[[ -n "${{study_id}}" ]] || {{ echo "study-progress requires a study id" >&2; exit 2; }}

request_args=(
  --dispatch-command study-progress
  --string-field profile_ref "${{profile_path}}"
  --string-field study_id "${{study_id}}"
)
[[ -z "${{entry_mode}}" ]] || request_args+=(--string-field entry_mode "${{entry_mode}}")
run_domain_entry "${{request_args[@]}}"
"""


def _render_paper_mission() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
{GENERATED_MARKER}
source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"

profile_path="${{PROFILE_PATH}}"
mission_command="inspect"
study_id=""
dry_run=0
optional_fields=()
if [[ "$#" -gt 0 && "$1" != -* ]]; then mission_command="$1"; shift; fi
[[ "${{mission_command}}" == "inspect" || "${{mission_command}}" == "drive" ]] || {{
  echo "paper-mission command must be inspect or drive" >&2
  exit 2
}}
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --format)
      [[ "$#" -ge 2 ]] || {{ echo "--format requires a value" >&2; exit 2; }}
      [[ "$2" == "json" ]] || {{ echo "paper-mission only emits JSON" >&2; exit 2; }}
      shift 2
      ;;
    --format=json)
      shift
      ;;
    --profile|--profile-ref)
      [[ "$#" -ge 2 ]] || {{ echo "$1 requires a value" >&2; exit 2; }}
      profile_path="$2"
      shift 2
      ;;
    --study-id)
      [[ "$#" -ge 2 ]] || {{ echo "--study-id requires a value" >&2; exit 2; }}
      study_id="$2"
      shift 2
      ;;
    --objective|--mission-id|--candidate|--run-id|--output-root)
      [[ "$#" -ge 2 ]] || {{ echo "$1 requires a value" >&2; exit 2; }}
      field_name="${{1#--}}"
      field_name="${{field_name//-/_}}"
      optional_fields+=(--string-field "${{field_name}}" "$2")
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -*)
      echo "Unsupported paper-mission argument: $1" >&2
      exit 2
      ;;
    *)
      [[ -z "${{study_id}}" ]] || {{ echo "paper-mission accepts one study id" >&2; exit 2; }}
      study_id="$1"
      shift
      ;;
  esac
done
[[ -n "${{study_id}}" ]] || {{ echo "paper-mission requires --study-id" >&2; exit 2; }}

request_args=(
  --dispatch-command paper-mission
  --string-field profile_ref "${{profile_path}}"
  --string-field study_id "${{study_id}}"
  --string-field paper_mission_command "${{mission_command}}"
)
if [[ "${{#optional_fields[@]}}" -gt 0 ]]; then request_args+=("${{optional_fields[@]}}"); fi
[[ "${{dry_run}}" -eq 0 ]] || request_args+=(--flag-field dry_run)
run_domain_entry "${{request_args[@]}}"
"""


def _render_enter_study() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
{GENERATED_MARKER}
source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"

profile_path="${{PROFILE_PATH}}"
study_id=""
entry_mode=""
flag_fields=()
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --format)
      [[ "$#" -ge 2 ]] || {{ echo "--format requires a value" >&2; exit 2; }}
      [[ "$2" == "json" ]] || {{ echo "enter-study only emits JSON" >&2; exit 2; }}
      shift 2
      ;;
    --format=json)
      shift
      ;;
    --profile|--profile-ref)
      [[ "$#" -ge 2 ]] || {{ echo "$1 requires a value" >&2; exit 2; }}
      profile_path="$2"
      shift 2
      ;;
    --study-id)
      [[ "$#" -ge 2 ]] || {{ echo "--study-id requires a value" >&2; exit 2; }}
      study_id="$2"
      shift 2
      ;;
    --entry-mode)
      [[ "$#" -ge 2 ]] || {{ echo "--entry-mode requires a value" >&2; exit 2; }}
      entry_mode="$2"
      shift 2
      ;;
    --allow-stopped-relaunch|--explicit-user-wakeup|--force)
      field_name="${{1#--}}"
      flag_fields+=(--flag-field "${{field_name//-/_}}")
      shift
      ;;
    -*)
      echo "Unsupported enter-study argument: $1" >&2
      exit 2
      ;;
    *)
      [[ -z "${{study_id}}" ]] || {{ echo "enter-study accepts one study id" >&2; exit 2; }}
      study_id="$1"
      shift
      ;;
  esac
done
[[ -n "${{study_id}}" ]] || {{ echo "enter-study requires a study id" >&2; exit 2; }}

request_args=(
  --dispatch-command launch-study
  --string-field profile_ref "${{profile_path}}"
  --string-field study_id "${{study_id}}"
)
if [[ "${{#flag_fields[@]}}" -gt 0 ]]; then request_args+=("${{flag_fields[@]}}"); fi
[[ -z "${{entry_mode}}" ]] || request_args+=(--string-field entry_mode "${{entry_mode}}")
run_domain_entry "${{request_args[@]}}"
"""


def _render_bootstrap() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
{GENERATED_MARKER}

OPL_BIN="${{OPL_BIN:-$(command -v opl || true)}}"
if [[ -z "${{OPL_BIN}}" || ! -x "${{OPL_BIN}}" ]]; then
  echo "OPL is required to prepare the MAS module runtime." >&2
  exit 1
fi
exec "${{OPL_BIN}}" connect update --module medautoscience --json "$@"
"""


def workspace_entry_assets(
    *,
    workspace_root: Path,
    profile_ref: Path,
    repo_root: Path | None = None,
) -> tuple[WorkspaceEntryAsset, ...]:
    root = workspace_root.expanduser().resolve()
    profile_path = _resolved_profile_path(workspace_root=root, profile_ref=profile_ref)
    try:
        profile_relpath = profile_path.relative_to(root)
    except ValueError:
        profile_relpath = profile_path
    source_root = (repo_root or _repo_config_path()).expanduser().resolve()
    ops_root = root / "ops" / "medautoscience"
    bin_root = ops_root / "bin"
    return (
        WorkspaceEntryAsset(
            ops_root / "config.env",
            render_medautoscience_config(
                workspace_root=root,
                profile_relpath=profile_path,
                repo_root=source_root,
            ),
            preserve_existing=True,
        ),
        WorkspaceEntryAsset(
            ops_root / "config.env.example",
            render_medautoscience_config(
                workspace_root=root,
                profile_relpath=profile_path,
                repo_root=source_root,
            ),
        ),
        WorkspaceEntryAsset(
            ops_root / "README.md",
            render_medautoscience_readme(profile_relpath=profile_relpath),
            preserve_existing=True,
        ),
        WorkspaceEntryAsset(bin_root / "_shared.sh", _render_shared(profile_relpath), executable=True),
        WorkspaceEntryAsset(bin_root / "bootstrap", _render_bootstrap(), executable=True),
        WorkspaceEntryAsset(bin_root / "enter-study", _render_enter_study(), executable=True),
        WorkspaceEntryAsset(bin_root / "paper-mission", _render_paper_mission(), executable=True),
        WorkspaceEntryAsset(bin_root / "study-progress", _render_study_progress(), executable=True),
        WorkspaceEntryAsset(
            bin_root / "study-state-matrix",
            _render_study_state_matrix(),
            executable=True,
        ),
    )


def _is_managed_workspace_entry(path: Path, content: str) -> bool:
    if GENERATED_MARKER in content:
        return True
    if path.name == "config.env.example":
        return "MED_AUTOSCIENCE_REPO=" in content and "MED_AUTOSCIENCE_PROFILE=" in content
    if path.name == "_shared.sh":
        return "MEDAUTOSCI_OPS_ROOT=" in content and "run_medautosci()" in content
    return 'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"' in content


def materialize_workspace_entries(
    *,
    workspace_root: Path,
    profile_ref: Path,
    repo_root: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, object]:
    root = workspace_root.expanduser().resolve()
    profile_path = _resolved_profile_path(workspace_root=root, profile_ref=profile_ref)
    source_root = (repo_root or _repo_config_path()).expanduser().resolve()
    if not profile_path.is_file():
        raise FileNotFoundError(f"Workspace profile does not exist: {profile_path}")
    carrier = source_root / "scripts" / "opl-module-dispatch.sh"
    if not carrier.is_file():
        raise FileNotFoundError(f"Canonical MAS domain-entry carrier does not exist: {carrier}")

    created: list[str] = []
    upgraded: list[str] = []
    unchanged: list[str] = []
    preserved: list[str] = []
    blocked: list[str] = []
    for asset in workspace_entry_assets(
        workspace_root=root,
        profile_ref=profile_path,
        repo_root=source_root,
    ):
        target = asset.path
        existing = target.read_text(encoding="utf-8") if target.is_file() else None
        if existing == asset.content:
            unchanged.append(str(target))
            if asset.executable and not dry_run:
                target.chmod(0o755)
            continue
        if existing is not None and asset.preserve_existing and not force:
            preserved.append(str(target))
            continue
        if existing is not None and not force and not _is_managed_workspace_entry(target, existing):
            blocked.append(str(target))
            continue

        destination = upgraded if existing is not None else created
        destination.append(str(target))
        if dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(asset.content, encoding="utf-8")
        if asset.executable:
            target.chmod(0o755)

    return {
        "surface_kind": "mas_workspace_entry_compatibility_materialization",
        "workspace_root": str(root),
        "profile_ref": str(profile_path),
        "domain_handler_target": SERVICE_SAFE_ENTRY_TARGET,
        "runtime_environment_owner": "one-person-lab",
        "generated_surface_owner": "one-person-lab",
        "created_files": created,
        "upgraded_files": upgraded,
        "unchanged_files": unchanged,
        "preserved_files": preserved,
        "blocked_files": blocked,
        "dry_run": dry_run,
        "workspace_local_venv_used": False,
        "private_cli_used": False,
    }


__all__ = [
    "GENERATED_MARKER",
    "WorkspaceEntryAsset",
    "materialize_workspace_entries",
    "render_medautoscience_config",
    "render_medautoscience_readme",
    "workspace_entry_assets",
]
