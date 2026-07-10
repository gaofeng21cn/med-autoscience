from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evo_scientist_projection_and_contract_preserve_nonblocking_authority() -> None:
    module = importlib.import_module("med_autoscience.evo_scientist_learning_projection")
    projection = module.build_evo_scientist_learning_projection()
    contract = json.loads(
        (REPO_ROOT / "contracts/evo_scientist_progress_accelerator.json").read_text(
            encoding="utf-8"
        )
    )

    assert projection["surface_kind"] == (
        "mas_evo_scientist_progress_accelerator_projection"
    )
    assert projection["progress_accelerator_contract_ref"] == (
        "contracts/evo_scientist_progress_accelerator.json"
    )
    assert contract["projection_builder_ref"] == projection["projection_builder_ref"]
    assert contract["runtime_sidecar_execution_surface"] == projection[
        "runtime_sidecar_execution_surface"
    ]

    boundary = projection["ordinary_progress_boundary"]
    assert boundary["diagnostic_only"] is True
    assert boundary["refs_only"] is True
    assert boundary["can_select_next_action"] is False
    assert boundary["can_generate_owner_receipt"] is False
    assert boundary["can_generate_typed_blocker"] is False
    assert boundary["can_authorize_provider_admission"] is False
    assert boundary["can_block_current_owner_action"] is False
    assert boundary["critical_path_waits_for_sidecar"] is False

    architecture = projection["target_sidecar_execution_architecture"]
    assert architecture["architecture_state"] == "repo_callable_worker_landed"
    assert architecture["remaining_learning_plan"] is False
    assert architecture["scheduling_contract"]["mainline_waits_for_sidecar"] is False
    assert architecture["admission_contract"][
        "sidecar_completion_required_for_dispatch"
    ] is False
    assert contract["authority_boundary"]["can_write_domain_truth"] is False
    assert contract["authority_boundary"]["can_authorize_provider_admission"] is False
    assert contract["authority_boundary"]["can_close_stage"] is False
