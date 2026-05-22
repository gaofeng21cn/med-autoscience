from __future__ import annotations

from .owner_route_handoff_command_cases.shared import _write_json
from .shared import *  # noqa: F403,F401
from tests.transition_descriptor_assertions import (  # noqa: E402
    assert_family_transition_descriptor_shape,
    resolve_json_pointer,
)


def test_sidecar_export_exposes_domain_declared_transition_spec_without_domain_truth_write(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "publication-blocked"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "status": "blocked",
            "blockers": ["claim_specificity_gap"],
            "assessment_provenance": {"owner": "publication_gate"},
        },
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    descriptor = payload["family_transition_spec_descriptor"]
    assert descriptor["authority_boundary"]["runner_owner"] == "OPL Framework"
    assert descriptor["authority_boundary"]["can_write_domain_truth"] is False
    assert descriptor["authority_boundary"]["opl_interprets_domain_quality"] is False
    assert_family_transition_descriptor_shape(descriptor)
    sidecar_locator_payload = {"mas_family_sidecar_export": payload}
    assert (
        resolve_json_pointer(sidecar_locator_payload, descriptor["locator_refs"]["sidecar_export_descriptor"])
        == descriptor
    )
    assert (
        resolve_json_pointer(sidecar_locator_payload, descriptor["source_refs"]["sidecar_export_descriptor"])
        == descriptor
    )
    assert payload["authority_boundary"]["writes_domain_truth"] is False
