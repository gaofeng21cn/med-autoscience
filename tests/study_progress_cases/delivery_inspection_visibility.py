from __future__ import annotations

import sys
from types import ModuleType

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _install_fake_delivery_inspector(monkeypatch, *, captured: dict[str, object]) -> None:
    inspector = ModuleType("med_autoscience.controllers.delivery_inspector")

    def inspect_study_delivery(
        *,
        profile,
        profile_ref=None,
        study_id=None,
        study_root=None,
        publication_profile=None,
    ):
        del publication_profile
        captured["profile_name"] = profile.name
        captured["profile_ref"] = profile_ref
        captured["study_id"] = study_id
        captured["study_root"] = study_root
        return {
            "surface": "delivery_inspector",
            "study_id": "001-risk",
            "mutation_policy": {"read_only": True, "writes_package": False},
            "freshness": {"verdict": "legacy", "delivery_status": "current"},
            "source_package": {
                "root": str(study_root / "paper" / "submission_minimal"),
                "layout_status": "legacy",
                "role": "controller_authorized_source",
            },
            "human_package": {
                "root": str(study_root / "manuscript" / "current_package"),
                "layout_status": "legacy",
                "role": "human_facing_mirror",
            },
            "wording": {
                "source": "submission_minimal = controller-authorized source",
                "mirror": "current_package = human-facing mirror",
                "legacy_upgrade": "Legacy layout upgrades on the next authorized sync.",
            },
        }

    def compact_delivery_inspection(payload):
        captured["compacted_verdict"] = payload["freshness"]["verdict"]
        return {
            "surface": payload["surface"],
            "study_id": payload["study_id"],
            "mutation_policy": payload["mutation_policy"],
            "freshness": payload["freshness"],
            "source_package": payload["source_package"],
            "human_package": payload["human_package"],
            "wording": payload["wording"],
        }

    inspector.inspect_study_delivery = inspect_study_delivery
    inspector.compact_delivery_inspection = compact_delivery_inspection
    monkeypatch.setitem(sys.modules, "med_autoscience.controllers.delivery_inspector", inspector)


def test_study_progress_projects_delivery_inspector_summary_without_authority_changes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    captured: dict[str, object] = {}
    _install_fake_delivery_inspector(monkeypatch, captured=captured)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "write",
                "phase_owner": "publication_gate",
                "current_required_action": "continue_write_stage",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    delivery = result["delivery_inspection"]
    assert captured == {
        "profile_name": "diabetes",
        "profile_ref": None,
        "study_id": None,
        "study_root": study_root,
        "compacted_verdict": "legacy",
    }
    assert delivery["source_labels"] == {
        "submission_minimal": "controller-authorized source",
        "current_package": "human-facing mirror",
    }
    assert delivery["legacy_layout_upgrade_note"] == "legacy layout 会在下一次 authorized sync 升级"
    assert delivery["status"] == "legacy_layout_pending_sync"
    assert delivery["authority"] == "observability_projection_only"
    assert delivery["can_authorize_submission"] is False
    assert delivery["can_authorize_publication_quality"] is False
    assert delivery["can_dispatch_delivery_sync"] is False

    markdown = module.render_study_progress_markdown(result)
    assert "submission_minimal = controller-authorized source" in markdown
    assert "current_package = human-facing mirror" in markdown
    assert "legacy layout 会在下一次 authorized sync 升级" in markdown


def test_delivery_visibility_projection_keeps_stale_visible_for_legacy_layout() -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_visibility_projection")

    projection = module.compact_delivery_inspection_projection(
        {
            "surface": "delivery_inspector",
            "study_id": "001-risk",
            "mutation_policy": {"read_only": True, "writes_package": False},
            "freshness": {"verdict": "stale", "delivery_status": "stale_source_changed"},
            "source_package": {"layout_status": "legacy"},
            "human_package": {"layout_status": "legacy"},
        }
    )

    assert projection["status"] == "stale"
    assert projection["legacy_layout_pending_sync"] is True
    assert projection["summary"] == "delivery status: stale_source_changed"
