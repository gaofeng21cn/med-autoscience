from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "plugins/med-autoscience/bin/mas-app-contribution"
REQUEST_PREFIX = {
    "schema_version": "opl-package-app-contribution-request.v1",
    "operation": "read",
    "ref": "mas.runtime-detail.v1#current",
}


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = root / "studies" / study_id
    trajectory_root = study_root / "artifacts" / "research_trajectory"
    trajectory_root.mkdir(parents=True)
    (root / "workspace_index.json").write_text(
        json.dumps(
            {
                "surface_kind": "workspace_index",
                "schema_version": "mas.workspace_index.v1",
                "studies": [
                    {
                        "study_id": study_id,
                        "canonical_study_root": f"studies/{study_id}",
                        "display_name": "China-US diabetes mortality transportability",
                        "status": "delivered_paused",
                        "business_status": "delivered_paused",
                        "lifecycle_state": "delivered_paused",
                        "current_stage_id": None,
                        "current_stage_status": None,
                        "next_action": {
                            "action_id": "complete_submission_metadata_or_wake_for_revision",
                            "action_type": "user_action",
                            "owner": "user",
                            "status": "waiting",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (trajectory_root / "snapshot.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_research_trajectory_snapshot",
                "version": "mas-research-trajectory-snapshot.v2",
                "study_id": study_id,
                "study_ref": {"kind": "mas_study", "ref": f"mas-study:{study_id}"},
                "revision": 3,
                "status": "active",
                "current_focus": {
                    "node_id": "route-authoring",
                    "primary_hypothesis": "排序可转运但绝对风险不能直接转运",
                },
                "active_branch": {
                    "branch_id": "branch-revision",
                    "label": "论文修订路线",
                },
                "summary": {
                    "current_judgment": "受限转运性结论",
                    "next_research_step": "独立审阅后修订论文",
                },
                "nodes": [
                    {
                        "id": "hypothesis-transportability",
                        "kind": "hypothesis",
                        "status": "supported",
                        "label": "风险排序假设",
                        "summary": "排序部分保留",
                    },
                    {
                        "id": "route-authoring",
                        "kind": "route",
                        "status": "active",
                        "label": "论文修订",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return root


def _run(root: Path, identity: dict[str, str]) -> subprocess.CompletedProcess[str]:
    payload = {**REQUEST_PREFIX, "input": {"work_item_identity": identity}}
    env = {**os.environ, "OPL_PROFILE_WORKSPACE": str(root)}
    return subprocess.run(
        [str(PRODUCER)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def _identity(work_item_id: str = "002-dm-china-us-mortality-attribution") -> dict[str, str]:
    return {
        "agent_id": "mas",
        "domain_id": "medautoscience",
        "work_item_id": work_item_id,
        "domain_work_item_id": work_item_id,
        "work_item_scope_id": "work-item:test-scope",
        "identity_state": "resolved",
    }


def test_runtime_detail_reads_real_sources_and_preserves_paused_business_state(tmp_path: Path) -> None:
    result = _run(_workspace(tmp_path), _identity())
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    detail = payload["result"]
    assert detail["identity"]["work_item_id"] == detail["identity"]["study_id"]
    assert detail["agent"] == {
        "agent_id": "mas",
        "display_name": "Med Auto Science",
        "authority_owner": "MedAutoScience",
    }
    assert detail["current_owner"] == "user"
    assert detail["phase"] == {
        "business_status": "delivered_paused",
        "lifecycle_state": "delivered_paused",
        "stage_id": None,
        "stage_status": None,
    }
    assert detail["work"]["active"] == []
    assert detail["work"]["queued"] == []
    assert detail["work"]["pending"][0]["action_id"] == (
        "complete_submission_metadata_or_wake_for_revision"
    )
    assert detail["hypotheses"][0]["hypothesis_id"] == "hypothesis-transportability"
    assert detail["roadmap"]["trajectory_revision"] == 3
    assert detail["authority_boundary"]["writes_domain_truth"] is False


def test_runtime_detail_rejects_unresolved_or_mismatched_identity(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    unresolved = _identity()
    unresolved["identity_state"] = "identity_unresolved"
    result = _run(root, unresolved)
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]["code"] == (
        "mas_runtime_detail_contribution_invalid"
    )

    mismatch = _identity()
    mismatch["domain_work_item_id"] = "001-dm-cvd-mortality-risk"
    result = _run(root, mismatch)
    assert result.returncode == 2
    assert "domain_work_item_id" in json.loads(result.stdout)["error"]["message"]


def test_owner_and_carrier_manifest_declare_one_runtime_detail_surface() -> None:
    owner = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(encoding="utf-8")
    )
    carrier = json.loads(
        (ROOT / "plugins/med-autoscience/opl-package.json").read_text(encoding="utf-8")
    )
    assert owner["app_contributions"] == carrier["app_contributions"]
    assert owner["codex_surface"]["app_contribution_abi"] == carrier["codex_surface"]["app_contribution_abi"]
    assert owner["codex_surface"]["app_contribution_adapter"] == carrier["codex_surface"]["app_contribution_adapter"]
    adapter = json.loads((ROOT / "app-contribution-adapter.json").read_text(encoding="utf-8"))
    carrier_adapter = json.loads(
        (ROOT / "plugins/med-autoscience/app-contribution-adapter.json").read_text(encoding="utf-8")
    )
    assert adapter == carrier_adapter
    assert set(adapter["reads"]) == {"mas.runtime-detail.v1#current"}
    assert adapter["reads"]["mas.runtime-detail.v1#current"]["stdin"] == "request_json"
    assert adapter["reads"]["mas.runtime-detail.v1#current"]["passthrough"] is True
    assert owner["app_contributions"]["ui"][0] == {
        "contribution_id": "mas.runtime-detail",
        "slot": "runtime.detail",
        "contribution_kind": "view",
        "trust_tier": "declarative",
        "scope": "work_item",
        "sort_order": 100,
        "view_id": "mas.runtime-detail",
    }
    assert owner["app_contributions"]["views"][0]["view_type"] == "activity_log"


def test_contribution_preserves_full_owner_trajectory(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    snapshot_file = root / "studies" / study_id / "artifacts/research_trajectory/snapshot.json"
    snapshot = json.loads(snapshot_file.read_text())
    snapshot["nodes"][0]["details"] = {"evidence_judgment": "Not established", "review_refs": ["review:1"]}
    snapshot["nodes"][0]["source_refs"] = [{"kind": "evidence", "ref": "evidence:1"}]
    snapshot_file.write_text(json.dumps(snapshot))
    request = {**REQUEST_PREFIX, "input": {"work_item_identity": {
        "agent_id": "mas", "domain_id": "medautoscience", "work_item_id": study_id,
        "domain_work_item_id": study_id, "work_item_scope_id": "scope:fixture", "identity_state": "resolved"}}}
    result = subprocess.run([str(PRODUCER)], input=json.dumps(request), text=True, capture_output=True,
                            env={**os.environ, "OPL_PROFILE_WORKSPACE": str(root)}, check=True)
    assert json.loads(result.stdout)["result"]["trajectory"] == snapshot


def test_current_study_progress_is_available_before_trajectory_exists(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    trajectory = root / "studies" / _identity()["work_item_id"] / "artifacts/research_trajectory/snapshot.json"
    trajectory.unlink()
    result = _run(root, _identity())
    assert result.returncode == 0, result.stdout
    detail = json.loads(result.stdout)["result"]
    assert detail["phase"]["business_status"] == "delivered_paused"
    assert detail["work"]["pending"][0]["status"] == "waiting"
    assert detail["trajectory"] is None
    assert detail["trajectory_status"] == "not_available"
    assert detail["artifacts"] == []
    assert detail["source_refs"] == ["workspace_index.json"]

    trajectory.write_text("broken JSON")
    result = _run(root, _identity())
    assert result.returncode == 2
    assert "unavailable or invalid" in json.loads(result.stdout)["error"]["message"]


def test_artifacts_preserve_owner_evidence_without_claiming_acceptance(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    path = root / "studies" / _identity()["work_item_id"] / "artifacts/research_trajectory/snapshot.json"
    snapshot = json.loads(path.read_text())
    artifact = {
        "id": "draft-manuscript",
        "kind": "artifact",
        "label": "Manuscript draft",
        "status": "produced",
        "summary": "Draft available for review",
        "revision": 7,
        "details": {"evidence_judgment": "Not assessed"},
        "source_refs": [{"kind": "manuscript", "ref": "manuscript/draft.md"}],
    }
    snapshot["nodes"].append(artifact)
    path.write_text(json.dumps(snapshot))
    result = _run(root, _identity())
    assert result.returncode == 0, result.stdout
    detail = json.loads(result.stdout)["result"]
    assert detail["artifacts"] == [{
        **artifact,
        "artifact_id": artifact["id"], "title": artifact["label"],
        "status": "produced", "summary": artifact["summary"],
        "details": artifact["details"], "source_refs": artifact["source_refs"],
    }]
    assert detail["trajectory"] == snapshot


def test_review_context_reopens_the_same_study_and_exact_observed_sources(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    first = json.loads(_run(root, _identity()).stdout)["result"]["review_context"]
    reopened = json.loads(_run(root, _identity()).stdout)["result"]["review_context"]
    assert reopened == first
    assert first["work_item_identity"] == _identity()
    assert first["trajectory_revision"] == 3
    for source in first["source_refs"]:
        assert source["sha256"] == "sha256:" + hashlib.sha256((root / source["ref"]).read_bytes()).hexdigest()
    assert first["artifacts"] == []


def test_review_revision_changes_for_selected_evidence_but_not_other_studies(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    first = json.loads(_run(root, _identity()).stdout)["result"]["review_context"]
    index_path = root / "workspace_index.json"
    index = json.loads(index_path.read_text())
    index["studies"].append({"study_id": "unrelated-study", "status": "running"})
    index_path.write_text(json.dumps(index))
    other = json.loads(_run(root, _identity()).stdout)["result"]["review_context"]
    assert other["revision"] == first["revision"]
    assert other["source_refs"][0]["sha256"] != first["source_refs"][0]["sha256"]
    trajectory_path = root / first["source_refs"][1]["ref"]
    trajectory = json.loads(trajectory_path.read_text())
    trajectory["revision"] = 4
    trajectory["nodes"][0]["summary"] = "New contrary evidence changes the proposed route"
    trajectory_path.write_text(json.dumps(trajectory))
    changed = json.loads(_run(root, _identity()).stdout)["result"]["review_context"]
    assert changed["revision"] != first["revision"]
    assert changed["trajectory_revision"] == 4


def test_review_context_is_available_without_trajectory_and_tracks_pending_decision(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    trajectory = root / "studies" / _identity()["work_item_id"] / "artifacts/research_trajectory/snapshot.json"
    trajectory.unlink()
    before = json.loads(_run(root, _identity()).stdout)["result"]
    assert before["review_context"]["trajectory_revision"] is None
    assert len(before["review_context"]["source_refs"]) == 1
    index_path = root / "workspace_index.json"
    index = json.loads(index_path.read_text())
    index["studies"][0]["next_action"]["status"] = "completed"
    index_path.write_text(json.dumps(index))
    after = json.loads(_run(root, _identity()).stdout)["result"]
    assert after["review_context"]["revision"] != before["review_context"]["revision"]
    assert after["work"]["pending"] == []
    assert after["phase"]["business_status"] == "delivered_paused"


def test_review_source_cannot_escape_registered_workspace(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    trajectory = root / "studies" / _identity()["work_item_id"] / "artifacts/research_trajectory/snapshot.json"
    outside = tmp_path / "outside.json"
    trajectory.rename(outside)
    trajectory.symlink_to(outside)
    result = _run(root, _identity())
    assert result.returncode == 2
    assert "escapes" in json.loads(result.stdout)["error"]["message"]
