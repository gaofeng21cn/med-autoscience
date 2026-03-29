from __future__ import annotations

import importlib
from pathlib import Path


def test_load_profile_parses_expected_fields(tmp_path: Path) -> None:
    profile_path = tmp_path / "nfpitnet.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤"',
                'runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime/quests"',
                'studies_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/studies"',
                'portfolio_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/portfolio"',
                'deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        profiles = importlib.import_module("med_autoscience.profiles")
    except ModuleNotFoundError:
        profiles = None

    assert profiles is not None
    load_profile = getattr(profiles, "load_profile", None)
    assert callable(load_profile)

    profile = load_profile(profile_path)

    assert profile.name == "nfpitnet"
    assert profile.workspace_root == Path("/Users/gaofeng/workspace/Yang/无功能垂体瘤")
    assert profile.default_publication_profile == "general_medical_journal"
    assert profile.default_citation_style == "AMA"
