from __future__ import annotations

from tests.product_entry_cases.attention_queue_and_cockpit_base import *
from tests.product_entry_cases.cockpit_status_and_entry_status_focus import *
from tests.product_entry_cases.authority_operation_manifest import *
from tests.product_entry_cases.manifest_launch_and_task_intake import *
from tests.product_entry_cases.manifest_launch_and_task_intake_cases.test_explicit_wakeup import *
from tests.product_entry_cases.repo_shell_and_handoff_templates import *
from tests.product_entry_cases.product_entry_preflight_and_task_submission import *
from tests.product_entry_cases.product_entry_markdown_and_skill_catalog import *
from tests.product_entry_cases.paper_orchestra_operator_projection import *
from tests.product_entry_cases.open_auto_research_projection import *
from tests.product_entry_cases.opl_current_control_state_handoff_projection import *
from tests.product_entry_cases.delivery_inspection_visibility import *
from tests.product_entry_cases.action_catalog_parity import *
from tests.product_entry_cases.functional_consumer_boundary import *
from tests.product_entry_cases.transition_spec_descriptor import *
from tests.product_entry_cases.functional_closure_projection import *


def test_product_entry_manifest_exposes_paper_mission_default_entry(tmp_path):
    from med_autoscience.controllers.product_entry_parts.manifest_surfaces import build_product_entry_manifest
    from med_autoscience.profiles import load_profile
    from tests.test_cli_cases.shared import write_profile

    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    profile = load_profile(profile_path)

    manifest = build_product_entry_manifest(profile=profile, profile_ref=profile_path)

    paper_mission = manifest["medical_paper_product_entry"]
    assert paper_mission["default_action_intent"] == "paper_mission/start_or_resume"
    assert paper_mission["authority_boundary"]["writes_authority"] is False
    assert "paper-mission drive" in paper_mission["default_command"]
    assert paper_mission["drive_command"] == paper_mission["default_command"]
    assert "paper-mission inspect" in paper_mission["inspect_command"]
    assert "paper_mission" not in manifest["product_entry_shell"]
