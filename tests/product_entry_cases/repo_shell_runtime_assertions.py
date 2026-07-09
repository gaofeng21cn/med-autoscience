from __future__ import annotations


def assert_manifest_runtime_and_continuity(*, module, payload, profile, profile_ref) -> None:
    assert payload["surface_kind"] == "product_entry_manifest"
    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["runtime"]["runtime_owner"] == "one-person-lab"
    assert payload["runtime"]["domain_owner"] == "med-autoscience"
    assert payload["managed_runtime_contract"]["domain_owner"] == "med-autoscience"
    assert payload["runtime_inventory"]["surface_kind"] == "runtime_inventory"
    assert payload["runtime_inventory"]["workspace_binding"]["workspace_root"] == str(profile.workspace_root)
    assert payload["session_continuity"]["domain_agent_id"] == "mas"
    assert payload["progress_projection"]["progress_surface"]["surface_kind"] == "study_progress"
    assert payload["owner_route"]["next_owner"] == "med-autoscience"
