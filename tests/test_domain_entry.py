from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.mark.parametrize("command", ("product-entry-status", "skill-catalog"))
def test_domain_entry_rejects_removed_public_wrapper_commands(command: str, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile_ref = tmp_path / "profile.local.toml"

    with pytest.raises(ValueError, match="不支持的 domain entry command"):
        module.MedAutoScienceDomainEntry().dispatch(
            {
                "command": command,
                "profile_ref": str(profile_ref),
            }
        )


def test_domain_entry_launch_study_forwards_explicit_user_wakeup(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    called: dict[str, object] = {}

    def fake_launch_study(
        *,
        profile,
        profile_ref,
        study_id: str,
        entry_mode: str | None,
        allow_stopped_relaunch: bool,
        explicit_user_wakeup: bool,
        force: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["entry_mode"] = entry_mode
        called["allow_stopped_relaunch"] = allow_stopped_relaunch
        called["explicit_user_wakeup"] = explicit_user_wakeup
        called["force"] = force
        return {"surface_kind": "launch_study", "runtime_status": {"decision": "resume"}}

    monkeypatch.setattr(module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(module, "launch_study", fake_launch_study)

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "launch-study",
            "profile_ref": str(profile_ref),
            "study_id": "001-risk",
            "entry_mode": "full_research",
            "allow_stopped_relaunch": True,
            "explicit_user_wakeup": True,
            "force": True,
        }
    )

    assert payload["command"] == "launch-study"
    assert called["profile"] is profile
    assert called["profile_ref"] == profile_ref
    assert called["study_id"] == "001-risk"
    assert called["entry_mode"] == "full_research"
    assert called["allow_stopped_relaunch"] is True
    assert called["explicit_user_wakeup"] is True
    assert called["force"] is True


def test_domain_entry_submit_study_task_forwards_task_intake_kind(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    called: dict[str, object] = {}

    def fake_submit_study_task(**kwargs):
        called.update(kwargs)
        return {"surface_kind": "submit_study_task"}

    monkeypatch.setattr(module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(module, "submit_study_task", fake_submit_study_task)

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "submit-study-task",
            "profile_ref": str(profile_ref),
            "study_id": "001-risk",
            "task_intent": "review evidence",
            "task_intake_kind": "owner_request",
        }
    )

    assert payload["command"] == "submit-study-task"
    assert called["task_intake_kind"] == "owner_request"


def test_external_caller_can_consume_domain_entry_contract_without_repo_local_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    domain_entry_module = importlib.import_module("med_autoscience.domain_entry")
    contract_module = importlib.import_module("med_autoscience.domain_entry_contract")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    contract = contract_module.build_domain_entry_contract()
    captured: dict[str, object] = {}

    monkeypatch.setattr(domain_entry_module, "load_profile", lambda ref: profile)
    def fake_read_study_progress(**kwargs):
        captured.update(kwargs)
        return {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前由 MAS 监管论文推进。",
        }

    monkeypatch.setattr(domain_entry_module, "read_study_progress", fake_read_study_progress)

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
    assert captured["sync_runtime_summary"] is False
    assert captured["materialize_read_model_artifacts"] is False


def test_domain_entry_rejects_missing_required_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")

    with pytest.raises(ValueError, match="缺少必填字段"):
        module.MedAutoScienceDomainEntry().dispatch(
            {
                "command": "study-progress",
                "profile_ref": str(tmp_path / "profile.local.toml"),
            }
        )


def test_domain_entry_dispatches_display_pack_agent_plan_without_profile() -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    repo_root = Path(__file__).resolve().parents[1]

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "display-pack-figure-plan",
            "repo_root": str(repo_root),
            "figure_request": {
                "figure_kind": "evidence_figure",
                "audit_family": "Prediction Performance",
                "preferred_renderer_family": "r_ggplot2",
                "query": "roc",
            },
        }
    )

    assert payload["command"] == "display-pack-figure-plan"
    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["authority_boundary"]["can_authorize_publication_readiness"] is False


