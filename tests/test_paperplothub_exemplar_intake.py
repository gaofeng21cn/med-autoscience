from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import tomllib

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_PATH = REPO_ROOT / "docs/capabilities/medical-display/paperplothub_exemplar_intake.md"
LEDGER_PATH = REPO_ROOT / "docs/capabilities/medical-display/paperplothub_exemplar_exhaustion_ledger.md"
TEMPLATE_ROOT = REPO_ROOT / "display-packs"

EXPECTED_STATUS_COUNTS = {
    "mapped_existing_template": 3,
    "visual_style_only": 3,
    "candidate_gap": 18,
    "reject_for_medical_display": 3,
}
EXPECTED_CANDIDATE_GAP_SLUGS = {
    "average_scores_across_warmup_steps",
    "paperespresso_swarm",
    "aievol_diversification",
    "opengame_debug_iters",
    "kronos_test_time_scaling",
    "phybench_model_perf",
    "ttrl_main_results",
    "prerl_behavior_bars",
    "prerl_passk_qwen4b",
    "prerl_behavior_panels",
    "prerl_grad_metrics_hist",
    "classwise_iou",
    "scatter_break",
    "line_selfdistill_scale",
    "line_selfdistill_train",
    "line_aime",
    "bar_spice",
    "bar_memevolve",
}
EXPECTED_CLUSTER_SLUGS = {
    "generic performance bar families": {
        "average_scores_across_warmup_steps",
        "phybench_model_perf",
        "ttrl_main_results",
        "prerl_behavior_bars",
        "bar_spice",
        "bar_memevolve",
    },
    "metric trajectory families": {
        "opengame_debug_iters",
        "kronos_test_time_scaling",
        "prerl_passk_qwen4b",
        "prerl_behavior_panels",
        "line_selfdistill_scale",
        "line_selfdistill_train",
        "line_aime",
    },
    "distribution panels": {
        "paperespresso_swarm",
        "prerl_grad_metrics_hist",
    },
    "temporal composition": {
        "aievol_diversification",
    },
    "heat-shaded performance tables": {
        "classwise_iou",
    },
    "tradeoff scatter / Pareto views": {
        "scatter_break",
    },
}


def _intake_rows() -> list[dict[str, str]]:
    lines = INTAKE_PATH.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    for line in lines:
        if line.startswith("| slug |"):
            header = [cell.strip() for cell in line.strip("|").split("|")]
            continue
        if header is None:
            continue
        if line.startswith("| ---"):
            continue
        if not line.startswith("| "):
            break

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == len(header)
        rows.append(dict(zip(header, cells, strict=True)))

    assert header == [
        "slug",
        "PaperPlotHub URL",
        "script URL",
        "paper/arXiv",
        "chart type",
        "tags",
        "MAS family",
        "existing template mapping",
        "landing status",
        "license/provenance note",
    ]
    return rows


def _strip_code(value: str) -> str:
    return value.strip().strip("`")


def test_paperplothub_intake_enumerates_current_public_gallery_and_status_counts() -> None:
    rows = _intake_rows()
    statuses = Counter(_strip_code(row["landing status"]) for row in rows)

    assert len(rows) == 27
    assert statuses == EXPECTED_STATUS_COUNTS
    assert {status for status in statuses} == set(EXPECTED_STATUS_COUNTS)
    assert all("https://paperplothub.tech/p/" in row["PaperPlotHub URL"] for row in rows)
    assert all("https://paperplothub.tech/files/" in row["script URL"] for row in rows)
    assert all("no script or image copied" in row["license/provenance note"] for row in rows)


def test_paperplothub_candidate_gaps_are_exhausted_into_promotion_clusters() -> None:
    rows = _intake_rows()
    candidate_slugs = {
        _strip_code(row["slug"])
        for row in rows
        if _strip_code(row["landing status"]) == "candidate_gap"
    }
    ledger = LEDGER_PATH.read_text(encoding="utf-8")

    assert candidate_slugs == EXPECTED_CANDIDATE_GAP_SLUGS
    assert "No More Current Learning Criteria" in ledger
    assert "出现新条目" in ledger
    assert "真实 MAS paper demand" in ledger
    assert "不创建新模板" in ledger

    clustered_slugs: set[str] = set()
    for cluster, slugs in EXPECTED_CLUSTER_SLUGS.items():
        assert cluster in ledger
        for slug in slugs:
            assert f"`{slug}`" in ledger
        clustered_slugs.update(slugs)

    assert clustered_slugs == candidate_slugs
    assert ledger.count("`exhausted_current_public_surface`") == len(EXPECTED_CLUSTER_SLUGS)


def test_paperplothub_template_exemplar_refs_stay_page_link_only() -> None:
    intake_slugs = {_strip_code(row["slug"]) for row in _intake_rows()}
    paperplothub_refs: list[tuple[Path, str]] = []

    for manifest_path in TEMPLATE_ROOT.rglob("template.toml"):
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        for ref in payload.get("exemplar_refs", []):
            if "PaperPlotHub" in ref:
                paperplothub_refs.append((manifest_path, ref))

    assert paperplothub_refs
    for manifest_path, ref in paperplothub_refs:
        assert "https://paperplothub.tech/p/" in ref, manifest_path
        assert "paperplothub.tech/files/" not in ref, manifest_path
        assert "script.py" not in ref, manifest_path
        match = re.fullmatch(r"PaperPlotHub `(?P<slug>[a-z0-9_]+)` https://paperplothub\.tech/p/(?P=slug)", ref)
        assert match is not None, (manifest_path, ref)
        assert match.group("slug") in intake_slugs
