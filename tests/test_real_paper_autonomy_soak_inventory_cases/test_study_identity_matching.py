from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_guarded_apply_proof,
    build_real_paper_autonomy_soak_closeout_projection,
    build_real_paper_autonomy_soak_projection,
)


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_profile(workspace: Path, profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        "\n".join(
            [
                'name = "fixture"',
                f'workspace_root = "{workspace}"',
                f'runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace / "studies"}"',
                f'portfolio_root = "{workspace / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_guarded_apply_preserves_cross_profile_numeric_study_identity(tmp_path: Path) -> None:
    yang_root = tmp_path / "Yang"
    dm_workspace = yang_root / "DM"
    nf_workspace = yang_root / "NF"
    dm_profile = dm_workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    nf_profile = nf_workspace / "ops" / "medautoscience" / "profiles" / "nf.workspace.toml"
    _write_profile(dm_workspace, dm_profile)
    _write_profile(nf_workspace, nf_profile)
    (dm_workspace / "portfolio").mkdir(parents=True)
    (nf_workspace / "portfolio").mkdir(parents=True)
    target_studies = (
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "002-early-residual-risk",
        "003-endocrine-burden-followup",
    )
    for workspace, study_id in (
        (dm_workspace, "002-dm-china-us-mortality-attribution"),
        (dm_workspace, "003-dpcc-primary-care-phenotype-treatment-gap"),
        (nf_workspace, "002-early-residual-risk"),
        (nf_workspace, "003-endocrine-burden-followup"),
    ):
        study_root = workspace / "studies" / study_id
        _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_id})
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": f"eval-{study_id}"},
        )

    projection = build_real_paper_autonomy_soak_projection(
        yang_root=yang_root,
        profile_paths=[dm_profile, nf_profile],
        target_studies=target_studies,
    )

    coverage = {item["target_study"]: item for item in projection["summary"]["target_coverage"]}
    assert {target: coverage[target]["matched_study_ids"] for target in target_studies} == {
        target: [target] for target in target_studies
    }

    closeout = build_real_paper_autonomy_soak_closeout_projection(
        yang_root=yang_root,
        profile_paths=[dm_profile, nf_profile],
        target_studies=target_studies,
    )

    closeout_ids = [packet["route_impact"]["study_id"] for packet in closeout["closeout_packets"]]
    assert closeout_ids == list(target_studies)

    guarded = build_real_paper_autonomy_guarded_apply_proof(
        yang_root=yang_root,
        profile_paths=[dm_profile, nf_profile],
        target_studies=target_studies,
    )

    paper_lines = [
        item["paper_line_id"]
        for item in guarded["paper_line_provider_canary_closeout"]["paper_line_owner_chain_results"]
    ]
    assert paper_lines == list(target_studies)

    alias_projection = build_real_paper_autonomy_soak_projection(
        yang_root=yang_root,
        profile_paths=[dm_profile, nf_profile],
        target_studies=("DM002", "DM003"),
    )

    alias_coverage = {item["target_study"]: item for item in alias_projection["summary"]["target_coverage"]}
    assert alias_coverage["DM002"]["matched_study_ids"] == [
        "002-dm-china-us-mortality-attribution"
    ]
    assert alias_coverage["DM003"]["matched_study_ids"] == [
        "003-dpcc-primary-care-phenotype-treatment-gap"
    ]
