from __future__ import annotations

from .local_time import (
    local_time_projection,
    localtime_symlink_target,
    system_timezone_name,
    timezone_name_from_localtime_target,
    valid_timezone_name,
)
from .rendering import (
    condition_badge,
    condition_section,
    event_section,
    gate_text,
    list_html,
    list_section,
    local_time_label,
    portal_css,
    refresh_meta,
    runtime_continuity_section,
    section,
    status_chip,
    status_label,
)
from .status_display import display_text
from .section_explanations import (
    progress_section_explanations,
    render_section_explanations_section,
)
from .source_refs import (
    display_source_refs,
    source_ref_allowed,
    source_refs,
)
from .study_workbench import (
    ARTIFACT_GROUPS,
    build_study_workbench_payload,
    render_study_workbench_sections,
)
from .live_console_shell import (
    LIVE_CONSOLE_HTML_REF,
    LIVE_CONSOLE_SERVE_COMMAND,
    LIVE_CONSOLE_SESSION_READ_MODEL_REF,
    live_console_projection,
    render_live_console_portal_link,
    render_live_console_static_shell,
)
from .workspace_overview import (
    dedupe_texts,
    render_workspace_studies_section,
    render_workspace_alerts_section,
    selected_workspace_study_id,
    unique_text,
    workspace_alert_projection,
    workspace_studies,
)
from .workspace_summary import (
    workspace_delivery_paragraphs,
    workspace_next_step_paragraphs,
    workspace_quality_paragraphs,
    workspace_status_paragraphs,
)

__all__ = [
    "LIVE_CONSOLE_HTML_REF",
    "LIVE_CONSOLE_SERVE_COMMAND",
    "LIVE_CONSOLE_SESSION_READ_MODEL_REF",
    "ARTIFACT_GROUPS",
    "build_study_workbench_payload",
    "condition_badge",
    "condition_section",
    "dedupe_texts",
    "display_text",
    "display_source_refs",
    "event_section",
    "gate_text",
    "list_html",
    "list_section",
    "live_console_projection",
    "local_time_label",
    "local_time_projection",
    "localtime_symlink_target",
    "portal_css",
    "progress_section_explanations",
    "refresh_meta",
    "render_workspace_studies_section",
    "render_workspace_alerts_section",
    "render_study_workbench_sections",
    "render_live_console_portal_link",
    "render_section_explanations_section",
    "render_live_console_static_shell",
    "runtime_continuity_section",
    "section",
    "source_ref_allowed",
    "source_refs",
    "status_chip",
    "status_label",
    "selected_workspace_study_id",
    "system_timezone_name",
    "timezone_name_from_localtime_target",
    "unique_text",
    "valid_timezone_name",
    "workspace_alert_projection",
    "workspace_delivery_paragraphs",
    "workspace_next_step_paragraphs",
    "workspace_quality_paragraphs",
    "workspace_status_paragraphs",
    "workspace_studies",
]