def test_domain_entry_dispatches_display_pack_agent_orchestrate_without_profile(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    from med_autoscience.publication_display_contract import seed_publication_display_contracts_if_missing

    repo_root = Path(__file__).resolve().parents[1]
    paper_root = tmp_path / "paper"
    seed_publication_display_contracts_if_missing(paper_root=paper_root)

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "display-pack-orchestrate",
            "repo_root": str(repo_root),
            "paper_root": str(paper_root),
            "current_owner_delta": {
                "action_type": "display_pack_orchestrate",
                "display_intent": "Create a ROC curve for prediction performance.",
            },
            "claim_ref": "claim:roc",
            "data_ref": "data:roc",
            "check_runtime_dependencies": False,
        }
    )

    assert payload["command"] == "display-pack-orchestrate"
    assert payload["surface_kind"] == "display_pack_agent_orchestration"
    assert payload["status"] == "needs_repair"
    assert payload["plan"]["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["preflight"]["blocking_findings"] == [
        {
            "code": "render_r_missing",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
            "route_hint": "renderer_asset_repair",
        }
    ]
    assert payload["next_callable"] == "display-pack-repair"
    assert payload["authority_boundary"]["can_authorize_publication_readiness"] is False


def test_domain_entry_contract_exports_display_pack_agent_commands() -> None:
    contract_module = importlib.import_module("med_autoscience.domain_entry_contract")

    contracts = {
        item["command"]: item
        for item in contract_module.build_domain_entry_contract()["command_contracts"]
    }

    assert contracts["display-pack-capability-discover"]["optional_fields"] == [
        "repo_root",
        "paper_root",
        "include_templates",
        "opl_descriptor_output_dir",
    ]
    assert "current_owner_delta" in contracts["display-pack-orchestrate"]["optional_fields"]
    assert "figure_request" in contracts["display-pack-orchestrate"]["optional_fields"]
    assert contracts["display-pack-figure-plan"]["required_fields"] == ["figure_request"]
    assert contracts["display-pack-render"]["required_fields"] == ["paper_root"]
    assert "visual_audit_review" in contracts["display-pack-render"]["optional_fields"]


def test_action_catalog_targets_and_required_fields_match_real_domain_entry_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    domain_entry_module = importlib.import_module("med_autoscience.domain_entry")
    contract_module = importlib.import_module("med_autoscience.domain_entry_contract")
    catalog = json.loads(
        (Path(__file__).resolve().parents[1] / "contracts/action_catalog.json").read_text(
            encoding="utf-8"
        )
    )
    actions = {item["action_id"]: item for item in catalog["actions"]}
    calls = _install_required_only_dispatch_handlers(monkeypatch, tmp_path)
    profile = make_profile(tmp_path)
    monkeypatch.setattr(domain_entry_module, "load_profile", lambda ref: profile)
    entry = domain_entry_module.MedAutoScienceDomainEntry(profile_loader=lambda ref: profile)

    assert set(actions) == {
        command.replace("-", "_") for command in contract_module.SERVICE_SAFE_DOMAIN_COMMANDS
    }
    for command, spec in contract_module.SERVICE_SAFE_DOMAIN_COMMANDS.items():
        action = actions[command.replace("-", "_")]
        target = contract_module.domain_entry_handler_target(command)
        assert action["required_fields"] == list(spec.required_fields)
        assert action["optional_fields"] == list(spec.optional_fields)
        assert action["workspace_locator_fields"] == list(spec.required_fields)
        assert action["input_schema_ref"] == (
            "contracts/schemas/v1/mas-action.input.schema.json#/$defs/"
            f"{command.replace('-', '_')}"
        )
        assert action["source_command"]["command"] == target
        for surface in ("cli", "mcp", "product_entry", "skill"):
            assert action["supported_surfaces"][surface]["command"] == target

        module_name, symbol_ref = target.split(":", 1)
        symbol_path, target_action_id = symbol_ref.split("#", 1)
        owner_name, method_name = symbol_path.split(".", 1)
        owner = getattr(importlib.import_module(module_name), owner_name)
        assert callable(getattr(owner, method_name))
        assert target_action_id == command.replace("-", "_")

        request = _required_only_request(command, spec.required_fields, tmp_path)
        assert set(request) == {"command", *spec.required_fields}
        payload = entry.dispatch(request)
        assert payload["command"] == command

        input_schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "contracts/schemas/v1/mas-action.input.schema.json"
            ).read_text(encoding="utf-8")
        )["$defs"][command.replace("-", "_")]
        assert input_schema["required"] == list(spec.required_fields)
        assert set(input_schema["properties"]) == {
            *spec.required_fields,
            *spec.optional_fields,
        }

    assert set(calls) == set(contract_module.SERVICE_SAFE_DOMAIN_COMMANDS)
    assert calls["scientific-capability-registry"]["args"] == ()
    assert calls["display-pack-capability-discover"]["kwargs"] == {
        "repo_root": None,
        "paper_root": None,
        "include_templates": False,
        "opl_descriptor_output_dir": None,
    }
    assert calls["research-integrity-gate-input"]["kwargs"] == {
        "reference_checks": (),
        "claim_spans": (),
        "citation_refs": (),
        "evidence_refs": (),
        "reference_attestation_refs": (),
        "manuscript_sections": None,
        "numeric_facts": None,
        "display_facts": None,
        "reporting_checklist_expectations": None,
    }
    assert calls["research-integrity-reference-verification"]["kwargs"] == {"payload": {}}
    assert calls["research-integrity-review-publication-gate-stage-hook"]["kwargs"] == {
        "payload": {}
    }
    assert calls["delivery-authority-backfill-apply"]["kwargs"] == {
        "workspace_roots": (tmp_path.resolve(),),
        "apply": False,
        "authority_snapshot": None,
    }


