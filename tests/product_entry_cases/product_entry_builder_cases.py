from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from . import cockpit_status_and_frontdesk_focus as _cockpit_status_and_frontdesk_focus
from . import manifest_launch_and_task_intake as _manifest_launch_and_task_intake
from . import repo_shell_and_handoff_templates as _repo_shell_and_handoff_templates

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_cockpit_status_and_frontdesk_focus)
_module_reexport(_manifest_launch_and_task_intake)
_module_reexport(_repo_shell_and_handoff_templates)

def test_build_product_entry_preflight_uses_shared_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = tmp_path / "profile.local.toml"
    doctor_report = SimpleNamespace(
        workspace_exists=True,
        runtime_exists=True,
        studies_exists=True,
        portfolio_exists=True,
        med_deepscientist_runtime_exists=True,
        medical_overlay_ready=True,
        external_runtime_contract={"ready": True},
        workspace_supervision_contract={"loaded": True},
    )
    captured: dict[str, object] = {}

    def _fake_build_preflight(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "product_entry_preflight", "checks": list(kwargs["checks"])}

    monkeypatch.setattr(module, "_build_shared_product_entry_preflight", _fake_build_preflight)

    payload = module._build_product_entry_preflight(doctor_report=doctor_report, profile_ref=profile_ref)

    assert payload["surface_kind"] == "product_entry_preflight"
    assert len(captured["checks"]) == 8
    assert str(captured["recommended_check_command"]).endswith("doctor --profile " + str(profile_ref.resolve()))
    assert str(captured["recommended_start_command"]).endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )

def test_build_product_entry_guardrails_uses_shared_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}

    def _fake_build_guardrails(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "surface_kind": "product_entry_guardrails",
            "guardrail_classes": list(kwargs["guardrail_classes"]),
            "recovery_loop": list(kwargs["recovery_loop"]),
        }

    monkeypatch.setattr(module, "_build_shared_product_entry_guardrails", _fake_build_guardrails)

    payload = module._build_product_entry_guardrails(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "product_entry_guardrails"
    assert len(captured["guardrail_classes"]) == 5
    assert len(captured["recovery_loop"]) == 4

def test_build_phase3_clearance_lane_uses_shared_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}

    def _fake_build_lane(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase3_host_clearance_lane", "proof_surfaces": list(kwargs["proof_surfaces"])}

    monkeypatch.setattr(module, "_build_shared_clearance_lane", _fake_build_lane)

    payload = module._build_phase3_clearance_lane(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "phase3_host_clearance_lane"
    assert str(captured["recommended_command"]).endswith("doctor --profile " + str(profile_ref.resolve()))
    assert len(captured["clearance_targets"]) == 3
    assert len(captured["clearance_loop"]) == 6
    assert len(captured["proof_surfaces"]) == 5

def test_build_phase4_backend_deconstruction_uses_shared_builder(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    captured: dict[str, object] = {}

    def _fake_build_lane(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase4_backend_deconstruction_lane", "substrate_targets": list(kwargs["substrate_targets"])}

    monkeypatch.setattr(module, "_build_shared_backend_deconstruction_lane", _fake_build_lane)

    payload = module._build_phase4_backend_deconstruction()

    assert payload["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert len(captured["substrate_targets"]) == 2
    assert captured["deconstruction_map_doc"] == "docs/program/med_deepscientist_deconstruction_map.md"

def test_build_phase5_platform_target_uses_shared_builder(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    captured: dict[str, object] = {}

    def _fake_build_platform(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase5_platform_target", "landing_sequence": list(kwargs["landing_sequence"])}

    monkeypatch.setattr(module, "_build_shared_platform_target", _fake_build_platform)

    payload = module._build_phase5_platform_target()

    assert payload["surface_kind"] == "phase5_platform_target"
    assert captured["sequence_scope"] == "monorepo_landing_readiness"
    assert len(captured["landing_sequence"]) == 5

def test_build_product_entry_manifest_uses_shared_family_product_entry_orchestration(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}

    def _fake_build_family_product_entry_orchestration(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "action_graph_ref": {
                "ref_kind": "json_pointer",
                "ref": "/family_orchestration/action_graph",
                "label": "mas family action graph",
            },
            "version": "family-action-graph.v1",
            "action_graph": {
                "graph_id": str(kwargs["graph_id"]),
                "target_domain_id": str(kwargs["target_domain_id"]),
                "graph_kind": str(kwargs["graph_kind"]),
                "graph_version": str(kwargs["graph_version"]),
                "nodes": list(kwargs["nodes"]),
                "edges": list(kwargs["edges"]),
                "entry_nodes": list(kwargs["entry_nodes"]),
                "exit_nodes": list(kwargs["exit_nodes"]),
                "human_gates": list(kwargs["human_gates"]),
                "checkpoint_policy": {
                    "mode": "explicit_nodes",
                    "checkpoint_nodes": list(kwargs["checkpoint_nodes"]),
                },
            },
            "human_gates": list(kwargs["human_gate_previews"]),
            "resume_contract": {
                "surface_kind": str(kwargs["resume_surface_kind"]),
                "session_locator_field": str(kwargs["session_locator_field"]),
                "checkpoint_locator_field": str(kwargs["checkpoint_locator_field"]),
            },
            "event_envelope_surface": dict(kwargs["event_envelope_surface"]),
            "checkpoint_lineage_surface": dict(kwargs["checkpoint_lineage_surface"]),
        }

    monkeypatch.setattr(
        module,
        "_build_shared_family_product_entry_orchestration",
        _fake_build_family_product_entry_orchestration,
    )

    payload = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)

    assert payload["family_orchestration"]["action_graph"]["graph_id"] == "mas_workspace_frontdoor_study_runtime_graph"
    assert captured["graph_kind"] == "study_runtime_orchestration"
    assert [node["node_id"] for node in captured["nodes"]] == [
        "step:open_frontdesk",
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert [edge["on"] for edge in captured["edges"]] == [
        "new_task",
        "resume_study",
        "inspect_status",
        "task_written",
        "progress_refresh",
    ]
    assert captured["entry_nodes"] == ["step:open_frontdesk"]
    assert captured["exit_nodes"] == ["step:continue_study", "step:inspect_progress"]
    assert captured["checkpoint_nodes"] == [
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert [gate["gate_id"] for gate in captured["human_gate_previews"]] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
