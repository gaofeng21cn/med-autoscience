from __future__ import annotations

import json
from pathlib import Path
import shlex
import tomllib

from med_autoscience.controllers import workspace_entry_rendering as workspace_entry_rendering_controller
from med_autoscience.developer_supervisor_mode import EXPECTED_DEVELOPER_GITHUB_LOGIN
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout


PROFILE_TABLE_MISNESTED_TOP_LEVEL_KEYS = {
    "developer_supervisor_mode",
    "github_username",
    "mas_developer_github_usernames",
}


def quote_toml_string(value: str | Path) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def render_workspace_profile_entries(
    *,
    workspace_root: Path,
    workspace_name: str,
    default_publication_profile: str,
    default_citation_style: str,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None,
    include_hermes_placeholders: bool,
    github_username: str | None,
) -> list[tuple[str, str]]:
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    entries: list[tuple[str, str]] = [
        ("name", f"name = {quote_toml_string(workspace_name)}"),
        ("workspace_root", f"workspace_root = {quote_toml_string(workspace_root)}"),
        ("runtime_root", f"runtime_root = {quote_toml_string(layout.quests_root)}"),
        ("managed_runtime_home", f"managed_runtime_home = {quote_toml_string(layout.runtime_root)}"),
        ("studies_root", f"studies_root = {quote_toml_string(workspace_root / 'studies')}"),
        ("portfolio_root", f"portfolio_root = {quote_toml_string(workspace_root / 'portfolio')}"),
    ]
    if hermes_agent_repo_root is not None:
        entries.append(
            (
                "hermes_agent_repo_root",
                f"hermes_agent_repo_root = {quote_toml_string(Path(hermes_agent_repo_root).expanduser().resolve())}",
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
                f"hermes_home_root = {quote_toml_string(resolved_hermes_home_root)}",
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
                f"default_publication_profile = {quote_toml_string(default_publication_profile)}",
            ),
            ("default_citation_style", f"default_citation_style = {quote_toml_string(default_citation_style)}"),
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
            ("developer_supervisor_mode", 'developer_supervisor_mode = "external_observe"'),
            (
                "mas_developer_github_usernames",
                f"mas_developer_github_usernames = [{quote_toml_string(EXPECTED_DEVELOPER_GITHUB_LOGIN)}]",
            ),
        ]
    )
    if github_username is not None:
        entries.append(("github_username", f"github_username = {quote_toml_string(github_username)}"))
    return entries


def merge_medautoscience_config_content(*, existing_content: str, workspace_root: Path, profile_relpath: Path) -> str:
    rendered_content = workspace_entry_rendering_controller.render_medautoscience_config(
        workspace_root=workspace_root,
        profile_relpath=profile_relpath,
    )
    existing_values = parse_env_assignments(existing_content)
    rendered_values = parse_env_assignments(rendered_content)
    placeholders_repaired = False
    merged_values: dict[str, str] = {}
    for key, rendered_value in rendered_values.items():
        existing_value = existing_values.get(key)
        if existing_value is None or is_placeholder_path(existing_value):
            merged_values[key] = rendered_value
            placeholders_repaired = placeholders_repaired or existing_value is not None
        else:
            merged_values[key] = existing_value
    if not placeholders_repaired and set(rendered_values).issubset(existing_values):
        return existing_content
    if placeholders_repaired:
        return render_medautoscience_config_from_values(
            workspace_root=workspace_root,
            profile_relpath=profile_relpath,
            values=merged_values,
        )
    rendered_lines = rendered_content.splitlines()
    try:
        node_line_index = next(
            index for index, line in enumerate(rendered_lines) if line.startswith("MED_AUTOSCIENCE_NODE_BIN=")
        )
    except StopIteration:
        return existing_content
    comment_index = node_line_index - 1 if node_line_index > 0 and rendered_lines[node_line_index - 1].startswith("#") else node_line_index
    node_block = "\n".join(rendered_lines[comment_index : node_line_index + 1]).strip()
    if not node_block:
        return existing_content
    base = existing_content.rstrip()
    separator = "\n\n" if base else ""
    return f"{base}{separator}{node_block}\n"


def parse_env_assignments(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if not key.startswith("MED_AUTOSCIENCE_"):
            continue
        try:
            parsed = shlex.split(raw_value, comments=False, posix=True)
        except ValueError:
            parsed = []
        values[key] = parsed[0] if parsed else raw_value.strip().strip("\"'")
    return values


def is_placeholder_path(value: str) -> bool:
    text = value.strip().strip("\"'")
    return not text or text.startswith("/ABS/PATH/TO/")


def render_medautoscience_config_from_values(
    *,
    workspace_root: Path,
    profile_relpath: Path,
    values: dict[str, str],
) -> str:
    rendered_content = workspace_entry_rendering_controller.render_medautoscience_config(
        workspace_root=workspace_root,
        profile_relpath=profile_relpath,
    )
    output_lines: list[str] = []
    for line in rendered_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output_lines.append(line)
            continue
        key, _ = stripped.split("=", 1)
        if key in values:
            output_lines.append(f"{key}={json.dumps(values[key], ensure_ascii=False)}")
        else:
            output_lines.append(line)
    return "\n".join(output_lines).rstrip() + "\n"


def merge_workspace_profile_content(
    *,
    existing_content: str,
    workspace_root: Path,
    workspace_name: str,
    default_publication_profile: str,
    default_citation_style: str,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None,
    github_username: str | None,
) -> str:
    merge_entries = render_workspace_profile_entries(
        workspace_root=workspace_root,
        workspace_name=workspace_name,
        default_publication_profile=default_publication_profile,
        default_citation_style=default_citation_style,
        hermes_agent_repo_root=hermes_agent_repo_root,
        hermes_home_root=hermes_home_root,
        include_hermes_placeholders=False,
        github_username=github_username,
    )
    repaired_content = remove_misnested_workspace_profile_entries(existing_content)
    try:
        payload = tomllib.loads(repaired_content)
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
    }
    if not required_identity_keys.issubset(payload):
        return existing_content
    missing_lines = [
        line
        for key, line in merge_entries
        if key not in payload
    ]
    if not missing_lines:
        return repaired_content
    root_lines, table_lines = split_root_and_table_lines(repaired_content)
    root = "\n".join(root_lines).rstrip()
    tables = "\n".join(table_lines).rstrip()
    merged_root = f"{root}{chr(10) if root else ''}{chr(10).join(missing_lines)}"
    return f"{merged_root}{chr(10) * 2 if tables else chr(10)}{tables}{chr(10) if tables else ''}"


def remove_misnested_workspace_profile_entries(existing_content: str) -> str:
    output_lines: list[str] = []
    in_table = False
    changed = False
    for line in existing_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_table = True
        if in_table:
            key = _profile_assignment_key(stripped)
            if key in PROFILE_TABLE_MISNESTED_TOP_LEVEL_KEYS:
                changed = True
                continue
        output_lines.append(line)
    if not changed:
        return existing_content
    return "\n".join(output_lines).rstrip() + "\n"


def split_root_and_table_lines(content: str) -> tuple[list[str], list[str]]:
    lines = content.rstrip().splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return lines[:index], lines[index:]
    return lines, []


def _profile_assignment_key(stripped_line: str) -> str | None:
    if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
        return None
    key, _ = stripped_line.split("=", 1)
    key = key.strip()
    return key or None