def test_domain_entry_dispatches_delivery_authority_backfill_apply(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    backfill = importlib.import_module("med_autoscience.controllers.delivery_authority_backfill_apply")
    workspace_root = tmp_path / "workspace"
    called: dict[str, object] = {}

    def fake_run_backfill_apply(*, workspace_roots, apply, authority_snapshot):
        called.update(
            workspace_roots=tuple(workspace_roots),
            apply=apply,
            authority_snapshot=authority_snapshot,
        )
        return {"surface": "delivery_authority_backfill_apply", "status": "planned"}

    monkeypatch.setattr(backfill, "run_backfill_apply", fake_run_backfill_apply)
    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "delivery-authority-backfill-apply",
            "workspace_roots": [str(workspace_root)],
            "apply": False,
            "authority_snapshot": {"decision": "inspect"},
        }
    )

    assert payload["command"] == "delivery-authority-backfill-apply"
    assert called == {
        "workspace_roots": (workspace_root.resolve(),),
        "apply": False,
        "authority_snapshot": {"decision": "inspect"},
    }


def test_domain_entry_rejects_control_plane_cleanup_apply(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"

    with pytest.raises(ValueError, match="不支持的 domain entry command"):
        module.MedAutoScienceDomainEntry().dispatch({
            "command": "control-plane-cleanup-apply",
            "workspace_roots": [str(workspace_root)],
            "apply": True,
        })


def test_domain_entry_contract_exports_domain_agent_entry_spec_v1() -> None:
    module = importlib.import_module("med_autoscience.domain_entry_contract")

    contract = module.build_domain_entry_contract()
    spec = contract["domain_agent_entry_spec"]

    assert spec["surface_kind"] == "domain_agent_entry_spec"
    assert spec["agent_id"] == "mas"
    assert spec["title"] == "MAS Domain Agent Entry (v1)"
    assert "可审计的入口与进度语义" in spec["description"]
    assert spec["default_engine"] == "codex"
    assert spec["workspace_requirement"] == "required"
    assert spec["locator_schema"] == {
        "required_fields": ["profile_ref"],
        "optional_fields": ["study_id", "entry_mode"],
    }
    assert spec["codex_entry_strategy"] == "domain_agent_entry"
    assert spec["artifact_conventions"] == "paper_and_submission_package"
    assert spec["progress_conventions"] == "study_runtime_narration"
    assert spec["entry_command"] == "study-progress"
    assert spec["manifest_command"] == "opl-generated-product-entry"
    assert contract["surface_role"] == "domain_handler_target_for_opl_generated_interfaces"
    assert contract["generated_descriptor_owner"] == "one-person-lab"
    assert contract["domain_handler_target_owner"] == "MedAutoScience"
    assert contract["domain_repo_can_own_generated_surface"] is False
    assert contract["authority_boundary"] == {
        "opl_owns_generated_cli_mcp_skill_product_status_workbench_descriptors": True,
        "mas_executes_domain_handlers_and_signs_owner_receipts": True,
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_quality_or_export": False,
    }


def _install_required_only_dispatch_handlers(monkeypatch, tmp_path: Path) -> dict[str, dict[str, object]]:
    calls: dict[str, dict[str, object]] = {}

    def capture(command: str):
        def handler(*args: object, **kwargs: object) -> dict[str, object]:
            calls[command] = {"args": args, "kwargs": kwargs}
            return {"surface_kind": command}

        return handler

    domain_entry = importlib.import_module("med_autoscience.domain_entry")
    monkeypatch.setattr(domain_entry, "read_study_progress", capture("study-progress"))
    monkeypatch.setattr(domain_entry, "launch_study", capture("launch-study"))
    monkeypatch.setattr(domain_entry, "submit_study_task", capture("submit-study-task"))

    module_handlers = {
        "med_autoscience.controllers.study_state_matrix": {
            "build_study_state_matrix": "study-state-matrix",
        },
        "med_autoscience.controllers.submission_inspection_export": {
            "export_inspection_package": "export-inspection-package",
        },
        "med_autoscience.controllers.publication_aftercare": {
            "build_publication_aftercare_plan": "publication-aftercare-plan",
        },
        "med_autoscience.controllers.delivery_authority_backfill_apply": {
            "run_backfill_apply": "delivery-authority-backfill-apply",
        },
        "med_autoscience.external_learning_adoption_closure": {
            "build_external_learning_adoption_closure": "external-learning-adoption-closure",
        },
        "med_autoscience.scientific_capability_registry": {
            "build_scientific_capability_registry_summary": "scientific-capability-registry",
        },
        "med_autoscience.controllers.mainline_status": {
            "read_mainline_status": "mainline-status",
            "read_mainline_phase_status": "mainline-phase",
        },
        "med_autoscience.display_pack_agent": {
            "display_pack_capability_discover": "display-pack-capability-discover",
            "display_pack_orchestrate": "display-pack-orchestrate",
            "display_pack_figure_plan": "display-pack-figure-plan",
            "display_pack_preflight": "display-pack-preflight",
            "display_pack_render": "display-pack-render",
        },
        "med_autoscience.research_integrity.gate_bundle": {
            "build_research_integrity_gate_input_bundle": "research-integrity-gate-input",
        },
        "med_autoscience.research_integrity.reference_verification": {
            "build_reference_verification_payload": "research-integrity-reference-verification",
        },
        "med_autoscience.research_integrity.stage_hooks": {
            "build_review_publication_gate_stage_hook_payload": (
                "research-integrity-review-publication-gate-stage-hook"
            ),
        },
        "med_autoscience.controllers.owner_route_handoff.domain_handler_export": {
            "export_family_domain_handler": "domain-handler-export",
        },
        "med_autoscience.controllers.owner_route_handoff.dispatch_orchestration": {
            "dispatch_family_domain_handler_task": "domain-handler-dispatch",
        },
    }
    for module_name, handlers in module_handlers.items():
        module = importlib.import_module(module_name)
        for function_name, command in handlers.items():
            monkeypatch.setattr(module, function_name, capture(command))

    return calls


def _required_only_request(
    command: str,
    required_fields: tuple[str, ...],
    tmp_path: Path,
) -> dict[str, object]:
    task_ref = tmp_path / "domain-handler-task.json"
    task_ref.write_text('{"task_kind":"generated-interface-parity"}\n', encoding="utf-8")
    values: dict[str, object] = {
        "profile_ref": str(tmp_path / "profile.local.toml"),
        "study_id": "study-001",
        "task_intent": "inspect",
        "study_root": str(tmp_path / "study"),
        "workspace_roots": [str(tmp_path)],
        "mode": "summary",
        "figure_request": {},
        "paper_root": str(tmp_path / "paper"),
        "task_ref": str(task_ref),
    }
    return {"command": command, **{field: values[field] for field in required_fields}}


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
