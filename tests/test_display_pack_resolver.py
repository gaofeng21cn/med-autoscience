from __future__ import annotations

import pytest

from med_autoscience.display_pack_resolver import split_full_template_id


def test_split_full_template_id_returns_pack_and_template() -> None:
    pack_id, template_id = split_full_template_id(
        "fenggaolab.org.medical-display-core::roc_curve_binary"
    )

    assert pack_id == "fenggaolab.org.medical-display-core"
    assert template_id == "roc_curve_binary"


def test_split_full_template_id_rejects_non_namespaced_value() -> None:
    with pytest.raises(ValueError, match="full template id"):
        split_full_template_id("roc_curve_binary")
