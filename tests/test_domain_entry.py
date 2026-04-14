from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def test_domain_entry_dispatches_product_frontdesk(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(
        module.product_entry,
        "build_product_frontdesk",
        lambda *, profile, profile_ref=None: {
            "surface_kind": "product_frontdesk",
            "target_domain_id": "med-autoscience",
        },
    )

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "product-frontdesk",
            "profile_ref": str(profile_ref),
        }
    )

    assert payload == {
        "command": "product-frontdesk",
        "surface_kind": "product_frontdesk",
        "target_domain_id": "med-autoscience",
    }


def test_external_caller_can_consume_domain_entry_contract_without_repo_local_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    product_entry_module = importlib.import_module("med_autoscience.controllers.product_entry")
    domain_entry_module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    product_entry_module.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="继续用统一 frontdoor contract 驱动 MAS，而不是暴露底层命令。",
        entry_mode="full_research",
    )

    product_entry_payload = product_entry_module.build_product_entry(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        direct_entry_mode="opl-handoff",
    )
    contract = product_entry_payload["return_surface_contract"]["domain_entry_contract"]

    monkeypatch.setattr(domain_entry_module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(
        domain_entry_module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前由 MAS 监管论文推进。",
        },
    )

    request = _build_request_from_contract(
        contract,
        "study-progress",
        profile_ref=str(profile_ref),
        study_id="001-risk",
    )
    payload = domain_entry_module.MedAutoScienceDomainEntry().dispatch(request)

    assert request == {
        "command": "study-progress",
        "profile_ref": str(profile_ref),
        "study_id": "001-risk",
    }
    assert payload["command"] == "study-progress"
    assert payload["current_stage"] == "publication_supervision"


def test_domain_entry_rejects_missing_required_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")

    with pytest.raises(ValueError, match="缺少必填字段"):
        module.MedAutoScienceDomainEntry().dispatch(
            {
                "command": "study-progress",
                "profile_ref": str(tmp_path / "profile.local.toml"),
            }
        )


def _build_request_from_contract(
    domain_entry_contract: dict[str, object],
    command: str,
    **context: str,
) -> dict[str, str]:
    for item in domain_entry_contract["command_contracts"]:
        if item["command"] == command:
            request = {"command": command}
            for field in item["required_fields"] + item["optional_fields"]:
                value = context.get(field)
                if value is not None:
                    request[field] = value
            missing_fields = [field for field in item["required_fields"] if field not in request]
            if missing_fields:
                raise AssertionError(f"external caller context 缺少字段: {missing_fields}")
            return request
    raise AssertionError(f"未找到 command contract: {command}")
