from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evo_scientist_projection_is_declarative_and_non_authoritative() -> None:
    module = importlib.import_module("med_autoscience.evo_scientist_learning_projection")
    projection = module.build_evo_scientist_learning_projection()
    contract = json.loads(
        (REPO_ROOT / "contracts/evo_scientist_progress_accelerator.json").read_text(
            encoding="utf-8"
        )
    )

    assert projection["status"] == "declarative_external_pattern_projection"
    assert projection["source_snapshot"]["observed_release"] == "v0.1.4"
    assert projection["source_snapshot"]["skills_release"] == "v1.0.0"
    assert projection["absorbed_pattern_ids"] == contract["absorbed_pattern_ids"]
    assert projection["watch_only_pattern_ids"] == contract["watch_only_pattern_ids"]
    assert projection["rejected_pattern_ids"] == contract["rejected_pattern_ids"]

    delta = projection["domain_delta"]
    assert delta == contract["domain_delta"]
    assert delta["invocation_kind"] == "descriptor_only_current_owner_input_refs"
    assert delta["binding_kind"] == "optional"
    assert delta["resolver_owner"] == "one-person-lab"
    assert delta["memory_accept_reject_owner"] == "MedAutoScience"
    assert delta["runtime_writer"] is None
    assert delta["local_persistence"] == "absent"

    boundary = projection["authority_boundary"]
    assert boundary["domain_truth_owner"] == "MedAutoScience"
    assert boundary["memory_accept_reject_owner"] == "MedAutoScience"
    for field, value in boundary.items():
        if field.startswith("can_"):
            assert value is False
