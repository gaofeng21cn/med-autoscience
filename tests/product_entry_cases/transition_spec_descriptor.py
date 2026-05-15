from __future__ import annotations

import importlib

from .shared import *  # noqa: F403,F401
from tests.transition_descriptor_assertions import (  # noqa: E402
    assert_family_transition_descriptor_shape,
    resolve_json_pointer,
)


def test_product_entry_manifest_exposes_domain_transition_spec_descriptor(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    descriptor = manifest["family_transition_spec_descriptor"]

    assert descriptor["authority_boundary"] == {
        "runner_owner": "OPL Framework",
        "domain_transition_owner": "MedAutoScience",
        "can_write_domain_truth": False,
        "opl_interprets_domain_quality": False,
        "opl_executes_domain_action": False,
    }
    assert_family_transition_descriptor_shape(descriptor)
    manifest_locator_payload = {"product_entry_manifest": manifest}
    assert (
        resolve_json_pointer(
            manifest_locator_payload,
            descriptor["locator_refs"]["product_entry_manifest_descriptor"],
        )
        == descriptor
    )
