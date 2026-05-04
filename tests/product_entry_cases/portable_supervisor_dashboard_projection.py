from __future__ import annotations

import json

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ready_report() -> SimpleNamespace:
    return SimpleNamespace(
        workspace_exists=True,
        runtime_exists=True,
        studies_exists=True,
        portfolio_exists=True,
        med_deepscientist_runtime_exists=True,
        medical_overlay_ready=True,
        external_runtime_contract={"ready": True},
        workspace_supervision_contract={
            "status": "loaded",
            "loaded": True,
            "summary": "Runtime supervision online.",
            "drift_reasons": [],
        },
    )


def test_workspace_cockpit_and_frontdesk_surface_portable_supervisor_queue_dashboard(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")
    hourly_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    hourly_payload = {
        "surface": "portable_supervisor_hourly_projection",
        "schema_version": 1,
        "generated_at": "2026-05-04T06:00:00+00:00",
        "authority": "observability_only",
        "developer_supervisor_mode": {
            "mode": "developer_apply_safe",
            "mode_label": "Developer Supervisor Mode",
            "scheduler_owner": "external_scheduler",
            "codex_app_heartbeat_required": False,
            "safe_actions_enabled": True,
            "repo_level_repair_authority": True,
            "github_user_gate": {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None},
        },
        "studies": [
            {
                "study_id": "001-risk",
                "quest_status": "blocked",
                "active_run_id": "run-001",
                "runtime_health": {"health_status": "external_supervisor_required"},
                "artifact_delta": {"status": "stale", "summary": "No new paper artifact delta."},
                "gate_specificity": {
                    "status": "blocked",
                    "blocked_reason": "publication_gate_specificity_required",
                },
                "ai_reviewer_status": {
                    "status": "trace_missing",
                    "summary": "AI reviewer trace missing.",
                },
                "action_queue": [
                    {
                        "action_type": "publication_gate_specificity_required",
                        "summary": "Request gate specificity.",
                    }
                ],
                "why_not_applied": ["runtime_recovery_retry_budget_exhausted"],
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "blocked_reason": "runtime_recovery_not_authorized",
            }
        ],
    }
    _write_json(hourly_path, hourly_payload)

    monkeypatch.setattr(module, "build_doctor_report", lambda profile: _ready_report())
    monkeypatch.setattr(
        module,
        "_inspect_workspace_supervision",
        lambda profile: {
            "manager": "launchd",
            "status": "loaded",
            "loaded": True,
            "job_exists": True,
            "summary": "Runtime supervision online.",
            "drift_reasons": [],
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {"id": "portable_supervisor_v2", "status": "in_progress"},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "Queue is blocked by runtime recovery.",
            "current_blockers": [],
            "next_system_action": "Inspect supervisor queue action.",
            "portable_supervisor_dashboard": {
                **dict(hourly_payload["studies"][0]),
                **dict(hourly_payload["developer_supervisor_mode"]),
            },
            "supervision": {"active_run_id": "run-001", "health_status": "external_supervisor_required"},
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {"action_mode": "inspect_progress"},
            "needs_physician_decision": False,
            "needs_user_decision": False,
            "task_intake": {},
            "progress_freshness": {"status": "fresh"},
        },
    )
    monkeypatch.setattr(
        module,
        "build_product_entry_manifest",
        lambda **kwargs: {
            "target_domain_id": "med-autoscience",
            "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
            "summary": {
                "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
            },
            "gateway_interaction_contract": {
                "frontdoor_owner": "opl_gateway_or_domain_gui",
                "user_interaction_mode": "natural_language_frontdoor",
            },
            "product_entry_preflight": {
                "surface_kind": "product_entry_preflight",
                "ready_to_try_now": True,
                "summary": "preflight ready",
                "recommended_check_command": "uv run python -m med_autoscience.cli doctor",
            },
            "product_entry_quickstart": {
                "surface_kind": "product_entry_quickstart",
                "steps": [],
            },
            "single_project_boundary": {
                "surface_kind": "single_project_boundary",
                "summary": "summary",
                "mas_owner_modules": ["controller_charter"],
                "mds_retained_roles": [{"role_id": "research_backend", "title": "Research backend", "summary": "summary"}],
                "post_gate_only": ["physical migration"],
                "not_now": ["not now"],
            },
            "capability_owner_boundary": {
                "surface_kind": "mas_capability_owner_boundary",
                "owner": "MedAutoScience",
                "summary": "summary",
                "mas_owned_capabilities": [
                    {
                        "capability_id": "portable_supervisor_dashboard",
                        "owner": "MedAutoScience",
                        "truth_surface": "artifacts/supervision/hourly/latest.json",
                        "summary": "Supervisor queue dashboard projection.",
                    }
                ],
                "mds_migration_only_roles": [
                    {
                        "role_id": "research_backend",
                        "migration_only": True,
                        "summary": "Research backend remains external.",
                    }
                ],
                "proof_and_absorb_boundary": {
                    "parity_status": "not_started",
                    "physical_absorb_status": "blocked_post_gate",
                    "parity_proof_sources": ["focused tests"],
                    "physical_absorb_gate": ["external runtime gate"],
                },
            },
        },
    )
    monkeypatch.setattr(module, "_validate_product_frontdesk_contract", lambda payload: None)
    monkeypatch.setattr(
        module,
        "_build_shared_family_product_frontdesk_from_manifest",
        lambda **kwargs: {
            **dict(kwargs.get("product_entry_manifest") or {}),
            **dict(kwargs.get("extra_payload") or {}),
            "target_domain_id": "med-autoscience",
            "schema_ref": kwargs.get("schema_ref"),
        },
    )

    cockpit = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    frontdesk = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
    cockpit_markdown = module.render_workspace_cockpit_markdown(cockpit)
    frontdesk_markdown = module.render_product_frontdesk_markdown(frontdesk)

    dashboard = cockpit["portable_supervisor_queue_dashboard"]
    assert dashboard["surface_kind"] == "portable_supervisor_queue_dashboard"
    assert dashboard["authority"] == "observability_only"
    assert dashboard["source_path"] == str(hourly_path)
    assert dashboard["supervisor_mode"] == {
        "mode": "developer_apply_safe",
        "mode_label": "Developer Supervisor Mode",
        "scheduler_owner": "external_scheduler",
        "codex_app_heartbeat_required": False,
        "safe_actions_enabled": True,
        "repo_level_repair_authority": True,
        "github_user_gate": {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None},
    }
    assert dashboard["counts"]["external_supervisor_required"] == 1
    assert dashboard["studies"][0]["mode"] == "developer_apply_safe"
    assert dashboard["studies"][0]["github_user_gate"] == {"expected_login": "gaofeng21cn", "login": "gaofeng21cn", "allowed": True, "source": "env", "reason": None}
    assert dashboard["studies"][0]["blocked_reason"] == "runtime_recovery_not_authorized"
    assert dashboard["studies"][0]["action_queue"][0]["action_type"] == "publication_gate_specificity_required"
    assert frontdesk["workspace_portable_supervisor_queue_dashboard"]["studies"][0]["why_not_applied"] == [
        "runtime_recovery_retry_budget_exhausted"
    ]
    assert frontdesk["workspace_portable_supervisor_queue_dashboard"]["supervisor_mode"]["mode"] == "developer_apply_safe"
    assert "Portable Supervisor Queue" in cockpit_markdown
    assert "developer supervisor mode: `developer_apply_safe`" in cockpit_markdown
    assert "Codex App heartbeat is an outer developer supervisor signal" in cockpit_markdown
    assert "publication_gate_specificity_required" in cockpit_markdown
    assert "runtime_recovery_not_authorized" in cockpit_markdown
    assert "Portable Supervisor Queue" in frontdesk_markdown
    assert "developer supervisor mode: `developer_apply_safe`" in frontdesk_markdown
    assert "Codex App heartbeat is an outer developer supervisor signal" in frontdesk_markdown
    assert "runtime_recovery_retry_budget_exhausted" in frontdesk_markdown
