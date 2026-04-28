from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from . import cockpit_status_and_frontdesk_focus as _cockpit_status_and_frontdesk_focus
from . import manifest_launch_and_task_intake as _manifest_launch_and_task_intake

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_cockpit_status_and_frontdesk_focus)
_module_reexport(_manifest_launch_and_task_intake)

from .repo_shell_runtime_assertions import assert_manifest_runtime_and_continuity
from .repo_shell_entry_assertions import assert_manifest_entry_and_lifecycle_surfaces
from .repo_shell_preflight_assertions import assert_manifest_preflight_and_guardrail_surfaces
from .repo_shell_phase_assertions import assert_manifest_phase_and_readiness_surfaces

def test_build_product_entry_manifest_projects_repo_shell_and_shared_handoff_templates(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
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
                "summary": "Hermes-hosted runtime supervision 已在线。",
                "drift_reasons": [],
            },
        ),
    )

    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {
                "id": "f4_blocker_closeout",
                "status": "in_progress",
                "summary": "继续收口 blocker 并把用户入口壳压实。",
            },
            "current_program_phase": {
                "id": "phase_2_user_product_loop",
                "status": "in_progress",
                "summary": "把用户 inbox 与持续进度回路收成稳定壳。",
            },
            "next_focus": [
                "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
            ],
            "remaining_gaps": [
                "mature standalone medical product entry is still not landed",
            ],
        },
    )

    payload = module.build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
    )

    assert_manifest_runtime_and_continuity(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    assert_manifest_entry_and_lifecycle_surfaces(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    assert_manifest_preflight_and_guardrail_surfaces(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    assert_manifest_phase_and_readiness_surfaces(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
