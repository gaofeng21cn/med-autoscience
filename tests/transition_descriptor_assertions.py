from __future__ import annotations


EXPECTED_TRANSITION_DESCRIPTOR_MATERIALIZED_SURFACES = {
    "study_state_matrix": [
        "domain_transition_table.family_transition_spec",
        "domain_transition_table.family_transition_matrix_cases",
    ],
    "domain_handler_export": ["family_transition_spec_descriptor"],
    "product_entry_manifest": ["family_transition_spec_descriptor"],
}

EXPECTED_TRANSITION_DESCRIPTOR_LOCATOR_REFS = {
    "study_state_matrix_spec": "/study_state_matrix/domain_transition_table/family_transition_spec",
    "study_state_matrix_cases": "/study_state_matrix/domain_transition_table/family_transition_matrix_cases",
    "domain_handler_export_descriptor": "/mas_family_domain_handler_export/family_transition_spec_descriptor",
    "product_entry_manifest_descriptor": "/product_entry_manifest/family_transition_spec_descriptor",
}

EXPECTED_TRANSITION_DESCRIPTOR_SOURCE_REFS = {
    "study_state_matrix_domain_transition_table": "/study_state_matrix/domain_transition_table",
    "domain_handler_export_descriptor": "/mas_family_domain_handler_export/family_transition_spec_descriptor",
    "product_entry_manifest_descriptor": "/product_entry_manifest/family_transition_spec_descriptor",
}


def resolve_json_pointer(payload: object, pointer: str) -> object:
    current = payload
    if pointer == "":
        return current
    assert pointer.startswith("/")
    for raw_part in pointer.split("/")[1:]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise AssertionError(f"Cannot resolve {pointer!r} through {type(current).__name__}")
    return current


def assert_family_transition_descriptor_shape(descriptor: dict[str, object]) -> None:
    assert descriptor["surface_kind"] == "family_transition_spec_descriptor"
    assert descriptor["target_domain_id"] == "medautoscience"
    assert descriptor["spec_surface_kind"] == "family_transition_spec"
    assert descriptor["contract_version"] == "family-transition-runner.v1"
    assert descriptor["refresh_policy"] == "rebuild_study_state_matrix_before_opl_runner"
    assert (
        descriptor["materialized_surfaces"]
        == EXPECTED_TRANSITION_DESCRIPTOR_MATERIALIZED_SURFACES
    )
    assert descriptor["locator_refs"] == EXPECTED_TRANSITION_DESCRIPTOR_LOCATOR_REFS
    assert descriptor["source_refs"] == EXPECTED_TRANSITION_DESCRIPTOR_SOURCE_REFS
    assert "sidecar_export_spec" not in descriptor["locator_refs"]
    assert "sidecar_export_descriptor" not in descriptor["locator_refs"]
