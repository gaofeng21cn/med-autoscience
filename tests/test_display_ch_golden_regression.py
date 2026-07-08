from __future__ import annotations

from tests.display_ch_golden_regression_cases.shared import (
    Path,
    importlib,
    json,
    _dump_json,
)
from tests.display_ch_golden_regression_cases.clinical_baseline_and_transportability_golden import (
    test_generalizability_subgroup_composite_panel_preserves_ch_bounded_contract,
    test_compact_effect_estimate_panel_preserves_ch_bounded_contract,
    test_coefficient_path_panel_preserves_ch_bounded_contract,
    test_broader_heterogeneity_summary_panel_preserves_ch_bounded_contract,
    test_interaction_effect_summary_panel_preserves_ch_bounded_contract,
)
